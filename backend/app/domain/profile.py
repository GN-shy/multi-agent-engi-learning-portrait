"""五维适应状态与六维计算机能力画像引擎。"""

from __future__ import annotations

from statistics import mean
from typing import Any

from app.domain.catalog import ComputerCatalog, get_catalog

DIMENSION_SKILLS = {
    "programming_and_algorithms": ["core.programming", "core.data_structures"],
    "systems_foundation": ["core.os", "core.network", "core.database", "core.linux"],
    "software_engineering": ["core.software_engineering", "core.git"],
    "architecture_and_security": ["be.observability", "sec.app", "fs.architecture"],
    "engineering_delivery": ["fs.delivery", "qa.automation", "ops.cicd", "ml.ops"],
}


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


class ProfileEngine:
    def __init__(self, catalog: ComputerCatalog | None = None):
        self.catalog = catalog or get_catalog()

    def analyze(self, data: dict[str, Any], selected_track: str | None = None) -> dict[str, Any]:
        self_scores = {key: float(value) for key, value in data.get("self_assessment", {}).items()}
        diagnostic = {
            key: float(value) for key, value in data.get("diagnostic_results", {}).items()
        }
        skill_scores: dict[str, float] = {}
        for code in self.catalog._skill_map:
            has_self = code in self_scores
            has_diag = code in diagnostic
            if has_self and has_diag:
                skill_scores[code] = round(self_scores[code] * 0.35 + diagnostic[code] * 0.65, 1)
            elif has_diag:
                skill_scores[code] = round(diagnostic[code], 1)
            elif has_self:
                skill_scores[code] = round(self_scores[code] * 0.85, 1)
            else:
                skill_scores[code] = 0.0

        dimensions = {
            name: round(mean(skill_scores[code] for code in codes if code in skill_scores), 1)
            for name, codes in DIMENSION_SKILLS.items()
        }
        route_codes = (
            [skill["code"] for skill in self.catalog.get_track(selected_track)["skills"]]
            if selected_track
            else [
                skill["code"]
                for track in self.catalog.tracks
                for skill in track["skills"]
            ]
        )
        nonzero_route = [skill_scores[code] for code in route_codes if skill_scores[code] > 0]
        dimensions["route_specific"] = round(mean(nonzero_route), 1) if nonzero_route else 0.0

        assessed = [score for score in skill_scores.values() if score > 0]
        breadth = len(assessed) / max(len(skill_scores), 1)
        depth = (
            mean(sorted(assessed, reverse=True)[: max(1, len(assessed) // 3)]) / 100
            if assessed
            else 0
        )
        engineering = mean(
            [
                dimensions["software_engineering"],
                dimensions["engineering_delivery"],
                dimensions["route_specific"],
            ]
        ) / 100
        weekly_hours = int(data.get("weekly_hours", 8))
        cognitive_load = _clamp(0.62 - weekly_hours / 100, 0.18, 0.75)

        relevant_codes = route_codes if selected_track else list(self.catalog._skill_map)
        ranked = sorted(
            ((code, skill_scores[code]) for code in relevant_codes),
            key=lambda pair: pair[1],
        )
        blind_spots = [
            {
                "skill_code": code,
                "name": self.catalog.get_skill(code)["name"],
                "score": score,
            }
            for code, score in ranked
            if score < 60
        ][:8]
        strengths = [
            {
                "skill_code": code,
                "name": self.catalog.get_skill(code)["name"],
                "score": score,
            }
            for code, score in reversed(ranked)
            if score >= 75
        ][:6]

        return {
            "background": data.get("background", ""),
            "goals": data.get("learning_goals", []),
            "preferences": data.get("preferences", []),
            "weekly_hours": weekly_hours,
            "learning_style": data.get("learning_style", "balanced"),
            "knowledge_breadth": round(breadth, 3),
            "knowledge_depth": round(depth, 3),
            "engineering_maturity": round(engineering, 3),
            "cognitive_load": round(cognitive_load, 3),
            "dimension_scores": dimensions,
            "skill_scores": skill_scores,
            "blind_spots": blind_spots,
            "strengths": strengths,
            "comprehensive_score": round(mean(dimensions.values()), 1),
            "evidence_count": len(assessed),
        }
