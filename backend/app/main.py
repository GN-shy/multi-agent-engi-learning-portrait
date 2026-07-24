"""工学智链 FastAPI 应用入口。"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import or_, select

from app.api import (
    auth,
    dashboard,
    evaluation,
    integrations,
    knowledge,
    learning,
    profiles,
    sessions,
    tracks,
)
from app.core.config import settings
from app.core.database import SessionLocal, init_database
from app.core.models import User
from app.core.security import hash_password
from app.domain.catalog import get_catalog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("gongxue")


def seed_demo_user() -> None:
    with SessionLocal() as db:
        exists = db.scalar(
            select(User).where(
                or_(User.username == "演示用户", User.email == "demo@gongxue.local")
            )
        )
        if not exists:
            db.add(
                User(
                    username="演示用户",
                    email="demo@gongxue.local",
                    password_hash=hash_password("demo12345"),
                )
            )
            db.commit()


def seed_bootstrap_admin() -> None:
    """按显式环境变量初始化治理账号，绝不内置生产管理员弱口令。"""
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return
    if len(settings.bootstrap_admin_password) < 12:
        raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD 至少需要 12 位")
    email = settings.bootstrap_admin_email.lower().strip()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            if user.role != "admin":
                user.role = "admin"
                db.commit()
            return
        db.add(
            User(
                username=settings.bootstrap_admin_username.strip() or "治理管理员",
                email=email,
                password_hash=hash_password(settings.bootstrap_admin_password),
                role="admin",
            )
        )
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    catalog = get_catalog()
    seed_demo_user()
    seed_bootstrap_admin()
    logger.info(
        "应用启动：catalog=%s tracks=%d environment=%s",
        catalog.version,
        len(catalog.tracks),
        settings.environment,
    )
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    description="计算机能力成长与职业路线决策平台",
    version=settings.app_version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-response-time-ms"] = str(round((time.perf_counter() - started) * 1000, 1))
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "请求参数校验失败",
            "data": {"errors": exc.errors()},
            "request_id": uuid.uuid4().hex[:12],
        },
    )


for api_router in (
    auth.router,
    tracks.router,
    profiles.router,
    evaluation.router,
    integrations.router,
    knowledge.router,
    sessions.router,
    learning.router,
    dashboard.router,
):
    app.include_router(api_router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", tags=["system"])
def health():
    catalog = get_catalog()
    return {
        "code": 0,
        "message": "healthy",
        "data": {
            "version": settings.app_version,
            "environment": settings.environment,
            "catalog_version": catalog.version,
            "track_count": len(catalog.tracks),
            "llm_enabled": settings.llm_enabled and bool(settings.llm_api_key),
        },
        "request_id": uuid.uuid4().hex[:12],
    }
