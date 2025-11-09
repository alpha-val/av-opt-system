# Plan for implementing scenarios

## Workflow

- Workflow: the overall system workflow is as follows
- Ingest base case report (unstructured data ingestion)
- ETL - parse, clean, chunks -> NER, entity, chunks, storage (mongo and vector DB)
- Ingest (optional) cost reference data (structured data ingestion)
- ETL - parse, clean, extract tables -> chunks, NER, entity, chunks, storage (mongo and vector DB)
- Scenario analysis
- Objective specification: Scenario global objective specification, with parts (1) type ("increase production" or "reduce capex"), and (2) % or value change
- LLM analysis of relevant entities: Identify relevant entities in base case report for part (1) of scenario global objective
- System resizing based on part (2) of global objective
- User provides additional constraints, e.g., set attributes to FIXED or VARIABLE, and provide attribute value ranges
- LLM analyzes the specs containing (1) Global objectives, (2) Local objectives, (3) User inputs
- Build system recommendation
- Identify tabular / costing reference data ingested
- Build costing profile
- Create a report

## Implementation Plan

- Build a plan to implement support for scenario analysis
- Build it in two phases, first on backend, then on frontend

## Part 1

- Create the following
- API: @app_v2/backend/api/v1/routers/scenarios.py
- Relevant files in @app_v2/backend/api/v1/domain/scenarios/.
- Write code for CRUD operations on scenarios, analysis, and reporting
- Write test cases in @app_v2/backend/tests/.

## Part 2

- Update the scenario slice in @frontend/src/redux/. to include the necessary operations using the backend api
- The scenario user interface will be shown under the "Scenarios" tab in the frontend @frontend/src/views/project/tabs/ScenariosTab.jsx
- A button "Add New Scenario" which will bring up a dialog to create a new scenario and provide global objectives
- A dashboard showing scenario cards, clicking on which the user will shown a page where they can specify and develop the scenario
- Options on the scenario card for viewing and deleting corresponding scenarios
- Update the project statistics when new scenarios are created or deleted (count updates)