<!-- e2f90abe-ee97-4d3b-844c-dd2a3e61a3aa 74148329-160a-48b6-b8d3-ec32680cc342 -->
# WebSocket ETL Progress Tracking Implementation

## Architecture Overview

**Backend Components:**

1. **WebSocket Router** (`backend/app_v2/api/v1/routers/websocket.py`) - FastAPI WebSocket endpoint for per-job connections
2. **Pub/Sub Manager** (`backend/app_v2/domain/parsing/progress.py`) - Abstract interface + in-memory implementation (Redis-ready)
3. **Progress Event Publisher** - Injected into DocumentProcessingService to emit checkpoints
4. **Background Task Runner** - ThreadPoolExecutor wrapper for async ETL processing
5. **Event Schema** - Standardized JSON envelope (stage, status, progress, seq, meta)
6. **Modified ETL Router** - Accept verbosity flags, return job_id, queue background task
7. **Modified Processing Service** - Emit progress events at key checkpoints

**Frontend Components:**

1. **WebSocket Hook** (`frontend/src/hooks/useETLProgress.jsx`) - React hook for WebSocket connection management
2. **Redux Slice** (`frontend/src/redux/etlProgressSlice.jsx`) - State management for progress tracking
3. **Progress UI Component** (`frontend/src/components/ETLProgressIndicator.jsx`) - Reusable progress display
4. **DocumentsTab Integration** - Connect WebSocket to existing upload flow

## Implementation Steps

### Phase 1: Backend Core Infrastructure

**1.1 Event Schema & Constants**

- File: `backend/app_v2/domain/parsing/progress.py`
- Define `ProgressEvent` dataclass with: stage, status, progress (0-100), seq, meta, job_id, timestamp
- Define stage constants: EXTRACTION, CHUNKING, ENTITY_EXTRACTION, VALIDATION, NORMALIZATION, STORAGE, COMPLETE, ERROR
- Define status constants: STARTED, IN_PROGRESS, COMPLETED, FAILED

**1.2 Pub/Sub Manager Interface**

- File: `backend/app_v2/domain/parsing/progress.py`
- Abstract base class `ProgressPublisher` with methods: `publish(job_id, event)`, `subscribe(job_id, callback)`, `unsubscribe(job_id)`
- In-memory implementation `InMemoryProgressPublisher` using dict + asyncio queues
- Design for easy swap to Redis later (same interface, different backend)

**1.3 WebSocket Router**

- File: `backend/app_v2/api/v1/routers/websocket.py`
- Endpoint: `/api/v1/ws/etl/{job_id}`
- Accepts job_id, validates connection, subscribes to progress events
- Emits events to connected client, handles disconnects gracefully
- Include connection management (track active connections per job_id)

**1.4 Background Task Runner**

- File: `backend/app_v2/domain/parsing/task_runner.py`
- ThreadPoolExecutor wrapper class
- Submit processing tasks, track job_ids, handle errors
- Integrate with progress publisher

### Phase 2: Processing Service Integration

**2.1 Progress Publisher Injection**

- File: `backend/app_v2/domain/parsing/services.py`
- Add optional `progress_publisher` parameter to `DocumentProcessingService.__init__`
- Add optional `job_id` and `verbosity` parameters to processing methods
- Create helper method `_emit_progress(stage, status, progress, meta=None)` for consistent event emission

**2.2 Checkpoint Integration**

- Modify `process_base_case_document()` to emit events at:
- Stage: EXTRACTION (after text extraction, include pages count)
- Stage: CHUNKING (after chunking, include chunks count; optionally emit per-chunk if verbosity=high)
- Stage: ENTITY_EXTRACTION (after LLM extraction, include nodes/edges counts)
- Stage: VALIDATION (after MSIO validation, include validation stats)
- Stage: NORMALIZATION (after normalization, include deduplication stats)
- Stage: STORAGE (after MongoDB/Pinecone storage, include counts)
- Stage: COMPLETE (final summary with all stats)
- Handle errors with ERROR stage events

### Phase 3: ETL Router Modifications

**3.1 Job ID Generation & Verbosity**

- File: `backend/app_v2/api/v1/routers/etl.py`
- Generate unique job_id (UUID) for each upload
- Accept optional `verbosity` parameter: "low" (default), "medium", "high"
- Return job_id immediately in response: `{"job_id": "...", "status": "queued"}`

**3.2 Background Processing**

- Modify `ingest_base_case_document()` to:
- Return job_id immediately (don't wait for processing)
- Submit processing task to background runner
- Pass job_id and verbosity to processing service
- Handle errors gracefully (emit ERROR event, don't crash)

### Phase 4: Frontend WebSocket Integration

**4.1 WebSocket Hook**

- File: `frontend/src/hooks/useETLProgress.jsx`
- Manages WebSocket connection lifecycle
- Connects on mount with job_id, disconnects on unmount
- Handles reconnection logic, message parsing
- Returns: `{ connected, progress, error, disconnect }`

**4.2 Redux Slice**

- File: `frontend/src/redux/etlProgressSlice.jsx`
- State: `{ jobs: { [jobId]: { stage, status, progress, meta, timestamp } } }`
- Actions: `updateProgress`, `resetProgress`, `setError`
- Selectors: `selectProgressByJobId`, `selectAllProgress`

**4.3 Progress UI Component**

- File: `frontend/src/components/ETLProgressIndicator.jsx`
- Displays timeline of stages with status indicators
- Shows progress bar when progress value available
- Displays meta information (counts, stats)
- Handles error states

**4.4 DocumentsTab Integration**

- File: `frontend/src/views/project/tabs/DocumentsTab.jsx`
- After upload starts, extract job_id from response
- Connect WebSocket using `useETLProgress` hook
- Display `ETLProgressIndicator` component
- Update existing progress indicators to use WebSocket data
- Handle completion and errors

### Phase 5: Main App Integration

**5.1 Register WebSocket Router**

- File: `backend/app_v2/main.py`
- Import and include websocket router
- Initialize global progress publisher instance (InMemoryProgressPublisher)

**5.2 Initialize Background Task Runner**

- In main.py lifespan, create ThreadPoolExecutor instance
- Pass to ETL router or create global instance

## Key Design Decisions

1. **Modularity**: Pub/sub interface allows Redis swap without API changes
2. **Simplicity**: Start with in-memory, add Redis layer later
3. **Verbosity Control**: Frontend sends enum, backend respects it in event emission
4. **Event Schema**: Fixed structure enables UI consistency and reconnection safety
5. **Error Handling**: All errors emit ERROR events, don't crash WebSocket connection
6. **Comments**: Extensive inline documentation explaining design choices

## Files to Create/Modify

**New Files:**

- `backend/app_v2/domain/parsing/progress.py` (pub/sub + event schema)
- `backend/app_v2/domain/parsing/task_runner.py` (background executor)
- `backend/app_v2/api/v1/routers/websocket.py` (WebSocket endpoint)
- `frontend/src/hooks/useETLProgress.jsx` (WebSocket hook)
- `frontend/src/redux/etlProgressSlice.jsx` (Redux state)
- `frontend/src/components/ETLProgressIndicator.jsx` (UI component)

**Modified Files:**

- `backend/app_v2/domain/parsing/services.py` (add progress emission)
- `backend/app_v2/api/v1/routers/etl.py` (job_id, background processing)
- `backend/app_v2/main.py` (register WebSocket router, init publisher)
- `frontend/src/views/project/tabs/DocumentsTab.jsx` (integrate WebSocket)