from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Uuid, Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ToolRun(Base):
    __tablename__ = 'tool_runs'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    step_code: Mapped[str] = mapped_column(String(50))
    tool_name: Mapped[str] = mapped_column(String(100))
    input_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    prompt_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey('prompt_templates.id'), nullable=True)
    prompt_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), default='ernie-5.0')
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='success')
    adopted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship('Project', back_populates='tool_runs')
    prompt_template = relationship('PromptTemplate', back_populates='tool_runs')


class Suggestion(Base):
    __tablename__ = 'suggestions'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    step_code: Mapped[str] = mapped_column(String(50))
    suggestion_type: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship('Project', back_populates='suggestions')


class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'
    __table_args__ = (UniqueConstraint('step_code', 'tool_name', 'version', name='uq_prompt_template_version'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_code: Mapped[str] = mapped_column(String(50))
    tool_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer)
    template: Mapped[str] = mapped_column(Text)
    variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tool_runs = relationship('ToolRun', back_populates='prompt_template')
