# 视觉设计规范 v1.0

> **背景**：用户反馈当前工作台视觉质量不达标，与竞品 Laper 差距明显。本文档从 UI/UX 视角完成设计审计、视觉差距分析，并给出完整视觉设计规范供 FE 落地。

---

## 一、竞品对比审计（Laper vs 当前）

### Visual Verdict

| 维度 | 当前状态 | Laper | Gap 等级 |
|------|---------|-------|----------|
| 编辑区沉浸感 | 被边框框住，高度受限，有压迫感 | 白纸悬浮在灰背景，无边界感 | 🔴 严重 |
| 版式专业度 | 通用富文本编辑器 | 剧本专属格式（场次/动作/对话/括注/转场） | 🔴 严重 |
| 色彩体系 | 随意 amber+gray，无体系 | 暖绿+米白+深棕，有品牌感 | 🟠 重要 |
| 字体排版 | prose-sm 通用样式 | 大字号、宽行距、剧本等宽字体 | 🟠 重要 |
| 左侧导航 | w-64 纯文本列表 | 精细图标+文字，场次列表 | 🟡 中等 |
| 顶部导航 | 无 | 剧本/封面/格式切换 Tab | 🟡 中等 |
| AI 面板 | 常驻右侧 280px，挤压编辑区 | 左上角轻提示，不占主体位置 | 🟠 重要 |
| 底部时间线 | 无 | 节拍结构时间线，直观展示故事结构 | 🟡 中等（P2） |

**综合评分：3.5 / 10**（当前），**目标：7.5 / 10**（本次迭代完成后）

---

## 二、设计原则

针对剧本创作工具的核心场景——长时间沉浸式文字创作，我们的设计原则：

1. **纸感优先（Paper-first）**：编辑区模拟白纸，让创作者忘记"软件"，只感受"写作"
2. **信息层级清晰**：背景 < 纸张 < 内容 < 工具，四层分明
3. **温暖克制**：暖色调体现创意氛围，不过度装饰
4. **工具不打扰创作**：AI 面板、格式工具栏默认收起或悬浮，按需出现

---

## 三、色彩系统

```
Brand Colors
──────────────────────────────────────────────────────────
Primary / Ink       #2D2A26   深棕墨色，主文字、强调元素
Primary / Warm      #7C6F5B   暖棕，次级文字、图标
Accent / Gold       #C8974A   金琥珀，品牌主色（按钮、激活态）
Accent / Gold Light #F5E6C8   浅金，激活背景

Surface Colors
──────────────────────────────────────────────────────────
Canvas              #F0EDE8   编辑区外底色（暖灰）
Paper               #FAFAF8   编辑区纸张色（近白）
Paper Shadow        rgba(0,0,0,0.06)  纸张投影

Neutral Colors
──────────────────────────────────────────────────────────
Sidebar BG          #F7F4EF   左侧导航背景
Border              #E8E4DC   分割线、边框
Muted Text          #9B8F7E   辅助文字
Placeholder         #C0B8AE   占位符文字

Semantic Colors
──────────────────────────────────────────────────────────
Success             #4A7C59   完成状态
Warning             #C8974A   警告（复用 Gold）
Error               #C0392B   错误
AI Highlight        #5B7FA6   AI 生成内容高亮
```

---

## 四、字体系统

### 字体栈

```css
/* 界面 UI 字体 */
--font-ui: "PingFang SC", "Helvetica Neue", sans-serif;

/* 剧本内容字体（等宽感强，专业感） */
--font-script: "Noto Serif SC", "Source Han Serif SC", Georgia, serif;

/* 代码 / 格式标记 */
--font-mono: "Courier Prime", "Courier New", monospace;
```

### 字号阶梯

| Token | 大小 | 行高 | 用途 |
|-------|------|------|------|
| `text-xs` | 11px | 1.5 | 辅助标签、元信息 |
| `text-sm` | 13px | 1.6 | 侧边栏列表、工具栏 |
| `text-base` | 15px | 1.8 | 剧本正文（默认） |
| `text-lg` | 18px | 1.9 | 步骤标题 |
| `text-xl` | 22px | 1.3 | 页面大标题 |

