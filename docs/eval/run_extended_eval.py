#!/usr/bin/env python3
"""
金手指 AI 评测脚本 v2.0 — 基于 ai-eval-framework.md

改进：
- 10 种题材 eval set（非单一固定输入）
- LLM-as-Judge（使用 ERNIE-5.0 自评，标注局限性）
- 多维内容质量打分（具体性/一致性/题材契合/独特性等）
- Slice 报告（按题材 × 步骤 × 模型）

API key 仅运行时传入，严禁提交到 Git。
"""

import json
import os
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# API 配置（运行时从环境变量读取）
# ─────────────────────────────────────────────
QIANFAN_API_KEY = os.environ.get("QIANFAN_API_KEY", "")
QIANFAN_BASE_URL = "https://qianfan.baidubce.com/v2/chat/completions"

SCRIPT_DIR = Path(__file__).parent
EVAL_SET_PATH = SCRIPT_DIR / "eval_set.json"

# ─────────────────────────────────────────────
# 世界观 prompt
# ─────────────────────────────────────────────
WORLDVIEW_SYSTEM = """你是一位资深微短剧编剧顾问，擅长世界观设计。
你的任务是根据用户提供的创意、题材和背景信息，输出一份结构化的世界观设定卡。

要求：
1. 输出必须是严格的 JSON 格式，不要有任何 markdown 代码块包裹
2. 世界观设定必须具体、可拍摄、有画面感
3. 避免空泛的描述，每个字段都要有实质内容
4. 时代背景、社会规则、核心冲突三者必须逻辑自洽"""

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

# ─────────────────────────────────────────────
# LLM-as-Judge prompt（worldview）
# ─────────────────────────────────────────────
JUDGE_WORLDVIEW_SYSTEM = """你是一位资深微短剧制片人和内容评审专家。
你的任务是对 AI 生成的世界观设定卡进行专业质量评分。
请严格按 JSON 格式输出，不要有任何额外文字。"""

JUDGE_WORLDVIEW_USER_TMPL = """请对以下 AI 生成的世界观设定卡进行评分：

【原始输入】
题材：{genre}，受众：{audience}
创意：{idea}

【AI 生成的世界观设定卡】
{worldview_json}

请对以下维度逐项打分（0-5分整数），并给出简短理由：
1. specificity（具体性）：设定是否足够具体有画面感（0=空泛，5=极具体可落地）
2. consistency（内部一致性）：背景/规则/冲突是否逻辑自洽（0=矛盾明显，5=完全自洽）
3. filmability（可拍摄性）：是否适合短剧实际制作（0=无法拍摄，5=高度可执行）
4. genre_fit（题材契合）：是否符合输入的题材和受众定位（0=完全不符，5=高度匹配）
5. originality（独特性）：是否真正区别于同类题材（0=高度雷同，5=高度原创）

严格输出以下 JSON，不要有任何其他内容：
{{
  "scores": {{"specificity": X, "consistency": X, "filmability": X, "genre_fit": X, "originality": X}},
  "rationale": {{"specificity": "...", "consistency": "...", "filmability": "...", "genre_fit": "...", "originality": "..."}},
  "overall_comment": "一句话总评",
  "red_flags": []
}}"""


def call_qianfan(model: str, system: str, user: str, temperature: float = 0.7) -> dict:
    """调用千帆 API，返回 {content, usage, latency_ms, error}"""
    if not QIANFAN_API_KEY:
        return {"content": None, "usage": {}, "latency_ms": 0, "error": "QIANFAN_API_KEY not set"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": 3000,
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QIANFAN_API_KEY}",
    }
    body = json.dumps(payload).encode()

    start = time.time()
    try:
        req = urllib.request.Request(QIANFAN_BASE_URL, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=150) as resp:
            latency_ms = int((time.time() - start) * 1000)
            raw = json.loads(resp.read().decode())
            content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = raw.get("usage", {})
            return {"content": content, "usage": usage, "latency_ms": latency_ms, "error": None}
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return {"content": None, "usage": {}, "latency_ms": latency_ms, "error": str(e)}


