"""
Cost estimation service.

This is the CORE USP: Intelligent cost estimation with proper:
- Equipment cost lookup from tables
- Cost escalation using indices
- Lang factor application (with correct logic)
- Detailed WBS breakdown
- Provenance tracking

This fixes the ChatGPT failures:
1. Actually looks up equipment cost from table (not just scales)
2. Uses proper lang factors from uploaded spreadsheet (not generic 2x)
3. Tracks WHERE every number came from
"""

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime

from ..repositories.table_repo import TableRepository
from ..services.escalation import EscalationService
from ..core.config import settings

logger = logging.getLogger(__name__)


class CostEstimationError(Exception):
    """Raised when cost estimation fails."""

    pass


class CostEstimator:
    """
    Cost estimation service.

    Handles all cost calculations with full provenance tracking.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.table_repo = TableRepository(db)
        self.escalation_service = EscalationService(db)

    async def estimate_equipment_cost(
        self,
        project_id: str,
        equipment_selection: Dict[str, Any],
        target_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Estimate complete equipment cost with breakdown.

        Steps:
        1. Look up base purchase cost from cost table
        2. Escalate to target year
        3. Apply lang factors for installation
        4. Build WBS breakdown
        5. Calculate total installed cost

        Args:
            project_id: Project ID
            equipment_selection: Equipment selection data
            target_year: Target year for escalation

        Returns:
            Complete cost data with provenance
        """
        model = equipment_selection["model"]
        equipment_type = equipment_selection["equipment_type"]

        logger.info(f"Estimating cost for {equipment_type} model {model}")

        # Step 1: Get base purchase cost
        cost_data = await self._get_purchase_cost(project_id, equipment_type, model)

        purchase_cost_base = cost_data["purchase_cost"]
        cost_year = cost_data["cost_year"]
        cost_source_table_id = cost_data["source_table_id"]
        cost_source_row = cost_data["source_row"]

        logger.info(f"Base purchase cost: ${purchase_cost_base:,.0f} ({cost_year})")

        # Step 2: Escalate to target year
        if target_year is None:
            target_year = datetime.now().year

        escalated = await self.escalation_service.escalate_cost(
            base_cost=purchase_cost_base,
            from_year=cost_year,
            to_year=target_year,
            index_name=settings.DEFAULT_ESCALATION_INDEX,
        )

        purchase_cost_escalated = escalated["escalated_cost"]
        escalation_multiplier = escalated["multiplier"]
        escalation_source_table_id = escalated.get("source_table_id")

        logger.info(
            f"Escalated cost: ${purchase_cost_escalated:,.0f} ({target_year}) "
            f"[multiplier: {escalation_multiplier:.3f}]"
        )

        # Step 3: Get lang factors
        lang_data = await self._get_lang_factors(project_id, equipment_type)

        equipment_multiplier = lang_data["equipment_multiplier"]
        wbs_breakdown = lang_data["wbs_breakdown"]
        lang_factor_source_table_id = lang_data["source_table_id"]

        logger.info(
            f"Lang factor: {equipment_multiplier}x "
            f"(category: {lang_data['category']})"
        )

        # Step 4: Calculate installed cost and WBS breakdown
        installed_equipment_cost = purchase_cost_escalated * equipment_multiplier

        detailed_wbs = []
        total_installed = 0.0

        # WBS breakdown
        for wbs_item in wbs_breakdown:
            wbs_code = wbs_item["wbs"]
            factor = wbs_item["factor"]
            amount = purchase_cost_escalated * factor

            detailed_wbs.append(
                {
                    "wbs": wbs_code,
                    "description": wbs_item.get("description", wbs_code),
                    "factor": factor,
                    "amount": amount,
                }
            )

            total_installed += amount

        logger.info(f"Total installed cost: ${total_installed:,.0f}")

        # Step 5: Build complete cost data
        cost_result = {
            # Base cost
            "purchase_cost_base": purchase_cost_base,
            "purchase_cost_currency": "USD",
            "purchase_cost_year": cost_year,
            # Escalation
            "escalation_index": escalated["index_name"],
            "escalation_multiplier": escalation_multiplier,
            "purchase_cost_escalated": purchase_cost_escalated,
            "escalation_target_year": target_year,
            # Installation
            "lang_factor_category": lang_data["category"],
            "equipment_multiplier": equipment_multiplier,
            "installed_equipment_cost": installed_equipment_cost,
            # Breakdown
            "wbs_breakdown": detailed_wbs,
            "total_installed_cost": total_installed,
            # Provenance (CRITICAL)
            "cost_source_table_id": cost_source_table_id,
            "cost_source_row": cost_source_row,
            "lang_factor_source_table_id": lang_factor_source_table_id,
            "escalation_source_table_id": escalation_source_table_id,
            # Confidence
            "confidence": "medium",  # Could be calculated based on data quality
            "assumptions": [
                f"Base cost from {cost_year}",
                f"Escalated using {escalated['index_name']}",
                f"Lang factors from category '{lang_data['category']}'",
                "Assumes no major scope changes",
            ],
        }

        return cost_result

    async def _get_purchase_cost(
        self, project_id: str, equipment_type: str, model: str
    ) -> Dict[str, Any]:
        """
        Look up purchase cost from cost table.

        This is what ChatGPT DIDN'T do - it just scaled the same equipment.

        Args:
            project_id: Project ID
            equipment_type: Equipment type
            model: Model designation

        Returns:
            Purchase cost data with provenance
        """
        # Get cost table
        cost_table = await self.table_repo.find_cost_table(
            project_id, equipment_type=equipment_type
        )

        if not cost_table:
            raise CostEstimationError(f"No cost table found for {equipment_type}")

        # Find row for this model
        cost_row = await self.table_repo.get_table_row(str(cost_table["_id"]), model)

        if not cost_row:
            raise CostEstimationError(
                f"No cost data found for model {model} in cost table"
            )

        # Extract purchase cost
        data = cost_row.get("data", {})
        purchase_cost = data.get("purchase_usd_2015") or data.get("purchase_cost")

        if purchase_cost is None:
            raise CostEstimationError(
                f"Purchase cost not found in row for model {model}"
            )

        # Get cost year from table metadata
        cost_year = cost_table.get("metadata", {}).get("cost_basis_year")
        if not cost_year:
            # Try to infer from field name (e.g., "purchase_usd_2015")
            for key in data.keys():
                if "2015" in key:
                    cost_year = 2015
                    break

        if not cost_year:
            logger.warning("Cost year not found in table, using default 2015")
            cost_year = 2015

        return {
            "purchase_cost": float(purchase_cost),
            "cost_year": cost_year,
            "source_table_id": str(cost_table["_id"]),
            "source_row": f"model={model}",
        }

    async def _get_lang_factors(
        self, project_id: str, equipment_type: str
    ) -> Dict[str, Any]:
        """
        Get lang factors from uploaded spreadsheet.

        This is critical - ChatGPT used generic 2x, we use ACTUAL factors.

        Args:
            project_id: Project ID
            equipment_type: Equipment type

        Returns:
            Lang factor data
        """
        # Determine category based on equipment type
        category_map = {
            "gyratory_crusher": "Primary Crushing",
            "jaw_crusher": "Primary Crushing",
            "cone_crusher": "Secondary Crushing",
            "ball_mill": "Grinding",
            "sag_mill": "Grinding",
            "conveyor": "Material Handling",
        }

        category = category_map.get(
            equipment_type, settings.DEFAULT_LANG_FACTOR_CATEGORY
        )

        # Get lang factors table
        lang_table = await self.table_repo.find_lang_factors(
            project_id, category=category
        )

        if not lang_table:
            logger.warning(
                f"No lang factors table found for category '{category}', "
                f"using defaults"
            )
            return self._get_default_lang_factors(category)

        # Extract factors
        rows = lang_table.get("extracted_data", {}).get("rows", [])

        # Find row for this category
        category_row = None
        for row in rows:
            data = row.get("data", {})
            row_category = data.get("category") or row.get("category")
            if row_category == category:
                category_row = data
                break

        if not category_row:
            logger.warning(
                f"Category '{category}' not found in lang factors table, "
                f"using defaults"
            )
            return self._get_default_lang_factors(category)

        # Extract factors
        equipment_multiplier = float(
            category_row.get("equipment_multiplier")
            or category_row.get("total_multiplier")
            or settings.DEFAULT_EQUIPMENT_MULTIPLIER
        )

        # Build WBS breakdown
        wbs_breakdown = []

        # Equipment purchase (always 1.0x of escalated cost)
        wbs_breakdown.append(
            {"wbs": "10-Equipment", "description": "Equipment Purchase", "factor": 1.0}
        )

        # Civil & Structural
        civil_factor = float(category_row.get("civil_structural_factor", 0.3))
        if civil_factor > 0:
            wbs_breakdown.append(
                {
                    "wbs": "20-Civil",
                    "description": "Civil & Structural",
                    "factor": civil_factor,
                }
            )

        # Electrical & Instrumentation
        electrical_factor = float(category_row.get("electrical_factor", 0.4))
        if electrical_factor > 0:
            wbs_breakdown.append(
                {
                    "wbs": "30-Electrical",
                    "description": "Electrical & Instrumentation",
                    "factor": electrical_factor,
                }
            )

        # Installation Labor
        installation_factor = float(category_row.get("installation_labor_factor", 0.5))
        if installation_factor > 0:
            wbs_breakdown.append(
                {
                    "wbs": "40-Installation",
                    "description": "Installation Labor",
                    "factor": installation_factor,
                }
            )

        # Indirect Costs
        indirect_pct = float(category_row.get("indirect_costs_pct", 15)) / 100.0
        # Indirect is % of subtotal
        subtotal_factor = sum(item["factor"] for item in wbs_breakdown)
        indirect_factor = subtotal_factor * indirect_pct
        wbs_breakdown.append(
            {
                "wbs": "50-Indirect",
                "description": "Indirect Costs",
                "factor": indirect_factor,
            }
        )

        # Owner's Costs
        owners_pct = float(category_row.get("owners_costs_pct", 10)) / 100.0
        owners_factor = (subtotal_factor + indirect_factor) * owners_pct
        wbs_breakdown.append(
            {
                "wbs": "60-Owners",
                "description": "Owner's Costs",
                "factor": owners_factor,
            }
        )

        # Contingency
        contingency_pct = float(category_row.get("contingency_pct", 10)) / 100.0
        total_before_contingency = sum(item["factor"] for item in wbs_breakdown)
        contingency_factor = total_before_contingency * contingency_pct
        wbs_breakdown.append(
            {
                "wbs": "70-Contingency",
                "description": "Contingency",
                "factor": contingency_factor,
            }
        )

        return {
            "category": category,
            "equipment_multiplier": equipment_multiplier,
            "wbs_breakdown": wbs_breakdown,
            "source_table_id": str(lang_table["_id"]),
        }

    def _get_default_lang_factors(self, category: str) -> Dict[str, Any]:
        """
        Get default lang factors if table not available.

        Args:
            category: Equipment category

        Returns:
            Default lang factor data
        """
        # Default factors based on industry standards
        defaults = {
            "Primary Crushing": {
                "equipment_multiplier": 3.5,
                "civil_structural_factor": 0.4,
                "electrical_factor": 0.5,
                "installation_labor_factor": 0.6,
                "indirect_costs_pct": 15,
                "owners_costs_pct": 10,
                "contingency_pct": 10,
            },
            "Material Handling": {
                "equipment_multiplier": 4.0,
                "civil_structural_factor": 0.5,
                "electrical_factor": 0.6,
                "installation_labor_factor": 0.7,
                "indirect_costs_pct": 15,
                "owners_costs_pct": 10,
                "contingency_pct": 10,
            },
            "Grinding": {
                "equipment_multiplier": 3.0,
                "civil_structural_factor": 0.3,
                "electrical_factor": 0.4,
                "installation_labor_factor": 0.5,
                "indirect_costs_pct": 15,
                "owners_costs_pct": 10,
                "contingency_pct": 10,
            },
        }

        category_defaults = defaults.get(category, defaults["Primary Crushing"])

        # Build WBS breakdown using defaults
        wbs_breakdown = [
            {"wbs": "10-Equipment", "description": "Equipment Purchase", "factor": 1.0},
            {
                "wbs": "20-Civil",
                "description": "Civil & Structural",
                "factor": category_defaults["civil_structural_factor"],
            },
            {
                "wbs": "30-Electrical",
                "description": "Electrical & Instrumentation",
                "factor": category_defaults["electrical_factor"],
            },
            {
                "wbs": "40-Installation",
                "description": "Installation Labor",
                "factor": category_defaults["installation_labor_factor"],
            },
        ]

        # Calculate indirect, owners, contingency
        subtotal = sum(item["factor"] for item in wbs_breakdown)
        indirect = subtotal * (category_defaults["indirect_costs_pct"] / 100.0)
        wbs_breakdown.append(
            {"wbs": "50-Indirect", "description": "Indirect Costs", "factor": indirect}
        )

        owners = (subtotal + indirect) * (category_defaults["owners_costs_pct"] / 100.0)
        wbs_breakdown.append(
            {"wbs": "60-Owners", "description": "Owner's Costs", "factor": owners}
        )

        total = subtotal + indirect + owners
        contingency = total * (category_defaults["contingency_pct"] / 100.0)
        wbs_breakdown.append(
            {
                "wbs": "70-Contingency",
                "description": "Contingency",
                "factor": contingency,
            }
        )

        return {
            "category": category,
            "equipment_multiplier": category_defaults["equipment_multiplier"],
            "wbs_breakdown": wbs_breakdown,
            "source_table_id": None,  # Using defaults
        }
