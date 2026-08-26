from app.domain.assessment import score_structured_answer
from app.domain.career import build_revision
from app.domain.catalog import get_catalog
from app.domain.content import ContentEngine
from app.domain.evaluation import get_frozen_evaluation
from app.domain.grounding import build_grounded_enhancement, verify_atomic_claims
from app.domain.knowledge import get_knowledge_engine
from app.domain.profile import ProfileEngine
from app.domain.routing import RouteEngine


def test_all_formal_tracks_have_real_minimum_loop():
    catalog = get_catalog()
    assert len(catalog.tracks) == 16
    for track in catalog.tracks:
        assert len(track["skills"]) >= 3
        assert track["project"]["deliverables"]
        assert track["project"]["acceptance"]
        assert len(track["sources"]) >= 2
        graph = catalog.skill_graph(track["code"])
        assert graph["nodes"]
        assert graph["edges"]
        assert len(catalog.diagnostic(track["code"])) == len(track["skills"])


def test_all_pathway_topics_expand_to_ordered_atomic_learning_units():
    catalog = get_catalog()
    assert len(catalog.pathways) == 29
    for pathway in catalog.pathways:
        assert len(pathway["learning_sources"]) >= 2
        assert all(source["url"].startswith("https://") for source in pathway["learning_sources"])
        for stage in pathway["stages"]:
            assert len(stage["learning_units"]) == len(stage["topics"])
            for unit in stage["learning_units"]:
                assert len(unit["knowledge_points"]) >= 4
                assert len(unit["learning_steps"]) >= 4
                assert len(unit["validation"]) >= 2
                assert len(unit["search_terms"]) >= 3
                assert unit["practice"].startswith("练习：")
                assert "原理说明、最小可运行示例" not in unit["learning_action"]

    frontend = catalog.get_pathway("react-frontend")
    html = frontend["stages"][0]["learning_units"][0]
    joined = "；".join(html["knowledge_points"])
    for expected in ["Live Server", "HTML 注释", "块级/行内", "图像", "音视频", "列表", "Markdown"]:
        assert expected in joined
    css = frontend["stages"][0]["learning_units"][2]
    assert "相邻兄弟（+）" in "；".join(css["knowledge_points"])


def test_composed_route_assigns_concrete_tasks_to_specific_weeks():
    route = get_catalog().compose_pathways(["agent-fullstack"], weekly_hours=8)
    assert route["phases"]
    for phase in route["phases"]:
        for task in phase["tasks"]:
            assert phase["week_start"] <= task["scheduled_week"] <= phase["week_end"]
            assert task["week_label"] == f"第 {task['scheduled_week']} 周"
            assert task["estimated_hours"] >= 0.5
            assert task["knowledge_points"]
            assert task["practice"]
            assert task["failure_drill"]
            assert task["evidence_required"]
            assert task["acceptance"]

    first_week = [task for task in route["phases"][0]["tasks"] if task["scheduled_week"] == 1]
    assert {task["title"] for task in first_week} == {"Python", "异步编程"}
    python_points = "；".join(first_week[0]["knowledge_points"])
    assert any(term in python_points for term in ["虚拟环境", ".venv"])
    assert "断点" in python_points


def test_blocked_revision_uses_the_current_topic_for_specific_remediation():
    phase = get_catalog().compose_pathways(["agent-fullstack"])["phases"][0]
    revised, _, _ = build_revision([phase], "blocked")
    support = revised[0]["tasks"][0]
    assert support["priority"] == "remediation"
    assert support["title"].startswith("回补前置：")
    assert support["knowledge_points"]
    assert support["failure_drill"]
    assert "原理说明、最小示例" not in support["learning_action"]


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
    results = RouteEngine().compare(profile, ["web_frontend", "backend", "agent_engineering"])
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
    evidence = get_knowledge_engine().search("API 事务 并发 可观测", track_code="backend", top_k=10)
    engine = ContentEngine()
    candidate_a = engine.generate_rigorous("backend", "完成可靠 API 项目", profile, route, evidence)
    candidate_b = engine.generate_project_first(
        "backend", "完成可靠 API 项目", profile, route, evidence
    )
    result = engine.arbitrate(candidate_a, candidate_b, evidence, profile)
    assert result["quality_metrics"]["knowledge_coverage"] == 1
    assert result["quality_metrics"]["citation_coverage"] == 1
    assert result["quality_metrics"]["grounding_coverage"] == 1
    assert result["quality_metrics"]["hallucination_risk"] == 0
    assert result["quality_metrics"]["prerequisite_violations"] == 0
    assert result["final_output"]["practice"]["steps"]


