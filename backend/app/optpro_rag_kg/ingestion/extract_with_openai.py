import os
from typing import List, Dict, Any, Tuple

def extract_openai(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    import openai, json
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    entities, relations = [], []
    for chunk in chunks:
        text = chunk.get("text", "")
        prompt = (
            "Extract entities and relationships from the following text in JSON format:",
            f"{text},",
            "Output format: {\"entities\":[{\"id\":...,\"label\":...,\"text\":...}],"
            "\"relationships\":[{\"source\":...,\"target\":...,\"type\":...}]}"
        )
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        try:
            data = json.loads(resp.choices[0].message["content"])
        except Exception:
            data = {"entities": [], "relationships": []}
        for ent in data.get("entities", []):
            ent["chunk_idx"] = chunk.get("chunk_idx")
            entities.append(ent)
        relations.extend(data.get("relationships", []))
    return entities, relations


