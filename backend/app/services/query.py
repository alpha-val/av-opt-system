from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from ..config import NEO4J_CONFIG

uri = NEO4J_CONFIG["uri"]
username = NEO4J_CONFIG["auth"][0]
password = NEO4J_CONFIG["auth"][1]
driver = GraphDatabase.driver(NEO4J_CONFIG["uri"], auth=(username, password))

def nodes(node_type=None, limit=100):
    print(f"DEBUG: Fetching nodes of type '{node_type}' with limit {limit}")
    try:
        with driver.session() as session:
            cypher = """
            MATCH (n)
            WHERE $node_type IS NULL OR $node_type IN labels(n)
            RETURN { id: elementId(n), labels: labels(n), properties: n } AS n
            LIMIT $limit
            """
            res = session.run(cypher, node_type=node_type, limit=limit)
            # Consume once; cursor is exhausted after this
            rows = res.data()
            return [row["n"] for row in rows]
    except ServiceUnavailable as e:
        print(f"Neo4j connection error: {e}")
        return []
    except Neo4jError as e:
        print(f"Cypher query error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in nodes query: {e}")
        return []



def edges(edge_type=None, limit=100):
    try:
        with driver.session() as session:
            cypher = f"MATCH (a)-[r{':' + edge_type if edge_type else ''}]->(b) RETURN a, r, b LIMIT $limit"
            result = session.run(cypher, limit=limit)
            rows = result.data()
            return [
                {"from": record["a"], "edge": record["r"], "to": record["b"]}
                for record in rows
            ]
    except ServiceUnavailable as e:
        print(f"Neo4j connection error: {e}")
        return []
    except Neo4jError as e:
        print(f"Cypher query error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in edges query: {e}")
        return []

