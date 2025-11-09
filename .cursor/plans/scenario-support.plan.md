<!-- e2f90abe-ee97-4d3b-844c-dd2a3e61a3aa 1f8f41b5-2e20-4cdd-b429-06ecf7da8eb7 -->
# Scenario Analysis Backend Implementation Plan

## Overview

Implement complete backend support for scenario analysis workflow, following app_v2 patterns and integrating with existing entity/relation infrastructure.

## Architecture

Follow existing domain-driven structure:

- **Router**: `app_v2/api/v1/routers/scenarios.py` - FastAPI endpoints
- **Service**: `app_v2/domain/scenarios/services.py` - Business logic orchestration
- **Repository**: `app_v2/domain/scenarios/repository.py` - MongoDB operations
- **Schemas**: `app_v2/domain/scenarios/schemas.py` - Pydantic models
- **Models**: `app_v2/domain/scenarios/models.py` - Domain models (if needed)
- **Analyzers**: `app_v2/domain/scenarios/analyzers/` - LLM analysis components
- **Resizers**: `app_v2/domain/scenarios/resizers/` - System resizing logic
- **Reporters**: `app_v2/domain/scenarios/reporters/` - Report generation

## Implementation Steps

### 1. Data Models and Schemas (`schemas.py`)

Create Pydantic schemas for:

- **ScenarioBase**: Core scenario fields (name, description, project_id, goal, change_type, change_magnitude, status)
- **ScenarioCreate**: For creating new scenarios
- **ScenarioUpdate**: For updating scenarios (partial updates)
- **ScenarioOut**: Output schema with all fields including id, timestamps
- **GlobalObjective**: Type and change specification (goal_type, change_direction, change_magnitude, change_unit)
- **LocalObjective**: Entity-parameter pairs with relevance scores
- **UserConstraints**: FIXED/VARIABLE attributes with value ranges
- **ScenarioAnalysis**: Results from LLM analysis (relevant_entities, local_objectives, assumptions, constraints)
- **SystemResizing**: Resized entity values and calculations
- **CostEstimationData**: Prepared cost data for estimation
- **ScenarioRecommendation**: System recommendation with approach options
- **ScenarioReport**: Optional formatted report data

### 2. Repository Layer (`repository.py`)

Implement MongoDB operations:

- `create_scenario()` - Insert new scenario document
- `get_scenario(scenario_id)` - Retrieve by ID
- `list_scenarios_by_project(project_id)` - List all scenarios for a project
- `update_scenario(scenario_id, update_data)` - Partial update
- `delete_scenario(scenario_id)` - Soft or hard delete
- `get_scenario_with_analysis(scenario_id)` - Include analysis results
- Use `_scenarios_collection` from mongo client
- Follow normalization patterns from `projects/repository.py`
- Store scenario state: draft, analyzing, ready, archived

### 3. Entity Analysis Component (`analyzers/entity_analyzer.py`)

Create analyzer that:

- Queries existing entities from base case using `projects/repository.py` functions
- Filters entities by artifact_type="base_case" and project_id
- Uses LLM to analyze entity relevance to global objective
- Identifies local objectives (entity-parameter pairs)
- Extracts assumptions, constraints, policies from base case
- Returns structured analysis following scenario prompt patterns
- Reuses entity extraction infrastructure patterns

### 4. LLM Prompt (`analyzers/scenario_analysis_prompt.py`)

Create new prompt following app_v2 patterns:

- Based on `prompt_for_scenarios.py` but adapted for app_v2 structure
- Use LangChain message format (SystemMessage, HumanMessage)
- Include MSIO ontology context
- Focus on identifying relevant entities and local objectives
- Output structured JSON matching ScenarioAnalysis schema
- Follow patterns from `entity_extraction_prompt.py`

### 5. System Resizing Component (`resizers/system_resizer.py`)

Implement hybrid resizing:

- **LLM Phase**: Identify which entities/parameters need resizing based on global objective
- **Algorithm Phase**: Calculate new values using:
- Percentage-based scaling for production changes
- Cost exponent rules (C2 = C1 * (S2/S1)^n) for equipment
- Linear scaling where appropriate
- User-provided constraints (FIXED/VARIABLE, ranges)
- Store original and resized values
- Track calculation methods and confidence

