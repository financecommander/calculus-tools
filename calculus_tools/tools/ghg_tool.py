"""GHG / Climate Tool — CrewAI BaseTool wrapper.

Delegates to ``calculus_tools.ghg`` for all analysis logic.
No external API key required.
"""

from __future__ import annotations

import json as _json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from calculus_tools.ghg import (
    model_carbon_cycle,
    assess_planetary_boundaries,
    model_warming_mitigation,
    generate_domain_data,
)


class GHGAnalysisInput(BaseModel):
    action: str = Field(
        ...,
        description=(
            "Action to perform. One of: "
            "'carbon_cycle'  — model carbon fluxes & sequestration; "
            "'planetary_boundaries' — assess a domain's boundary status; "
            "'mitigation' — model warming-mitigation scenario; "
            "'generate_data' — produce synthetic climate data."
        ),
    )
    domain: str = Field(
        "atmospheric",
        description="Climate domain (atmospheric, oceanic, terrestrial, cryospheric, biospheric, anthropogenic).",
    )
    time_period: str = Field("2025", description="Time period label (e.g. '2025', '2020-2030').")
    scenario: str = Field(
        "net_zero_2050",
        description="Mitigation scenario (business_as_usual, moderate_action, net_zero_2050, aggressive_drawdown).",
    )
    months: int = Field(12, ge=1, le=120, description="Months of synthetic data to generate.")


class GHGTool(BaseTool):
    """Greenhouse-gas and climate intelligence tool."""

    name: str = "ghg_climate"
    description: str = (
        "Analyse greenhouse-gas emissions, model the carbon cycle, assess "
        "planetary boundaries, and run warming-mitigation scenarios. "
        "Action must be one of: carbon_cycle, planetary_boundaries, "
        "mitigation, generate_data."
    )
    args_schema: type = GHGAnalysisInput

    def _run(
        self,
        action: str,
        domain: str = "atmospheric",
        time_period: str = "2025",
        scenario: str = "net_zero_2050",
        months: int = 12,
    ) -> str:
        if action == "carbon_cycle":
            result = model_carbon_cycle(time_period)
            return _json.dumps({
                "cycle_id": result.cycle_id,
                "time_period": result.time_period,
                "carbon_fluxes": result.carbon_fluxes,
                "insights": result.consciousness_insights,
                "sequestration_potential": result.sequestration_potential,
                "emission_trends": result.emission_trends,
                "mitigation_strategies": result.mitigation_strategies,
            }, indent=2)

        if action == "planetary_boundaries":
            return _json.dumps(assess_planetary_boundaries(domain), indent=2)

        if action == "mitigation":
            return _json.dumps(model_warming_mitigation(scenario), indent=2)

        if action == "generate_data":
            data = generate_domain_data(domain, months=months)
            return _json.dumps(data, indent=2, default=str)

        return f"Unknown action '{action}'. Use: carbon_cycle, planetary_boundaries, mitigation, generate_data."
