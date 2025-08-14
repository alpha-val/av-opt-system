from __future__ import annotations
from typing import List, Dict, Any
from neo4j import GraphDatabase
from .models import GraphDoc, Node, Relationship

class GraphLoader:
    def __init__(self, settings):
        self.settings = settings
        self.driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))

    def close(self):
        self.driver.close()

    def load_document_graph(self, doc_id: str, filename: str, graph_docs: List[GraphDoc]) -> Dict[str, int]:
        # Aggregate nodes/relationships; dedupe by (id, type)
        node_map: Dict[str, Node] = {}
        rel_key_set = set()
        relationships: List[Relationship] = []

        for gd in graph_docs:
            for n in gd.nodes:
                key = f"{n.type}::{n.id}"
                if key not in node_map:
                    node_map[key] = n
                else:
                    # merge properties (new overwrites old)
                    node_map[key].properties.update(n.properties)
            for r in gd.relationships:
                rkey = (r.source_id, r.target_id, r.type)
                if rkey not in rel_key_set:
                    relationships.append(r)
                    rel_key_set.add(rkey)

        nodes = list(node_map.values())

        # Write to Neo4j
        with self.driver.session() as sess:
            # Ensure SourceDocument provenance root
            sess.execute_write(self._merge_source_document, doc_id, filename)

            # MERGE nodes
            for n in nodes:
                sess.execute_write(self._merge_node, n)

            # Special: link only Document nodes to SourceDocument
            for n in nodes:
                if n.type == "Document":
                    sess.execute_write(self._link_to_source, doc_id, n.id)

            # MERGE relationships
            for r in relationships:
                sess.execute_write(self._merge_relationship, r)

        return {"nodes": len(nodes), "relationships": len(relationships)}

    @staticmethod
    def _merge_source_document(tx, doc_id: str, filename: str):
        tx.run(
            "MERGE (s:SourceDocument {id: $id}) "
            "SET s.filename = $filename, s.ingested_at = timestamp()",
            id=doc_id, filename=filename
        )

    @staticmethod
    def _merge_node(tx, node: Node):
        # Dynamic label with MERGE by id
        q = f"MERGE (n:`{node.type}` {{id: $id}}) SET n += $props"
        tx.run(q, id=node.id, props=node.properties)

    @staticmethod
    def _link_to_source(tx, source_doc_id: str, document_node_id: str):
        tx.run(
            "MATCH (s:SourceDocument {id: $sid}), (d:Document {id: $did}) "
            "MERGE (s)-[:CONTAINS]->(d)",
            sid=source_doc_id, did=document_node_id
        )

    @staticmethod
    def _merge_relationship(tx, rel: Relationship):
        # We need labels of endpoints; for simplicity assume ids uniquely identify nodes regardless of label.
        # If you need label-aware matching, include 'type' in Relationship properties and fetch labels beforehand.
        tx.run(
            "MATCH (a {id: $aid}), (b {id: $bid}) "
            "MERGE (a)-[r:`%s`]->(b) "
            "SET r += $props" % rel.type,
            aid=rel.source_id, bid=rel.target_id, props=rel.properties
        )