def extract_json(text: str) -> dict | None:
    """从文本中提取 JSON 对象"""
    if not text:
        return None
    text = text.strip()
    # 去除 markdown 代码块
    if "```" in text:
        lines = text.split("\n")
        in_block = False
        clean_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block or not line.strip().startswith("```"):
                if not line.strip().startswith("```"):
                    clean_lines.append(line)
        text = "\n".join(clean_lines).strip()
    try:
        return json.loads(text)
    except Exception:
        # 尝试找到第一个 { 到最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass
    return None


def validate_worldview(obj: dict) -> list[str]:
    """校验 worldview schema，返回错误列表"""
    required = ["title", "era_setting", "social_rules", "core_conflict", "visual_style", "taboos", "unique_elements"]
    errors = []
    for f in required:
        if f not in obj:
            errors.append(f"missing field: {f}")
    if "social_rules" in obj and not isinstance(obj["social_rules"], list):
        errors.append("social_rules must be array")
    if "visual_style" in obj and not isinstance(obj["visual_style"], list):
        errors.append("visual_style must be array")
    return errors


def judge_worldview(worldview_json: dict, input_data: dict, judge_model: str) -> dict:
    """使用 LLM 对 worldview 输出评分"""
    user_prompt = JUDGE_WORLDVIEW_USER_TMPL.format(
        genre=input_data.get("genre", ""),
        audience=input_data.get("audience", ""),
        idea=input_data.get("idea", ""),
        worldview_json=json.dumps(worldview_json, ensure_ascii=False, indent=2),
    )
    result = call_qianfan(judge_model, JUDGE_WORLDVIEW_SYSTEM, user_prompt, temperature=0.3)
    if result["error"]:
        return {"error": result["error"], "scores": None}

    parsed = extract_json(result["content"])
    if not parsed or "scores" not in parsed:
        return {"error": f"judge parse failed: {result['content'][:200]}", "scores": None}
    return {"error": None, "scores": parsed.get("scores", {}), "rationale": parsed.get("rationale", {}),
            "overall_comment": parsed.get("overall_comment", ""), "red_flags": parsed.get("red_flags", [])}


def compute_worldview_score(schema_pass: bool, judge_result: dict) -> dict:
    """合并自动分和 LLM Judge 分"""
    # L1: 结构合规 (满分20)
    l1_score = 20 if schema_pass else 0

    # L2: LLM Judge (各维度，满分各5分，合计80分)
    l2_score = 0
    weights = {"specificity": 20, "consistency": 20, "filmability": 15, "genre_fit": 15, "originality": 10}
    l2_detail = {}
    if judge_result.get("scores"):
        scores = judge_result["scores"]
        for dim, weight in weights.items():
            raw = scores.get(dim, 0)
            # 原始0-5分，转换为该维度满分
            normalized = (raw / 5.0) * weight
            l2_detail[dim] = {"raw": raw, "weighted": round(normalized, 1)}
            l2_score += normalized

    total = round(l1_score + l2_score, 1)
    return {
        "total": total,
        "l1_schema": l1_score,
        "l2_content": round(l2_score, 1),
        "l2_detail": l2_detail,
        "red_flags": judge_result.get("red_flags", []),
        "overall_comment": judge_result.get("overall_comment", ""),
    }


