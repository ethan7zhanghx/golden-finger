# 金手指 AI 编剧助手 — 前端技术方案

> 版本：v1.0 | 日期：2026-04-09 | 阶段：M1 方案收束
> 来源：ZHA-5 | Owner：FE-Dev

---

## 一、技术选型

### 1.1 框架

**选型：Next.js 15 (App Router) + React 19**

理由：
- App Router 的 Server Components 可将静态内容（提示词库、模板库、步骤说明）在服务端渲染，减少客户端 JS 体积
- 内置 Route Handlers 可直接代理 AI 流式接口（SSE/streaming），避免跨域问题
- 文件系统路由与 Layout 嵌套天然匹配工作台"全局 Shell + 项目内 Shell + 步骤内容"三层结构
- Vercel 部署生态成熟，CDN、Edge Functions、Image Optimization 开箱即用
- React 19 的 `use()` + Suspense 对流式 AI 输出有原生支持

### 1.2 UI 组件库

**选型：shadcn/ui（基于 Radix UI + Tailwind CSS）**

理由：
- 组件代码直接复制到项目，完全可定制，不受第三方版本锁定
- Radix UI 提供无障碍（WAI-ARIA）基础，满足可访问性要求
- Tailwind CSS 与 Next.js 集成零配置，设计 token 统一管理
- 相比 Ant Design / MUI，包体积更小，Tree-shaking 更彻底
- 工作台三栏布局、卡片编辑、候选稿对比等复杂 UI 可基于 Radix Primitives 自由组合

补充：图标库使用 **Lucide React**（shadcn/ui 默认配套）。

### 1.3 状态管理

**选型：Zustand（全局状态）+ TanStack Query v5（服务端状态）**

理由：
- Zustand：轻量（~1KB），无 Provider 嵌套，适合工作台内步骤状态、候选稿状态、工具运行状态等跨组件共享
- TanStack Query：处理 API 数据获取、缓存、乐观更新、后台重新验证，与 Next.js App Router 的 Server Actions 可无缝配合
- 两者职责分离：Zustand 管理 UI 交互状态，TanStack Query 管理服务端数据生命周期
- 不引入 Redux/MobX，避免过度工程化

### 1.4 富文本编辑器

**选型：TipTap v2（基于 ProseMirror）**

理由：
- 模块化扩展架构，可按步骤按需加载扩展（如台词写作需要局部改写工具栏，骨架编辑需要大纲折叠）
- 内置 Collaboration 扩展，为后续团队协作预留接口
- 支持 Headless 模式，完全由 Tailwind 控制样式，与 shadcn/ui 风格统一
- 相比 Slate.js：TipTap 文档更完善，社区更活跃，ProseMirror 底层更稳定
- 相比 Quill：TipTap 对 React 18+ 支持更好，无遗留 jQuery 依赖
- AI 改写场景：通过 TipTap Extension 实现"选中文本 → 触发 AI 改写 → 差异高亮预览 → 接受/拒绝"完整交互

### 1.5 图表库

**选型：Recharts（数据图表）+ Mermaid.js（流程图/结构图）**

理由：
- Recharts：基于 React + D3，适合节奏分析报告中的分集 beats 分布图、完成度漏斗等
- Mermaid.js：PRD 中已有大量 Mermaid 图，工作台内展示骨架结构、流程图时可直接渲染
- 两者按需加载，不影响工作台首屏性能

---

## 二、组件架构设计

### 2.1 工作台核心组件树

