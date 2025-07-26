from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from ..config import NEO4J_CONFIG

driver = GraphDatabase.driver(**NEO4J_CONFIG)


def nodes(node_type=None, limit=100):
    try:
        with driver.session() as session:
            cypher = (
                f"MATCH (n{':' + node_type if node_type else ''}) RETURN n LIMIT $limit"
            )
            result = session.run(cypher, limit=limit)
            return [record["n"] for record in result]
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
            return [
                {"from": record["a"], "edge": record["r"], "to": record["b"]}
                for record in result
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