def run_eval(models: list[str], judge_model: str, rounds: int = 3) -> dict:
    """主评测函数：10题材 × N模型 × M轮"""
    eval_set = json.loads(EVAL_SET_PATH.read_text())
    results = {
        "metadata": {
            "run_time": datetime.now().isoformat(),
            "models": models,
            "judge_model": judge_model,
            "rounds": rounds,
            "eval_set_size": len(eval_set),
            "note": "LLM-as-Judge 使用与生成相同的 ERNIE-5.0，存在自评偏差，待换用独立 Judge 校准"
        },
        "by_model": {}
    }

    for model in models:
        print(f"\n{'='*60}")
        print(f"模型: {model}")
        print(f"{'='*60}")
        model_results = []

        for item in eval_set:
            genre_id = item["id"]
            genre_label = item["genre_label"]
            input_data = item["input"]

            print(f"\n  题材 [{genre_id}] {genre_label}:")
            genre_rounds = []

            for r in range(1, rounds + 1):
                print(f"    第 {r}/{rounds} 轮 ", end="", flush=True)

                # 生成 worldview
                user_prompt = WORLDVIEW_USER_TMPL.format(
                    idea=input_data.get("idea", ""),
                    genre=input_data.get("genre", ""),
                    era=input_data.get("era", ""),
                    audience=input_data.get("audience", ""),
                    extra_notes=input_data.get("extra_notes", ""),
                )
                gen_result = call_qianfan(model, WORLDVIEW_SYSTEM, user_prompt)
                print(f"gen({gen_result['latency_ms']}ms) ", end="", flush=True)

                round_data = {
                    "round": r,
                    "latency_ms": gen_result["latency_ms"],
                    "tokens": gen_result["usage"].get("total_tokens", 0),
                    "schema_pass": False,
                    "schema_errors": [],
                    "judge": None,
                    "score": None,
                    "error": gen_result["error"],
                }

                if gen_result["error"]:
                    print(f"✗ ERROR: {gen_result['error'][:60]}")
                    genre_rounds.append(round_data)
                    continue

                parsed = extract_json(gen_result["content"])
                if not parsed:
                    print(f"✗ JSON parse failed")
                    round_data["schema_errors"] = ["JSON parse failed"]
                    genre_rounds.append(round_data)
                    continue

                schema_errors = validate_worldview(parsed)
                round_data["schema_pass"] = len(schema_errors) == 0
                round_data["schema_errors"] = schema_errors

                # LLM-as-Judge 评分
                judge_result = judge_worldview(parsed, input_data, judge_model)
                print(f"judge({'' if not judge_result['error'] else 'err'}) ", end="", flush=True)
                round_data["judge"] = judge_result

                score = compute_worldview_score(round_data["schema_pass"], judge_result)
                round_data["score"] = score

                flag = "✓" if round_data["schema_pass"] else "✗"
                score_str = f"{score['total']}/100" if score else "N/A"
                print(f"{flag} schema={'pass' if round_data['schema_pass'] else 'fail'} score={score_str}")
                if score.get("red_flags"):
                    print(f"      ⚠ red_flags: {score['red_flags']}")

                genre_rounds.append(round_data)
                time.sleep(0.5)

            model_results.append({
                "genre_id": genre_id,
                "genre_label": genre_label,
                "rounds": genre_rounds,
            })

        results["by_model"][model] = model_results

    return results


