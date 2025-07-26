"""
LangChain-native ETL for the “Optionality” graph
───────────────────────────────────────────────
• parses the NI 43-101 PDF
• chunks text
• asks GPT-4o (via LLMGraphTransformer) to emit *typed* nodes & edges
  using OpenAI function-calling under the hood (`use_functions=True`)
• bulk-loads the resulting GraphDocuments into Neo4j
"""

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph

# ──────────────────────────────────────────────────────────────────────────────
# 0. Load PDF & chunk it
# ──────────────────────────────────────────────────────────────────────────────
raw_docs = PyMuPDFLoader("i-80_GetchellProjcTechRpJan2021.pdf").load()
chunks = RecursiveCharacterTextSplitter(
    chunk_size=2_000, chunk_overlap=200  # tokens ≈ words for PDF prose
).split_documents(raw_docs)

# ──────────────────────────────────────────────────────────────────────────────
# 1. Configure the graph schema *for Optionality*
#    (these become enums in the OpenAI function automatically)
# ──────────────────────────────────────────────────────────────────────────────
NODE_TYPES = [
    "Workspace",  # e.g. “Getchell Optionality Study”
    "Scenario",  # “Base Case – Heap Leach”
    "Process",  # “Autoclave”, “Drift-and-Fill Mining”
    "Equipment",  # “30-ton haul truck”
    "Material",  # “Cyanide”, “Limestone”
    "CostEstimate",  # numeric cost items
]

EDGE_TYPES = [
    "HAS_SCENARIO",  # (Workspace) ──HAS_SCENARIO──▶ (Scenario)
    "INCLUDES_PROCESS",  # (Scenario)  ──INCLUDES_PROCESS──▶ (Process)
    "USES_EQUIPMENT",  # (Process)   ──USES_EQUIPMENT──▶ (Equipment)
    "CONSUMES_MATERIAL",  # (Process)   ──CONSUMES_MATERIAL──▶ (Material)
    "HAS_COST",  # (Scenario|Process) ──HAS_COST──▶ (CostEstimate)
]

# ──────────────────────────────────────────────────────────────────────────────
# 2. Instantiate LLM + GraphTransformer (✨ use_functions=True ✨)
#    → GPT-4o will be called with an OpenAI *function schema* generated
#      from NODE_TYPES / EDGE_TYPES; no manual JSON schema needed.
# ──────────────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

graph_xf = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=NODE_TYPES,
    allowed_edges=EDGE_TYPES,
    use_functions=True,  # <<< key flag: forces function-calling
)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Extract GraphDocuments from every chunk
#    (one call per chunk; returns list[GraphDocument])
# ──────────────────────────────────────────────────────────────────────────────
graph_docs_raw = graph_xf.transform_documents(chunks)

# Optional: drop low-confidence edges & dedupe nodes/edges
graph_docs = graph_xf.postprocess_graph_documents(
    graph_docs_raw, score_threshold=0.80  # keep only ≥80 % confidence
)

# ──────────────────────────────────────────────────────────────────────────────
# 4. Bulk-insert into Neo4j
# ──────────────────────────────────────────────────────────────────────────────
neo = Neo4jGraph(
    url="bolt://localhost:7687", username="neo4j", password="password"  # ← change me
)

neo.add_graph_documents(graph_docs, include_source=True)

print(f"✅ Loaded {len(graph_docs)} GraphDocuments into Neo4j.")
