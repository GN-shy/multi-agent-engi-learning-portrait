"""当前计算机学习平台完整初始结构。

Revision ID: 001_current_schema
Revises:
Create Date: 2026-07-24
"""

from alembic import op

from app.core.database import Base
from app.core import models  # noqa: F401


revision = "001_current_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 元数据是 ORM 的单一结构事实源，避免旧原型 SQL 与模型持续漂移。
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
