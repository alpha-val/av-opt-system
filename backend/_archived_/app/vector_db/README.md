# Workflow

# Step 1: Extract concepts from scenario
scenario_text = "Replace primary jaw crusher with 800 tph capacity"

# Step 2: Generate embedding
query_embedding = embed_text(scenario_text)

# Step 3: Search with filters
base_case_results = index.query(
    vector=query_embedding,
    top_k=20,
    filter={
        "project_id": {"$eq": project_id},
        "artifact_type": {"$eq": "base_case"},
        "entity_type": {"$eq": "equipment"},
        "category": {"$in": ["crusher", "jaw_crusher"]},
        "status": {"$eq": "active"}
    },
    namespace=f"project_{project_id}",
    include_metadata=True
)

tabular_results = index.query(
    vector=query_embedding,
    top_k=20,
    filter={
        "project_id": {"$eq": project_id},
        "artifact_type": {"$eq": "tabular_data"},
        "entity_type": {"$eq": "equipment"},
        "category": {"$in": ["crusher", "jaw_crusher"]},
        "capacity": {"$gte": 700, "$lte": 900}  # ±100 tph
    },
    namespace=f"project_{project_id}",
    include_metadata=True
)