def test_claim_grounding_rejects_fake_citations_numbers_and_unquoted_claims():
    evidence = [
        {
            "chunk_id": "kb:fastapi-testing",
            "title": "FastAPI 测试",
            "content": "使用 TestClient 验证 API 正常路径与失败路径。",
            "source_title": "FastAPI Documentation",
        }
    ]
    payload = {
        "atomic_claims": [
            {
                "kind": "tip",
                "text": "使用 TestClient 验证 API 正常路径与失败路径。",
                "citation_ids": ["kb:fastapi-testing"],
                "evidence_quote": "使用 TestClient 验证 API 正常路径与失败路径。",
            },
            {
                "kind": "summary",
                "text": "FastAPI 3.0 可把性能提升 80%。",
                "citation_ids": ["kb:fastapi-testing"],
                "evidence_quote": "使用 TestClient 验证 API 正常路径与失败路径。",
            },
            {
                "kind": "tip",
                "text": "这条陈述没有模型提供的引用。",
                "citation_ids": [],
                "evidence_quote": "",
            },
        ]
    }
    audit = verify_atomic_claims(payload, evidence)
    released = build_grounded_enhancement(payload, audit)
    assert audit["supported_claims"] == 1
    assert audit["rejected_claims"] == 2
    assert released["project_tips"] == ["使用 TestClient 验证 API 正常路径与失败路径。"]
    assert all(item["status"] == "supported" for item in released["atomic_claims"])


def test_structured_assessment_requires_distinct_reasoning_and_evidence_for_profile_update():
    repeated = "测试异常取舍实现步骤，因为测试异常取舍实现步骤。" * 4
    gaming = score_structured_answer(
        {
            "action": repeated,
            "validation": repeated,
            "boundary": repeated,
            "reasoning": repeated,
            "evidence": [],
        }
    )
    assert gaming["eligible_for_profile_update"] is False
    assert "duplicated_sections" in gaming["integrity_flags"]

    verified = score_structured_answer(
        {
            "action": "步骤 1：实现 API 模块；步骤 2：输入样例数据；步骤 3：检查输出并提交增量。",
            "validation": "运行 pytest 并断言状态码和输出字段，正常与错误样例全部通过。",
            "boundary": "构造权限错误和超时场景，通过日志定位后重试或回滚并检查恢复。",
            "reasoning": "选择分层模块而不用单文件方案，因为维护和测试成本更低；代价是初期结构更多。",
            "evidence": [
                {"type": "test", "value": "pytest -q：10 passed，包含权限错误与超时恢复用例。"},
                {"type": "commit", "value": "a1b2c3d4"},
            ],
        }
    )
    assert verified["score"] >= 7
    assert verified["eligible_for_profile_update"] is True
    assert verified["evidence_level"] in {"moderate", "strong"}


def test_frozen_evaluation_covers_six_personas_sixty_tasks_and_all_tracks():
    summary = get_frozen_evaluation().validation
    assert summary["profile_count"] == 6
    assert summary["task_count"] == 64
    assert summary["track_count"] == 16
    assert set(summary["cluster_distribution"]) == {"software", "ai", "systems"}
    assert all(count == 4 for count in summary["tasks_per_track"].values())
