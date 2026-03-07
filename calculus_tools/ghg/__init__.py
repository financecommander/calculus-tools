"""GHG / Climate intelligence — core analysis logic.

No CrewAI dependency.  Importable as::

    from calculus_tools.ghg import (
        model_carbon_cycle,
        assess_planetary_boundaries,
        model_warming_mitigation,
        generate_domain_data,
        CarbonCycleIntelligence,
        ClimateDomain,
        ClimateTimeframe,
        PLANETARY_BOUNDARIES,
    )
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ======================================================================
# Domain enums
# ======================================================================

class ClimateDomain(str, Enum):
    ATMOSPHERIC = "atmospheric"
    OCEANIC = "oceanic"
    TERRESTRIAL = "terrestrial"
    CRYOSPHERIC = "cryospheric"
    BIOSPHERIC = "biospheric"
    ANTHROPOGENIC = "anthropogenic"


class ClimateTimeframe(str, Enum):
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"
    CENTURY_SCALE = "century_scale"


class ExtremeEvent(str, Enum):
    HEATWAVE = "heatwave"
    DROUGHT = "drought"
    FLOOD = "flood"
    HURRICANE = "hurricane"
    WILDFIRE = "wildfire"
    SEA_LEVEL_RISE = "sea_level_rise"
    CORAL_BLEACHING = "coral_bleaching"


class ConsciousnessClimateLevel(float, Enum):
    SCIENTIFIC = 0.1
    SYSTEMS_THINKING = 0.3
    ECOLOGICAL = 0.6
    PLANETARY = 0.8
    COSMIC = 1.0


# ======================================================================
# Data classes
# ======================================================================

@dataclass
class CarbonCycleIntelligence:
    """Intelligence analysis of the carbon cycle."""
    cycle_id: str
    time_period: str
    carbon_fluxes: Dict[str, float]
    consciousness_insights: List[str]
    sequestration_potential: float
    emission_trends: Dict[str, Any]
    mitigation_strategies: List[str]
    analyzed_at: datetime


@dataclass
class ClimateDataPoint:
    timestamp: datetime
    location: Tuple[float, float]
    domain: ClimateDomain
    variable: str
    value: float
    uncertainty: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClimatePattern:
    pattern_id: str
    domain: ClimateDomain
    pattern_type: str
    description: str
    confidence: float
    time_range: Tuple[datetime, datetime]
    spatial_extent: Dict[str, Any]
    consciousness_insights: List[Dict[str, Any]]
    predicted_impact: Dict[str, Any]
    mitigation_suggestions: List[str]


# ======================================================================
# Planetary boundaries reference
# ======================================================================

PLANETARY_BOUNDARIES: Dict[str, Dict[str, Any]] = {
    "climate_change": {"current": 1.1, "boundary": 1.0, "unit": "°C warming"},
    "biodiversity_loss": {"current": 227, "boundary": 10, "unit": "extinction rate"},
    "land_system_change": {"current": 72, "boundary": 75, "unit": "% transformed"},
    "biogeochemical_flows": {"current": 1.7, "boundary": 1.0, "unit": "N flow ratio"},
    "ocean_acidification": {"current": 2.8, "boundary": 2.75, "unit": "pH"},
    "ozone_depletion": {"current": 0.0, "boundary": 5, "unit": "DU"},
    "atmospheric_aerosols": {"current": 0.6, "boundary": 0.5, "unit": "W/m²"},
    "freshwater_change": {"current": 0.8, "boundary": 0.4, "unit": "km³/year"},
}

_DOMAIN_BOUNDARIES: Dict[str, List[str]] = {
    "atmospheric": ["climate_change", "atmospheric_aerosols", "ozone_depletion"],
    "oceanic": ["ocean_acidification", "biogeochemical_flows"],
    "cryospheric": ["climate_change", "freshwater_change"],
    "terrestrial": ["land_system_change", "biodiversity_loss"],
    "biospheric": ["biodiversity_loss", "biogeochemical_flows"],
    "anthropogenic": ["climate_change", "land_system_change", "biogeochemical_flows"],
}


# ======================================================================
# Carbon-cycle modelling
# ======================================================================

def model_carbon_cycle(
    time_period: str,
    carbon_data: Optional[Dict[str, Any]] = None,
) -> CarbonCycleIntelligence:
    """Model carbon cycle intelligence for a given time period."""
    carbon_data = carbon_data or {}
    cycle_id = f"carbon_{time_period}_{uuid.uuid4().hex[:8]}"

    fluxes = carbon_data.get("fluxes", {
        "fossil_fuel_emissions": 36.8,
        "land_use_change": 3.9,
        "ocean_sink": -10.5,
        "land_sink": -12.4,
        "atmospheric_growth": 17.8,
    })

    total_emission = fluxes.get("fossil_fuel_emissions", 0) + fluxes.get("land_use_change", 0)
    total_sink = abs(fluxes.get("ocean_sink", 0)) + abs(fluxes.get("land_sink", 0))
    sequestration_potential = total_sink / total_emission if total_emission else 0

    insights = [
        f"Total anthropogenic emission: {total_emission:.1f} GtCO2/yr",
        f"Natural sinks absorb {total_sink:.1f} GtCO2/yr ({sequestration_potential*100:.0f}% of emissions)",
        f"Atmospheric accumulation: {fluxes.get('atmospheric_growth', 0):.1f} GtCO2/yr",
    ]
    if sequestration_potential < 0.5:
        insights.append("CRITICAL: Sinks absorb less than half of emissions — accelerating accumulation.")

    mitigation = [
        "Accelerate renewable energy transition to cut fossil-fuel emissions",
        "Halt deforestation and restore degraded forests (land-use change reduction)",
        "Invest in direct-air-capture and enhanced weathering technologies",
        "Scale regenerative agriculture for soil carbon sequestration",
    ]

    emission_trends = carbon_data.get("emission_trends", {
        "direction": "increasing",
        "rate_gtco2_per_year": 0.5,
        "peak_year_estimate": 2030,
    })

    return CarbonCycleIntelligence(
        cycle_id=cycle_id,
        time_period=time_period,
        carbon_fluxes=fluxes,
        consciousness_insights=insights,
        sequestration_potential=sequestration_potential,
        emission_trends=emission_trends,
        mitigation_strategies=mitigation,
        analyzed_at=datetime.utcnow(),
    )


# ======================================================================
# Planetary boundary assessment
# ======================================================================

def assess_planetary_boundaries(domain: str) -> Dict[str, Any]:
    """Assess planetary boundaries relevant to a climate domain."""
    relevant = _DOMAIN_BOUNDARIES.get(domain, [])
    assessment: Dict[str, Any] = {
        "domain": domain,
        "boundaries": {},
        "critical": [],
        "overall_status": "safe",
        "recommendations": [],
    }

    for name in relevant:
        if name not in PLANETARY_BOUNDARIES:
            continue
        b = PLANETARY_BOUNDARIES[name]
        status = "safe" if b["current"] <= b["boundary"] else "exceeded"
        assessment["boundaries"][name] = {
            "current": b["current"],
            "boundary": b["boundary"],
            "unit": b["unit"],
            "status": status,
        }
        if status == "exceeded":
            assessment["critical"].append(name)

    if assessment["critical"]:
        assessment["overall_status"] = (
            "critical" if len(assessment["critical"]) > 2 else "warning"
        )
        assessment["recommendations"] = [
            "Immediate action required on exceeded boundaries",
            "Implement rapid decarbonisation strategies",
            "Enhance ecosystem restoration efforts",
        ]

    return assessment


# ======================================================================
# Climate data generation (synthetic)
# ======================================================================

def generate_domain_data(
    domain: str,
    months: int = 12,
    start: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Generate synthetic monthly climate data points for *domain*."""
    start = start or datetime.utcnow() - timedelta(days=30 * months)
    points: List[Dict[str, Any]] = []
    generators: Dict[str, list] = {
        "atmospheric": [
            ("temperature", 15.0, 0.008),
            ("co2_ppm", 420.0, 0.21),
        ],
        "oceanic": [
            ("sea_level_mm", 50.0, 0.27),
            ("ocean_ph", 8.1, -0.00012),
        ],
        "cryospheric": [
            ("arctic_ice_extent_mkm2", 12000, -4.1),
        ],
        "terrestrial": [
            ("soil_moisture_percent", 25.0, -0.004),
            ("vegetation_index", 0.6, -0.00008),
        ],
    }

    for var, base, slope in generators.get(domain, generators["atmospheric"]):
        for m in range(months):
            ts = start + timedelta(days=30 * m)
            points.append({
                "timestamp": ts.isoformat(),
                "variable": var,
                "value": round(base + slope * 30 * m, 4),
                "uncertainty": round(abs(slope) * 30 * 3, 4),
                "domain": domain,
            })

    return points


