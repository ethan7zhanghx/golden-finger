import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(..., max_length=200)
    genre: str | None = None
    episode_count: int | None = None
    description: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    genre: str | None = None
    episode_count: int | None = None
    description: str | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    genre: str | None
    episode_count: int | None
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StepProgressOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    step_code: str
    status: str
    current_asset_id: uuid.UUID | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    step_code: str
    asset_type: str
    title: str | None = None
    content: dict | None = None


class AssetOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    step_code: str
    asset_type: str
    title: str | None
    content: dict | None
    is_formal: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetVersionOut(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    version: int
    content: dict | None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: str
    password: str = Field(..., min_length=6)
    display_name: str | None = None


class AuthLogin(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    display_name: str | None

    model_config = {"from_attributes": True}
