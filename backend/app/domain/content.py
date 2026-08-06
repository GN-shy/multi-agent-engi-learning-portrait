"""双策略生成、结构化仲裁与质量度量。"""

from __future__ import annotations

import re
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
        pathway_id: str | None = None,
        pathway_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        selected_pathways = pathway_ids or ([pathway_id] if pathway_id else [])
        track = self._learning_scope(track_code, selected_pathways)
        ordered = self._ordered_skills(track)
        catalog_sources = self._catalog_sources(track)
        auditable_evidence = evidence + catalog_sources
        sections = []
        for skill in ordered:
            source = self._evidence_for_skill(skill["code"], auditable_evidence)
            sections.append(
                {
                    "skill_code": skill["code"],
                    "title": skill["name"],
                    "difficulty": skill["difficulty"],
                    "objective": f"能够解释并完成 {skill['name']} 的代表性任务",
                    "explanation": skill["description"],
                    "why_this_matters": f"{skill['name']} 是完成“{track['project']['title']}”时必须能够独立判断和落地的能力。",
                    "learning_tasks": [
                        f"用一个最小示例验证 {skill['name']} 的核心机制",
                        "记录输入、预期输出、实际输出和差异",
                        "整理一条可复用的排错清单",
                    ],
                    "common_mistakes": [
                        "只记结论，没有运行或对照证据",
                        "忽略异常路径与失败边界",
                    ],
                    "verification": "提供可重复执行的命令、测试结果或界面操作记录。",
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
            auditable_evidence,
            practice_mode="specification_first",
            pathway_id=pathway_id,
            pathway_ids=selected_pathways,
        )

    def generate_project_first(
        self,
        track_code: str,
        goal: str,
        profile: dict[str, Any],
        route_match: dict[str, Any],
        evidence: list[dict[str, Any]],
        pathway_id: str | None = None,
        pathway_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        selected_pathways = pathway_ids or ([pathway_id] if pathway_id else [])
        track = self._learning_scope(track_code, selected_pathways)
        skills = self._ordered_skills(track)
        catalog_sources = self._catalog_sources(track)
        auditable_evidence = evidence + catalog_sources
        sections = []
        for index, skill in enumerate(skills):
            source = self._evidence_for_skill(skill["code"], auditable_evidence)
            sections.append(
                {
                    "skill_code": skill["code"],
                    "title": f"挑战 {index + 1}：用 {skill['name']} 推进项目",
                    "difficulty": skill["difficulty"],
                    "objective": f"在“{track['project']['title']}”中产出可验证增量",
                    "explanation": (
                        f"先实现最小结果，再根据失败现象回到原理：{skill['description']}"
                    ),
                    "why_this_matters": f"这一能力直接决定“{track['project']['title']}”能否从演示走向可交付。",
                    "learning_tasks": [
                        "先交付一个可以运行的最小增量",
                        "为正常路径和异常路径各补一条验证",
                        "根据证据解释一次关键技术取舍",
                    ],
                    "common_mistakes": [
                        "只展示最终界面，无法复现过程",
                        "用主观描述代替测试、日志或数据指标",
                    ],
                    "verification": "将代码提交、测试结果与对应任务步骤关联。",
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
            auditable_evidence,
            practice_mode="challenge_first",
            pathway_id=pathway_id,
            pathway_ids=selected_pathways,
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
        pathway_id: str | None = None,
        pathway_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        weekly_hours = profile.get("weekly_hours", 8)
        selected_ids = pathway_ids or ([pathway_id] if pathway_id else [])
        pathways = track.get("selected_pathways", [])
        pathway = pathways[0] if pathways else None
        route_bundle = (
            self.catalog.compose_pathways(selected_ids, weekly_hours, strategy)
            if selected_ids
            else None
        )
        phases = (
            route_bundle["phases"]
            if route_bundle
            else self._plan_phases(track, sections, weekly_hours, strategy, pathway)
        )
        quizzes = [
            {
                "id": f"q-{skill['code']}",
                "skill_code": skill["code"],
                "type": "evidence",
                "question": f"为“{skill['name']}”设计一个可验证的小任务，并写出通过标准。",
                "rubric": [
                    "写出可执行行动",
                    "给出客观验证方式",
                    "覆盖异常与失败边界",
                    "解释关键技术取舍",
                ],
                "answer_requirements": [
                    "做什么",
                    "如何验证",
                    "失败如何定位",
                    "为什么这样选择",
                ],
                "max_score": 10,
            }
            for skill in track["skills"]
        ]
        return {
            "agent": agent,
            "strategy": strategy,
            "track_code": track["code"],
            "track_codes": track.get("track_codes", [track["code"]]),
            "target_skill_codes": [skill["code"] for skill in track["skills"]],
            "pathway": (
                {
                    "id": pathway["id"],
                    "name": pathway["name"],
                    "estimated_months": pathway["estimated_months"],
                    "milestone": pathway["milestone"],
                }
                if pathway
                else None
            ),
            "pathways": [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "track_code": item["track_code"],
                    "estimated_months": item["estimated_months"],
                    "milestone": item["milestone"],
                }
                for item in pathways
            ],
            "route_bundle": route_bundle,
            "title": (
                f"{' + '.join(item['name'] for item in pathways)} · {goal}"
                if pathways
                else f"{track['name']} · {goal}"
            ),
            "learner_fit": {
                "style": profile.get("learning_style", "balanced"),
                "weekly_hours": weekly_hours,
                "top_gaps": route_match.get("skill_gaps", [])[:3],
                "selected_pathways": [item["name"] for item in pathways],
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
                        "instructions": (
                            f"围绕“{section['objective']}”完成一个可运行增量；"
                            "先写清验收条件，再实现、验证并记录失败修正。"
                        ),
                        "proof_required": "至少提交一条仓库、提交哈希、测试结果或部署地址，并与本步骤关联",
                        "evidence_types": ["repository", "commit", "test", "deployment"],
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
                    "skill_code": item.get("skill_code", ""),
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
        quality_gate = {
            "passed": (
                final_score["citation_coverage"] >= 0.95
                and final_score["prerequisite_violations"] == 0
                and final_score["hallucination_risk"] < 0.05
            ),
            "rules": {
                "citation_coverage_at_least_95_percent": final_score["citation_coverage"] >= 0.95,
                "no_prerequisite_violation": final_score["prerequisite_violations"] == 0,
                "system_detected_unsupported_content_below_5_percent": final_score["hallucination_risk"] < 0.05,
            },
            "notice": "该闸门检查引用是否真实存在且与同一技能绑定；它是发布前系统检测，不等同于人工盲测的真实幻觉率。",
        }
        return {
            "candidate_scores": {"dgs_a": score_a, "dgs_b": score_b},
            "debate_triggered": debate_triggered,
            "debate_rounds": len(debate),
            "debate": debate,
            "winner": winner["agent"],
            "decision_summary": (
                f"采用 {winner['strategy']} 作为主结构，并融合另一策略的项目步骤。"
            ),
            "quality_gate": quality_gate,
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
        target = set(
            candidate.get("target_skill_codes")
            or [
                skill["code"]
                for skill in self.catalog.get_track(candidate["track_code"])["skills"]
            ]
        )
        covered = {section["skill_code"] for section in sections}
        valid_sources = {item["chunk_id"] for item in evidence} | {
            item["chunk_id"] for item in candidate.get("source_traces", [])
        }
        cited_sections = [
            section
            for section in sections
            if section.get("citation_ids")
            and all(item in valid_sources for item in section["citation_ids"])
        ]
        source_items = {
            item["chunk_id"]: item
            for item in evidence + candidate.get("source_traces", [])
            if item.get("chunk_id")
        }
        grounded_sections = [
            section
            for section in cited_sections
            if any(
                source_items.get(citation_id, {}).get("skill_code") == section["skill_code"]
                for citation_id in section.get("citation_ids", [])
            )
        ]
        coverage = len(target & covered) / max(1, len(target))
        citation_coverage = len(cited_sections) / max(1, len(sections))
        grounding_coverage = len(grounded_sections) / max(1, len(sections))
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
            "citation_integrity": round(
                sum(
                    bool(section.get("citation_ids"))
                    and all(item in valid_sources for item in section["citation_ids"])
                    for section in sections
                )
                / max(1, len(sections)),
                3,
            ),
            "grounding_coverage": round(grounding_coverage, 3),
            "profile_fit": round(difficulty_fit, 3),
            "prerequisite_violations": prerequisite_violations,
            "hallucination_risk": round(max(0, 1 - grounding_coverage), 3),
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

    def _learning_scope(
        self,
        primary_track_code: str,
        pathway_ids: list[str],
    ) -> dict[str, Any]:
        primary = self.catalog.get_track(primary_track_code)
        if not pathway_ids:
            return primary
        pathways = [self.catalog.get_pathway(pathway_id) for pathway_id in pathway_ids]
        if pathways[0]["track_code"] != primary_track_code:
            raise ValueError("主方向必须与第一条细分路线一致")
        track_codes = list(dict.fromkeys(item["track_code"] for item in pathways))
        tracks = [self.catalog.get_track(code) for code in track_codes]
        skills = list(
            {
                skill["code"]: skill
                for track in tracks
                for skill in track["skills"]
            }.values()
        )
        deliverables = [
            f"{pathway['name']}：{pathway['milestone']}"
            for pathway in pathways
        ]
        return {
            **primary,
            "name": " + ".join(pathway["name"] for pathway in pathways),
            "description": (
                "本组合路线按共同基础、方向核心、工程质量、性能部署和综合项目组织，"
                "覆盖：" + "、".join(pathway["name"] for pathway in pathways) + "。"
            ),
            "track_codes": track_codes,
            "selected_pathways": pathways,
            "skills": skills,
            "project": {
                "title": "跨方向综合作品：" + " + ".join(
                    pathway["name"] for pathway in pathways
                ),
                "deliverables": deliverables,
                "acceptance": (
                    "每条所选路线均完成对应里程碑；共同技术只验收一次，"
                    "跨方向接口、部署、测试和关键取舍必须有可复现证据。"
                ),
            },
        }

    @staticmethod
    def _evidence_for_skill(
        skill_code: str, evidence: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        return next((item for item in evidence if item.get("skill_code") == skill_code), None)

    @staticmethod
    def _catalog_sources(track: dict[str, Any]) -> list[dict[str, Any]]:
        """Turn reviewed catalog references into explicit, skill-scoped traces.

        These traces do not pretend a web retrieval happened. They record the exact
        route catalog source and version used for deterministic section content.
        """
        sources = track.get("sources", [])
        if not sources:
            return []
        traces = []
        for index, skill in enumerate(track.get("skills", [])):
            source = sources[index % len(sources)]
            traces.append(
                {
                    "chunk_id": f"catalog:{track['code']}:{skill['code']}",
                    "skill_code": skill["code"],
                    "title": f"{skill['name']}：领域目录审核依据",
                    "source_title": source["title"],
                    "source_url": source["url"],
                    "content_version": source.get("version", "catalog-current"),
                    "source_layer": "catalog_reference",
                    "credibility": 0.9,
                    "retrieved_at": None,
                }
            )
        return traces

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

    def _plan_phases(
        self,
        track: dict[str, Any],
        sections: list[dict[str, Any]],
        weekly_hours: int,
        strategy: str,
        pathway: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if pathway:
            route_skills = [item["code"] for item in track["skills"]]
            week_cursor = 1
            phases = []
            for index, stage in enumerate(pathway["stages"]):
                duration_numbers = [
                    int(value) for value in re.findall(r"\d+", stage["duration"])
                ]
                duration_weeks = (
                    max(1, min(10, round(mean(duration_numbers))))
                    if duration_numbers
                    else 2
                )
                assigned_skill = route_skills[
                    min(
                        len(route_skills) - 1,
                        index * len(route_skills) // max(1, len(pathway["stages"])),
                    )
                ]
                tasks = [
                    {
                        "id": f"{pathway['id']}:stage-{index + 1}:task-{task_index + 1}",
                        "title": topic,
                        "skill_code": assigned_skill,
                        "evidence_required": "学习笔记、可运行代码、测试结果或作品截图至少一项",
                    }
                    for task_index, topic in enumerate(stage["topics"])
                ]
                phases.append(
                    {
                        "id": f"phase-{index + 1}",
                        "pathway_id": pathway["id"],
                        "pathway_name": pathway["name"],
                        "name": stage["title"],
                        "source_duration": stage["duration"],
                        "week_start": week_cursor,
                        "week_end": week_cursor + duration_weeks - 1,
                        "hours_per_week": weekly_hours,
                        "strategy": strategy,
                        "skills": sorted(
                            {task["skill_code"] for task in tasks}
                        ),
                        "tasks": tasks,
                        "milestone": (
                            pathway["milestone"]
                            if index == len(pathway["stages"]) - 1
                            else f"完成“{stage['title']}”的可验证阶段作品并通过复盘"
                        ),
                        "status": "active" if index == 0 else "pending",
                    }
                )
                week_cursor += duration_weeks
            return phases

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
