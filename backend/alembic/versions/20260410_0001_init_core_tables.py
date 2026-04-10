"""init core tables

Revision ID: 20260410_0001
Revises: 
Create Date: 2026-04-10 13:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260410_0001'
down_revision = None
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'projects',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('user_id', UUID, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('genre', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('current_step_code', sa.String(length=50), nullable=False, server_default='writer-quality'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])

    op.create_table(
        'step_progresses',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_code', sa.String(length=50), nullable=False),
        sa.Column('step_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('progress_percent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('project_id', 'step_code', name='uq_step_progress_project_step'),
    )
    op.create_index('ix_step_progresses_project_id', 'step_progresses', ['project_id'])

    op.create_table(
        'assets',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_code', sa.String(length=50), nullable=False),
        sa.Column('asset_type', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content', JSONB, nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('project_id', 'step_code', 'asset_type', name='uq_asset_project_step_type'),
    )
    op.create_index('ix_assets_project_id', 'assets', ['project_id'])

    op.create_table(
        'asset_versions',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('asset_id', UUID, sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('asset_id', 'version', name='uq_asset_version_asset_version'),
    )
    op.create_index('ix_asset_versions_asset_id', 'asset_versions', ['asset_id'])

    op.create_table(
        'prompt_templates',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('step_code', sa.String(length=50), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('template', sa.Text(), nullable=False),
        sa.Column('variables', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('step_code', 'tool_name', 'version', name='uq_prompt_template_version'),
    )

    op.create_table(
        'tool_runs',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_code', sa.String(length=50), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('input_snapshot', JSONB, nullable=True),
        sa.Column('output_snapshot', JSONB, nullable=True),
        sa.Column('prompt_template_id', UUID, sa.ForeignKey('prompt_templates.id'), nullable=True),
        sa.Column('prompt_version', sa.Integer(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False, server_default='ernie-5.0'),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='success'),
        sa.Column('adopted', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_tool_runs_project_id', 'tool_runs', ['project_id'])

    op.create_table(
        'suggestions',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_code', sa.String(length=50), nullable=False),
        sa.Column('suggestion_type', sa.String(length=50), nullable=False),
        sa.Column('payload', JSONB, nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_suggestions_project_id', 'suggestions', ['project_id'])

    op.create_table(
        'export_jobs',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('format', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_export_jobs_project_id', 'export_jobs', ['project_id'])

    op.create_table(
        'copyright_bundles',
        sa.Column('id', UUID, primary_key=True, nullable=False),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bundle_type', sa.String(length=50), nullable=False, server_default='registration'),
        sa.Column('payload', JSONB, nullable=False),
        sa.Column('checksum', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_copyright_bundles_project_id', 'copyright_bundles', ['project_id'])


def downgrade() -> None:
    op.drop_index('ix_copyright_bundles_project_id', table_name='copyright_bundles')
    op.drop_table('copyright_bundles')
    op.drop_index('ix_export_jobs_project_id', table_name='export_jobs')
    op.drop_table('export_jobs')
    op.drop_index('ix_suggestions_project_id', table_name='suggestions')
    op.drop_table('suggestions')
    op.drop_index('ix_tool_runs_project_id', table_name='tool_runs')
    op.drop_table('tool_runs')
    op.drop_table('prompt_templates')
    op.drop_index('ix_asset_versions_asset_id', table_name='asset_versions')
    op.drop_table('asset_versions')
    op.drop_index('ix_assets_project_id', table_name='assets')
    op.drop_table('assets')
    op.drop_index('ix_step_progresses_project_id', table_name='step_progresses')
    op.drop_table('step_progresses')
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_table('projects')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
