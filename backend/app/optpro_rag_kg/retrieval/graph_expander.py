from typing import List, Dict, Any
from ..stores.neo4j_store import Neo4jStore

class GraphExpander:
    def __init__(self, kg: Neo4jStore): self.kg = kg
    def expand_from_hits(self, hits: List[Dict[str, Any]], hop: int = 2) -> List[Dict[str, Any]]:
        seed = set()
        for h in hits:
            seed.update(h.get("metadata", {}).get("entity_ids", []))
        if not seed: return []
        rows = self.kg.expand_from_entities(sorted(seed), hop=hop)
        out = []
        for r in rows:
            out.append({
                "seed": dict(r.get("e")) if r.get("e") else None,
                "node": dict(r.get("n")) if r.get("n") else None,
                "cost": dict(r.get("c")) if r.get("c") else None,
            })
        return out
