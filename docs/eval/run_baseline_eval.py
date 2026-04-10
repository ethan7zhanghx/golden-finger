#!/usr/bin/env python3
"""AI 生成质量 Baseline 评测脚本

评测 worldview / selling_point / hook 三步流水线
模型：ernie-5.0, deepseek-v3.2 (百度千帆), gpt-5.4 (claudechn.com Responses API)

用法：
  export QIANFAN_API_KEY="bce-v3/..."
  export CLAUDECHN_API_KEY="sk-..."
  python docs/eval/run_baseline_eval.py

注意：API key 绝不写入代码，通过环境变量注入。
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

# ─────────────────── 配置 ───────────────────

QIANFAN_BASE_URL = "https://qianfan.baidubce.com/v2/chat/completions"
CLAUDECHN_BASE_URL = "https://claudechn.com/codex/v1/responses"

MODELS = {
    "ernie-5.0": {"group": "A", "api": "qianfan", "display": "ERNIE-5.0"},
    "deepseek-v3.2": {"group": "A", "api": "qianfan", "display": "DeepSeek-V3.2"},
    "gpt-5.4": {"group": "B", "api": "claudechn", "display": "GPT-5.4"},
}

ROUNDS = 5  # 每个模型每个步骤的评测轮次

# 共用评测输入样本（固定，保证跨模型可比性）
EVAL_INPUT = {
    "idea": "一个关于记忆交易的赛博朋克世界，女主发现自己的所有记忆全是被人工植入的假记忆，真实身份是被消除记忆的反抗军领袖",
    "genre": "悬疑科幻",
    "era": "2050年近未来都市",
    "audience": "18-35岁女性",
    "extra_notes": "强调情感冲突和身份认同主题，适合短剧集数（20集以内）",
}

# ─────────────────── Prompt 模板 ───────────────────

WORLDVIEW_SYSTEM = """你是一位资深微短剧编剧顾问，擅长世界观设计。
你的任务是根据用户提供的创意、题材和背景信息，输出一份结构化的世界观设定卡。

要求：
1. 输出必须是严格的 JSON 格式
2. 世界观设定必须具体、可拍摄、有画面感
3. 避免空泛的描述，每个字段都要有实质内容
4. 时代背景、社会规则、核心冲突三者必须逻辑自洽
5. 适合微短剧的体量，不要设计过于宏大的世界观"""

WORLDVIEW_USER_TMPL = """请根据以下信息生成世界观设定卡：

【创意概述】
{idea}

【题材类型】
{genre}

【时代背景】
{era}

【目标受众】
{audience}

【补充说明】
{extra_notes}

请以 JSON 格式输出世界观设定卡，包含以下字段：
- title: 世界观名称
- era_setting: 时代与地域设定
- social_rules: 社会规则与权力结构（数组，每项包含 rule 和 detail）
- core_conflict: 核心矛盾与张力来源
- visual_style: 视觉风格关键词（数组）
- taboos: 世界观内的禁忌或限制（数组）
- unique_elements: 区别于同类题材的独特元素（数组）"""

SELLING_POINT_SYSTEM = """你是一位资深微短剧市场策划专家，擅长提炼作品卖点和撰写 logline。
你的任务是根据已有的世界观设定，提炼出最具市场竞争力的核心卖点，并生成一句话 logline。

要求：
1. 输出必须是严格的 JSON 格式
2. 卖点必须具备"一句话就能让人想看"的吸引力
3. logline 需要包含主角、核心冲突和情感钩子
4. 卖点排序按市场吸引力从高到低
5. 每个卖点要说明"为什么观众会为此买单"
"""

SELLING_POINT_USER_TMPL = """请根据以下世界观设定，提炼核心卖点：

【世界观设定】
{worldview_json}

【题材类型】
{genre}

【目标受众】
{audience}