```
<WorkbenchLayout>                    # 工作台全局 Shell（三栏 + 底部）
  ├── <StepNavigation>               # 左侧：16 步流程导航
  │   ├── <PhaseGroup>               # 阶段分组（准备/策划/创作/完善）
  │   │   └── <StepItem>             # 单步骤条目（状态图标 + 标题 + 展开说明）
  │   └── <ProgressSummary>          # 整体进度摘要
  │
  ├── <MainCreationArea>             # 中央：主创作区（根据步骤切换形态）
  │   ├── <StepHeader>               # 步骤标题 + 状态 + 操作按钮
  │   ├── <ContentRenderer>          # 内容形态路由（5 种形态）
  │   │   ├── <InputFormView>        # 形态1：输入表单型
  │   │   ├── <CardEditView>         # 形态2：卡片编辑型
  │   │   ├── <OutlineEditView>      # 形态3：大纲/分段编辑型
  │   │   ├── <RichTextEditView>     # 形态4：正文编辑 + AI 改写型
  │   │   └── <AnalysisExportView>   # 形态5：分析/导出型
  │   ├── <AICandidatePanel>         # AI 候选稿区（候选态，未写入正式资产）
  │   │   ├── <CandidateCard>        # 单个候选稿卡片
  │   │   └── <CandidateActions>     # 接受/插入/覆盖/重新生成
  │   └── <AssetVersionHistory>      # 历史版本入口（抽屉/弹窗）
  │
  ├── <AssistantPanel>               # 右侧：辅助区
  │   ├── <StepGuide>                # 当前步骤创作要点
  │   ├── <PromptCardList>           # 提示词卡片列表
  │   ├── <QuickNav>                 # 快速导航
  │   └── <StepRules>                # 注意事项
  │
  └── <BottomServiceBar>             # 底部：横向服务区
      ├── <DataAnalysisCard>         # 数据分析
      ├── <SmartSuggestionCard>      # 智能建议
      ├── <TemplateLibraryCard>      # 模板库
      └── <CopyrightCard>            # 版权保护
```

### 2.2 中央区五种内容形态

| 形态 | 组件 | 适用步骤 | 核心子组件 |
|------|------|----------|------------|
| 输入表单型 | `<InputFormView>` | 编剧素质、世界观设定 | `<FormField>`, `<ConstraintCard>`, `<AIGenerateButton>` |
| 卡片编辑型 | `<CardEditView>` | 卖点、钩子、人物卡、叙事策略 | `<AssetCard>`, `<CardSortable>`, `<TagFilter>` |
| 大纲/分段编辑型 | `<OutlineEditView>` | 骨架框架、桥段 beats、剧本介绍 | `<TipTapEditor>` (outline mode), `<BeatItem>`, `<SectionCollapse>` |
| 正文编辑 + AI 改写型 | `<RichTextEditView>` | 开头写作、台词写作 | `<TipTapEditor>` (rich mode), `<InlineAIToolbar>`, `<DiffPreview>` |
| 分析/导出型 | `<AnalysisExportView>` | 节奏控制、剧本格式、版权证书 | `<AnalysisReport>`, `<RhythmChart>`, `<ExportPanel>` |

---

## 三、状态管理方案

### 3.1 Zustand Store 设计

```typescript
// store/workbench.ts — 工作台核心状态
interface WorkbenchStore {
  projectId: string | null;
  currentStepCode: StepCode;
  stepStatuses: Record<StepCode, StepStatus>;
  // StepStatus: 'not_started' | 'draft_generated' | 'manually_edited' | 'confirmed' | 'needs_review'

  toolRunStatus: Record<string, ToolRunStatus>;
  // ToolRunStatus: 'idle' | 'running' | 'success' | 'partial_failed' | 'validation_failed'

  aiCandidates: Record<StepCode, AICandidateItem[]>;
  activeCandidateId: string | null;

  activeBottomService: 'analysis' | 'suggestion' | 'template' | 'copyright' | null;

  setCurrentStep: (code: StepCode) => void;
  updateStepStatus: (code: StepCode, status: StepStatus) => void;
  setAICandidates: (code: StepCode, candidates: AICandidateItem[]) => void;
  acceptCandidate: (candidateId: string) => void;
  setToolRunStatus: (toolId: string, status: ToolRunStatus) => void;
}
```

```typescript
// store/streaming.ts — AI 流式输出状态
interface StreamingStore {
  streams: Record<string, StreamState>;
  // StreamState: { status, buffer, error, abortController }

  startStream: (streamId: string, abortController: AbortController) => void;
  appendChunk: (streamId: string, chunk: string) => void;
  finishStream: (streamId: string) => void;
  abortStream: (streamId: string) => void;
}
```