### 剧本元素字体规格

| 剧本元素 | 字体 | 大小 | 颜色 | 对齐 | 特殊处理 |
|---------|------|------|------|------|---------|
| 场景标题（Scene Heading）| mono | 15px | #2D2A26 | 左对齐 | 全大写 |
| 动作描述（Action）| serif | 15px | #2D2A26 | 两端对齐 | 正常 |
| 角色名（Character）| mono | 15px | #2D2A26 | 居中 | 全大写 |
| 括注（Parenthetical）| serif | 14px | #7C6F5B | 居中 | 斜体 |
| 对话（Dialogue）| serif | 15px | #2D2A26 | 居中，最大宽35ch | 正常 |
| 转场（Transition）| mono | 14px | #7C6F5B | 右对齐 | 全大写 |

---

## 五、编辑区设计规范（核心）

### 布局结构

```
┌─────────────────────────────────────────────────────────┐
│  TopBar: 项目名 ← → 剧本/封面切换 Tab → 导出/分享按钮      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [左侧导航 w-56]  │  [编辑区 flex-1]  │ [AI面板 折叠态]  │
│                   │                   │                 │
│  步骤树           │  ┌─────────────┐  │  [悬浮按钮触发]  │
│  + 场景列表（P2） │  │   Paper     │  │                 │
│                   │  │             │  │                 │
│                   │  │  内容区域   │  │                 │
│                   │  │             │  │                 │
│                   │  └─────────────┘  │                 │
│                   │                   │                 │
├─────────────────────────────────────────────────────────┤
│  [格式工具栏，仅 richtext 步骤出现，悬浮在 Paper 上方]     │
└─────────────────────────────────────────────────────────┘
```

### Paper 组件规格

```css
/* 纸张容器 */
.paper {
  background: #FAFAF8;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.03);
  border-radius: 4px;

  /* 内边距：上下宽松，左右留白 */
  padding: 48px 64px;

  /* 高度：全视口减去 TopBar + 底部状态栏 */
  min-height: calc(100vh - 120px);

  /* 最大宽度约束：模拟真实纸张，不要无限拉伸 */
  max-width: 720px;
  margin: 24px auto;
}

/* Canvas 背景 */
.canvas {
  background: #F0EDE8;
  padding: 0 24px;
  overflow-y: auto;
  height: calc(100vh - 60px); /* 减去 TopBar */
}
```

### AI 面板改造：从「常驻右侧」→「悬浮触发」

**当前问题**：AI 面板常驻 w-80，压缩中央编辑区，让人感觉"这是 AI 工具界面，不是剧本写作工具"。

**改造方案**：

```
默认态：
  右下角悬浮按钮 [✨ AI 助手]，不占主体空间

展开态（点击触发）：
  右侧抽屉滑出，宽 320px，半透明遮罩
  编辑区不缩小，抽屉覆盖在上层

AI 生成流式内容：
  在 Paper 内以浅蓝色背景高亮展示候选内容
  工具栏出现 [采纳] [放弃] 两个操作
```

---

## 六、左侧导航设计规范

### 尺寸与颜色

```css
.step-nav {
  width: 224px;        /* 从 256px 缩到 224px */
  background: #F7F4EF;
  border-right: 1px solid #E8E4DC;
  padding: 16px 0;
}
```

### 阶段标题

```
字体：11px，letter-spacing: 0.08em，全大写
颜色：#9B8F7E
padding：0 20px，margin-bottom 8px
```

### 步骤项（未激活 / 激活 / 完成）

```css
/* 通用 */
.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 16px;
  margin: 1px 8px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

/* 未激活 */
.step-item--default {
  color: #7C6F5B;
  background: transparent;
}
.step-item--default:hover {
  background: #EDE9E2;
  color: #2D2A26;
}

/* 激活 */
.step-item--active {
  background: #F5E6C8;   /* 浅金 */
  color: #2D2A26;
  font-weight: 600;
}
/* 激活项左侧有 2px 金色竖条 */
.step-item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 20%;
  height: 60%;
  width: 2px;
  background: #C8974A;
  border-radius: 0 1px 1px 0;
}

/* 完成 */
.step-item--done {
  color: #7C6F5B;
}
.step-item--done .icon {
  color: #4A7C59;  /* 绿色对勾 */
}
```

