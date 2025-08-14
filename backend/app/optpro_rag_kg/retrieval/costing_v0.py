"""Costing model hook: parse simple $ amounts (replace with domain model)."""
from __future__ import annotations
from typing import List, Dict, Any
import re

def _extract_currency_numbers(text: str) -> List[float]:
    nums = []
    for m in re.finditer(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)", text):
        try:
            nums.append(float(m.group(1).replace(",", "")))
        except Exception:
            pass
    return nums

def estimate_cost(matches: List[Dict[str, Any]], chunks: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    candidates: List[float] = []
    print("[COSTING] begin")
    for m in matches:
        md = m.get("metadata") or {}
        txt = (md.get("text") or "")
        if txt:
            candidates.extend(_extract_currency_numbers(txt))
    if chunks:
        for r in chunks:
            txt = (r.get("text") or "")
            if txt:
                candidates.extend(_extract_currency_numbers(txt))
    summary = {
        "samples_found": len(candidates),
        "sum_usd": round(sum(candidates), 2) if candidates else None,
        "min_usd": round(min(candidates), 2) if candidates else None,
        "max_usd": round(max(candidates), 2) if candidates else None,
        "samples": candidates[:20],
    }
    return summary
