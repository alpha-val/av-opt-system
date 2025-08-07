from requests import session
from neo4j import GraphDatabase
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import Node, Relationship, GraphDocument
from langchain_core.documents import Document
from typing import Union

from .config import NEO4J_CONFIG

import pprint
import re

pp = pprint.PrettyPrinter(indent=2)


def to_camel_case(s):
    """Convert string to CamelCase (e.g., 'cost_rule' -> 'CostRule')"""
    if not s:
        return ""
    # Replace underscores/hyphens with spaces, split, capitalize, join
    return "".join(word.capitalize() for word in re.split(r"[_\-\s]+", s))


def langextract_to_neo4j_format(extractions):
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

    for ex in extractions:
        node_class = getattr(ex, "extraction_class", None) or None
        node_id = getattr(ex, "id", None) or getattr(ex, "extraction_text", None)
        properties = (
            getattr(ex, "properties", None) or getattr(ex, "attributes", {}) or {}
        )

        # Build Node if extraction_class == "NODE"
        if node_class == "NODE":
            raw_label = (
                properties.get("label")
                if isinstance(properties, dict) and "label" in properties
                else getattr(ex, "extraction_class", None) or "Unknown"
            )
            node_type = to_camel_case(raw_label)

            if not node_id or node_id in node_ids:
                continue
            node_ids.add(node_id)
            nodes.append(
                {
                    "id": node_id,
                    "type": node_type,
                    "labels": [node_type],
                    "properties": {k: v for k, v in properties.items() if v is not None}, # Exclude None values
                }
            )

        # Build Relationship if extraction_class == "RELATIONSHIP"
        elif node_class == "RELATIONSHIP":
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
                            if k not in ["source_id", "target_id"]
                        },
                    }
                )

    # print("[DEBUG] Nodes and edges converted from langextract format:")
    # pp.pprint(f"NODES>\n{nodes}")
    # pp.pprint(f"EDGES>\n{edges}")
    # print("- - - - - - - -")
    return nodes, edges


def _to_document(payload: Union[str, bytes]) -> Document:
    """Normalise text / bytes to a langchain Document."""
    if isinstance(payload, bytes):
        text = payload.decode("utf-8", errors="replace")
    elif isinstance(payload, str):
        text = payload
    else:
        raise TypeError(f"Unsupported type {type(payload)} – expected str or bytes.")
    return Document(page_content=text, metadata={"source": "graph_ingest"})


def build_neo4j_graph(raw_nodes, raw_edges, input_text):
    # Convert to Neo4j format
    nodes_neo = [
        Node(id=n["id"], type=n["type"], properties=n.get("properties", {}))
        for n in raw_nodes
    ]

    id_to_type = {
        n["id"]: n.get("properties", {}).get("label" or "Placeholder")
        for n in raw_nodes
    }

    def _safe_node(node_id: str):
        label = id_to_type.get(node_id) or "Placeholder"
        return Node(id=node_id, type=label, properties={})

    rels_neo = [
        Relationship(
            source=_safe_node(e["source"]),
            target=_safe_node(e["target"]),
            type=e.get("properties", {}).get("label", "RELATED_TO"),
            properties=e.get("properties", {}),
        )
        for e in raw_edges
        if e["source"] != e["target"]
    ]

    # print("[DEBUG] Nodes and edges converted in Neo4j format:")
    # pp.pprint(f"NODES>\n{nodes_neo}")
    # pp.pprint(f"EDGES>\n{rels_neo}")
    # print("< - - - - - - - - >")

    # Create a GraphDocument
    graph_doc = GraphDocument(
        nodes=nodes_neo,
        relationships=rels_neo,
        source=_to_document(input_text), # Optional: include source document
    )
    return graph_doc

def save_to_neo4j(graph_doc, full_wipe: bool = False):
    print("[DEBUG] Writing to Neo4j database...")
    try:
        neo_graph = Neo4jGraph(
            url=NEO4J_CONFIG["uri"],
            username=NEO4J_CONFIG["auth"][0],
            password=NEO4J_CONFIG["auth"][1],
        )

        if full_wipe:
            neo_graph.query("MATCH (n) DETACH DELETE n")

        print("[DEBUG] Adding graph document to Neo4j...")
        # Add the graph document to the Neo4j database
        neo_graph.add_graph_documents([graph_doc], include_source=True)
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neo4j or write data: {e}")
        return f"Failed to connect to Neo4j or write data: {e}"

    return {"message": "Saved to Neo4j successfully"}