---

## 七、格式工具栏（剧本 richtext 步骤专用）

仅在剧本类步骤（开头写作、对话场景等）出现，悬浮在 Paper 顶部。

### 视觉规格

```css
.format-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: rgba(250, 250, 248, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid #E8E4DC;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);

  /* 悬浮定位：Paper 顶部居中 */
  position: sticky;
  top: 16px;
  z-index: 10;
  width: fit-content;
  margin: 0 auto 16px;
}
```

### 格式按钮组

```
[场次] [动作] [角色] [括注] [对话] [转场]  |  [B] [I] [U]
```

每个剧本格式按钮：
- 宽 48px，高 32px
- 图标（12px）+ 文字（11px）垂直排列
- 激活时：background #F5E6C8，底部 2px solid #C8974A
- Hover 时：background #EDE9E2

---

## 八、交互状态规范

### Loading 态
- Skeleton Loader：Paper 内显示 3-4 行浅灰色骨架块
- 颜色：`#E8E4DC` → `#F0EDE8` 渐变动画（shimmer）
- 不使用 spinner，避免打破纸张沉浸感

### Empty 态
- Paper 中央显示：大号浅灰图标 + "开始你的创作" 提示
- 颜色：`#C0B8AE`，字号 14px
- 点击任意区域聚焦到编辑器

### Error 态
- Paper 顶部出现一条细线 toast（高 36px）
- 背景 `rgba(192,57,43,0.08)`，左边 3px 红色竖条
- 不使用全屏遮罩，不打断创作

### AI 生成中
- 流式输出：字符逐个出现，光标闪烁
- 背景：`rgba(91,127,166,0.06)` 浅蓝高亮
- 右上角 [停止生成] 按钮

---

## 九、FE Handoff Checklist

实现时需逐项确认：

- [ ] Canvas 背景色 `#F0EDE8` 替换 `bg-white`
- [ ] Paper 组件独立封装，含投影和圆角
- [ ] Paper `max-w-[720px] mx-auto`，`min-h-[calc(100vh-120px)]`
- [ ] Paper `padding: 48px 64px`（响应式：移动端 24px 16px）
- [ ] 左侧导航从 `w-64 bg-gray-50` 改为 `w-56 bg-[#F7F4EF]`
- [ ] 步骤激活态从 `bg-amber-50` 改为 `bg-[#F5E6C8]`，加左竖条
- [ ] AI 面板改为悬浮抽屉，默认折叠，右下角 FAB 触发
- [ ] 格式工具栏：剧本类步骤才显示，含6种剧本元素格式
- [ ] 编辑区字体：正文使用 Noto Serif SC
- [ ] 场景标题/角色名使用等宽字体且全大写
- [ ] 完成态图标色 `#4A7C59`，非 `text-green-500`
- [ ] 移除所有 `border border-gray-200` 的编辑框边框（改用 Paper 投影代替）

---

## 十、设计取舍说明

| 取舍点 | 决策 | 理由 |
|-------|------|------|
| AI 面板移出主区域 | 采用 | 编辑沉浸感 > AI 可见性，用户主动唤出更合理 |
| 底部时间线（P2） | 推迟 | 当前核心场景是写作，时间线需要数据结构支持，单独排期 |
| 移动端适配 | 推迟 | 剧本创作主要在桌面端，移动端后续排期 |
| 多主题（深色模式） | 推迟 | 先做好一套暖色主题 |
| 剧本自动格式化（智能识别元素类型） | P2 | 需要 AI 联动，先支持手动格式选择 |

---

*文档版本：v1.0 / 2026-04-10*
*作者：UI/UX Agent*
*关联 issue：[ZHA-22](mention://issue/a02d8689-30be-4459-9217-24f6d16988de)*
