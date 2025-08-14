import os
from typing import List, Dict, Any, Tuple
from .langex_kg import KGExtractor
from ..utils.logging import get_logger

log = get_logger(__name__)


def extract_graph(
    chunks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Wrapper for LangExtract KG extraction using chunks.
    """
    kg_extractor = KGExtractor()

    log.info("[KGExtractor] Starting extraction from chunks...")
    raw_nodes, raw_edges, mentions = kg_extractor.build_graph_from_chunks(chunks)
    
    # # Extract knowledge graph
    # extractions = kg_extractor.build_graph_from_chunks(chunks)

    # # Convert extractions to Neo4j format
    # raw_nodes, raw_edges = kg_extractor.langextract_to_neo4j_format(chunks, extractions)

    # Build Neo4j graph documents
    log.info("[KGExtractor] Building Neo4j graph documents...")
    graph_docs = kg_extractor.build_neo4j_graph(raw_nodes, raw_edges, mentions, input_text="<source>")
    
    # Save graph documents to Neo4j
    res = kg_extractor.save_to_neo4j(graph_docs)
    return res
