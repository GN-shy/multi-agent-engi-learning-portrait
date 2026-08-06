"""可解释的计算机职业方向决策与组合路线推荐。"""

from __future__ import annotations

import json
import re
from statistics import mean
from typing import Any

from app.domain.catalog import ComputerCatalog, get_catalog

CONTEXT_PREFIX = "@decision_context:"

TRACK_ALIASES = {
    "web_frontend": ["前端", "web frontend", "javascript", "typescript", "vue", "react"],
    "backend": ["后端", "backend", "服务端", "java", "python"],
    "fullstack": ["全栈", "fullstack", "full stack"],
    "mobile": ["移动端", "跨端", "android", "ios", "flutter"],
    "quality_engineering": ["质量工程", "软件测试", "自动化测试"],
    "devops": ["devops", "云原生", "持续交付", "sre"],
    "algorithms": ["算法", "数据结构", "复杂度", "竞赛"],
    "machine_learning": ["机器学习", "machine learning", "算法工程师", "mlops"],
    "llm_application": ["llm", "大模型", "rag", "提示工程"],
    "agent_engineering": ["agent", "智能体", "多智能体"],
    "embedded_iot": ["嵌入式", "物联网", "单片机", "硬件"],
    "operating_systems": ["操作系统", "内核", "系统编程"],
    "network_security": ["网络安全", "安全攻防", "应急响应"],
    "database_systems": ["数据库内核", "查询优化", "事务系统"],
    "data_engineering": ["数据工程", "数据仓库", "数据分析", "流处理"],
    "uiux": ["ui", "ux", "交互设计", "用户研究", "设计系统", "figma"],
}

# 量表维度不是职业结论，只用于识别更愿意长期投入的问题类型。
TRACK_INTEREST_WEIGHTS: dict[str, dict[str, float]] = {
    "web_frontend": {"visual_product": 1, "logic_system": .45, "communication_product": .55},
    "backend": {"logic_system": 1, "automation_reliability": .65, "data_insight": .35},
    "fullstack": {"visual_product": .65, "logic_system": .75, "communication_product": .55},
    "mobile": {"visual_product": .8, "logic_system": .55, "communication_product": .45},
    "quality_engineering": {"security_investigation": .7, "automation_reliability": 1, "logic_system": .55},
    "devops": {"automation_reliability": 1, "logic_system": .75, "security_investigation": .45},
    "algorithms": {"math_model": 1, "logic_system": .8},
    "machine_learning": {"math_model": .9, "data_insight": 1, "logic_system": .45},
    "llm_application": {"data_ai": 1, "communication_product": .65, "logic_system": .45},
    "agent_engineering": {"data_ai": 1, "logic_system": .7, "communication_product": .7},
    "embedded_iot": {"hardware_device": 1, "logic_system": .65, "automation_reliability": .5},
    "operating_systems": {"logic_system": 1, "automation_reliability": .55, "hardware_device": .35},
    "network_security": {"security_investigation": 1, "logic_system": .7},
    "database_systems": {"logic_system": .9, "data_insight": .65, "automation_reliability": .45},
    "data_engineering": {"data_insight": 1, "automation_reliability": .65, "logic_system": .5},
    "uiux": {"visual_product": 1, "communication_product": 1},
}

GOAL_TRACKS = {
    "internship": {"web_frontend", "backend", "fullstack", "quality_engineering", "mobile"},
    "employment": {"web_frontend", "backend", "fullstack", "quality_engineering", "devops", "data_engineering"},
    "postgraduate": {"algorithms", "operating_systems", "database_systems", "machine_learning", "backend"},
    "competition": {"agent_engineering", "llm_application", "fullstack", "algorithms", "embedded_iot"},
    "portfolio": {"web_frontend", "fullstack", "mobile", "agent_engineering", "uiux"},
    "upskill": {"backend", "devops", "agent_engineering", "data_engineering", "quality_engineering"},
}

CITY_ECOSYSTEMS = {
    "ai": {"北京", "上海", "深圳", "杭州", "合肥", "南京", "武汉"},
    "internet": {"北京", "上海", "深圳", "杭州", "广州", "成都", "南京", "武汉", "厦门", "长沙"},
    "industry": {"深圳", "苏州", "东莞", "无锡", "合肥", "西安", "成都", "重庆", "宁波", "佛山"},
    "finance_enterprise": {"上海", "北京", "深圳", "苏州", "南京", "广州", "天津"},
}

