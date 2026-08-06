"""岗位目标、成果证据与路线版本。

Revision ID: 002_career_learning_loop
Revises: 001_current_schema
Create Date: 2026-08-05
"""

import sqlalchemy as sa
from alembic import op


revision = "002_career_learning_loop"
down_revision = "001_current_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 001 使用当前 ORM 元数据创建全量表；新库执行 001 时可能已包含本轮表。
    # 老库则三张表都不存在。显式处理两种状态，避免重复建表。
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    required = {"career_targets", "evidence_artifacts", "route_revisions"}
    if required.issubset(existing):
        return
    if required & existing:
        raise RuntimeError("career learning loop migration found a partial schema")
    op.create_table(
        "career_targets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("company", sa.String(length=160), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("education", sa.String(length=80), nullable=False),
        sa.Column("experience", sa.String(length=120), nullable=False),
        sa.Column("salary", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("responsibilities", sa.JSON(), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_targets_user_id", "career_targets", ["user_id"])
    op.create_index("ix_career_targets_title", "career_targets", ["title"])
    op.create_index("ix_career_targets_active", "career_targets", ["active"])

    op.create_table(
        "evidence_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=240), nullable=False),
        sa.Column("evidence_type", sa.String(length=40), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("verification", sa.JSON(), nullable=False),
        sa.Column("skill_updates", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["learning_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_artifacts_user_id", "evidence_artifacts", ["user_id"])
    op.create_index("ix_evidence_artifacts_plan_id", "evidence_artifacts", ["plan_id"])
    op.create_index("ix_evidence_artifacts_task_id", "evidence_artifacts", ["task_id"])
    op.create_index("ix_evidence_artifacts_status", "evidence_artifacts", ["status"])

    op.create_table(
        "route_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("from_version", sa.Integer(), nullable=False),
        sa.Column("to_version", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(length=60), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("old_phases", sa.JSON(), nullable=False),
        sa.Column("new_phases", sa.JSON(), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["learning_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_route_revisions_user_id", "route_revisions", ["user_id"])
    op.create_index("ix_route_revisions_plan_id", "route_revisions", ["plan_id"])
    op.create_index("ix_route_revisions_trigger", "route_revisions", ["trigger"])
    op.create_index("ix_route_revisions_status", "route_revisions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_route_revisions_status", table_name="route_revisions")
    op.drop_index("ix_route_revisions_trigger", table_name="route_revisions")
    op.drop_index("ix_route_revisions_plan_id", table_name="route_revisions")
    op.drop_index("ix_route_revisions_user_id", table_name="route_revisions")
    op.drop_table("route_revisions")
    op.drop_index("ix_evidence_artifacts_status", table_name="evidence_artifacts")
    op.drop_index("ix_evidence_artifacts_task_id", table_name="evidence_artifacts")
    op.drop_index("ix_evidence_artifacts_plan_id", table_name="evidence_artifacts")
    op.drop_index("ix_evidence_artifacts_user_id", table_name="evidence_artifacts")
    op.drop_table("evidence_artifacts")
    op.drop_index("ix_career_targets_active", table_name="career_targets")
    op.drop_index("ix_career_targets_title", table_name="career_targets")
    op.drop_index("ix_career_targets_user_id", table_name="career_targets")
    op.drop_table("career_targets")
