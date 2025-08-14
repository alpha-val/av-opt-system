import os
from typing import List, Dict, Any, Tuple

def extract_spacy(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    try:
        import spacy
    except ImportError:
        raise ImportError("spaCy not installed. Please run `pip install spacy` and download a model.")
    model_name = os.getenv("SPACY_MODEL", "en_core_web_sm")
    nlp = spacy.load(model_name)
    entities, relations = [], []
    for chunk in chunks:
        text = chunk.get("text", "")
        doc = nlp(text)
        for ent in doc.ents:
            entities.append({
                "id": f"ent_{ent.start_char}_{ent.end_char}",
                "label": ent.label_,
                "text": ent.text,
                "chunk_idx": chunk.get("chunk_idx")
            })
    return entities, relations
