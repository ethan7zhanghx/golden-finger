from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)
    stream: bool = False
    max_tokens: int = 4096
    temperature: float = 0.7


class RewriteRequest(BaseModel):
    selected_text: str
    scene_context: str
    character_name: str
    stream: bool = False
    max_tokens: int = 2048
    temperature: float = 0.7


class PromptView(BaseModel):
    system: str
    context_template: str
    user_template: str


class ContextAsset(BaseModel):
    asset_id: str
    asset_type: str
    title: str
    priority: Literal["required", "optional"]


class ContextResponse(BaseModel):
    assets: list[ContextAsset]


class LLMResponse(BaseModel):
    provider: str = "ernie"
    model: str = "ERNIE-5.0"
    content: str
    finish_reason: str = "stop"
    usage: dict[str, int] = Field(default_factory=dict)


class ParseResult(BaseModel):
    data: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    valid: bool = True


class StepChunk(BaseModel):
    event: Literal["start", "chunk", "done", "error"]
    data: dict[str, Any]


class StepResult(BaseModel):
    run_id: str
    step_code: str
    status: Literal["queued", "processing", "completed", "failed"]
    result: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class ActionRequest(BaseModel):
    action: str


class ToolRunStatusResponse(BaseModel):
    run_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    result: dict[str, Any] | None = None
