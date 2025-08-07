import langextract as lx
from langextract.inference import OpenAILanguageModel
from langchain_community.graphs.graph_document import Node, Relationship, GraphDocument
from langchain_core.documents import Document
from langchain_community.graphs import Neo4jGraph
from .ingest_langex import build_graph
import datetime


def make_graph(data, full_wipe: bool = False):
    print("[DEBUG] Starting document processing...")
    result = build_graph(
        input_data=data,
        full_wipe=full_wipe,  # Set to True for initial ingestion
    )

    return {"message": "Document processed successfully", "data": result}