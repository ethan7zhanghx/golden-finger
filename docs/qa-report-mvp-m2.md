# 金手指 MVP M2 — QA 验收报告

> 报告日期：2026-04-10
> 测试人：QA Agent
> 分支：agent/qa/96ead3eb
> 测试方式：静态代码分析 + AI 工作流单元测试（环境限制：无 Docker/PostgreSQL/Redis）

---

## 执行摘要

| 维度 | 状态 |
|------|------|
| AI 工作流单元测试（19 条） | ✅ **全部通过** |
| 后端 API 结构审查 | ✅ **结构完整，存在 3 个功能缺陷** |
| 前端页面结构审查 | ✅ **主流程完整，存在 2 个类型错误** |
| 前后端联调可行性 | ⚠️ **AI 生成端点无鉴权，current_step 字段缺失** |
| 环境可启动性 | ⚠️ **依赖 Docker，本地无法独立启动** |

**整体结论：CONDITIONAL SHIP**
核心链路（注册→登录→项目管理→步骤编辑）代码结构完整，AI 工作流 mock 测试全通过。但存在 3 个影响集成联调的中高风险 bug，建议修复后再执行端到端验收。

---

## Acceptance Criteria 逐项核对

| AC | 状态 | 证据 |
|----|------|------|
| 完整用户流程可走通（注册→登录→创建项目→步骤编辑→AI 生成） | PARTIAL | 代码层面结构完整，但 `current_step` 缺失（见 BUG-01）、AI 端点无鉴权（见 BUG-02），端到端联调未验证 |
| 列出发现的 bug 和改进建议 | VERIFIED | 见下方 Bug 清单 |
| 测试报告 commit 到仓库 | VERIFIED | 本文件已 commit |

---

## AI 工作流单元测试结果

```
platform darwin -- Python 3.11.14, pytest-9.0.3
rootdir: golden-finger/

backend/tests_ai/test_workflows.py::TestExtractJson::test_code_block          PASSED
backend/tests_ai/test_workflows.py::TestExtractJson::test_mixed_text           PASSED
backend/tests_ai/test_workflows.py::TestExtractJson::test_no_json              PASSED
backend/tests_ai/test_workflows.py::TestExtractJson::test_pure_json            PASSED
backend/tests_ai/test_workflows.py::TestOutputPipeline::test_fallback_called   PASSED
backend/tests_ai/test_workflows.py::TestOutputPipeline::test_invalid_output    PASSED
backend/tests_ai/test_workflows.py::TestOutputPipeline::test_valid_worldview   PASSED
backend/tests_ai/test_workflows.py::TestSchemaValidation::test_hook_output     PASSED
backend/tests_ai/test_workflows.py::TestSchemaValidation::test_selling_point   PASSED
backend/tests_ai/test_workflows.py::TestSchemaValidation::test_worldview_miss  PASSED
backend/tests_ai/test_workflows.py::TestSchemaValidation::test_worldview_valid PASSED
backend/tests_ai/test_workflows.py::TestWorldviewWorkflow::test_end_to_end     PASSED
backend/tests_ai/test_workflows.py::TestWorldviewWorkflow::test_invalid_input  PASSED
backend/tests_ai/test_workflows.py::TestSellingPointWorkflow::test_end_to_end  PASSED
backend/tests_ai/test_workflows.py::TestHookWorkflow::test_end_to_end          PASSED
backend/tests_ai/test_workflows.py::TestWorkflowRouter::test_full_pipeline_3   PASSED
backend/tests_ai/test_workflows.py::TestWorkflowRouter::test_list_steps        PASSED
backend/tests_ai/test_workflows.py::TestWorkflowRouter::test_register_and_run  PASSED
backend/tests_ai/test_workflows.py::TestWorkflowRouter::test_unknown_step      PASSED

19 passed in 0.07s
```

**结论**：JSON 提取、Schema 校验、世界观/卖点/钩子三步工作流、WorkflowRouter 全流水线均通过 mock 验证。

---

## Bug 清单

### BUG-01 【高】`Project` 模型和 Schema 缺少 `current_step` 字段

**文件**：
- `backend/app/models/models.py` — `Project` 无 `current_step` 列
- `backend/app/schemas/project.py` — `ProjectOut` 无 `current_step` 字段

