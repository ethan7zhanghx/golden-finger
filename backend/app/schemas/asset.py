from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    step_code: str = Field(min_length=1, max_length=50)
    asset_type: str = Field(min_length=1, max_length=100)
    title: Optional[str] = Field(default=None, max_length=255)
    content: dict[str, Any] = Field(default_factory=dict)


class AssetRead(BaseModel):
    id: UUID
    project_id: UUID
    step_code: str
    asset_type: str
    title: Optional[str]
    content: dict[str, Any]
    version: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {'from_attributes': True}


class AssetVersionRead(BaseModel):
    id: UUID
    asset_id: UUID
    version: int
    content: dict[str, Any]
    created_at: datetime

    model_config = {'from_attributes': True}
