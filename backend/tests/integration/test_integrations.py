import json

from app.infrastructure.external_gateway import GatewayError, LLMResult


def unwrap(response):
    assert response.status_code < 400, response.text
    return response.json()["data"]


def test_byok_full_mode_masking_usage_and_safe_degradation(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(
        "app.infrastructure.external_gateway.validate_external_url",
        lambda url, resolve_dns=True: url.rstrip("/"),
    )

    def fake_search(self, query, top_k=8):
        return [
            {
                "chunk_id": "web:1",
                "title": "FastAPI 官方测试指南",
                "content": "使用依赖覆盖和 TestClient 验证 API 边界与失败路径。",
                "source_title": "FastAPI Documentation",
                "source_url": "https://fastapi.tiangolo.com/tutorial/testing/",
                "content_version": "retrieved-live",
                "credibility": 0.9,
                "source_layer": "web",
            }
        ]

    def fake_complete(self, messages, max_tokens=None, operation="generation"):
        return LLMResult(
            content=json.dumps(
                {
                    "personalized_summary": "优先完成状态图最小闭环，再提交失败恢复证据。",
                    "project_tips": ["为工具调用增加超时测试", "保存结构化执行事件"],
                    "caution": "不要跳过前置依赖。",
                    "citation_ids": [],
                },
                ensure_ascii=False,
            ),
            prompt_tokens=120,
            completion_tokens=80,
            model="mock-computer-model",
            provider="openai_compatible",
            estimated_cost=0.002,
        )

    monkeypatch.setattr(
        "app.infrastructure.external_gateway.WebSearchGateway.search", fake_search
    )
    monkeypatch.setattr(
        "app.infrastructure.external_gateway.OpenAICompatibleGateway.complete",
        fake_complete,
    )

    llm_secret = "sk-test-secret-never-return-9876"
    search_secret = "search-secret-never-return-5432"
    llm = unwrap(
        client.post(
            "/api/v1/integrations/providers",
            headers=auth_headers,
            json={
                "service_type": "llm",
                "provider": "openai_compatible",
                "label": "测试模型",
                "base_url": "https://mock-llm.example/v1",
                "model": "mock-computer-model",
                "api_key": llm_secret,
                "storage_mode": "temporary",
                "max_tokens_per_request": 2048,
                "daily_budget": 10,
                "timeout_seconds": 10,
                "input_price_per_million": 1,
                "output_price_per_million": 2,
                "daily_request_limit": 20,
                "enabled": True,
            },
        )
    )
    search = unwrap(
        client.post(
            "/api/v1/integrations/providers",
            headers=auth_headers,
            json={
                "service_type": "search",
                "provider": "custom",
                "label": "测试搜索",
                "base_url": "https://mock-search.example",
                "model": "",
                "api_key": search_secret,
                "storage_mode": "temporary",
                "max_tokens_per_request": 512,
                "daily_budget": 10,
                "timeout_seconds": 10,
                "input_price_per_million": 0,
                "output_price_per_million": 0,
                "daily_request_limit": 20,
                "enabled": True,
            },
        )
    )
    serialized_configs = json.dumps([llm, search], ensure_ascii=False)
    assert llm_secret not in serialized_configs
    assert search_secret not in serialized_configs
    assert llm["masked_key"].endswith("9876")
    assert search["masked_key"].endswith("5432")
    assert llm["key_available"] is True

    session = unwrap(
        client.post(
            "/api/v1/sessions",
            headers=auth_headers,
            json={
                "track_code": "agent_engineering",
                "goal": "完成带来源审计的多智能体项目",
                "topic": "状态图、工具调用和恢复测试",
                "source_mode": "full",
                "llm_config_id": llm["id"],
                "search_config_id": search["id"],
            },
        )
    )
    assert session["status"] == "completed"
    assert session["source_audit"]["effective_mode"] == "full"
    assert session["source_audit"]["fallbacks"] == []
    assert any(item.get("source_layer") == "web" for item in session["evidence"])
    enhancement = session["final_output"]["lecture"]["ai_enhancement"]
    assert enhancement["ai_generated"] is True
    assert enhancement["model"] == "mock-computer-model"
    serialized_session = json.dumps(session, ensure_ascii=False)
    assert llm_secret not in serialized_session
    assert search_secret not in serialized_session

    usage = unwrap(
        client.get("/api/v1/integrations/usage", headers=auth_headers)
    )["items"]
    usage_by_id = {item["config"]["id"]: item["today"] for item in usage}
    assert usage_by_id[llm["id"]]["requests"] == 1
    assert usage_by_id[search["id"]]["requests"] == 1

    def failed_search(self, query, top_k=8):
        raise GatewayError("provider_error", "模拟搜索故障")

    def failed_complete(self, messages, max_tokens=None, operation="generation"):
        raise GatewayError("provider_error", "模拟模型故障")

    monkeypatch.setattr(
        "app.infrastructure.external_gateway.WebSearchGateway.search", failed_search
    )
    monkeypatch.setattr(
        "app.infrastructure.external_gateway.OpenAICompatibleGateway.complete",
        failed_complete,
    )
    degraded = unwrap(
        client.post(
            "/api/v1/sessions",
            headers=auth_headers,
            json={
                "track_code": "agent_engineering",
                "goal": "验证外部服务故障时核心功能保持可用",
                "topic": "降级与恢复",
                "source_mode": "full",
                "llm_config_id": llm["id"],
                "search_config_id": search["id"],
            },
        )
    )
    assert degraded["status"] == "completed"
    assert degraded["source_audit"]["effective_mode"] == "knowledge_only"
    assert degraded["source_audit"]["fallback_triggered"] is True
    assert len(degraded["source_audit"]["fallbacks"]) == 2


def test_provider_config_isolated_between_users(client, auth_headers):
    config = unwrap(
        client.post(
            "/api/v1/integrations/providers",
            headers=auth_headers,
            json={
                "service_type": "llm",
                "provider": "openai_compatible",
                "label": "隔离验证模型",
                "base_url": "https://isolation.example/v1",
                "model": "isolated-model",
                "api_key": "sk-isolation-owner-key",
                "storage_mode": "temporary",
            },
        )
    )
    other = client.post(
        "/api/v1/auth/register",
        json={
            "username": "隔离测试用户",
            "email": "isolated-user@test.local",
            "password": "isolated-user-12345",
        },
    )
    assert other.status_code == 201
    other_headers = {
        "Authorization": f"Bearer {other.json()['data']['access_token']}"
    }
    visible = unwrap(
        client.get("/api/v1/integrations/providers", headers=other_headers)
    )["items"]
    assert all(item["id"] != config["id"] for item in visible)
    forbidden = client.post(
        f"/api/v1/integrations/providers/{config['id']}/temporary-key",
        headers=other_headers,
        json={"api_key": "sk-should-not-write"},
    )
    assert forbidden.status_code == 404


def test_switching_secret_storage_requires_key_and_service_can_be_disabled(
    client, auth_headers
):
    config = unwrap(
        client.post(
            "/api/v1/integrations/providers",
            headers=auth_headers,
            json={
                "service_type": "llm",
                "provider": "deepseek",
                "label": "密钥模式边界测试",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "api_key": "sk-temporary-storage-key",
                "storage_mode": "temporary",
            },
        )
    )

    missing_key = client.put(
        f"/api/v1/integrations/providers/{config['id']}",
        headers=auth_headers,
        json={
            "service_type": "llm",
            "provider": "deepseek",
            "label": "密钥模式边界测试",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "api_key": "",
            "storage_mode": "encrypted",
        },
    )
    assert missing_key.status_code == 422
    assert "重新输入 API Key" in missing_key.json()["detail"]

    disabled = unwrap(
        client.put(
            f"/api/v1/integrations/providers/{config['id']}",
            headers=auth_headers,
            json={
                "service_type": "llm",
                "provider": "deepseek",
                "label": "密钥模式边界测试",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "api_key": "",
                "storage_mode": "temporary",
                "enabled": False,
            },
        )
    )
    assert disabled["enabled"] is False
    assert disabled["key_available"] is True