**影响**：
前端 `Project` 类型中有 `current_step?: StepCode`，项目列表点击后通过 `project.current_step ?? "worldview"` 跳转。由于后端不返回该字段，所有项目始终回退到 `worldview` 步骤，无法记忆用户上次编辑位置。

**复现**：
1. 在步骤 `hook` 编辑后返回项目列表
2. 再次点击该项目 → 跳转到 `worldview` 而非 `hook`

**建议修复**：
在 `Project` 模型添加 `current_step: Mapped[str | None]`，在 `ProjectOut` 中暴露，并在步骤切换时调用 `PUT /api/projects/{id}` 更新（`updateProject` API 已存在）。

---

### BUG-02 【高】AI 生成端点（`/generate`、`/rewrite`）无用户鉴权

**文件**：`backend/app/api/routes.py`

**影响**：
`POST /api/projects/{project_id}/steps/{step_code}/generate` 不需要 Bearer Token，任何人知道项目 ID 即可触发 AI 生成（消耗 API 额度），也无法隔离用户数据。

**建议修复**：
```python
from backend.app.core.auth import get_current_user
from backend.app.models.models import User

async def generate_step(
    project_id: str,
    step_code: str,
    request: GenerateRequest,
    user: User = Depends(get_current_user),   # 添加此行
):
```

---

### BUG-03 【中】前端 `UserLoginInput` / `UserRegisterInput` 类型与后端不一致

**文件**：`frontend/src/types/index.ts`

```typescript
// 当前（错误）
export interface UserLoginInput {
  email: string;    // ← 后端 AuthLogin 要求 username
  password: string;
}
export interface UserRegisterInput {
  email: string;    // ← 缺少 username 字段
  password: string;
}
```

**影响**：
`api.ts` 中的 `login()` 函数接受 `UserLoginInput`，但后端要求 `username`。当前登录页面用了裸 `fetch` 绕过类型检查，类型定义会误导未来使用 `login()` 函数的调用者。

**建议修复**：
```typescript
export interface UserLoginInput {
  username: string;
  password: string;
}
export interface UserRegisterInput {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}
```

---

### BUG-04 【低】`useSSE` 的 `abort()` 功能不生效

**文件**：`frontend/src/hooks/useSSE.ts`

**问题**：`abortRef` 创建了 `AbortController` 但从未将其 `signal` 传入 `fetch()`（`consume` 函数接受 `Response` 而非 URL），导致调用 `abort()` 后流不会中断。

**影响**：用户点击"停止生成"后后端继续输出，直到流结束。

**建议**：将 `AbortController` 的控制权移到 `useAIGenerate` 钩子，在调用 `generateStepStream()` 时传入 `signal`。

---

## 未覆盖范围（环境限制）

由于本次测试运行环境无 Docker、PostgreSQL、Redis，以下场景**未能执行端到端验证**：

| 场景 | 风险 |
|------|------|
| 注册/登录 HTTP 流程 | 低（代码逻辑清晰，类型问题已记录） |
| 创建项目 → 16 步初始化 | 中（DB 触发器逻辑依赖 PostgreSQL ENUM） |
| SSE 流式 AI 生成 | 高（主要功能，未实测） |
| 自动保存（500ms debounce） | 中（单元逻辑正确，网络层未测） |
| 步骤导航 16 步切换 | 低（路由逻辑简单） |

---

## 改进建议

1. **添加集成测试环境说明**：在 README 补充不依赖 Docker 的本地开发方式（如 SQLite 配置或 `docker compose up` 一键启动命令）。
2. **AI 服务接入真实 ERNIE API**：`backend/app/services/ai.py` 中 `LLMClient` 为 placeholder，需对接 `backend/ai/ernie_client.py` 中已有的实现。
3. **项目页面加 loading skeleton**：当前 `loading` 状态只显示文字，建议加骨架屏提升体验。
4. **步骤保存状态持久化**：当前 `stepStore` 为内存状态，页面刷新后 `dirty` 标记丢失，可能导致未保存内容静默丢失。

---

## 发布建议

**CONDITIONAL SHIP** — 满足以下条件后可发布：

- [ ] BUG-01 修复（`current_step` 字段）
- [ ] BUG-02 修复（AI 端点鉴权）
- [ ] 端到端人工验收（登录 → 创建项目 → AI 生成 → 接受候选）至少走通一次

BUG-03、BUG-04 可列入下一版本修复，不阻塞当前发布。
