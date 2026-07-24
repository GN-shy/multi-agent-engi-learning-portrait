"""计算机方向、技能图谱与知识来源目录。"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.core.config import settings


class CatalogError(RuntimeError):
    pass


class ComputerCatalog:
    def __init__(self, raw: dict[str, Any]):
        self.raw = raw
        self.version = raw["version"]
        self.domain = raw["domain"]
        self.clusters = raw["clusters"]
        self.tracks = raw["tracks"]
        self._track_map = {track["code"]: track for track in self.tracks}
        self._skill_map = {skill["code"]: skill for skill in raw["core_skills"]}
        for track in self.tracks:
            for skill in track["skills"]:
                self._skill_map[skill["code"]] = {**skill, "track_code": track["code"]}
        self.validate()

    def validate(self) -> None:
        if len(self.tracks) < 15:
            raise CatalogError("正式计算机路线不得少于 15 条")
        for track in self.tracks:
            required = ("code", "cluster", "name", "description", "skills", "project", "sources")
            missing = [key for key in required if not track.get(key)]
            if missing:
                raise CatalogError(f"路线 {track.get('code')} 缺少字段: {missing}")
            if len(track["skills"]) < 3:
                raise CatalogError(f"路线 {track['code']} 至少需要 3 个专属技能")
            if not track["project"].get("acceptance"):
                raise CatalogError(f"路线 {track['code']} 缺少项目验收标准")
            for skill in track["skills"]:
                for prerequisite in skill.get("prerequisites", []):
                    if prerequisite not in self._skill_map:
                        raise CatalogError(
                            f"技能 {skill['code']} 引用了不存在的前置技能 {prerequisite}"
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
        return ComputerCatalog(json.load(handle))
