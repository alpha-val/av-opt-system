# in_pipeline/costing.py
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import math
import re

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
UNIT_PAIR_RE = re.compile(r"^\s*([-\d.,]+)\s*([A-Za-z/%\"-]+)?\s*$")


def _to_float(x: Any, default: float = 0.0) -> float:
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    m = NUM_RE.search(s)
    if not m:
        return default
    try:
        return float(m.group(0).replace(",", ""))
    except Exception:
        return default


def _parse_value_unit(x: Any) -> Tuple[float, str]:
    """Return (value, unit) from strings like '1000 tph', '720 kW', '90%'."""
    if x is None:
        return 0.0, ""
    if isinstance(x, (int, float)):
        return float(x), ""
    s = str(x).strip()
    m = UNIT_PAIR_RE.match(s)
    if not m:
        return _to_float(s), ""
    val = _to_float(m.group(1))
    unit = (m.group(2) or "").strip()
    return val, unit


def _percent_to_frac(x: Any, default: float = 1.0) -> float:
    v, u = _parse_value_unit(x)
    if "%" in (u or "") or (isinstance(x, str) and "%" in x):
        return max(0.0, min(1.0, v / 100.0))
    # If someone passes 0–1 already, accept it; if >1, assume already a frac?
    if v <= 1.0:
        return v if v > 0 else default
    # Otherwise treat as %, e.g., 90 -> 0.9
    return v / 100.0


def _tpd_from_capacity(props: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """
    Derive tpd from system_capacity and availability if present.
    Accepts '1000 tph', '20,000 tpd', etc. Defaults to 24h*availability for tph.
    """
    capacity_raw = props.get("system_capacity") or props.get("capacity") or ""
    val, unit = _parse_value_unit(capacity_raw)
    availability = _percent_to_frac(props.get("availability_target", 0.9), 0.9)

    tpd = 0.0
    if "tpd" in unit.lower():
        tpd = val
    elif "tph" in unit.lower() or "t/h" in unit.lower():
        tpd = val * 24.0 * availability
    elif "tpa" in unit.lower():  # per annum
        tpd = val / 365.0
    else:
        # unknown unit: leave as is (assume already tpd if sensible)
        tpd = val

    return tpd, {"system_capacity": capacity_raw, "availability": availability}


def scale_capex(
    base_capex: float, base_tpd: float, target_tpd: float, exponent: float = 0.6
) -> float:
    """Scale CAPEX by capacity using a cost curve exponent (default 0.6)."""
    if base_tpd <= 0 or target_tpd <= 0:
        return float(base_capex)
    return float(base_capex) * (target_tpd / max(base_tpd, 1.0)) ** float(exponent)


def _sum_known_civil_costs(props: Dict[str, Any]) -> float:
    """
    Sum obvious line items from Installation/Civil equipment nodes.
    You can expand this list as you ingest more components.
    """
    keys = [
        "site_prep",
        "transport_rigging",
        "buildings_walkways_fencing",
        "foundations",
        "civils",
        "electrical_install",
        "mechanical_install",
        "structural_steel",
        "contingency",
    ]
    total = 0.0
    for k in keys:
        total += _to_float(props.get(k, 0.0))
    return total


def _extract_project(nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for n in nodes:
        if "Project" in (n.get("labels") or []):
            return n
    return None


def _equipment_nodes_linked_to_project(
    graph: Dict[str, Any], project_node_id: str
) -> List[Dict[str, Any]]:
    nodes = graph.get("nodes", [])
    rels = graph.get("relationships", [])
    id2node = {n["id"]: n for n in nodes}
    linked = []
    for r in rels:
        if r.get("type") == "USES_EQUIPMENT" and r.get("start") == project_node_id:
            eq = id2node.get(r.get("end"))
            if eq and "Equipment" in (eq.get("labels") or []):
                linked.append(eq)
    return linked


def estimate_cost(
    graph: Dict[str, Any], params: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Build a cost estimate from your RAG graph:
    - Use Project.estimated_cost if present
    - Otherwise sum civil/installation components from linked Equipment
    - Optionally scale to target throughput (tpd) with exponent
    - Add simple power OPEX estimate if power + electricity_rate provided
    """
    print("[DEBUG] estimate_cost called with params:", params)
    params = params or {}
    nodes = graph.get("nodes", [])
    rels = graph.get("relationships", [])

    proj = _extract_project(nodes)
    if not proj:
        return {"note": "No Project node found.", "estimate": None}

    pprops = proj.get("props", {}) or {}
    # Base throughput:
    base_tpd, cap_info = _tpd_from_capacity(pprops)
    target_tpd = float(params.get("throughput_tpd") or base_tpd or 0.0)
    exponent = float(params.get("capex_exponent", 0.6))

    # CAPEX sources
    proj_est_capex = _to_float(pprops.get("estimated_cost"))
    # Civil/installation roll-up from linked Equipment:
    equipment = _equipment_nodes_linked_to_project(graph, proj["id"])
    civils_sum = 0.0
    civils_items = []
    for eq in equipment:
        s = _sum_known_civil_costs(eq.get("props", {}) or {})
        if s > 0:
            civils_sum += s
            civils_items.append({"equipment": eq["props"].get("name"), "sum": s})

    # Choose a base to scale from
    base_capex = proj_est_capex if proj_est_capex > 0 else civils_sum
    base_used = (
        "project.estimated_cost"
        if proj_est_capex > 0
        else "sum(civil/installation lines)"
    )

    # Determine base_tpd for scaling:
    base_for_scale = float(params.get("base_tpd") or base_tpd or target_tpd or 0.0)

    # Scaled CAPEX
    if target_tpd > 0 and base_for_scale > 0 and base_capex > 0:
        capex_scaled = scale_capex(base_capex, base_for_scale, target_tpd, exponent)
    else:
        capex_scaled = base_capex

    # Simple power OPEX (optional)
    power_kw, _ = _parse_value_unit(pprops.get("total_power_required"))
    elec_rate = float(params.get("electricity_rate", 0.08))  # $/kWh
    availability = cap_info.get("availability", 0.9)
    hours_per_year = 24.0 * 365.0 * availability
    annual_power_opex = power_kw * hours_per_year * elec_rate if power_kw > 0 else 0.0

    return {
        "project": {
            "name": pprops.get("name"),
            "location": pprops.get("location"),
            "ore_type": pprops.get("ore_type"),
        },
        "throughput": {
            "base_tpd": base_for_scale,
            "target_tpd": target_tpd,
            "availability_frac": availability,
            "capacity_field": cap_info.get("system_capacity"),
        },
        "capex": {
            "base_source": base_used,
            "base_capex_usd": round(base_capex, 2),
            "capex_exponent": exponent,
            "scaled_capex_usd": round(capex_scaled, 2),
            "civils_breakdown": civils_items,
        },
        "opex": {
            "annual_power_kw": power_kw,
            "electricity_rate_per_kwh": elec_rate,
            "estimated_annual_power_opex_usd": round(annual_power_opex, 2),
        },
        "assumptions": {
            "scaling_curve": "CAPEX ~ (TPD)^exponent",
            "fallback": "If project.estimated_cost is missing, sum civil/installation components from linked Equipment.",
        },
    }
