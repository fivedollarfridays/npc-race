"""Coaching tips from time trial efficiency data."""

from __future__ import annotations

from engine.time_trial import TrialResult


def generate_coaching(result: TrialResult) -> list[str]:
    """Generate actionable tips from trial result efficiency data."""
    tips: list[str] = []
    eff = result.efficiency

    # Gearbox
    gb = eff.get("gearbox", 1.0)
    if gb < 0.95:
        tips.append(
            f"Gearbox efficiency: {gb:.0%} — "
            f"peak torque is 10,800-12,500 RPM. "
            f"Try shifting at 11,000 RPM."
        )

    # Cooling
    cool = eff.get("cooling", 1.0)
    if cool < 0.90:
        tips.append(
            f"Cooling efficiency: {cool:.0%} — "
            f"high cooling effort adds drag. "
            f"Try values around 0.2-0.4."
        )

    # Fuel mix
    fuel = eff.get("fuel_mix", 1.0)
    if fuel < 0.90:
        tips.append(
            f"Fuel mix efficiency: {fuel:.0%} — "
            f"target lambda around 1.0 for optimal burn."
        )

    # Overall product
    product = gb * cool * fuel
    if product < 0.85:
        loss_pct = round((1 - product) * 100)
        tips.append(
            f"Combined efficiency: {product:.0%} — "
            f"your car is losing ~{loss_pct}% of its potential."
        )

    # All good
    if not tips:
        tips.append(
            "All part efficiencies are excellent! "
            "Try a different track or move to Ghost mode."
        )

    return tips


def format_trial_output(result: TrialResult, tips: list[str]) -> str:
    """Format time trial result + coaching as terminal output."""
    eff = result.efficiency

    mins = int(result.lap_time // 60)
    secs = result.lap_time % 60
    time_str = f"{mins}:{secs:06.3f}"

    lines = [
        f"TIME TRIAL — {result.track_name.upper()}",
        "",
        f"  Lap time:  {time_str}",
        "",
        "  EFFICIENCY BREAKDOWN",
    ]

    parts_to_show = ["gearbox", "cooling", "strategy"]
    for part in parts_to_show:
        score = eff.get(part, 1.0)
        bar_len = int(score * 10)
        bar = "\u2588" * bar_len + "\u2591" * (10 - bar_len)
        annotation = ""
        if part == "gearbox" and score < 0.95:
            annotation = "  \u2190 shifts past peak torque"
        elif part == "cooling" and score < 0.90:
            annotation = "  \u2190 high drag"
        connector = "\u251c" if part != parts_to_show[-1] else "\u2514"
        lines.append(
            f"  {connector}\u2500\u2500 {part.capitalize():12s} "
            f"{bar}  {score:.2f}{annotation}"
        )

    if tips:
        lines.append("")
        for tip in tips:
            lines.append(f"  Tip: {tip}")

    return "\n".join(lines)
