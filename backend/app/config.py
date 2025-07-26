import os

NODE_TYPES = [
    "Workspace",
    "Scenario",
    "Process",
    "Equipment",
    "Material",
    "CostEstimate",
]

EDGE_TYPES = [
    "HAS_SCENARIO",
    "INCLUDES_PROCESS",
    "USES_EQUIPMENT",
    "CONSUMES_MATERIAL",
    "HAS_COST",
]

NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "auth": (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
}
