## How to wire it up

1. **Install**: place the `structured/` folder next to your existing `in_pipeline/` package. Import and register the blueprint:

```python
# in your Flask app factory
from .structured import structured_bp
app.register_blueprint(structured_bp)
```

2. **Ingest**:

- `POST /structured/ingest` with form-data `files=<xlsx>` (optional `sheet`, `currency`, `base_year`)
- or JSON `{ "paths": ["/abs/path.xlsx"], "sheet": "Gyratory" }`

3. **What you get**:

- Neo4j nodes: `Table, Row, Cell, Equipment, CostEstimate, Chunk`
- Edges: `HAS_ROW, HAS_CELL, EVIDENCES, HAS_COST, MENTIONS`
- Pinecone vectors: **row‑cards** (one per Row) with metadata `{table_id,row_id,family,size_code,base_year,currency,source_file}`
- Everything is provenance‑linked, so your existing `/costing_pipeline/query` flow can seed from these \:Chunk ids and traverse via `MENTIONS` → `Equipment/CostEstimate`.

4. **Extend mapping**:

- Add smarter matchers in `transform.py` (e.g., parse capacity matrices into `CapacityPoint` nodes and link via `HAS_CAPACITY`).
- Swap `units.py` with a `pint`-backed converter if you want richer UoM.
- Attach your project‑specific escalation indices and installed‑cost factors at `(Project)` or `(Scenario)` and reference them during analysis.

## PDF table extraction (on-prem OCR)

### Dependencies
- `pdfplumber` (page analysis)
- `camelot-py` (optional; vector PDF tables). Requires Ghostscript.
- `pdf2image` + Poppler (render image PDFs)
- `opencv-python` (grid detection)
- `pytesseract` + system Tesseract binary (OCR)

Ubuntu quickstart:
```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr poppler-utils ghostscript
pip install pdfplumber pdf2image opencv-python pytesseract camelot-py[cv]
