## File: `structured/rowcards.py`

from __future__ import annotations
from typing import Dict, Any, List, Tuple
from ..storage import GNode, GRel


def _row_card_text(row: Dict[str, Any], table: Dict[str, Any]) -> str:
    a = row.get("attrs") or {}
    parts = []
    fam = a.get("family")
    size = a.get("size_code")
    hp = a.get("hp")
    if fam or size:
        parts.append(f"{fam or 'Equipment'} {size or ''}".strip())
    if hp:
        parts.append(f"HP: {hp}")
    # try to surface a few numeric cells
    cap_bits = []
    for c in row.get("cells", [])[:6]:
        col = str(c.get("col"))
        val = c.get("value_num")
        uom = c.get("uom")
        if val is not None and uom in ("t/h", "mm", None):
            cap_bits.append(f"{col}: {val:.0f}{' '+uom if uom else ''}")
    if cap_bits:
        parts.append("; ".join(cap_bits))
    # purchase
    p = a.get("purchase") or {}
    if p:
        parts.append(
            f"Purchase: {p.get('amount'):,} {p.get('currency') or table.get('currency')} ({table.get('base_year')})"
        )

    parts.append(f"Source: {table.get('source_file')} | {table.get('sheet')}")
    return " — ".join(parts)


def make_row_card_chunks(parsed: Dict[str, Any]) -> Dict[str, Any]:
    table = parsed["table"]
    rows = parsed["rows"]

    nodes: List[GNode] = []
    rels: List[GRel] = []
    chunks_for_pinecone: List[Dict[str, Any]] = []

    for i, r in enumerate(rows):
        chunk_id = f"chunk::{r['id']}"
        text = _row_card_text(r, table)
        # :Chunk node
        cnode = GNode(
            id=chunk_id,
            type="Chunk",
            properties={
                "chunk_id": chunk_id,
                "text": text,
                "seq": i,
                "table_id": table["id"],
                "row_id": r["id"],
            },
        )
        nodes.append(cnode)

        # Mention edges to Equipment/CostEstimate if present
        # (these nodes are created in transform.build_graph_from_table)
        if r.get("attrs", {}).get("size_code") or r.get("attrs", {}).get("family"):
            eq_id = f"equip::{r['attrs'].get('family','Equipment')}::{r['attrs'].get('size_code','unknown')}"
            rels.append(
                GRel(
                    source=cnode,
                    target=GNode(id=eq_id, type="Equipment", properties={}),
                    type="MENTIONS",
                    properties={"surface": r.get("label_text")},
                )
            )
        if r.get("attrs", {}).get("purchase"):
            cost_id = f"cost::{(eq_id if r.get('attrs').get('size_code') else r['id'])}::{table['base_year']}::purchase"
            rels.append(
                GRel(
                    source=cnode,
                    target=GNode(id=cost_id, type="CostEstimate", properties={}),
                    type="MENTIONS",
                    properties={"surface": "purchase"},
                )
            )

        # Pinecone chunk dict
        chunks_for_pinecone.append(
            {
                "chunk_id": chunk_id,
                "doc_id": table["id"],
                "seq": i,
                "text": text,
                "meta": {
                    "table_id": table["id"],
                    "row_id": r["id"],
                    "sheet": table.get("sheet"),
                    "family": r.get("attrs", {}).get("family"),
                    "size_code": r.get("attrs", {}).get("size_code"),
                    "base_year": table.get("base_year"),
                    "currency": table.get("currency"),
                    "source_file": table.get("source_file"),
                },
            }
        )
    print(f"[INGEST 3] - Created {len(nodes)} row-card Chunk nodes and {len(rels)} MENTIONS edges.")
    return {
        "nodes": nodes,
        "relationships": rels,
        "chunks_for_pinecone": chunks_for_pinecone,
    }
