from fastapi import APIRouter, Query, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
import json
import logging
import pandas as pd
import datetime
import uuid

from app.text_clean import (
    extract_and_clean,
    chunk_by_page,
    process_extracted_nodes,
    NAMESPACE,
)
from ..ontology import load_ontology
from ..build_prompt import gen_prompt
from .tabular_rules import TABULAR_RULES
from .table_payload import build_llm_payload
from ..bronze_store import (
    bulk_upsert_chunks,
    bulk_upsert_entities,
    bulk_upsert_relations,
)
from app.etl_base.extract_with_openai import openai_extract_nodes_rels
from app.vector_db.vector_operations import (
    upsert_entities_to_pinecone,
)


logger = logging.getLogger(__name__)
router_ingest_tables = APIRouter()


def _generate_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def _normalize_entity_id(entity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure entity has proper UUID-style _id and id fields.

    Args:
        entity: Entity dictionary (node)

    Returns:
        Entity with normalized IDs
    """
    # Generate new UUID if _id doesn't exist or isn't UUID format
    if "_id" not in entity or not _is_valid_uuid(entity.get("_id")):
        entity["_id"] = _generate_uuid()

    # Ensure id matches _id
    entity["id"] = entity["_id"]

    # Store original LLM-generated ID in properties for reference
    if "properties" not in entity:
        entity["properties"] = {}

    # If there was an original text ID, preserve it as a reference
    original_id = entity.get("name", "").lower().replace(" ", "_")
    if original_id and original_id != entity["_id"]:
        entity["properties"]["original_id"] = original_id

    return entity


def _normalize_edge_id(
    edge: Dict[str, Any], node_id_map: Dict[str, str]
) -> Dict[str, Any]:
    """
    Ensure edge has proper UUID-style _id and remapped source/target.

    Args:
        edge: Edge dictionary (relation)
        node_id_map: Mapping from old text IDs to new UUIDs

    Returns:
        Edge with normalized IDs
    """
    # Remap source and target from text IDs to UUIDs
    source = edge.get("source")
    target = edge.get("target")

    if source in node_id_map:
        edge["source"] = node_id_map[source]
    if target in node_id_map:
        edge["target"] = node_id_map[target]

    # Generate edge _id from source|target|type
    if "_id" not in edge:
        edge["_id"] = f"{edge['source']}|{edge['target']}|{edge['type']}"

    # Ensure id matches _id
    edge["id"] = edge["_id"]

    return edge


def _is_valid_uuid(id_str: str) -> bool:
    """Check if string is a valid UUID."""
    try:
        uuid.UUID(str(id_str))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def _extract_tables_from_pdf(
    pdf_bytes: bytes, pages: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract tables from PDF using cascade approach (Camelot → pdfplumber fallback).

    Args:
        pdf_bytes: PDF file bytes
        pages: Optional page range (e.g., "1-5,10")

    Returns:
        List of table dictionaries with 'df' and 'meta'
    """
    try:
        from ..pdf_extract import extract_pdf_tables

        tables = extract_pdf_tables(pdf_bytes, pages=pages)
        logger.info(f"[TABLE_EXTRACT] Extracted {len(tables)} tables using cascade")
        return tables
    except ImportError:
        logger.warning(
            "[TABLE_EXTRACT] pdf_extract module not found, falling back to Camelot"
        )
        return _extract_tables_camelot(pdf_bytes, pages)
    except Exception as e:
        logger.error(
            f"[TABLE_EXTRACT] Cascade extraction failed: {e}, falling back to Camelot"
        )
        return _extract_tables_camelot(pdf_bytes, pages)


def _extract_tables_camelot(
    pdf_bytes: bytes, pages: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fallback: Extract tables using Camelot only.

    Args:
        pdf_bytes: PDF file bytes
        pages: Optional page range

    Returns:
        List of table dictionaries
    """
    try:
        import camelot
        import tempfile
        import os
    except ImportError:
        logger.error("[TABLE_EXTRACT] Camelot not installed")
        return []

    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(pdf_bytes)

        pages_str = pages or "1-end"
        tables = camelot.read_pdf(path, pages=pages_str, flavor="lattice")

        out = []
        for i, t in enumerate(tables or []):
            df = t.df
            # Light cleanup
            df = (
                df.replace(r"^\s*$", None, regex=True)
                .dropna(how="all")
                .dropna(axis=1, how="all")
            )
            out.append(
                {"df": df, "meta": {"page": t.page, "flavor": "lattice", "index": i}}
            )

        logger.info(f"[TABLE_EXTRACT] Extracted {len(out)} tables using Camelot")
        return out

    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def make_table_id(doc_id: str, page: int, index: int) -> str:
    """Generate deterministic table ID."""
    return f"tbl::{doc_id}::p{page}::{index}"


def make_row_id(table_id: str, row_idx: int) -> str:
    """Generate deterministic row ID."""
    return f"row::{table_id}::{row_idx}"


def _prepare_table_metadata(
    df: pd.DataFrame,
    meta: Dict[str, Any],
    doc_id: str,
    project_id: str,
    user_id: str,
    filename: str,
) -> Dict[str, Any]:
    """
    Prepare table metadata in the format expected by downstream processing.

    Args:
        df: DataFrame with table data
        meta: Extraction metadata (page, index, etc.)
        doc_id: Document identifier
        project_id: Project identifier
        user_id: User identifier
        filename: Source filename

    Returns:
        Table metadata dictionary
    """
    page = int(meta.get("page", 1))
    index = int(meta.get("index", 0))
    table_id = make_table_id(doc_id, page, index)

    # Ensure column names are strings
    df.columns = [str(c) for c in df.columns]
    columns = list(df.columns)

    # Create preview
    preview = df.head(5).to_dict(orient="records")

    table_metadata = {
        "table_id": table_id,
        "doc_id": doc_id,
        "project_id": project_id,
        "user_id": user_id,
        "filename": filename,
        "page": page,
        "index": index,
        "columns": columns,
        "column_count": len(columns),
        "row_count": len(df),
        "preview": preview,
        "data_type": "tabular",
        "artifact_type": "tabular_data",
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at": datetime.datetime.now(datetime.timezone.utc),
        **meta,  # Include original extraction metadata
    }

    return table_metadata


def _prepare_row_documents(df: pd.DataFrame, table_id: str) -> List[Dict[str, Any]]:
    """
    Convert DataFrame rows to row documents format.

    Args:
        df: DataFrame with table data
        table_id: Table identifier

    Returns:
        List of row documents
    """
    row_docs = []
    columns = [str(c) for c in df.columns]

    for i, row in df.iterrows():
        # Handle different index types
        i_num = (
            int(i)
            if isinstance(i, (int, float)) or (isinstance(i, str) and i.isdigit())
            else len(row_docs)
        )

        row_id = make_row_id(table_id, i_num)

        # Build cell data
        cells = []
        for col in columns:
            raw = row.get(col)
            val = None if pd.isna(raw) else str(raw)
            cells.append({"col": col, "raw": val, "text": val})

        row_docs.append(
            {"_id": row_id, "table_id": table_id, "row_idx": i_num, "cells": cells}
        )

    return row_docs


def enhance_with_lineage(
    kg_data: Dict[str, Any], table_meta: Dict[str, Any], rows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Add lineage edges connecting entities to their source rows.
    """
    table_id = table_meta.get("table_id")

    # DEBUG: Log what we receive
    logger.info(f"[LINEAGE] Received {len(kg_data.get('nodes', []))} nodes")
    logger.info(f"[LINEAGE] Received {len(kg_data.get('edges', []))} edges")

    valid_nodes = kg_data.get("nodes", [])
    valid_edges = kg_data.get("edges", [])

    # Create TableRow nodes
    table_row_nodes = []
    for row in rows:
        if not isinstance(row, dict):
            logger.warning(f"[LINEAGE] Skipping invalid row: {type(row)}")
            continue

        table_row_nodes.append(
            {
                "id": row.get("_id"),
                "type": "TableRow",
                "properties": {
                    "row_index": row.get("row_idx", 0),
                    "table_id": table_id,
                    "confidence": 1.0,
                },
            }
        )

    # Add lineage edges from entities to rows
    lineage_edges = []
    for node in valid_nodes.get("nodes", []):
        if not isinstance(node.get("properties"), dict):
            continue

        row_idx = node.get("properties", {}).get("row_index")
        if row_idx is not None:
            matching_row = next(
                (
                    r
                    for r in rows
                    if isinstance(r, dict) and r.get("row_idx") == row_idx
                ),
                None,
            )
            if matching_row:
                lineage_edges.append(
                    {
                        "source": node.get("id"),
                        "target": matching_row.get("_id"),
                        "type": "DERIVES_FROM",
                        "properties": {
                            "row_index": row_idx,
                            "extraction_method": "tabular_direct",
                            "confidence": 1.0,
                        },
                    }
                )

    # Merge into KG data
    kg_data["nodes"].extend(table_row_nodes)
    kg_data["edges"].extend(lineage_edges)

    logger.info(
        f"[LINEAGE] Final: {len(kg_data['nodes'])} total nodes ({len(valid_nodes)} entities + {len(table_row_nodes)} TableRow), "
        f"{len(kg_data['edges'])} total edges ({len(valid_edges)} original + {len(lineage_edges)} lineage)"
    )

    return kg_data


def _prepare_table_chunks(
    df: pd.DataFrame,
    table_meta: Dict[str, Any],
    rows: List[Dict[str, Any]],
    doc_id: str,
    project_id: str,
    user_id: str,
    artifact_type: str,
) -> List[Dict[str, Any]]:
    """
    Create chunk documents from table rows.
    Each chunk represents the table with its assembled text from all rows.

    Args:
        df: DataFrame with table data
        table_meta: Table metadata
        rows: List of row documents
        doc_id: Document identifier
        project_id: Project identifier
        user_id: User identifier
        artifact_type: Artifact type

    Returns:
        List of chunk documents
    """
    table_id = table_meta.get("table_id")
    page = table_meta.get("page", 1)
    chunk_index = table_meta.get("index", 0)

    # Assemble text representation from rows
    columns = [str(c) for c in df.columns]

    # Create header row
    header_text = " | ".join(columns)
    separator = "-" * len(header_text)

    # Create text rows
    row_texts = []
    for row_doc in rows:
        cells = row_doc.get("cells", [])
        cell_values = []
        for cell in cells:
            val = cell.get("text") or cell.get("raw") or ""
            cell_values.append(str(val))
        row_text = " | ".join(cell_values)
        row_texts.append(row_text)

    # Assemble full table text
    table_text_parts = [
        f"Table {chunk_index} (Page {page})",
        header_text,
        separator,
    ]
    table_text_parts.extend(row_texts)

    text_raw = "\n".join(table_text_parts)

    # Clean text version (remove extra whitespace, normalize)
    text_clean = " ".join(text_raw.split())

    # Create chunk document with ALL required fields
    chunk = {
        "chunk_id": f"chunk::{table_id}",
        "doc_id": doc_id,
        "table_id": table_id,
        "page": page,
        "seq": chunk_index,  # Add seq field (required by bulk_upsert_chunks)
        "chunk_index": chunk_index,
        "text_raw": text_raw,
        "text": text_clean,
        "chunk_type": "table",
        "n_tokens": len(text_clean.split()),  # Add token count
        "embedding": None,  # Add embedding field (can be populated later)
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at": datetime.datetime.now(datetime.timezone.utc),
        # Add properties field (required by bulk_upsert_chunks)
        "properties": {
            "project_id": project_id,
            "user_id": user_id,
            "artifact_type": artifact_type,
            "table_id": table_id,
            "row_count": len(rows),
            "column_count": len(columns),
            "columns": columns,
            "source": "tabular_extraction",
            "chunk_type": "table",
            "page": page,
        },
        #  Legacy metadata field (if needed for backward compatibility)
        "metadata": {
            "table_id": table_id,
            "row_count": len(rows),
            "column_count": len(columns),
            "columns": columns,
            "source": "tabular_extraction",
        },
    }

    return [chunk]


# Update the main processing function
def map_tables_to_entities(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    user_id: str = Form(...),
    doc_id: str = Form(...),
    artifact_type: str = Form("tabular_data"),
    pages: Optional[str] = Form(None),
    batch_size: int = Form(50),
):
    """
    Extract entities from PDF tables using LLM.

    This endpoint:
    1. Accepts a PDF file upload
    2. Extracts tables from the PDF
    3. Converts table rows to entities using LLM
    4. Stores entities in Silver collection

    Args:
        file: PDF file upload
        project_id: Project identifier
        user_id: User identifier
        doc_id: Document identifier
        artifact_type: Type of artifact (default: tabular_data)
        pages: Optional page range (e.g., "1-5,10")
        batch_size: Rows per LLM call (default 50)

    Returns:
        Extraction statistics including tables, rows, nodes, and edges
    """
    # Validate file type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file")

    # Ensure batch_size is an integer (Form data comes as string)
    try:
        batch_size = int(batch_size)
    except (TypeError, ValueError):
        batch_size = 50  # Default fallback

    # Read PDF bytes
    pdf_bytes = file.file.read()
    filename = file.filename or "uploaded.pdf"

    # Extract and clean text to get file hash
    try:
        some_id, file_sha, pages_raw, pages_clean = extract_and_clean(
            pdf_bytes, filename
        )
        file_size = len(pdf_bytes)
        logger.info(f"[TABULAR_PIPELINE] Processed doc_id: {doc_id}")
    except Exception as e:
        logger.error(f"[TABULAR_PIPELINE] Text extraction failed: {e}")
        raise HTTPException(500, f"Text extraction failed: {str(e)}")

    # Extract tables from PDF
    try:
        table_results = _extract_tables_from_pdf(pdf_bytes, pages)
        logger.info(
            f"[TABULAR_PIPELINE] Extracted {len(table_results)} tables from PDF"
        )
    except Exception as e:
        logger.error(f"[TABULAR_PIPELINE] Table extraction failed: {e}")
        raise HTTPException(500, f"Table extraction failed: {str(e)}")

    # If no tables found, fallback to text extraction only
    if not table_results:
        logger.warning(f"[TABULAR_PIPELINE] No tables found in {filename}")

        # 2) Build page chunks (Bronze) - Fallback to text extraction
        chunks = chunk_by_page(pages_clean, doc_id)
        raw_by_page = {p: t for p, t in pages_raw}
        for c in chunks:
            c["text_raw"] = raw_by_page.get(c["page"])
            # Add artifact_type, project_id, user_id to properties
            if "properties" not in c or not isinstance(c["properties"], dict):
                c["properties"] = {}
            c["properties"]["artifact_type"] = artifact_type
            c["properties"]["project_id"] = project_id
            c["properties"]["user_id"] = user_id
            c["properties"]["doc_id"] = doc_id

        # 3) Entities/relations/mentions from free text (Bronze)
        kg = openai_extract_nodes_rels(
            chunks, rules=["Units_Normalization", "Table_Extraction"]
        )
        nodes = list(kg.get("nodes", []) or [])
        edges = list(kg.get("edges", []) or [])

        # Attach simple source back-pointer to each node
        for n in nodes:
            srcs = n.get("sources") or []
            if not any(isinstance(s, dict) and s.get("doc_id") == doc_id for s in srcs):
                srcs.append({"doc_id": doc_id})
            n["sources"] = srcs
            # Add artifact_type, project_id, user_id to properties
            if "properties" not in n or not isinstance(n["properties"], dict):
                n["properties"] = {}
            n["properties"]["artifact_type"] = artifact_type
            n["properties"]["project_id"] = project_id
            n["properties"]["user_id"] = user_id
            n["properties"]["doc_id"] = doc_id

        # Apply additional processing to nodes if needed
        nodes = process_extracted_nodes(nodes)

        for e in edges:
            # Add artifact_type, project_id, user_id to properties
            if "properties" not in e or not isinstance(e["properties"], dict):
                e["properties"] = {}
            e["properties"]["artifact_type"] = artifact_type
            e["properties"]["project_id"] = project_id
            e["properties"]["user_id"] = user_id
            e["properties"]["doc_id"] = doc_id

        bulk_upsert_chunks(chunks)
        bulk_upsert_entities(nodes)
        bulk_upsert_relations(edges)

        # ========== NEW: Store in Vector Database ==========
        vectors_upserted = 0
        try:
            vectors_upserted = upsert_entities_to_pinecone(
                entities=nodes, project_id=project_id, artifact_type=artifact_type
            )
            logger.info(f"[INFO] Upserted {vectors_upserted} vectors to Pinecone")
        except Exception as e:
            logger.error(f"[ERROR] Failed to upsert to Pinecone: {e}")
            # Don't fail the entire ETL if vector upsert fails
        # ===================================================

        return {
            "filename": filename,
            "file_size": file_size,
            "file_sha256": file_sha,
            "pages": len(pages_clean),
            "chunks_written": len(chunks),
            "entities_written": len(nodes),
            "relations_written": len(edges),
            "vectors_upserted": vectors_upserted,  # NEW
        }

    # Process tables with LLM extraction
    else:
        # Load ontology and build prompt
        ontology = load_ontology()
        base_prompt = gen_prompt(ontology, rules=["Units_Normalization", "Table_Extraction"])
        full_prompt = base_prompt

        # Accumulators for all tables
        all_chunks = []
        all_nodes = []
        all_edges = []
        all_errors = []
        total_rows_processed = 0

        # Process each extracted table
        for seq, table_result in enumerate(table_results):
            df = table_result["df"]
            meta = table_result.get("meta", {})

            # Prepare table metadata
            table_meta = _prepare_table_metadata(
                df=df,
                meta=meta,
                doc_id=doc_id,
                project_id=project_id,
                user_id=user_id,
                filename=filename,
            )

            table_id = table_meta["table_id"]

            try:
                # Prepare row documents
                rows = _prepare_row_documents(df, table_id)

                if not rows:
                    logger.warning(f"[TABULAR_PIPELINE] No rows in table {table_id}")
                    continue

                # Create chunks from table rows
                table_chunks = _prepare_table_chunks(
                    df=df,
                    table_meta=table_meta,
                    rows=rows,
                    doc_id=doc_id,
                    project_id=project_id,
                    user_id=user_id,
                    artifact_type=artifact_type,
                )

                all_chunks.extend(table_chunks)

                # Limit rows for this batch
                rows_batch = rows[:batch_size]
                payload = build_llm_payload(table_meta, rows_batch, max_rows=batch_size)

                # Construct prompt with payload
                # input_text = (
                #     f"{full_prompt}\n\n"
                #     f"INPUT TABLE DATA (JSON):\n"
                #     f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
                # )
                chunks: List[Dict[str, Any]] = []
                chunk_id = str(uuid.uuid5(NAMESPACE, f"{doc_id}|{seq}"))
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "doc_id": doc_id,
                        "seq": seq,
                        "page": 0,
                        "text": json.dumps(payload, indent=2, ensure_ascii=False),
                    }
                )

                # Call LLM
                logger.info(
                    f"[TABULAR_PIPELINE] Calling LLM for table {table_id} ({len(rows_batch)} rows)"
                )
                # kg_data = call_llm_for_tables(input_text, ontology)
                kg_data = openai_extract_nodes_rels(chunks, rules=["Units_Normalization", "Table_Extraction"])

                # Check for errors in response
                if "error" in kg_data:
                    logger.error(
                        f"[TABULAR_PIPELINE] LLM extraction failed for {table_id}: {kg_data['error']}"
                    )
                    all_errors.append({"table_id": table_id, "error": kg_data["error"]})
                    continue

                nodes = list(kg_data.get("nodes", []) or [])
                edges = list(kg_data.get("edges", []) or [])

                # Filter out invalid nodes (must be dicts)
                nodes = [n for n in nodes if isinstance(n, dict)]
                edges = [e for e in edges if isinstance(e, dict)]

                if not nodes and not edges:
                    logger.warning(
                        f"[TABULAR_PIPELINE] No valid nodes or edges returned for {table_id}"
                    )
                    all_errors.append(
                        {
                            "table_id": table_id,
                            "error": "LLM returned invalid response format",
                        }
                    )
                    continue

                # Create mapping from old text IDs to new UUIDs
                node_id_map = {}
                normalized_nodes = []

                for n in nodes:
                    # Store original ID before normalization
                    original_id = (
                        n.get("id")
                        or n.get("_id")
                        or n.get("name", "").lower().replace(" ", "_")
                    )

                    # Normalize to UUID
                    n = _normalize_entity_id(n)

                    # Map old ID to new UUID
                    if original_id:
                        node_id_map[original_id] = n["_id"]

                    # Attach metadata
                    srcs = n.get("sources") or []
                    if not any(
                        isinstance(s, dict) and s.get("doc_id") == doc_id for s in srcs
                    ):
                        srcs.append({"doc_id": doc_id})
                    n["sources"] = srcs

                    if "properties" not in n or not isinstance(n["properties"], dict):
                        n["properties"] = {}
                    n["properties"]["artifact_type"] = artifact_type
                    n["properties"]["project_id"] = project_id
                    n["properties"]["user_id"] = user_id
                    n["properties"]["doc_id"] = doc_id
                    n["properties"]["table_id"] = table_id

                    normalized_nodes.append(n)

                # Apply additional processing to nodes if needed
                normalized_nodes = process_extracted_nodes(normalized_nodes)

                # Normalize edges with ID remapping
                normalized_edges = []
                for e in edges:
                    # Remap source/target from text IDs to UUIDs
                    e = _normalize_edge_id(e, node_id_map)

                    # Attach metadata
                    if "properties" not in e or not isinstance(e["properties"], dict):
                        e["properties"] = {}
                    e["properties"]["artifact_type"] = artifact_type
                    e["properties"]["project_id"] = project_id
                    e["properties"]["user_id"] = user_id
                    e["properties"]["doc_id"] = doc_id
                    e["properties"]["table_id"] = table_id

                    normalized_edges.append(e)

                # Use normalized entities
                all_nodes.extend(normalized_nodes)
                all_edges.extend(normalized_edges)
                total_rows_processed += len(rows_batch)

                logger.info(
                    f"[TABULAR_PIPELINE] Table {table_id}: {len(normalized_nodes)} nodes, {len(normalized_edges)} edges (IDs normalized)"
                )

            except Exception as e:
                logger.error(
                    f"[TABULAR_PIPELINE] Failed to process table {table_id}: {e}"
                )
                import traceback

                traceback.print_exc()
                all_errors.append({"table_id": table_id, "error": str(e)})
                continue

        # Bulk insert all accumulated data
        logger.info(
            f"[TABULAR_PIPELINE] Writing to database: "
            f"{len(all_chunks)} chunks, {len(all_nodes)} nodes, {len(all_edges)} edges"
        )

        try:
            if all_chunks:
                bulk_upsert_chunks(all_chunks)
            if all_nodes:
                bulk_upsert_entities(all_nodes)
            if all_edges:
                bulk_upsert_relations(all_edges)
        except Exception as e:
            logger.error(f"[TABULAR_PIPELINE] Database write failed: {e}")
            import traceback

            traceback.print_exc()
            raise HTTPException(500, f"Database write failed: {str(e)}")

        # Store in Vector Database
        vectors_upserted = 0
        try:
            vectors_upserted = upsert_entities_to_pinecone(
                entities=all_nodes, project_id=project_id, artifact_type=artifact_type
            )
            logger.info(f"[INFO] Upserted {vectors_upserted} vectors to Pinecone")
        except Exception as e:
            logger.error(f"[ERROR] Failed to upsert to Pinecone: {e}")
            import traceback

            traceback.print_exc()

        results = {
            "doc_id": doc_id,
            "filename": filename,
            "file_size": file_size,
            "file_sha256": file_sha,
            "pages": len(pages_clean),
            "tables_processed": len(table_results),
            "rows_processed": total_rows_processed,
            "chunks_written": len(all_chunks),
            "entities_written": len(all_nodes),
            "relations_written": len(all_edges),
            "vectors_upserted": vectors_upserted,
            "errors": all_errors if all_errors else None,
        }

        logger.info(f"[TABULAR_PIPELINE] Completed: {results}")
        return results
