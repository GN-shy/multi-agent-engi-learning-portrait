"""双策略生成、结构化仲裁与质量度量。"""

from __future__ import annotations

from statistics import mean
from typing import Any

from app.domain.catalog import ComputerCatalog, get_catalog


class ContentEngine:
    def __init__(self, catalog: ComputerCatalog | None = None):
        self.catalog = catalog or get_catalog()

    def generate_rigorous(
        self,
        track_code: str,
        goal: str,
        profile: dict[str, Any],
        route_match: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        track = self.catalog.get_track(track_code)
        ordered = self._ordered_skills(track)
        sections = []
        for skill in ordered:
            source = self._evidence_for_skill(skill["code"], evidence)
            sections.append(
                {
                    "skill_code": skill["code"],
                    "title": skill["name"],
                    "difficulty": skill["difficulty"],
                    "objective": f"能够解释并完成 {skill['name']} 的代表性任务",
                    "explanation": skill["description"],
                    "checkpoint": f"用自己的话说明 {skill['name']} 的边界、常见失败和验证方法。",
                    "citation_ids": [source["chunk_id"]] if source else [],
                }
            )
        return self._candidate(
            "dgs_a",
            "rigorous",
            track,
            goal,
            profile,
            route_match,
            sections,
            evidence,
            practice_mode="specification_first",
        )

    def generate_project_first(
        self,
        track_code: str,
        goal: str,
        profile: dict[str, Any],
        route_match: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        track = self.catalog.get_track(track_code)
        skills = self._ordered_skills(track)
        sections = []
        for index, skill in enumerate(skills):
            source = self._evidence_for_skill(skill["code"], evidence)
            sections.append(
                {
                    "skill_code": skill["code"],
                    "title": f"挑战 {index + 1}：用 {skill['name']} 推进项目",
                    "difficulty": skill["difficulty"],
                    "objective": f"在“{track['project']['title']}”中产出可验证增量",
                    "explanation": (
                        f"先实现最小结果，再根据失败现象回到原理：{skill['description']}"
                    ),
                    "checkpoint": f"提交运行证据，并说明一次与 {skill['name']} 有关的取舍。",
                    "citation_ids": [source["chunk_id"]] if source else [],
                }
            )
        return self._candidate(
            "dgs_b",
            "project_first",
            track,
            goal,
            profile,
            route_match,
            sections,
            evidence,
            practice_mode="challenge_first",
        )

    def _candidate(
        self,
        agent: str,
        strategy: str,
        track: dict[str, Any],
        goal: str,
        profile: dict[str, Any],
        route_match: dict[str, Any],
        sections: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        practice_mode: str,
    ) -> dict[str, Any]:
        weekly_hours = profile.get("weekly_hours", 8)
        phases = self._plan_phases(track, sections, weekly_hours, strategy)
        quizzes = [
            {
                "id": f"q-{skill['code']}",
                "skill_code": skill["code"],
                "type": "evidence",
                "question": f"为“{skill['name']}”设计一个可验证的小任务，并写出通过标准。",
                "rubric": [
                    "任务覆盖核心概念",
                    "通过标准可以客观检查",
                    "能说明常见失败与定位方法",
                ],
                "max_score": 10,
            }
            for skill in track["skills"]
        ]
        return {
            "agent": agent,
            "strategy": strategy,
            "track_code": track["code"],
            "title": f"{track['name']} · {goal}",
            "learner_fit": {
                "style": profile.get("learning_style", "balanced"),
                "weekly_hours": weekly_hours,
                "top_gaps": route_match.get("skill_gaps", [])[:3],
            },
            "lecture": {
                "summary": track["description"],
                "objectives": [section["objective"] for section in sections],
                "sections": sections,
            },
            "practice": {
                "mode": practice_mode,
                "title": track["project"]["title"],
                "deliverables": track["project"]["deliverables"],
                "steps": [
                    {
                        "id": f"step-{index + 1}",
                        "title": section["title"],
                        "skill_code": section["skill_code"],
                        "done": False,
                        "proof_required": "代码提交、运行截图或测试结果",
                    }
                    for index, section in enumerate(sections)
                ],
                "acceptance": track["project"]["acceptance"],
            },
            "assessment": {
                "questions": quizzes,
                "pass_score": round(len(quizzes) * 10 * 0.7),
            },
            "plan": phases,
            "source_traces": [
                {
                    "chunk_id": item["chunk_id"],
                    "title": item["title"],
                    "source_title": item["source_title"],
                    "source_url": item["source_url"],
                    "content_version": item["content_version"],
                    "source_layer": item.get("source_layer", "local_knowledge"),
                    "credibility": item.get("credibility"),
                    "retrieved_at": item.get("retrieved_at"),
                }
                for item in evidence
            ],
        }

    def arbitrate(
        self,
        candidate_a: dict[str, Any],
        candidate_b: dict[str, Any],
        evidence: list[dict[str, Any]],
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        score_a = self._score(candidate_a, evidence, profile)
        score_b = self._score(candidate_b, evidence, profile)
        delta = abs(score_a["total"] - score_b["total"])
        debate_triggered = delta < 4 or min(
            score_a["citation_coverage"], score_b["citation_coverage"]
        ) < 0.95
        debate = []
        if debate_triggered:
            debate = [
                {
                    "round": 1,
                    "topic": "学习顺序与项目切入点",
                    "dgs_a": "先满足前置依赖，再进入综合项目，降低认知跳跃。",
                    "dgs_b": "用可运行增量激活动机，再按失败证据回补原理。",
                    "ars_decision": "保留严格前置顺序，同时每阶段加入可运行项目增量。",
                    "evidence_ids": [item["chunk_id"] for item in evidence[:3]],
                }
            ]

        winner = candidate_a if score_a["total"] >= score_b["total"] else candidate_b
        secondary = candidate_b if winner is candidate_a else candidate_a
        final = {
            **winner,
            "agent": "ars_fusion",
            "strategy": f"fused:{winner['strategy']}+{secondary['strategy']}",
            "practice": {
                **winner["practice"],
                "steps": self._merge_steps(
                    winner["practice"]["steps"], secondary["practice"]["steps"]
                ),
            },
        }
        final_score = self._score(final, evidence, profile)
        return {
            "candidate_scores": {"dgs_a": score_a, "dgs_b": score_b},
            "debate_triggered": debate_triggered,
            "debate_rounds": len(debate),
            "debate": debate,
            "winner": winner["agent"],
            "decision_summary": (
                f"采用 {winner['strategy']} 作为主结构，并融合另一策略的项目步骤。"
            ),
            "final_output": final,
            "quality_metrics": final_score,
        }

    def _score(
        self,
        candidate: dict[str, Any],
        evidence: list[dict[str, Any]],
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        sections = candidate["lecture"]["sections"]
        track_skills = self.catalog.get_track(candidate["track_code"])["skills"]
        target = {skill["code"] for skill in track_skills}
        covered = {section["skill_code"] for section in sections}
        valid_sources = {item["chunk_id"] for item in evidence}
        cited_sections = [
            section
            for section in sections
            if section.get("citation_ids")
            and all(item in valid_sources for item in section["citation_ids"])
        ]
        coverage = len(target & covered) / max(1, len(target))
        citation_coverage = len(cited_sections) / max(1, len(sections))
        prerequisite_violations = self._prerequisite_violations(sections)
        expected_difficulty = 1 + profile.get("knowledge_depth", 0.2) * 4
        actual_difficulty = mean(section["difficulty"] for section in sections)
        difficulty_fit = max(0, 1 - abs(expected_difficulty - actual_difficulty) / 4)
        total = (
            coverage * 35
            + citation_coverage * 30
            + difficulty_fit * 25
            + max(0, 10 - prerequisite_violations * 3)
        )
        return {
            "total": round(total, 1),
            "knowledge_coverage": round(coverage, 3),
            "citation_coverage": round(citation_coverage, 3),
            "profile_fit": round(difficulty_fit, 3),
            "prerequisite_violations": prerequisite_violations,
            "hallucination_risk": round(max(0, 1 - citation_coverage) * 0.08, 3),
        }

    def _prerequisite_violations(self, sections: list[dict[str, Any]]) -> int:
        positions = {section["skill_code"]: index for index, section in enumerate(sections)}
        violations = 0
        for code, index in positions.items():
            for prerequisite in self.catalog.get_skill(code).get("prerequisites", []):
                if prerequisite in positions and positions[prerequisite] > index:
                    violations += 1
        return violations

    def _ordered_skills(self, track: dict[str, Any]) -> list[dict[str, Any]]:
        remaining = {item["code"]: item for item in track["skills"]}
        ordered = []
        while remaining:
            ready = [
                item
                for item in remaining.values()
                if all(
                    prerequisite not in remaining
                    for prerequisite in item.get("prerequisites", [])
                )
            ]
            if not ready:
                ready = [min(remaining.values(), key=lambda item: item["difficulty"])]
            for item in sorted(ready, key=lambda entry: (entry["difficulty"], entry["code"])):
                ordered.append(item)
                remaining.pop(item["code"])
        return ordered

    @staticmethod
    def _evidence_for_skill(
        skill_code: str, evidence: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        return next((item for item in evidence if item.get("skill_code") == skill_code), None)

    @staticmethod
    def _merge_steps(primary: list[dict], secondary: list[dict]) -> list[dict]:
        merged = []
        seen = set()
        for step in primary + secondary:
            key = step["skill_code"]
            if key not in seen:
                seen.add(key)
                merged.append(step)
        return merged

    @staticmethod
    def _plan_phases(
        track: dict[str, Any],
        sections: list[dict[str, Any]],
        weekly_hours: int,
        strategy: str,
    ) -> list[dict[str, Any]]:
        labels = ["基础校准", "核心能力", "项目交付", "评测与复盘"]
        buckets = [sections[:1], sections[1:3], sections[3:], sections[-1:]]
        return [
            {
                "id": f"phase-{index + 1}",
                "name": label,
                "week_start": index * 2 + 1,
                "week_end": index * 2 + 2,
                "hours_per_week": weekly_hours,
                "strategy": strategy,
                "skills": [section["skill_code"] for section in bucket],
                "milestone": (
                    track["project"]["deliverables"][
                        min(index, len(track["project"]["deliverables"]) - 1)
                    ]
                ),
                "status": "active" if index == 0 else "pending",
            }
            for index, (label, bucket) in enumerate(zip(labels, buckets))
        ]
