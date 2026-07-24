def unwrap(response, expected=200):
    assert response.status_code == expected, response.text
    payload = response.json()
    assert payload["code"] == 0
    return payload["data"]


def test_complete_human_learning_loop(client, auth_headers, admin_headers):
    profile = unwrap(
        client.put(
            "/api/v1/profiles/me/analyze",
            headers=auth_headers,
            json={
                "background": "计算机专业大三，做过 Python API 项目",
                "learning_goals": ["成为 Agent 全栈工程师"],
                "preferences": ["后端", "LLM", "多智能体"],
                "weekly_hours": 12,
                "learning_style": "practice_first",
                "self_assessment": {
                    "core.programming": 72,
                    "core.database": 62,
                    "core.network": 55,
                    "core.git": 70,
                },
                "diagnostic_results": {"agent.workflow": 48, "be.api": 65},
            },
        )
    )
    # 首次创建画像时版本从 1 开始；后续诊断与评测才递增版本。
    assert profile["version"] == 1
    assert len(profile["dimension_scores"]) == 6

    tree = unwrap(client.get("/api/v1/tracks/tree"))
    assert len(tree["clusters"]) == 3
    assert sum(len(cluster["tracks"]) for cluster in tree["clusters"]) == 15

    compared = unwrap(
        client.post(
            "/api/v1/tracks/compare",
            headers=auth_headers,
            json={
                "track_codes": [
                    "backend",
                    "fullstack",
                    "llm_application",
                    "agent_engineering",
                ]
            },
        )
    )
    assert len(compared["items"]) == 4
    selected = unwrap(
        client.post(
            "/api/v1/tracks/select",
            headers=auth_headers,
            json={"track_code": "agent_engineering"},
        )
    )
    assert selected["track"]["code"] == "agent_engineering"

    pending_document = unwrap(
        client.post(
            "/api/v1/knowledge/documents",
            headers=auth_headers,
            json={
                "track_code": "agent_engineering",
                "title": "Agent 状态机工程实践",
            "content": (
                "状态机必须显式定义输入、输出、条件路由、超时、恢复和终止条件。"
                "工具调用需要权限边界、结构化错误和审计事件。"
            ),
                "source_url": "https://example.com/agent-state-machine",
                "license_type": "CC-BY-4.0",
                "content_version": "2026.07",
            },
        )
    )
    assert pending_document["status"] == "pending"
    reviewed = unwrap(
        client.put(
            f"/api/v1/knowledge/documents/{pending_document['id']}/review",
            headers=admin_headers,
            json={"status": "approved", "review_notes": "来源、版本与内容范围完整"},
        )
    )
    assert reviewed["status"] == "approved"
    search = unwrap(
        client.get(
            "/api/v1/knowledge/search",
            params={"q": "Agent 状态机 超时 恢复", "track_code": "agent_engineering"},
        )
    )
    assert any(item["chunk_id"].startswith("contrib:") for item in search["items"])

    session = unwrap(
        client.post(
            "/api/v1/sessions",
            headers=auth_headers,
            json={
                "track_code": "agent_engineering",
                "goal": "完成一个可评测、可恢复的多智能体项目",
                "topic": "状态图、工具调用与轨迹评测",
                "source_mode": "knowledge_only",
            },
        )
    )
    assert session["status"] == "completed"
    assert len(session["events"]) == 6
    assert session["quality_metrics"]["knowledge_coverage"] >= 0.9
    assert session["quality_metrics"]["citation_coverage"] >= 0.95

    resources = unwrap(client.get("/api/v1/resources", headers=auth_headers))["items"]
    types = {item["resource_type"] for item in resources}
    assert {"lecture", "practice", "assessment", "plan"} <= types

    practice = next(item for item in resources if item["resource_type"] == "practice")
    practice_detail = unwrap(
        client.get(f"/api/v1/resources/{practice['id']}", headers=auth_headers)
    )
    step_ids = [item["id"] for item in practice_detail["content"]["steps"]]
    practice_result = unwrap(
        client.post(
            f"/api/v1/practice/{practice['id']}/submit",
            headers=auth_headers,
            json={
                "completed_step_ids": step_ids,
                "evidence": [f"commit-{index}" for index in range(len(step_ids))],
            },
        )
    )
    assert practice_result["passed"] is True

    assessment = next(item for item in resources if item["resource_type"] == "assessment")
    assessment_detail = unwrap(
        client.get(f"/api/v1/resources/{assessment['id']}", headers=auth_headers)
    )
    answers = {
        question["id"]: (
            "1. 实现最小任务；2. 编写测试验证正常与边界输入；"
            "3. 记录运行指标；4. 构造失败样例并说明定位方法与通过标准。"
        )
        for question in assessment_detail["content"]["questions"]
    }
    assessment_result = unwrap(
        client.post(
            f"/api/v1/assessments/{assessment['id']}/submit",
            headers=auth_headers,
            json={"answers": answers},
        )
    )
    assert assessment_result["passed"] is True
    assert assessment_result["skill_updates"]

    feedback = unwrap(
        client.post(
            f"/api/v1/sessions/{session['id']}/feedback",
            headers=auth_headers,
            json={"feedback_type": "too_hard", "content": {}},
        )
    )
    assert feedback["adjustment"]["plan_action"] == "split_current_phase"
    assert feedback["adjustment"]["plan_version"] >= 2

    plan = unwrap(client.get("/api/v1/plans/current", headers=auth_headers))
    task_ids = [
        f"{phase['id']}:{skill}"
        for phase in plan["phases"]
        for skill in phase.get("skills", [])
    ][:2]
    checkin = unwrap(
        client.post(
            f"/api/v1/plans/{plan['id']}/checkin",
            headers=auth_headers,
            json={"completed_task_ids": task_ids},
        )
    )
    assert checkin["progress"] >= 0

    report = unwrap(client.get("/api/v1/reports/latest", headers=auth_headers))
    assert report["blind_spots"]
    assert report["quality_metrics"]
    assert report["route"]["track_code"] == "agent_engineering"

    agents = unwrap(client.get("/api/v1/agents/status", headers=auth_headers))
    assert len(agents["items"]) == 6
    assert all(item["status"] == "completed" for item in agents["items"])

    messages = unwrap(client.get("/api/v1/messages", headers=auth_headers))["items"]
    persisted = next(item for item in messages if not item["id"].startswith("onboarding:"))
    marked = unwrap(
        client.put(f"/api/v1/messages/{persisted['id']}/read", headers=auth_headers)
    )
    assert marked["read"] is True

    exported = unwrap(client.get("/api/v1/auth/data-export", headers=auth_headers))
    assert exported["user"]["email"] == "demo@gongxue.local"
    assert exported["sessions"]
    assert exported["resources"]
    assert "knowledge_contributions" in exported
    assert "notifications" in exported
    assert "external_services" in exported

    dashboard = unwrap(client.get("/api/v1/dashboard", headers=auth_headers))
    assert dashboard["resources"]["total"] >= 4
    assert dashboard["latest_session"]["status"] == "completed"

    evaluation_summary = unwrap(
        client.get("/api/v1/evaluation/summary", headers=auth_headers)
    )
    assert evaluation_summary["dataset"]["task_count"] == 60
    assert evaluation_summary["can_run"] is False

    evaluation_run = unwrap(
        client.post("/api/v1/evaluation/run", headers=admin_headers)
    )
    assert evaluation_run["system"]["status"] == "completed"
    assert evaluation_run["system"]["metrics"]["task_success_rate"] >= 0.95
    assert all(row["status"] == "not_run" for row in evaluation_run["baselines"])


def test_account_deletion_removes_login_and_profile_data(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "username": "待删除学习者",
            "email": "delete-me@test.local",
            "password": "delete-me-12345",
        },
    )
    assert registered.status_code == 201
    token = registered.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    analyzed = client.put(
        "/api/v1/profiles/me/analyze",
        headers=headers,
        json={
            "background": "隐私删除回归账号",
            "learning_goals": ["测试数据删除"],
            "preferences": ["后端"],
            "weekly_hours": 6,
            "learning_style": "balanced",
            "self_assessment": {"core.programming": 40},
            "diagnostic_results": {"core.programming": 45},
        },
    )
    assert analyzed.status_code == 200

    deleted = client.request(
        "DELETE",
        "/api/v1/auth/me",
        headers=headers,
        json={"current_password": "delete-me-12345", "confirmation": "DELETE"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True

    login_again = client.post(
        "/api/v1/auth/login",
        json={"account": "delete-me@test.local", "password": "delete-me-12345"},
    )
    assert login_again.status_code == 401
