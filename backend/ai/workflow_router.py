"""WorkflowRouter

根据 step_code 路由到对应的 workflow 函数。
"""

import logging
from typing import Any, Callable

from .ernie_client import ErnieClient
from .output_pipeline import OutputPipeline

logger = logging.getLogger(__name__)

WorkflowFn = Callable[[dict, ErnieClient, OutputPipeline], dict]


class WorkflowRouter:
    """根据 step_code 路由到对应 workflow 函数

    用法:
        router = WorkflowRouter(client, pipeline)
        router.register("worldview", worldview_workflow)
        result = router.run("worldview", {"idea": "...", "genre": "都市"})
    """

    def __init__(self, client: ErnieClient, pipeline: OutputPipeline | None = None):
        self._client = client
        self._pipeline = pipeline or OutputPipeline()
        self._routes: dict[str, WorkflowFn] = {}

    def register(self, step_code: str, fn: WorkflowFn) -> None:
        self._routes[step_code] = fn

    def list_steps(self) -> list[str]:
        return list(self._routes.keys())

    def run(self, step_code: str, input_data: dict) -> dict:
        """执行指定步骤的 workflow

        Args:
            step_code: 步骤代码（如 worldview, selling_point, hook）
            input_data: 输入数据，须符合对应 input schema

        Returns:
            校验通过的输出 dict
        """
        if step_code not in self._routes:
            raise ValueError(
                f"Unknown step_code: {step_code}. Available: {self.list_steps()}"
            )

        logger.info(f"Running workflow: {step_code}")
        fn = self._routes[step_code]
        result = fn(input_data, self._client, self._pipeline)
        logger.info(f"Workflow {step_code} completed")
        return result
