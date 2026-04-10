"""Prompt 模板加载器

从 YAML 文件加载 prompt 模板，并渲染变量。
"""

import os
from typing import Any

import yaml

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def load_prompt(step_code: str) -> dict:
    """加载指定步骤的 prompt 模板"""
    path = os.path.join(PROMPTS_DIR, f"{step_code}.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def render_prompt(template: str, variables: dict[str, Any]) -> str:
    """用变量渲染 prompt 模板（简单 str.format）"""
    return template.format(**variables)
