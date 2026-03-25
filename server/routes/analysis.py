"""Car code analysis endpoint -- parts detection, league, code quality."""

import ast

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["analysis"])

KNOWN_PARTS = [
    "engine_map", "gearbox", "fuel_mix", "suspension", "cooling",
    "ers_deploy", "differential", "brake_bias", "ers_harvest", "strategy",
]

F3_PARTS = {"gearbox", "cooling", "strategy"}
F2_PARTS = F3_PARTS | {"suspension", "ers_deploy", "fuel_mix"}
F1_PARTS = F2_PARTS | {"differential", "brake_bias", "ers_harvest", "engine_map"}


class AnalysisRequest(BaseModel):
    source: str


@router.post("/car-analysis")
async def analyze_car(req: AnalysisRequest):
    """Analyze car source for parts, league, and code quality."""
    source = req.source.strip()
    parts_detected = _detect_parts(source)
    league = _determine_league(parts_detected)
    quality = _compute_quality(source)
    return {"parts": parts_detected, "league": league, "quality": quality}


def _detect_parts(source: str) -> list[dict]:
    """Detect which of the 10 parts are defined as functions."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [{"name": p, "detected": False} for p in KNOWN_PARTS]

    defined_funcs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_funcs.add(node.name)

    return [{"name": p, "detected": p in defined_funcs} for p in KNOWN_PARTS]


def _determine_league(parts: list[dict]) -> str:
    """Determine league from detected parts."""
    detected = {p["name"] for p in parts if p["detected"]}
    if detected >= F1_PARTS:
        return "Championship"
    if detected >= F2_PARTS:
        return "F2"
    return "F3"


def _compute_quality(source: str) -> dict:
    """Compute code quality metrics."""
    try:
        from engine.code_quality import (
            compute_cyclomatic_complexity,
            compute_reliability_score,
        )

        cc = compute_cyclomatic_complexity(source)
        reliability = compute_reliability_score(source)
        return {"complexity": cc, "reliability": round(reliability, 2)}
    except Exception:
        return {"complexity": {}, "reliability": 1.0}
