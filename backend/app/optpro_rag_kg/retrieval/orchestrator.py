from typing import Dict, Any
from .vector_retriever import VectorRetriever
from .graph_expander import GraphExpander
from .rerank import simple_rerank
from .costing import compute_cost_report
from ..utils.units import normalize_units

class QueryOrchestrator:
    def __init__(self, vr: VectorRetriever, gx: GraphExpander):
        self.vr = vr; self.gx = gx

    def query(self, q: str, params: Dict[str, Any] | None = None, top_k: int = 8, hop: int = 2) -> Dict[str, Any]:
        params = params or {}
        # A) vector recall
        hits = self.vr.search(q, top_k=top_k)
        hits = simple_rerank(hits)
        # B) graph expansion
        graph = self.gx.expand_from_hits(hits, hop=hop)
        # C) costing (toy)
        cost = compute_cost_report(graph, normalize_units(params))
        return {"hits": hits, "graph": graph, "cost": cost}
