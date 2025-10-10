"""
Cost escalation service.

Handles cost escalation using various indices (CEPCI, CPI, etc.)
"""

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from ..repositories.table_repo import TableRepository

logger = logging.getLogger(__name__)


class EscalationService:
    """
    Cost escalation service.

    Escalates costs from base year to target year using indices.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.table_repo = TableRepository(db)

        # Hardcoded indices for common escalations
        # In production, these would come from database or external API
        self.indices = {
            "CEPCI": {
                2015: 556.8,
                2016: 541.7,
                2017: 567.5,
                2018: 603.1,
                2019: 607.5,
                2020: 596.2,
                2021: 708.0,
                2022: 816.0,
                2023: 800.0,  # Estimated
                2024: 820.0,  # Estimated
                2025: 835.0,  # Estimated
            },
            "CPI": {
                2015: 237.0,
                2016: 240.0,
                2017: 245.1,
                2018: 251.1,
                2019: 255.7,
                2020: 258.8,
                2021: 271.0,
                2022: 292.7,
                2023: 304.7,
                2024: 313.5,  # Estimated
                2025: 323.0,  # Estimated
            },
        }

    async def escalate_cost(
        self, base_cost: float, from_year: int, to_year: int, index_name: str = "CEPCI"
    ) -> Dict[str, Any]:
        """
        Escalate cost from base year to target year.

        Args:
            base_cost: Cost in base year
            from_year: Base year
            to_year: Target year
            index_name: Index to use (CEPCI, CPI, etc.)

        Returns:
            Escalation result with multiplier and escalated cost
        """
        if from_year == to_year:
            return {
                "base_cost": base_cost,
                "escalated_cost": base_cost,
                "from_year": from_year,
                "to_year": to_year,
                "multiplier": 1.0,
                "index_name": index_name,
                "source": "no_escalation_required",
            }

        # Get index values
        index_data = self.indices.get(index_name)

        if not index_data:
            logger.warning(f"Unknown index {index_name}, using CPI as fallback")
            index_data = self.indices["CPI"]
            index_name = "CPI"

        from_value = index_data.get(from_year)
        to_value = index_data.get(to_year)

        if from_value is None or to_value is None:
            raise ValueError(
                f"Index {index_name} not available for years {from_year} or {to_year}"
            )

        # Calculate multiplier
        multiplier = to_value / from_value
        escalated_cost = base_cost * multiplier

        logger.info(
            f"Escalated ${base_cost:,.0f} ({from_year}) to "
            f"${escalated_cost:,.0f} ({to_year}) using {index_name} "
            f"[{from_value} → {to_value}, multiplier: {multiplier:.3f}]"
        )

        return {
            "base_cost": base_cost,
            "escalated_cost": escalated_cost,
            "from_year": from_year,
            "to_year": to_year,
            "multiplier": multiplier,
            "index_name": index_name,
            "from_index_value": from_value,
            "to_index_value": to_value,
            "source": "hardcoded_indices",
        }
