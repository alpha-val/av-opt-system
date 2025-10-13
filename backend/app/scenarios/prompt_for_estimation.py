import json
from typing import List, Dict, Any


def _build_cost_estimation_prompt(
    scenario_description: str,
    base_case_entities: List[Dict[str, Any]],
    tabular_entities: List[Dict[str, Any]],
) -> str:
    """
    Build the prompt for LLM-based cost estimation.

    Args:
        scenario_description: User's scenario description and goals
        base_case_entities: Entities from base case documents
        tabular_entities: Entities from tabular data (equipment catalogs, price lists)

    Returns:
        Formatted prompt string
    """
    # Format base case entities
    base_case_json = (
        json.dumps(base_case_entities[:50], indent=2)
        if len(base_case_entities) > 50
        else json.dumps(base_case_entities, indent=2)
    )
    base_case_truncation = (
        f"... (showing first 50 of {len(base_case_entities)} entities)"
        if len(base_case_entities) > 50
        else ""
    )

    # Format tabular entities
    tabular_json = (
        json.dumps(tabular_entities[:50], indent=2)
        if len(tabular_entities) > 50
        else json.dumps(tabular_entities, indent=2)
    )
    tabular_truncation = (
        f"... (showing first 50 of {len(tabular_entities)} entities)"
        if len(tabular_entities) > 50
        else ""
    )

    prompt = f"""# COST ESTIMATION TASK

You are a cost estimation expert for mining and processing equipment. Your task is to analyze a proposed scenario and estimate the cost difference compared to the current base case configuration.

## Scenario Information
{scenario_description}

## Available Data

### Base Case Entities
These represent the current configuration. Total entities: {len(base_case_entities)}

```json
{base_case_json}
```
{"... (showing first 50 of " + str(len(base_case_entities)) + " entities)" if len(base_case_entities) > 50 else ""}

### Tabular Entities
These represent available equipment and pricing data. Total entities: {len(tabular_entities)}

```json
{tabular_json}
```
{"... (showing first 50 of " + str(len(tabular_entities)) + " entities)" if len(tabular_entities) > 50 else ""}

Your Task
Step 1: Understand the Scenario
Parse the scenario goal, description, and change type
Identify what equipment/processes are affected
Determine if this is an addition, replacement, removal, or modification
Step 2: Map Relevant Entities
From base_case_entities: Identify equipment/entities that are relevant to this scenario
From tabular_entities: Find equipment options that match the scenario requirements
Match base case equipment to their tabular equivalents or upgrades
Step 3: Extract Cost Information
For each relevant entity, extract:

Purchase/capital costs
Installation costs
Operating costs (annual)
Maintenance costs
Any other cost properties present in the data
If cost information is missing, use 0 and note this in assumptions.

Step 4: Calculate Cost Difference
Base Case Total: Sum all costs for current relevant equipment
Proposed Total: Sum all costs for proposed equipment configuration
Delta: proposed_total - base_case_total (positive = cost increase, negative = savings)
Step 5: Provide Detailed Breakdown
Break down costs by:

Equipment type/category
Cost category (capital, installation, operating, maintenance)
Individual equipment items
Required Output Format
Return a JSON object with the following structure:
```json
{{
  "relevant_entities": {{
    "base_case": [
      {{
        "entity_id": "string",
        "name": "string",
        "type": "string",
        "costs": {{
          "capital_cost": 0,
          "installation_cost": 0,
          "operating_cost_annual": 0,
          "maintenance_cost_annual": 0,
          "total": 0
        }},
        "reason_for_relevance": "string"
      }}
    ],
    "proposed": [
      {{
        "entity_id": "string",
        "name": "string",
        "type": "string",
        "source": "tabular_data or base_case_modified",
        "costs": {{
          "capital_cost": 0,
          "installation_cost": 0,
          "operating_cost_annual": 0,
          "maintenance_cost_annual": 0,
          "total": 0
        }},
        "reason_for_inclusion": "string"
      }}
    ]
  }},
  "cost_breakdown": {{
    "base_case_total": {{
      "capital": 0,
      "installation": 0,
      "operating_annual": 0,
      "maintenance_annual": 0,
      "total": 0
    }},
    "proposed_total": {{
      "capital": 0,
      "installation": 0,
      "operating_annual": 0,
      "maintenance_annual": 0,
      "total": 0
    }},
    "delta": {{
      "capital": 0,
      "installation": 0,
      "operating_annual": 0,
      "maintenance_annual": 0,
      "total": 0
    }},
    "by_category": {{
      "equipment_type_1": {{
        "base_case": 0,
        "proposed": 0,
        "delta": 0
      }}
    }}
  }},
  "assumptions": [
    "List any assumptions made during estimation",
    "Note any missing cost data",
    "Explain any significant decisions"
  ],
  "confidence": "high|medium|low",
  "confidence_explanation": "Explanation of confidence level based on data completeness and quality",
  "notes": "Any additional notes, warnings, or recommendations"
}}
```

Important Guidelines
Only include relevant entities: Don't list all entities, only those affected by the scenario
Be explicit about matching: When matching base case to tabular equipment, explain the match
Handle missing data gracefully: Use 0 for missing costs and document in assumptions
Consider the change type:
Equipment: Focus on equipment replacement/addition costs
Process: Consider process modification and associated equipment
Capacity: Scale equipment based on capacity requirements
Location: Include relocation and installation costs
Technology: Consider technology upgrade paths and compatibility
Annual vs. one-time costs: Clearly distinguish between capital/installation (one-time) and operating/maintenance (annual)
Confidence scoring:
High: Complete cost data available, clear equipment matches
Medium: Some cost data missing or estimates required
Low: Significant gaps in data or unclear requirements
Delta interpretation: Positive delta means the scenario will cost MORE than base case
Example Scenario Handling
If scenario goal is "Increase Production":

Look for equipment with higher capacity/throughput
Calculate additional equipment needs
Include scaling factors for supporting equipment
If scenario goal is "Reduce Cost":

Look for more efficient equipment alternatives
Consider operating cost reductions
Evaluate maintenance cost improvements
If change type is "Equipment":

Focus on direct equipment costs
Include installation and commissioning
Consider equipment removal costs if replacing
Return ONLY the JSON object, no additional text.
"""
    return prompt