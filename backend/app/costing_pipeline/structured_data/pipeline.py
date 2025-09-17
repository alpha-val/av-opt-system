## File: `structured/pipeline.py`

from __future__ import annotations
from typing import Optional, Dict, Any
import pandas as pd
import os, io, hashlib
from app.costing_pipeline.storage import (
    GNode,
    GRel,
    GDoc,
    Neo4jWriter,
    embed_and_upsert_to_pinecone,
)
from .transform import parse_table_dataframe, build_graph_from_table
from .rowcards import make_row_card_chunks
from .cypher_bundle import ensure_constraints


def _file_hash(name: str, df: pd.DataFrame) -> str:
    m = hashlib.sha1()
    m.update((name or "").encode("utf-8"))
    # include header + first rows to detect versioning
    m.update("|".join(map(str, df.columns)).encode("utf-8"))
    m.update(df.head(20).to_csv(index=False).encode("utf-8"))
    return m.hexdigest()[:12]


def _load_dataframe(stream_or_path, sheet: Optional[str] = None) -> pd.DataFrame:
    name = getattr(stream_or_path, "name", None) or str(stream_or_path)
    if isinstance(stream_or_path, (io.BytesIO, io.BufferedReader)) or hasattr(
        stream_or_path, "read"
    ):
        # try Excel first, then CSV
        stream_or_path.seek(0)
        try:
            return pd.read_excel(stream_or_path, sheet_name=sheet)
        except Exception:
            stream_or_path.seek(0)
            return pd.read_csv(stream_or_path)
    else:
        path = str(stream_or_path)
        ext = os.path.splitext(path)[1].lower()
        if ext in [".xlsx", ".xlsm", ".xls"]:
            return pd.read_excel(path, sheet_name=sheet)
        return pd.read_csv(path)


def _doc_id(file_name: str, table_title: str) -> str:
    base = os.path.basename(file_name)
    return f"table::{base}::{table_title}"


def _table_title(df: pd.DataFrame, sheet: Optional[str]) -> str:
    title = sheet or "Sheet1"
    # If a first header cell looks like a title string, prefer it
    try:
        h0 = str(df.columns[0])
        if len(h0) > 15:
            title = h0
    except Exception:
        pass
    return title


def run_ingestion_for_table_stream(
    stream,
    *,
    sheet: Optional[str] = None,
    currency_override: Optional[str] = None,
    base_year_override: Optional[int] = None,
) -> Dict[str, Any]:
    df = _load_dataframe(stream, sheet=sheet)
    file_name = getattr(stream, "name", "uploaded.xlsx")
    table_title = _table_title(df, sheet)
    return _process_dataframe(
        df,
        file_name=file_name,
        table_title=table_title,
        currency_override=currency_override,
        base_year_override=base_year_override,
    )


def run_ingestion_for_table_path(
    path: str,
    *,
    sheet: Optional[str] = None,
    currency_override: Optional[str] = None,
    base_year_override: Optional[int] = None,
) -> Dict[str, Any]:
    df = _load_dataframe(path, sheet=sheet)
    table_title = _table_title(df, sheet)
    return _process_dataframe(
        df,
        file_name=path,
        table_title=table_title,
        currency_override=currency_override,
        base_year_override=base_year_override,
    )


def _process_dataframe(
    df: pd.DataFrame,
    *,
    file_name: str,
    table_title: str,
    currency_override: Optional[str],
    base_year_override: Optional[int],
) -> Dict[str, Any]:
    # 1) parse → Table/Row/Cell + domain facts
    try:
        parsed = parse_table_dataframe(
            df,
            source_file=file_name,
            sheet=table_title,
            currency_override=currency_override,
            base_year_override=base_year_override,
        )
    except Exception as ex:
        raise ValueError(
            f"Failed to parse table '{table_title}' in '{file_name}': {ex}"
        )
    # 2) build graph package
    gdoc: GDoc = build_graph_from_table(parsed)

    # 3) create row-card :Chunk nodes and MENTIONS; add to graph
    try:
        print(f"[INGEST 2] - Creating row-cards for table '{table_title}' in '{file_name}'...")
        # nodes, rels, chunks = make_row_card_chunks(parsed)
        rowcard_result = make_row_card_chunks(parsed)
        nodes = rowcard_result["nodes"]
        rels = rowcard_result["relationships"]
        chunks_for_pinecone = rowcard_result["chunks_for_pinecone"]
    except Exception as ex:
        raise ValueError(
            f"Failed to create row-cards for table '{table_title}' in '{file_name}': {ex}"
        )
    # gdoc.nodes.extend(chunks["nodes"])  # :Chunk nodes
    gdoc.nodes.extend(nodes)  # row-card nodes
    gdoc.relationships.extend(rels)  # :MENTIONS edges from row-cards

    # 4) write to Neo4j (ensures constraints first)
    ensure_constraints()
    writer = Neo4jWriter()
    write_stats = writer.save(gdoc)
    writer.close()

    # 5) upsert row-cards to Pinecone (dense + sparse hybrid)
    upsert_stats = embed_and_upsert_to_pinecone(
        file_id=_doc_id(file_name, table_title),
        chunks=chunks_for_pinecone,
    )

    return {
        "file": file_name,
        "table": table_title,
        "hash": _file_hash(file_name, df),
        "nodes_written": write_stats["nodes_written"],
        "rels_written": write_stats["rels_written"],
        "pinecone": upsert_stats,
        "parsed_counts": parsed["counts"],
    }
