Scenario analysis workflow

Prompt: Next, sketch the workflow for scenario analysis at `run_analysis_v3` in @scenarios.py



┌─────────────────────────────────────────────────────────────────────────┐

│  API Endpoint: POST /{scenario_id}/run-analysis-v3                      │

│  Authentication: JWT token (current_user)                                │

└─────────────────────────────────────────────────────────────────────────┘

                              │

                              ▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 1: Validation & Setup                                              │

│  ├─ Extract user_id from JWT token                                      │

│  ├─ Validate scenario_id format (MongoDB ObjectId)                      │

│  ├─ Fetch scenario from database                                         │

│  │   └─ 404 if not found                                                │

│  ├─ Validate global objective requirements:                              │

│  │   • global_objective_type (required)                                  │

│  │   • global_objective_target (required)                                │

│  │   └─ 400 if missing                                                  │

│  ├─ Fetch project from database                                          │

│  │   └─ 404 if not found                                                │

│  └─ Validate project has base_case_documents                            │

│      └─ 400 if empty                                                    │

└─────────────────────────────────────────────────────────────────────────┘

                              │

                              ▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 2: Initialize Background Task                                      │

│  ├─ Update scenario status → PROCESSING                                  │

│  ├─ Generate unique job_id (UUID)                                       │

│  ├─ Create asyncio background task:                                     │

│  │   _run_analysis_background_v3(                                       │

│  │     job_id, scenario_id, project_id, user_id,                        │

│  │     global_objective_type, global_objective_target,                  │

│  │     objective_description, base_case_document_ids                    │

│  │   )                                                                   │

│  ├─ Register task in _analysis_v3_tasks dict                            │

│  └─ Return response immediately with:                                    │

│      • job_id                                                            │

│      • websocket_url: /api/v1/ws/progress/{job_id}                      │

│      • status: "queued"                                                 │

└─────────────────────────────────────────────────────────────────────────┘

                              │

                              ▼

┌─────────────────────────────────────────────────────────────────────────┐

│  BACKGROUND TASK: _run_analysis_background_v3                           │

│  (Runs asynchronously, publishes progress via WebSocket)                 │

└─────────────────────────────────────────────────────────────────────────┘

                              │

                              ▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 3: Initialize & Publish Start Event                                │

│  ├─ Get ProgressPublisher, OrchestrationService, FileStorageService     │

│  ├─ Publish START event (progress: 0%)                                   │

│  │   meta: scenario_id, project_id, total_documents                    │

│  └─ Import text extraction utilities                                    │

└─────────────────────────────────────────────────────────────────────────┘

                              │

                              ▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 4: Read Base Case Documents (Progress: 10%)                        │

│  ├─ Publish progress event: "Reading base case documents"               │

│  ├─ orchestration._read_base_case_documents_v3()                        │

│  │   FOR EACH document_id:                                               │

│  │   ├─ Retrieve file_bytes from GridFS (FileStorageService)            │

│  │   ├─ Get file metadata (filename)                                     │

│  │   └─ Return: [{file_bytes, filename, document_id}, ...]               │

│  └─ Raise error if no documents retrieved                               │

└─────────────────────────────────────────────────────────────────────────┘

                              │

                              ▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 5: Process Each Document (Sequential Loop)                         │

│                                                                          │

│  FOR EACH document (idx = 1 to N):                                       │

│  │                                                                       │

│  ├─ Extract Text from PDF                                                │

│  │   ├─ extract_and_clean(file_bytes, filename)                         │

│  │   │   └─ Returns: pages_clean                                        │

│  │   └─ extract_fulltext(pages_clean)                                    │

│  │       └─ Returns: full_text (string)                                  │

│  │                                                                       │

│  ├─ STEP 5.1: Extract Recommendations (Progress: 30-60%)                │

│  │   ├─ Publish progress event:                                         │

│  │   │   "Extracting recommendations for document {idx}/{N}"            │

│  │   │   progress: 30 + (idx-1)/N * 30                                   │

│  │   │                                                                   │

│  │   ├─ orchestration._extract_recommendations_v3()                      │

│  │   │   ├─ Build LLM prompt with:                                       │

│  │   │   │   • Global objective context                                  │

│  │   │   │   • Base case text (first 50k chars)                          │

│  │   │   │   • Instructions for recommendations + entity specs           │

│  │   │   │                                                                │

│  │   │   ├─ Invoke LLM (ChatOpenAI) with extract_recommendations tool   │

│  │   │   │                                                                │

│  │   │   ├─ Parse LLM response:                                         │

│  │   │   │   • recommendations: List[Dict]                               │

│  │   │   │   • entities_for_costing: List[Dict]                          │

│  │   │   │     (Each entity spec includes: _id, type, properties with    │

│  │   │     name, MSIO classification, expected_attributes, etc.)         │

│  │   │   │                                                                │

│  │   │   └─ Return: {recommendations, entities_for_costing}              │

│  │   │                                                                   │

│  │   └─ Accumulate recommendations in all_recommendations                │