def compute_summary(results: dict) -> dict:
    """计算汇总统计"""
    summary = {"by_model": {}, "by_genre": {}, "cross_model_comparison": []}

    for model, genre_list in results["by_model"].items():
        model_stats = {
            "total_rounds": 0, "schema_pass": 0, "schema_pass_rate": 0,
            "scores": [], "latencies": [], "tokens": [],
            "red_flag_rounds": 0, "by_genre": {}
        }

        for genre_data in genre_list:
            gid = genre_data["genre_id"]
            glabel = genre_data["genre_label"]
            genre_stats = {"schema_pass": 0, "total": 0, "scores": [], "latencies": []}

            for rnd in genre_data["rounds"]:
                model_stats["total_rounds"] += 1
                genre_stats["total"] += 1
                if rnd["latency_ms"]:
                    model_stats["latencies"].append(rnd["latency_ms"])
                    genre_stats["latencies"].append(rnd["latency_ms"])
                if rnd["tokens"]:
                    model_stats["tokens"].append(rnd["tokens"])
                if rnd["schema_pass"]:
                    model_stats["schema_pass"] += 1
                    genre_stats["schema_pass"] += 1
                if rnd["score"] and rnd["score"]["total"] > 0:
                    model_stats["scores"].append(rnd["score"]["total"])
                    genre_stats["scores"].append(rnd["score"]["total"])
                if rnd["score"] and rnd["score"].get("red_flags"):
                    model_stats["red_flag_rounds"] += 1

            genre_stats["schema_pass_rate"] = round(genre_stats["schema_pass"] / genre_stats["total"] * 100, 1) if genre_stats["total"] else 0
            genre_stats["score_avg"] = round(sum(genre_stats["scores"]) / len(genre_stats["scores"]), 1) if genre_stats["scores"] else None
            genre_stats["latency_avg"] = round(sum(genre_stats["latencies"]) / len(genre_stats["latencies"])) if genre_stats["latencies"] else None
            model_stats["by_genre"][gid] = {"label": glabel, **genre_stats}

        total = model_stats["total_rounds"]
        model_stats["schema_pass_rate"] = round(model_stats["schema_pass"] / total * 100, 1) if total else 0
        model_stats["score_avg"] = round(sum(model_stats["scores"]) / len(model_stats["scores"]), 1) if model_stats["scores"] else None
        model_stats["score_p10"] = sorted(model_stats["scores"])[int(len(model_stats["scores"]) * 0.1)] if len(model_stats["scores"]) >= 5 else None
        model_stats["latency_avg"] = round(sum(model_stats["latencies"]) / len(model_stats["latencies"])) if model_stats["latencies"] else None
        model_stats["latency_p95"] = sorted(model_stats["latencies"])[int(len(model_stats["latencies"]) * 0.95)] if len(model_stats["latencies"]) >= 3 else None
        model_stats["token_avg"] = round(sum(model_stats["tokens"]) / len(model_stats["tokens"])) if model_stats["tokens"] else None
        model_stats["red_flag_rate"] = round(model_stats["red_flag_rounds"] / total * 100, 1) if total else 0
        summary["by_model"][model] = model_stats

    return summary


