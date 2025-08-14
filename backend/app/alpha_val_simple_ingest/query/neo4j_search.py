# ````python // filepath: /Users/test/Documents/Projects/Optionality_Mining/av-opt-system/backend/app/alpha_val_simple_ingest/query/neo4j_search.py
from __future__ import annotations
from typing import List, Dict, Any
from neo4j import GraphDatabase
from ..config import SETTINGS


def _fetch(
    driver,
    doc_ids: List[str],
    limit_nodes: int = 100,
    limit_rels: int = 200,
) -> Dict[str, Any]:
    """
    Attempt to fetch nodes + relationships tied to doc_ids (if present),
    else fallback to generic top nodes.
    """
    session = driver.session()
    result_nodes = []
    result_rels = []
    try:
        if doc_ids:
            cypher_nodes = """
            MATCH (n)
            WHERE n.doc_id IN $doc_ids
            RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
            LIMIT $limit_nodes
            """
            cypher_rels = """
            MATCH (a)-[r]-(b)
            WHERE a.doc_id IN $doc_ids AND b.doc_id IN $doc_ids
            RETURN elementId(r) AS id,
                elementId(a) AS source,
                elementId(b) AS target,
                type(r) AS type,
                properties(r) AS properties
            LIMIT $limit_rels
            """
            result_nodes = session.run(
                cypher_nodes,
                doc_ids=doc_ids,
                limit_nodes=limit_nodes,
            ).data()
            result_rels = session.run(
                cypher_rels,
                doc_ids=doc_ids,
                limit_rels=limit_rels,
            ).data()
        else:
            # fallback generic
            print("\t[DEBUG] falling back on generic query.")
            result_nodes = session.run(
                """
                MATCH (n)
                RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
                LIMIT $limit_nodes
                """,
                limit_nodes=limit_nodes,
            ).data()
    except Exception as e:
        print("Error fetching Neo4j data:", e)
    session.close()
    return {"nodes": result_nodes, "relationships": result_rels}


def query_neo4j_for_docs(doc_ids: List[str]) -> Dict[str, Any]:
    """
    Connect to Neo4j and fetch nodes/relationships related to doc_ids.
    """
    driver = GraphDatabase.driver(
        SETTINGS.neo4j_uri,
        auth=(SETTINGS.neo4j_user, SETTINGS.neo4j_password),
    )
    try:
        data = _fetch(driver, doc_ids)
    finally:
        driver.close()
    return data