│  │                                                                       │

│  ├─ STEP 5.2: Retrieve Relevant Entities (Progress: 60-80%)             │

│  │   ├─ Publish progress event:                                          │

│  │   │   "Retrieving relevant entities from MongoDB for document {idx}"  │

│  │   │   progress: 60 + (idx-1)/N * 20                                   │

│  │   │                                                                   │

│  │   ├─ orchestration._retrieve_relevant_entities_v3()                   │

│  │   │   FOR EACH entity_spec in entities_for_costing:                   │

│  │   │   │                                                                │

│  │   │   ├─ Convert entity_spec to entity-like dict                      │

│  │   │   │                                                                │

│  │   │   ├─ Build text representation                                    │

│  │   │   │   └─ EntityVectorStore.build_text_for_embedding()             │

│  │   │   │                                                                │

│  │   │   ├─ Generate embedding                                           │

│  │   │   │   └─ generate_embeddings([text]) → [embedding_vector]         │

│  │   │   │                                                                │

│  │   │   ├─ Semantic Search (Pinecone)                                    │

│  │   │   │   └─ search_entities_by_embedding(                             │

│  │   │   │       embedding, project_id, scenario_id,                     │

│  │   │   │       artifact_type="base_case",                               │

│  │   │   │       top_k=5, cutoff=0.7                                      │

│  │   │   │     )                                                          │

│  │   │   │   ├─ Query Pinecone with filters                              │

│  │   │   │   ├─ Get entity IDs from matches                              │

│  │   │   │   ├─ Fetch full entities from MongoDB                         │

│  │   │   │   └─ Add relevance_score to entities                          │

│  │   │   │                                                                │

│  │   │   ├─ Filter by scenario_id (if not in Pinecone metadata)          │

│  │   │   │                                                                │

│  │   │   ├─ IF semantic search found match:                              │

│  │   │   │   └─ Use top match (highest relevance_score)                  │

│  │   │   │                                                                │

│  │   │   ├─ ELSE (fallback to MongoDB exact query):                      │

│  │   │   │   ├─ Build MongoDB query with:                                 │

│  │   │   │   │   • project_id, scenario_id, artifact_type                │

│  │   │   │   │   • name (regex, case-insensitive)                        │

│  │   │   │   │   • MSIO classification (discipline, category, etc.)      │

│  │   │   │   │   • entity type                                            │

│  │   │   │   ├─ Query MongoDB entities collection                        │

│  │   │   │   └─ Use first match if found                                  │

│  │   │   │                                                                │

│  │   │   └─ IF no match found:                                           │

│  │   │       └─ Create placeholder entity                                 │

│  │   │           └─ _create_placeholder_entity()                          │

│  │   │               (includes: _id, type, properties with MSIO,         │

│  │   │                is_placeholder=True, expected_attributes, etc.)    │

│  │   │                                                                │

│  │   ├─ Deduplicate matched entities (by _id)                            │

│  │   │                                                                │

│  │   └─ Return: [matched_entities + placeholder_entities]                │

│  │                                                                       │

│  │   └─ Accumulate entities in all_relevant_entities                     │

│  │                                                                       │

│  └─ STEP 5.3: Store Recommendations (Progress: 80-100%)                 │

│      ├─ orchestration._store_recommendations_v3()                        │

│      │   ├─ Generate recommendations_id (UUID)                          │

│      │   ├─ Create document:                                             │

│      │   │   {                                                           │

│      │   │     _id: recommendations_id,                                  │

│      │   │     document_id, project_id, scenario_id, user_id,            │

│      │   │     global_objective_type, global_objective_target,            │

│      │   │     recommendations: [...],                                   │

│      │   │     relevant_entities: [...],                                  │

│      │   │     workflow_version: "v3",                                    │

│      │   │     created_at, updated_at                                     │

│      │   │   }                                                           │

│      │   └─ Store in MongoDB: base_case_recommendations collection       │

│      │                                                                   │

│      └─ Track document result:                                           │

│          {document_id, filename, status, recommendations_count,          │

│           relevant_entities_count, recommendations_id}                   │

└─────────────────────────────────────────────────────────────────────────┘

                              │

                              ▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 6: Finalize & Complete                                             │

│  ├─ Update scenario status → COMPLETED                                  │

│  ├─ Publish COMPLETE event (progress: 100%)                              │

│  │   meta:                                                               │

│  │   • documents_processed                                               │

│  │   • total_recommendations                                             │

│  │   • total_relevant_entities                                           │

│  └─ Cleanup: Remove task from _analysis_v3_tasks                         │

│                                                                          │

│  ERROR HANDLING:                                                         │

│  ├─ If exception occurs:                                                 │

│  │   ├─ Update scenario status → FAILED                                 │

│  │   ├─ Publish FAILED event (progress: 0%)                              │

│  │   │   meta: {error: str(e)}                                           │

│  │   └─ Log error with full traceback                                   │

│  └─ Always cleanup task registry                                        │

└─────────────────────────────────────────────────────────────────────────┘