def generate_report(results: dict, summary: dict) -> str:
    """生成 Markdown 报告"""
    meta = results["metadata"]
    lines = [
        "# AI 生成质量扩展评测报告（10题材 × 多模型）",
        "",
        f"**运行时间**: {meta['run_time']}",
        f"**评测框架**: ai-eval-framework.md v1.0",
        f"**题材数量**: {meta['eval_set_size']} 种（G01-G10）",
        f"**每题材轮次**: {meta['rounds']}",
        f"**Judge 模型**: {meta['judge_model']}（注：与生成模型相同，存在自评偏差，待独立 Judge 校准）",
        "",
        "---",
        "",
        "## 评分维度说明（worldview 步骤）",
        "",
        "| 维度 | 满分 | 评分方式 |",
        "|------|------|---------|",
        "| 结构合规 (L1) | 20 | 自动：JSON schema 完整性 |",
        "| 具体性 | 20 | LLM Judge：设定细节丰富度 |",
        "| 内部一致性 | 20 | LLM Judge：背景/规则/冲突逻辑自洽 |",
        "| 可拍摄性 | 15 | LLM Judge：短剧制作可行性 |",
        "| 题材契合度 | 15 | LLM Judge：与输入题材/受众匹配 |",
        "| 独特性 | 10 | LLM Judge：区别于同类题材 |",
        "",
        "---",
        "",
        "## 多模型综合对比",
        "",
        "| 模型 | Schema通过率 | 平均质量分(/100) | P10质量分 | 平均Latency | P95 Latency | 平均Token | Red-flag率 |",
        "|------|-------------|----------------|----------|------------|------------|---------|-----------|",
    ]

    for model, stats in summary["by_model"].items():
        lines.append(
            f"| {model} | {stats['schema_pass_rate']}% | "
            f"{stats['score_avg'] or 'N/A'} | "
            f"{stats['score_p10'] or 'N/A'} | "
            f"{stats['latency_avg'] or 'N/A'}ms | "
            f"{stats['latency_p95'] or 'N/A'}ms | "
            f"{stats['token_avg'] or 'N/A'} | "
            f"{stats['red_flag_rate']}% |"
        )

    lines += ["", "---", "", "## 分题材 Slice（Schema通过率 × 质量分）", ""]

    # Build genre slice table
    all_genre_ids = []
    for genre_data_list in results["by_model"].values():
        for gd in genre_data_list:
            if gd["genre_id"] not in all_genre_ids:
                all_genre_ids.append(gd["genre_id"])

    models = list(results["by_model"].keys())
    header = "| 题材 |" + "".join(f" {m} Schema% | {m} 质量分 |" for m in models)
    sep = "|------|" + "".join("|---|---|" for _ in models)
    lines.append(header)
    lines.append(sep)

    genre_labels = {gd["genre_id"]: gd["genre_label"] for gd_list in results["by_model"].values() for gd in gd_list}
    for gid in all_genre_ids:
        row = f"| [{gid}] {genre_labels.get(gid, '')} |"
        for model in models:
            gs = summary["by_model"].get(model, {}).get("by_genre", {}).get(gid, {})
            row += f" {gs.get('schema_pass_rate', 'N/A')}% | {gs.get('score_avg', 'N/A')} |"
        lines.append(row)

    lines += ["", "---", "", "## Release Gate 检查", ""]
    lines.append("| 模型 | schema≥90% | quality_p50≥65 | red_flag≤10% | 综合判定 |")
    lines.append("|------|-----------|---------------|------------|---------|")
    for model, stats in summary["by_model"].items():
        schema_ok = (stats["schema_pass_rate"] or 0) >= 90
        quality_ok = (stats["score_avg"] or 0) >= 65
        rflag_ok = (stats["red_flag_rate"] or 0) <= 10
        verdict = "PASS" if (schema_ok and quality_ok and rflag_ok) else "BLOCKER"
        lines.append(
            f"| {model} | {'✅' if schema_ok else '❌'} | {'✅' if quality_ok else '❌'} | "
            f"{'✅' if rflag_ok else '❌'} | **{verdict}** |"
        )

    lines += [
        "",
        "---",
        "",
        "## 局限性与诚实声明",
        "",
        "| 局限 | 影响 |",
        "|------|------|",
        "| LLM-as-Judge 使用与生成相同的模型 | Judge 可能存在自我偏好，需独立模型校准 |",
        "| 每题材仅 3 轮 | 统计显著性有限，p10 参考意义有限 |",
        "| 仅覆盖 worldview 步骤 | selling_point 和 hook 的内容质量尚未评测 |",
        "| 无人工标注对齐 | LLM Judge 分与真实商业价值的相关性未知 |",
        "",
        "---",
        "",
        "## 下一步",
        "",
        "1. [ ] 实现 selling_point 和 hook 的 LLM Judge 评分",
        "2. [ ] 引入独立 Judge 模型（Claude/GPT）校准自评偏差",
        "3. [ ] 完成 100+ 条人工标注，对齐 LLM Judge 与商业价值",
        "4. [ ] 补测 claude-sonnet-4-6 和 gpt-5.4（待 API 可用）",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    models = ["ernie-5.0", "deepseek-v3.2"]
    judge_model = "ernie-5.0"
    rounds = 3

    print(f"开始扩展评测: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模型: {', '.join(models)}")
    print(f"题材: 10种 (G01-G10)")
    print(f"每题材轮次: {rounds}")
    print(f"Judge: {judge_model}")

    results = run_eval(models, judge_model, rounds)
    summary = compute_summary(results)
    report = generate_report(results, summary)

    # 保存
    raw_path = SCRIPT_DIR / "extended_eval_raw.json"
    report_path = SCRIPT_DIR / "extended_eval_report.md"

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "summary": summary}, f, ensure_ascii=False, indent=2)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n\n{'='*60}")
    print(report)
    print(f"\n报告已保存: {report_path}")
    print(f"原始数据已保存: {raw_path}")
