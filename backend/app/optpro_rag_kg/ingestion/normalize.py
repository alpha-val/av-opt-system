"""Normalization: units, synonyms, and stable IDs minted upstream/downstream."""
from typing import Dict, Any
from ..utils.units import normalize_units

def normalize_payload(meta: Dict[str, Any]) -> Dict[str, Any]:
    return normalize_units(meta)