TRACK_CITY_ECOSYSTEMS = {
    "web_frontend": ("internet",), "backend": ("internet", "finance_enterprise"),
    "fullstack": ("internet", "finance_enterprise"), "mobile": ("internet",),
    "uiux": ("internet",), "quality_engineering": ("internet", "industry"),
    "agent_engineering": ("ai", "internet"), "llm_application": ("ai", "internet"),
    "machine_learning": ("ai",), "algorithms": ("ai",),
    "data_engineering": ("ai", "finance_enterprise"), "devops": ("internet", "industry"),
    "embedded_iot": ("industry",), "operating_systems": ("industry",),
    "network_security": ("finance_enterprise", "industry"),
    "database_systems": ("finance_enterprise", "internet"),
}

HIGH_EDUCATION_TRACKS = {"machine_learning", "algorithms", "operating_systems", "database_systems"}


def extract_decision_context(preferences: list[str] | None) -> dict[str, Any]:
    """从兼容旧数据库的隐藏偏好项中读取结构化决策上下文。"""
    for value in preferences or []:
        if isinstance(value, str) and value.startswith(CONTEXT_PREFIX):
            try:
                parsed = json.loads(value[len(CONTEXT_PREFIX):])
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}
    return {}


def visible_preferences(preferences: list[str] | None) -> list[str]:
    return [item for item in (preferences or []) if not str(item).startswith(CONTEXT_PREFIX)]


def _text_tokens(values: list[str]) -> set[str]:
    text = " ".join(values).lower()
    latin = set(re.findall(r"[a-z0-9+#.]+", text))
    chinese = {text[index:index + 2] for index in range(max(0, len(text) - 1))}
    return latin | chinese


def _education_level(value: str) -> int:
    if "硕士" in value or "博士" in value:
        return 4
    if "本科" in value:
        return 3
    if "专科" in value or "大专" in value:
        return 2
    return 1


