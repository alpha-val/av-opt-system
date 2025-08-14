from .extract_with_spacy import extract_spacy
from .extract_with_openai import extract_openai
from .langextract_wrapper import extract_graph
from ..stores.neo4j_store import Neo4jStore
from typing import List, Dict, Any, Tuple

def extract_entities_and_relations(chunks: List[Dict[str, Any]], method: str = "langextract") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if method == "spacy":
        return extract_spacy(chunks)
    elif method == "openai":
        return extract_openai(chunks)
    elif method == "langextract":
        return extract_graph(chunks)
    else:
        raise ValueError(f"Unknown extraction method: {method}")
