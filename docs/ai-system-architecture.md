# 金手指 AI 系统架构 — 前 3 步 Workflow 设计

> 版本：v0.1 | 日期：2026-04-10 | Owner：AI-Arch Agent

## 1. 概述

本文档定义金手指 AI 编剧助手前 3 个创作步骤（世界观设定、核心卖点提炼、爽点和钩子）的 AI workflow 实现架构。

**设计原则**：workflow-first、asset-grounded、tool-assisted
- 固定工作流管理步骤推进和上下文衔接
- 专用生成模块处理各步骤核心创作任务
- 结构化校验保证输出质量

## 2. 架构概览

```
用户输入 → WorkflowRouter → step workflow → ErnieClient → OutputPipeline → 结构化资产
                                   ↑                            ↓
                            PromptLoader                  JSON Schema 校验
                          (YAML 模板渲染)                    + fallback
```

### 核心组件

| 组件 | 职责 | 文件 |
|------|------|------|
| ErnieClient | ERNIE-5.0 API 调用（OAuth2、流式、重试） | `src/ernie_client.py` |
| PromptLoader | 加载 YAML prompt 模板并渲染变量 | `src/prompt_loader.py` |
| WorkflowRouter | 根据 step_code 路由到对应 workflow | `src/workflow_router.py` |
| OutputPipeline | JSON 解析 → schema 校验 → fallback | `src/output_pipeline.py` |
| Step Workflows | 各步骤的具体执行逻辑 | `src/workflows/*.py` |

## 3. 数据流

### Step 1: 世界观设定 (worldview)
- **输入**：创意概述、题材类型、时代背景、目标受众
- **输出**：世界观卡（名称、时代设定、社会规则、核心矛盾、视觉风格、禁忌、独特元素）
- **依赖**：无上游依赖

### Step 2: 核心卖点提炼 (selling_point)
- **输入**：世界观卡 JSON、题材、受众
- **输出**：logline + 卖点列表 + 定位 + 差异化要素
- **依赖**：worldview 输出

### Step 3: 爽点和钩子 (hook)
- **输入**：世界观卡 JSON、卖点卡 JSON、受众、风格偏好
- **输出**：爽点库（5-8 个）+ 钩子库（5-8 个）+ 情绪曲线建议
- **依赖**：worldview + selling_point 输出

## 4. 质量保障

- 每步输入/输出均有 JSON Schema 约束（`schemas/` 目录）
- OutputPipeline 三级处理：JSON 提取 → schema 校验 → fallback
- ErnieClient 自动重试 3 次
- 单元测试 19 项全部通过（mock LLM 端到端验证）

## 5. 文件结构

```
golden-finger/
├── docs/
│   └── ai-system-architecture.md    # 本文档
├── src/
│   ├── __init__.py
│   ├── ernie_client.py              # ERNIE-5.0 客户端封装
│   ├── prompt_loader.py             # Prompt 模板加载器
│   ├── workflow_router.py           # 步骤路由器
│   ├── output_pipeline.py           # 输出处理管道
│   └── workflows/
│       ├── __init__.py
│       ├── worldview.py             # 世界观设定 workflow
│       ├── selling_point.py         # 核心卖点 workflow
│       └── hook.py                  # 爽点和钩子 workflow
├── prompts/
│   ├── worldview.yaml               # 世界观 prompt 模板
│   ├── selling_point.yaml           # 卖点 prompt 模板
│   └── hook.yaml                    # 钩子 prompt 模板
├── schemas/
│   ├── worldview_input.json
│   ├── worldview_output.json
│   ├── selling_point_input.json
│   ├── selling_point_output.json
│   ├── hook_input.json
│   └── hook_output.json
└── tests/
    ├── __init__.py
    └── test_workflows.py            # 19 项单元测试
```

## 6. 后续扩展

- 接入真实 ERNIE API 后需配置 `api_key` / `secret_key`
- 后续步骤（骨架框架、剧情桥段等）可复用同一 WorkflowRouter + OutputPipeline 架构
- 可增加 RAG 模块为后续步骤注入项目上下文
- 可增加 evaluator 模块做输出质量评分
