from typing import Dict, Any
def normalize_units(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Minimal demo normalizer: add your real conversions here.
    out = dict(payload)
    if "throughput" in out and "unit" in out:
        if out["unit"].lower() in {"tph","t/h"}:
            out["throughput_tpd"] = float(out["throughput"]) * 24.0
        elif out["unit"].lower() in {"tpd","t/day"}:
            out["throughput_tpd"] = float(out["throughput"])
    return out
