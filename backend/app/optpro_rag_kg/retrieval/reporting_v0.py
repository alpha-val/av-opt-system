"""Report generation hook (plug in your LLM)."""
from __future__ import annotations
from typing import Dict, Any

def draft_report(question: str, retrieval: Dict[str, Any], graph_view: Dict[str, Any], costing: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Mining Optionality & Cost Estimate")
    lines.append("")
    lines.append("## Question")
    lines.append(question)
    lines.append("")
    lines.append("## Retrieval (Pinecone)")
    lines.append(str(retrieval)[:2000])
    lines.append("")
    lines.append("## Graph View (Neo4j)")
    lines.append(str(graph_view)[:2000])
    lines.append("")
    lines.append("## Costing")
    lines.append(str(costing)[:1000])
    lines.append("")
    lines.append("_Replace this with an LLM-generated narrative summary._")
    return "\n".join(lines)
