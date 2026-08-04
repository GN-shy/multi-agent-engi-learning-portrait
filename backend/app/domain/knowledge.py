"""带来源过滤与可解释打分的轻量知识检索。"""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from typing import Any

from app.domain.catalog import ComputerCatalog, get_catalog


def tokenize(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.lower())
    latin = re.findall(r"[a-z0-9_+#.-]+", normalized)
    chinese_blocks = re.findall(r"[\u4e00-\u9fff]+", normalized)
    chinese = []
    for block in chinese_blocks:
        chinese.extend(block[index : index + 2] for index in range(max(1, len(block) - 1)))
    return latin + chinese


class KnowledgeEngine:
    def __init__(self, catalog: ComputerCatalog | None = None):
        self.catalog = catalog or get_catalog()
        self.documents = self._build_documents()
        self.document_frequency = Counter()
        for document in self.documents:
            self.document_frequency.update(set(tokenize(document["search_text"])))

    def _build_documents(self) -> list[dict[str, Any]]:
        documents = []
        for track in self.catalog.tracks:
            sources = track["sources"]
            for index, skill in enumerate(track["skills"]):
                source = sources[index % len(sources)]
                documents.append(
                    {
                        "chunk_id": f"{track['code']}:{skill['code']}",
                        "track_code": track["code"],
                        "skill_code": skill["code"],
                        "title": skill["name"],
                        "content": skill["description"],
                        "difficulty": skill["difficulty"],
                        "source_id": source["id"],
                        "source_title": source["title"],
                        "source_url": source["url"],
                        "content_version": source["version"],
                        "credibility": 0.95,
                        "search_text": " ".join(
                            [
                                track["name"],
                                track["description"],
                                skill["name"],
                                skill["description"],
                                " ".join(track["keywords"]),
                            ]
                        ),
                    }
                )
            source = sources[0]
            documents.append(
                {
                    "chunk_id": f"{track['code']}:project",
                    "track_code": track["code"],
                    "skill_code": "",
                    "title": track["project"]["title"],
                    "content": (
                        f"交付物：{'、'.join(track['project']['deliverables'])}。"
                        f"验收：{track['project']['acceptance']}"
                    ),
                    "difficulty": 3,
                    "source_id": source["id"],
                    "source_title": source["title"],
                    "source_url": source["url"],
                    "content_version": source["version"],
                    "credibility": 0.9,
                    "search_text": " ".join(
                        [
                            track["name"],
                            track["project"]["title"],
                            " ".join(track["project"]["deliverables"]),
                            track["project"]["acceptance"],
                        ]
                    ),
                }
            )
            for pathway in track.get("pathway_variants", []):
                career = pathway.get("career", {})
                for stage_index, stage in enumerate(pathway["stages"]):
                    source = sources[(stage_index + len(track["skills"])) % len(sources)]
                    topics = list(stage.get("topics", []))
                    documents.append(
                        {
                            "chunk_id": f"pathway:{pathway['id']}:stage:{stage_index + 1}",
                            "track_code": track["code"],
                            "skill_code": "",
                            "title": f"{pathway['name']} · {stage['title']}",
                            "content": (
                                f"建议周期：{stage['duration']}。"
                                f"具体技术：{'、'.join(topics)}。"
                                f"阶段目标：完成可运行示例、测试证据和复盘说明。"
                            ),
                            "difficulty": pathway.get("difficulty", 3),
                            "source_id": source["id"],
                            "source_title": source["title"],
                            "source_url": source["url"],
                            "content_version": source["version"],
                            "credibility": 0.92,
                            "search_text": " ".join(
                                [
                                    track["name"],
                                    track["description"],
                                    pathway["name"],
                                    pathway.get("suitable_for", ""),
                                    stage["title"],
                                    " ".join(topics),
                                    " ".join(career.get("roles", [])),
                                    " ".join(career.get("work_content", [])),
                                ]
                            ),
                        }
                    )
        return documents

    def search(
        self,
        query: str,
        track_code: str | None = None,
        top_k: int = 8,
        target_difficulty: float | None = None,
    ) -> list[dict[str, Any]]:
        query_tokens = list(dict.fromkeys(tokenize(query)))
        normalized_query = re.sub(r"\s+", " ", query.lower()).strip()
        total_documents = len(self.documents)
        candidates = [
            document
            for document in self.documents
            if not track_code or document["track_code"] == track_code
        ]
        scored = []
        for document in candidates:
            document_tokens = tokenize(document["search_text"])
            normalized_document = document["search_text"].lower()
            counts = Counter(document_tokens)
            lexical = 0.0
            matched = []
            for token in query_tokens:
                if token in counts:
                    matched.append(token)
                    inverse_frequency = math.log(
                        1 + total_documents / (1 + self.document_frequency[token])
                    )
                    lexical += (1 + math.log(counts[token])) * inverse_frequency
                elif len(token) >= 3:
                    partial = next(
                        (
                            candidate
                            for candidate in counts
                            if len(candidate) >= 3
                            and (token in candidate or candidate in token)
                        ),
                        None,
                    )
                    if partial:
                        matched.append(token)
                        lexical += 0.65
            phrase_bonus = (
                2.0
                if normalized_query and normalized_query in normalized_document
                else 0.0
            )
            track_bonus = 1.2 if track_code and document["track_code"] == track_code else 0
            difficulty_fit = 0.0
            if target_difficulty is not None:
                difficulty_fit = max(0.0, 1.0 - abs(document["difficulty"] - target_difficulty) / 5)
            score = lexical + phrase_bonus + track_bonus + difficulty_fit * 0.5
            if score > 0 or not query_tokens:
                scored.append(
                    {
                        **{key: value for key, value in document.items() if key != "search_text"},
                        "score": round(score, 4),
                        "matched_terms": sorted(set(matched))[:8],
                    }
                )
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


@lru_cache
def get_knowledge_engine() -> KnowledgeEngine:
    return KnowledgeEngine()
