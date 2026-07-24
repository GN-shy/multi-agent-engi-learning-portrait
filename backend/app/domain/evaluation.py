"""冻结评测集校验与离线可复现实验。

本模块只报告真实执行结果。需要外部模型的直接 LLM、单 Agent RAG 对照组
在未运行时明确标记为 not_run，禁止用估算值冒充实验数据。
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from functools import lru_cache
from statistics import mean
from time import perf_counter
from typing import Any

from app.core.config import settings
from app.domain.catalog import get_catalog
from app.domain.orchestration import run_workflow
from app.domain.profile import ProfileEngine
from app.domain.routing import RouteEngine


class EvaluationDatasetError(RuntimeError):
    pass


def _read_json(path) -> dict[str, Any]:
    if not path.exists():
        raise EvaluationDatasetError(f"评测数据不存在：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * ratio)))
    return ordered[index]


class FrozenEvaluation:
    def __init__(self):
        self.profile_dataset = _read_json(settings.evaluation_profiles_path)
        self.task_dataset = _read_json(settings.evaluation_tasks_path)
        self.profiles = {row["id"]: row for row in self.profile_dataset["profiles"]}
        self.tasks = self.task_dataset["tasks"]
        self.validation = self._validate()

    def _validate(self) -> dict[str, Any]:
        catalog = get_catalog()
        track_codes = {track["code"] for track in catalog.tracks}
        task_ids = [task["id"] for task in self.tasks]
        if len(self.profiles) < 6:
            raise EvaluationDatasetError("冻结集至少需要 6 类差异化画像")
        if len(self.tasks) < 60:
            raise EvaluationDatasetError("冻结集至少需要 60 个任务")
        if len(task_ids) != len(set(task_ids)):
            raise EvaluationDatasetError("冻结任务 ID 必须唯一")
        unknown_profiles = {
            task["persona_id"] for task in self.tasks if task["persona_id"] not in self.profiles
        }
        unknown_tracks = {
            task["track_code"] for task in self.tasks if task["track_code"] not in track_codes
        }
        if unknown_profiles:
            raise EvaluationDatasetError(f"任务引用未知画像：{sorted(unknown_profiles)}")
        if unknown_tracks:
            raise EvaluationDatasetError(f"任务引用未知路线：{sorted(unknown_tracks)}")

        track_counts = Counter(task["track_code"] for task in self.tasks)
        uncovered = sorted(track_codes - set(track_counts))
        if uncovered:
            raise EvaluationDatasetError(f"正式路线未被评测覆盖：{uncovered}")
        clusters = Counter(task["cluster"] for task in self.tasks)
        task_types = Counter(task["task_type"] for task in self.tasks)
        required_types = {
            "profile_diagnosis",
            "route_decision",
            "content_generation",
            "dependency_audit",
        }
        if not required_types.issubset(task_types):
            raise EvaluationDatasetError("冻结集未覆盖全部核心任务类型")
        return {
            "valid": True,
            "profile_count": len(self.profiles),
            "task_count": len(self.tasks),
            "track_count": len(track_counts),
            "cluster_distribution": dict(clusters),
            "task_type_distribution": dict(task_types),
            "tasks_per_track": dict(sorted(track_counts.items())),
            "profile_dataset_version": self.profile_dataset["version"],
            "task_dataset_version": self.task_dataset["version"],
            "frozen_at": self.task_dataset["frozen_at"],
        }

    @staticmethod
    def _profile_input(persona: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
        return {
            "background": persona["background"],
            "learning_goals": [*persona["learning_goals"], task["goal"]],
            "preferences": persona["preferences"],
            "weekly_hours": persona["weekly_hours"],
            "learning_style": persona["learning_style"],
            "self_assessment": persona["self_assessment"],
            "diagnostic_results": persona["diagnostic_results"],
        }

    def run(self) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        started_all = perf_counter()
        for task in self.tasks:
            started = perf_counter()
            persona = self.profiles[task["persona_id"]]
            profile_input = self._profile_input(persona, task)
            expected = task["expected"]

            if task["task_type"] == "profile_diagnosis":
                profile = ProfileEngine().analyze(profile_input, task["track_code"])
                observed = {
                    "evidence_count": profile["evidence_count"],
                    "blind_spot_count": len(profile["blind_spots"]),
                    "comprehensive_score": profile["comprehensive_score"],
                }
                passed = (
                    observed["evidence_count"] >= expected["min_evidence_count"]
                    and (not expected["requires_blind_spots"] or observed["blind_spot_count"] > 0)
                )
            elif task["task_type"] == "route_decision":
                profile = ProfileEngine().analyze(profile_input)
                ranking = RouteEngine().compare(profile)
                top_codes = [row["track_code"] for row in ranking[: expected["top_k"]]]
                observed = {
                    "target_track": expected["target_track"],
                    "rank": next(
                        (
                            index + 1
                            for index, row in enumerate(ranking)
                            if row["track_code"] == expected["target_track"]
                        ),
                        None,
                    ),
                    "top_tracks": top_codes,
                }
                passed = expected["target_track"] in top_codes
            else:
                state = run_workflow(
                    profile_input,
                    task["track_code"],
                    task["goal"],
                    topic=task["goal"],
                )
                metrics = state["arbitration"]["quality_metrics"]
                observed = {
                    **metrics,
                    "agent_event_count": len(state["events"]),
                    "debate_rounds": state["arbitration"]["debate_rounds"],
                }
                if task["task_type"] == "content_generation":
                    passed = (
                        metrics["knowledge_coverage"] >= expected["min_knowledge_coverage"]
                        and metrics["citation_coverage"] >= expected["min_citation_coverage"]
                    )
                else:
                    passed = (
                        metrics["prerequisite_violations"]
                        <= expected["max_prerequisite_violations"]
                    )

            results.append(
                {
                    "task_id": task["id"],
                    "persona_id": task["persona_id"],
                    "cluster": task["cluster"],
                    "track_code": task["track_code"],
                    "task_type": task["task_type"],
                    "passed": passed,
                    "observed": observed,
                    "duration_ms": round((perf_counter() - started) * 1000, 2),
                }
            )

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in results:
            grouped[row["task_type"]].append(row)
        content_rows = grouped["content_generation"]
        dependency_rows = grouped["dependency_audit"]
        route_rows = grouped["route_decision"]
        durations = [row["duration_ms"] for row in results]
        metrics = {
            "task_success_rate": round(mean(float(row["passed"]) for row in results), 3),
            "route_top3_accuracy": round(mean(float(row["passed"]) for row in route_rows), 3),
            "knowledge_coverage": round(
                mean(row["observed"]["knowledge_coverage"] for row in content_rows), 3
            ),
            "citation_coverage": round(
                mean(row["observed"]["citation_coverage"] for row in content_rows), 3
            ),
            "hallucination_risk_upper_bound": round(
                mean(row["observed"]["hallucination_risk"] for row in content_rows), 3
            ),
            "prerequisite_violation_rate": round(
                sum(row["observed"]["prerequisite_violations"] for row in dependency_rows)
                / max(1, len(dependency_rows) * 4),
                3,
            ),
            "task_p95_ms": round(percentile(durations, 0.95), 2),
            "total_duration_ms": round((perf_counter() - started_all) * 1000, 2),
        }
        targets = {
            "route_top3_accuracy": 0.85,
            "knowledge_coverage": 0.90,
            "citation_coverage": 0.95,
            "hallucination_risk_upper_bound": 0.05,
            "prerequisite_violation_rate": 0.03,
        }
        target_status = {
            key: (
                metrics[key] <= target
                if key in {"hallucination_risk_upper_bound", "prerequisite_violation_rate"}
                else metrics[key] >= target
            )
            for key, target in targets.items()
        }
        return {
            "run_type": "deterministic_offline_replay",
            "dataset": self.validation,
            "system": {
                "name": "工学智链六 Agent",
                "status": "completed",
                "metrics": metrics,
                "targets": targets,
                "target_status": target_status,
            },
            "baselines": [
                {
                    "name": "直接 LLM",
                    "status": "not_run",
                    "reason": "需在 BYOK 阶段用相同模型、参数和冻结知识快照运行，当前不伪造结果",
                },
                {
                    "name": "单 Agent RAG",
                    "status": "not_run",
                    "reason": "需在 BYOK 阶段用相同模型、参数和冻结知识快照运行，当前不伪造结果",
                },
            ],
            "results": results,
        }


@lru_cache
def get_frozen_evaluation() -> FrozenEvaluation:
    return FrozenEvaluation()
