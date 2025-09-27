## File: `structured/transform.py`

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import re
import pandas as pd

from ..storage import GNode, GRel, GDoc
from .units import normalize_value, parse_currency_amount

# ---------------- Data containers ----------------

@dataclass
class TableRec:
    id: str
    source_file: str
    sheet: str
    title: str
    currency: str
    base_year: int

@dataclass
class RowRec:
    id: str
    table_id: str
    row_idx: int
    label_text: str
    cells: List[Dict[str, Any]]  # [{col, raw, value_num, uom, text}]
    attrs: Dict[str, Any]        # semantic attrs (family,size_code,hp,...)

@dataclass
class ParsedTable:
    table: TableRec
    rows: List[RowRec]
    counts: Dict[str, int]

# --------------- Helpers: recognize equipment rows ---------------
SIZE_RE = re.compile(r"(\d{2,3})\s*[x×-]\s*(\d{2,3})")
FAMILY_RE = re.compile(r"gyratory|jaw|cone|sag|ball", re.I)
HP_RE = re.compile(r"(\d{2,4})\s*hp", re.I)
MONEY_RE = re.compile(r"([\$€£])?\s*([0-9,]+(?:\.[0-9]+)?)")


# Map currency symbol → code
CURR = {"$": "USD", "€": "EUR", "£": "GBP"}


def _coerce_base_year(sheet_or_title: str, default: int = 2015) -> int:
    m = re.search(r"(19|20)\d{2}", sheet_or_title or "")
    return int(m.group(0)) if m else default


# --------------- Main parse ---------------

def parse_table_dataframe(
    df: pd.DataFrame,
    *,
    source_file: str,
    sheet: str,
    currency_override: Optional[str] = None,
    base_year_override: Optional[int] = None,
) -> Dict[str, Any]:
    """Converts a worksheet to `ParsedTable`.
    Handles two common formats:
      A) Cost table with Description/HP/Capital Cost columns
      B) Capacity matrix with Size rows (e.g., 54x75) and OSS columns (e.g., 7, 7.5, 8, 9 in)
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    table_id = f"tbl::{source_file.rsplit('/',1)[-1]}::{sheet}"
    base_year = base_year_override or _coerce_base_year(sheet)

    # Infer currency at table-level if the last column looks like money
    currency = currency_override or _infer_currency_from_df(df)

    table = TableRec(
        id=table_id,
        source_file=source_file,
        sheet=sheet,
        title=sheet,
        currency=currency or "USD",
        base_year=base_year,
    )

    rows: List[RowRec] = []

    # Strategy: if first column name contains 'size' or 'description' treat as label column
    label_col = df.columns[0]
    for i, r in df.iterrows():
        label_text = str(r.get(label_col, "")).strip()
        attrs: Dict[str, Any] = {}

        # detect family & size code in label
        fam_m = FAMILY_RE.search(label_text)
        if fam_m:
            attrs["family"] = fam_m.group(0).title()
        size_m = SIZE_RE.search(label_text.replace("–","-"))
        if size_m:
            attrs["size_code"] = f"{size_m.group(1)}x{size_m.group(2)}"
        hp_m = HP_RE.search(" ".join(str(x) for x in r.values))
        if hp_m:
            attrs["hp"] = int(hp_m.group(1))

        cells = []
        for col in df.columns[1:]:
            raw = r.get(col)
            value_num, uom, text = normalize_value(raw, header=col)
            cells.append({"col": col, "raw": raw, "value_num": value_num, "uom": uom, "text": text})

        # If a column looks like price, extract purchase cost
        purchase = None
        for c in cells:
            if _looks_price_col(c["col"]) and c["value_num"] is not None:
                amt, cur = parse_currency_amount(str(r.get(c["col"])), default_code=table.currency)
                if amt is not None:
                    purchase = {"amount": amt, "currency": cur or table.currency}
                break

        if purchase:
            attrs["purchase"] = purchase

        rows.append(RowRec(id=f"row::{table_id}::{i}", table_id=table_id, row_idx=int(i), label_text=label_text, cells=cells, attrs=attrs))

    parsed = ParsedTable(table=table, rows=rows, counts={"rows": len(rows), "cells": sum(len(r.cells) for r in rows)})
    return {"table": table.__dict__, "rows": [r.__dict__ for r in rows], "counts": parsed.counts}


def _looks_price_col(col: str) -> bool:
    s = str(col).lower()
    return any(k in s for k in ["capital", "cost", "price", "purchase"]) or s.endswith("$")


def _infer_currency_from_df(df: pd.DataFrame) -> Optional[str]:
    # scan headers and a few cells for symbols
    for c in list(df.columns) + list(df.head(5).astype(str).values.ravel()):
        m = MONEY_RE.search(str(c))
        if m and m.group(1) in CURR:
            return CURR[m.group(1)]
    return None


# --------------- Build graph (Table/Row/Cell + domain) ---------------

def build_graph_from_table(parsed: Dict[str, Any]) -> GDoc:
    table = parsed["table"]
    rows = parsed["rows"]

    nodes: List[GNode] = []
    rels: List[GRel] = []

    # Table node
    tnode = GNode(id=table["id"], type="Table", properties={k: table[k] for k in ["source_file","sheet","title","currency","base_year"]})
    nodes.append(tnode)

    for r in rows:
        rnode = GNode(id=r["id"], type="Row", properties={"row_idx": r["row_idx"], "label_text": r["label_text"], "table_id": r["table_id"]})
        nodes.append(rnode)
        rels.append(GRel(source=tnode, target=rnode, type="HAS_ROW", properties={}))

        # Cell nodes (only keep numeric cells; store uom)
        for c in r["cells"]:
            cid = f"cell::{r['id']}::{c['col']}"
            cnode = GNode(id=cid, type="Cell", properties={
                "column": c["col"],
                "raw": str(c["raw"]),
                "value_num": c["value_num"],
                "uom": c["uom"],
            })
            nodes.append(cnode)
            rels.append(GRel(source=rnode, target=cnode, type="HAS_CELL", properties={}))

        # Domain: Equipment (optional when recognizable)
        attrs = r.get("attrs") or {}
        eq_node = None
        if attrs.get("size_code") or attrs.get("family"):
            eq_id = f"equip::{attrs.get('family','Equipment')}::{attrs.get('size_code','unknown')}"
            eq_node = GNode(id=eq_id, type="Equipment", properties={
                "family": attrs.get("family"),
                "size_code": attrs.get("size_code"),
                "power_hp": attrs.get("hp"),
            })
            nodes.append(eq_node)
            rels.append(GRel(source=rnode, target=eq_node, type="EVIDENCES", properties={"source":"row"}))

        # Domain: CostEstimate node if purchase parsed
        if attrs.get("purchase"):
            p = attrs["purchase"]
            cost_id = f"cost::{eq_node.id if eq_node else r['id']}::{table['base_year']}::purchase"
            cnode = GNode(id=cost_id, type="CostEstimate", properties={
                "cost": p["amount"],
                "currency": p["currency"],
                "cost_type": "purchase",
                "cost_basis": "table",
                "base_year": table["base_year"],
            })
            nodes.append(cnode)
            if eq_node:
                rels.append(GRel(source=eq_node, target=cnode, type="HAS_COST", properties={}))
            # provenance links
            rels.append(GRel(source=rnode, target=cnode, type="EVIDENCES", properties={"source":"row"}))

    return GDoc(nodes=nodes, relationships=rels)


