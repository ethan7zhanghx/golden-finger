"""核心卖点提炼 workflow

输入组装 → LLM 调用 → 输出解析
"""

from ..ernie_client import ChatMessage, ErnieClient
from ..output_pipeline import OutputPipeline, validate_output
from ..prompt_loader import load_prompt, render_prompt


def selling_point_workflow(
    input_data: dict,
    client: ErnieClient,
    pipeline: OutputPipeline,
) -> dict:
    """核心卖点提炼 workflow

    Args:
        input_data: 符合 selling_point_input schema 的输入
        client: ERNIE 客户端
        pipeline: 输出处理管道

    Returns:
        符合 selling_point_output schema 的卖点卡
    """
    # 1. 校验输入
    input_errors = validate_output(input_data, "selling_point_input")
    if input_errors:
        raise ValueError(f"Invalid input: {input_errors}")

    # 2. 加载并渲染 prompt
    prompt_config = load_prompt("selling_point")
    system_prompt = prompt_config["system"]
    user_prompt = render_prompt(
        prompt_config["user_template"],
        {
            "worldview_json": input_data["worldview_json"],
            "genre": input_data["genre"],
            "audience": input_data.get("audience", "18-35岁女性"),
        },
    )

    # 3. 调用 LLM
    params = prompt_config.get("parameters", {})
    response = client.chat(
        messages=[ChatMessage(role="user", content=user_prompt)],
        system=system_prompt,
        temperature=params.get("temperature", 0.7),
        top_p=params.get("top_p", 0.9),
        max_output_tokens=params.get("max_output_tokens", 2048),
    )

    # 4. 输出解析与校验
    return pipeline.process(response.content, "selling_point_output")