### 3.2 资产状态流转

```
候选稿（aiCandidates in Zustand）
    ↓ 用户点击"接受"
正式资产（Asset via TanStack Query mutation）
    ↓ 自动创建版本
AssetVersion（历史版本列表）
```

---

## 四、路由设计

```
/                                          # 首页
/projects                                  # 项目列表
/projects/new                              # 新建项目
/projects/[projectId]                      # 工作台（重定向到当前步骤）
/projects/[projectId]/steps/[stepCode]     # 工作台 + 具体步骤
/projects/[projectId]/export               # 导出页
/projects/[projectId]/copyright            # 版权保护页
/templates                                 # 模板库
/prompts                                   # 提示词库
```

**stepCode 枚举：**
`writer-quality` | `market-research` | `worldview` | `core-selling-points` | `hooks` | `story-structure` | `plot-beats` | `characters` | `narrative-method` | `opening` | `dialogue` | `rhythm` | `title` | `script-format` | `synopsis` | `copyright`

**Layout 嵌套：**
```
app/
  layout.tsx                   # 全局 Shell（顶部导航、认证）
  projects/
    [projectId]/
      layout.tsx               # 项目 Shell（WorkbenchLayout 三栏）
      steps/[stepCode]/page.tsx
      export/page.tsx
      copyright/page.tsx
```

---

## 五、AI 流式输出方案

### 5.1 协议：SSE（Server-Sent Events）

选 SSE 而非 WebSocket 的理由：
- 工作台 AI 交互为"用户触发 → 服务端推送"，单向流，SSE 语义更匹配
- 基于 HTTP，Next.js Route Handler 原生支持 `ReadableStream`
- SSE 自动重连机制对网络抖动更友好

### 5.2 Route Handler 实现

```typescript
// app/api/ai/generate/route.ts
export async function POST(req: Request) {
  const { stepCode, input, projectId } = await req.json();

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      for await (const chunk of callAIService(stepCode, input, projectId)) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`));
      }
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    }
  });
}
```

### 5.3 流式状态 UI

| 状态 | UI 表现 |
|------|---------|
| `idle` | 显示"生成"按钮 |
| `running` | 按钮变为"停止生成"，候选稿区显示流式文字（打字机效果） |
| `success` | 候选稿完整展示，显示"接受/插入/覆盖/重新生成"操作 |
| `partial_failed` | 显示已生成内容 + 错误提示 + "重试"按钮 |
| `validation_failed` | 显示校验失败原因 + "重新生成"按钮 |

---

## 六、性能策略

### 6.1 代码分割

```typescript
// 五种内容形态按需加载
const InputFormView = dynamic(() => import('./views/InputFormView'));
const CardEditView = dynamic(() => import('./views/CardEditView'));
const OutlineEditView = dynamic(() => import('./views/OutlineEditView'));
const RichTextEditView = dynamic(() => import('./views/RichTextEditView'));
const AnalysisExportView = dynamic(() => import('./views/AnalysisExportView'));

// 图表库懒加载（仅节奏分析步骤使用）
const RhythmChart = dynamic(() => import('./charts/RhythmChart'), { ssr: false });
```

### 6.2 关键性能目标

| 指标 | 目标 |
|------|------|
| 工作台首屏 LCP | ≤ 2.5s |
| 步骤切换响应 | ≤ 300ms |
| 资产保存响应 | ≤ 500ms（乐观更新） |
| AI 首 token 到达 | ≤ 3s |
| 编辑器输入延迟 | ≤ 16ms（60fps） |

---

## 七、依赖清单

| 包 | 版本 | 用途 |
|----|------|------|
| next | 15.x | 框架 |
| react | 19.x | UI 运行时 |
| @tiptap/react | 2.x | 富文本编辑器 |
| zustand | 5.x | 全局状态 |
| @tanstack/react-query | 5.x | 服务端状态 |
| tailwindcss | 4.x | 样式 |
| recharts | 2.x | 数据图表 |
| mermaid | 11.x | 流程图渲染 |
| lucide-react | latest | 图标 |
| @radix-ui/* | latest | 无障碍原语 |
