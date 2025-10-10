"""
Equipment selection service.

This is the CORE logic that selects appropriate equipment based on:
- Parameter changes (e.g., product size change)
- Throughput requirements
- Feed size constraints
- Availability in sizing tables

This addresses the ChatGPT failure where it didn't select different equipment.
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from ..repositories.table_repo import TableRepository
from ..core.config import settings

logger = logging.getLogger(__name__)


class EquipmentSelectionError(Exception):
    """Raised when equipment selection fails."""

    pass


class EquipmentSelector:
    """
    Equipment selection service.

    Responsible for:
    1. Understanding parameter changes
    2. Querying sizing tables
    3. Selecting suitable equipment models
    4. Validating capacity and constraints
    5. Ranking by suitability
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.table_repo = TableRepository(db)

    async def select_equipment_for_scenario(
        self, project_id: str, scenario_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Main entry point: Select equipment for a scenario.

        Args:
            project_id: Project ID
            scenario_data: Scenario data including parameter_changes

        Returns:
            List of suitable equipment selections

        Raises:
            EquipmentSelectionError: If no suitable equipment found
        """
        parameter_changes = scenario_data.get("parameter_changes", [])
        constraints = scenario_data.get("constraints", {})

        # Determine equipment type from parameter changes
        equipment_type = self._determine_equipment_type(parameter_changes)

        if equipment_type == "gyratory_crusher":
            return await self._select_gyratory_crusher(
                project_id, parameter_changes, constraints
            )
        elif equipment_type == "jaw_crusher":
            return await self._select_jaw_crusher(
                project_id, parameter_changes, constraints
            )
        else:
            raise EquipmentSelectionError(
                f"Unsupported equipment type: {equipment_type}"
            )

    def _determine_equipment_type(self, parameter_changes: List[Dict[str, Any]]) -> str:
        """
        Determine equipment type from parameter changes.

        Args:
            parameter_changes: List of parameter changes

        Returns:
            Equipment type string
        """
        # Check if any parameter is related to crushing
        for change in parameter_changes:
            param = change.get("parameter", "").lower()
            if "crusher" in param or "crushing" in param:
                # Default to gyratory for now
                # In a real system, this would be more sophisticated
                return "gyratory_crusher"

        # Default
        return "gyratory_crusher"

    async def _select_gyratory_crusher(
        self,
        project_id: str,
        parameter_changes: List[Dict[str, Any]],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Select gyratory crusher models.

        This is the logic that ChatGPT missed:
        - Look at NEW product size requirement
        - Query sizing table for models that meet requirement
        - Validate throughput capacity
        - Return multiple candidates

        Args:
            project_id: Project ID
            parameter_changes: List of parameter changes
            constraints: Constraints

        Returns:
            List of suitable crusher models
        """
        # Extract target product size
        target_p80_in = None
        for change in parameter_changes:
            if change.get("parameter") == "crusher_product_size":
                target_p80_in = float(change.get("to_value"))
                break

        if target_p80_in is None:
            raise EquipmentSelectionError(
                "No crusher_product_size parameter found in changes"
            )

        logger.info(f"Selecting crusher for P80 = {target_p80_in} inches")

        # Get sizing table
        sizing_table = await self.table_repo.find_sizing_table(
            project_id, equipment_type="gyratory_crusher"
        )

        if not sizing_table:
            raise EquipmentSelectionError(
                "No gyratory crusher sizing table found for project"
            )

        # Extract rows from sizing table
        rows = sizing_table.get("extracted_data", {}).get("rows", [])

        if not rows:
            raise EquipmentSelectionError("Sizing table has no rows")

        # Get throughput requirement
        required_tph = constraints.get("min_throughput_tph")
        max_feed_in = constraints.get("max_feed_size_in")

        # Select suitable models
        candidates = []
        rejected = []

        for row in rows:
            model = row.get("model") or row.get("data", {}).get("model")
            data = row.get("data", {})

            # Validate required fields exist
            required_fields = ["min_p80_in", "max_tph", "power_kW"]
            missing = [f for f in required_fields if data.get(f) is None]
            if missing:
                rejected.append(
                    {
                        "model": model,
                        "reason": f"Missing fields: {missing}",
                        "data": data,
                    }
                )
                continue

            try:
                # Extract and convert values
                min_p80 = float(data["min_p80_in"])
                max_p80 = float(data.get("max_p80_in", 999))
                max_capacity_tph = float(data["max_tph"])
                power_kw = float(data["power_kW"])
                feed_opening_in = data.get("feed_opening_in")

                # Check P80 constraint
                if not (min_p80 <= target_p80_in <= max_p80):
                    rejected.append(
                        {
                            "model": model,
                            "reason": f'P80 {target_p80_in}" outside range [{min_p80}, {max_p80}]',
                            "data": data,
                        }
                    )
                    continue

                # Check throughput constraint
                capacity_margin_pct = None
                if required_tph is not None:
                    if max_capacity_tph < required_tph:
                        rejected.append(
                            {
                                "model": model,
                                "reason": f"Insufficient capacity: {max_capacity_tph} < {required_tph} tph",
                                "data": data,
                            }
                        )
                        continue

                    capacity_margin_pct = (
                        (max_capacity_tph - required_tph) / max_capacity_tph
                    ) * 100.0

                    # Require minimum 10% margin
                    if capacity_margin_pct < 10.0:
                        rejected.append(
                            {
                                "model": model,
                                "reason": f"Insufficient margin: {capacity_margin_pct:.1f}% < 10%",
                                "data": data,
                            }
                        )
                        continue

                # Check feed size constraint
                if max_feed_in and feed_opening_in:
                    # Rule of thumb: feed should be < 80% of opening
                    if max_feed_in > float(feed_opening_in) * 0.8:
                        rejected.append(
                            {
                                "model": model,
                                "reason": f'Feed {max_feed_in}" too large for opening {feed_opening_in}"',
                                "data": data,
                            }
                        )
                        continue

                # Model is suitable!
                candidate = {
                    "equipment_type": "gyratory_crusher",
                    "manufacturer": data.get("manufacturer", "Unknown"),
                    "model": model,
                    "capacity_tph": max_capacity_tph,
                    "capacity_margin_pct": capacity_margin_pct,
                    "power_kw": power_kw,
                    "p80_range_in": [min_p80, max_p80],
                    "feed_opening_in": feed_opening_in,
                    "specifications": data,
                    "suitability_score": self._calculate_suitability_score(
                        data, target_p80_in, required_tph
                    ),
                    # Provenance
                    "sizing_source_table_id": str(sizing_table["_id"]),
                    "sizing_source_row": f"model={model}",
                }

                candidates.append(candidate)

            except (ValueError, KeyError, TypeError) as e:
                rejected.append(
                    {"model": model, "reason": f"Data parsing error: {e}", "data": data}
                )
                continue

        if not candidates:
            # Log rejections for debugging
            logger.warning(
                f"No suitable crushers found. Rejected {len(rejected)} models:"
            )
            for r in rejected[:5]:
                logger.warning(f"  - {r['model']}: {r['reason']}")

            raise EquipmentSelectionError(
                f'No crushers meet requirements (P80={target_p80_in}", '
                f"TPH={required_tph}). Checked {len(rows)} models."
            )

        # Sort by suitability score
        candidates.sort(key=lambda x: x["suitability_score"], reverse=True)

        logger.info(
            f"Found {len(candidates)} suitable crushers for "
            f'P80={target_p80_in}", TPH={required_tph}'
        )

        return candidates

    async def _select_jaw_crusher(
        self,
        project_id: str,
        parameter_changes: List[Dict[str, Any]],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Select jaw crusher models.

        Similar logic to gyratory selection but for jaw crushers.
        """
        # Implementation similar to gyratory
        # Left as exercise - same pattern
        raise NotImplementedError("Jaw crusher selection not yet implemented")

    def _calculate_suitability_score(
        self, specs: Dict[str, Any], target_p80: float, required_tph: Optional[float]
    ) -> float:
        """
        Calculate suitability score (0-100) for a model.

        Higher score = better match.

        Factors:
        - Capacity margin (prefer 15-30%)
        - Power consumption (prefer lower = more efficient)
        - P80 range precision

        Args:
            specs: Equipment specifications
            target_p80: Target product size
            required_tph: Required throughput

        Returns:
            Score from 0-100
        """
        score = 50.0  # Base score

        # Factor 1: Capacity margin
        if required_tph is not None:
            max_tph = specs.get("max_tph")
            if max_tph:
                margin_pct = ((max_tph - required_tph) / max_tph) * 100.0

                # Optimal margin: 15-30%
                if 15 <= margin_pct <= 30:
                    score += 20
                elif 10 <= margin_pct < 15:
                    score += 15
                elif 30 < margin_pct <= 50:
                    score += 10
                else:
                    # Either too tight or too oversized
                    score += 5

        # Factor 2: Power efficiency
        power_kw = specs.get("power_kW", 1000)
        if power_kw < 500:
            score += 15
        elif power_kw < 750:
            score += 10
        elif power_kw < 1000:
            score += 5

        # Factor 3: P80 range precision
        min_p80 = specs.get("min_p80_in", 0)
        max_p80 = specs.get("max_p80_in", 999)
        p80_range = max_p80 - min_p80

        # Narrower range = more specialized/precise
        if p80_range < 3:
            score += 10
        elif p80_range < 5:
            score += 5

        # Factor 4: Target P80 position in range
        if min_p80 > 0 and max_p80 < 999:
            # Prefer if target is near middle of range
            target_position = (target_p80 - min_p80) / (max_p80 - min_p80)
            if 0.4 <= target_position <= 0.6:
                score += 5

        return min(100.0, max(0.0, score))

    async def validate_equipment_has_cost_data(
        self, project_id: str, equipment_selections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate that cost data exists for equipment selections.

        This prevents generating options that can't be costed.
        Critical step that ChatGPT missed.

        Args:
            project_id: Project ID
            equipment_selections: List of equipment selections

        Returns:
            List of validated selections (only those with cost data)
        """
        # Get cost table
        cost_table = await self.table_repo.find_cost_table(
            project_id, equipment_type="gyratory_crusher"
        )

        if not cost_table:
            logger.warning("No cost table found - cannot validate cost data")
            return equipment_selections

        # Build lookup of models with cost data
        cost_rows = cost_table.get("extracted_data", {}).get("rows", [])
        models_with_cost = set()

        for row in cost_rows:
            model = row.get("model") or row.get("data", {}).get("model")
            if model:
                models_with_cost.add(model)

        # Filter selections
        validated = []
        for selection in equipment_selections:
            model = selection["model"]
            if model in models_with_cost:
                validated.append(selection)
            else:
                logger.warning(
                    f"Model {model} has sizing data but no cost data - skipping"
                )

        if not validated:
            raise EquipmentSelectionError(
                f"Equipment found in sizing table but none have cost data: "
                f"{[s['model'] for s in equipment_selections]}"
            )

        logger.info(
            f"Validated {len(validated)}/{len(equipment_selections)} "
            f"equipment selections have cost data"
        )

        return validated
