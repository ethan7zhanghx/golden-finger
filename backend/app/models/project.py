from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Uuid, Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Project(Base):
    __tablename__ = 'projects'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(500))
    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='active')
    current_step_code: Mapped[str] = mapped_column(String(50), default='writer-quality')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship('User', back_populates='projects')
    step_progresses = relationship('StepProgress', back_populates='project', cascade='all, delete-orphan')
    assets = relationship('Asset', back_populates='project', cascade='all, delete-orphan')
    tool_runs = relationship('ToolRun', back_populates='project', cascade='all, delete-orphan')
    suggestions = relationship('Suggestion', back_populates='project', cascade='all, delete-orphan')
    export_jobs = relationship('ExportJob', back_populates='project', cascade='all, delete-orphan')
    copyright_bundles = relationship('CopyrightBundle', back_populates='project', cascade='all, delete-orphan')


class StepProgress(Base):
    __tablename__ = 'step_progresses'
    __table_args__ = (UniqueConstraint('project_id', 'step_code', name='uq_step_progress_project_step'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    step_code: Mapped[str] = mapped_column(String(50))
    step_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default='pending')
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    step_metadata: Mapped[Optional[dict]] = mapped_column('metadata', JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship('Project', back_populates='step_progresses')


class ExportJob(Base):
    __tablename__ = 'export_jobs'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    format: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default='pending')
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship('Project', back_populates='export_jobs')


class CopyrightBundle(Base):
    __tablename__ = 'copyright_bundles'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    bundle_type: Mapped[str] = mapped_column(String(50), default='registration')
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship('Project', back_populates='copyright_bundles')
