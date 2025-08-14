"""Costing functions: scale equipment costs to a target throughput."""
from typing import Dict, Any, List
# from ..ontology import DEFAULT_SCALING

def scale_capex(base_capex: float, base_tpd: float, target_tpd: float, exponent: float = None) -> float:
    # e = exponent if exponent is not None else DEFAULT_SCALING["CostCurve"]["capex_exponent"]
    # return float(base_capex) * (target_tpd / max(base_tpd,1.0)) ** e
    return None
def compute_cost_report(graph_rows: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
    """Very simple example: take first Equipment->CostCurve we find and scale it."""
    target_tpd = float(params.get("throughput_tpd", 0))
    for row in graph_rows:
        node = row.get("node") or {}
        cost = row.get("cost") or {}
        if node.get("labels", [""])[0] == "Equipment" or node.get("category") == "Equipment":
            if cost:
                capex = float(cost.get("capex_usd", 0))
                base_tpd = float(node.get("max_tpd", params.get("base_tpd", target_tpd or 1)))
                scaled = scale_capex(capex, base_tpd, target_tpd or base_tpd)
                return {
                    "estimate_capex_usd": round(scaled, 2),
                    "base_capex_usd": capex,
                    "base_tpd": base_tpd,
                    "target_tpd": target_tpd or base_tpd,
                    # "assumptions": {"capex_exponent": DEFAULT_SCALING["CostCurve"]["capex_exponent"]},
                }
    return {"note": "No cost curve found; provide more context or ingest cost data."}
