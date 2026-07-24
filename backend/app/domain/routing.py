"""方向匹配与反事实路线比较。"""

from __future__ import annotations

import re
from statistics import mean
from typing import Any

from app.domain.catalog import ComputerCatalog, get_catalog

TRACK_ALIASES = {
    "web_frontend": ["前端", "web frontend", "javascript", "typescript"],
    "backend": ["后端", "backend", "服务端"],
    "fullstack": ["全栈", "fullstack", "full stack"],
    "mobile": ["移动端", "跨端", "android", "ios"],
    "quality_engineering": ["质量工程", "软件测试", "自动化测试"],
    "devops": ["devops", "云原生", "持续交付", "sre"],
    "algorithms": ["算法", "数据结构", "复杂度"],
    "machine_learning": ["机器学习", "machine learning", "mlops"],
    "llm_application": ["llm", "大模型", "rag", "提示工程"],
    "agent_engineering": ["agent", "智能体", "多智能体"],
    "embedded_iot": ["嵌入式", "物联网", "单片机"],
    "operating_systems": ["操作系统", "内核", "系统编程"],
    "network_security": ["网络安全", "安全攻防", "应急响应"],
    "database_systems": ["数据库内核", "查询优化", "事务系统"],
    "data_engineering": ["数据工程", "数据仓库", "批流处理"],
    "uiux": ["ui", "ux", "交互设计", "用户研究", "设计系统", "figma"],
}


def _text_tokens(values: list[str]) -> set[str]:
    text = " ".join(values).lower()
    latin = set(re.findall(r"[a-z0-9+#.]+", text))
    chinese = {text[index : index + 2] for index in range(max(0, len(text) - 1))}
    return latin | chinese


class RouteEngine:
    def __init__(self, catalog: ComputerCatalog | None = None):
        self.catalog = catalog or get_catalog()

    def compare(
        self, profile: dict[str, Any], track_codes: list[str] | None = None
    ) -> list[dict[str, Any]]:
        tracks = (
            [self.catalog.get_track(code) for code in track_codes]
            if track_codes
            else self.catalog.tracks
        )
        interest_values = (
            profile.get("preferences", [])
            + profile.get("goals", [])
            + [profile.get("background", "")]
        )
        interests = _text_tokens(interest_values)
        interest_text = " ".join(str(value) for value in interest_values).lower()
        skill_scores = profile.get("skill_scores", {})
        weekly_hours = max(1, int(profile.get("weekly_hours", 8)))
        results = []

        for track in tracks:
            graph = self.catalog.skill_graph(track["code"])
            required_codes = [node["id"] for node in graph["nodes"]]
            readiness_scores = [skill_scores.get(code, 0) for code in required_codes]
            observed = [score for score in readiness_scores if score > 0]
            readiness = mean(observed) if observed else 20.0

            keyword_hits = []
            for keyword in track["keywords"]:
                key_tokens = _text_tokens([keyword])
                if interests & key_tokens or keyword.lower() in interest_text:
                    keyword_hits.append(keyword)
            # 路线名/岗位名是用户最明确的意图证据，不能因为目录关键词未重复
            # “前端”“后端”等标签而被弱化；同时排除“开发、工程、系统”等泛词。
            generic_tokens = {"开发", "工程", "系统", "应用", "能力", "方向"}
            label_tokens = _text_tokens(
                [track["name"], track["role"], track["code"].replace("_", " ")]
            ) - generic_tokens
            explicit_alias_hit = any(
                alias.lower() in interest_text
                for alias in TRACK_ALIASES.get(track["code"], [])
            )
            explicit_label_hit = explicit_alias_hit or bool(interests & label_tokens)
            interest = min(
                100.0,
                35.0
                + len(keyword_hits) * 16.0
                + (45.0 if explicit_alias_hit else (20.0 if explicit_label_hit else 0.0)),
            )

            average_difficulty = mean(skill["difficulty"] for skill in track["skills"])
            feasibility = max(25.0, min(100.0, 45 + weekly_hours * 3.5 - average_difficulty * 6))
            score = round(readiness * 0.42 + interest * 0.38 + feasibility * 0.20, 1)

            gaps = sorted(
                [
                    {
                        "skill_code": skill["code"],
                        "name": skill["name"],
                        "current": skill_scores.get(skill["code"], 0),
                        "target": 75,
                        "gap": max(0, round(75 - skill_scores.get(skill["code"], 0), 1)),
                        "difficulty": skill["difficulty"],
                    }
                    for skill in track["skills"]
                ],
                key=lambda item: (-item["gap"], item["difficulty"]),
            )
            workload = sum(item["gap"] / 12 * item["difficulty"] for item in gaps)
            estimated_weeks = max(4, round(workload / weekly_hours))
            results.append(
                {
                    "track_code": track["code"],
                    "track_name": track["name"],
                    "role": track["role"],
                    "score": score,
                    "readiness": round(readiness, 1),
                    "interest_fit": round(interest, 1),
                    "feasibility": round(feasibility, 1),
                    "estimated_weeks": estimated_weeks,
                    "matched_keywords": keyword_hits,
                    "explicit_label_hit": explicit_label_hit,
                    "skill_gaps": gaps,
                    "project": track["project"],
                    "pathway_variants": [
                        {
                            "id": item["id"],
                            "name": item["name"],
                            "estimated_months": item["estimated_months"],
                            "difficulty": item["difficulty"],
                            "milestone": item["milestone"],
                            "stage_count": len(item["stages"]),
                        }
                        for item in track.get("pathway_variants", [])
                    ],
                    "why": self._explain(
                        track, readiness, interest, feasibility, keyword_hits, gaps
                    ),
                    "counterfactual": {
                        "if_weekly_hours_plus_4": max(4, round(workload / (weekly_hours + 4))),
                        "highest_cost_skill": gaps[0]["name"] if gaps else "",
                        "switch_cost": round(workload, 1),
                    },
                }
            )

        return sorted(results, key=lambda item: item["score"], reverse=True)

    @staticmethod
    def _explain(
        track: dict,
        readiness: float,
        interest: float,
        feasibility: float,
        hits: list[str],
        gaps: list[dict],
    ) -> list[str]:
        reasons = [
            f"当前相关基础匹配度 {readiness:.0f} 分",
            f"按每周投入估算的可行性 {feasibility:.0f} 分",
        ]
        if hits:
            reasons.append(f"目标描述命中兴趣关键词：{'、'.join(hits[:3])}")
        else:
            reasons.append("尚未发现强兴趣证据，建议先完成路线体验任务")
        if gaps:
            reasons.append(f"优先补齐：{'、'.join(item['name'] for item in gaps[:2])}")
        reasons.append(f"代表项目：{track['project']['title']}")
        return reasons
