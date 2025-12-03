"""
Service layer for scenario operations.

Orchestrates scenario creation, analysis, resizing, recommendations, and reporting.
"""

from typing import Dict, Any, List, Optional
import logging
from .repository import (
    create_scenario,
    get_scenario,
    get_scenario_with_analysis,
    list_scenarios_by_project,
    update_scenario,
    update_scenario_analysis,
    update_scenario_resizing,
    update_scenario_cost_estimation,
    update_scenario_recommendation,
    update_scenario_user_constraints,
    delete_scenario,
)
from .schemas import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioOut,
    ScenarioWithAnalysis,
    UserConstraint,
    GlobalObjective,
)
from .analyzers.entity_analyzer import EntityAnalyzer
from .analyzers.cost_preparator import CostPreparator
from .analyzers.recommendation_builder import RecommendationBuilder
from .resizers.system_resizer import SystemResizer
from .reporters.scenario_reporter import ScenarioReporter

logger = logging.getLogger(__name__)


class ScenarioService:
    """Service for scenario operations."""
    
    def __init__(self):
        """Initialize service with analyzers and resizers."""
        self.entity_analyzer = EntityAnalyzer()
        self.system_resizer = SystemResizer()
        self.cost_preparator = CostPreparator()
        self.recommendation_builder = RecommendationBuilder()
        self.reporter = ScenarioReporter()
    
    async def create_scenario(self, data: ScenarioCreate) -> ScenarioOut:
        """Create a new scenario."""
        logger.info(f"Creating scenario: {data.name}")
        return await create_scenario(data)
    
    async def get_scenario(self, scenario_id: str) -> Optional[ScenarioOut]:
        """Get a scenario by ID."""
        return await get_scenario(scenario_id)
    
    async def get_scenario_with_analysis(self, scenario_id: str) -> Optional[ScenarioWithAnalysis]:
        """Get a scenario with all analysis data."""
        return await get_scenario_with_analysis(scenario_id)
    
    async def list_scenarios(self, project_id: str) -> List[ScenarioOut]:
        """List all scenarios for a project."""
        return await list_scenarios_by_project(project_id)
    
    async def update_scenario(self, scenario_id: str, data: ScenarioUpdate) -> Optional[ScenarioOut]:
        """Update a scenario."""
        logger.info(f"Updating scenario {scenario_id}")
        return await update_scenario(scenario_id, data)
    
    async def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario."""
        logger.info(f"Deleting scenario {scenario_id}")
        return await delete_scenario(scenario_id)
    
    async def analyze_scenario(self, scenario_id: str) -> Optional[ScenarioWithAnalysis]:
        """
        Run LLM analysis of relevant entities for a scenario.
        
        Updates scenario with analysis results.
        """
        logger.info(f"Analyzing scenario {scenario_id}")
        
        # Get scenario
        scenario = await get_scenario(scenario_id)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found")
            return None
        
        # Update status to analyzing
        await update_scenario(scenario_id, ScenarioUpdate(status="analyzing", compute_state="running"))
        
        try:
            # Get global objective
            if not scenario.global_objective:
                logger.error(f"Scenario {scenario_id} has no global objective")
                await update_scenario(scenario_id, ScenarioUpdate(status="draft", compute_state="failed"))
                return None
            
            global_objective_dict = scenario.global_objective.model_dump() if hasattr(scenario.global_objective, 'model_dump') else scenario.global_objective
            
            # Run entity analysis
            analysis = await self.entity_analyzer.analyze(
                project_id=scenario.project_id,
                global_objective=global_objective_dict,
            )
            
            # Update scenario with analysis
            await update_scenario_analysis(scenario_id, analysis)
            
            # Update status
            await update_scenario(scenario_id, ScenarioUpdate(status="ready", compute_state="succeeded"))
            
            # Return updated scenario
            return await get_scenario_with_analysis(scenario_id)
            
        except Exception as e:
            logger.error(f"Error analyzing scenario {scenario_id}: {e}", exc_info=True)
            await update_scenario(scenario_id, ScenarioUpdate(status="draft", compute_state="failed"))
            return None
    
    async def resize_system(
        self, scenario_id: str, user_constraints: List[UserConstraint] = None
    ) -> Optional[ScenarioWithAnalysis]:
        """
        Apply system resizing based on global objective and user constraints.
        
        Updates scenario with resizing results.
        """
        logger.info(f"Resizing system for scenario {scenario_id}")
        
        # Get scenario with analysis
        scenario = await get_scenario_with_analysis(scenario_id)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found")
            return None
        
        if not scenario.analysis:
            logger.error(f"Scenario {scenario_id} has no analysis - run analyze first")
            return None
        
        try:
            # Get global objective
            global_objective_dict = scenario.global_objective.model_dump() if hasattr(scenario.global_objective, 'model_dump') else scenario.global_objective
            
            # Run resizing
            resizing = self.system_resizer.resize(
                project_id=scenario.project_id,
                global_objective=global_objective_dict,
                analysis=scenario.analysis,
                user_constraints=user_constraints or scenario.user_constraints,
            )
            
            # Update scenario with resizing
            await update_scenario_resizing(scenario_id, resizing)
            
            # Update user constraints if provided
            if user_constraints:
                await update_scenario_user_constraints(scenario_id, user_constraints)
            
            # Return updated scenario
            return await get_scenario_with_analysis(scenario_id)
            
        except Exception as e:
            logger.error(f"Error resizing system for scenario {scenario_id}: {e}", exc_info=True)
            return None
    
    async def build_recommendation(self, scenario_id: str) -> Optional[ScenarioWithAnalysis]:
        """
        Build system recommendations with approach options.
        
        Updates scenario with recommendation results.
        """
        logger.info(f"Building recommendation for scenario {scenario_id}")
        
        # Get scenario with analysis and resizing
        scenario = await get_scenario_with_analysis(scenario_id)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found")
            return None
        
        if not scenario.analysis:
            logger.error(f"Scenario {scenario_id} has no analysis - run analyze first")
            return None
        
        try:
            # Get global objective
            global_objective_dict = scenario.global_objective.model_dump() if hasattr(scenario.global_objective, 'model_dump') else scenario.global_objective
            
            # Build recommendation
            recommendation = self.recommendation_builder.build(
                global_objective=global_objective_dict,
                analysis=scenario.analysis,
                resizing=scenario.resizing,
                user_constraints=scenario.user_constraints,
            )
            
            # Update scenario with recommendation
            await update_scenario_recommendation(scenario_id, recommendation)
            
            # Return updated scenario
            return await get_scenario_with_analysis(scenario_id)
            
        except Exception as e:
            logger.error(f"Error building recommendation for scenario {scenario_id}: {e}", exc_info=True)
            return None
    
    async def prepare_cost_estimation(
        self, scenario_id: str, generate_estimates: bool = False
    ) -> Optional[ScenarioWithAnalysis]:
        """
        Prepare cost estimation data.
        
        Optionally generates cost estimates if generate_estimates=True.
        Updates scenario with cost estimation data.
        """
        logger.info(f"Preparing cost estimation for scenario {scenario_id}, generate={generate_estimates}")
        
        # Get scenario with analysis and resizing
        scenario = await get_scenario_with_analysis(scenario_id)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found")
            return None
        
        if not scenario.analysis:
            logger.error(f"Scenario {scenario_id} has no analysis - run analyze first")
            return None
        
        try:
            # Prepare cost estimation
            cost_estimation = await self.cost_preparator.prepare(
                project_id=scenario.project_id,
                analysis=scenario.analysis,
                resizing=scenario.resizing,
                generate_estimates=generate_estimates,
            )
            
            # Update scenario with cost estimation
            await update_scenario_cost_estimation(scenario_id, cost_estimation)
            
            # Return updated scenario
            return await get_scenario_with_analysis(scenario_id)
            
        except Exception as e:
            logger.error(f"Error preparing cost estimation for scenario {scenario_id}: {e}", exc_info=True)
            return None
    
    async def generate_report(
        self, scenario_id: str, format: str = "json"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a formatted report for a scenario.
        
        Args:
            scenario_id: Scenario identifier
            format: Report format ("json" or "markdown")
        
        Returns:
            Report data as dictionary
        """
        logger.info(f"Generating {format} report for scenario {scenario_id}")
        
        # Get scenario with all data
        scenario = await get_scenario_with_analysis(scenario_id)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found")
            return None
        
        try:
            # Generate report
            report = self.reporter.generate_report(scenario, format=format)
            
            # Return report data
            return report.model_dump()
            
        except Exception as e:
            logger.error(f"Error generating report for scenario {scenario_id}: {e}", exc_info=True)
            return None

