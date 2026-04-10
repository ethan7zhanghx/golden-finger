# AI 生成质量 Baseline 评测报告

**运行时间**: 2026-04-10 16:08:30  
**评测轮次**: 5 轮/模型/步骤  
**评测样本**: 固定单一输入（赛博朋克悬疑微短剧）  

---

## 评测方法

### 步骤
| 步骤 | 说明 |
|------|------|
| worldview | 世界观设定卡生成 |
| selling_point | 核心卖点提炼 |
| hook | 爽点 & 钩子库设计 |

### Rubric 说明（满分 10 分）

**worldview**: schema_compliance(3) + specificity(3) + consistency(2) + uniqueness(2)
**selling_point**: schema_compliance(3) + logline_quality(2) + selling_point_count(2) + priority_order(1) + differentiation(2)
**hook**: schema_compliance(3) + highlights_count(2) + hooks_count(2) + position_variety(2) + emotion_curve(1)

---

## 分步骤结果

### 世界观（worldview）

| 模型 | Schema通过率 | 平均Rubric(/10) | 平均Latency(ms) | P95 Latency(ms) | 平均Token数 |
|------|-------------|----------------|----------------|----------------|------------|
| ERNIE-5.0 | 60% | 8.0 | 75780 | 117494 | 2123 |
| DeepSeek-V3.2 | 100% | 8.2 | 38074 | 45046 | 1248 |
| GPT-5.4 | 0% | 0.0 | 1219 | 1862 | 0 |

### 卖点（selling_point）

| 模型 | Schema通过率 | 平均Rubric(/10) | 平均Latency(ms) | P95 Latency(ms) | 平均Token数 |
|------|-------------|----------------|----------------|----------------|------------|
| ERNIE-5.0 | 100% | 10.0 | 69000 | 77930 | 2680 |
| DeepSeek-V3.2 | 40% | 10.0 | 27230 | 29539 | 1830 |
| GPT-5.4 | N/A | N/A | N/A | N/A | N/A |

### 钩子（hook）

| 模型 | Schema通过率 | 平均Rubric(/10) | 平均Latency(ms) | P95 Latency(ms) | 平均Token数 |
|------|-------------|----------------|----------------|----------------|------------|
| ERNIE-5.0 | 100% | 10.0 | 97356 | 107744 | 3935 |
| DeepSeek-V3.2 | 50% | 10.0 | 83110 | 99797 | 4146 |
| GPT-5.4 | N/A | N/A | N/A | N/A | N/A |

---

## 多模型横向对比（三步平均）

| 模型 | 整体Schema通过率 | 整体Rubric均分 | 整体平均Latency | 整体平均Token |
|------|----------------|--------------|----------------|--------------|
| ERNIE-5.0 | 87% | 9.3 | 80712 ms | 2913 |
| DeepSeek-V3.2 | 63% | 9.4 | 49471 ms | 2408 |
| GPT-5.4 | 0% | 0.0 | 1219 ms | 0 |

---

## 错误汇总

**GPT-5.4 / worldview**: HTTP Error 403: Forbidden

---

## Verification & Limitations

- **已验证**: Schema 校验通过率基于实际 API 响应，JSON 结构比对确认
- **样本量**: 每模型每步骤 5 轮，共 15 轮/模型
- **局限**: 固定单一输入（不代表全量场景多样性）；Rubric 为规则化自动评分，未做人工标注
- **Blocker**: 组 C（claude-4.6-sonnet）未评测，待附件确认后推进

## Suggested Next Step

1. PM 验收本次 baseline 结果
2. 选定 baseline 最优模型（推荐以 schema_pass_rate 为主要 gate）
3. 设计多样化 eval set（≥10 种不同题材输入）做鲁棒性验证
4. 确认组 C claude-4.6-sonnet 附件后补测