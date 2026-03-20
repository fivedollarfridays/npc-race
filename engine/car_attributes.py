"""Derived attributes calculator — components → 8 performance numbers.

Takes a component selection dict and computes the attributes that the
physics engine uses: top speed, cornering grip, braking, tire wear, etc.
"""

from .parts_catalog import get_component


def compute_attributes(selections: dict) -> dict:
    """Compute derived performance attributes from component selections."""
    eng = get_component("ENGINE", selections.get("ENGINE", "pu_balanced")) or {}
    aero = get_component("AERO", selections.get("AERO", "aero_balanced")) or {}
    fw = get_component("FRONT_WING", selections.get("FRONT_WING", "fw_standard")) or {}
    rw = get_component("REAR_WING", selections.get("REAR_WING", "rw_standard")) or {}
    sus = get_component("SUSPENSION", selections.get("SUSPENSION", "sus_medium")) or {}
    brk = get_component("BRAKES", selections.get("BRAKES", "brk_standard")) or {}
    wt = get_component("WEIGHT", selections.get("WEIGHT", "wt_standard")) or {}
    cool = get_component("COOLING", selections.get("COOLING", "cool_standard")) or {}
    gbx = get_component("GEARBOX", selections.get("GEARBOX", "gbx_standard")) or {}

    hp = eng.get("hp", 960)
    weight_kg = wt.get("weight_kg", 798)
    drag = aero.get("drag_coeff", 0.88)
    df = aero.get("downforce_coeff", 0.85)
    cool_drag = cool.get("drag_penalty", 0.0)

    # Top speed: base + engine HP + gearbox - drag - weight - cooling drag
    top_speed = (330
                 + (hp - 960) * 0.25
                 + gbx.get("top_speed_mod", 0)
                 - (drag - 0.85) * 80
                 - (weight_kg - 798) * 0.2
                 - cool_drag * 200)
    top_speed = max(315, min(355, top_speed))

    # Low-speed grip (mechanical cornering — hairpins, chicanes)
    low_speed_grip = (1.0
                      * sus.get("mech_grip_mult", 1.0)
                      * (fw.get("front_df_pct", 100) / 100)
                      * (798 / max(weight_kg, 700)))

    # High-speed grip (aero cornering — fast sweepers)
    high_speed_grip = (1.0
                       * df
                       * sus.get("aero_stability_mult", 1.0)
                       * (rw.get("rear_df_pct", 100) / 100))

    # Braking performance (G-force)
    braking_g = brk.get("brake_g", 5.0) * (fw.get("front_df_pct", 100) / 100)

    # Tire wear multiplier (lower = less wear)
    tire_wear_mult = (sus.get("tire_wear_mult", 1.0)
                      * (1.0 + (weight_kg - 798) * 0.003)
                      * (1.0 + max(0, df - 0.9) * 0.1))

    return {
        "top_speed_kmh": round(top_speed, 1),
        "low_speed_grip": round(low_speed_grip, 3),
        "high_speed_grip": round(high_speed_grip, 3),
        "braking_g": round(braking_g, 2),
        "tire_wear_mult": round(tire_wear_mult, 3),
        "fuel_kg_per_lap": eng.get("fuel_kg_per_lap", 1.85),
        "reliability": eng.get("reliability", 0.98),
        "cooling_efficiency": cool.get("cooling_eff", 1.0),
        "weight_kg": weight_kg,
        "drs_effect": rw.get("drs_effect", 1.0),
        "fragility": fw.get("fragility", 1.0),
        "brake_temp_window": brk.get("temp_window", 1.0),
        "accel_mod": gbx.get("accel_mod", 0),
    }
