"""知识检索、来源详情与审核知识入库 API。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, success
from app.core.database import get_db
from app.core.models import KnowledgeContribution, User
from app.domain.catalog import CatalogError, get_catalog
from app.domain.knowledge import get_knowledge_engine, tokenize
from app.schemas import KnowledgeContributionInput, KnowledgeReviewInput

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search")
def search(
    q: str = Query(default="", max_length=500),
    track_code: str | None = None,
    top_k: int = Query(default=8, ge=1, le=30),
    db: Session = Depends(get_db),
):
    if track_code:
        try:
            get_catalog().get_track(track_code)
        except CatalogError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    items = get_knowledge_engine().search(q, track_code=track_code, top_k=top_k * 2)
    query_terms = set(tokenize(q))
    contributions = db.scalars(
        select(KnowledgeContribution).where(
            KnowledgeContribution.status == "approved",
            *(
                [KnowledgeContribution.track_code == track_code]
                if track_code
                else []
            ),
        )
    ).all()
    reviewed_items = []
    for row in contributions:
        terms = set(tokenize(f"{row.title} {row.content}"))
        overlap = len(query_terms & terms) / max(1, len(query_terms)) if query_terms else 1
        if overlap <= 0:
            continue
        reviewed_items.append(
            {
                "chunk_id": f"contrib:{row.id}",
                "track_code": row.track_code,
                "skill_code": "",
                "title": row.title,
                "content": row.content,
                "difficulty": 3,
                "source_id": f"contrib:{row.id}",
                "source_title": row.title,
                "source_url": row.source_url,
                "content_version": row.content_version,
                "credibility": 0.88,
                "score": round(overlap + 0.8, 4),
                "matched_terms": sorted(query_terms & terms)[:8],
                "source_layer": "reviewed_contribution",
            }
        )
    # 审核通过的用户贡献属于本地审核知识库。不同检索器的原始分数不可直接比较，
    # 因此为相关贡献保留结果位，避免 TF-IDF 数值尺度将其静默挤出。
    reviewed_items.sort(key=lambda item: item["score"], reverse=True)
    reserved_count = min(len(reviewed_items), max(1, top_k // 3))
    reserved = reviewed_items[:reserved_count]
    remainder = sorted(
        items + reviewed_items[reserved_count:],
        key=lambda item: item["score"],
        reverse=True,
    )
    items = (reserved + remainder)[:top_k]
    return success(
        {
            "items": items,
            "total": len(items),
            "query": q,
            "suggestions": (
                []
                if items
                else ["Python", "Vue 3", "Java 后端", "Agent", "RAG", "Docker"]
            ),
            "popular_queries": ["Python", "Vue 3", "React", "Java", "Agent", "算法", "嵌入式"],
            "filters": {"track_code": track_code, "catalog_version": get_catalog().version},
        }
    )


@router.get("/chunks/{chunk_id:path}")
def chunk_detail(chunk_id: str, db: Session = Depends(get_db)):
    if chunk_id.startswith("contrib:"):
        row = db.get(KnowledgeContribution, chunk_id.removeprefix("contrib:"))
        if not row or row.status != "approved":
            raise HTTPException(status_code=404, detail="知识片段不存在")
        return success(
            {
                "chunk_id": chunk_id,
                "track_code": row.track_code,
                "skill_code": "",
                "title": row.title,
                "content": row.content,
                "difficulty": 3,
                "source_id": chunk_id,
                "source_title": row.title,
                "source_url": row.source_url,
                "content_version": row.content_version,
                "credibility": 0.88,
                "source_layer": "reviewed_contribution",
                "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
            }
        )
    item = next(
        (
            document
            for document in get_knowledge_engine().documents
            if document["chunk_id"] == chunk_id
        ),
        None,
    )
    if not item:
        raise HTTPException(status_code=404, detail="知识片段不存在")
    return success({key: value for key, value in item.items() if key != "search_text"})


@router.get("/sources")
def sources(track_code: str | None = None):
    tracks = (
        [get_catalog().get_track(track_code)] if track_code else get_catalog().tracks
    )
    seen = set()
    items = []
    for track in tracks:
        for source in track["sources"]:
            if source["id"] not in seen:
                seen.add(source["id"])
                items.append({**source, "track_code": track["code"]})
    return success({"items": items, "catalog_version": get_catalog().version})


def contribution_view(row: KnowledgeContribution) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "track_code": row.track_code,
        "title": row.title,
        "content": row.content,
        "source_url": row.source_url,
        "license_type": row.license_type,
        "content_version": row.content_version,
        "status": row.status,
        "review_notes": row.review_notes,
        "reviewed_by": row.reviewed_by,
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "created_at": row.created_at.isoformat(),
    }


@router.post("/documents")
def submit_document(
    body: KnowledgeContributionInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        get_catalog().get_track(body.track_code)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not body.source_url.startswith("https://"):
        raise HTTPException(status_code=422, detail="来源地址必须使用 HTTPS")
    row = KnowledgeContribution(
        user_id=user.id,
        track_code=body.track_code,
        title=body.title.strip(),
        content=body.content.strip(),
        source_url=body.source_url.strip(),
        license_type=body.license_type.strip(),
        content_version=body.content_version.strip(),
        status="approved" if user.role == "admin" else "pending",
        reviewed_by=user.id if user.role == "admin" else None,
        reviewed_at=datetime.now(timezone.utc) if user.role == "admin" else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return success(
        contribution_view(row),
        "文档已入库" if row.status == "approved" else "文档已提交审核",
    )


@router.get("/documents")
def list_documents(
    status_filter: str | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = select(KnowledgeContribution)
    if user.role != "admin":
        statement = statement.where(KnowledgeContribution.user_id == user.id)
    if status_filter:
        statement = statement.where(KnowledgeContribution.status == status_filter)
    rows = db.scalars(statement.order_by(KnowledgeContribution.created_at.desc())).all()
    return success({"items": [contribution_view(row) for row in rows]})


@router.put("/documents/{document_id}/review")
def review_document(
    document_id: str,
    body: KnowledgeReviewInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可以审核知识文档")
    row = db.get(KnowledgeContribution, document_id)
    if not row:
        raise HTTPException(status_code=404, detail="知识文档不存在")
    row.status = body.status
    row.review_notes = body.review_notes
    row.reviewed_by = user.id
    row.reviewed_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return success(contribution_view(row), "审核结果已保存")
