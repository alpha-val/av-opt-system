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
import asyncio

# Import LLM components
from app_v2.adapters.config import SETTINGS
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import MongoDB client
from ...adapters.mongo.client import db

# Import parsing utilities
from ..parsing.utils.llm_tools import (
    TOOLS,
    TOOLS_RECOMMENDATIONS,
    TOOLS_OBJECTIVE_DRIVEN,
    is_valid_json,
    sanitize_for_json,
)
from ..parsing.prompts.entity_extraction_prompt import (
    PROMPT_DISCIPLINE_STRUCTURED_SUMMARY,
    generate_prompt,
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
            model=SETTINGS.llm_model_name or "gpt-5.1",
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

        # Initialize LLM for objective-driven entity extraction
        self._llm_objective_driven = ChatOpenAI(
            model=SETTINGS.llm_model_name or "gpt-5-mini",
            api_key=SETTINGS.openai_api_key,
            timeout=300,
            max_retries=3,
            temperature=0,
            max_tokens=4096,
            model_kwargs={
                "tools": TOOLS_OBJECTIVE_DRIVEN,
                "tool_choice": "auto",
            },
        )

        # Initialize LLM for recommendations extraction
        self._llm_recommendations = ChatOpenAI(
            model=SETTINGS.llm_model_name or "gpt-5.1",
            api_key=SETTINGS.openai_api_key,
            timeout=300,
            max_retries=3,
            temperature=0,
            max_tokens=4096,
            model_kwargs={
                "tools": TOOLS_RECOMMENDATIONS,
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
                    document_id=document_id, scenario_id=scenario_id
                )
                relations_updated = document_store.update_relations_scenario_id(
                    document_id=document_id, scenario_id=scenario_id
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

    def _calculate_total_base_case_costs(
        self,
        entities: List[Dict[str, Any]],
        project_id: str,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate total base case costs by aggregating cost_value from entity properties (not attributes).

        Args:
            entities: List of entity dictionaries with attributes array
            project_id: Project identifier
            scenario_id: Optional scenario identifier

        Returns:
            Dictionary with total cost information:
            {
                "total_cost_value": number,
                "total_cost_currency": string,
                "entity_count": number,
                "costs_by_type": {"CAPEX": number, "OPEX": number, "Total": number, "Other": number},
                "costs_by_currency": {"USD": number, "EUR": number, ...},
                "entities_with_costs": number
            }
        """
        try:
            total_cost_by_currency = {}
            costs_by_type = {"CAPEX": 0.0, "OPEX": 0.0, "Total": 0.0, "Other": 0.0}
            entities_with_costs = 0
            entity_count = len(entities)

            for entity in entities:
                props = entity.get("properties", {})

                # Extract cost information from properties (not attributes array)
                # Cost is now stored as direct properties: cost_value, cost_currency, cost_type, etc.
                cost_value = props.get("cost_value")
                cost_currency = props.get("cost_currency")
                cost_type = props.get("cost_type")

                # Handle cost_value if it's a string (convert to float)
                if isinstance(cost_value, str):
                    try:
                        cost_value = float(
                            cost_value.replace(",", "").replace("$", "").strip()
                        )
                    except (ValueError, AttributeError):
                        cost_value = None
                elif cost_value is not None:
                    try:
                        cost_value = float(cost_value)
                    except (ValueError, TypeError):
                        cost_value = None

                # Default currency to USD if not specified
                if cost_currency is None:
                    cost_currency = "USD"

                # Default cost_type to "Other" if not specified
                if cost_type is None:
                    cost_type = "Other"

                if cost_value is not None and cost_value > 0:
                    entities_with_costs += 1
                    currency = cost_currency or "USD"

                    # Aggregate by currency
                    if currency not in total_cost_by_currency:
                        total_cost_by_currency[currency] = 0.0
                    total_cost_by_currency[currency] += cost_value

                    # Aggregate by type
                    cost_type_key = cost_type if cost_type in costs_by_type else "Other"
                    costs_by_type[cost_type_key] += cost_value

            # Determine primary currency (most common or largest amount)
            primary_currency = "USD"
            if total_cost_by_currency:
                primary_currency = max(
                    total_cost_by_currency.items(), key=lambda x: x[1]
                )[0]

            total_cost_value = total_cost_by_currency.get(primary_currency, 0.0)

            logger.info(
                f"Calculated total base case costs: {total_cost_value} {primary_currency} "
                f"from {entities_with_costs} entities with costs out of {entity_count} total entities"
            )

            return {
                "total_cost_value": total_cost_value,
                "total_cost_currency": primary_currency,
                "entity_count": entity_count,
                "costs_by_type": costs_by_type,
                "costs_by_currency": total_cost_by_currency,
                "entities_with_costs": entities_with_costs,
            }

        except Exception as e:
            logger.error(
                f"Error calculating total base case costs: {e}",
                exc_info=True,
            )
            return {
                "total_cost_value": 0.0,
                "total_cost_currency": "USD",
                "entity_count": len(entities),
                "costs_by_type": {
                    "CAPEX": 0.0,
                    "OPEX": 0.0,
                    "Total": 0.0,
                    "Other": 0.0,
                },
                "costs_by_currency": {},
                "entities_with_costs": 0,
            }

    def _extract_total_costs_from_entities(
        self,
        entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extract total costs from CostItem entities that have total_cost_value as properties.

        Args:
            entities: List of entity dictionaries

        Returns:
            List of extracted total cost entities with their values
        """
        try:
            extracted_totals = []

            for entity in entities:
                entity_type = entity.get("type", "")
                if entity_type != "CostItem":
                    continue

                props = entity.get("properties", {})

                # Extract cost information from properties (not attributes array)
                # For CostItem entities, we look for total_cost_value, total_cost_currency, etc. as direct properties
                total_cost_value = props.get("total_cost_value") or props.get(
                    "cost_value"
                )
                total_cost_currency = props.get("total_cost_currency") or props.get(
                    "cost_currency"
                )
                cost_type = props.get("cost_type")

                # Handle total_cost_value if it's a string (convert to float)
                if isinstance(total_cost_value, str):
                    try:
                        total_cost_value = float(
                            total_cost_value.replace(",", "").replace("$", "").strip()
                        )
                    except (ValueError, AttributeError):
                        total_cost_value = None
                elif total_cost_value is not None:
                    try:
                        total_cost_value = float(total_cost_value)
                    except (ValueError, TypeError):
                        total_cost_value = None

                # Default currency to USD if not specified
                if total_cost_currency is None:
                    total_cost_currency = "USD"

                if total_cost_value is not None and total_cost_value > 0:
                    extracted_totals.append(
                        {
                            "entity_id": entity.get("id", ""),
                            "entity_name": props.get("name", "Unknown"),
                            "total_cost_value": total_cost_value,
                            "total_cost_currency": total_cost_currency or "USD",
                            "cost_type": cost_type,
                        }
                    )

            logger.info(
                f"Extracted {len(extracted_totals)} total cost entities from {len(entities)} entities"
            )

            return extracted_totals

        except Exception as e:
            logger.error(
                f"Error extracting total costs from entities: {e}",
                exc_info=True,
            )
            return []

    def _validate_total_costs(
        self,
        calculated_totals: Dict[str, Any],
        extracted_totals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate extracted totals against calculated totals.

        Args:
            calculated_totals: Result from _calculate_total_base_case_costs
            extracted_totals: Result from _extract_total_costs_from_entities

        Returns:
            Validation report dictionary
        """
        try:
            calculated_value = calculated_totals.get("total_cost_value", 0.0)
            calculated_currency = calculated_totals.get("total_cost_currency", "USD")

            validation_results = {
                "calculated_total": {
                    "value": calculated_value,
                    "currency": calculated_currency,
                },
                "extracted_totals": extracted_totals,
                "validation_status": "unknown",
                "discrepancies": [],
                "warnings": [],
            }

            if not extracted_totals:
                validation_results["validation_status"] = "no_extracted_totals"
                validation_results["warnings"].append(
                    "No total cost entities (TIC, TCC) were extracted from the text. "
                    "Only calculated totals are available."
                )
                return validation_results

            # Find matching currency extracted total
            matching_extracted = None
            for extracted in extracted_totals:
                if extracted.get("total_cost_currency") == calculated_currency:
                    matching_extracted = extracted
                    break

            if not matching_extracted:
                # Use first extracted total if no currency match
                matching_extracted = extracted_totals[0] if extracted_totals else None
                validation_results["warnings"].append(
                    f"Currency mismatch: calculated in {calculated_currency}, "
                    f"extracted in {matching_extracted.get('total_cost_currency') if matching_extracted else 'unknown'}"
                )

            if matching_extracted:
                extracted_value = matching_extracted.get("total_cost_value", 0.0)
                difference = abs(calculated_value - extracted_value)
                percent_difference = (
                    (difference / extracted_value * 100) if extracted_value > 0 else 0.0
                )

                validation_results["extracted_total"] = {
                    "value": extracted_value,
                    "currency": matching_extracted.get("total_cost_currency"),
                }
                validation_results["difference"] = {
                    "absolute": difference,
                    "percent": percent_difference,
                }

                # Determine validation status
                if percent_difference < 1.0:
                    validation_results["validation_status"] = "excellent_match"
                elif percent_difference < 5.0:
                    validation_results["validation_status"] = "good_match"
                elif percent_difference < 10.0:
                    validation_results["validation_status"] = "acceptable_match"
                    validation_results["warnings"].append(
                        f"Cost difference of {percent_difference:.2f}% between calculated and extracted totals"
                    )
                else:
                    validation_results["validation_status"] = "significant_discrepancy"
                    validation_results["discrepancies"].append(
                        {
                            "type": "cost_mismatch",
                            "message": (
                                f"Significant difference between calculated ({calculated_value} {calculated_currency}) "
                                f"and extracted ({extracted_value} {matching_extracted.get('total_cost_currency')}) totals: "
                                f"{percent_difference:.2f}%"
                            ),
                            "calculated": calculated_value,
                            "extracted": extracted_value,
                            "difference_percent": percent_difference,
                        }
                    )

            logger.info(
                f"Cost validation status: {validation_results['validation_status']}, "
                f"calculated: {calculated_value} {calculated_currency}, "
                f"extracted: {len(extracted_totals)} total(s)"
            )

            return validation_results

        except Exception as e:
            logger.error(
                f"Error validating total costs: {e}",
                exc_info=True,
            )
            return {
                "validation_status": "error",
                "error": str(e),
                "calculated_total": calculated_totals,
                "extracted_totals": extracted_totals,
            }

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

    # Process a tabular data file
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

    # Process a tabular data file
    async def process_base_case_file(
        self,
        file_bytes: bytes,
        filename: str,
        file_id: str,
        project_id: str,
        user_id: str,
        store_in_pinecone: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a base case file: extract text, extract entities, and store in MongoDB.

        This method orchestrates the complete processing pipeline for a base case file:
        1. Extract text from PDF using TextExtractor
        2. Chunk text using specified chunking strategy
        3. Extract entities using LLM via EntityExtractor with MSIO ontology
        4. Validate and normalize entities
        5. Store chunks, entities, and edges in MongoDB
        6. Optionally store chunks and entities in Pinecone (disabled by default)

        Args:
            file_bytes: File content as bytes
            filename: Original filename
            file_id: GridFS file ID (used as doc_id)
            project_id: Project identifier
            user_id: User identifier
            store_in_pinecone: Whether to store chunks and entities in Pinecone (default: False)

        Returns:
            Dictionary with processing results including:
            - doc_id: Document identifier
            - filename: Original filename
            - file_sha256: SHA256 hash of the file
            - pages: Number of pages extracted
            - chunks_created: Number of chunks created
            - chunks_stored: Number of chunks stored in MongoDB
            - chunks_vectorized: Number of chunks stored in Pinecone (if enabled)
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
            f"Processing base case file: {filename} (file_id: {file_id}, "
            f"project_id: {project_id}, store_in_pinecone: {store_in_pinecone})"
        )

        try:
            # Process the base case document
            result = self._document_processing_service.process_base_case_document(
                pdf_bytes=file_bytes,
                filename=filename,
                doc_id=file_id,
                project_id=project_id,
                user_id=user_id,
                store_in_pinecone=store_in_pinecone,
                chunking_strategy="character",
                char_limit=15000,
            )

            logger.info(
                f"Successfully processed base case file {filename}: "
                f"{result.get('pages', 0)} pages, "
                f"{result.get('chunks_created', 0)} chunks, "
                f"{result.get('entities_extracted', 0)} entities, "
                f"{result.get('edges_extracted', 0)} edges"
            )

            return result

        except Exception as e:
            logger.error(
                f"Error processing base case file {filename}: {e}", exc_info=True
            )
            return {
                "doc_id": file_id,
                "filename": filename,
                "file_sha256": None,
                "pages": 0,
                "chunks_created": 0,
                "chunks_stored": 0,
                "chunks_vectorized": 0,
                "entities_extracted": 0,
                "entities_stored": 0,
                "entities_vectorized": 0,
                "edges_extracted": 0,
                "edges_stored": 0,
                "validation_warnings": [],
                "status": "error",
                "error": str(e),
            }

    # Extract entities from a base case document using V2 workflow (recommendations-first approach)
    async def extract_base_case_entities_v2(
        self,
        project_id: str,
        document_id: str,
        global_objective_type: str,
        global_objective_target: str,
        user_id: str,
        scenario_id: str,
        objective_description: Optional[str] = None,
        extract_summary: bool = False,
        extraction_scope: str = "exact",
    ) -> Dict[str, Any]:
        """
        Extract entities from a base case document using V2 workflow (recommendations-first approach).

        This method first analyzes the document to generate recommendations and identify
        relevant entities, then extracts only those entities. This is more targeted and
        efficient than extracting all entities first.

        Args:
            project_id: Project identifier
            document_id: Document identifier (GridFS file ID)
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            user_id: User identifier
            scenario_id: Scenario identifier
            objective_description: Optional description of the global objective
            extract_summary: Whether to extract document summary (default: False)
            extraction_scope: "exact" (only specified entities), "with_relationships"
            (entities + direct relationships), or "with_context"
            (entities + related entities in same context)

        Returns:
            Dictionary with extracted entities, recommendations, and metadata

        Raises:
            RuntimeError: If required services are not initialized
        """
        logger.info(
            f"Extracting entities (V2) from document {document_id} "
            f"for project {project_id}, scenario {scenario_id} "
            f"(objective: {global_objective_type}, target: {global_objective_target})"
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

            # Step 2: Extract full text for analysis
            from ..parsing.extractors.text_extractor import TextExtractor

            text_extractor = TextExtractor()
            _, _, _, pages_clean = text_extractor.extract(file_bytes, filename, None)
            full_text = text_extractor.extract_full_text(pages_clean)

            # Step 3: Extract recommendations and identify relevant entities (Step 1 of V2 workflow)
            recommendations_result = (
                await self._extract_recommendations_with_entities_v2(
                    full_text=full_text,
                    global_objective_type=global_objective_type,
                    global_objective_target=global_objective_target,
                    objective_description=objective_description,
                    document_id=document_id,
                    project_id=project_id,
                    scenario_id=scenario_id,
                    user_id=user_id,
                )
            )

            recommendations = recommendations_result.get("recommendations", [])
            relevant_entities = recommendations_result.get("relevant_entities", [])
            recommendations_id = recommendations_result.get("recommendations_id", "")

            logger.info(
                f"Step 1 complete: {len(recommendations)} recommendations, "
                f"{len(relevant_entities)} relevant entities identified"
            )

            if not relevant_entities:
                logger.warning(
                    f"No relevant entities identified for document {document_id}. "
                    f"Cannot proceed with entity extraction."
                )
                return {
                    "document_id": document_id,
                    "project_id": project_id,
                    "scenario_id": scenario_id,
                    "processing_status": "warning",
                    "message": "No relevant entities identified",
                    "recommendations": recommendations,
                    "recommendations_id": recommendations_id,
                    "entities_extracted": 0,
                    "relations_extracted": 0,
                }

            # Step 4: Extract targeted entities (Step 2 of V2 workflow)
            entities_result = await self._extract_targeted_entities_v2(
                file_bytes=file_bytes,
                filename=filename,
                document_id=document_id,
                project_id=project_id,
                user_id=user_id,
                scenario_id=scenario_id,
                relevant_entities=relevant_entities,
                extraction_scope=extraction_scope,
            )

            entities_extracted = len(entities_result.get("nodes", []))
            edges_extracted = len(entities_result.get("edges", []))

            logger.info(
                f"Step 2 complete: {entities_extracted} entities, {edges_extracted} edges extracted"
            )

            # Step 5: Optionally extract document summary
            summary = None
            summary_id = None
            if extract_summary:
                summary = await self._extract_document_summary(
                    full_text=full_text,
                    filename=filename,
                    document_id=document_id,
                )
                summary_id = await self._store_summary(
                    document_id=document_id,
                    project_id=project_id,
                    scenario_id=scenario_id,
                    summary=summary,
                )
                logger.info(f"Extracted and stored summary (id: {summary_id})")

            # Step 6: Return structured response
            return {
                "document_id": document_id,
                "project_id": project_id,
                "scenario_id": scenario_id,
                "processing_status": "success",
                "summary": summary,
                "summary_id": summary_id,
                "entities_extracted": entities_extracted,
                "relations_extracted": edges_extracted,
                "recommendations": recommendations,
                "recommendations_id": recommendations_id,
                "relevant_entities_count": len(relevant_entities),
                "extraction_scope": extraction_scope,
                "statistics": {
                    "chunks_processed": entities_result.get("chunks_processed", 0),
                    "entities_stored": entities_result.get("entities_stored", 0),
                    "edges_stored": entities_result.get("edges_stored", 0),
                },
            }

        except Exception as e:
            logger.error(
                f"Error extracting entities (V2) from document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "document_id": document_id,
                "project_id": project_id,
                "scenario_id": scenario_id,
                "processing_status": "error",
                "error": str(e),
                "entities_extracted": 0,
                "relations_extracted": 0,
                "recommendations": [],
                "relevant_entities": [],
            }

    # Extract recommendations and identify relevant entities for extraction (Step 1 of V2 workflow)
    async def _extract_recommendations_with_entities_v2(
        self,
        full_text: str,
        global_objective_type: str,
        global_objective_target: str,
        objective_description: Optional[str],
        document_id: str,
        project_id: str,
        scenario_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Extract recommendations and identify relevant entities for extraction (Step 1 of V2 workflow).

        Args:
            full_text: Full text content of the document
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            objective_description: Optional description of the global objective
            document_id: Document identifier
            project_id: Project identifier
            scenario_id: Scenario identifier
            user_id: User identifier

        Returns:
            Dictionary with recommendations, relevant_entities, and recommendations_id
        """
        logger.info(
            f"Extracting recommendations and identifying relevant entities "
            f"for objective: {global_objective_type} ({global_objective_target})"
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

            # Limit text to avoid token limits (keep first 50000 chars)
            text_for_analysis = (
                full_text[:50000] if len(full_text) > 50000 else full_text
            )

            recommendations_prompt = f"""
            You are an expert process engineer and cost estimator analyzing a base case engineering report.

            {objective_context}

            TASK:
            1. Analyze the base case document in the context of the global objective.
            2. Generate specific recommendations for system redesign to meet the objective.
            3. Identify which entities are most relevant for achieving the recommendations.
            4. For each relevant entity, provide a COMPLETE NODE STRUCTURE with:
            - id: unique identifier for the entity
            - type: entity type from NODE_TYPES
            - properties: complete properties object including:
                * name: entity name
                * discipline, category, subcategory, entity: MSIO classification (REQUIRED)
                * All applicable properties from NODE_PROPERTIES as found in the text
                * expected_attributes: list of attribute names to extract
                * evidence_locations: text snippets, page references, section anchors
                * extraction_rationale: why this entity is relevant
                * extraction_priority: priority level (high/medium/low)

            BASE CASE TEXT:
            {text_for_analysis}

            INSTRUCTIONS:
            - Generate recommendations that address what needs to change to meet the objective.
            - For each recommendation, identify ALL entities that should be modified/replaced.
            - Prioritize recommendations based on impact and feasibility.
            - For each relevant entity, provide a COMPLETE NODE STRUCTURE following the extract_nodes format:
            * Include id, type, and properties fields
            * Include all applicable properties from NODE_PROPERTIES
            * Include complete MSIO classification (discipline, category, subcategory, entity)
            * Include expected_attributes, evidence_locations, extraction_rationale, extraction_priority in properties
            - Include evidence locations (text snippets, page numbers, section references) to guide entity extraction.
            - List expected attributes that should be extracted for each entity.
            - Be comprehensive: identify all entities relevant to the recommendations.
            - ALL relevant_entities must follow the exact structure: id, type, properties (with all NODE_PROPERTIES)

            Use the extract_recommendations tool to provide your analysis.
            """

            system_prompt = SystemMessage(
                content="You are an expert process engineer and cost estimator. Analyze base case documents and provide recommendations for system redesign based on global objectives, including detailed specifications of relevant entities to extract."
            )
            human_message = HumanMessage(content=recommendations_prompt)

            messages = [system_prompt, human_message]
            resp = self._llm.invoke(messages)

            # Process tool calls
            recommendations = []
            relevant_entities = []

            for call in resp.additional_kwargs.get("tool_calls", []):
                fn = call.get("function", {})
                name = fn.get("name")

                if name == "extract_recommendations":
                    arguments = fn.get("arguments", "{}")
                    if is_valid_json(arguments):
                        payload = json.loads(arguments)
                        payload = sanitize_for_json(payload)
                        recommendations = payload.get("recommendations", [])
                        relevant_entities = payload.get("relevant_entities", [])
                        break

            # If no recommendations extracted, log warning
            if not recommendations:
                logger.warning(
                    f"No recommendations extracted for document {document_id}"
                )

            if not relevant_entities:
                logger.warning(
                    f"No relevant entities identified for document {document_id}"
                )

            # Store recommendations in MongoDB
            recommendations_id = await self._store_recommendations_v2(
                document_id=document_id,
                project_id=project_id,
                scenario_id=scenario_id,
                user_id=user_id,
                global_objective_type=global_objective_type,
                global_objective_target=global_objective_target,
                recommendations=recommendations,
                relevant_entities=relevant_entities,
            )

            logger.info(
                f"Extracted {len(recommendations)} recommendations and "
                f"{len(relevant_entities)} relevant entities"
            )

            return {
                "recommendations": recommendations,
                "relevant_entities": relevant_entities,
                "recommendations_id": recommendations_id,
            }

        except Exception as e:
            logger.error(
                f"Error extracting recommendations (V2) for document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "recommendations": [],
                "relevant_entities": [],
                "recommendations_id": "",
            }

    def dedupe_nodes_by_attributes_and_msio(
        self,
        nodes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        De-duplicate nodes based on attributes and MSIO categorization.
        """
        deduped_nodes = []
        seen_nodes = set()
        try:
            for node in nodes:
                node_key = (
                    node.get("properties", {}).get("name"),
                    node.get("properties", {}).get("discipline"),
                    node.get("properties", {}).get("category"),
                    node.get("properties", {}).get("subcategory"),
                    node.get("properties", {}).get("entity"),
                )
                if node_key not in seen_nodes:
                    seen_nodes.add(node_key)
                    deduped_nodes.append(node)
                else:
                    logger.debug(f"Skipping duplicate node: {node_key}")
            return deduped_nodes
        except Exception as e:
            logger.error(f"Error deduplicating nodes: {e}")
            return nodes

    async def _extract_targeted_entities_v2(
        self,
        file_bytes: bytes,
        filename: str,
        document_id: str,
        project_id: str,
        user_id: str,
        scenario_id: str,
        relevant_entities: List[Dict[str, Any]],
        extraction_scope: str = "exact",
    ) -> Dict[str, Any]:
        """
        Extract targeted entities based on relevant_entities specifications (Step 2 of V2 workflow).

        Args:
            file_bytes: PDF file content
            filename: Original filename
            document_id: Document identifier
            project_id: Project identifier
            user_id: User identifier
            scenario_id: Scenario identifier
            relevant_entities: List of entity specifications from Step 1
            extraction_scope: "exact", "with_relationships", or "with_context"

        Returns:
            Dictionary with extracted nodes, edges, and statistics
        """
        logger.info(
            f"Extracting targeted entities for document {document_id}, "
            f"scope: {extraction_scope}, {len(relevant_entities)} entities to extract"
        )

        try:
            # Extract text and create chunks
            from ..parsing.extractors.text_extractor import TextExtractor
            from ..parsing.chunkers import CharacterChunker
            from ..parsing.storage.document_store import DocumentStore
            import uuid

            # Use same namespace as DocumentProcessingService
            CHUNK_NAMESPACE = uuid.UUID("11111111-2222-3333-4444-555555555555")

            text_extractor = TextExtractor()
            _, _, _, pages_clean = text_extractor.extract(file_bytes, filename, None)
            full_text = text_extractor.extract_full_text(pages_clean)

            # Create chunks
            chunk_metadata = {
                "artifact_type": "base_case",
                "project_id": project_id,
                "user_id": user_id,
                "doc_id": document_id,
                "scenario_id": scenario_id,
            }

            chunker = CharacterChunker(document_id, CHUNK_NAMESPACE, char_limit=5000)
            chunks = chunker.chunk(full_text, chunk_metadata)

            logger.info(f"Created {len(chunks)} chunks for targeted extraction")

            # Extract entities using targeted extraction
            from ..parsing.extractors.entity_extractor import EntityExtractor

            entity_extractor = EntityExtractor()
            extraction_result = entity_extractor.extract_targeted(
                chunks=chunks,
                relevant_entities=relevant_entities,
                extraction_scope=extraction_scope,
            )

            nodes = extraction_result.get("nodes", [])
            edges = extraction_result.get("edges", [])

            # De-dupe nodes based on attributes and MSIO categorization
            nodes = self.dedupe_nodes_by_attributes_and_msio(nodes)

            # Generate UUID IDs for nodes that have non-UUID IDs (e.g., "E1", "E2", etc.)
            id_mapping = {}  # Map old IDs to new UUID IDs
            for node in nodes:
                old_id = node.get("id", "")
                if not old_id:
                    # Generate UUID if no ID present
                    new_id = str(uuid.uuid4())
                    node["id"] = new_id
                    logger.debug(f"Generated UUID for node without ID: {new_id}")
                else:
                    # Check if ID is a simple string like "E1", "E2", etc. (not a valid UUID)
                    try:
                        # Try to parse as UUID to validate
                        uuid.UUID(old_id)
                        # If successful, it's already a valid UUID, keep it
                        new_id = old_id
                    except (ValueError, AttributeError):
                        # Not a valid UUID, generate a new one
                        new_id = str(uuid.uuid4())
                        id_mapping[old_id] = new_id
                        node["id"] = new_id
                        logger.debug(
                            f"Replaced non-UUID ID '{old_id}' with UUID '{new_id}' "
                            f"for node type '{node.get('type', 'Unknown')}'"
                        )

            # Update edge source/target references to use new UUID IDs
            for edge in edges:
                source = edge.get("source", "")
                target = edge.get("target", "")
                if source in id_mapping:
                    edge["source"] = id_mapping[source]
                    logger.debug(
                        f"Updated edge source from '{source}' to '{id_mapping[source]}'"
                    )
                if target in id_mapping:
                    edge["target"] = id_mapping[target]
                    logger.debug(
                        f"Updated edge target from '{target}' to '{id_mapping[target]}'"
                    )

            # Validate and add metadata to entities and edges
            validated_nodes = []
            for node in nodes:
                # Ensure node has complete structure (id, type, properties)
                if not node.get("id"):
                    logger.warning(
                        f"Node missing id, skipping: {node.get('type', 'Unknown')}"
                    )
                    continue
                if not node.get("type"):
                    logger.warning(
                        f"Node missing type, skipping: {node.get('id', 'Unknown')}"
                    )
                    continue
                if not node.get("properties"):
                    node["properties"] = {}

                # Ensure MSIO classification is present
                props = node["properties"]
                if not all(
                    key in props
                    for key in ["discipline", "category", "subcategory", "entity"]
                ):
                    logger.warning(
                        f"Node {node.get('id')} missing MSIO classification, "
                        f"attempting to infer from relevant_entities"
                    )
                    # Try to match with relevant_entities to get MSIO classification
                    for rel_entity in relevant_entities:
                        rel_props = rel_entity.get("properties", {})
                        if rel_props.get("name") == props.get("name") or rel_entity.get(
                            "id"
                        ) == node.get("id"):
                            props.setdefault(
                                "discipline", rel_props.get("discipline", "")
                            )
                            props.setdefault("category", rel_props.get("category", ""))
                            props.setdefault(
                                "subcategory", rel_props.get("subcategory", "")
                            )
                            props.setdefault("entity", rel_props.get("entity", ""))
                            break

                # Add chunk metadata
                props.update(chunk_metadata)
                validated_nodes.append(node)

            nodes = validated_nodes

            for edge in edges:
                edge.setdefault("properties", {})
                edge["properties"].update(chunk_metadata)

            # Store entities and edges in MongoDB
            document_store = DocumentStore()
            entities_stored = document_store.bulk_upsert_entities(nodes)
            edges_stored = document_store.bulk_upsert_relations(edges)

            # Store chunks
            chunks_stored = document_store.bulk_upsert_chunks(chunks)

            logger.info(
                f"Stored {entities_stored} entities, {edges_stored} edges, "
                f"{chunks_stored} chunks"
            )

            return {
                "nodes": nodes,
                "edges": edges,
                "chunks_processed": len(chunks),
                "entities_stored": entities_stored,
                "edges_stored": edges_stored,
            }

        except Exception as e:
            logger.error(
                f"Error extracting targeted entities for document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "nodes": [],
                "edges": [],
                "chunks_processed": 0,
                "entities_stored": 0,
                "edges_stored": 0,
            }

    async def _store_recommendations_v2(
        self,
        document_id: str,
        project_id: str,
        scenario_id: str,
        user_id: str,
        global_objective_type: str,
        global_objective_target: str,
        recommendations: List[Dict[str, Any]],
        relevant_entities: List[Dict[str, Any]],
    ) -> str:
        """
        Store recommendations with relevant entities in MongoDB (V2 format).

        Args:
            document_id: Document identifier
            project_id: Project identifier
            scenario_id: Scenario identifier
            user_id: User identifier
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            recommendations: List of recommendation dictionaries
            relevant_entities: List of relevant entity specifications

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
                "user_id": user_id,
                "global_objective_type": global_objective_type,
                "global_objective_target": global_objective_target,
                "recommendations": recommendations,
                "relevant_entities": relevant_entities,
                "workflow_version": "v2",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            db().base_case_recommendations.replace_one(
                {"_id": recommendations_id}, recommendations_doc, upsert=True
            )

            logger.info(
                f"Stored recommendations (V2) {recommendations_id} for document {document_id}"
            )
            return recommendations_id

        except Exception as e:
            logger.error(
                f"Error storing recommendations (V2) for document {document_id}: {e}",
                exc_info=True,
            )
            return ""

        # ============================================================================
        # V3 Analysis Workflow Functions
        # ============================================================================

    async def _read_base_case_documents_v3(
        self,
        document_ids: List[str],
        file_storage_service,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve base case documents from GridFS.

        Args:
            document_ids: List of document IDs (GridFS file IDs)
            file_storage_service: FileStorageService instance

        Returns:
            List of dictionaries with file_bytes, filename, document_id
        """
        documents = []
        for doc_id in document_ids:
            try:
                file_bytes = file_storage_service.get_file(doc_id)
                if file_bytes:
                    metadata = file_storage_service.get_file_metadata(doc_id)
                    filename = (
                        metadata.get("filename", "unknown.pdf")
                        if metadata
                        else "unknown.pdf"
                    )
                    documents.append(
                        {
                            "file_bytes": file_bytes,
                            "filename": filename,
                            "document_id": doc_id,
                        }
                    )
                    logger.info(
                        f"Retrieved base case document: {filename} ({doc_id}, {len(file_bytes)} bytes)"
                    )
                else:
                    logger.warning(f"Failed to retrieve base case document: {doc_id}")
            except Exception as e:
                logger.error(
                    f"Error retrieving document {doc_id}: {e}",
                    exc_info=True,
                )
        return documents

    async def _extract_recommendations_v3(
        self,
        full_text: str,
        global_objective_type: str,
        global_objective_target: str,
        objective_description: Optional[str],
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Extract recommendations using LLM (simplified version, no entity extraction).

        Args:
            full_text: Full text content of the document
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            objective_description: Optional description of the global objective
            document_id: Document identifier

        Returns:
            Dictionary with recommendations and recommendations_id
        """
        logger.info(
            f"Extracting recommendations (V3) for objective: {global_objective_type} ({global_objective_target})"
        )

        try:
            # Build prompt for recommendations extraction
            objective_context = f"""
                GLOBAL OBJECTIVE:
                - Analyze the text to achieve the following objective: {global_objective_type}
                - Target magnitude of change by: {global_objective_target}
                """
            if objective_description:
                objective_context += f"- Description: {objective_description}\n"

            # Limit text to avoid token limits (keep first 15000 chars)
            # text_for_analysis = (
            #     full_text[:15000] if len(full_text) > 15000 else full_text
            # )
            text_for_analysis = full_text

            recommendations_prompt = f"""
            You are an expert process engineer and cost estimator analyzing a base case engineering report. You are tasked with analyzing the text to achieve the following objective: 
            {objective_context}

            TASK:
            1. Comprehensively analyze the base case document in the context of the objective: {global_objective_type} and target magnitude of change by: {global_objective_target}.
            2. Generate a COMPREHENSIVE set of recommendations (aim for 15-30+ recommendations) categorized as:
               - PRIMARY recommendations (5-10): High-impact, direct solutions that directly address the objective
               - SECONDARY recommendations (5-10): Supporting changes that enhance or enable primary recommendations
               - OTHER recommendations (5-10): Alternative approaches, lower-priority options, or innovative solutions
            3. Explore ALL aspects of the system across multiple categories:
               - Equipment Upgrades: Capacity increases, replacements, additions, technology upgrades
               - Process Optimization: Flow improvements, efficiency gains, throughput enhancements
               - Operational Changes: Shift patterns, staffing, procedures, scheduling
               - Infrastructure: Utilities, buildings, site work, foundations, structures
               - Material Changes: Raw materials, consumables, feedstocks, product specifications
               - Control Systems: Automation, instrumentation, SCADA, control logic
               - Energy Efficiency: Power consumption, heat recovery, waste minimization
               - Maintenance Strategy: Reliability improvements, preventive maintenance, spare parts
               - Safety Enhancements: Safety systems, procedures, equipment, training
               - Environmental Improvements: Emissions reduction, waste treatment, compliance
            4. For each recommendation, classify it with:
               - recommendation_category: "primary", "secondary", or "other"
               - type: Specific category (e.g., "Equipment Upgrade", "Process Optimization", etc.)
               - estimated_cost_range: Rough cost estimate
               - time_to_implement: Implementation timeline
               - dependencies: Other recommendations this depends on (if any)
               - alternative_to: Alternative approaches to other recommendations (if any)
            5. Identify ALL entities relevant for achieving each recommendation.
            6. For each relevant entity, provide a COMPLETE NODE STRUCTURE with:
            - id: unique identifier for the entity
            - type: entity type from NODE_TYPES
            - properties: complete properties object including:
                * name: entity name
                * discipline, category, subcategory, entity: MSIO classification (REQUIRED)
                * All applicable properties from NODE_PROPERTIES as found in the text
                * expected_attributes: list of attribute names to extract
                * evidence_locations: text snippets, page references, section anchors
                * extraction_rationale: why this entity is relevant
                * extraction_priority: priority level (high/medium/low)

            BASE CASE TEXT:
            {text_for_analysis}

            INSTRUCTIONS:
            - THINK BROADLY: Don't just focus on obvious equipment upgrades. Explore all aspects:
              * Equipment: pumps, tanks, vessels, reactors, heat exchangers, compressors, filters, separators
              * Processes: reaction conditions, separation methods, purification steps, material handling
              * Operations: work schedules, batch vs continuous, staffing levels, training
              * Infrastructure: utilities (steam, cooling water, electricity), buildings, site improvements
              * Materials: feed quality, product specifications, consumables, catalysts
              * Controls: automation level, instrumentation, data collection, process control
              * Energy: power consumption, heat integration, waste heat recovery, efficiency
              * Maintenance: reliability, spare parts, preventive maintenance, condition monitoring
              * Safety: safety systems, emergency response, hazard mitigation, personal protective equipment
              * Environment: emissions, waste streams, treatment systems, compliance
            - Generate MINIMUM 15 recommendations (ideally 20-30+), distributed across categories:
              * 5-10 primary recommendations (direct, high-impact solutions)
              * 5-10 secondary recommendations (supporting/enabling changes)
              * 5-10 other recommendations (alternatives, innovations, lower priority)
            - For each recommendation, identify ALL entities that should be modified/replaced/added.
            - Prioritize recommendations based on impact, feasibility, and cost-effectiveness.
            - For each relevant entity, exhaustively combine all possible information from the base case reports and provide a COMPLETE NODE STRUCTURE:
                * Include id, type, and properties fields
                * Include all applicable properties from NODE_PROPERTIES
                * Include complete MSIO classification (discipline, category, subcategory, entity)
                * Include expected_attributes, evidence_locations, extraction_rationale, extraction_priority in properties
                * Explicitly encode based on the objective: {global_objective_type} and target magnitude of change by: {global_objective_target} whether the entity is a fixed or floating entity.
                * Explicitly encode in the attributes the direction of the change: encode the direction of the change in the attributes. 
                * Explicitly encode in the attributes the unit of the change: encode the unit of the change in the attributes.
                * Explicitly encode in the attributes the basis year of the change: encode the basis year of the change in the attributes.
                * Explicitly encode in the attributes the currency of the change: encode the currency of the change in the attributes.
                * Explicitly encode in the attributes the source of the change: encode the source of the change in the attributes.
                * Explicitly encode in the attributes the update frequency of the change: encode the update frequency of the change in the attributes.
                * Explicitly encode in the attributes the effective life of the change: encode the effective life of the change in the attributes.
                * Explicitly encode in the attributes the reclamation cost of the change: encode the reclamation cost of the change in the attributes.
            - Include evidence locations (text snippets, page numbers, section references) to guide entity extraction.
            - List expected attributes that should be extracted for each entity.
            - Be COMPREHENSIVE: identify all entities relevant to ALL recommendations across ALL categories.
            - ALL relevant_entities must follow the exact structure: id, type, properties (with all NODE_PROPERTIES)

            EXAMPLES OF RECOMMENDATION TYPES TO EXPLORE:
            - Equipment Upgrade: "Upgrade pump from 100 gpm to 125 gpm capacity"
            - Process Optimization: "Optimize reaction temperature to increase yield by 10%"
            - Operational Change: "Implement 24/7 operation with 3-shift schedule"
            - Infrastructure: "Install additional cooling water system capacity"
            - Material Change: "Switch to higher-grade feedstock for improved efficiency"
            - Control System: "Implement advanced process control (APC) system"
            - Energy Efficiency: "Install heat exchanger to recover waste heat"
            - Maintenance Strategy: "Implement predictive maintenance program"
            - Safety Enhancement: "Install automated emergency shutdown system"
            - Environmental Improvement: "Add scrubber system to reduce emissions"

            IMPORTANT:
            - EXPLORE EXHAUSTIVELY: Think beyond the obvious. Consider all system components, processes, and operations.
            - Generate a COMPREHENSIVE set: Aim for 15-30+ recommendations across all categories.
            - Categorize properly: Primary = direct high-impact solutions, Secondary = supporting changes, Other = alternatives/innovations.
            - Be thorough: Every significant system component, process step, and operational aspect should be considered.
            
            Return recommendations with extract_recommendations(recommendations=[...]) as per the output contract.
            """

            system_prompt = SystemMessage(
                content="You are an expert process engineer and cost estimator. Analyze base case documents and provide recommendations for system redesign based on global objectives, including queryable entity information for MongoDB lookup."
            )
            human_message = HumanMessage(content=recommendations_prompt)

            messages = [system_prompt, human_message]
            resp = self._llm_recommendations.invoke(messages)

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
                        entities_for_costing = payload.get("relevant_entities", [])
                        break

            # If no recommendations extracted, log warning
            if not recommendations:
                logger.warning(
                    f"No recommendations extracted for document {document_id}"
                )

            # Sort recommendations by category (primary first, then secondary, then other)
            category_order = {"primary": 0, "secondary": 1, "other": 2}
            recommendations.sort(
                key=lambda r: (
                    category_order.get(r.get("recommendation_category", "other"), 2),
                    r.get("recommendation_id", ""),
                )
            )

            # Log recommendation counts by category
            primary_count = sum(
                1
                for r in recommendations
                if r.get("recommendation_category") == "primary"
            )
            secondary_count = sum(
                1
                for r in recommendations
                if r.get("recommendation_category") == "secondary"
            )
            other_count = sum(
                1
                for r in recommendations
                if r.get("recommendation_category") == "other"
            )

            logger.info(
                f"Extracted {len(recommendations)} total recommendations "
                f"(Primary: {primary_count}, Secondary: {secondary_count}, Other: {other_count}) "
                f"and {len(entities_for_costing)} entities for costing"
            )

            return {
                "recommendations": recommendations,
                "entities_for_costing": entities_for_costing,
            }

        except Exception as e:
            logger.error(
                f"Error extracting recommendations (V3) for document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "recommendations": [],
                "entities_for_costing": [],
            }

    async def _extract_recommendations_v3_chunked(
        self,
        full_text: str,
        global_objective_type: str,
        global_objective_target: str,
        objective_description: Optional[str],
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Extract recommendations using LLM with chunking approach.

        This version chunks the base case text into 15000-character chunks with overlap,
        processes each chunk separately, and merges the results.

        Args:
            full_text: Full text content of the document
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            objective_description: Optional description of the global objective
            document_id: Document identifier

        Returns:
            Dictionary with recommendations and entities_for_costing (merged from all chunks)
        """
        logger.info(
            f"Extracting recommendations (V3 chunked) for objective: {global_objective_type} ({global_objective_target})"
        )

        try:
            # Import chunking utilities
            import uuid

            # Use same namespace as DocumentProcessingService
            CHUNK_NAMESPACE = uuid.UUID("11111111-2222-3333-4444-555555555555")

            # Chunk the text with 15000 character limit and 20% overlap (3000 chars)
            char_limit = 15000
            overlap = 3000  # 20% overlap

            # Create chunks with overlap manually (CharacterChunker doesn't support overlap)
            chunks = []
            current_pos = 0
            seq = 1

            while current_pos < len(full_text):
                chunk_text = full_text[current_pos : current_pos + char_limit]
                chunk_id = str(uuid.uuid5(CHUNK_NAMESPACE, f"{document_id}|{seq}"))

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "doc_id": document_id,
                        "seq": seq,
                        "text": chunk_text,
                        "start_pos": current_pos,
                        "end_pos": current_pos + len(chunk_text),
                    }
                )

                # Move forward by char_limit - overlap to create overlap
                current_pos += char_limit - overlap
                seq += 1

                # Break if we've reached the end
                if current_pos >= len(full_text):
                    break

            logger.info(
                f"Created {len(chunks)} chunks for recommendations extraction "
                f"(char_limit: {char_limit}, overlap: {overlap})"
            )

            # Build objective context (same for all chunks)
            objective_context = f"""
                GLOBAL OBJECTIVE:
                - Analyze the text to achieve the following objective: {global_objective_type}
                - Target magnitude of change by: {global_objective_target}
                """
            if objective_description:
                objective_context += f"- Description: {objective_description}\n"

            # Process each chunk
            all_recommendations = []
            all_entities_for_costing = []
            recommendation_ids_seen = set()
            entity_ids_seen = set()

            for chunk_idx, chunk in enumerate(chunks):
                chunk_text = chunk["text"]
                chunk_seq = chunk["seq"]

                logger.info(
                    f"Processing chunk {chunk_seq}/{len(chunks)} "
                    f"(positions {chunk['start_pos']}-{chunk['end_pos']}, "
                    f"{len(chunk_text)} chars)"
                )

                recommendations_prompt = f"""
            You are an expert process engineer and cost estimator analyzing a base case engineering report. You are tasked with analyzing the text to achieve the following objective: 
            {objective_context}

            TASK:
            1. Comprehensively analyze this section of the base case document in the context of the objective: {global_objective_type} and target magnitude of change by: {global_objective_target}.
            2. Generate a COMPREHENSIVE set of recommendations (aim for 15-30+ recommendations) categorized as:
               - PRIMARY recommendations (5-10): High-impact, direct solutions that directly address the objective
               - SECONDARY recommendations (5-10): Supporting changes that enhance or enable primary recommendations
               - OTHER recommendations (5-10): Alternative approaches, lower-priority options, or innovative solutions
            3. Explore ALL aspects of the system across multiple categories:
               - Equipment Upgrades: Capacity increases, replacements, additions, technology upgrades
               - Process Optimization: Flow improvements, efficiency gains, throughput enhancements
               - Operational Changes: Shift patterns, staffing, procedures, scheduling
               - Infrastructure: Utilities, buildings, site work, foundations, structures
               - Material Changes: Raw materials, consumables, feedstocks, product specifications
               - Control Systems: Automation, instrumentation, SCADA, control logic
               - Energy Efficiency: Power consumption, heat recovery, waste minimization
               - Maintenance Strategy: Reliability improvements, preventive maintenance, spare parts
               - Safety Enhancements: Safety systems, procedures, equipment, training
               - Environmental Improvements: Emissions reduction, waste treatment, compliance
            4. For each recommendation, classify it with:
               - recommendation_category: "primary", "secondary", or "other"
               - type: Specific category (e.g., "Equipment Upgrade", "Process Optimization", etc.)
               - estimated_cost_range: Rough cost estimate
               - time_to_implement: Implementation timeline
               - dependencies: Other recommendations this depends on (if any)
               - alternative_to: Alternative approaches to other recommendations (if any)
            5. Identify ALL entities relevant for achieving each recommendation.
            6. For each relevant entity, provide a COMPLETE NODE STRUCTURE with:
            - id: unique identifier for the entity
            - type: entity type from NODE_TYPES
            - properties: complete properties object including:
                * name: entity name
                * discipline, category, subcategory, entity: MSIO classification (REQUIRED)
                * All applicable properties from NODE_PROPERTIES as found in the text
                * expected_attributes: list of attribute names to extract
                * evidence_locations: text snippets, page references, section anchors
                * extraction_rationale: why this entity is relevant
                * extraction_priority: priority level (high/medium/low)

            BASE CASE TEXT (CHUNK {chunk_seq} of {len(chunks)}):
            {chunk_text}

            INSTRUCTIONS:
            - THINK BROADLY: Don't just focus on obvious equipment upgrades. Explore all aspects:
              * Equipment: pumps, tanks, vessels, reactors, heat exchangers, compressors, filters, separators
              * Processes: reaction conditions, separation methods, purification steps, material handling
              * Operations: work schedules, batch vs continuous, staffing levels, training
              * Infrastructure: utilities (steam, cooling water, electricity), buildings, site improvements
              * Materials: feed quality, product specifications, consumables, catalysts
              * Controls: automation level, instrumentation, data collection, process control
              * Energy: power consumption, heat integration, waste heat recovery, efficiency
              * Maintenance: reliability, spare parts, preventive maintenance, condition monitoring
              * Safety: safety systems, emergency response, hazard mitigation, personal protective equipment
              * Environment: emissions, waste streams, treatment systems, compliance
            - Generate MINIMUM 15 recommendations (ideally 20-30+), distributed across categories:
              * 5-10 primary recommendations (direct, high-impact solutions)
              * 5-10 secondary recommendations (supporting/enabling changes)
              * 5-10 other recommendations (alternatives, innovations, lower priority)
            - For each recommendation, identify ALL entities that should be modified/replaced/added.
            - Prioritize recommendations based on impact, feasibility, and cost-effectiveness.
            - For each relevant entity, exhaustively combine all possible information from the base case reports and provide a COMPLETE NODE STRUCTURE:
                * Include id, type, and properties fields
                * Include all applicable properties from NODE_PROPERTIES
                * Include complete MSIO classification (discipline, category, subcategory, entity)
                * Include expected_attributes, evidence_locations, extraction_rationale, extraction_priority in properties
                * Explicitly encode based on the objective: {global_objective_type} and target magnitude of change by: {global_objective_target} whether the entity is a fixed or floating entity.
                * Explicitly encode in the attributes the direction of the change: encode the direction of the change in the attributes. 
                * Explicitly encode in the attributes the unit of the change: encode the unit of the change in the attributes.
                * Explicitly encode in the attributes the basis year of the change: encode the basis year of the change in the attributes.
                * Explicitly encode in the attributes the currency of the change: encode the currency of the change in the attributes.
                * Explicitly encode in the attributes the source of the change: encode the source of the change in the attributes.
                * Explicitly encode in the attributes the update frequency of the change: encode the update frequency of the change in the attributes.
                * Explicitly encode in the attributes the effective life of the change: encode the effective life of the change in the attributes.
                * Explicitly encode in the attributes the reclamation cost of the change: encode the reclamation cost of the change in the attributes.
            - Include evidence locations (text snippets, page numbers, section references) to guide entity extraction.
            - List expected attributes that should be extracted for each entity.
            - Be COMPREHENSIVE: identify all entities relevant to ALL recommendations across ALL categories.
            - ALL relevant_entities must follow the exact structure: id, type, properties (with all NODE_PROPERTIES)
            - NOTE: This is chunk {chunk_seq} of {len(chunks)}. Focus on recommendations and entities found in this section, but consider how they relate to the overall objective.

            EXAMPLES OF RECOMMENDATION TYPES TO EXPLORE:
            - Equipment Upgrade: "Upgrade pump from 100 gpm to 125 gpm capacity"
            - Process Optimization: "Optimize reaction temperature to increase yield by 10%"
            - Operational Change: "Implement 24/7 operation with 3-shift schedule"
            - Infrastructure: "Install additional cooling water system capacity"
            - Material Change: "Switch to higher-grade feedstock for improved efficiency"
            - Control System: "Implement advanced process control (APC) system"
            - Energy Efficiency: "Install heat exchanger to recover waste heat"
            - Maintenance Strategy: "Implement predictive maintenance program"
            - Safety Enhancement: "Install automated emergency shutdown system"
            - Environmental Improvement: "Add scrubber system to reduce emissions"

            IMPORTANT:
            - EXPLORE EXHAUSTIVELY: Think beyond the obvious. Consider all system components, processes, and operations.
            - Generate a COMPREHENSIVE set: Aim for 15-30+ recommendations across all categories.
            - Categorize properly: Primary = direct high-impact solutions, Secondary = supporting changes, Other = alternatives/innovations.
            - Be thorough: Every significant system component, process step, and operational aspect should be considered.
            
            Return recommendations with extract_recommendations(recommendations=[...]) as per the output contract.
            """

                system_prompt = SystemMessage(
                    content="You are an expert process engineer and cost estimator. Analyze base case documents and provide recommendations for system redesign based on global objectives, including queryable entity information for MongoDB lookup."
                )
                human_message = HumanMessage(content=recommendations_prompt)

                messages = [system_prompt, human_message]
                resp = self._llm_recommendations.invoke(messages)

                # Process tool calls for this chunk
                chunk_recommendations = []
                chunk_entities = []

                for call in resp.additional_kwargs.get("tool_calls", []):
                    fn = call.get("function", {})
                    name = fn.get("name")

                    if name == "extract_recommendations":
                        arguments = fn.get("arguments", "{}")
                        if is_valid_json(arguments):
                            payload = json.loads(arguments)
                            payload = sanitize_for_json(payload)
                            chunk_recommendations = payload.get("recommendations", [])
                            chunk_entities = payload.get("relevant_entities", [])
                            break

                # Deduplicate and merge recommendations
                for rec in chunk_recommendations:
                    rec_id = rec.get("recommendation_id")
                    if rec_id and rec_id not in recommendation_ids_seen:
                        recommendation_ids_seen.add(rec_id)
                        all_recommendations.append(rec)
                    elif not rec_id:
                        # If no ID, add with generated ID to avoid duplicates
                        rec["recommendation_id"] = f"R{len(all_recommendations) + 1}"
                        all_recommendations.append(rec)

                # Deduplicate and merge entities
                for entity in chunk_entities:
                    entity_id = entity.get("id") or entity.get("_id")
                    if entity_id and entity_id not in entity_ids_seen:
                        entity_ids_seen.add(entity_id)
                        all_entities_for_costing.append(entity)
                    elif not entity_id:
                        # If no ID, generate one and add
                        entity["id"] = str(uuid.uuid4())
                        all_entities_for_costing.append(entity)

                logger.info(
                    f"Chunk {chunk_seq}/{len(chunks)}: extracted {len(chunk_recommendations)} recommendations, "
                    f"{len(chunk_entities)} entities (total so far: {len(all_recommendations)} recommendations, "
                    f"{len(all_entities_for_costing)} entities)"
                )

            # Sort recommendations by category (primary first, then secondary, then other)
            category_order = {"primary": 0, "secondary": 1, "other": 2}
            all_recommendations.sort(
                key=lambda r: (
                    category_order.get(r.get("recommendation_category", "other"), 2),
                    r.get("recommendation_id", ""),
                )
            )

            # Log recommendation counts by category
            primary_count = sum(
                1
                for r in all_recommendations
                if r.get("recommendation_category") == "primary"
            )
            secondary_count = sum(
                1
                for r in all_recommendations
                if r.get("recommendation_category") == "secondary"
            )
            other_count = sum(
                1
                for r in all_recommendations
                if r.get("recommendation_category") == "other"
            )

            logger.info(
                f"Extracted {len(all_recommendations)} total recommendations from {len(chunks)} chunks "
                f"(Primary: {primary_count}, Secondary: {secondary_count}, Other: {other_count}) "
                f"and {len(all_entities_for_costing)} entities for costing"
            )

            return {
                "recommendations": all_recommendations,
                "entities_for_costing": all_entities_for_costing,
            }

        except Exception as e:
            logger.error(
                f"Error extracting recommendations (V3 chunked) for document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "recommendations": [],
                "entities_for_costing": [],
            }

    async def _retrieve_relevant_entities_v3(
        self,
        project_id: str,
        scenario_id: str,
        recommendations: List[Dict[str, Any]],
        entities_for_costing: List[Dict[str, Any]],
        artifact_type: str = "base_case",
    ) -> List[Dict[str, Any]]:
        """
        Query entities using semantic search (Pinecone) with MongoDB fallback.
        Create placeholders if no matches found.

        Args:
            project_id: Project identifier
            scenario_id: Scenario identifier
            recommendations: List of recommendation dictionaries
            entities_for_costing: List of entity specifications from recommendations extraction
            artifact_type: Type of artifact (default: "base_case")

        Returns:
            List of entity documents (matched + placeholders)
        """
        from ..parsing.storage.document_store import DocumentStore
        from ..parsing.storage.vector_store import (
            search_entities_by_embedding,
            generate_embeddings,
            EntityVectorStore,
        )

        document_store = DocumentStore()
        entity_vector_store = EntityVectorStore()
        matched_entities = []
        placeholder_entities = []

        try:
            # Use entities_for_costing directly (passed from recommendations extraction)
            all_entities_for_costing = entities_for_costing

            # If no entities_for_costing, try to extract from recommendation structure
            if not all_entities_for_costing:
                logger.warning(
                    "No entities_for_costing found, attempting to extract from recommendation structure"
                )
                # Try to extract entity information from recommendation descriptions
                # Look for affected_entities in recommendations
                for rec in recommendations:
                    affected_entities = rec.get("affected_entities", [])
                    if affected_entities:
                        # Create basic entity specs from affected_entities names
                        for entity_name in affected_entities:
                            all_entities_for_costing.append(
                                {
                                    "_id": f"E{len(all_entities_for_costing) + 1}",
                                    "type": "Unknown",
                                    "properties": {
                                        "name": entity_name,
                                        "discipline": "",
                                        "category": "",
                                        "subcategory": "",
                                        "entity": "",
                                    },
                                }
                            )

            # Process each entity specification with semantic search
            for entity_spec in all_entities_for_costing:
                # Normalize entity_spec to match MongoDB entity format
                # Entity spec format: {_id, type, properties: {name, discipline, category, subcategory, entity, ...}}
                properties = entity_spec.get("properties", {})

                # Extract name from properties if not at top level (normalize format)
                entity_name = properties.get("name") or entity_spec.get(
                    "name", "unknown"
                )
                entity_type = entity_spec.get("type")

                # Ensure MSIO fields are in properties dict (normalize structure)
                normalized_properties = properties.copy()
                if "name" not in normalized_properties:
                    normalized_properties["name"] = entity_name

                # Convert expected_attributes to readable format if present
                if "expected_attributes" in normalized_properties:
                    expected_attrs = normalized_properties["expected_attributes"]
                    if isinstance(expected_attrs, list):
                        # Convert list to comma-separated string for better semantic matching
                        normalized_properties["attributes"] = ", ".join(
                            str(attr) for attr in expected_attrs if attr
                        )

                # Attributes to exclude
                attributes_to_exclude = [
                    "expected_attributes",
                    "evidence_locations",
                    "extraction_rationale",
                    "extraction_priority",
                ]

                for attr in attributes_to_exclude:
                    if attr in normalized_properties:
                        del normalized_properties[attr]

                found_entity = None

                try:
                    # Convert entity_spec to entity-like dict matching MongoDB format exactly
                    # Format: {id, type, name, properties: {name, discipline, category, subcategory, entity, ...}}
                    entity_like_dict = {
                        "id": entity_spec.get("_id") or entity_spec.get("id", ""),
                        "type": entity_type or "Unknown",
                        "name": entity_name,
                        "properties": normalized_properties,
                    }
                    # Build text representation for embedding
                    text_for_embedding = entity_vector_store.build_text_for_embedding(
                        entity_like_dict
                    )

                    logger.info(
                        f"Semantic search for '{entity_name}': "
                        f"project_id={project_id}, scenario_id={scenario_id}, "
                        f"artifact_type={artifact_type}"
                    )
                    logger.debug(
                        f"Semantic search query text for '{entity_name}': {text_for_embedding}"
                    )

                    # Generate embedding
                    embeddings = generate_embeddings([text_for_embedding])
                    if not embeddings:
                        raise ValueError("Failed to generate embedding")

                    embedding = embeddings[0]
                    logger.debug(
                        f"Generated embedding vector of length {len(embedding)} for '{entity_name}'"
                    )

                    # Search Pinecone with progressive cutoff fallback
                    # Note: For base_case entities, scenario_id filter is automatically skipped
                    # because base case entities don't have scenario_id (they're shared across scenarios)
                    semantic_matches = None
                    cutoff_used = 0.7
                    used_scenario_filter = (
                        artifact_type != "base_case" and scenario_id is not None
                    )

                    # Search with progressive cutoff (0.7, then 0.5)
                    # scenario_id filter is handled automatically in search_entities_by_embedding
                    for cutoff_attempt in [0.5]:
                        semantic_matches = search_entities_by_embedding(
                            embedding=embedding,
                            project_id=project_id,
                            # scenario_id=scenario_id if artifact_type != "base_case" else None, # DON't search for scenario_id
                            artifact_type=artifact_type,
                            entity_types=None,  # Remove type filter - rely on semantic similarity
                            top_k=5,
                            cutoff=cutoff_attempt,
                        )

                        if semantic_matches:
                            cutoff_used = cutoff_attempt
                            logger.info(
                                f"Semantic search found {len(semantic_matches)} matches for '{entity_name}' "
                                f"with cutoff {cutoff_attempt} "
                                f"({'with scenario_id filter' if used_scenario_filter else 'without scenario_id filter (base_case)'})"
                            )
                            break
                        else:
                            logger.debug(
                                f"Semantic search found no matches for '{entity_name}' "
                                f"with cutoff {cutoff_attempt}, trying lower cutoff..."
                            )

                    # Log all match scores for debugging (even if filtered)
                    if semantic_matches:
                        score_details = [
                            f"{m.get('id', 'unknown')}: {m.get('relevance_score', 0):.3f}"
                            for m in semantic_matches
                        ]
                        logger.debug(
                            f"Semantic match scores for '{entity_name}': {', '.join(score_details)}"
                        )

                        # Log stored entity text_content for comparison (first match)
                        top_match = semantic_matches[0]
                        stored_text = (
                            top_match.get("properties", {}).get("text_content") or "N/A"
                        )
                        logger.debug(
                            f"Stored entity text_content (first match) for '{entity_name}': "
                            f"{stored_text[:300]}..."
                        )

                        # Compare MSIO hierarchies
                        stored_props = top_match.get("properties", {})
                        stored_msio = (
                            f"{stored_props.get('discipline', 'N/A')} > "
                            f"{stored_props.get('category', 'N/A')} > "
                            f"{stored_props.get('subcategory', 'N/A')} > "
                            f"{stored_props.get('entity', 'N/A')}"
                        )
                        query_msio = (
                            f"{normalized_properties.get('discipline', 'N/A')} > "
                            f"{normalized_properties.get('category', 'N/A')} > "
                            f"{normalized_properties.get('subcategory', 'N/A')} > "
                            f"{normalized_properties.get('entity', 'N/A')}"
                        )
                        logger.debug(
                            f"MSIO comparison for '{entity_name}': "
                            f"Stored: {stored_msio}, Query: {query_msio}"
                        )

                    # Filter results by scenario_id if not already filtered by Pinecone
                    if semantic_matches:
                        filtered_matches = []
                        for match in semantic_matches:
                            match_props = match.get("properties", {})
                            match_scenario_id = match_props.get("scenario_id")

                            if match_scenario_id == scenario_id:
                                filtered_matches.append(match)
                            else:
                                logger.debug(
                                    f"Filtered out match {match.get('id')} for '{entity_name}': "
                                    f"scenario_id mismatch (expected: {scenario_id}, got: {match_scenario_id})"
                                )

                        if filtered_matches:
                            # Use top match (already sorted by relevance_score)
                            found_entity = filtered_matches[0]
                            logger.info(
                                f"Semantic search found entity for '{entity_name}': "
                                f"id={found_entity.get('id')}, "
                                f"score={found_entity.get('relevance_score', 0):.3f}, "
                                f"cutoff={cutoff_used}"
                            )
                        elif semantic_matches:
                            # If we have matches but none match scenario_id, use top match anyway
                            # (scenario_id might not be in Pinecone metadata)
                            found_entity = semantic_matches[0]
                            logger.info(
                                f"Semantic search found entity for '{entity_name}' "
                                f"(scenario_id not verified): id={found_entity.get('id')}, "
                                f"score={found_entity.get('relevance_score', 0):.3f}, "
                                f"cutoff={cutoff_used}"
                            )
                    else:
                        logger.debug(
                            f"No semantic matches found for '{entity_name}' "
                            f"even with cutoff 0.5"
                        )

                except Exception as e:
                    logger.warning(
                        f"Semantic search failed for entity '{entity_name}': {e}. "
                        f"Falling back to MongoDB exact query."
                    )

                # Fallback to MongoDB exact query if semantic search didn't find a match
                if not found_entity:
                    query = {
                        "properties.project_id": project_id,
                        "properties.scenario_id": scenario_id,
                        "properties.artifact_type": artifact_type,
                    }

                    # Match by entity name
                    if entity_name:
                        query["properties.name"] = {
                            "$regex": entity_name,
                            "$options": "i",
                        }

                    # Match by MSIO classification (directly from properties)
                    if properties.get("discipline"):
                        query["properties.discipline"] = properties["discipline"]
                    if properties.get("category"):
                        query["properties.category"] = properties["category"]
                    if properties.get("subcategory"):
                        query["properties.subcategory"] = properties["subcategory"]
                    if properties.get("entity"):
                        query["properties.entity"] = properties["entity"]

                    # Match by entity type (at top level)
                    if entity_type:
                        query["type"] = entity_type

                    # Query MongoDB
                    found_entities = list(document_store._db.entities.find(query))

                    if found_entities:
                        found_entity = found_entities[0]  # Use first match
                        logger.info(
                            f"MongoDB exact query found {len(found_entities)} matching entities "
                            f"for '{entity_name}'"
                        )

                # Add matched entity or create placeholder
                if found_entity:
                    matched_entities.append(found_entity)
                else:
                    # Create placeholder entity
                    placeholder = self._create_placeholder_entity(
                        entity_spec, project_id, scenario_id, artifact_type
                    )
                    placeholder_entities.append(placeholder)
                    logger.info(
                        f"Created placeholder entity for '{entity_name}' "
                        f"(no matches found via semantic search or MongoDB)"
                    )

            # Remove duplicates from matched_entities (by _id)
            seen_ids = set()
            unique_matched = []
            for entity in matched_entities:
                entity_id = entity.get("_id") or entity.get("id")
                if entity_id and entity_id not in seen_ids:
                    seen_ids.add(entity_id)
                    unique_matched.append(entity)

            logger.info(
                f"Retrieved {len(unique_matched)} matched entities (semantic search + MongoDB) "
                f"and created {len(placeholder_entities)} placeholder entities"
            )

            return unique_matched + placeholder_entities

        except Exception as e:
            logger.error(
                f"Error retrieving relevant entities (V3): {e}",
                exc_info=True,
            )
            # Return placeholders even on error
            return placeholder_entities

    def _create_placeholder_entity(
        self,
        entity_spec: Dict[str, Any],
        project_id: str,
        scenario_id: str,
        artifact_type: str,
    ) -> Dict[str, Any]:
        """
        Create a placeholder entity from recommendation specification.

        Args:
            entity_spec: Entity specification from recommendations (format: {_id, type, properties: {...}})
            project_id: Project identifier
            scenario_id: Scenario identifier
            artifact_type: Type of artifact

        Returns:
            Placeholder entity dictionary
        """
        # Use existing _id from entity_spec if available, otherwise generate new UUID
        entity_id = entity_spec.get("_id") or entity_spec.get("id") or str(uuid.uuid4())

        # Extract properties from entity spec (format: {_id, type, properties: {...}})
        properties = entity_spec.get("properties", {})
        entity_name = properties.get("name", "Unknown Entity")
        entity_type = entity_spec.get("type", "Unknown")

        placeholder = {
            "_id": entity_id,
            "id": entity_id,
            "type": entity_type,
            "properties": {
                "name": entity_name,
                "discipline": properties.get("discipline", ""),
                "category": properties.get("category", ""),
                "subcategory": properties.get("subcategory", ""),
                "entity": properties.get("entity", ""),
                "project_id": project_id,
                "scenario_id": scenario_id,
                "artifact_type": artifact_type,
                "is_placeholder": True,
                "attributes": [],
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Preserve additional properties from entity_spec if available
        # (e.g., expected_attributes, evidence_locations, extraction_rationale, extraction_priority)
        for key in [
            "expected_attributes",
            "evidence_locations",
            "extraction_rationale",
            "extraction_priority",
        ]:
            if key in properties:
                placeholder["properties"][key] = properties[key]

        return placeholder

    async def _store_recommendations_v3(
        self,
        document_id: str,
        project_id: str,
        scenario_id: str,
        user_id: str,
        global_objective_type: str,
        global_objective_target: str,
        recommendations: List[Dict[str, Any]],
        relevant_entities: List[Dict[str, Any]],
        overwrite: bool = True,
    ) -> str:
        """
        Store recommendations in MongoDB (V3 format).

        Args:
            document_id: Document identifier
            project_id: Project identifier
            scenario_id: Scenario identifier
            user_id: User identifier
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            recommendations: List of recommendation dictionaries
            relevant_entities: List of relevant entities from MongoDB query
            overwrite: If True, update existing recommendation matching scenario_id, project_id, and document_id.
                      If False, always create a new recommendation document. Default: True

        Returns:
            Recommendations document ID
        """
        try:
            # If overwrite is True, check for existing recommendation
            if overwrite:
                existing_doc = db().base_case_recommendations.find_one(
                    {
                        "scenario_id": scenario_id,
                        "project_id": project_id,
                        "document_id": document_id,
                        "workflow_version": "v3",
                    }
                )

                if existing_doc:
                    # Update existing document
                    recommendations_id = existing_doc.get("_id") or existing_doc.get(
                        "id"
                    )
                    existing_created_at = existing_doc.get("created_at")

                    recommendations_doc = {
                        "_id": recommendations_id,
                        "id": recommendations_id,
                        "document_id": document_id,
                        "project_id": project_id,
                        "scenario_id": scenario_id,
                        "user_id": user_id,
                        "global_objective_type": global_objective_type,
                        "global_objective_target": global_objective_target,
                        "recommendations": recommendations,
                        "relevant_entities": relevant_entities,
                        "workflow_version": "v3",
                        "created_at": existing_created_at
                        or datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }

                    db().base_case_recommendations.replace_one(
                        {"_id": recommendations_id}, recommendations_doc
                    )

                    logger.info(
                        f"Updated existing recommendations (V3) {recommendations_id} for document {document_id}"
                    )
                    return str(recommendations_id)

            # Create new recommendation document (either overwrite=False or no existing doc found)
            recommendations_id = str(uuid.uuid4())
            recommendations_doc = {
                "_id": recommendations_id,
                "id": recommendations_id,
                "document_id": document_id,
                "project_id": project_id,
                "scenario_id": scenario_id,
                "user_id": user_id,
                "global_objective_type": global_objective_type,
                "global_objective_target": global_objective_target,
                "recommendations": recommendations,
                "relevant_entities": relevant_entities,
                "workflow_version": "v3",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            db().base_case_recommendations.insert_one(recommendations_doc)

            logger.info(
                f"Stored new recommendations (V3) {recommendations_id} for document {document_id}"
            )
            return recommendations_id

        except Exception as e:
            logger.error(
                f"Error storing recommendations (V3) for document {document_id}: {e}",
                exc_info=True,
            )
            return ""

    async def _extract_objective_driven_nodes_and_relations_v4(
        self,
        full_text: str,
        global_objective_type: str,
        global_objective_target: str,
        objective_description: Optional[str],
        document_id: str,
        project_id: str,
        scenario_id: Optional[str] = None,
        global_objective_unit: str = "%",
        job_id: Optional[str] = None,
        publisher=None,
        base_seq: int = 0,
    ) -> Dict[str, Any]:
        """
        Extract objective-driven nodes and relations using V4 workflow.

        This method chunks the full text, uses recommendation-based entity extraction prompt,
        and extracts nodes and edges using LLM with tools.

        Args:
            full_text: Full text content of the document
            global_objective_type: Type of global objective
            global_objective_target: Target magnitude of change
            objective_description: Optional description of the global objective
            document_id: Document identifier
            global_objective_unit: Unit of the global objective
        Returns:
            Dictionary with nodes and edges extracted from the document
        """
        logger.info(
            f"Extracting objective-driven nodes and relations (V4) for objective: "
            f"{global_objective_type} ({global_objective_target} {global_objective_unit})"
        )

        # # Get progress publisher if job_id is provided
        # publisher = None
        # if job_id:
        #     try:
        #         from ....api.v1.routers.websocket import get_progress_publisher
        #         from ..progress.events import ProgressEvent, Stage, Status
        #         publisher = get_progress_publisher()
        #     except Exception as e:
        #         logger.warning(f"Could not get progress publisher for job_id {job_id}: {e}")
        # Import progress event types if publisher is provided
        if publisher and job_id:
            from ..progress.events import ProgressEvent, Stage, Status
        try:
            # Import chunking utilities
            import uuid

            # Use same namespace as DocumentProcessingService
            CHUNK_NAMESPACE = uuid.UUID("11111111-2222-3333-4444-555555555555")

            # Chunk the text
            char_limit = 5000
            overlap = 1000

            # Create chunks with overlap manually
            chunks = []
            current_pos = 0
            seq = 1

            while current_pos < len(full_text):
                chunk_text = full_text[current_pos : current_pos + char_limit]
                chunk_id = str(uuid.uuid5(CHUNK_NAMESPACE, f"{document_id}|{seq}"))

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "doc_id": document_id,
                        "seq": seq,
                        "text": chunk_text,
                        "start_pos": current_pos,
                        "end_pos": current_pos + len(chunk_text),
                    }
                )

                # Move forward by char_limit - overlap to create overlap
                current_pos += char_limit - overlap
                seq += 1

                # Break if we've reached the end
                if current_pos >= len(full_text):
                    break

            logger.info(
                f"Created {len(chunks)} chunks for entity extraction "
                f"(char_limit: {char_limit}, overlap: {overlap})"
            )

            # Publish event after chunking
            if publisher and job_id:
                try:
                    publisher.publish(
                        job_id,
                        ProgressEvent(
                            job_id=job_id,
                            stage=Stage.PROCESSING,
                            status=Status.IN_PROGRESS,
                            progress=50,
                            seq=base_seq,
                            meta={
                                "document_id": document_id,
                                "total_chunks": len(chunks),
                                "base_seq": base_seq,
                                "message": "Chunking text for entity extraction",
                            },
                        ),
                    )
                except Exception as e:
                    logger.warning(f"Failed to publish progress event: {e}")

            # Build objective context for the prompt
            objective_context = f"""
                GLOBAL OBJECTIVE:
                - Objective type: {global_objective_type}
                - Target magnitude of change: {global_objective_target} {global_objective_unit}
                """
            if objective_description:
                objective_context += f"- Description: {objective_description}\n"

            # Get the recommendation-based entity extraction prompt
            rules = [
                "NODES_AND_RELATIONS",
                "PROVENANCE_AND_CONFIDENCE",
                "UNITS_NORMALIZATION",
            ]
            base_prompt = generate_prompt(
                artifact_type="base_case",
                objective_type=global_objective_type,
                objective_target=global_objective_target,
                objective_unit=global_objective_unit,
                rules=rules,
            )

            # Add objective context to the prompt
            full_user_prompt = f"""{base_prompt}

            {objective_context}
            """

            # Prepare system prompt
            system_prompt = SystemMessage(content=full_user_prompt)

            # Collect all extracted data
            all_nodes = []
            all_edges = []
            node_ids_seen = set()
            edge_ids_seen = set()

            # Process each chunk
            for chunk_idx, chunk in enumerate(chunks):
                # Check for cancellation at the start of each chunk iteration
                # This allows the task to be cancelled between chunks
                # Note: We check cancellation by attempting to access the task registry
                # If the task was cancelled, it will raise CancelledError when awaited
                # We'll catch it in the outer try-except block

                chunk_text = chunk["text"]
                chunk_seq = chunk["seq"]

                logger.info(
                    f"Processing chunk {chunk_seq}/{len(chunks)} "
                    f"(positions {chunk['start_pos']}-{chunk['end_pos']}, "
                    f"{len(chunk_text)} chars)"
                )

                # Publish event before processing chunk
                if publisher and job_id:
                    try:
                        progress_chunk = 50 + int(chunk_idx * 40 / len(chunks))
                        publisher.publish(
                            job_id,
                            ProgressEvent(
                                job_id=job_id,
                                stage=Stage.PROCESSING,
                                status=Status.IN_PROGRESS,
                                progress=progress_chunk,
                                seq=base_seq + chunk_idx + 1,
                                meta={
                                    "document_id": document_id,
                                    "chunk_index": chunk_idx + 1,
                                    "total_chunks": len(chunks),
                                    "base_seq": base_seq,
                                    "message": f"Extracting entities from text > processing text chunk {chunk_idx + 1} of {len(chunks)}",
                                },
                            ),
                        )
                    except Exception as e:
                        logger.warning(f"Failed to publish progress event: {e}")

                try:
                    # Prepare messages with chunk text (following entity_extractor pattern)
                    human_message = HumanMessage(content=chunk_text)
                    messages = [system_prompt, human_message]

                    # Invoke LLM with tools
                    resp = await self._llm_objective_driven.ainvoke(messages)

                    # Track counts for this chunk
                    chunk_nodes_count = 0
                    chunk_edges_count = 0

                    # Process tool calls
                    for call in resp.additional_kwargs.get("tool_calls", []):
                        fn = call.get("function", {})
                        name = fn.get("name")

                        try:
                            arguments = fn.get("arguments", "{}")
                            if not is_valid_json(arguments):
                                logger.error(
                                    f"Invalid JSON received for {name}: {arguments}"
                                )
                                continue

                            payload = json.loads(arguments)
                            payload = sanitize_for_json(payload)

                            if name == "extract_nodes":
                                nodes = payload.get("nodes", [])
                                # Deduplicate nodes by ID
                                for node in nodes:
                                    # Generate ID
                                    node["id"] = str(uuid.uuid4())
                                    all_nodes.append(node)
                                    chunk_nodes_count += 1
                                    logger.warning(
                                        f"Generated ID for node without ID in chunk {chunk_seq}"
                                    )

                            elif name == "extract_edges":
                                edges = payload.get("edges", [])
                                # Deduplicate edges by ID
                                for edge in edges:
                                    # Generate ID
                                    edge["id"] = str(uuid.uuid4())
                                    all_edges.append(edge)
                                    chunk_edges_count += 1
                                    logger.warning(
                                        f"Generated ID for edge without ID in chunk {chunk_seq}"
                                    )

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse LLM JSON for {name}: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing tool call {name}: {e}")
                            continue

                except Exception as e:
                    logger.error(
                        f"Error processing chunk {chunk_seq}/{len(chunks)}: {e}",
                        exc_info=True,
                    )
                    continue

                logger.info(
                    f"Chunk {chunk_seq}/{len(chunks)}: extracted {chunk_nodes_count} nodes, "
                    f"{chunk_edges_count} edges (total: {len(all_nodes)} nodes, {len(all_edges)} edges)"
                )

            logger.info(
                f"Extracted {len(all_nodes)} total nodes and {len(all_edges)} total edges "
                f"from {len(chunks)} chunks"
            )

            # Publish event after all chunks processed
            if publisher and job_id:
                try:
                    publisher.publish(
                        job_id,
                        ProgressEvent(
                            job_id=job_id,
                            stage=Stage.PROCESSING,
                            status=Status.IN_PROGRESS,
                            progress=90,
                            seq=base_seq + len(chunks) + 1,
                            meta={
                                "document_id": document_id,
                                "total_nodes": len(all_nodes),
                                "total_edges": len(all_edges),
                                "base_seq": base_seq,
                                "message": "Completed entity extraction",
                            },
                        ),
                    )
                except Exception as e:
                    logger.warning(f"Failed to publish progress event: {e}")

            # Calculate and validate total costs
            calculated_totals = self._calculate_total_base_case_costs(
                entities=all_nodes,
                project_id=project_id,
                scenario_id=scenario_id,
            )
            extracted_totals = self._extract_total_costs_from_entities(all_nodes)
            cost_validation = self._validate_total_costs(
                calculated_totals, extracted_totals
            )

            return {
                "nodes": all_nodes,
                "edges": all_edges,
                "num_chunks": len(
                    chunks
                ),  # Return chunk count for sequence number tracking
                "cost_summary": {
                    "calculated_totals": calculated_totals,
                    "extracted_totals": extracted_totals,
                    "validation": cost_validation,
                },
            }

        except asyncio.CancelledError:
            logger.info(
                f"Extraction cancelled for document {document_id} (job_id: {job_id})"
            )
            # Publish cancellation event if publisher is available
            if publisher and job_id:
                try:
                    publisher.publish(
                        job_id,
                        ProgressEvent(
                            job_id=job_id,
                            stage=Stage.ERROR,
                            status=Status.FAILED,
                            progress=0,
                            seq=base_seq + len(chunks) + 2,
                            meta={
                                "document_id": document_id,
                                "message": "Extraction cancelled by user",
                            },
                        ),
                    )
                except Exception as e:
                    logger.warning(f"Failed to publish cancellation event: {e}")
            # Re-raise to propagate cancellation
            raise
        except Exception as e:
            logger.error(
                f"Error extracting objective-driven nodes and relations (V4) "
                f"for document {document_id}: {e}",
                exc_info=True,
            )
            return {
                "nodes": [],
                "edges": [],
                "num_chunks": 0,
            }
