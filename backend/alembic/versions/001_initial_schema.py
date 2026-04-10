"""Initial schema with all 10 core tables

Revision ID: 001
Revises:
Create Date: 2026-04-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("genre", sa.String(50)),
        sa.Column("episode_count", sa.Integer),
        sa.Column("description", sa.Text),
        sa.Column(
            "status",
            sa.Enum("draft", "in_progress", "completed", "archived", name="project_status"),
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "step_progresses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("step_code", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.Enum("not_started", "in_progress", "completed", name="step_status"),
            server_default="not_started",
        ),
        sa.Column("current_asset_id", UUID(as_uuid=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("step_code", sa.String(50), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("content", JSONB),
        sa.Column("is_formal", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "asset_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("content", JSONB),
        sa.Column(
            "source",
            sa.Enum("user", "ai_generated", "ai_accepted", name="asset_source"),
            server_default="user",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tool_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("step_code", sa.String(50), nullable=False),
        sa.Column("tool_type", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "success", "failed", name="tool_run_status"),
            server_default="pending",
        ),
        sa.Column("input_snapshot", JSONB),
        sa.Column("output_snapshot", JSONB),
        sa.Column("prompt_version", sa.Integer),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("total_tokens", sa.Integer),
        sa.Column("estimated_cost", sa.Float),
        sa.Column(
            "user_action",
            sa.Enum("accepted", "rejected", "partial_accepted", "regenerated", name="user_action"),
        ),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "suggestions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tool_run_id", UUID(as_uuid=True), sa.ForeignKey("tool_runs.id"), nullable=False),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("rank", sa.Integer, server_default="0"),
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "rejected", name="suggestion_status"),
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "prompt_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("step_code", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column("user_prompt_template", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "export_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "processing", "completed", "failed", name="export_status"),
            server_default="queued",
        ),
        sa.Column("output_url", sa.String(500)),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "copyright_bundles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("author_name", sa.String(200), nullable=False),
        sa.Column("registration_number", sa.String(100)),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("copyright_bundles")
    op.drop_table("export_jobs")
    op.drop_table("prompt_templates")
    op.drop_table("suggestions")
    op.drop_table("tool_runs")
    op.drop_table("asset_versions")
    op.drop_table("assets")
    op.drop_table("step_progresses")
    op.drop_table("projects")
    op.drop_table("users")
    for name in [
        "project_status", "step_status", "asset_source",
        "tool_run_status", "user_action", "suggestion_status", "export_status",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {name}")
