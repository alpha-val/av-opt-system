# mentions_from_openai.py
# -------------------------------------------------------------------
# Build Chunk->MENTIONS records using your LLM extractor:
# `openai_extract_nodes_rels(text, **kwargs)` from extract_with_openai.py
#
# Output schema (per mention):
# {
#   "chunk_id": str,
#   "entity_id": str,          # stable id
#   "entity_label": str,       # "Equipment" | "Process" | ...
#   "span_start": int|None,
#   "span_end": int|None,
#   "surface": str|None,
#   "conf": float|None
# }
# -------------------------------------------------------------------

from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import hashlib
import re
import unicodedata

# Your extractor
from .extract_with_openai import openai_extract_nodes_rels  # <- provided by you


# -----------------------------
# Public entry point
# -----------------------------


def generate_mentions_from_chunks(
    chunks: Sequence[Dict[str, Any]],
    *,
    allowed_labels: Sequence[str] = (
        "Equipment",
        "Process",
        "Material",
        "Scenario",
        "Project",
        "Entity",
    ),
    default_label: str = "Entity",
    extractor_kwargs: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Call your LLM extractor per chunk and convert returned nodes to MENTIONS rows.

    Args:
      chunks: [{chunk_id, text, ...}, ...]  (requires chunk_id, text)
      allowed_labels: restrict/normalize entity labels to these
      default_label: fallback label when extractor doesn't provide one
      extractor_kwargs: forwarded to openai_extract_nodes_rels

    Returns:
      List of mention dicts ready for Neo4j UNWIND.
    """
    extractor_kwargs = extractor_kwargs or {}
    mentions: List[Dict[str, Any]] = []

    for ch in chunks:
        chunk_id = ch.get("chunk_id")
        text = ch.get("text") or ""
        if not chunk_id or not text:
            continue

        try:
            result = openai_extract_nodes_rels(text=text, **extractor_kwargs)
        except Exception as e:
            # Don't fail the whole doc on one chunk
            print(f"[WARN] extractor failed for chunk {chunk_id}: {e}")
            continue

        # Accept a variety of shapes: dict with 'nodes', or tuple (nodes, rels), etc.
        nodes = _pull_nodes(result)

        # Convert nodes → mentions (zero, one, or many per node depending on span matches)
        for node in nodes:
            norm = _normalize_node(node, allowed_labels, default_label)
            if not norm:
                continue

            # Try to find spans for node surfaces; emit one mention per match
            found_any = False
            for surface, conf_base in _candidate_surfaces(node, norm["name"]):
                for s, e, matched in _find_all_spans(text, surface):
                    mentions.append(
                        {
                            "chunk_id": chunk_id,
                            "entity_id": norm["entity_id"],
                            "entity_label": norm["label"],
                            "span_start": s,
                            "span_end": e,
                            "surface": matched,
                            "conf": _resolve_confidence(node, conf_base),
                        }
                    )
                    found_any = True

            # If no span found, still emit a single mention (span-less provenance)
            if not found_any:
                mentions.append(
                    {
                        "chunk_id": chunk_id,
                        "entity_id": norm["entity_id"],
                        "entity_label": norm["label"],
                        "span_start": None,
                        "span_end": None,
                        "surface": norm["name"],
                        "conf": _resolve_confidence(node, 0.65),
                    }
                )

    return _dedupe_mentions(mentions)


# -----------------------------
# Helpers: normalize extractor output
# -----------------------------


def _pull_nodes(result: Any) -> List[Dict[str, Any]]:
    """
    Accepts common shapes:
      - {"nodes": [...], "rels": [...]}
      - {"nodes": [...]}
      - (nodes, rels)
      - [...]
    """
    if result is None:
        return []
    if isinstance(result, dict) and "nodes" in result:
        return list(result.get("nodes") or [])
    if isinstance(result, (list, tuple)):
        if len(result) == 2 and isinstance(result[0], list):
            return list(result[0])
        if isinstance(result, list):
            # Maybe the extractor already returns just the nodes
            return result
    # Unknown shape
    return []


def _normalize_node(
    node: Dict[str, Any], allowed_labels: Sequence[str], default_label: str
) -> Optional[Dict[str, Any]]:
    """
    Unify fields: id, label, name. Returns None if cannot determine name.
    """
    # name/title/text
    name = (
        node.get("name") or node.get("title") or node.get("surface") or node.get("text")
    )
    if not name or not str(name).strip():
        return None
    name = str(name).strip()

    # label/type/category
    raw_label = (
        node.get("label") or node.get("type") or node.get("category") or default_label
    )
    raw_label = str(raw_label).strip()

    label = _coerce_label(raw_label, allowed_labels, default_label)

    # stable entity id
    entity_id = (
        node.get("id") or node.get("entity_id") or _build_entity_id(label, name, node)
    )

    return {"name": name, "label": label, "entity_id": entity_id}


def _coerce_label(raw: str, allowed: Sequence[str], default_label: str) -> str:
    # simple normalization and aliasing
    r = raw.lower()
    alias_map = {
        "equip": "Equipment",
        "equipment": "Equipment",
        "process": "Process",
        "proc": "Process",
        "material": "Material",
        "mat": "Material",
        "scenario": "Scenario",
        "project": "Project",
        "entity": "Entity",
        "thing": "Entity",
    }
    label = alias_map.get(r, raw.title())
    if label not in allowed:
        return default_label
    return label


def _build_entity_id(label: str, name: str, node: Dict[str, Any]) -> str:
    """
    Deterministic id using label + normalized name (+ optional domain hints if provided).
    Format: <label>:<slug>-<sha1_8>
    """
    norm = _normalize_for_id(name)
    hint = ""
    for k in ("unit", "spec", "source", "std"):
        if node.get(k):
            hint += f"|{str(node[k]).strip()}"
    h = hashlib.sha1(f"{label}|{norm}{hint}".encode("utf-8")).hexdigest()[:8]
    return f"{label.lower()}:{_slugify(name)}-{h}"


# -----------------------------
# Span finding & surfaces
# -----------------------------


def _candidate_surfaces(
    node: Dict[str, Any], fallback_name: str
) -> Iterable[Tuple[str, float]]:
    """
    Yield (surface_string, base_confidence) candidates to search in text.
    Includes name + aliases/synonyms if present.
    """
    yielded = set()

    def _push(s: Optional[str], conf: float):
        s = (s or "").strip()
        if not s:
            return
        key = s.lower()
        if key in yielded:
            return
        yielded.add(key)
        yield (s, conf)

    # prefer exact 'surface' if provided
    surface = node.get("surface")
    if surface:
        yield from _push(surface, 0.9)

    # main name
    yield from _push(node.get("name") or fallback_name, 0.88)

    # aliases, synonyms, abbreviations
    for key in ("aliases", "alias", "synonyms", "abbrev", "abbreviation"):
        val = node.get(key)
        if isinstance(val, str):
            yield from _push(val, 0.82)
        elif isinstance(val, (list, tuple)):
            for v in val:
                yield from _push(str(v), 0.82)


def _find_all_spans(text: str, needle: str) -> List[Tuple[int, int, str]]:
    """
    Find all occurrences of needle in text (case-insensitive), allowing
    flexible whitespace/hyphen variants.
    """
    if not text or not needle:
        return []

    # Exact first
    spans = []
    for m in re.finditer(re.escape(needle), text, flags=re.IGNORECASE):
        spans.append((m.start(), m.end(), text[m.start() : m.end()]))

    # If none, try flexible matching:
    if not spans:
        pat = _flex_pattern(needle)
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            spans.append((m.start(), m.end(), text[m.start() : m.end()]))

    return spans


def _flex_pattern(needle: str) -> str:
    """
    Build a regex that treats spaces and hyphens interchangeably and collapses multiple spaces.
    E.g., "open side setting" -> r"open[\s\-]+side[\s\-]+setting"
    """
    toks = re.split(r"\s+", needle.strip())
    toks = [re.escape(t) for t in toks if t]
    if not toks:
        return re.escape(needle)
    return r"(?:" + r"[\s\-]+".join(toks) + r")"


# -----------------------------
# Misc utils
# -----------------------------


def _normalize_for_id(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _slugify(s: str) -> str:
    s = _normalize_for_id(s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _resolve_confidence(node: Dict[str, Any], base: float) -> float:
    """
    If extractor provided a confidence, blend it lightly with base.
    """
    raw = node.get("confidence") or node.get("conf") or node.get("score")
    try:
        rawf = float(raw)
        # weighted avg to keep span-type signal
        return round(min(1.0, 0.6 * base + 0.4 * rawf), 4)
    except (TypeError, ValueError):
        return round(base, 4)


def _dedupe_mentions(mentions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove exact duplicates (same chunk_id, entity_id, start, end).
    """
    seen = set()
    out = []
    for m in mentions:
        key = (m["chunk_id"], m["entity_id"], m.get("span_start"), m.get("span_end"))
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
    return out


# -----------------------------
# Convenience: one-shot adapter
# -----------------------------


def build_mentions_for_ingest(
    produced_chunks: Sequence[Dict[str, Any]],
    *,
    extractor_kwargs: Optional[Dict[str, Any]] = None,
    allowed_labels: Sequence[str] = (
        "Equipment",
        "Process",
        "Material",
        "Scenario",
        "Project",
        "Entity",
    ),
    default_label: str = "Entity",
) -> List[Dict[str, Any]]:
    """
    Thin wrapper if your pipeline already has `produced_chunks` with {chunk_id, text, ...}
    """
    return generate_mentions_from_chunks(
        produced_chunks,
        allowed_labels=allowed_labels,
        default_label=default_label,
        extractor_kwargs=extractor_kwargs,
    )
