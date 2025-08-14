# OptPro: RAG (Pinecone) + GraphRAG (Neo4j)

This repo implements a **modular**, **explainable** pipeline that connects **RAG**
(Pinecone vector store over chunks) with **GraphRAG** (Neo4j knowledge graph).

- Swap or disable components via config (dense/sparse embeddings, NER, etc.).
- Shared IDs connect chunks ↔ graph so queries can bridge both worlds.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add keys & URIs
python -m src.app.api.server  # or: python -m src.app.api.router
```

**Key endpoints (Flask):**
- `POST /ingest`  → Ingest a PDF or text, build RAG & KG
- `POST /query`   → Hybrid: Pinecone recall → Neo4j expansion → cost report
- `GET  /health`

See `src/app/api/router.py` for the blueprint-based routes (mirrors your reference `router.py`).

## Modules
- `ingestion/` PDF parsing, normalization, chunking, embeddings, upserts
- `kg/`        Ontology-aware entity/relationship extraction + Neo4j writer
- `stores/`    Pinecone + Neo4j thin clients (hybrid dense+sparse supported)
- `retrieval/` Vector recall, graph expansion, rerank stubs, costing & report
- `api/`       Flask app & blueprint router

MIT License.
