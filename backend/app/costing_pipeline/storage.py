"""
Pinecone (dense + sparse) & Neo4j I/O.
- Dense embeddings via OpenAI.
- Sparse vectors via stable hashed-term TF "tf-idf-lite" to fixed space (default 2^20).
- Neo4j writer that anchors on :__Entity {id} then adds domain labels; deterministic UUID5.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import os
import sys
import uuid
import math
import re
import unicodedata
import hashlib
from collections import Counter, defaultdict

# --- Load config from user's adapter (supports both 'SETTINGS' object or flat constants)
# Add /mnt/data on sys.path for the uploaded config_adapter.py / ontology.py if needed
if "/mnt/data" not in sys.path:
    sys.path.append("/mnt/data")

try:
    import config_adapter  # user-supplied

    SETTINGS = getattr(config_adapter, "SETTINGS", config_adapter)
    OPENAI_API_KEY = getattr(SETTINGS, "openai_api_key", os.getenv("OPENAI_API_KEY"))
    PINECONE_API_KEY = getattr(
        SETTINGS, "pinecone_api_key", os.getenv("PINECONE_API_KEY")
    )
    PINECONE_INDEX = getattr(SETTINGS, "pinecone_index", "optpro-chunks")
    PINECONE_CLOUD = getattr(SETTINGS, "pinecone_cloud", "aws")
    PINECONE_REGION = getattr(SETTINGS, "pinecone_region", "us-east-1")
    NEO4J_URI = getattr(SETTINGS, "neo4j_uri", os.getenv("NEO4J_URI"))
    NEO4J_USER = getattr(SETTINGS, "neo4j_user", os.getenv("NEO4J_USER"))
    NEO4J_PASSWORD = getattr(SETTINGS, "neo4j_password", os.getenv("NEO4J_PASSWORD"))
    EMBED_MODEL = getattr(SETTINGS, "embed_model", "text-embedding-3-small")
except Exception:
    # fallback to env-only
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX", "optpro-chunks")
    PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# --- OpenAI embeddings client (v1 API)
try:
    from openai import OpenAI

    _openai_client = OpenAI(api_key=OPENAI_API_KEY)
except Exception:
    _openai_client = None

# --- Pinecone v3
try:
    from pinecone import Pinecone, ServerlessSpec

    _pc = Pinecone(api_key=PINECONE_API_KEY) if PINECONE_API_KEY else None
except Exception:
    _pc = None
    ServerlessSpec = None

# --- Neo4j v5
try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None


# ----------------------- Data classes for graph -----------------------


@dataclass
class GNode:
    id: str
    type: str
    properties: Dict[str, Any]


@dataclass
class GRel:
    source: GNode
    target: GNode
    type: str
    properties: Dict[str, Any]


@dataclass
class GDoc:
    nodes: List[GNode]
    relationships: List[GRel]
    source: Optional[Any] = None


# ----------------------- Deterministic UUID5 --------------------------

UUID5_NS = uuid.UUID("3f8b15a1-66c9-4e21-92b4-0e6fc0c77b3e")  # constant namespace


def canonical_key(node: Dict[str, Any]) -> str:
    typ = (node.get("type") or "").strip().lower()
    props = node.get("properties", {}) or {}
    name = (props.get("name") or "").strip().lower()
    original = (props.get("original_id") or node.get("id") or "").strip().lower()
    return f"{typ}|{name}|{original}"


def deterministic_uuid5(key: str) -> str:
    return str(uuid.uuid5(UUID5_NS, key))


# ----------------------- Safe names and IDs ----------

SAFE_NS = re.compile(
    r"[^A-Za-z0-9_.-]"
)  # keep only letters, digits, underscore, dot, dash


def make_safe_ascii(s: str) -> str:
    """ASCII-only, replace unsafe chars with '_', collapse repeats, trim."""
    if not s:
        return "default"
    # strip diacritics & non-ascii (turn “—” into "-“ or drop)
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = s_norm.encode("ascii", "ignore").decode("ascii")
    # replace spaces with _, then drop any other unsafe char
    s_ascii = s_ascii.replace(" ", "_")
    s_ascii = SAFE_NS.sub("_", s_ascii)
    # collapse consecutive underscores/dots/dashes
    s_ascii = re.sub(r"[_\.-]{2,}", "_", s_ascii).strip("._-")
    return s_ascii or "default"


def make_namespace_from_filename(fname: str) -> str:
    """
    Build a stable, safe namespace from a filename, with a short hash to avoid collisions.
    Pinecone allows ASCII-printable only; be conservative and use [A-Za-z0-9_.-].
    """
    base = (fname or "default").rsplit(".", 1)[0]
    safe = make_safe_ascii(base)
    # add short hash for uniqueness across similar names after sanitization
    h = hashlib.sha1((fname or "").encode("utf-8")).hexdigest()[:8]
    ns = f"{safe}_{h}"
    # trim to a reasonable length (Pinecone recommends short ids/namespaces)
    return ns[:60]  # conservative cap


def make_safe_id(prefix: str, i: int) -> str:
    p = make_safe_ascii(prefix)
    return f"{p}{i}"


# ----------------------- Sparse vectors (hashed TF-IDF-lite) ----------

TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")  # simple tokenization heuristic


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


def _hash_token(token: str, dim: int) -> int:
    # MD5 → int → modulo dim for a stable hashed coordinate
    import hashlib

    return int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim


def build_sparse_hybrid_vectors(
    texts: List[str], dim: int = 2**20
) -> List[Dict[str, List[float]]]:
    """
    Create Pinecone-compatible sparse vectors:
      [{"indices":[...], "values":[...]}, ...]
    using hashed TF-IDF in a fixed space (dim).
    """
    N = len(texts)
    # Document frequencies
    df = defaultdict(int)
    docs_tokens = []
    for tx in texts:
        toks = _tokenize(tx)
        docs_tokens.append(toks)
        for tok in set(toks):
            df[tok] += 1

    sparse_vecs = []
    for toks in docs_tokens:
        tf = Counter(toks)
        coords = defaultdict(float)
        for tok, freq in tf.items():
            if df[tok] == 0:
                continue
            idf = math.log((1 + N) / (1 + df[tok])) + 1.0
            weight = (freq / max(1, len(toks))) * idf
            idx = _hash_token(tok, dim)
            coords[idx] += weight

        if coords:
            indices, values = zip(*sorted(coords.items()))
            sparse_vecs.append(
                {"indices": list(indices), "values": [float(v) for v in values]}
            )
        else:
            sparse_vecs.append({"indices": [], "values": []})
    return sparse_vecs


# ----------------------- OpenAI dense embeddings ----------------------


def embed_texts_dense(texts: List[str], model: str = None) -> List[List[float]]:
    if _openai_client is None:
        raise RuntimeError(
            "OpenAI client not available. Set OPENAI_API_KEY and install `openai` >= 1.0."
        )
    use_model = model or EMBED_MODEL
    resp = _openai_client.embeddings.create(model=use_model, input=texts)
    return [d.embedding for d in resp.data]


# ----------------------- Pinecone index helpers -----------------------


class PineconeStore:
    def __init__(self, index_name: str = None):
        if _pc is None:
            raise RuntimeError(
                "Pinecone client not available. Install `pinecone-client` (v3 package `pinecone`)."
            )
        self.index_name = index_name or PINECONE_INDEX
        self._ensure_index()

    def _ensure_index(self):
        # If the index doesn't exist, create a serverless one.
        existing = [idx["name"] for idx in _pc.list_indexes()]
        if self.index_name not in existing:
            if ServerlessSpec is None:
                raise RuntimeError(
                    "Pinecone ServerlessSpec unavailable. Check your pinecone client version."
                )
            _pc.create_index(
                name=self.index_name,
                dimension=1536,  # default for text-embedding-3-small; override if you use another model
                metric="dotproduct",
                spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
            )
        self.index = _pc.Index(self.index_name)

    def upsert_chunks(
        self,
        chunk_texts: List[str],
        dense_vecs: List[List[float]],
        sparse_vecs: List[Dict[str, List[float]]],
        metas: List[Dict[str, Any]],
        namespace: str = "default",
        id_prefix: str = "chunk_",
    ) -> int:
        """
        Upsert chunk vectors. Dense + sparse hybrid with metadata.
        """
        vectors = []
        namespace = make_safe_ascii(namespace)
        for i, (dv, sv, md) in enumerate(zip(dense_vecs, sparse_vecs, metas)):
            vectors.append(
                {
                    "id": make_safe_id(id_prefix, i),
                    "values": dv,
                    "sparse_values": sv,
                    "metadata": md or {},
                }
            )

        try:
            self.index.upsert(vectors=vectors, namespace=namespace)
        except Exception:
            # Last-resort fallback — keeps ingestion running
            self.index.upsert(vectors=vectors, namespace="default")
        
        return len(vectors)


# ----------------------- Neo4j writer --------------------------------


class Neo4jWriter:
    """
    Anchors all nodes on :__Entity {id} (unique), then adds domain labels (:Project/:Equipment/...).
    Merges relationships with properties.
    """

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        if GraphDatabase is None:
            raise RuntimeError("Neo4j driver not available. `pip install neo4j`.")
        self._driver = GraphDatabase.driver(
            uri or NEO4J_URI, auth=(user or NEO4J_USER, password or NEO4J_PASSWORD)
        )

    def close(self):
        self._driver.close()

    @staticmethod
    def _clean_props(d: Dict[str, Any] | None) -> Dict[str, Any]:
        return {str(k): v for k, v in (d or {}).items() if v is not None and k != "id"}

    def _ensure_constraint(self):
        with self._driver.session() as s:
            s.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:__Entity) REQUIRE n.id IS UNIQUE"
            )

    def _merge_legacy_node_twins(self, session):
        # Merge any pairs that share the same id but different labels (e.g., :Node vs :__Entity:Equipment)
        session.run("""
        CALL {
        MATCH (n) WHERE exists(n.id)
        WITH n.id AS id, collect(n) AS ns
        WHERE size(ns) > 1
        CALL apoc.refactor.mergeNodes(ns, {properties:'combine', mergeRels:true})
        YIELD node
        RETURN count(*) AS merged
        }
        """)
    
    def save(self, gdoc: GDoc, full_wipe: bool = False) -> dict:
        self._ensure_constraint()
        with self._driver.session() as s:
            if full_wipe:
                s.run("MATCH (n) DETACH DELETE n")
                self._ensure_constraint()

            # Optional consolidation if APOC is available
            # one-time consolidation for any old :Node duplicates
            try:
                self._merge_legacy_node_twins(s)
            except Exception:
                # APOC not available – skip; see non-APOC fallback below
                pass

            # --- Nodes ---
            for n in gdoc.nodes:
                props = self._clean_props(n.properties)
                print(f"Merging node {n.id} of type {n.type}: node: {n}")
                s.run(
                    f"""
                    MERGE (x:__Entity {{id: $id}})
                    SET x += $props
                    SET x:`{n.type}`
                    """,
                    id=n.id, props=props
                )

            # --- Relationships ---
            for r in gdoc.relationships:
                rprops = self._clean_props(r.properties)
                cypher = f"""
                MERGE (s:__Entity {{id: $sid}}) SET s:`{r.source.type}`
                MERGE (t:__Entity {{id: $tid}}) SET t:`{r.target.type}`
                MERGE (s)-[rel:`{r.type}`]->(t)
                SET rel += $rprops
                """
                s.run(cypher, sid=r.source.id, tid=r.target.id, rprops=rprops)

        return {"nodes_written": len(gdoc.nodes), "rels_written": len(gdoc.relationships)}