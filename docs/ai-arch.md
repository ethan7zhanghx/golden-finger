# 金手指 AI 编剧助手 — AI 系统架构设计

> 版本：v1.0 | 日期：2026-04-09 | 阶段：M1 方案收束
> 来源：ZHA-11 | Owner：AI-Arch
> 模型：ERNIE-5.0（文心一言）

---

## 一、AI 系统设计原则

1. **Workflow-first**：每个步骤的 AI 能力以 workflow 形式定义，而非单次 prompt 调用
2. **Asset-grounded**：所有 AI 生成以项目已确认资产为 context 基础，确保一致性
3. **Human-in-the-loop**：AI 输出默认为候选稿，经人工确认后才写入正式资产
4. **Observable**：每次 AI 调用完整记录 input/output/token/latency/adoption，支持持续优化

---

## 二、ERNIE-5.0 调用架构

### 2.1 调用封装层

```python
# services/ernie_client.py

class ERNIEClient:
    """ERNIE-5.0 统一调用封装"""

    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
        self.model = "ernie-5.0-8k"

    async def chat(
        self,
        messages: list[dict],
        stream: bool = False,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        timeout: int = 120,
    ) -> AsyncGenerator[str, None] | dict:
        """调用 ERNIE-5.0，支持流式和非流式"""
        pass

    async def chat_with_retry(
        self,
        messages: list[dict],
        max_retries: int = 3,
        **kwargs
    ):
        """带重试的调用，指数退避"""
        for attempt in range(max_retries):
            try:
                return await self.chat(messages, **kwargs)
            except RateLimitError:
                await asyncio.sleep(2 ** attempt)
            except TokenLimitError:
                # 截断 context 后重试
                messages = self._truncate_context(messages)
        raise MaxRetriesExceeded()
```

### 2.2 Token 预算控制

| 场景 | 输入 token 上限 | 输出 token 上限 |
|------|----------------|----------------|
| 短文本生成（卖点、钩子） | 2,000 | 1,000 |
| 中等生成（人物卡、叙事策略） | 4,000 | 2,000 |
| 长文本生成（骨架、桥段） | 6,000 | 4,000 |
| 全文分析（节奏分析） | 8,000 | 2,000 |

超出上限时，按以下优先级截断 context：
1. 保留当前步骤的直接依赖资产（全量）
2. 保留间接依赖资产的摘要（前 500 字）
3. 丢弃无关步骤资产

---

## 三、Prompt 工程设计

### 3.1 Prompt 模板结构

每个步骤的每个工具对应一个 prompt 模板，存储在 `prompt_templates` 表中，支持版本管理。

```
[系统角色]
你是一位专业的微短剧编剧助手，正在协助编剧完成{step_name}阶段的创作。

[项目背景]
{project_context}  ← 从已确认资产动态注入

[当前任务]
{task_description}

[输入]
{user_input}

[输出格式]
{output_schema}  ← JSON Schema 约束

[注意事项]
{constraints}
```

### 3.2 各步骤 AI 工具清单

| 步骤 | 工具名 | 输入 | 输出 | 模式 |
|------|--------|------|------|------|
| 市场调研 | `analyze_market` | 题材/类型 | 市场分析报告 | 非流式 |
| 核心卖点 | `generate_selling_points` | 世界观+题材 | 卖点列表（JSON） | 流式 |
| 钩子设计 | `generate_hooks` | 卖点+类型 | 钩子列表（JSON） | 流式 |
| 故事骨架 | `generate_skeleton` | 卖点+钩子+人物 | 骨架框架（JSON） | 异步任务 |
| 桥段 beats | `generate_beats` | 骨架+分集数 | beats 列表（JSON） | 异步任务 |
| 人物卡 | `generate_character` | 故事背景+角色定位 | 人物卡（JSON） | 流式 |
| 叙事策略 | `suggest_narrative` | 骨架+类型 | 叙事策略建议 | 流式 |
| 开头写作 | `generate_opening` | 骨架+人物+叙事策略 | 开头文本 | 流式 |
| 台词改写 | `rewrite_dialogue` | 选中文本+角色信息 | 改写候选 | 流式 |
| 节奏分析 | `analyze_rhythm` | 完整剧本 | 节奏分析报告（JSON） | 非流式 |
| 剧本格式化 | `format_script` | 原始文本 | 标准格式剧本 | 非流式 |

### 3.3 结构化输出校验

所有 JSON 输出通过 Pydantic 模型校验：

```python
# schemas/ai_outputs.py

class SellingPoint(BaseModel):
    title: str = Field(max_length=50)
    description: str = Field(max_length=200)
    target_audience: str
    emotional_hook: str

class SellingPointsOutput(BaseModel):
    selling_points: list[SellingPoint] = Field(min_length=3, max_length=8)
    recommended_index: int  # 推荐主卖点索引

class Character(BaseModel):
    name: str
    role: Literal["protagonist", "antagonist", "supporting"]
    background: str = Field(max_length=500)
    personality_traits: list[str] = Field(max_length=5)
    character_arc: str = Field(max_length=300)
    relationships: list[dict]  # {character_name, relationship_type}
```

校验失败时的处理策略：
1. 尝试修复（提示 ERNIE 重新输出符合 schema 的内容，最多 2 次）
2. 仍失败则返回 `validation_failed` 状态，前端展示错误原因

---

## 四、RAG 方案设计

### 4.1 哪些资产需要向量化

| 资产类型 | 向量化时机 | 用途 |
|----------|-----------|------|
| 世界观设定 | 确认后立即 | 所有后续步骤的 context 注入 |
| 人物卡 | 确认后立即 | 台词写作、开头写作的角色一致性 |
| 核心卖点 | 确认后立即 | 骨架生成的方向约束 |
| 骨架框架 | 确认后立即 | 桥段生成、节奏分析 |
| 桥段 beats | 按集确认后 | 台词写作的情节一致性 |

