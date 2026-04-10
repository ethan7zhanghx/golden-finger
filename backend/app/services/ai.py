from __future__ import annotations

import json
from collections.abc import AsyncIterator
from uuid import uuid4

from backend.app.schemas.ai import (
    ContextAsset,
    ContextResponse,
    GenerateRequest,
    LLMResponse,
    ParseResult,
    PromptView,
    RewriteRequest,
    StepChunk,
    StepResult,
    ToolRunStatusResponse,
)

STEP_DEPENDENCIES: dict[str, list[tuple[str, str, str]]] = {
    "worldview": [
        ("creation_charter", "创作约束卡", "required"),
    ],
    "selling_point": [
        ("worldview", "世界观卡", "required"),
        ("creation_charter", "创作约束卡", "optional"),
    ],
    "hook": [
        ("worldview", "世界观卡", "required"),
        ("selling_point", "卖点卡", "required"),
    ],
}

PROMPT_REGISTRY: dict[str, PromptView] = {
    "worldview": PromptView(
        system="你是一位资深微短剧编剧顾问，严格输出结构化 JSON。",
        context_template="## 项目已有资产\n{context_assets}\n\n## 创作约束\n{constraints}",
        user_template="请根据题材 {genre} 与创意 {user_input} 生成世界观设定。",
    ),
    "selling_point": PromptView(
        system="你是一位内容策划，输出核心卖点 JSON。",
        context_template="## 世界观\n{worldview}\n## 创作约束\n{constraints}",
        user_template="请基于用户输入 {user_input} 提炼 3 条核心卖点。",
    ),
}


class LLMClient:
    """ERNIE API 调用封装占位实现。"""

    async def generate(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> LLMResponse | AsyncIterator[str]:
        if stream:
            return self._stream_response(messages)

        content = json.dumps(
            {
                "summary": "placeholder generation",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            ensure_ascii=False,
        )
        return LLMResponse(
            content=content,
            usage={"input": min(1200, max_tokens // 2), "output": min(800, max_tokens // 3)},
        )

    async def generate_with_retry(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> LLMResponse:
        _ = max_retries
        response = await self.generate(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        assert isinstance(response, LLMResponse)
        return response

    async def _stream_response(self, messages: list[dict]) -> AsyncIterator[str]:
        for message in messages:
            yield f"基于 {message['role']} 消息生成中..."
        yield "结构化输出已完成。"


class OutputParser:
    """结构化输出解析与校验占位实现。"""

    def parse_and_validate(self, raw_output: str, step_code: str) -> ParseResult:
        try:
            payload = json.loads(raw_output)
            if isinstance(payload, dict):
                return ParseResult(data={"step_code": step_code, **payload}, valid=True)
        except json.JSONDecodeError:
            pass

        return ParseResult(
            data={"step_code": step_code, "raw_output": raw_output},
            warnings=["LLM 输出不是严格 JSON，已降级保存原始文本。"],
            valid=False,
        )


class WorkflowEngine:
    """各步骤 AI workflow 编排占位实现。"""

    def __init__(self, llm_client: LLMClient | None = None, output_parser: OutputParser | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self.output_parser = output_parser or OutputParser()

    async def execute_step(
        self,
        project_id: str,
        step_code: str,
        user_input: dict,
        stream: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> StepResult | AsyncIterator[StepChunk]:
        prompts = self.get_prompt(step_code)
        messages = [
            {"role": "system", "content": prompts.system},
            {"role": "user", "content": json.dumps(user_input, ensure_ascii=False)},
        ]
        run_id = str(uuid4())

        if stream:
            return self._stream_step(run_id=run_id, step_code=step_code, messages=messages)

        response = await self.llm_client.generate_with_retry(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        parsed = self.output_parser.parse_and_validate(response.content, step_code)
        return StepResult(
            run_id=run_id,
            step_code=step_code,
            status="completed",
            result={
                "project_id": project_id,
                "parsed": parsed.data,
                "usage": response.usage,
            },
            warnings=parsed.warnings,
        )

    def get_prompt(self, step_code: str) -> PromptView:
        return PROMPT_REGISTRY.get(
            step_code,
            PromptView(
                system="你是一位 AI 创作助手，请输出结构化 JSON。",
                context_template="## Context\n{context_assets}",
                user_template="请根据输入完成步骤 {step_code}。",
            ),
        )

    def get_context(self, project_id: str, step_code: str) -> ContextResponse:
        dependencies = STEP_DEPENDENCIES.get(step_code, [])
        assets = [
            ContextAsset(
                asset_id=f"{project_id}-{asset_type}",
                asset_type=asset_type,
                title=title,
                priority=priority,
            )
            for asset_type, title, priority in dependencies
        ]
        return ContextResponse(assets=assets)

    def get_tool_run_status(self, run_id: str) -> ToolRunStatusResponse:
        return ToolRunStatusResponse(
            run_id=run_id,
            status="processing",
            progress=60,
            result={"message": "placeholder status; connect Redis/Celery result backend in M2 implementation"},
        )

    async def _stream_step(
        self,
        run_id: str,
        step_code: str,
        messages: list[dict],
    ) -> AsyncIterator[StepChunk]:
        yield StepChunk(event="start", data={"run_id": run_id, "step_code": step_code})
        stream = await self.llm_client.generate(messages=messages, stream=True)
        assert not isinstance(stream, LLMResponse)
        async for content in stream:
            yield StepChunk(event="chunk", data={"content": content})
        yield StepChunk(
            event="done",
            data={
                "run_id": run_id,
                "result": {"step_code": step_code, "status": "completed"},
                "tokens": {"input": 1200, "output": 800},
            },
        )


def build_rewrite_input(request: RewriteRequest) -> GenerateRequest:
    return GenerateRequest(
        input={
            "selected_text": request.selected_text,
            "scene_context": request.scene_context,
            "character_name": request.character_name,
            "mode": "rewrite",
        },
        stream=request.stream,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )
