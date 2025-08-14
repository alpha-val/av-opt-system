"""LangExtract -> Neo4j conversion wired to Chunk metadata."""

from __future__ import annotations
from typing import Iterable, Dict, Any, List
from neo4j import GraphDatabase, Driver
from ..config_adapter import SETTINGS
from ..utils.logging import get_logger
import re

log = get_logger(__name__)


class Neo4jStore:
    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ):
        self.driver: Driver = GraphDatabase.driver(
            uri or SETTINGS.neo4j_uri,
            auth=(user or SETTINGS.neo4j_user, password or SETTINGS.neo4j_password),
        )

    @staticmethod
    def _safe_get(obj: Any, key: str, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        try:
            return getattr(obj, key, default)
        except Exception:
            return default

    @staticmethod
    def to_camel_case(s):
        """Convert string to CamelCase (e.g., 'cost_rule' -> 'CostRule')"""
        if not s:
            return ""
        # Replace underscores/hyphens with spaces, split, capitalize, join
        return "".join(word.capitalize() for word in re.split(r"[_\-\s]+", s))



    @staticmethod
    def _get(obj: Any, key: str):
        if isinstance(obj, dict):
            return obj.get(key)
        try:
            return getattr(obj, key)
        except Exception:
            return None

    def close(self):
        self.driver.close()

    def run(self, cypher: str, **params):
        with self.driver.session() as s:
            return s.run(cypher, **params)

    # Writes
    def upsert_section_mentions(
        self, doc_id: str, section_id: str, title: str, entity_ids: Iterable[str]
    ):
        cypher = """
        MERGE (d:Document {id:$doc_id})
        MERGE (s:Section {id:$section_id})-[:PART_OF]->(d)
        SET s.title = $title
        WITH s
        UNWIND $entity_ids AS eid
        MERGE (e:Entity {id:eid})
        MERGE (s)-[:MENTIONS]->(e)
        """
        self.run(
            cypher,
            doc_id=doc_id,
            section_id=section_id,
            title=title,
            entity_ids=list(entity_ids),
        )

    def upsert_equipment(self, eq: Dict[str, Any]):
        self.run(
            "MERGE (e:Equipment {id:$id}) SET e += $props",
            id=eq["id"],
            props={k: v for k, v in eq.items() if k != "id"},
        )

    def connect_equipment_cost(self, eq_id: str, cost: Dict[str, Any]):
        cypher = """
        MERGE (c:CostCurve {id:$cid}) SET c += $cprops
        WITH c MATCH (e:Equipment {id:$eid}) MERGE (e)-[:HAS_COST]->(c)
        """
        self.run(
            cypher,
            cid=cost["id"],
            cprops={k: v for k, v in cost.items() if k != "id"},
            eid=eq_id,
        )

    # Reads
    def expand_from_entities(
        self, entity_ids: List[str], hop: int = 2, limit: int = 200
    ):
        cypher = f"""
        MATCH (e:Entity) WHERE e.id IN $entity_ids
        MATCH (e)-[r*1..{hop}]-(n)
        WITH DISTINCT e,n LIMIT $limit
        OPTIONAL MATCH (n)-[:HAS_COST]->(c:CostCurve)
        RETURN e,n,c
        """
        return list(self.run(cypher, entity_ids=entity_ids, limit=limit))

    
    def langextract_to_neo4j_format_0(
        self, graph_docs: Any
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Polymorphic converter.
        Accepts:
        1) A dict with keys 'nodes','relationships','mentions' (already normalized)
        2) A list/dict object with those keys
        3) A raw list of LangExtract Extraction objects (extraction_class in {'NODE','RELATIONSHIP'})
        Returns dict {nodes:[...], relationships:[...], mentions:[...]} where:
        nodes item: {"labels":["Node"], "key":{"name": str, "type": str}, "props": {...}}
        relationships item: {"type": str, "start": {...}, "end": {...}, "props": {...}}
        """
        # Case 1: already normalized dict
        if isinstance(graph_docs, dict) and (
            "nodes" in graph_docs or "relationships" in graph_docs
        ):
            raw_nodes = graph_docs.get("nodes", [])
            raw_rels = graph_docs.get("relationships", [])
            raw_mentions = graph_docs.get("mentions", [])
        # Case 2: raw list of Extraction objects
        elif (
            isinstance(graph_docs, list)
            and graph_docs
            and hasattr(graph_docs[0], "extraction_class")
        ):
            raw_nodes, raw_rels, raw_mentions = self._from_extractions(graph_docs)
        else:
            # Fallback treat as empty
            raw_nodes, raw_rels, raw_mentions = [], [], []

        nodes_rows: List[Dict[str, Any]] = []
        rel_rows: List[Dict[str, Any]] = []
        mentions_rows: List[Dict[str, Any]] = []

        for n in raw_nodes:
            n_type = self._get(n, "type") or (self._get(n, "label")) or "Node"
            props = self._get(n, "properties") or self._get(n, "props") or {}
            name = (
                props.get("name")
                or self._get(n, "id")
                or props.get("label")
                or props.get("title")
                or "UNKNOWN"
            )
            nodes_rows.append(
                {
                    "labels": [n_type],
                    "key": {"name": str(name), "type": str(n_type)},
                    "props": dict(props),
                }
            )

        for r in raw_rels:
            rtype = (
                self._get(r, "type")
                or (r.get("properties", {}) if isinstance(r, dict) else {}).get("label")
                or "RELATED"
            )
            s = self._get(r, "source") or self._get(r, "start") or {}
            t = self._get(r, "target") or self._get(r, "end") or {}
            if not isinstance(s, dict):
                s = {
                    "id": getattr(s, "id", None),
                    "type": getattr(s, "type", None),
                    "properties": getattr(s, "properties", {}) or {},
                }
            if not isinstance(t, dict):
                t = {
                    "id": getattr(t, "id", None),
                    "type": getattr(t, "type", None),
                    "properties": getattr(t, "properties", {}) or {},
                }
            s_name = (
                (s.get("properties", {}) or {}).get("name") or s.get("id") or "UNKNOWN"
            )
            s_type = s.get("type") or "Node"
            t_name = (
                (t.get("properties", {}) or {}).get("name") or t.get("id") or "UNKNOWN"
            )
            t_type = t.get("type") or "Node"
            rel_rows.append(
                {
                    "type": str(rtype),
                    "start": {
                        "labels": ["Node"],
                        "key": {"name": str(s_name), "type": str(s_type)},
                    },
                    "end": {
                        "labels": ["Node"],
                        "key": {"name": str(t_name), "type": str(t_type)},
                    },
                    "props": self._get(r, "properties") or self._get(r, "props") or {},
                }
            )

        for m in raw_mentions:
            cidx = m.get("chunk_idx")
            ent = m.get("entity") or {}
            if cidx is None or not ent:
                continue
            name = ent.get("name")
            etype = ent.get("type", "Node")
            if not name:
                continue
            mentions_rows.append(
                {
                    "chunk_idx": int(cidx),
                    "entity": {"name": str(name), "type": str(etype)},
                }
            )

        return {
            "nodes": nodes_rows,
            "relationships": rel_rows,
            "mentions": mentions_rows,
        }

    def _from_extractions(self, extractions: List[Any]):
        """
        Convert raw LangExtract Extraction objects into primitive node / relationship lists.
        Each extraction has:
        .extraction_class in {'NODE','RELATIONSHIP'}
        .extraction_text
        .attributes (dict)
        """
        nodes = []
        rels = []
        mentions = []
        for ex in extractions:
            cls = getattr(ex, "extraction_class", None)
            attrs = getattr(ex, "attributes", {}) or {}
            text_id = getattr(ex, "extraction_text", None)
            if cls == "NODE":
                node_type = attrs.get("label") or attrs.get("type") or "Node"
                props = dict(attrs)
                # ensure id & name
                node_id = (
                    text_id
                    or props.get("name")
                    or props.get("label")
                    or f"node_{len(nodes)+1}"
                )
                if "name" not in props and node_id:
                    props["name"] = node_id
                nodes.append(
                    {
                        "id": node_id,
                        "type": node_type,
                        "properties": props,
                    }
                )
            elif cls == "RELATIONSHIP":
                rel_type = attrs.get("label") or attrs.get("type") or "RELATED"
                source = attrs.get("source")
                target = attrs.get("target")
                if source and target:
                    rels.append(
                        {
                            "type": rel_type,
                            "source": {
                                "id": source,
                                "type": None,
                                "properties": {"name": source},
                            },
                            "target": {
                                "id": target,
                                "type": None,
                                "properties": {"name": target},
                            },
                            "properties": dict(attrs),
                        }
                    )
            elif cls == "MENTION":
                mentions.append(
                    {
                        "chunk_idx": attrs.get("chunk_idx"),
                        "entity": {
                            "name": attrs.get("name"),
                            "type": attrs.get("type", "Node"),
                        },
                    }
                )
        return nodes, rels, mentions

    def build_neo4j_graph(self, graph_docs: Any) -> Dict[str, Any]:
        converted = self.langextract_to_neo4j_format(graph_docs)
        return {
            "graph": {
                "nodes": converted["nodes"],
                "relationships": converted["relationships"],
            },
            "mentions": converted.get("mentions", []),
        }
