"""爽点和钩子 workflow

输入组装 → LLM 调用 → 输出解析
"""

from ..ernie_client import ChatMessage, ErnieClient
from ..output_pipeline import OutputPipeline, validate_output
from ..prompt_loader import load_prompt, render_prompt


def hook_workflow(
    input_data: dict,
    client: ErnieClient,
    pipeline: OutputPipeline,
) -> dict:
    """爽点和钩子 workflow

    Args:
        input_data: 符合 hook_input schema 的输入
        client: ERNIE 客户端
        pipeline: 输出处理管道

    Returns:
        符合 hook_output schema 的爽点库和钩子库
    """
    # 1. 校验输入
    input_errors = validate_output(input_data, "hook_input")
    if input_errors:
        raise ValueError(f"Invalid input: {input_errors}")

    # 2. 加载并渲染 prompt
    prompt_config = load_prompt("hook")
    system_prompt = prompt_config["system"]
    user_prompt = render_prompt(
        prompt_config["user_template"],
        {
            "worldview_json": input_data["worldview_json"],
            "selling_points_json": input_data["selling_points_json"],
            "audience": input_data.get("audience", "18-35岁女性"),
            "style_preference": input_data.get("style_preference", ""),
        },
    )

    # 3. 调用 LLM
    params = prompt_config.get("parameters", {})
    response = client.chat(
        messages=[ChatMessage(role="user", content=user_prompt)],
        system=system_prompt,
        temperature=params.get("temperature", 0.8),
        top_p=params.get("top_p", 0.9),
        max_output_tokens=params.get("max_output_tokens", 3072),
    )

    # 4. 输出解析与校验
    return pipeline.process(response.content, "hook_output")
