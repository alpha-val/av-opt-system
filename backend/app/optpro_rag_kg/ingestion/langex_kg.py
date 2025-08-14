"""LangExtract wrapper (user to plug in real call; no OpenAI)."""

from __future__ import annotations
import langextract as lx
# from langchain_community.graphs import Neo4jGraph
from langchain_neo4j import Neo4jGraph
from langchain_community.graphs.graph_document import Node, Relationship, GraphDocument
from langchain_core.documents import Document
from typing import Any, Dict, List
from ..config_adapter import SETTINGS

# from ..graph.neo4j_utils import langextract_to_neo4j_format, build_neo4j_graph
from ..prompt.build_prompt import gen_prompt
import os, re, unicodedata
from ..utils.logging import get_logger
from ..ontology import load_ontology

log = get_logger(__name__)


def _normalize_chunk_text(t: str) -> str:
    if not t:
        return ""
    # Unicode normalization & thin spaces
    t = unicodedata.normalize("NFC", t).replace("\u2009", " ").replace("\ufeff", "")
    # Standardize bullets
    t = t.replace("●", "•")
    # Collapse pattern: newline + (only spaces or a single space line) + newline => single space
    # This removes the per‑word line breaks pattern: "Word\n \nNext"
    t = re.sub(r"\n[ \t]*\n", " ", t)
    # Remove leftover isolated newlines immediately followed by lowercase/number (word wraps)
    t = re.sub(r"\n(?=[a-z0-9])", " ", t)
    # Compress multiple spaces
    t = re.sub(r"[ \t]{2,}", " ", t)
    # Restore paragraph breaks where we accidentally flattened true blank lines:
    # Heuristic: if we flattened a period followed by a capital, keep as is (fine for LLMs).
    # Ensure bullets start on new line
    t = re.sub(r"\s*•\s*", "\n• ", t)
    return t.strip()


