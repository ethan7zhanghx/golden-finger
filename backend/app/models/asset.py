from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Uuid, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Asset(Base):
    __tablename__ = 'assets'
    __table_args__ = (UniqueConstraint('project_id', 'step_code', 'asset_type', name='uq_asset_project_step_type'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    step_code: Mapped[str] = mapped_column(String(50))
    asset_type: Mapped[str] = mapped_column(String(100))
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship('Project', back_populates='assets')
    versions = relationship('AssetVersion', back_populates='asset', cascade='all, delete-orphan')


class AssetVersion(Base):
    __tablename__ = 'asset_versions'
    __table_args__ = (UniqueConstraint('asset_id', 'version', name='uq_asset_version_asset_version'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), index=True)
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    asset = relationship('Asset', back_populates='versions')