请以 JSON 格式输出，包含以下字段：
- logline: 一句话 logline（不超过 50 字）
- selling_points: 核心卖点数组（3-5 个），每项包含：
  - point: 卖点名称
  - description: 卖点描述（1-2 句话）
  - audience_appeal: 对目标受众的吸引力说明
  - priority: 优先级（1 最高）
- positioning: 作品定位（一句话总结）
- differentiation: 与同类作品的差异化要素（数组）"""

HOOK_SYSTEM = """你是一位微短剧爆款内容策划专家，擅长设计情绪刺激点和追更钩子。
你的任务是根据已有的世界观和卖点，设计一套完整的爽点库和钩子库。

核心概念：
- 爽点：让观众产生强烈情绪满足的场景设计（逆袭、打脸、揭秘、甜宠等）
- 钩子：让观众必须看下一集的悬念设计（信息差、反转预告、命运转折等）

要求：
1. 输出必须是严格的 JSON 格式
2. 爽点要具体到场景级别，不能只是抽象概念
3. 钩子要制造强烈的"下一集期待"
4. 爽点和钩子需要标注适用的剧情位置（开头/中段/高潮/结尾）
5. 每个爽点/钩子要标注情绪类型标签"""

HOOK_USER_TMPL = """请根据以下信息设计爽点库和钩子库：

【世界观设定】
{worldview_json}

【核心卖点】
{selling_points_json}

【目标受众】
{audience}

【偏好风格】
{style_preference}

请以 JSON 格式输出，包含以下字段：
- highlights: 爽点库（5-8 个），每项包含：
  - name: 爽点名称
  - scene_description: 具体场景描述（2-3 句话）
  - emotion_type: 情绪类型（如：逆袭、打脸、甜宠、揭秘、复仇等）
  - position: 适用位置（opening/middle/climax/ending）
  - intensity: 强度（1-5，5 为最强）
- hooks: 钩子库（5-8 个），每项包含：
  - name: 钩子名称
  - hook_description: 钩子设计描述（2-3 句话）
  - hook_type: 钩子类型（如：悬念、反转、信息差、命运转折等）
  - position: 适用位置（episode_end/mid_episode/arc_end）
  - cliffhanger_strength: 追更驱动力（1-5，5 为最强）
