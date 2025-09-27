from __future__ import annotations
from typing import Optional, Dict, Any, List, Union, IO
import io
import os

import pandas as pd
import tabulate

from .pdf_extract import extract_pdf_tables
from .pipeline import _process_dataframe  # reuse existing spreadsheet path


def run_ingestion_for_structured_pdf_stream(
    stream: IO[bytes],
    *,
    file_name: Optional[str] = None,
    pages: Optional[str] = None,
    dpi: int = 300,
    currency_override: Optional[str] = None,
    base_year_override: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Extract all tables from the PDF stream and ingest each as its own Table.
    """
    stream.seek(0)
    raw = stream.read()
    pdf_results = extract_pdf_tables(raw, pages=pages, dpi=dpi)

    agg_nodes = 0
    agg_rels = 0
    pine_stats: List[Dict[str, Any]] = []
    parsed_counts: List[Dict[str, int]] = []
    file_display = file_name or getattr(stream, "name", "uploaded.pdf")

    for t in pdf_results:
        df: pd.DataFrame = t["df"]
        page = t["meta"].get("page")
        flavor = t["meta"].get("flavor")
        title = f"page-{page}-{flavor}-table-{t['meta'].get('index',0)}"
        print(
            f"[INGEST:STRUCTURED PDF] - processing table '{title}' from '{file_display}'..."
        )
        print(f"[INGEST:STRUCTURED PDF] - data frame: {df.shape} > {df.head(10)}")
        # out = _process_dataframe(
        #     df,
        #     file_name=file_display,
        #     table_title=title,
        #     currency_override=currency_override,
        #     base_year_override=base_year_override,
        # )
        # agg_nodes += out["nodes_written"]
        # agg_rels += out["rels_written"]
        # pine_stats.append(out["pinecone"])
        # parsed_counts.append(out["parsed_counts"])
        
        print(f"[INGEST:STRUCTURED PDF] - data frame: {df.shape} > {df.head(10)}")
        # Print formatted table for inspection
        print("\n[DATAFRAME TABLE PREVIEW]")
        print(df.to_markdown(index=False, tablefmt="grid"))

    return {
        "file": file_display,
        "tables_found": len(pdf_results),
        "tables": pdf_results,
        # "nodes_written": agg_nodes,
        # "rels_written": agg_rels,
        # "pinecone": pine_stats,
        # "parsed_counts": parsed_counts,
    }


def run_ingestion_for_structured_pdf_path(
    path: str,
    *,
    pages: Optional[str] = None,
    dpi: int = 300,
    currency_override: Optional[str] = None,
    base_year_override: Optional[int] = None,
) -> Dict[str, Any]:
    with open(path, "rb") as f:
        return run_ingestion_for_structured_pdf_stream(
            f,
            file_name=os.path.basename(path),
            pages=pages,
            dpi=dpi,
            currency_override=currency_override,
            base_year_override=base_year_override,
        )
