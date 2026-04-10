"""输出处理管道

JSON 解析 → schema 校验 → fallback
"""

import json
import logging
import os
import re
from typing import Any, Optional

import jsonschema

logger = logging.getLogger(__name__)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")


def load_schema(schema_name: str) -> dict:
    """加载 JSON schema 文件"""
    path = os.path.join(SCHEMA_DIR, f"{schema_name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_json_from_text(text: str) -> Optional[str]:
    """从 LLM 输出中提取 JSON 字符串

    处理常见情况：
    1. 纯 JSON 输出
    2. 包含 ```json ... ``` 代码块
    3. JSON 前后有额外文字
    """
    text = text.strip()

    # 尝试直接解析
    if text.startswith("{"):
        return text

    # 尝试提取 ```json ... ``` 代码块
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 尝试找到第一个 { 到最后一个 } 的范围
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return None


def parse_json_output(text: str) -> dict:
    """解析 LLM 输出为 JSON dict，失败抛出 ValueError"""
    json_str = extract_json_from_text(text)
    if json_str is None:
        raise ValueError(f"No JSON found in LLM output: {text[:200]}...")

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in LLM output: {e}") from e


def validate_output(data: dict, schema_name: str) -> list[str]:
    """用 JSON schema 校验输出，返回错误列表（空列表表示校验通过）"""
    schema = load_schema(schema_name)
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for error in validator.iter_errors(data):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{path}: {error.message}")
    return errors


class OutputPipeline:
    """输出处理管道

    1. 解析 LLM 原始文本为 JSON
    2. 用对应 step 的 output schema 校验
    3. 校验失败时执行 fallback 策略
    """

    def __init__(self, fallback_fn: Any = None):
        self._fallback_fn = fallback_fn

    def process(
        self,
        raw_text: str,
        output_schema_name: str,
    ) -> dict:
        """处理 LLM 输出

        Args:
            raw_text: LLM 原始输出文本
            output_schema_name: 输出 schema 名称（不含 .json 后缀）

        Returns:
            校验通过的 JSON dict

        Raises:
            ValueError: 解析或校验失败且无 fallback
        """
        # Step 1: JSON 解析
        try:
            data = parse_json_output(raw_text)
        except ValueError:
            logger.warning("JSON parse failed, trying fallback")
            if self._fallback_fn:
                return self._fallback_fn(raw_text, output_schema_name)
            raise

        # Step 2: Schema 校验
        errors = validate_output(data, output_schema_name)
        if not errors:
            return data

        logger.warning(f"Schema validation errors: {errors}")

        # Step 3: Fallback
        if self._fallback_fn:
            return self._fallback_fn(raw_text, output_schema_name)

        raise ValueError(f"Output schema validation failed: {errors}")
