# File ingestion workflow

Prompt: sketch the pipeline of file ingestion workflow api e.g., `upload_project_files`

┌─────────────────────────────────────────────────────────────────────────┐

│                    API Endpoint: POST /{project_id}/upload-files        │

│                    Parameters: base_case_files, tabular_data_files       │

│                    Query: store_in_pinecone (default: True)              │

└─────────────────────────────────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 1: Authentication & Validation                                    │

│  ├─ Extract user_id from JWT token                                      │

│  ├─ Validate project exists (404 if not found)                          │

│  ├─ Validate file types:                                                │

│  │   • Base case: PDF only                                               │

│  │   • Tabular: PDF, Excel, CSV                                         │

│  └─ Validate total size < 25MB                                           │

└─────────────────────────────────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 2: File Upload & Storage (Sequential Processing)                  │

│                                                                          │

│  FOR EACH base_case_file:                                               │

│  ├─ Read file bytes                                                     │

│  ├─ Check total size limit                                              │

│  ├─ Store in GridFS via FileStorageService                              │

│  │   └─ Returns doc_id                                                  │

│  ├─ Add to base_case_doc_ids list                                       │

│  └─ If PDF: Add (file_bytes, filename, doc_id, "base_case")            │

│     to files_to_process queue                                            │

│                                                                          │

│  FOR EACH tabular_data_file:                                            │

│  ├─ Read file bytes                                                     │

│  ├─ Check total size limit                                              │

│  ├─ Store in GridFS via FileStorageService                              │

│  │   └─ Returns doc_id                                                  │

│  ├─ Add to tabular_doc_ids list                                         │

│  └─ If PDF: Add (file_bytes, filename, doc_id, "tabular_data")          │

│     to files_to_process queue                                            │

└─────────────────────────────────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 3: Project Update                                                  │

│  ├─ Merge new base_case_doc_ids with existing                           │

│  ├─ Merge new tabular_doc_ids with existing                             │

│  └─ Update project document via ProjectService.update()                 │

└─────────────────────────────────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────────────────┐

│  STEP 4: Background Task Setup (if files_to_process not empty)          │

│  ├─ Generate unique job_id (UUID)                                       │

│  ├─ Publish START progress event via ProgressPublisher                  │

│  ├─ Create asyncio background task:                                     │

│  │   _process_uploaded_files_background(                                 │

│  │     job_id, files_to_process, project_id,                            │

│  │     user_id, store_in_pinecone                                       │

│  │   )                                                                   │

│  ├─ Register task in _upload_processing_tasks dict                      │

│  └─ Return response with job_id and websocket_url                       │

│                                                                          │

│  If no PDFs to process:                                                 │

│  └─ Return success response (no background task)                        │

└─────────────────────────────────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────────────────┐

│  BACKGROUND TASK: _process_uploaded_files_background                     │

│  (Runs asynchronously, publishes progress via WebSocket)                 │

└─────────────────────────────────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────────────────┐

│  FOR EACH file in files_to_process (Sequential):                        │

│                                                                          │

│  ├─ Publish FILE_START progress event                                   │

│  │   (progress: (idx-1)/total * 100)                                    │

│  │                                                                       │

│  ├─ Route by artifact_type:                                            │

│  │                                                                       │

│  │   IF artifact_type == "base_case":                                   │

│  │   └─ orchestration.process_base_case_file()                          │

│  │      ├─ Extract text from PDF (TextExtractor)                        │

│  │      ├─ Chunk text (CharacterChunker)                                │

│  │      ├─ Extract entities & edges (EntityExtractor + LLM)             │

│  │      ├─ Normalize & deduplicate entities                             │

│  │      ├─ Store chunks in MongoDB                                     │

│  │      ├─ Store entities & edges in MongoDB                            │

│  │      └─ IF store_in_pinecone=True:                                   │

│  │         ├─ Vectorize chunks → Store in Pinecone                      │

│  │         └─ Vectorize entities → Store in Pinecone                    │

│  │                                                                       │

│  │   IF artifact_type == "tabular_data":                                │

│  │   └─ orchestration.process_tabular_data_file()                      │

│  │      ├─ Extract tables from PDF (TableExtractor)                     │

│  │      ├─ Extract entities from tables (EntityExtractor + LLM)         │

│  │      ├─ Store tables in MongoDB                                      │

│  │      ├─ Store entities & edges in MongoDB                             │

│  │      └─ IF store_in_pinecone=True:                                   │

│  │         └─ Vectorize entities → Store in Pinecone                    │

│  │                                                                       │

│  └─ Publish FILE_COMPLETE progress event                                │

│     (progress: idx/total * 100, includes stats)                         │

└─────────────────────────────────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────────────────┐

│  FINAL STEP: Completion                                                  │

│  ├─ Publish COMPLETE/FAILED progress event                              │

│  │   (includes: successful_files, failed_files, errors)                 │

│  └─ Cleanup: Remove task from _upload_processing_tasks                  │

└─────────────────────────────────────────────────────────────────────────┘

## Data Flow Summary

Storage Locations:

1. GridFS: Raw file bytes (via FileStorageService)

1. MongoDB:

- documents collection: File metadata

- chunks collection: Text chunks (base_case only)

- entities collection: Extracted entities

- relations collection: Entity relationships/edges

- tables collection: Extracted tables (tabular_data only)

1. Pinecone (if store_in_pinecone=True):

- Chunk vectors (base_case only)

- Entity vectors (both base_case and tabular_data)

- Namespace: project_id

- Metadata: Includes project_id, artifact_type, entity_type, etc.

Progress Tracking:

- Real-time progress via WebSocket: /api/v1/ws/progress/{job_id}

- Events: START → FILE_START → FILE_COMPLETE → ... → COMPLETE/FAILED

- Progress percentage: 0% → 100% based on files processed

Error Handling:

- Validation errors: Return 400 immediately

- Background processing errors: Logged, included in final progress event

- Partial success: Some files may succeed while others fail

This pipeline supports parallel uploads, sequential background processing, and real-time progress updates.