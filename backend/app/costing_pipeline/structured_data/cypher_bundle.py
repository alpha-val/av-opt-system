## File: `structured/cypher_bundle.py`

from __future__ import annotations
from ..storage import GraphDatabase, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

CY_CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Table) REQUIRE t.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Row)   REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Cell)  REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Equipment) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (x:CostEstimate) REQUIRE x.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (k:Chunk) REQUIRE k.chunk_id IS UNIQUE",
]

# Template merges when writing raw Cypher (not used by the writer, but handy)
CY_MERGE_TABLE = """
MERGE (t:Table {id: $table_id}) SET t += $props RETURN t
"""

CY_MERGE_ROW = """
MERGE (r:Row {id: $row_id}) SET r += $props
WITH r
MATCH (t:Table {id: $table_id})
MERGE (t)-[:HAS_ROW]->(r)
RETURN r
"""

CY_MERGE_CELL = """
MERGE (c:Cell {id: $cell_id}) SET c += $props
WITH c
MATCH (r:Row {id: $row_id})
MERGE (r)-[:HAS_CELL]->(c)
RETURN c
"""

CY_LINK_EVIDENCE = """
MATCH (r:Row {id: $row_id}), (n {id: $node_id})
MERGE (r)-[:EVIDENCES {source:'row'}]->(n)
"""

CY_CHUNK_MENTIONS = """
MERGE (k:Chunk {chunk_id: $chunk_id}) SET k += $props
WITH k
MATCH (n {id: $node_id})
MERGE (k)-[:MENTIONS {surface: $surface}]->(n)
"""


def ensure_constraints():
    drv = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with drv.session() as s:
        for cy in CY_CONSTRAINTS:
            s.run(cy)
    drv.close()