### 6. Cost Estimation Preparation (`analyzers/cost_preparator.py`)

Prepare cost estimation data:

- Identify relevant cost reference data (tabular_data documents)
- Extract cost guidelines and scaling rules
- Map entities to cost items
- Prepare cost drivers and sensitivity analysis
- Optionally generate cost estimates if user preference enabled
- Store in cost_estimates collection if generated

### 7. Recommendation Builder (`analyzers/recommendation_builder.py`)

Build system recommendations:

- Analyze global objectives, local objectives, and user constraints
- Generate approach options (e.g., "upsize pump", "add parallel train")
- Calculate expected effects (throughput, capex, opex, quality)
- Identify dependencies and risks
- Rank options by feasibility and impact
- Return structured recommendation data

### 8. Report Generator (`reporters/scenario_reporter.py`)

Generate optional reports:

- Format scenario analysis as markdown/structured text
- Include summary, relevant entities, resizing results, recommendations
- Support JSON export
- Future: PDF generation (not in Part 1)

### 9. Service Layer (`services.py`)

Orchestrate scenario workflow:

- `create_scenario(data)` - Create and store scenario
- `analyze_scenario(scenario_id)` - Run LLM analysis of relevant entities
- `resize_system(scenario_id, user_constraints)` - Apply resizing logic
- `build_recommendation(scenario_id)` - Generate recommendations
- `prepare_cost_estimation(scenario_id, generate_estimates=False)` - Prepare/generate cost data
- `generate_report(scenario_id, format='json')` - Generate optional report
- `get_scenario(scenario_id)` - Retrieve with all related data
- `list_scenarios(project_id)` - List all scenarios for project
- `update_scenario(scenario_id, data)` - Update scenario
- `delete_scenario(scenario_id)` - Delete scenario

### 10. API Router (`routers/scenarios.py`)

Create FastAPI endpoints:

- `POST /api/v1/scenarios/` - Create scenario
- `GET /api/v1/scenarios/{scenario_id}` - Get scenario details
- `GET /api/v1/projects/{project_id}/scenarios` - List scenarios for project
- `PATCH /api/v1/scenarios/{scenario_id}` - Update scenario
- `DELETE /api/v1/scenarios/{scenario_id}` - Delete scenario
- `POST /api/v1/scenarios/{scenario_id}/analyze` - Run entity analysis
- `POST /api/v1/scenarios/{scenario_id}/resize` - Apply system resizing
- `POST /api/v1/scenarios/{scenario_id}/recommend` - Build recommendations
- `POST /api/v1/scenarios/{scenario_id}/cost-estimation` - Prepare/generate cost data
- `GET /api/v1/scenarios/{scenario_id}/report` - Generate report (optional)

### 11. Integration Points

- **Entity/Relation Access**: Use `projects/repository.py` functions to query entities
- **Document Access**: Query base case documents for text extraction if needed
- **Cost Estimates**: Integrate with cost_estimates collection
- **LLM Configuration**: Use `adapters/config.py` SETTINGS for API keys
- **Logging**: Use structured logging throughout
- **Error Handling**: Consistent error responses following FastAPI patterns

### 12. Testing (`tests/test_scenarios.py`)

Create test cases:

- Test CRUD operations
- Test entity analysis with mock LLM responses
- Test system resizing calculations
- Test cost estimation preparation
- Test recommendation building
- Test error handling
- Mock MongoDB and LLM calls

### 13. Registration

- Register scenarios router in `main.py`
- Ensure MongoDB indexes in `adapters/mongo/client.py` (already has scenarios collection)

## Key Design Decisions

1. **Entity Analysis**: Query existing entities from MongoDB, then use LLM to analyze relevance and extract local objectives
2. **Resizing**: LLM identifies what to resize, deterministic algorithms calculate new values
3. **Prompts**: New prompts following app_v2 LangChain patterns, inspired by existing scenario prompts
4. **Cost Estimates**: Prepare data always, generate estimates optionally based on user preference
5. **Reports**: Return JSON always, optionally generate formatted reports
6. **State Management**: Track scenario status (draft → analyzing → ready → archived)
7. **Async Operations**: Analysis and resizing can be long-running; consider background tasks for future

