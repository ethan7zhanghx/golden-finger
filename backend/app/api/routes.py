from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Response, status
from fastapi.responses import StreamingResponse

from app.schemas.ai import ActionRequest, GenerateRequest, RewriteRequest
from app.services.ai import WorkflowEngine, build_rewrite_input

router = APIRouter(tags=["ai"])
workflow_engine = WorkflowEngine()


@router.post("/projects/{project_id}/steps/{step_code}/generate")
async def generate_step(project_id: str, step_code: str, request: GenerateRequest):
    if request.stream:
        stream = await workflow_engine.execute_step(
            project_id=project_id,
            step_code=step_code,
            user_input=request.input,
            stream=True,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        return StreamingResponse(_to_sse(stream), media_type="text/event-stream")

    return await workflow_engine.execute_step(
        project_id=project_id,
        step_code=step_code,
        user_input=request.input,
        stream=False,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )


@router.post("/projects/{project_id}/steps/{step_code}/rewrite")
async def rewrite_step(project_id: str, step_code: str, request: RewriteRequest):
    generate_request = build_rewrite_input(request)
    return await generate_step(project_id=project_id, step_code=step_code, request=generate_request)


@router.get("/projects/{project_id}/steps/{step_code}/context")
async def get_step_context(project_id: str, step_code: str):
    return workflow_engine.get_context(project_id=project_id, step_code=step_code)


@router.post(
    "/tool-runs/{run_id}/action",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def record_tool_run_action(run_id: str, request: ActionRequest) -> Response:
    _ = (run_id, request.action)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tool-runs/{run_id}/status")
async def get_tool_run_status(run_id: str):
    return workflow_engine.get_tool_run_status(run_id)


@router.get("/prompts/{step_code}")
async def get_active_prompt(step_code: str):
    return workflow_engine.get_prompt(step_code)


async def _to_sse(stream: AsyncIterator) -> AsyncIterator[str]:
    async for chunk in stream:
        yield f"event: {chunk.event}\ndata: {json.dumps(chunk.data, ensure_ascii=False)}\n\n"
