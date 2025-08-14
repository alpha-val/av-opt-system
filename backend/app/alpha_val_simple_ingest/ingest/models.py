from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple


@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    filename: str
    text: str
    page_start: int
    page_end: int
    section_path: str | None = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphDoc:
    nodes: List[Node] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
