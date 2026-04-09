# 金手指 AI 编剧助手 — 后端工程架构设计

> 版本：v1.0 | 日期：2026-04-09 | 阶段：M1 方案收束
> 来源：ZHA-4 | Owner：BE-Dev

---

## 一、技术选型

| 层次 | 选型 | 理由 |
|------|------|------|
| **Web 框架** | FastAPI (Python 3.12) | 原生异步、OpenAPI 自动生成、Pydantic v2 数据校验、SSE 支持好 |
| **数据库** | PostgreSQL 16 + pgvector | 关系型数据 + 向量检索一体，避免引入独立向量库 |
| **缓存/队列** | Redis 7 | 会话缓存、任务队列 broker、SSE 连接状态 |
| **异步任务** | Celery 5 + Redis broker | AI 长任务（骨架生成 60-180s）异步化，支持进度回调 |
| **ORM** | SQLAlchemy 2 (async) + Alembic | 异步 ORM，迁移管理 |
| **认证** | JWT (python-jose) + bcrypt | 无状态认证，适合前后端分离 |
| **容器化** | Docker Compose | 本地开发 + 云服务器部署统一 |

---

## 二、系统分层架构

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Next.js)                    │
└──────────────────────┬──────────────────────────────┘
                       │ REST + SSE
┌──────────────────────▼──────────────────────────────┐
│              FastAPI 应用层                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │ Auth API │ │Project API│ │  AI API  │             │
│  └──────────┘ └──────────┘ └──────────┘             │
│  ┌──────────────────────────────────────┐            │
│  │         Service Layer                │            │
│  │  ProjectService / AssetService       │            │
│  │  AIOrchestrationService              │            │
│  └──────────────────────────────────────┘            │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  PostgreSQL  │ │  Redis   │ │  Celery      │
│  + pgvector  │ │  Cache   │ │  Workers     │
└──────────────┘ └──────────┘ └──────────────┘
                                      │
                              ┌───────▼───────┐
                              │  ERNIE-5.0    │
                              │  API (百度)   │
                              └───────────────┘
```

---

## 三、核心数据模型

### 3.1 数据库表设计

```sql
-- 用户
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 项目
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    genre VARCHAR(100),
    current_step_code VARCHAR(50) DEFAULT 'writer-quality',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 项目资产（正式资产）
CREATE TABLE project_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    step_code VARCHAR(50) NOT NULL,
    asset_type VARCHAR(100) NOT NULL,
    content JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, step_code, asset_type)
);

-- 资产版本历史
CREATE TABLE asset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES project_assets(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI 工具运行记录（可观测性）
CREATE TABLE tool_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    step_code VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    input_snapshot JSONB,
    output_snapshot JSONB,
    prompt_template_id UUID,
    prompt_version INTEGER,
    model_name VARCHAR(100) DEFAULT 'ernie-5.0',
    tokens_used INTEGER,
    latency_ms INTEGER,
    status VARCHAR(50),  -- success / failed / partial
    adopted BOOLEAN,     -- 用户是否采纳了输出
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prompt 模板版本管理
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step_code VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    template TEXT NOT NULL,
    variables JSONB,     -- 模板变量定义
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(step_code, tool_name, version)
);

-- 向量索引（RAG 用）
CREATE TABLE asset_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES project_assets(id) ON DELETE CASCADE,
    content_chunk TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON asset_embeddings USING ivfflat (embedding vector_cosine_ops);
```

---

## 四、API 设计

### 4.1 认证

```
POST /api/v1/auth/register    # 注册
POST /api/v1/auth/login       # 登录，返回 JWT
POST /api/v1/auth/refresh     # 刷新 token
```

### 4.2 项目管理

```
GET    /api/v1/projects              # 项目列表
POST   /api/v1/projects              # 创建项目
GET    /api/v1/projects/{id}         # 项目详情
PATCH  /api/v1/projects/{id}         # 更新项目
DELETE /api/v1/projects/{id}         # 删除项目
```

### 4.3 资产管理

```
GET    /api/v1/projects/{id}/assets/{step_code}          # 获取步骤资产
PUT    /api/v1/projects/{id}/assets/{step_code}          # 写入/更新资产（确认候选稿）
GET    /api/v1/projects/{id}/assets/{step_code}/versions # 版本历史
POST   /api/v1/projects/{id}/assets/{step_code}/rollback # 回滚到指定版本
```

### 4.4 AI 生成（SSE 流式）

```
POST /api/v1/ai/generate
# Body: { project_id, step_code, tool_name, input }
# Response: text/event-stream
# Events: { type: "chunk", data: "..." } | { type: "done" } | { type: "error", message: "..." }

POST /api/v1/ai/generate/abort
# Body: { run_id }
# 中止正在进行的生成任务
```

### 4.5 异步任务（长任务）

```
POST /api/v1/tasks/generate-skeleton   # 提交骨架生成任务
GET  /api/v1/tasks/{task_id}/status    # 查询任务状态
GET  /api/v1/tasks/{task_id}/result    # 获取任务结果
```

---

## 五、Celery 异步任务设计

```python
# tasks/ai_tasks.py

@celery_app.task(bind=True, max_retries=3)
def generate_skeleton_task(self, project_id: str, input_data: dict):
    """骨架生成长任务（预计 60-180s）"""
    try:
        # 1. 从 DB 加载项目资产作为 context
        # 2. 调用 ERNIE-5.0 API（分步生成）
        # 3. 结构化解析输出
        # 4. 写入 tool_runs 记录
        # 5. 通过 Redis Pub/Sub 推送进度
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)

@celery_app.task
def generate_beats_task(project_id: str, skeleton_asset_id: str):
    """桥段 beats 生成（依赖骨架资产）"""
    pass
```

---

## 六、项目目录结构

```
backend/
  app/
    api/
      v1/
        auth.py
        projects.py
        assets.py
        ai.py
        tasks.py
    core/
      config.py          # 环境变量配置
      security.py        # JWT 工具
      database.py        # SQLAlchemy async engine
    models/
      user.py
      project.py
      asset.py
      tool_run.py
      prompt_template.py
    services/
      project_service.py
      asset_service.py
      ai_orchestration_service.py
      rag_service.py
    tasks/
      celery_app.py
      ai_tasks.py
    main.py
  alembic/
    versions/
    env.py
  docker-compose.yml
  .env.example
  requirements.txt
```

---

## 七、Docker Compose 配置

```yaml
version: '3.9'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - postgres
      - redis

  worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    env_file: .env
    depends_on:
      - postgres
      - redis

  beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info
    env_file: .env
    depends_on:
      - redis

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: golden_finger
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## 八、非功能性要求

| 指标 | 目标 |
|------|------|
| API 响应时间（非 AI） | P95 ≤ 200ms |
| AI 首 token 延迟 | ≤ 3s |
| 骨架生成任务超时 | 300s |
| 数据库连接池 | 最大 20 连接 |
| JWT 有效期 | access 1h / refresh 7d |
| 日志级别 | INFO（生产），DEBUG（开发） |

---

## 九、待对齐事项（与 ZHA-11 AI-Arch）

- `tool_runs` 表的 `input_snapshot` / `output_snapshot` 字段 schema 需与 AI-Arch 的 prompt 模板变量定义对齐
- RAG 检索策略（top-k、相似度阈值）由 AI-Arch 决策后，`rag_service.py` 按方案实现
- ERNIE-5.0 API 调用封装（重试、fallback、token 预算）由 AI-Arch 设计接口契约，BE-Dev 实现
