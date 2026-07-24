from app.domain.catalog import get_catalog
from app.domain.content import ContentEngine
from app.domain.evaluation import get_frozen_evaluation
from app.domain.knowledge import get_knowledge_engine
from app.domain.profile import ProfileEngine
from app.domain.routing import RouteEngine


def test_all_formal_tracks_have_real_minimum_loop():
    catalog = get_catalog()
    assert len(catalog.tracks) == 15
    for track in catalog.tracks:
        assert len(track["skills"]) >= 3
        assert track["project"]["deliverables"]
        assert track["project"]["acceptance"]
        assert len(track["sources"]) >= 2
        graph = catalog.skill_graph(track["code"])
        assert graph["nodes"]
        assert graph["edges"]
        assert len(catalog.diagnostic(track["code"])) == len(track["skills"])


def test_profile_and_route_comparison_are_evidence_driven():
    profile = ProfileEngine().analyze(
        {
            "background": "计算机专业，有 Python 后端项目经验",
            "learning_goals": ["成为 Agent 全栈工程师"],
            "preferences": ["LLM", "后端", "智能体"],
            "weekly_hours": 14,
            "learning_style": "practice_first",
            "self_assessment": {"core.programming": 75, "core.database": 65},
            "diagnostic_results": {"agent.workflow": 60, "be.api": 70},
        }
    )
    results = RouteEngine().compare(
        profile, ["web_frontend", "backend", "agent_engineering"]
    )
    assert results[0]["track_code"] in {"backend", "agent_engineering"}
    assert all(item["skill_gaps"] for item in results)
    assert all(item["counterfactual"]["if_weekly_hours_plus_4"] >= 4 for item in results)


def test_retrieval_generation_and_arbitration_have_citations():
    profile = ProfileEngine().analyze(
        {
            "weekly_hours": 10,
            "learning_style": "balanced",
            "diagnostic_results": {"core.programming": 60},
        },
        "backend",
    )
    route = RouteEngine().compare(profile, ["backend"])[0]
    evidence = get_knowledge_engine().search(
        "API 事务 并发 可观测", track_code="backend", top_k=10
    )
    engine = ContentEngine()
    candidate_a = engine.generate_rigorous(
        "backend", "完成可靠 API 项目", profile, route, evidence
    )
    candidate_b = engine.generate_project_first(
        "backend", "完成可靠 API 项目", profile, route, evidence
    )
    result = engine.arbitrate(candidate_a, candidate_b, evidence, profile)
    assert result["quality_metrics"]["knowledge_coverage"] == 1
    assert result["quality_metrics"]["citation_coverage"] == 1
    assert result["quality_metrics"]["prerequisite_violations"] == 0
    assert result["final_output"]["practice"]["steps"]


def test_frozen_evaluation_covers_six_personas_sixty_tasks_and_all_tracks():
    summary = get_frozen_evaluation().validation
    assert summary["profile_count"] == 6
    assert summary["task_count"] == 60
    assert summary["track_count"] == 15
    assert set(summary["cluster_distribution"]) == {"software", "ai", "systems"}
    assert all(count == 4 for count in summary["tasks_per_track"].values())
