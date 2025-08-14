from __future__ import annotations
import re, datetime
from typing import Iterable, Tuple, List

def now_iso() -> str:
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

# Very light numeric+unit extractor used by fallback KG extractor
def extract_numbers_with_units(text: str) -> List[Tuple[float, str]]:
    out = []
    for m in re.finditer(r"(\d[\d,\.]*?)\s*(kW|MW|t\/d|tpd|tph|kg|t|g\/t|ppm|%)\b", text, flags=re.I):
        try:
            val = float(m.group(1).replace(",", ""))
            unit = m.group(2)
            out.append((val, unit))
        except Exception:
            continue
    return out