### 4.2 检索策略

```python
# services/rag_service.py

async def retrieve_context(
    project_id: str,
    step_code: str,
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.75,
) -> list[str]:
    """
    检索与当前步骤相关的项目资产 context
    优先级：直接依赖资产（全量）> 相似度检索（top-k）
    """
    # 1. 加载当前步骤的直接依赖资产（全量，不走向量检索）
    direct_deps = STEP_DEPENDENCIES[step_code]
    direct_context = await load_assets(project_id, direct_deps)

    # 2. 向量检索补充相关 context
    query_embedding = await embed(query)
    similar_chunks = await vector_search(
        project_id=project_id,
        embedding=query_embedding,
        top_k=top_k,
        threshold=similarity_threshold,
        exclude_step_codes=direct_deps,  # 避免重复
    )

    return direct_context + [c.content for c in similar_chunks]
```

### 4.3 步骤依赖关系

```python
STEP_DEPENDENCIES = {
    "core-selling-points": ["worldview", "market-research"],
    "hooks": ["core-selling-points", "worldview"],
    "story-structure": ["core-selling-points", "hooks", "worldview"],
    "plot-beats": ["story-structure", "characters"],
    "characters": ["worldview", "story-structure"],
    "narrative-method": ["story-structure", "characters"],
    "opening": ["story-structure", "characters", "narrative-method"],
    "dialogue": ["plot-beats", "characters", "narrative-method"],
    "rhythm": ["plot-beats", "dialogue"],
    "script-format": ["dialogue", "opening"],
    "synopsis": ["story-structure", "characters", "script-format"],
    "copyright": ["synopsis", "script-format"],
}
```

---

## 五、AI 可观测性设计

### 5.1 tool_runs 记录规范

每次 AI 工具调用必须写入 `tool_runs` 表，包含：

```python
ToolRun(
    project_id=project_id,
    step_code=step_code,
    tool_name=tool_name,
    input_snapshot={
        "user_input": user_input,
        "context_assets": context_summary,  # 注入的资产摘要（非全量，控制存储）
        "prompt_version": prompt_version,
    },
    output_snapshot={
        "raw_output": raw_llm_output,
        "parsed_output": parsed_result,
        "validation_status": "success" | "failed",
    },
    prompt_template_id=template_id,
    prompt_version=prompt_version,
    model_name="ernie-5.0",
    tokens_used=token_count,
    latency_ms=latency,
    status="success" | "failed" | "partial",
    adopted=None,  # 由前端在用户确认/拒绝时回调更新
)
```

### 5.2 采纳率追踪

前端在用户点击"接受候选稿"或"重新生成"时，回调更新 `tool_runs.adopted`：

```
POST /api/v1/ai/runs/{run_id}/feedback
Body: { adopted: true | false, rejection_reason?: string }
```

### 5.3 关键监控指标

| 指标 | 计算方式 | 告警阈值 |
|------|----------|----------|
| 工具采纳率 | adopted=true / total runs | < 40% 触发 prompt 优化 |
| 生成成功率 | status=success / total | < 90% 触发告警 |
| 平均首 token 延迟 | avg(latency_ms) | > 5s 触发告警 |
| 校验失败率 | validation_failed / total | > 10% 触发 schema 审查 |
| 每项目 token 消耗 | sum(tokens_used) by project | 超预算时提示用户 |

---

## 六、AI Guardrails

### 6.1 输入限制

```python
INPUT_LIMITS = {
    "max_user_input_chars": 2000,      # 用户输入最大字符数
    "max_project_title_chars": 100,
    "max_asset_content_chars": 10000,  # 单个资产最大字符数
}

def validate_input(user_input: str, step_code: str) -> str:
    """输入清洗：截断超长输入，过滤敏感词"""
    if len(user_input) > INPUT_LIMITS["max_user_input_chars"]:
        user_input = user_input[:INPUT_LIMITS["max_user_input_chars"]]
    # 内容安全过滤（调用百度内容审核 API）
    return sanitize(user_input)
```

### 6.2 输出限制

- 所有输出经 Pydantic schema 校验，不符合格式的输出不返回给前端
- 输出内容经百度内容安全 API 过滤（涉政、涉黄、涉暴）
- 单次生成 token 上限硬限制，超出时截断并标记 `partial`

### 6.3 并发控制

- 同一用户同时最多 2 个 AI 生成任务（短任务）
- 骨架/桥段等长任务同时最多 1 个（通过 Celery 任务队列控制）
- 超出限制时返回 429，前端提示"请等待当前生成完成"

---

## 七、Handoff 契约（给 BE-Dev）

BE-Dev 在实现时需遵循以下接口契约：

### 7.1 AI 服务接口

```python
# BE-Dev 需实现的 AIOrchestrationService 接口
class AIOrchestrationService:
    async def generate_stream(
        self,
        project_id: str,
        step_code: str,
        tool_name: str,
        user_input: dict,
    ) -> AsyncGenerator[GenerateChunk, None]:
        """流式生成，yield GenerateChunk"""
        pass

    async def generate_async(
        self,
        project_id: str,
        step_code: str,
        tool_name: str,
        user_input: dict,
    ) -> str:
        """提交异步任务，返回 task_id"""
        pass
```

### 7.2 tool_runs 写入时机

- 流式任务：生成完成后（`[DONE]` 事件后）写入
- 异步任务：Celery 任务完成后写入
- 失败任务：捕获异常后写入（status=failed）

### 7.3 Prompt 模板加载

BE-Dev 通过 `prompt_template_id` + `version` 从 DB 加载模板，不硬编码 prompt 字符串。
