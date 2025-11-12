"""
Project orchestration service.

This module provides high-level orchestration of project workflows including
document processing, entity extraction, validation, and report generation.
It integrates with existing document processing services to coordinate
the scenario-first project workflow.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
import uuid
import json

# Import LLM components
from app_v2.adapters.config import SETTINGS
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import MongoDB client
from ...adapters.mongo.client import db

# Import parsing utilities
from ..parsing.utils.llm_tools import TOOLS, is_valid_json, sanitize_for_json
from ..parsing.prompts.entity_extraction_prompt import (
    PROMPT_DISCIPLINE_STRUCTURED_SUMMARY,
)

logger = logging.getLogger(__name__)


class ProjectOrchestrationService:
    """
    Service for orchestrating project workflows.

    This service coordinates document processing, entity extraction,
    validation, and report generation for projects. It acts as a
    high-level orchestrator that integrates with existing domain services.

    Note: This is a placeholder implementation. Actual orchestration
    logic will be implemented later.
    """

    def __init__(self, file_storage_service=None, document_processing_service=None):
        """
        Initialize the orchestration service.

        Args:
            file_storage_service: Optional FileStorageService instance for retrieving files from GridFS
            document_processing_service: Optional DocumentProcessingService instance for processing documents

        In the future, this will inject dependencies like:
        - CostEstimationService
        - ReportGenerator
        """
        self._file_storage_service = file_storage_service
        self._document_processing_service = document_processing_service

        # Initialize LLM for recommendations extraction
        self._llm = ChatOpenAI(
            model=SETTINGS.llm_model_name or "gpt-4o",
            api_key=SETTINGS.openai_api_key,
            timeout=300,
            max_retries=3,
            temperature=0,
            max_tokens=4096,
            model_kwargs={
                "tools": TOOLS,
                "tool_choice": "auto",
            },
        )

        logger.info("Initialized ProjectOrchestrationService")

    async def process_project_documents(
        self,
        project_id: str,
        global_objective_type: str,
        global_objective_target: str,
        base_case_document_ids: List[str],
        tabular_data_document_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Orchestrate document processing for a project.

        This method coordinates the processing of base case documents
        and tabular data documents, using the global objectives to guide
        entity extraction and processing.

        Args:
            project_id: Project identifier
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            base_case_document_ids: List of base case document IDs (GridFS file IDs)
            tabular_data_document_ids: List of tabular data document IDs (GridFS file IDs)

        Returns:
            Dictionary with processing results and statistics

        Note:
            This is a placeholder. Actual implementation will:
            1. Retrieve files from GridFS using FileStorageService
            2. Process base case documents using DocumentProcessingService
            3. Process tabular data documents
            4. Extract entities using LLM with global objectives
            5. Return processing results
        """
        logger.info(
            f"Processing documents for project {project_id} "
            f"(objective: {global_objective_type}, target: {global_objective_target})"
        )

        # Retrieve files from GridFS if file storage service is available
        if self._file_storage_service:
            logger.info(
                f"Retrieving {len(base_case_document_ids)} base case files and {len(tabular_data_document_ids)} tabular data files from GridFS"
            )

            # Retrieve base case files
            base_case_files = []
            for doc_id in base_case_document_ids:
                file_bytes = self._file_storage_service.get_file(doc_id)
                if file_bytes:
                    metadata = self._file_storage_service.get_file_metadata(doc_id)
                    base_case_files.append(
                        {
                            "file_id": doc_id,
                            "content": file_bytes,
                            "filename": (
                                metadata.get("filename", "unknown.pdf")
                                if metadata
                                else "unknown.pdf"
                            ),
                        }
                    )
                    logger.debug(
                        f"Retrieved base case file: {doc_id} ({len(file_bytes)} bytes)"
                    )
                else:
                    logger.warning(f"Failed to retrieve base case file: {doc_id}")

            # Retrieve tabular data files
            tabular_data_files = []
            for doc_id in tabular_data_document_ids:
                file_bytes = self._file_storage_service.get_file(doc_id)
                if file_bytes:
                    metadata = self._file_storage_service.get_file_metadata(doc_id)
                    tabular_data_files.append(
                        {
                            "file_id": doc_id,
                            "content": file_bytes,
                            "filename": (
                                metadata.get("filename", "unknown")
                                if metadata
                                else "unknown"
                            ),
                        }
                    )
                    logger.debug(
                        f"Retrieved tabular data file: {doc_id} ({len(file_bytes)} bytes)"
                    )
                else:
                    logger.warning(f"Failed to retrieve tabular data file: {doc_id}")

            logger.info(
                f"Retrieved {len(base_case_files)} base case files and {len(tabular_data_files)} tabular data files from GridFS"
            )

            # TODO: Pass file content to DocumentProcessingService for actual processing
            # For now, this is a placeholder that just confirms files were retrieved

        # Placeholder implementation
        return {
            "project_id": project_id,
            "status": "processing",
            "base_case_documents_processed": len(base_case_document_ids),
            "tabular_data_documents_processed": len(tabular_data_document_ids),
            "message": "Document processing orchestration (placeholder - files retrieved from GridFS)",
        }

    async def extract_base_case_entities(
        self,
        project_id: str,
        document_id: str,
        global_objective_type: str,
        global_objective_target: str,
        user_id: str,
        scenario_id: str,
        objective_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract entities from a base case document using LLM.

        This method uses the global objectives to generate prompts
        for entity extraction, ensuring extracted entities are relevant
        to the project's goals. It also extracts document summaries,
        generates recommendations, and identifies entities for cost estimation.

        Args:
            project_id: Project identifier
            document_id: Document identifier (GridFS file ID)
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            user_id: User identifier
            scenario_id: Scenario identifier
            objective_description: Optional description of the global objective

        Returns:
            Dictionary with extracted entities, summary, recommendations, and metadata

        Raises:
            RuntimeError: If required services are not initialized
        """
        logger.info(
            f"Extracting entities from document {document_id} "
            f"for project {project_id} (objective: {global_objective_type}, target: {global_objective_target})"
        )

        # Validate services are available
        if not self._file_storage_service:
            raise RuntimeError("FileStorageService not initialized")
        if not self._document_processing_service:
            raise RuntimeError("DocumentProcessingService not initialized")

        try:
            # Step 1: Retrieve document from GridFS
            file_bytes = self._file_storage_service.get_file(document_id)
            if not file_bytes:
                raise ValueError(f"Document not found: {document_id}")

            metadata = self._file_storage_service.get_file_metadata(document_id)
            filename = (
                metadata.get("filename", "unknown.pdf") if metadata else "unknown.pdf"
            )

            logger.info(f"Retrieved document {document_id} ({len(file_bytes)} bytes)")

            # Step 2: Process document through DocumentProcessingService
            # This extracts entities and stores them in MongoDB
            processing_result = (
                self._document_processing_service.process_base_case_document(
                    pdf_bytes=file_bytes,
                    filename=filename,
                    doc_id=document_id,
                    project_id=project_id,
                    user_id=user_id,
                    chunking_strategy="character",
                    char_limit=5000,
                )
            )

            entities_extracted = processing_result.get("entities_extracted", 0)
            edges_extracted = processing_result.get("edges_extracted", 0)

            logger.info(
                f"Processed document: {entities_extracted} entities, {edges_extracted} edges extracted"
            )

            # Step 3: Query extracted entities from MongoDB and update with scenario_id
            from ..parsing.storage.document_store import DocumentStore

            document_store = DocumentStore()
            extracted_entities = document_store.get_entities_by_doc_id(document_id)
            
            # Update entities and relations with scenario_id
            if extracted_entities:
                entities_updated = document_store.update_entities_scenario_id(
                    document_id=document_id,
                    scenario_id=scenario_id
                )
                relations_updated = document_store.update_relations_scenario_id(
                    document_id=document_id,
                    scenario_id=scenario_id
                )
                logger.info(
                    f"Updated {entities_updated} entities and {relations_updated} relations "
                    f"with scenario_id {scenario_id}"
                )

            # Step 4: Extract full text for summary and recommendations
            from ..parsing.extractors.text_extractor import TextExtractor

            text_extractor = TextExtractor()
            _, _, _, pages_clean = text_extractor.extract(file_bytes, filename, None)
            full_text = text_extractor.extract_full_text(pages_clean)

            # Step 5: Extract structured summary using LLM
            summary = await self._extract_document_summary(
                full_text=full_text,
                filename=filename,
                document_id=document_id,
            )

            # Step 6: Extract recommendations and identify entities for costing
            recommendations_result = await self._extract_recommendations_and_entities(
                full_text=full_text,
                entities=extracted_entities,
                global_objective_type=global_objective_type,
                global_objective_target=global_objective_target,
                objective_description=objective_description,
                document_id=document_id,
            )

            recommendations = recommendations_result.get("recommendations", [])
            entities_for_costing = recommendations_result.get(
                "entities_for_costing", []
            )

            # Step 7: Store summary and recommendations in MongoDB
            summary_id = await self._store_summary(
                document_id=document_id,
                project_id=project_id,
                scenario_id=scenario_id,
                summary=summary,
            )

            recommendations_id = await self._store_recommendations(
                document_id=document_id,
                project_id=project_id,
                scenario_id=scenario_id,
                global_objective_type=global_objective_type,
                global_objective_target=global_objective_target,
                recommendations=recommendations,
            )

            logger.info(
                f"Stored summary (id: {summary_id}) and recommendations (id: {recommendations_id})"
            )

            # Step 8: Return structured response
            return {
                "document_id": document_id,
                "project_id": project_id,
                "processing_status": "success",
                "summary": summary,
                "summary_id": summary_id,
                "entities_extracted": entities_extracted,
                "relations_extracted": edges_extracted,
                "entities_for_costing": entities_for_costing,
                "recommendations": recommendations,
                "recommendations_id": recommendations_id,
                "statistics": {
                    "pages": processing_result.get("pages", 0),
                    "chunks_created": processing_result.get("chunks_created", 0),
                    "chunks_stored": processing_result.get("chunks_stored", 0),
                    "entities_stored": processing_result.get("entities_stored", 0),
                    "edges_stored": processing_result.get("edges_stored", 0),
                },
            }

        except Exception as e:
            logger.error(
                f"Error extracting entities from document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "document_id": document_id,
                "project_id": project_id,
                "processing_status": "error",
                "error": str(e),
                "entities_extracted": 0,
                "relations_extracted": 0,
                "summary": None,
                "recommendations": [],
                "entities_for_costing": [],
            }

    async def _extract_document_summary(
        self,
        full_text: str,
        filename: str,
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Extract structured document summary using LLM.

        Args:
            full_text: Full text content of the document
            filename: Original filename
            document_id: Document identifier

        Returns:
            Dictionary with structured summary
        """
        logger.info(f"Extracting structured summary for document {document_id}")

        try:
            # Build prompt for structured summary extraction
            system_prompt = SystemMessage(content=PROMPT_DISCIPLINE_STRUCTURED_SUMMARY)
            human_message = HumanMessage(
                content=f"BASE_CASE_TEXT:\n{full_text}\n\nExtract structured summary following the format specified."
            )

            messages = [system_prompt, human_message]
            resp = self._llm.invoke(messages)

            # Process tool calls
            summary = {}
            for call in resp.additional_kwargs.get("tool_calls", []):
                fn = call.get("function", {})
                name = fn.get("name")

                if name == "extract_structured_report":
                    arguments = fn.get("arguments", "{}")
                    if is_valid_json(arguments):
                        payload = json.loads(arguments)
                        payload = sanitize_for_json(payload)
                        summary = payload.get("base_case_extract", {})
                        break

            if not summary:
                logger.warning(f"No summary extracted for document {document_id}")
                summary = {
                    "doc_header": {"filename": filename, "document_id": document_id},
                    "sections": [],
                    "process_flows": {},
                    "design_criteria": {},
                    "equipment": [],
                    "materials": [],
                    "instrumentation_controls": [],
                    "site_data": [],
                    "codes_standards": [],
                    "policies_recommendations": [],
                    "constraints": [],
                    "costs": [],
                    "risks_uncertainties": [],
                    "provenance": {},
                }

            logger.info(f"Extracted summary for document {document_id}")
            return summary

        except Exception as e:
            logger.error(
                f"Error extracting summary for document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "doc_header": {"filename": filename, "document_id": document_id},
                "sections": [],
                "error": str(e),
            }

    async def _extract_recommendations_and_entities(
        self,
        full_text: str,
        entities: List[Dict[str, Any]],
        global_objective_type: str,
        global_objective_target: str,
        objective_description: Optional[str],
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Extract recommendations and identify entities for cost estimation.

        Args:
            full_text: Full text content of the document
            entities: List of extracted entities
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            objective_description: Optional description of the global objective
            document_id: Document identifier

        Returns:
            Dictionary with recommendations and entities_for_costing
        """
        logger.info(
            f"Extracting recommendations for objective: {global_objective_type} ({global_objective_target})"
        )

        try:
            # Build prompt for recommendations extraction
            objective_context = f"""
GLOBAL OBJECTIVE:
- Type: {global_objective_type}
- Target: {global_objective_target}
"""
            if objective_description:
                objective_context += f"- Description: {objective_description}\n"

            # Create summary of entities for context
            entities_summary = self._create_entities_summary(entities)

            # Limit text to avoid token limits (keep first 50000 chars)
            text_for_analysis = (
                full_text[:50000] if len(full_text) > 50000 else full_text
            )

            recommendations_prompt = f"""
You are an expert process engineer and cost estimator analyzing a base case engineering report.

{objective_context}

TASK:
1. Analyze the base case document and extracted entities in the context of the global objective.
2. Generate specific recommendations for system redesign to meet the objective.
3. Identify which entities are most relevant for cost estimation queries.

BASE CASE TEXT:
{text_for_analysis}

EXTRACTED ENTITIES SUMMARY:
{entities_summary}

INSTRUCTIONS:
- Generate recommendations that address what needs to change to meet the objective.
- For each recommendation, identify which entities should be modified/replaced.
- Prioritize recommendations based on impact and feasibility.
- Identify entities that are critical for cost estimation (equipment, materials, processes with cost implications).
- Provide cost relevance scores (0.0-1.0) for each entity based on its importance for costing.

Use the extract_recommendations tool to provide your analysis.
"""

            system_prompt = SystemMessage(
                content="You are an expert process engineer and cost estimator. Analyze base case documents and provide recommendations for system redesign based on global objectives."
            )
            human_message = HumanMessage(content=recommendations_prompt)

            messages = [system_prompt, human_message]
            resp = self._llm.invoke(messages)

            # Process tool calls
            recommendations = []
            entities_for_costing = []

            for call in resp.additional_kwargs.get("tool_calls", []):
                fn = call.get("function", {})
                name = fn.get("name")

                if name == "extract_recommendations":
                    arguments = fn.get("arguments", "{}")
                    if is_valid_json(arguments):
                        payload = json.loads(arguments)
                        payload = sanitize_for_json(payload)
                        recommendations = payload.get("recommendations", [])
                        entities_for_costing = payload.get("entities_for_costing", [])
                        break

            # If no recommendations extracted, create default structure
            if not recommendations:
                logger.warning(
                    f"No recommendations extracted for document {document_id}"
                )
                recommendations = []

            # If no entities for costing identified, use all equipment/material entities
            if not entities_for_costing:
                entities_for_costing = self._identify_default_entities_for_costing(
                    entities
                )

            logger.info(
                f"Extracted {len(recommendations)} recommendations and "
                f"{len(entities_for_costing)} entities for costing"
            )

            return {
                "recommendations": recommendations,
                "entities_for_costing": entities_for_costing,
            }

        except Exception as e:
            logger.error(
                f"Error extracting recommendations for document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "recommendations": [],
                "entities_for_costing": self._identify_default_entities_for_costing(
                    entities
                ),
            }

    def _create_entities_summary(self, entities: List[Dict[str, Any]]) -> str:
        """
        Create a summary of extracted entities for LLM context.

        Args:
            entities: List of entity dictionaries

        Returns:
            String summary of entities
        """
        if not entities:
            return "No entities extracted yet."

        # Group entities by type
        by_type = {}
        for entity in entities[:100]:  # Limit to first 100 entities
            entity_type = entity.get("type", "Unknown")
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(
                {
                    "id": entity.get("id", ""),
                    "name": entity.get("name", ""),
                    "properties": entity.get("properties", {}),
                }
            )

        summary_parts = []
        for entity_type, items in by_type.items():
            summary_parts.append(f"\n{entity_type} ({len(items)} items):")
            for item in items[:10]:  # Limit to 10 per type
                props = item.get("properties", {})
                msio = f"{props.get('discipline', '')} > {props.get('category', '')} > {props.get('subcategory', '')} > {props.get('entity', '')}"
                summary_parts.append(
                    f"  - {item.get('name', 'Unnamed')} (id: {item.get('id', '')}, MSIO: {msio})"
                )

        return "\n".join(summary_parts)

    def _identify_default_entities_for_costing(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify default entities for cost estimation when LLM doesn't provide them.

        Args:
            entities: List of entity dictionaries

        Returns:
            List of entities identified for costing
        """
        costing_entity_types = ["Equipment", "Material", "Process", "CostItem"]
        entities_for_costing = []

        for entity in entities:
            entity_type = entity.get("type", "")
            if entity_type in costing_entity_types:
                props = entity.get("properties", {})
                entities_for_costing.append(
                    {
                        "entity_id": entity.get("id", ""),
                        "entity_name": entity.get("name", ""),
                        "entity_type": entity_type,
                        "msio_classification": {
                            "discipline": props.get("discipline", ""),
                            "category": props.get("category", ""),
                            "subcategory": props.get("subcategory", ""),
                            "entity": props.get("entity", ""),
                        },
                        "key_attributes": {
                            k: v
                            for k, v in props.items()
                            if k
                            not in [
                                "discipline",
                                "category",
                                "subcategory",
                                "entity",
                                "doc_id",
                                "project_id",
                                "user_id",
                            ]
                        },
                        "query_metadata": {
                            "normalized_attributes": {},
                            "units": {},
                            "ranges": {},
                        },
                        "cost_relevance_score": (
                            0.8 if entity_type == "Equipment" else 0.6
                        ),
                    }
                )

        return entities_for_costing[:50]  # Limit to 50 entities

    async def _store_summary(
        self,
        document_id: str,
        project_id: str,
        scenario_id: str,
        summary: Dict[str, Any],
    ) -> str:
        """
        Store document summary in MongoDB.
        
        Args:
            document_id: Document identifier
            project_id: Project identifier
            scenario_id: Scenario identifier
            summary: Summary dictionary
            
        Returns:
            Summary document ID
        """
        try:
            summary_id = str(uuid.uuid4())
            summary_doc = {
                "_id": summary_id,
                "id": summary_id,
                "document_id": document_id,
                "project_id": project_id,
                "scenario_id": scenario_id,
                "summary": summary,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            db().base_case_summaries.replace_one(
                {"_id": summary_id}, summary_doc, upsert=True
            )

            logger.info(f"Stored summary {summary_id} for document {document_id}")
            return summary_id

        except Exception as e:
            logger.error(
                f"Error storing summary for document {document_id}: {e}", exc_info=True
            )
            return ""

    async def _store_recommendations(
        self,
        document_id: str,
        project_id: str,
        scenario_id: str,
        global_objective_type: str,
        global_objective_target: str,
        recommendations: List[Dict[str, Any]],
    ) -> str:
        """
        Store recommendations in MongoDB.
        
        Args:
            document_id: Document identifier
            project_id: Project identifier
            scenario_id: Scenario identifier
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            recommendations: List of recommendation dictionaries
            
        Returns:
            Recommendations document ID
        """
        try:
            recommendations_id = str(uuid.uuid4())
            recommendations_doc = {
                "_id": recommendations_id,
                "id": recommendations_id,
                "document_id": document_id,
                "project_id": project_id,
                "scenario_id": scenario_id,
                "global_objective_type": global_objective_type,
                "global_objective_target": global_objective_target,
                "recommendations": recommendations,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            db().base_case_recommendations.replace_one(
                {"_id": recommendations_id}, recommendations_doc, upsert=True
            )

            logger.info(
                f"Stored recommendations {recommendations_id} for document {document_id}"
            )
            return recommendations_id

        except Exception as e:
            logger.error(
                f"Error storing recommendations for document {document_id}: {e}",
                exc_info=True,
            )
            return ""

    async def validate_entities(
        self,
        project_id: str,
        entity_updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate and update entity attributes.

        This method processes user-provided entity updates, allowing
        users to mark entities as fixed/variable and set attribute ranges.

        Args:
            project_id: Project identifier
            entity_updates: List of entity updates with attributes

        Returns:
            Dictionary with validation results

        Note:
            This is a placeholder. Actual implementation will:
            1. Validate entity updates
            2. Update entity attributes in database
            3. Return validation results
        """
        logger.info(f"Validating entities for project {project_id}")

        # Placeholder implementation
        return {
            "project_id": project_id,
            "entities_updated": len(entity_updates),
            "message": "Entity validation (placeholder)",
        }

    async def generate_report(
        self,
        project_id: str,
    ) -> str:
        """
        Generate markdown report for a project.

        This method generates a comprehensive markdown report including
        project details, extracted entities, cost estimates, and system
        design recommendations.

        Args:
            project_id: Project identifier

        Returns:
            Markdown string with project report

        Note:
            This is a placeholder. Actual implementation will:
            1. Fetch project details
            2. Fetch extracted entities and relations
            3. Fetch cost estimates (if available)
            4. Generate markdown report
            5. Return markdown string
        """
        logger.info(f"Generating report for project {project_id}")

        # Placeholder implementation
        return f"""# Project Report

## Project: {project_id}

This is a placeholder report. Actual report generation will be implemented later.

### Project Details
- Status: Processing
- Report generated: Placeholder

### Entities
No entities extracted yet.

### Cost Estimates
No cost estimates available yet.

### Recommendations
Report generation is a placeholder.
"""

    async def process_tabular_data_file(
        self,
        file_bytes: bytes,
        filename: str,
        file_id: str,
        project_id: str,
        user_id: str,
        store_in_pinecone: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a tabular data file: extract tables, extract entities, and store in MongoDB.

        This method orchestrates the complete processing pipeline for a tabular data file:
        1. Extract tables from PDF using TableExtractor
        2. Extract entities using LLM via EntityExtractor with MSIO ontology
        3. Store tables and entities/edges in MongoDB
        4. Optionally store entities in Pinecone (disabled by default)

        Args:
            file_bytes: File content as bytes
            filename: Original filename
            file_id: GridFS file ID (used as doc_id)
            project_id: Project identifier
            user_id: User identifier
            store_in_pinecone: Whether to store entities in Pinecone (default: False)

        Returns:
            Dictionary with processing results including:
            - doc_id: Document identifier
            - tables_extracted: Number of tables extracted
            - entities_extracted: Number of entities extracted
            - entities_stored: Number of entities stored in MongoDB
            - entities_vectorized: Number of entities stored in Pinecone (if enabled)
            - edges_extracted: Number of edges/relations extracted
            - edges_stored: Number of edges stored in MongoDB
            - status: Processing status ("success" or "error")
            - error: Error message if processing failed

        Raises:
            RuntimeError: If DocumentProcessingService is not initialized
        """
        if not self._document_processing_service:
            raise RuntimeError("DocumentProcessingService not initialized")

        logger.info(
            f"Processing tabular data file: {filename} (file_id: {file_id}, "
            f"project_id: {project_id}, store_in_pinecone: {store_in_pinecone})"
        )

        try:
            # Process the tabular data document
            result = self._document_processing_service.process_tabular_data_document(
                pdf_bytes=file_bytes,
                filename=filename,
                doc_id=file_id,
                project_id=project_id,
                user_id=user_id,
                store_in_pinecone=store_in_pinecone,
            )

            logger.info(
                f"Successfully processed tabular data file {filename}: "
                f"{result.get('tables_extracted', 0)} tables, "
                f"{result.get('entities_extracted', 0)} entities, "
                f"{result.get('edges_extracted', 0)} edges"
            )

            return result

        except Exception as e:
            logger.error(
                f"Error processing tabular data file {filename}: {e}", exc_info=True
            )
            return {
                "doc_id": file_id,
                "filename": filename,
                "tables_extracted": 0,
                "entities_extracted": 0,
                "entities_stored": 0,
                "entities_vectorized": 0,
                "edges_extracted": 0,
                "edges_stored": 0,
                "status": "error",
                "error": str(e),
            }