# ======================================================================
# Global-warming mitigation modelling
# ======================================================================

def model_warming_mitigation(
    scenario: str = "net_zero_2050",
    time_horizon_years: int = 25,
) -> Dict[str, Any]:
    """Model global-warming mitigation for a named scenario."""
    scenarios = {
        "business_as_usual": {
            "annual_reduction_pct": 0,
            "peak_warming_c": 3.2,
            "success_probability": 0.05,
        },
        "moderate_action": {
            "annual_reduction_pct": 2.0,
            "peak_warming_c": 2.4,
            "success_probability": 0.30,
        },
        "net_zero_2050": {
            "annual_reduction_pct": 7.6,
            "peak_warming_c": 1.5,
            "success_probability": 0.55,
        },
        "aggressive_drawdown": {
            "annual_reduction_pct": 10.0,
            "peak_warming_c": 1.2,
            "success_probability": 0.40,
        },
    }

    params = scenarios.get(scenario, scenarios["net_zero_2050"])

    strategies = [
        "Rapid renewable energy deployment",
        "Electrification of transport and industry",
        "Nature-based carbon removal at scale",
        "Methane and short-lived pollutant reduction",
    ]
    if params["annual_reduction_pct"] >= 7:
        strategies.append("Direct-air-capture industrial build-out")
        strategies.append("Global carbon pricing / border adjustment")

    return {
        "scenario": scenario,
        "time_horizon_years": time_horizon_years,
        "annual_emission_reduction_pct": params["annual_reduction_pct"],
        "projected_peak_warming_c": params["peak_warming_c"],
        "success_probability": params["success_probability"],
        "mitigation_strategies": strategies,
        "challenges": [
            "Political will and policy consistency",
            "Financing the transition in developing nations",
            "Technology readiness for hard-to-abate sectors",
        ],
    }


__all__ = [
    # Enums
    "ClimateDomain",
    "ClimateTimeframe",
    "ExtremeEvent",
    "ConsciousnessClimateLevel",
    # Dataclasses
    "CarbonCycleIntelligence",
    "ClimateDataPoint",
    "ClimatePattern",
    # Constants
    "PLANETARY_BOUNDARIES",
    # Functions
    "model_carbon_cycle",
    "assess_planetary_boundaries",
    "generate_domain_data",
    "model_warming_mitigation",
]
