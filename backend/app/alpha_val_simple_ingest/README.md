# Alpha-Val Simple Text Ingestion Pipeline (Python 3.12)

A **minimal, modular** ingestion pipeline for mining reports (NI 43-101, PEA/SK 1300/JORC).
It parses PDFs, chunks text, creates **dense + sparse** embeddings, upserts to **Pinecone**,
extracts a **knowledge graph** (KG) using a placeholder **LangExtract** wrapper, and loads it into **Neo4j**.
The code is organized for a Flask backend and leaves clear TODO hooks for future RAG/QA endpoints.

> This is a *simple*, production-lean version intended to be easy to read and extend.

---

## Features
- PDF parsing via **PyMuPDF**
- Chunking with provenance (doc_id, chunk_id, pages, section path)
- **Dense** embeddings via `sentence-transformers` (configurable)
- **Sparse** vectors via `scikit-learn` TF-IDF for Pinecone **hybrid**
- KG extraction stub with optional LLM integration (LangExtract/Gemini)
- Neo4j graph loader with MERGE semantics and a `SourceDocument` provenance root
- Clean, documented Python modules
- Flask endpoint `POST /ingest` to upload one or more PDFs
- CLI: `python -m scripts.run_ingest <pdf_or_dir>`

> **Strict requirement:** Python **3.12**. See `requirements.txt` for pinned versions.

---

## Quickstart

1) **Create and edit environment** from example:
```bash
cp .env.example .env
# Fill your keys & URIs
```

2) **Install deps** (inside a fresh Python 3.12 venv):
```bash
pip install -r requirements.txt
```

3) **Start Neo4j + Pinecone** (ensure credentials in `.env`).

4) **Run Flask**:
```bash
export FLASK_APP=app.py
flask run
```
Then `POST /ingest` with files:
```bash
curl -X POST -F "files=@/path/report.pdf" http://127.0.0.1:5000/ingest
```

5) **Or use CLI**:
```bash
python -m scripts.run_ingest /path/to/reports_or_dir
```

---

## Project Structure
```
alpha_val_simple_ingest/
├─ app.py                       # Flask app with /ingest
├─ config.py                    # Settings from .env
├─ .env.example                 # Fill in and copy to .env
├─ requirements.txt
├─ README.md
├─ prompts/
│  └─ build_prompt.py            # Template prompt for KG extraction
├─ alpha_val/
│  ├─ __init__.py
│  ├─ models.py                # Node/Relationship/Chunk/GraphDoc dataclasses
│  ├─ parsing.py               # PDF parsing (PyMuPDF)
│  ├─ chunking.py              # Text chunker with provenance
│  ├─ embeddings.py            # Dense + sparse (TF-IDF) vectors
│  ├─ vector_store.py          # Pinecone hybrid upserts
│  ├─ langex_kg_extraction.py  # LangExtract wrapper + rule-based fallback
|  |— neo4j_utils.py           # Neo4j utilities
│  ├─ graph_store.py           # Neo4j MERGE loader
│  ├─ ontology.py              # Built-in ontology + user override loader
│  └─ utils.py                 # IDs, normalization, helpers
└─ scripts/
   └─ run_ingest.py            # Simple CLI to ingest PDFs
```

---

## Configuration
All config is in `.env` (loaded via `config.py`):

- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME` (default: `alpha-val-hybrid`)
- `PINECONE_CLOUD` (e.g., `aws`), `PINECONE_REGION` (e.g., `us-east-1`)
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `EMBED_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `CHUNK_SIZE` (default: 1200), `CHUNK_OVERLAP` (default: 120)
- `GOOGLE_API_KEY` (optional; required if you wire up LangExtract/Gemini)

> **Dense dimension** is inferred from the chosen sentence-transformer at runtime.
> **Sparse** vectors are created with a per-batch TF-IDF vocabulary.

---

## How It Works (High-Level)

1. **Parse PDFs** → list of `(page_num, text)` using PyMuPDF.
2. **Chunk** with overlap and **provenance** (doc_id, chunk_id, pages, section path).
3. **Embed** chunks:
   - Dense with sentence-transformers.
   - Sparse TF-IDF using `scikit-learn`.
4. **Upsert to Pinecone** with both dense (`values`) and sparse (`sparse_values`).
5. **Extract KG** per chunk (LangExtract call **or** rule-based fallback), collect globally.
6. **Load to Neo4j** with `MERGE` for nodes/relationships.
   - A root node `(:SourceDocument {id: doc_id})` is created.
   - Only nodes of label `Document` are linked to `SourceDocument`.
7. **Return summary JSON**.

---

## TODO Hooks (for later phases)
- RAG/QA endpoints that query Pinecone + Neo4j
- Better section path extraction (ToC-aware)
- Unit & currency normalization with real libraries
- Domain ontologies & validation against `ALLOWED_PROPS`
- Robust LangExtract client (Gemini 2.5 flash) + retries/streaming
- Async queues for long-running ingestion

---

## Notes
- The included KG extractor has a **regex-based fallback** so the pipeline runs without LLM keys.
- For Pinecone Serverless, ensure `cloud` and `region` match your account’s index settings.
- If you already have a TF-IDF vocabulary, you can persist it and reuse to keep stable sparse indices.

---

© 2025 Alpha-Val — Simple Ingestion Pipeline
