"""Parts catalog — all car components with specs, costs, and interactions.

Players select one component from each category. Components combine into
8 derived performance attributes via car_attributes.py.
"""

BUDGET_CAP = 140  # $M total

CATALOG = {
    "ENGINE": {
        "pu_balanced": {
            "name": "V6 Balanced", "hp": 960, "reliability": 0.98,
            "fuel_kg_per_lap": 1.85, "cost_m": 15,
        },
        "pu_high_output": {
            "name": "V6 High Output", "hp": 1000, "reliability": 0.95,
            "fuel_kg_per_lap": 2.10, "cost_m": 22,
        },
        "pu_efficient": {
            "name": "V6 Efficient", "hp": 930, "reliability": 0.99,
            "fuel_kg_per_lap": 1.60, "cost_m": 18,
        },
        "pu_aggressive": {
            "name": "V6 Aggressive", "hp": 1020, "reliability": 0.92,
            "fuel_kg_per_lap": 2.25, "cost_m": 35,
        },
    },
    "AERO": {
        "aero_low_drag": {
            "name": "Low Drag", "downforce_coeff": 0.70, "drag_coeff": 0.75, "cost_m": 20,
        },
        "aero_balanced": {
            "name": "Balanced", "downforce_coeff": 0.85, "drag_coeff": 0.88, "cost_m": 22,
        },
        "aero_high_df": {
            "name": "High Downforce", "downforce_coeff": 1.00, "drag_coeff": 1.00, "cost_m": 25,
        },
        "aero_ground_effect": {
            "name": "Ground Effect Focus", "downforce_coeff": 0.95, "drag_coeff": 0.82, "cost_m": 35,
        },
    },
    "FRONT_WING": {
        "fw_standard": {"name": "Standard", "front_df_pct": 100, "fragility": 1.0, "cost_m": 5},
        "fw_aggressive": {"name": "Aggressive", "front_df_pct": 112, "fragility": 1.5, "cost_m": 8},
        "fw_sturdy": {"name": "Sturdy", "front_df_pct": 95, "fragility": 0.5, "cost_m": 4},
    },
    "REAR_WING": {
        "rw_standard": {"name": "Standard", "rear_df_pct": 100, "drs_effect": 1.0, "cost_m": 5},
        "rw_drs_optimized": {"name": "DRS Optimized", "rear_df_pct": 95, "drs_effect": 1.4, "cost_m": 7},
        "rw_maximum": {"name": "Maximum Load", "rear_df_pct": 115, "drs_effect": 0.8, "cost_m": 6},
    },
    "SUSPENSION": {
        "sus_soft": {
            "name": "Soft", "mech_grip_mult": 1.15, "aero_stability_mult": 0.90,
            "tire_wear_mult": 0.95, "cost_m": 8,
        },
        "sus_medium": {
            "name": "Medium", "mech_grip_mult": 1.00, "aero_stability_mult": 1.00,
            "tire_wear_mult": 1.00, "cost_m": 6,
        },
        "sus_stiff": {
            "name": "Stiff", "mech_grip_mult": 0.90, "aero_stability_mult": 1.15,
            "tire_wear_mult": 1.05, "cost_m": 10,
        },
    },
    "BRAKES": {
        "brk_standard": {"name": "Standard Carbon", "brake_g": 5.0, "temp_window": 1.0, "cost_m": 5},
        "brk_aggressive": {"name": "Aggressive Carbon", "brake_g": 5.5, "temp_window": 0.7, "cost_m": 8},
        "brk_endurance": {"name": "Endurance", "brake_g": 4.8, "temp_window": 1.3, "cost_m": 4},
    },
    "WEIGHT": {
        "wt_standard": {"name": "Standard", "weight_kg": 798, "cost_m": 0},
        "wt_stage1": {"name": "Stage 1", "weight_kg": 790, "cost_m": 8},
        "wt_stage2": {"name": "Stage 2", "weight_kg": 783, "cost_m": 15},
        "wt_extreme": {"name": "Extreme", "weight_kg": 778, "cost_m": 30},
    },
    "COOLING": {
        "cool_standard": {"name": "Standard", "cooling_eff": 1.0, "drag_penalty": 0.0, "cost_m": 3},
        "cool_aggressive": {"name": "Aggressive", "cooling_eff": 0.8, "drag_penalty": -0.02, "cost_m": 5},
        "cool_conservative": {"name": "Conservative", "cooling_eff": 1.3, "drag_penalty": 0.03, "cost_m": 4},
    },
    "GEARBOX": {
        "gbx_standard": {"name": "Standard 8-speed", "top_speed_mod": 0, "accel_mod": 0, "cost_m": 5},
        "gbx_short": {"name": "Short Ratios", "top_speed_mod": -5, "accel_mod": 8, "cost_m": 6},
        "gbx_tall": {"name": "Tall Ratios", "top_speed_mod": 8, "accel_mod": -3, "cost_m": 6},
    },
}

DEFAULTS = {
    "ENGINE": "pu_balanced", "AERO": "aero_balanced", "FRONT_WING": "fw_standard",
    "REAR_WING": "rw_standard", "SUSPENSION": "sus_medium", "BRAKES": "brk_standard",
    "WEIGHT": "wt_standard", "COOLING": "cool_standard", "GEARBOX": "gbx_standard",
}


def get_component(category: str, component_id: str) -> dict | None:
    """Return component dict or None if not found."""
    return CATALOG.get(category, {}).get(component_id)


def get_defaults() -> dict:
    """Return default component selections."""
    return dict(DEFAULTS)


def list_components(category: str) -> list[str]:
    """Return list of component IDs for a category."""
    return list(CATALOG.get(category, {}).keys())


def list_categories() -> list[str]:
    """Return all component categories."""
    return list(CATALOG.keys())


def get_total_cost(selections: dict) -> float:
    """Compute total cost of a component build in $M."""
    total = 0.0
    for cat, comp_id in selections.items():
        comp = get_component(cat, comp_id)
        if comp:
            total += comp.get("cost_m", 0)
    return total


def validate_build(selections: dict) -> tuple[bool, str]:
    """Validate a component build. Returns (valid, message)."""
    for cat in CATALOG:
        if cat not in selections:
            return False, f"Missing component category: {cat}"
        comp = get_component(cat, selections[cat])
        if comp is None:
            return False, f"Unknown component '{selections[cat]}' in {cat}"
    cost = get_total_cost(selections)
    if cost > BUDGET_CAP:
        return False, f"Over budget: ${cost:.1f}M > ${BUDGET_CAP}M cap"
    return True, f"Valid build: ${cost:.1f}M / ${BUDGET_CAP}M"


def validate_budget(selections: dict) -> tuple[bool, float]:
    """Check if total cost is within BUDGET_CAP."""
    cost = get_total_cost(selections)
    return cost <= BUDGET_CAP, cost