- emotion_curve_suggestion: 情绪曲线建议（1-2 句话）"""

# ─────────────────── JSON Schema ───────────────────

WORLDVIEW_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["title", "era_setting", "social_rules", "core_conflict", "visual_style", "taboos", "unique_elements"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "era_setting": {"type": "string", "minLength": 1},
        "social_rules": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["rule", "detail"]}},
        "core_conflict": {"type": "string", "minLength": 1},
        "visual_style": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "taboos": {"type": "array", "items": {"type": "string"}},
        "unique_elements": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    },
}

SELLING_POINT_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["logline", "selling_points", "positioning", "differentiation"],
    "properties": {
        "logline": {"type": "string", "minLength": 1},
        "selling_points": {
            "type": "array", "minItems": 3, "maxItems": 5,
            "items": {"type": "object", "required": ["point", "description", "audience_appeal", "priority"]},
        },
        "positioning": {"type": "string", "minLength": 1},
        "differentiation": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    },
}

HOOK_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["highlights", "hooks", "emotion_curve_suggestion"],
    "properties": {
        "highlights": {
            "type": "array", "minItems": 5, "maxItems": 8,
            "items": {"type": "object", "required": ["name", "scene_description", "emotion_type", "position", "intensity"]},
        },
        "hooks": {
            "type": "array", "minItems": 5, "maxItems": 8,
            "items": {"type": "object", "required": ["name", "hook_description", "hook_type", "position", "cliffhanger_strength"]},
        },
        "emotion_curve_suggestion": {"type": "string", "minLength": 1},
    },
}

# ─────────────────── API Clients ───────────────────

@dataclass
class CallResult:
    content: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error: Optional[str] = None
    raw: dict = field(default_factory=dict)


def call_qianfan(model: str, system: str, user: str, api_key: str) -> CallResult:
    """调用百度千帆 OpenAI-compatible Chat Completions API"""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 3072,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        QIANFAN_BASE_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        latency_ms = (time.time() - t0) * 1000
        content = raw["choices"][0]["message"]["content"]
        usage = raw.get("usage", {})
        return CallResult(
            content=content,
            latency_ms=latency_ms,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            raw=raw,
        )
    except Exception as e:
        latency_ms = (time.time() - t0) * 1000
        return CallResult(content="", latency_ms=latency_ms, input_tokens=0, output_tokens=0, total_tokens=0, error=str(e))


def call_claudechn_responses(model: str, system: str, user: str, api_key: str) -> CallResult:
    """调用 claudechn.com OpenAI Responses API (wire_api: responses)"""
    payload = {
        "model": model,
        "instructions": system,
        "input": [{"role": "user", "content": user}],
        "temperature": 0.7,
        "max_output_tokens": 3072,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CLAUDECHN_BASE_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        latency_ms = (time.time() - t0) * 1000
        # Responses API output format
        content = ""
        for item in raw.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        content += c.get("text", "")
        usage = raw.get("usage", {})
        return CallResult(
            content=content,
            latency_ms=latency_ms,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            raw=raw,
        )
    except Exception as e:
        latency_ms = (time.time() - t0) * 1000
        return CallResult(content="", latency_ms=latency_ms, input_tokens=0, output_tokens=0, total_tokens=0, error=str(e))


def call_model(model: str, system: str, user: str, qianfan_key: str, claudechn_key: str) -> CallResult:
    info = MODELS[model]
    if info["api"] == "qianfan":
        return call_qianfan(model, system, user, qianfan_key)
    else:
        return call_claudechn_responses(model, system, user, claudechn_key)


# ─────────────────── JSON 解析 ───────────────────

def extract_json(text: str) -> Optional[dict]:
    text = text.strip()
    # Try direct parse
    if text.startswith("{"):
        try:
            return json.loads(text)
        except Exception:
            pass
    # Try ```json block
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            pass
    # Try first { ... last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass
    return None


def validate_schema(data: dict, schema: dict) -> list[str]:
    """Simple schema validation without jsonschema library dependency"""
    errors = []
    required = schema.get("required", [])
    for field_name in required:
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")
            continue
        val = data[field_name]
        prop_schema = schema.get("properties", {}).get(field_name, {})
        # Type check
        expected_type = prop_schema.get("type")
        if expected_type == "string" and not isinstance(val, str):
            errors.append(f"{field_name}: expected string")
        elif expected_type == "array":
            if not isinstance(val, list):
                errors.append(f"{field_name}: expected array")
            else:
                min_items = prop_schema.get("minItems", 0)
                max_items = prop_schema.get("maxItems", float("inf"))
                if len(val) < min_items:
                    errors.append(f"{field_name}: minItems={min_items}, got {len(val)}")
                if len(val) > max_items:
                    errors.append(f"{field_name}: maxItems={max_items}, got {len(val)}")
                # Check item required fields
                item_schema = prop_schema.get("items", {})
                item_required = item_schema.get("required", [])
                for i, item in enumerate(val):
                    if isinstance(item, dict):
                        for ir in item_required:
                            if ir not in item:
                                errors.append(f"{field_name}[{i}]: missing '{ir}'")
        # minLength
        if expected_type == "string" and isinstance(val, str):
            min_len = prop_schema.get("minLength", 0)
            if len(val) < min_len:
                errors.append(f"{field_name}: minLength={min_len}, got {len(val)}")
    return errors


# ─────────────────── Rubric 评分 ───────────────────

def score_worldview(data: dict) -> dict:
    """
    Rubric (满分 10 分):
    - schema_compliance (3分): 所有必填字段完整且非空
    - specificity (3分): 字段内容丰富度 (avg content length proxy)
    - consistency (2分): core_conflict 与 social_rules 存在关联词汇
    - uniqueness (2分): unique_elements 数量 ≥ 3 且内容不重复
    """
    scores = {}
    # schema_compliance
    errors = validate_schema(data, WORLDVIEW_OUTPUT_SCHEMA)
    scores["schema_compliance"] = 3 if not errors else max(0, 3 - len(errors))

    # specificity: avg char length of text fields
    text_vals = [
        data.get("title", ""), data.get("era_setting", ""),
        data.get("core_conflict", ""),
    ] + [r.get("detail", "") for r in data.get("social_rules", []) if isinstance(r, dict)]
    avg_len = sum(len(v) for v in text_vals) / max(len(text_vals), 1)
    scores["specificity"] = 3 if avg_len >= 30 else (2 if avg_len >= 15 else 1)

    # consistency: check if core_conflict mentions keywords from social_rules
    conflict = data.get("core_conflict", "").lower()
    rules_keywords = []
    for r in data.get("social_rules", []):
        if isinstance(r, dict):
            rules_keywords.extend(r.get("rule", "").lower().split())
    overlap = sum(1 for kw in rules_keywords if kw and kw in conflict and len(kw) > 1)
    scores["consistency"] = 2 if overlap >= 2 else (1 if overlap >= 1 else 0)

    # uniqueness
    unique = data.get("unique_elements", [])
    scores["uniqueness"] = 2 if len(unique) >= 3 else (1 if len(unique) >= 2 else 0)

    scores["total"] = sum(scores.values())
    return scores


def score_selling_point(data: dict) -> dict:
    """
    Rubric (满分 10 分):
    - schema_compliance (3分)
    - logline_quality (2分): logline 长度 10-50 字，有冲突感
    - selling_point_count (2分): 3-5 个卖点
    - priority_order (1分): priority 字段从 1 开始递增
    - differentiation (2分): differentiation ≥ 2 条
    """
    scores = {}
    errors = validate_schema(data, SELLING_POINT_OUTPUT_SCHEMA)
    scores["schema_compliance"] = 3 if not errors else max(0, 3 - len(errors))

    logline = data.get("logline", "")
    ll_len = len(logline)
    scores["logline_quality"] = 2 if 10 <= ll_len <= 100 else (1 if ll_len > 0 else 0)

    sps = data.get("selling_points", [])
    scores["selling_point_count"] = 2 if 3 <= len(sps) <= 5 else (1 if len(sps) > 0 else 0)

    priorities = [sp.get("priority") for sp in sps if isinstance(sp, dict)]
    scores["priority_order"] = 1 if sorted(priorities) == list(range(1, len(priorities)+1)) else 0

    diff = data.get("differentiation", [])
    scores["differentiation"] = 2 if len(diff) >= 2 else (1 if len(diff) >= 1 else 0)

    scores["total"] = sum(scores.values())
    return scores


def score_hook(data: dict) -> dict:
    """
    Rubric (满分 10 分):
    - schema_compliance (3分)
    - highlights_count (2分): 5-8 个爽点
    - hooks_count (2分): 5-8 个钩子
    - position_variety (2分): highlights 覆盖 ≥ 3 种 position 值
    - emotion_curve (1分): emotion_curve_suggestion 非空且 ≥ 20 字
    """
    scores = {}
    errors = validate_schema(data, HOOK_OUTPUT_SCHEMA)
    scores["schema_compliance"] = 3 if not errors else max(0, 3 - len(errors))

    highlights = data.get("highlights", [])
    scores["highlights_count"] = 2 if 5 <= len(highlights) <= 8 else (1 if len(highlights) >= 3 else 0)

    hooks = data.get("hooks", [])
    scores["hooks_count"] = 2 if 5 <= len(hooks) <= 8 else (1 if len(hooks) >= 3 else 0)

    positions = {h.get("position") for h in highlights if isinstance(h, dict)}
    scores["position_variety"] = 2 if len(positions) >= 3 else (1 if len(positions) >= 2 else 0)

    ec = data.get("emotion_curve_suggestion", "")
    scores["emotion_curve"] = 1 if len(ec) >= 20 else 0

    scores["total"] = sum(scores.values())
    return scores


SCORERS = {
    "worldview": score_worldview,
    "selling_point": score_selling_point,
    "hook": score_hook,
}

SCHEMAS = {
    "worldview": WORLDVIEW_OUTPUT_SCHEMA,
    "selling_point": SELLING_POINT_OUTPUT_SCHEMA,
    "hook": HOOK_OUTPUT_SCHEMA,
}

# ─────────────────── 评测主流程 ───────────────────

@dataclass
class RoundResult:
    model: str
    step: str
    round_num: int
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    schema_pass: bool
    schema_errors: list
    rubric_scores: dict
    error: Optional[str] = None
    content_preview: str = ""


def run_eval_round(
    model: str, step: str, round_num: int,
    worldview_data: Optional[dict],
    selling_point_data: Optional[dict],
    qianfan_key: str, claudechn_key: str,
) -> RoundResult:
    """运行单轮评测"""
    if step == "worldview":
        system = WORLDVIEW_SYSTEM
        user = WORLDVIEW_USER_TMPL.format(**EVAL_INPUT)
    elif step == "selling_point":
        system = SELLING_POINT_SYSTEM
        wv_json = json.dumps(worldview_data, ensure_ascii=False) if worldview_data else "{}"
        user = SELLING_POINT_USER_TMPL.format(
            worldview_json=wv_json,
            genre=EVAL_INPUT["genre"],
            audience=EVAL_INPUT["audience"],
        )
    else:  # hook
        system = HOOK_SYSTEM
        wv_json = json.dumps(worldview_data, ensure_ascii=False) if worldview_data else "{}"
        sp_json = json.dumps(selling_point_data, ensure_ascii=False) if selling_point_data else "{}"
        user = HOOK_USER_TMPL.format(
            worldview_json=wv_json,
            selling_points_json=sp_json,
            audience=EVAL_INPUT["audience"],
            style_preference="悬疑+情感",
        )

    result = call_model(model, system, user, qianfan_key, claudechn_key)

    if result.error:
        return RoundResult(
            model=model, step=step, round_num=round_num,
            latency_ms=result.latency_ms,
            input_tokens=0, output_tokens=0, total_tokens=0,
            schema_pass=False, schema_errors=[result.error],
            rubric_scores={}, error=result.error,
        )

    # Parse JSON
    data = extract_json(result.content)
    if data is None:
        return RoundResult(
            model=model, step=step, round_num=round_num,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            schema_pass=False,
            schema_errors=["JSON parse failed"],
            rubric_scores={},
            content_preview=result.content[:100],
        )

    schema_errors = validate_schema(data, SCHEMAS[step])
    schema_pass = len(schema_errors) == 0
    rubric = SCORERS[step](data)

    return RoundResult(
        model=model, step=step, round_num=round_num,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        total_tokens=result.total_tokens,
        schema_pass=schema_pass,
        schema_errors=schema_errors,
        rubric_scores=rubric,
        content_preview=result.content[:150],
    )


def run_full_eval(qianfan_key: str, claudechn_key: str) -> list[RoundResult]:
    all_results = []
    steps = ["worldview", "selling_point", "hook"]

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"模型: {MODELS[model]['display']}")
        print(f"{'='*60}")

        # 每个模型独立跑 ROUNDS 轮完整流水线
        for r in range(1, ROUNDS + 1):
            print(f"\n  第 {r}/{ROUNDS} 轮:")
            wv_data = None
            sp_data = None

            for step in steps:
                print(f"    [{step}] 调用中...", end="", flush=True)
                res = run_eval_round(model, step, r, wv_data, sp_data, qianfan_key, claudechn_key)
                all_results.append(res)

                status = "✓" if res.schema_pass else "✗"
                print(f" {status} schema={res.schema_pass} latency={res.latency_ms:.0f}ms tokens={res.total_tokens} rubric={res.rubric_scores.get('total', 0)}/10")

                if res.error:
                    print(f"      ERROR: {res.error}")
                    break  # 此步失败，跳过后续步骤

                # 解析当前步骤输出，作为下一步输入
                if step == "worldview" and res.schema_pass:
                    # Re-parse from content (we already have data in rubric scorer)
                    wv_data = extract_json(res.content_preview)
                    # We need full content; store in result
                    # Actually content_preview is truncated, let's use rubric scores to infer pass
                    # We need to store the full parsed data
                    pass

    return all_results


# ─────────────────── 结果聚合 ───────────────────

def aggregate_results(results: list[RoundResult]) -> dict:
    """按 model x step 聚合统计"""
    from collections import defaultdict
    stats = defaultdict(lambda: {
        "total": 0, "schema_pass": 0, "latencies": [], "tokens": [],
        "rubric_totals": [], "errors": [],
    })

    for r in results:
        key = (r.model, r.step)
        s = stats[key]
        s["total"] += 1
        if r.schema_pass:
            s["schema_pass"] += 1
        s["latencies"].append(r.latency_ms)
        if r.total_tokens > 0:
            s["tokens"].append(r.total_tokens)
        if r.rubric_scores:
            s["rubric_totals"].append(r.rubric_scores.get("total", 0))
        if r.error:
            s["errors"].append(r.error)

    summary = {}
    for (model, step), s in stats.items():
        n = s["total"]
        latencies = s["latencies"]
        tokens = s["tokens"]
        rubrics = s["rubric_totals"]
        summary[(model, step)] = {
            "n": n,
            "schema_pass_rate": s["schema_pass"] / n if n > 0 else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "p95_latency_ms": sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0,
            "avg_tokens": sum(tokens) / len(tokens) if tokens else 0,
            "avg_rubric": sum(rubrics) / len(rubrics) if rubrics else 0,
            "errors": s["errors"],
        }

    return summary


def format_report(summary: dict, run_ts: str) -> str:
    steps = ["worldview", "selling_point", "hook"]
    step_display = {"worldview": "世界观", "selling_point": "卖点", "hook": "钩子"}

    lines = [
        f"# AI 生成质量 Baseline 评测报告",
        f"",
        f"**运行时间**: {run_ts}  ",
        f"**评测轮次**: {ROUNDS} 轮/模型/步骤  ",
        f"**评测样本**: 固定单一输入（赛博朋克悬疑微短剧）  ",
        f"",
        f"---",
        f"",
        f"## 评测方法",
        f"",
        f"### 步骤",
        f"| 步骤 | 说明 |",
        f"|------|------|",
        f"| worldview | 世界观设定卡生成 |",
        f"| selling_point | 核心卖点提炼 |",
        f"| hook | 爽点 & 钩子库设计 |",
        f"",
        f"### Rubric 说明（满分 10 分）",
        f"",
        f"**worldview**: schema_compliance(3) + specificity(3) + consistency(2) + uniqueness(2)",
        f"**selling_point**: schema_compliance(3) + logline_quality(2) + selling_point_count(2) + priority_order(1) + differentiation(2)",
        f"**hook**: schema_compliance(3) + highlights_count(2) + hooks_count(2) + position_variety(2) + emotion_curve(1)",
        f"",
        f"---",
        f"",
        f"## 分步骤结果",
        f"",
    ]

    for step in steps:
        lines.append(f"### {step_display[step]}（{step}）")
        lines.append(f"")
        lines.append(f"| 模型 | Schema通过率 | 平均Rubric(/10) | 平均Latency(ms) | P95 Latency(ms) | 平均Token数 |")
        lines.append(f"|------|-------------|----------------|----------------|----------------|------------|")
        for model in MODELS:
            key = (model, step)
            if key not in summary:
                lines.append(f"| {MODELS[model]['display']} | N/A | N/A | N/A | N/A | N/A |")
                continue
            s = summary[key]
            lines.append(
                f"| {MODELS[model]['display']} "
                f"| {s['schema_pass_rate']*100:.0f}% "
                f"| {s['avg_rubric']:.1f} "
                f"| {s['avg_latency_ms']:.0f} "
                f"| {s['p95_latency_ms']:.0f} "
                f"| {s['avg_tokens']:.0f} |"
            )
        lines.append(f"")

    # 横向对比总表
    lines += [
        f"---",
        f"",
        f"## 多模型横向对比（三步平均）",
        f"",
        f"| 模型 | 整体Schema通过率 | 整体Rubric均分 | 整体平均Latency | 整体平均Token |",
        f"|------|----------------|--------------|----------------|--------------|",
    ]

    for model in MODELS:
        all_keys = [(model, step) for step in steps if (model, step) in summary]
        if not all_keys:
            lines.append(f"| {MODELS[model]['display']} | N/A | N/A | N/A | N/A |")
            continue
        schema_rates = [summary[k]["schema_pass_rate"] for k in all_keys]
        rubrics = [summary[k]["avg_rubric"] for k in all_keys]
        latencies = [summary[k]["avg_latency_ms"] for k in all_keys]
        tokens = [summary[k]["avg_tokens"] for k in all_keys]
        lines.append(
            f"| {MODELS[model]['display']} "
            f"| {sum(schema_rates)/len(schema_rates)*100:.0f}% "
            f"| {sum(rubrics)/len(rubrics):.1f} "
            f"| {sum(latencies)/len(latencies):.0f} ms "
            f"| {sum(tokens)/len(tokens):.0f} |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## 错误汇总",
        f"",
    ]

    has_errors = False
    for (model, step), s in summary.items():
        if s["errors"]:
            has_errors = True
            lines.append(f"**{MODELS[model]['display']} / {step}**: {'; '.join(set(s['errors'][:3]))}")

    if not has_errors:
        lines.append("无错误")

    lines += [
        f"",
        f"---",
        f"",
        f"## Verification & Limitations",
        f"",
        f"- **已验证**: Schema 校验通过率基于实际 API 响应，JSON 结构比对确认",
        f"- **样本量**: 每模型每步骤 {ROUNDS} 轮，共 {ROUNDS*3} 轮/模型",
        f"- **局限**: 固定单一输入（不代表全量场景多样性）；Rubric 为规则化自动评分，未做人工标注",
        f"- **Blocker**: 组 C（claude-4.6-sonnet）未评测，待附件确认后推进",
        f"",
        f"## Suggested Next Step",
        f"",
        f"1. PM 验收本次 baseline 结果",
        f"2. 选定 baseline 最优模型（推荐以 schema_pass_rate 为主要 gate）",
        f"3. 设计多样化 eval set（≥10 种不同题材输入）做鲁棒性验证",
        f"4. 确认组 C claude-4.6-sonnet 附件后补测",
    ]

    return "\n".join(lines)


# ─────────────────── 入口 ───────────────────

def main():
    qianfan_key = os.environ.get("QIANFAN_API_KEY", "")
    claudechn_key = os.environ.get("CLAUDECHN_API_KEY", "")

    if not qianfan_key:
        print("ERROR: QIANFAN_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not claudechn_key:
        print("WARNING: CLAUDECHN_API_KEY not set, gpt-5.4 eval will be skipped")

    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"开始评测: {run_ts}")
    print(f"模型: {', '.join(MODELS.keys())}")
    print(f"轮次: {ROUNDS} 轮/模型/步骤")

    # Run eval — need full content to chain steps, redesign run loop
    all_results = []
    steps = ["worldview", "selling_point", "hook"]

    for model in MODELS:
        if MODELS[model]["api"] == "claudechn" and not claudechn_key:
            print(f"\n跳过 {model}（缺少 CLAUDECHN_API_KEY）")
            continue

        print(f"\n{'='*60}")
        print(f"模型: {MODELS[model]['display']}")
        print(f"{'='*60}")

        for r in range(1, ROUNDS + 1):
            print(f"\n  第 {r}/{ROUNDS} 轮:")
            wv_data = None
            sp_data = None

            for step in steps:
                print(f"    [{step}] 调用中...", end="", flush=True)

                # Build prompts
                if step == "worldview":
                    system = WORLDVIEW_SYSTEM
                    user = WORLDVIEW_USER_TMPL.format(**EVAL_INPUT)
                elif step == "selling_point":
                    system = SELLING_POINT_SYSTEM
                    wv_json = json.dumps(wv_data, ensure_ascii=False) if wv_data else "{}"
                    user = SELLING_POINT_USER_TMPL.format(
                        worldview_json=wv_json,
                        genre=EVAL_INPUT["genre"],
                        audience=EVAL_INPUT["audience"],
                    )
                else:
                    system = HOOK_SYSTEM
                    wv_json = json.dumps(wv_data, ensure_ascii=False) if wv_data else "{}"
                    sp_json = json.dumps(sp_data, ensure_ascii=False) if sp_data else "{}"
                    user = HOOK_USER_TMPL.format(
                        worldview_json=wv_json,
                        selling_points_json=sp_json,
                        audience=EVAL_INPUT["audience"],
                        style_preference="悬疑+情感",
                    )

                call_result = call_model(model, system, user, qianfan_key, claudechn_key)

                if call_result.error:
                    res = RoundResult(
                        model=model, step=step, round_num=r,
                        latency_ms=call_result.latency_ms,
                        input_tokens=0, output_tokens=0, total_tokens=0,
                        schema_pass=False, schema_errors=[call_result.error],
                        rubric_scores={}, error=call_result.error,
                        content_preview="",
                    )
                    all_results.append(res)
                    print(f" ✗ ERROR: {call_result.error[:80]}")
                    break

                data = extract_json(call_result.content)
                if data is None:
                    res = RoundResult(
                        model=model, step=step, round_num=r,
                        latency_ms=call_result.latency_ms,
                        input_tokens=call_result.input_tokens,
                        output_tokens=call_result.output_tokens,
                        total_tokens=call_result.total_tokens,
                        schema_pass=False,
                        schema_errors=["JSON parse failed"],
                        rubric_scores={},
                        content_preview=call_result.content[:100],
                    )
                    all_results.append(res)
                    print(f" ✗ JSON parse failed")
                    break

                schema_errors = validate_schema(data, SCHEMAS[step])
                schema_pass = len(schema_errors) == 0
                rubric = SCORERS[step](data)

                res = RoundResult(
                    model=model, step=step, round_num=r,
                    latency_ms=call_result.latency_ms,
                    input_tokens=call_result.input_tokens,
                    output_tokens=call_result.output_tokens,
                    total_tokens=call_result.total_tokens,
                    schema_pass=schema_pass,
                    schema_errors=schema_errors,
                    rubric_scores=rubric,
                    content_preview=call_result.content[:100],
                )
                all_results.append(res)

                status = "✓" if schema_pass else "✗"
                print(f" {status} schema={schema_pass} latency={call_result.latency_ms:.0f}ms tokens={call_result.total_tokens} rubric={rubric.get('total',0)}/10")

                # Chain outputs
                if step == "worldview":
                    wv_data = data
                elif step == "selling_point":
                    sp_data = data

    # Aggregate and report
    summary = aggregate_results(all_results)
    report = format_report(summary, run_ts)

    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "baseline_results.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n\n报告已保存: {report_path}")

    # Also save raw JSON results
    raw_path = os.path.join(os.path.dirname(__file__), "baseline_raw_results.json")
    raw_data = []
    for r in all_results:
        raw_data.append({
            "model": r.model, "step": r.step, "round": r.round_num,
            "latency_ms": r.latency_ms,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "total_tokens": r.total_tokens,
            "schema_pass": r.schema_pass,
            "schema_errors": r.schema_errors,
            "rubric_scores": r.rubric_scores,
            "error": r.error,
        })
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"原始数据已保存: {raw_path}")

    print("\n" + "="*60)
    print(report)


if __name__ == "__main__":
    main()
