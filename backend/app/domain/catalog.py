"""计算机方向、技能图谱与知识来源目录。"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from math import ceil
from statistics import mean
from typing import Any

from app.core.config import settings


class CatalogError(RuntimeError):
    pass


class ComputerCatalog:
    def __init__(
        self,
        raw: dict[str, Any],
        pathways_raw: dict[str, Any] | None = None,
        career_raw: dict[str, Any] | None = None,
    ):
        self.raw = raw
        self.version = raw["version"]
        self.domain = raw["domain"]
        self.clusters = raw["clusters"]
        self.tracks = raw["tracks"]
        self.salary_scope = (career_raw or {}).get("salary_scope", "")
        career_profiles = (career_raw or {}).get("profiles", {})
        self.pathways = [
            {
                **pathway,
                "career": career_profiles.get(pathway["id"], {}),
                "salary_scope": self.salary_scope,
            }
            for pathway in (pathways_raw or {}).get("directions", [])
        ]
        self._pathway_map = {pathway["id"]: pathway for pathway in self.pathways}
        for track in self.tracks:
            track["pathway_variants"] = [
                pathway
                for pathway in self.pathways
                if pathway["track_code"] == track["code"]
            ]
        self._track_map = {track["code"]: track for track in self.tracks}
        self._skill_map = {skill["code"]: skill for skill in raw["core_skills"]}
        for track in self.tracks:
            for skill in track["skills"]:
                self._skill_map[skill["code"]] = {**skill, "track_code": track["code"]}
        self.validate()

    def validate(self) -> None:
        if len(self.tracks) < 15:
            raise CatalogError("正式计算机路线不得少于 15 条")
        unknown_pathway_tracks = sorted(
            {
                pathway["track_code"]
                for pathway in self.pathways
                if pathway["track_code"] not in self._track_map
            }
        )
        if unknown_pathway_tracks:
            raise CatalogError(f"细分路线引用了不存在的主路线: {unknown_pathway_tracks}")
        for track in self.tracks:
            required = ("code", "cluster", "name", "description", "skills", "project", "sources")
            missing = [key for key in required if not track.get(key)]
            if missing:
                raise CatalogError(f"路线 {track.get('code')} 缺少字段: {missing}")
            if len(track["skills"]) < 3:
                raise CatalogError(f"路线 {track['code']} 至少需要 3 个专属技能")
            if not track["pathway_variants"]:
                raise CatalogError(f"路线 {track['code']} 缺少可执行的细分学习路线")
            if not track["project"].get("acceptance"):
                raise CatalogError(f"路线 {track['code']} 缺少项目验收标准")
            for skill in track["skills"]:
                for prerequisite in skill.get("prerequisites", []):
                    if prerequisite not in self._skill_map:
                        raise CatalogError(
                            f"技能 {skill['code']} 引用了不存在的前置技能 {prerequisite}"
                        )
            for pathway in track["pathway_variants"]:
                if not pathway.get("stages") or not pathway.get("milestone"):
                    raise CatalogError(f"细分路线 {pathway.get('id')} 缺少阶段或里程碑")
                if not pathway.get("career", {}).get("roles"):
                    raise CatalogError(f"细分路线 {pathway.get('id')} 缺少就业画像")
                for stage in pathway["stages"]:
                    if not stage.get("title") or not stage.get("topics"):
                        raise CatalogError(
                            f"细分路线 {pathway['id']} 存在不可执行的空阶段"
                        )

    def get_track(self, code: str) -> dict[str, Any]:
        try:
            return self._track_map[code]
        except KeyError as exc:
            raise CatalogError(f"未知计算机路线: {code}") from exc

    def get_skill(self, code: str) -> dict[str, Any]:
        try:
            return self._skill_map[code]
        except KeyError as exc:
            raise CatalogError(f"未知技能: {code}") from exc

    def get_pathway(
        self, pathway_id: str, track_code: str | None = None
    ) -> dict[str, Any]:
        try:
            pathway = self._pathway_map[pathway_id]
        except KeyError as exc:
            raise CatalogError(f"未知细分路线: {pathway_id}") from exc
        if track_code and pathway["track_code"] != track_code:
            raise CatalogError(
                f"细分路线 {pathway_id} 不属于主路线 {track_code}"
            )
        return pathway

    def pathway_summary(self, pathway: dict[str, Any]) -> dict[str, Any]:
        track = self.get_track(pathway["track_code"])
        return {
            **pathway,
            "track_name": track["name"],
            "track_role": track["role"],
            "stage_count": len(pathway["stages"]),
            "technology_count": len(
                {
                    self._topic_key(topic)
                    for stage in pathway["stages"]
                    for topic in stage["topics"]
                }
            ),
        }

    def list_pathways(self) -> list[dict[str, Any]]:
        return [self.pathway_summary(pathway) for pathway in self.pathways]

    @staticmethod
    def _topic_key(topic: str) -> str:
        normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff+#.]", "", topic.lower())
        aliases = {
            "html": "html",
            "html5": "html",
            "html语义化": "html-semantics",
            "html5语义化": "html-semantics",
            "git版本控制": "git",
            "git与开发环境": "git",
            "git": "git",
            "cicd": "ci-cd",
            "ci/cd": "ci-cd",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _duration_weeks(duration: str) -> int:
        values = [int(value) for value in re.findall(r"\d+", duration)]
        return max(1, min(12, round(mean(values)))) if values else 2

    def compose_pathways(
        self,
        pathway_ids: list[str],
        weekly_hours: int = 8,
        strategy: str = "dependency_first",
    ) -> dict[str, Any]:
        unique_ids = list(dict.fromkeys(pathway_ids))
        if not unique_ids:
            raise CatalogError("请至少选择一条细分学习路线")
        if len(unique_ids) > 6:
            raise CatalogError("一次最多组合 6 条细分学习路线")
        pathways = [self.get_pathway(pathway_id) for pathway_id in unique_ids]
        stage_labels = [
            "通用基础与开发环境",
            "核心语言、框架与数据流",
            "工程生态、数据与质量",
            "性能优化与生产交付",
            "高级架构与综合项目",
            "作品集、面试与持续进阶",
            "专项能力深化",
            "生产级闭环",
            "职业能力与前沿探索",
        ]
        seen_topics: set[str] = set()
        phases: list[dict[str, Any]] = []
        week_cursor = 1
        max_stages = max(len(pathway["stages"]) for pathway in pathways)

        for stage_index in range(max_stages):
            stage_entries = [
                (pathway, pathway["stages"][stage_index])
                for pathway in pathways
                if stage_index < len(pathway["stages"])
            ]
            if not stage_entries:
                continue
            tasks: list[dict[str, Any]] = []
            phase_skills: set[str] = set()
            source_weeks: list[int] = []
            checkpoints: list[str] = []
            for pathway, stage in stage_entries:
                track = self.get_track(pathway["track_code"])
                route_skills = [skill["code"] for skill in track["skills"]]
                assigned_skill = route_skills[
                    min(
                        len(route_skills) - 1,
                        stage_index * len(route_skills) // max(1, len(pathway["stages"])),
                    )
                ]
                source_weeks.append(self._duration_weeks(stage["duration"]))
                checkpoints.append(f"{pathway['name']}：完成“{stage['title']}”阶段作品")
                for topic_index, topic in enumerate(stage["topics"]):
                    topic_key = self._topic_key(topic)
                    if topic_key in seen_topics:
                        continue
                    seen_topics.add(topic_key)
                    phase_skills.add(assigned_skill)
                    tasks.append(
                        {
                            "id": (
                                f"{pathway['id']}:stage-{stage_index + 1}:"
                                f"task-{topic_index + 1}"
                            ),
                            "title": topic,
                            "pathway_id": pathway["id"],
                            "pathway_name": pathway["name"],
                            "stage_title": stage["title"],
                            "skill_code": assigned_skill,
                            "learning_action": (
                                f"围绕“{topic}”完成原理说明、最小可运行示例、"
                                "正常与异常路径验证，并记录一次关键取舍。"
                            ),
                            "evidence_required": (
                                "代码仓库或作品链接 + 运行截图/日志 + 测试结果 + 复盘说明"
                            ),
                            "acceptance": (
                                f"能够不照抄教程独立完成“{topic}”代表任务，"
                                "解释失败边界，并用客观证据证明结果。"
                            ),
                        }
                    )
            if not tasks:
                continue
            base_weeks = max(source_weeks)
            duration_weeks = max(
                1,
                ceil(base_weeks * (1 + 0.35 * max(0, len(stage_entries) - 1))),
            )
            phases.append(
                {
                    "id": f"phase-{len(phases) + 1}",
                    "name": (
                        stage_labels[stage_index]
                        if stage_index < len(stage_labels)
                        else f"专项进阶 {stage_index + 1}"
                    ),
                    "week_start": week_cursor,
                    "week_end": week_cursor + duration_weeks - 1,
                    "hours_per_week": weekly_hours,
                    "strategy": strategy,
                    "pathway_ids": [pathway["id"] for pathway, _ in stage_entries],
                    "pathway_names": [pathway["name"] for pathway, _ in stage_entries],
                    "skills": sorted(phase_skills),
                    "tasks": tasks,
                    "milestones": checkpoints,
                    "milestone": "；".join(checkpoints),
                    "status": "active" if not phases else "pending",
                }
            )
            week_cursor += duration_weeks

        stack_index = [
            {
                "pathway_id": pathway["id"],
                "pathway_name": pathway["name"],
                "track_code": pathway["track_code"],
                "track_name": self.get_track(pathway["track_code"])["name"],
                "estimated_months": pathway["estimated_months"],
                "stages": [
                    {
                        **stage,
                        "sequence": index + 1,
                    }
                    for index, stage in enumerate(pathway["stages"])
                ],
                "technologies": list(
                    dict.fromkeys(
                        topic
                        for stage in pathway["stages"]
                        for topic in stage["topics"]
                    )
                ),
                "milestone": pathway["milestone"],
            }
            for pathway in pathways
        ]
        total_weeks = phases[-1]["week_end"] if phases else 0
        return {
            "pathway_ids": unique_ids,
            "pathway_count": len(pathways),
            "track_codes": list(dict.fromkeys(item["track_code"] for item in pathways)),
            "title": " + ".join(item["name"] for item in pathways),
            "total_weeks": total_weeks,
            "estimated_months": round(total_weeks / 4.3, 1),
            "technology_count": len(seen_topics),
            "stack_index": stack_index,
            "phases": phases,
            "final_milestones": [
                {"pathway_name": item["name"], "milestone": item["milestone"]}
                for item in pathways
            ],
            "optimization_notes": [
                "公共基础只学习一次，重复技术点已自动合并，避免多路线重复投入。",
                "先安排共同前置能力，再交错推进各方向专项，降低认知切换成本。",
                "每个任务都带可提交证据与验收标准，学习结果可验证、可进入作品集。",
                "最终项目同时覆盖所选方向，形成面向就业的复合型能力证明。",
            ],
        }

    def track_tree(self) -> list[dict[str, Any]]:
        return [
            {
                **cluster,
                "tracks": [
                    self.track_summary(track)
                    for track in self.tracks
                    if track["cluster"] == cluster["code"]
                ],
            }
            for cluster in self.clusters
        ]

    def track_summary(self, track: dict[str, Any]) -> dict[str, Any]:
        return {
            "code": track["code"],
            "cluster": track["cluster"],
            "name": track["name"],
            "role": track["role"],
            "description": track["description"],
            "keywords": track["keywords"],
            "skill_count": len(track["skills"]),
            "project": track["project"]["title"],
            "pathway_count": len(track["pathway_variants"]),
            "pathway_names": [item["name"] for item in track["pathway_variants"]],
            "estimated_months": sorted(
                {item["estimated_months"] for item in track["pathway_variants"]}
            ),
        }

    def skill_graph(self, track_code: str) -> dict[str, Any]:
        track = self.get_track(track_code)
        route_skill_codes = {item["code"] for item in track["skills"]}
        included = set(route_skill_codes)
        frontier = list(route_skill_codes)
        while frontier:
            code = frontier.pop()
            for prerequisite in self.get_skill(code).get("prerequisites", []):
                if prerequisite not in included:
                    included.add(prerequisite)
                    frontier.append(prerequisite)

        nodes = []
        edges = []
        for code in included:
            skill = self.get_skill(code)
            nodes.append(
                {
                    "id": code,
                    "name": skill["name"],
                    "description": skill["description"],
                    "difficulty": skill["difficulty"],
                    "kind": "route" if code in route_skill_codes else "core",
                }
            )
            for prerequisite in skill.get("prerequisites", []):
                if prerequisite in included:
                    edges.append(
                        {
                            "source": prerequisite,
                            "target": code,
                            "relation": "prerequisite",
                        }
                    )
        return {
            "track": self.track_summary(track),
            "nodes": sorted(nodes, key=lambda item: (item["difficulty"], item["id"])),
            "edges": edges,
        }

    def diagnostic(self, track_code: str) -> list[dict[str, Any]]:
        track = self.get_track(track_code)
        questions = []
        for index, skill in enumerate(track["skills"]):
            questions.append(
                {
                    "id": f"diag-{track_code}-{index + 1}",
                    "skill_code": skill["code"],
                    "type": "self_evidence",
                    "prompt": (
                        f"你能否在不照抄教程的情况下完成“{skill['name']}”相关任务，"
                        "并解释关键取舍？"
                    ),
                    "options": [
                        {"label": "不了解", "score": 10},
                        {"label": "能跟做", "score": 35},
                        {"label": "能独立完成", "score": 70},
                        {"label": "能评审和优化", "score": 90}
                    ],
                }
            )
        return questions


@lru_cache
def get_catalog() -> ComputerCatalog:
    if not settings.catalog_path.exists():
        raise CatalogError(f"计算机路线目录不存在: {settings.catalog_path}")
    with settings.catalog_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    pathways_raw: dict[str, Any] = {}
    career_raw: dict[str, Any] = {}
    if settings.pathways_path.exists():
        with settings.pathways_path.open("r", encoding="utf-8") as handle:
            pathways_raw = json.load(handle)
    if settings.career_profiles_path.exists():
        with settings.career_profiles_path.open("r", encoding="utf-8") as handle:
            career_raw = json.load(handle)
    return ComputerCatalog(raw, pathways_raw, career_raw)