class RouteEngine:
    def __init__(self, catalog: ComputerCatalog | None = None):
        self.catalog = catalog or get_catalog()

    def compare(self, profile: dict[str, Any], track_codes: list[str] | None = None) -> list[dict[str, Any]]:
        tracks = [self.catalog.get_track(code) for code in track_codes] if track_codes else self.catalog.tracks
        context = extract_decision_context(profile.get("preferences", []))
        visible = visible_preferences(profile.get("preferences", []))
        interest_values = visible + profile.get("goals", []) + [profile.get("background", "")]
        interests = _text_tokens(interest_values)
        interest_text = " ".join(str(value) for value in interest_values).lower()
        skill_scores = profile.get("skill_scores", {})
        weekly_hours = max(1, int(profile.get("weekly_hours", 8)))
        selected_directions = set(context.get("directions", []))
        goal_codes = set(context.get("goal_codes", []))
        scale = context.get("interest_scale", {}) if isinstance(context.get("interest_scale"), dict) else {}
        results = []

        for track in tracks:
            graph = self.catalog.skill_graph(track["code"])
            required_codes = [node["id"] for node in graph["nodes"]]
            observed = [skill_scores.get(code, 0) for code in required_codes if skill_scores.get(code, 0) > 0]
            readiness = mean(observed) if observed else 20.0

            keyword_hits = [keyword for keyword in track["keywords"] if interests & _text_tokens([keyword]) or keyword.lower() in interest_text]
            alias_hit = any(alias.lower() in interest_text for alias in TRACK_ALIASES.get(track["code"], []))
            scale_fit = self._scale_fit(track["code"], scale)
            if track["code"] in selected_directions:
                interest = 96.0
                interest_basis = "你主动选择了该方向"
            elif scale:
                interest = min(100.0, scale_fit * .8 + (12 if alias_hit else 0) + min(8, len(keyword_hits) * 2))
                interest_basis = "职业倾向量表与目标描述"
            else:
                interest = min(100.0, 42 + (35 if alias_hit else 0) + len(keyword_hits) * 8)
                interest_basis = "目标和偏好关键词（尚未完成量表）"

            goal_fit = self._goal_fit(track["code"], goal_codes)
            education_fit, education_note = self._education_fit(track["code"], context.get("education", ""))
            city_fit, city_note = self._city_fit(track["code"], context.get("city", ""))
            average_difficulty = mean(skill["difficulty"] for skill in track["skills"])
            feasibility = max(25.0, min(100.0, 45 + weekly_hours * 3.5 - average_difficulty * 6))
            score = round(
                readiness * .25 + interest * .25 + goal_fit * .15
                + education_fit * .10 + city_fit * .10 + feasibility * .15,
                1,
            )

            gaps = sorted([
                {
                    "skill_code": skill["code"], "name": skill["name"],
                    "current": skill_scores.get(skill["code"], 0), "target": 75,
                    "gap": max(0, round(75 - skill_scores.get(skill["code"], 0), 1)),
                    "difficulty": skill["difficulty"],
                }
                for skill in track["skills"]
            ], key=lambda item: (-item["gap"], item["difficulty"]))
            workload = sum(item["gap"] / 12 * item["difficulty"] for item in gaps)
            estimated_weeks = max(4, round(workload / weekly_hours))
            dimensions = {
                "ability": round(readiness, 1), "interest": round(interest, 1),
                "goal": round(goal_fit, 1), "education": round(education_fit, 1),
                "city": round(city_fit, 1), "time": round(feasibility, 1),
            }
            results.append({
                "track_code": track["code"], "track_name": track["name"], "role": track["role"],
                "score": score, "readiness": dimensions["ability"], "interest_fit": dimensions["interest"],
                "feasibility": dimensions["time"], "dimension_scores": dimensions,
                "estimated_weeks": estimated_weeks, "matched_keywords": keyword_hits,
                "explicit_label_hit": alias_hit or track["code"] in selected_directions,
                "skill_gaps": gaps, "project": track["project"],
                "decision_basis": {
                    "interest": interest_basis, "education": education_note, "city": city_note,
                    "city_data_type": "区域产业生态启发式，不是实时岗位数量",
                    "profile_fields": {
                        "education": context.get("education", "未填写"),
                        "city": context.get("city", "未填写"),
                        "goals": list(goal_codes), "weekly_hours": weekly_hours,
                    },
                },
                "confidence": self._confidence(profile, context),
                "pathway_variants": [self._pathway_summary(item) for item in track.get("pathway_variants", [])],
                "career_summary": self._career_summary(track),
                "why": self._explain(track, dimensions, keyword_hits, gaps, education_note, city_note),
                "counterfactual": {
                    "if_weekly_hours_plus_4": max(4, round(workload / (weekly_hours + 4))),
                    "highest_cost_skill": gaps[0]["name"] if gaps else "", "switch_cost": round(workload, 1),
                },
            })
        return sorted(results, key=lambda item: item["score"], reverse=True)

    def recommend_pathways(self, profile: dict[str, Any], track_codes: list[str]) -> dict[str, Any]:
        """为用户主动选择的每个主方向选出一个最合适的细分路线并直接组合。"""
        context = extract_decision_context(profile.get("preferences", []))
        goal_codes = set(context.get("goal_codes", []))
        education = context.get("education", "")
        weekly_hours = max(1, int(profile.get("weekly_hours", 8)))
        selected = []
        rationales = []
        for track_code in list(dict.fromkeys(track_codes)):
            track = self.catalog.get_track(track_code)
            ranked = sorted(
                track.get("pathway_variants", []),
                key=lambda item: self._pathway_fit(item, goal_codes, education),
                reverse=True,
            )
            if not ranked:
                continue
            pathway = ranked[0]
            selected.append(pathway["id"])
            rationales.append({
                "track_code": track_code, "track_name": track["name"],
                "pathway_id": pathway["id"], "pathway_name": pathway["name"],
                "reason": self._pathway_reason(pathway, goal_codes, education),
            })
        composed = self.catalog.compose_pathways(selected, weekly_hours=weekly_hours)
        return {
            "pathway_ids": selected,
            "pathways": [self.catalog.pathway_summary(self.catalog.get_pathway(item)) for item in selected],
            "rationales": rationales,
            "composed": composed,
            "message": "已按你主动选择的方向生成组合路线；系统只负责选细分技术栈、补前置和去重，不再对你的方向做伪排名。",
        }

    @staticmethod
    def _scale_fit(track_code: str, scale: dict[str, Any]) -> float:
        weights = TRACK_INTEREST_WEIGHTS.get(track_code, {})
        values = []
        for code, weight in weights.items():
            try:
                answer = max(1.0, min(5.0, float(scale.get(code, 3))))
            except (TypeError, ValueError):
                answer = 3.0
            values.append(((answer - 1) * 20 + 20, weight))
        return sum(value * weight for value, weight in values) / sum(weight for _, weight in values) if values else 60.0

    @staticmethod
    def _goal_fit(track_code: str, goals: set[str]) -> float:
        if not goals:
            return 60.0
        hits = sum(track_code in GOAL_TRACKS.get(goal, set()) for goal in goals)
        return min(100.0, 52 + hits * 20)

    @staticmethod
    def _education_fit(track_code: str, education: str) -> tuple[float, str]:
        if not education:
            return 65.0, "未填写学历，按中性值处理"
        level = _education_level(education)
        if track_code in HIGH_EDUCATION_TRACKS:
            score = {1: 48, 2: 60, 3: 78, 4: 94}[level]
            return float(score), f"{education}；该方向理论门槛较高，学历仅作为入门成本提示，不作为淘汰条件"
        score = {1: 66, 2: 78, 3: 90, 4: 92}[level]
        return float(score), f"{education}；该方向更看重可验证项目与工程能力"

    @staticmethod
    def _city_fit(track_code: str, city: str) -> tuple[float, str]:
        city = str(city or "").strip()
        if not city or "暂不" in city:
            return 70.0, "城市暂未确定，不加分也不扣分"
        ecosystems = TRACK_CITY_ECOSYSTEMS.get(track_code, ())
        if any(any(name in city for name in CITY_ECOSYSTEMS[ecosystem]) for ecosystem in ecosystems):
            return 88.0, f"{city}与该方向常见产业生态较匹配；需在求职前用实时岗位数据复核"
        return 72.0, f"系统没有用静态城市表否定{city}；当前按中性值处理，后续应接入实时岗位检索复核"

    @staticmethod
    def _confidence(profile: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        skill_evidence = sum(float(value or 0) > 0 for value in profile.get("skill_scores", {}).values())
        scale_count = sum(bool(value) for value in context.get("interest_scale", {}).values())
        evidence = skill_evidence + scale_count + sum(bool(context.get(key)) for key in ("education", "city", "goal_codes"))
        level = "高" if evidence >= 18 else "中" if evidence >= 10 else "初始"
        return {"level": level, "evidence_count": evidence, "note": "完成项目、测评或真实岗位检索后会重新计算"}

    @staticmethod
    def _pathway_fit(pathway: dict[str, Any], goals: set[str], education: str) -> float:
        score = float(pathway.get("demand", 3)) * 12 - float(pathway.get("difficulty", 3)) * 3
        text = f"{pathway.get('name', '')} {pathway.get('suitable_for', '')}".lower()
        if goals & {"internship", "employment"}:
            score += float(pathway.get("demand", 3)) * 4
            if "java" in text or "vue" in text:
                score += 6
        if "portfolio" in goals and float(pathway.get("difficulty", 3)) <= 4:
            score += 8
        if "competition" in goals and any(word in text for word in ("agent", "ai", "全栈", "嵌入式")):
            score += 9
        if _education_level(education) < 3 and float(pathway.get("difficulty", 3)) >= 5:
            score -= 10
        return score

    @staticmethod
    def _pathway_reason(pathway: dict[str, Any], goals: set[str], education: str) -> str:
        reasons = [f"需求热度 {pathway.get('demand', 0)}/5", f"难度 {pathway.get('difficulty', 0)}/5"]
        if goals & {"internship", "employment"}:
            reasons.append("优先就业可迁移性与岗位覆盖")
        if "portfolio" in goals or "competition" in goals:
            reasons.append("兼顾可展示作品和交付闭环")
        reasons.append(f"结合{education or '未填写学历'}控制理论起点")
        return "；".join(reasons)

    @staticmethod
    def _pathway_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"], "name": item["name"], "estimated_months": item["estimated_months"],
            "difficulty": item["difficulty"], "milestone": item["milestone"],
            "stage_count": len(item["stages"]),
            "technology_count": sum(len(stage["topics"]) for stage in item["stages"]),
            "career": item.get("career", {}), "salary_scope": item.get("salary_scope", ""),
        }

    @staticmethod
    def _career_summary(track: dict[str, Any]) -> dict[str, Any]:
        pathways = track.get("pathway_variants", [])
        return {
            "roles": list(dict.fromkeys(role for item in pathways for role in item.get("career", {}).get("roles", [])))[:8],
            "salary_ranges": list(dict.fromkeys(item.get("career", {}).get("salary_range", "") for item in pathways if item.get("career", {}).get("salary_range"))),
            "education": list(dict.fromkeys(item.get("career", {}).get("education", {}).get("competitive", "") for item in pathways if item.get("career", {}).get("education", {}).get("competitive"))),
            "salary_scope": next((item.get("salary_scope", "") for item in pathways if item.get("salary_scope")), ""),
        }

    @staticmethod
    def _explain(track: dict, dimensions: dict[str, float], hits: list[str], gaps: list[dict], education_note: str, city_note: str) -> list[str]:
        reasons = [
            f"已有能力证据 {dimensions['ability']:.0f} 分；优先补齐：{'、'.join(item['name'] for item in gaps[:2]) or '暂无'}",
            f"兴趣倾向 {dimensions['interest']:.0f} 分，目标一致性 {dimensions['goal']:.0f} 分" + (f"；命中：{'、'.join(hits[:3])}" if hits else ""),
            f"学历适配 {dimensions['education']:.0f} 分：{education_note}",
            f"城市生态 {dimensions['city']:.0f} 分：{city_note}",
            f"每周投入可行性 {dimensions['time']:.0f} 分；代表项目：{track['project']['title']}",
        ]
        return reasons