class KGExtractor:
    def __init__(
        self, model_name: str = "gemini-2.5-flash", ontology: Dict[str, Any] | None = None
    ):
        self.model_name = model_name
        self.ontology = load_ontology() or {}
        node_prop_examples = self.ontology.get("NODE_PROP_EXAMPLES", {})
        self.prompt = gen_prompt(self.ontology)
        self.lx_examples = [
            lx.data.ExampleData(
                text="Project Type: Jaw Crusher Installation Location: Carson City Nevada Capacity: 1,000 tph Moisture: 3% Availability: 90%",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="NODE",
                        extraction_text="jaw_crusher_installation",
                        attributes={
                            "label": "PROJECT",
                            **node_prop_examples,
                        },
                    ),
                    lx.data.Extraction(
                        extraction_class="RELATIONSHIP",
                        extraction_text="<link_id_1>",
                        attributes={
                            "label": "USES",
                            "source": "jaw_crusher",
                            "target": "rock",
                            "directionality": "one-way",
                        },
                    ),
                ],
            )
        ]

    @staticmethod
    def _is_fake_chunk_node(n: Dict[str, Any]) -> bool:
        """
        Detect nodes that are really chunk placeholders accidentally extracted as entities.

        Supports both raw extraction -> converted node shapes:
          Raw (possible):
            {"id": "...", "type": "Chunk", "properties": {"name":"chunk:0", ...}}
          Converted (from langextract_to_neo4j_format):
            {"labels":["Node"], "key":{"name":"chunk:0","type":"Chunk"}, "props":{...}}
        """
        if not isinstance(n, dict):
            return False

        # Try every location a 'type' could live
        type_candidates = [
            n.get("type"),
            (n.get("key") or {}).get("type"),
            (n.get("properties") or {}).get("type"),
            (n.get("props") or {}).get("type"),
        ]
        t = next((str(x).lower() for x in type_candidates if x), "")

        # Extract name / id across possible shapes
        name_candidates = [
            (n.get("properties") or {}).get("name"),
            (n.get("props") or {}).get("name"),
            (n.get("key") or {}).get("name"),
            n.get("id"),
        ]
        name = next((str(x).lower() for x in name_candidates if x), "")
        print(f"(> Name and type: {name}, {t})")
        # Heuristics for fake chunk nodes
        if t == "chunk":
            return True
        if name.startswith("chunk:") or name.startswith("chunk_"):
            return True
        if name.startswith("page ") or name.startswith("page:"):
            return True
        return False

    @staticmethod
    def to_camel_case(s):
        """Convert string to CamelCase (e.g., 'cost_rule' -> 'CostRule')"""
        if not s:
            return ""
        # Replace underscores/hyphens with spaces, split, capitalize, join
        return "".join(word.capitalize() for word in re.split(r"[_\-\s]+", s))

    @staticmethod
    def _to_document(payload: Union[str, bytes]) -> Document:
        """Normalise text / bytes to a langchain Document."""
        if isinstance(payload, bytes):
            text = payload.decode("utf-8", errors="replace")
        elif isinstance(payload, str):
            text = payload
        else:
            raise TypeError(
                f"Unsupported type {type(payload)} – expected str or bytes."
            )
        return Document(page_content=text, metadata={"source": "graph_ingest"})

    def build_graph_from_chunks(
        self,
        chunks: List[Any],
        join_delimiter: str = "\n\n",  # (kept signature; unused now)
    ) -> Dict[str, Any]:
        """
        Chunk-wise extraction (no giant concatenation).

        For each chunk:
          1. Normalize text.
          2. Run LangExtract on that chunk only.
          3. Convert extractions -> neo4j-ish node/relationship dicts.
          4. Accumulate nodes / relationships.
          5. Emit a mention record for each node surfaced in that chunk.

        Returns:
            {
              "nodes": [...],            # raw aggregated nodes (not deduped)
              "relationships": [...],    # raw aggregated relationships
              "mentions": [ {chunk_idx, entity:{id,name,type}} , ... ]
            }

        NOTE: You can deduplicate nodes/relationships downstream (e.g. by id or (name,type)).
        """
        
        if not chunks:
            return {"nodes": [], "relationships": [], "mentions": []}

        all_nodes: List[Dict[str, Any]] = []
        all_rels: List[Dict[str, Any]] = []
        mentions: List[Dict[str, Any]] = []

        log.info("[KGExtractor] Iterating through chunks...")
        for idx, ch in enumerate(chunks):
            # Derive stable chunk index (prefer attribute if present)
            chunk_idx = ch.get("id")
            input_text = ch.get("text")
            log.info(f"[CHUNK] > {ch}")
            if not input_text.strip():
                log.info(f"! ! ! [KGExtractor] Skipping empty chunk {chunk_idx}")
                continue
            # input_text = "Project Overview\nProject Type: Saltwater Dilution & Transfer System\n\nLocation: Charlotte, North Carolina\n\nTank Capacity: 10,000 gallons (stainless steel, insulated)\n\nWater Inflow Rate: 1,000 GPM (potable)\n\nSalt Addition: 10 × 50 lb bags = 500 lb total\n\nAgitation Time: 1 hour (post-fill)\n\nDischarge Flow Rate: 50 GPM to external storage tank"

            try:
                log.info(f"[KGExtractor] Starting lx.extract... input text length: {len(input_text)}")
                result = lx.extract(
                    text_or_documents=input_text,
                    prompt_description=self.prompt,
                    examples=self.lx_examples,
                    model_id=self.model_name,
                    api_key=os.getenv("GEMINI_API_KEY"),
                    extraction_passes=1,
                    batch_length=50,
                    max_workers=4,  # smaller since per-chunk
                    temperature=0.0,
                )
            except Exception as e:
                log.info(f"[KGExtractor] chunk {chunk_idx} extract fail: {e}")
                continue

            # Convert raw extractions -> node/relationship primitives
            try:
                log.info("[KGExtractor] Converting to neo4j format...")
                neo_nodes, neo_edges = self.langextract_to_neo4j_format(
                    chunks=ch, extractions=result.extractions
                )
            except Exception as e:
                log.info(f"[KGExtractor] chunk {chunk_idx} format fail: {e}")
                continue

            all_nodes.extend(neo_nodes)
            all_rels.extend(neo_edges)

            # Mentions: link this chunk to each surfaced node
            for n in neo_nodes:
                props = n.get("properties") or n.get("props") or {}
                ent_id = n.get("id") or props.get("id")
                ent_name = props.get("name") or ent_id
                ent_type = n.get("type") or props.get("type") or "Node"
                if ent_name or ent_id:
                    mentions.append(
                        {
                            "chunk_idx": chunk_idx,
                            "entity": {
                                "id": ent_id,
                                "name": ent_name,
                                "type": ent_type,
                            },
                        }
                    )

        clean_nodes = [n for n in all_nodes if not self._is_fake_chunk_node(n)]

        return clean_nodes, all_rels, mentions

    def langextract_to_neo4j_format(
        self, chunks: List[Any], extractions: list
    ) -> Dict[str, Any]:
        """
        Convert langextract output (list of Extraction objects) to Neo4j node and edge dicts.
        Each extraction is expected to have:
        - extraction_class ("NODE" or "RELATIONSHIP")
        - extraction_text (node name or relationship type)
        - attributes (dict of properties, may include relationships)
        """
        nodes = []
        edges = []
        node_ids = set()
        log.info(
            f"[Neo4j] Converting {len(extractions)} extractions to Neo4j format..."
        )
        for ex in extractions:
            node_class = getattr(ex, "extraction_class", None) or None
            node_id = getattr(ex, "id", None) or getattr(ex, "extraction_text", None)
            properties = (
                getattr(ex, "properties", None) or getattr(ex, "attributes", {}) or {}
            )

            # Build Node if extraction_class == "NODE"
            if node_class == "NODE":
                log.info("[Neo4j] working on a node...")
                raw_label = (
                    properties.get("label")
                    if isinstance(properties, dict) and "label" in properties
                    else getattr(ex, "extraction_class", None) or "Unknown"
                )
                node_type = self.to_camel_case(raw_label)
                # pp.pprint(f"node properties: {properties}")
                if not node_id or node_id in node_ids:
                    continue
                node_ids.add(node_id)
                nodes.append(
                    {
                        "id": node_id,
                        "type": node_type,
                        "labels": [node_type],
                        # Exclude None and literal "null" (string), keep valid falsy like 0 or False
                        "properties": {
                            k: v
                            for k, v in properties.items()
                            if v is not None and v != "null"
                        },
                    }
                )
                # log.info(f"[Neo4j] Built node: {node_id} ({node_type}) with properties: {properties}")

            # Build Relationship if extraction_class == "RELATIONSHIP"
            elif node_class == "RELATIONSHIP":
                log.info("[Neo4j] working on a relationship...")
                # Expect properties to contain 'source' and 'target'
                src_id = properties.get("source")
                tgt_id = properties.get("target")
                rel_type = (
                    getattr(ex, "extraction_text", None)
                    or properties.get("type")
                    or "RELATED_TO"
                )
                if src_id and tgt_id:
                    edges.append(
                        {
                            "source": src_id,
                            "target": tgt_id,
                            "type": rel_type,
                            "properties": {
                                k: v
                                for k, v in properties.items()
                                if v is not None and v != "null"
                            },
                        }
                    )
                # log.info(f"[Neo4j] Built relationship: {src_id} -> {tgt_id} ({rel_type}) with properties: {properties}")
        log.info("[Neo4j] done assembling nodes and edges!")
        return nodes, edges

    def build_neo4j_graph(self, raw_nodes, raw_edges, mentions, input_text):
        nodes_neo = [
            Node(id=n["id"], type=n["type"], properties=n.get("properties", {}))
            for n in raw_nodes
        ]

        # for node in nodes_neo:
        #     pp.pprint(f"{node.id} ({node.type}) with properties:")
        #     pp.pprint(node.properties)
        log.info(
            f"[Build Neo4j Graph] Nodes: {len(nodes_neo)}, Edges: {len(raw_edges)}, Mentions: {len(mentions)}"
        )
        # Updated fallback order: properties.label -> node["type"] -> "Other"
        id_to_type = {}
        for n in raw_nodes:
            props = n.get("properties", {}) or {}
            lbl = props.get("label") or n.get("type") or "Other"
            id_to_type[n["id"]] = lbl

        def _safe_node(node_id: str):
            label = id_to_type.get(node_id, "Other")
            return Node(id=node_id, type=label, properties={})

        rels_neo = [
            Relationship(
                source=_safe_node(e["source"]),
                target=_safe_node(e["target"]),
                type=e.get("properties", {}).get("label", e.get("type", "RELATED_TO")),
                properties=e.get("properties", {}),
            )
            for e in raw_edges
            if e["source"] != e["target"]
        ]

        graph_doc = GraphDocument(
            nodes=nodes_neo,
            relationships=rels_neo,
            source=self._to_document(input_text),
        )
        return graph_doc

    def save_to_neo4j(self, graph_doc: GraphDocument | List[GraphDocument]):
        """
        Persist one or many GraphDocument objects to Neo4j.
        Accepts:
        - single GraphDocument
        - list[GraphDocument]
        - nested lists (will be flattened)
        The earlier error 'list' object has no attribute 'source' happened because a
        list was wrapped again: add_graph_documents([graph_doc]) where graph_doc was
        already a list, so Neo4j driver saw a list instead of a GraphDocument.
        """
        # Normalize to flat list of GraphDocument
        if isinstance(graph_doc, list):
            docs = []
            for item in graph_doc:
                if isinstance(item, list):
                    docs.extend(item)
                elif item is not None:
                    docs.append(item)
        else:
            docs = [graph_doc] if graph_doc is not None else []

        if not docs:
            return {"message": "No graph documents to save (empty list)."}

        print(f"[DEBUG] Writing {len(docs)} graph document(s) to Neo4j database...")
        try:
            neo_graph = Neo4jGraph(
                url=SETTINGS.neo4j_uri,
                username=SETTINGS.neo4j_user,
                password=SETTINGS.neo4j_password,
            )

            neo_graph.query("MATCH (n) DETACH DELETE n")
            print("[DEBUG] Adding graph documents to Neo4j...")
            neo_graph.add_graph_documents(docs, include_source=False)
        except Exception as e:
            print(f"[ERROR] Failed to connect to Neo4j or write data: {e}")
            return {"error": f"Failed to connect to Neo4j or write data: {e}"}

        return {"message": f"Saved {len(docs)} graph document(s) to Neo4j successfully"}