## Files to Create/Modify

**New Files:**

- `app_v2/api/v1/routers/scenarios.py`
- `app_v2/domain/scenarios/schemas.py` (populate)
- `app_v2/domain/scenarios/repository.py` (populate)
- `app_v2/domain/scenarios/services.py` (populate)
- `app_v2/domain/scenarios/analyzers/__init__.py`
- `app_v2/domain/scenarios/analyzers/entity_analyzer.py`
- `app_v2/domain/scenarios/analyzers/scenario_analysis_prompt.py`
- `app_v2/domain/scenarios/analyzers/cost_preparator.py`
- `app_v2/domain/scenarios/analyzers/recommendation_builder.py`
- `app_v2/domain/scenarios/resizers/__init__.py`
- `app_v2/domain/scenarios/resizers/system_resizer.py`
- `app_v2/domain/scenarios/reporters/__init__.py`
- `app_v2/domain/scenarios/reporters/scenario_reporter.py`
- `app_v2/tests/test_scenarios.py`

**Modify Files:**

- `app_v2/main.py` - Register scenarios router
- `app_v2/adapters/mongo/client.py` - Ensure scenarios collection indexes (verify existing)

## Dependencies

- Existing: projects repository, entity/relation data, LLM infrastructure
- New: Scenario-specific LLM prompts, resizing algorithms, cost estimation logic
- External: OpenAI API (via LangChain), MongoDB, existing vector store (for entity queries)

## Success Criteria

- All CRUD operations work correctly
- Entity analysis identifies relevant entities from base case
- System resizing calculates new values correctly
- Recommendations are generated with approach options
- Cost estimation data is prepared correctly
- Optional reports can be generated
- All endpoints return proper error responses
- Tests pass for all major functionality

### To-dos

- [ ] Create Pydantic schemas in app_v2/domain/scenarios/schemas.py: ScenarioBase, ScenarioCreate, ScenarioUpdate, ScenarioOut, GlobalObjective, LocalObjective, UserConstraints, ScenarioAnalysis, SystemResizing, CostEstimationData, ScenarioRecommendation, ScenarioReport
- [ ] Implement MongoDB repository in app_v2/domain/scenarios/repository.py: create_scenario, get_scenario, list_scenarios_by_project, update_scenario, delete_scenario, get_scenario_with_analysis
- [ ] Create LLM prompt in app_v2/domain/scenarios/analyzers/scenario_analysis_prompt.py following app_v2 patterns, adapted from existing scenario prompts
- [ ] Implement entity analyzer in app_v2/domain/scenarios/analyzers/entity_analyzer.py: query entities from base case, use LLM to analyze relevance, extract local objectives
- [ ] Implement hybrid resizing in app_v2/domain/scenarios/resizers/system_resizer.py: LLM identifies what to resize, algorithms calculate new values using scaling rules
- [ ] Implement cost estimation preparation in app_v2/domain/scenarios/analyzers/cost_preparator.py: identify cost reference data, extract guidelines, optionally generate estimates
- [ ] Implement recommendation builder in app_v2/domain/scenarios/analyzers/recommendation_builder.py: analyze objectives and constraints, generate approach options, rank by feasibility
- [ ] Implement report generator in app_v2/domain/scenarios/reporters/scenario_reporter.py: format analysis as JSON/markdown, include summary and recommendations
- [ ] Implement service layer in app_v2/domain/scenarios/services.py: orchestrate create, analyze, resize, recommend, cost_estimation, report, get, list, update, delete operations
- [ ] Create FastAPI router in app_v2/api/v1/routers/scenarios.py: implement all CRUD endpoints plus analyze, resize, recommend, cost-estimation, report endpoints
- [ ] Register scenarios router in app_v2/main.py and verify MongoDB indexes in app_v2/adapters/mongo/client.py
- [ ] Create test cases in app_v2/tests/test_scenarios.py: test CRUD, analysis, resizing, recommendations, cost estimation, error handling with mocked dependencies