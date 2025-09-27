## File: `structured/units.py`

from __future__ import annotations
from typing import Tuple, Optional
import re

# Basic normalization without external deps

LEN = {"in": 25.4, "inch": 25.4, "mm": 1.0}
MASS = {"lb": 0.45359237, "lbs": 0.45359237, "kg": 1.0}
FLOW = {"stph": 0.90718474, "stpd": 0.90718474 / 24.0, "tph": 1.0}  # short ton/h → t/h
POWER = {"hp": 0.7457, "kw": 1.0}

MONEY_RE = re.compile(r"([\$€£])?\s*([0-9,]+(?:\.[0-9]+)?)")
CURR = {"$": "USD", "€": "EUR", "£": "GBP"}


def normalize_value(
    raw, *, header: str = ""
) -> Tuple[Optional[float], Optional[str], str]:
    """Attempt to produce a numeric canonical value + unit from a cell.
    Returns (value_num_in_SI, uom, text). Unknown → (None, None, str(raw)).
    """
    if raw is None or (isinstance(raw, float) and str(raw) == "nan"):
        return None, None, ""

    s = str(raw).strip()
    low = s.lower()

    # Capacity (stph) hinted by header
    if any(k in header.lower() for k in ["stph", "stpd", "capacity", "tph"]):
        # pure number → assume stph if header says stph; else tph
        try:
            v = float(s.replace(",", ""))
            if "stph" in header.lower():
                return v * FLOW["stph"], "t/h", s
            if "stpd" in header.lower():
                return v * FLOW["stpd"], "t/h", s
            return v, "t/h", s
        except Exception:
            pass

    # Length columns (in, mm)
    if any(
        k in header.lower() for k in ["in.", "in ", "oss", "opening", "inches", "mm"]
    ):
        try:
            v = float(s.replace(",", ""))
            if "mm" in header.lower():
                return v, "mm", s
            return v * LEN["in"], "mm", s
        except Exception:
            pass

    # HP columns
    if "hp" in header.lower():
        try:
            v = float(s)
            return v * POWER["hp"], "kW", s
        except Exception:
            pass

    # Generic numeric
    try:
        v = float(s.replace(",", ""))
        return v, None, s
    except Exception:
        pass

    return None, None, s


def parse_currency_amount(
    s: str, *, default_code: Optional[str] = None
) -> Tuple[Optional[float], Optional[str]]:
    if not s:
        return None, default_code
    m = MONEY_RE.search(str(s))
    if not m:
        try:
            return float(str(s).replace(",", "")), default_code
        except Exception:
            return None, default_code
    sym, num = m.group(1), m.group(2)
    try:
        amt = float(num.replace(",", ""))
    except Exception:
        return None, default_code
    code = CURR.get(sym) or default_code
    return amt, code
