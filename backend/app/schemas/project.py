from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    genre: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    genre: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = None
    current_step_code: Optional[str] = None


class ProjectRead(BaseModel):
    id: UUID
    title: str
    genre: Optional[str]
    description: Optional[str]
    status: str
    current_step_code: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class StepProgressRead(BaseModel):
    id: UUID
    step_code: str
    step_name: str
    status: str
    progress_percent: int
    is_current: bool
    metadata: Optional[dict[str, Any]] = Field(default=None, validation_alias='step_metadata', serialization_alias='metadata')
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
