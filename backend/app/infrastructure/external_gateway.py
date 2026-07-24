"""OpenAI-compatible LLM 与搜索服务统一网关。"""

from __future__ import annotations

import ipaddress
import json
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings


class GatewayError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def validate_external_url(url: str, resolve_dns: bool = True) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise GatewayError("invalid_url", "服务地址必须是有效的 HTTPS URL")
    if parsed.username or parsed.password:
        raise GatewayError("invalid_url", "服务地址不得包含用户名或密码")
    if not resolve_dns:
        return url.rstrip("/")
    if settings.allow_private_integration_hosts:
        return url.rstrip("/")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                parsed.hostname,
                parsed.port or 443,
                type=socket.SOCK_STREAM,
            )
        }
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise GatewayError("private_host", "不允许连接内网、回环或保留地址")
    except socket.gaierror as exc:
        raise GatewayError("dns_failed", "服务域名无法解析") from exc
    return url.rstrip("/")


@dataclass
class LLMResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    provider: str
    estimated_cost: float


class OpenAICompatibleGateway:
    def __init__(self, config: dict[str, Any], api_key: str):
        self.config = config
        self.api_key = api_key
        self.base_url = validate_external_url(config["base_url"])

    def test_connection(self) -> LLMResult:
        return self.complete(
            [
                {"role": "system", "content": "Return only the word OK."},
                {"role": "user", "content": "Connection test"},
            ],
            max_tokens=8,
            operation="connection_test",
        )

    def complete(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        operation: str = "generation",
    ) -> LLMResult:
        limit = min(
            int(max_tokens or self.config["max_tokens_per_request"]),
            int(self.config["max_tokens_per_request"]),
        )
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.config["model"],
            "messages": messages,
            "max_tokens": limit,
            "temperature": 0.2,
        }
        try:
            with httpx.Client(
                timeout=float(self.config["timeout_seconds"]),
                follow_redirects=False,
            ) as client:
                response = client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            if response.status_code >= 400:
                safe_message = f"模型服务返回 HTTP {response.status_code}"
                raise GatewayError("provider_error", safe_message)
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage") or {}
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            estimated_cost = (
                prompt_tokens / 1_000_000 * float(self.config["input_price_per_million"])
                + completion_tokens
                / 1_000_000
                * float(self.config["output_price_per_million"])
            )
            return LLMResult(
                content=content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model=str(data.get("model") or self.config["model"]),
                provider=self.config["provider"],
                estimated_cost=round(estimated_cost, 8),
            )
        except GatewayError:
            raise
        except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError) as exc:
            raise GatewayError("connection_failed", "模型服务连接或响应格式无效") from exc


class WebSearchGateway:
    def __init__(self, config: dict[str, Any], api_key: str):
        self.config = config
        self.api_key = api_key
        self.base_url = validate_external_url(config["base_url"])

    def test_connection(self) -> list[dict[str, Any]]:
        return self.search("computer science learning", top_k=1)

    def search(self, query: str, top_k: int = 8) -> list[dict[str, Any]]:
        provider = self.config["provider"]
        try:
            with httpx.Client(
                timeout=float(self.config["timeout_seconds"]),
                follow_redirects=False,
            ) as client:
                if provider == "tavily":
                    response = client.post(
                        f"{self.base_url}/search",
                        json={
                            "api_key": self.api_key,
                            "query": query,
                            "max_results": top_k,
                            "search_depth": "advanced",
                        },
                    )
                elif provider == "serper":
                    response = client.post(
                        f"{self.base_url}/search",
                        headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                        json={"q": query, "num": top_k},
                    )
                else:
                    response = client.post(
                        f"{self.base_url}/search",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={"query": query, "top_k": top_k},
                    )
            if response.status_code >= 400:
                raise GatewayError("provider_error", f"搜索服务返回 HTTP {response.status_code}")
            return self._normalize(response.json(), top_k)
        except GatewayError:
            raise
        except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
            raise GatewayError("connection_failed", "搜索服务连接或响应格式无效") from exc

    def _normalize(self, data: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
        raw_items = data.get("results") or data.get("organic") or data.get("items") or []
        normalized = []
        for index, item in enumerate(raw_items[:top_k]):
            url = item.get("url") or item.get("link")
            title = item.get("title") or f"搜索结果 {index + 1}"
            content = item.get("content") or item.get("snippet") or item.get("description") or ""
            if not url or not content:
                continue
            normalized.append(
                {
                    "chunk_id": f"web:{index + 1}",
                    "title": str(title)[:300],
                    "content": str(content)[:4000],
                    "source_title": str(title)[:300],
                    "source_url": str(url)[:1000],
                    "content_version": "retrieved-live",
                    "credibility": 0.72,
                    "source_layer": "web",
                }
            )
        return normalized
