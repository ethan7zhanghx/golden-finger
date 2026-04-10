"""金手指 AI 工作流单元测试

使用 mock LLM 调用，验证 workflow 端到端可运行且输出通过 schema 校验。
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 确保项目 src 在 path 上
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ai.ernie_client import ChatResponse, ErnieClient, ErnieConfig
from ai.output_pipeline import (
    OutputPipeline,
    extract_json_from_text,
    parse_json_output,
    validate_output,
)
from ai.workflow_router import WorkflowRouter
from ai.workflows.hook import hook_workflow
from ai.workflows.selling_point import selling_point_workflow
from ai.workflows.worldview import worldview_workflow

# ───────────────────── Mock 数据 ─────────────────────

MOCK_WORLDVIEW_OUTPUT = {
    "title": "霓虹帝国",
    "era_setting": "2045 年近未来都市，科技与阶层分化共存的赛博朋克城市",
    "social_rules": [
        {"rule": "信用积分制", "detail": "每个人的社会地位由信用积分决定，积分低于阈值将被驱逐到外城区"},
        {"rule": "记忆交易合法化", "detail": "可以出售自己的记忆换取积分，但买入他人记忆可能导致人格混乱"},
    ],
    "core_conflict": "女主角发现自己的全部记忆是人工植入的，真实身份是被抹去记忆的反抗军领袖",
    "visual_style": ["赛博朋克", "霓虹灯光", "高楼与贫民窟对比", "全息投影"],
    "taboos": ["禁止私下交易记忆", "禁止查询已删除的记忆档案"],
    "unique_elements": ["记忆交易系统", "信用积分决定生死", "人格分裂风险"],
}

MOCK_SELLING_POINT_OUTPUT = {
    "logline": "一个失忆女孩发现自己是被抹除记忆的反抗军领袖，在记忆迷宫中找回真相与爱情",
    "selling_points": [
        {
            "point": "记忆反转",
            "description": "女主的每一段记忆都可能是假的，真相层层揭开",
            "audience_appeal": "满足观众对悬疑反转的强烈好奇心",
            "priority": 1,
        },
        {
            "point": "身份逆袭",
            "description": "从底层无名者到反抗军领袖的身份反转",
            "audience_appeal": "逆袭类题材天然具备爽感和代入感",
            "priority": 2,
        },
        {
            "point": "禁忌爱情",
            "description": "与记忆中的男主重逢，却发现对方是敌方阵营",
            "audience_appeal": "虐恋情深、阵营对立提供强情感冲突",
            "priority": 3,
        },
    ],
    "positioning": "高概念悬疑 + 情感向赛博朋克微短剧",
    "differentiation": ["记忆交易这一独特设定", "每集一个记忆反转的叙事结构", "科幻外壳下的纯爱内核"],
}

MOCK_HOOK_OUTPUT = {
    "highlights": [
        {
            "name": "记忆觉醒",
            "scene_description": "女主在一次意外中闪回战场画面，发现自己竟然能徒手格斗",
            "emotion_type": "逆袭",
            "position": "opening",
            "intensity": 5,
        },
        {
            "name": "积分打脸",
            "scene_description": "被嘲笑积分为零的女主当众展示隐藏的高级权限码",
            "emotion_type": "打脸",
            "position": "middle",
            "intensity": 4,
        },
        {
            "name": "真相揭露",
            "scene_description": "女主进入记忆黑市，看到自己被抹除的领袖就职演说记忆",
            "emotion_type": "揭秘",
            "position": "climax",
            "intensity": 5,
        },
        {
            "name": "甜蜜重逢",
            "scene_description": "男主冒着被清除积分的风险在雨中找到女主，两人记忆碎片完美拼合",
            "emotion_type": "甜宠",
            "position": "middle",
            "intensity": 4,
        },
        {
            "name": "反抗军集结",
            "scene_description": "女主在废弃信号塔重新接通反抗军通讯，所有沉睡的同伴同时觉醒",
            "emotion_type": "逆袭",
            "position": "ending",
            "intensity": 5,
        },
    ],
    "hooks": [
        {
            "name": "谁植入了我的记忆",
            "hook_description": "女主发现植入记忆的操作者正是自己最信任的人",
            "hook_type": "悬念",
            "position": "episode_end",
            "cliffhanger_strength": 5,
        },
        {
            "name": "男主的真实身份",
            "hook_description": "监控画面显示男主曾亲手执行了对女主的记忆清除",
            "hook_type": "反转",
            "position": "episode_end",
            "cliffhanger_strength": 5,
        },
        {
            "name": "第二个自己",
            "hook_description": "女主在记忆黑市看到另一个自己——一个仍在活动的克隆体",
            "hook_type": "信息差",
            "position": "mid_episode",
            "cliffhanger_strength": 4,
        },
        {
            "name": "积分归零倒计时",
            "hook_description": "系统宣布女主积分将在 24 小时后清零，届时将被永久驱逐",
            "hook_type": "命运转折",
            "position": "episode_end",
            "cliffhanger_strength": 4,
        },
        {
            "name": "领袖遗言",
            "hook_description": "在一段被标记为危险的记忆碎片中，女主听到自己的声音说'计划已经启动，无法终止'",
            "hook_type": "悬念",
            "position": "arc_end",
            "cliffhanger_strength": 5,
        },
    ],
    "emotion_curve_suggestion": "前3集以悬疑揭秘为主快速升温，中段穿插甜虐情感线调节节奏，尾段以连续反转和逆袭推向情绪高潮",
}


def make_mock_client(mock_output: dict) -> ErnieClient:
    """创建返回固定 JSON 的 mock ErnieClient"""
    client = ErnieClient(ErnieConfig())
    mock_response = ChatResponse(content=json.dumps(mock_output, ensure_ascii=False))
    client.chat = MagicMock(return_value=mock_response)
    return client


# ───────────────────── 测试类 ─────────────────────


class TestExtractJson(unittest.TestCase):
    def test_pure_json(self):
        text = '{"key": "value"}'
        self.assertEqual(extract_json_from_text(text), text)

    def test_code_block(self):
        text = '```json\n{"key": "value"}\n```'
        self.assertEqual(extract_json_from_text(text), '{"key": "value"}')

    def test_mixed_text(self):
        text = '这是一些说明文字\n{"key": "value"}\n以上是结果'
        result = extract_json_from_text(text)
        self.assertEqual(json.loads(result), {"key": "value"})

    def test_no_json(self):
        self.assertIsNone(extract_json_from_text("no json here"))


class TestOutputPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = OutputPipeline()

    def test_valid_worldview_output(self):
        raw = json.dumps(MOCK_WORLDVIEW_OUTPUT, ensure_ascii=False)
        result = self.pipeline.process(raw, "worldview_output")
        self.assertEqual(result["title"], "霓虹帝国")

    def test_invalid_output_raises(self):
        raw = json.dumps({"title": "test"})  # missing required fields
        with self.assertRaises(ValueError):
            self.pipeline.process(raw, "worldview_output")

    def test_fallback_called_on_parse_failure(self):
        fallback = MagicMock(return_value=MOCK_WORLDVIEW_OUTPUT)
        pipeline = OutputPipeline(fallback_fn=fallback)
        result = pipeline.process("not json at all!!!", "worldview_output")
        fallback.assert_called_once()
        self.assertEqual(result["title"], "霓虹帝国")


class TestSchemaValidation(unittest.TestCase):
    def test_worldview_output_valid(self):
        errors = validate_output(MOCK_WORLDVIEW_OUTPUT, "worldview_output")
        self.assertEqual(errors, [])

    def test_selling_point_output_valid(self):
        errors = validate_output(MOCK_SELLING_POINT_OUTPUT, "selling_point_output")
        self.assertEqual(errors, [])

    def test_hook_output_valid(self):
        errors = validate_output(MOCK_HOOK_OUTPUT, "hook_output")
        self.assertEqual(errors, [])

    def test_worldview_output_missing_field(self):
        bad = {"title": "test"}
        errors = validate_output(bad, "worldview_output")
        self.assertGreater(len(errors), 0)


class TestWorldviewWorkflow(unittest.TestCase):
    def test_end_to_end(self):
        client = make_mock_client(MOCK_WORLDVIEW_OUTPUT)
        pipeline = OutputPipeline()
        input_data = {
            "idea": "一个关于记忆交易的赛博朋克世界，女主发现自己的记忆全是假的",
            "genre": "悬疑",
            "era": "近未来",
            "audience": "18-35岁女性",
        }
        result = worldview_workflow(input_data, client, pipeline)
        self.assertEqual(result["title"], "霓虹帝国")
        self.assertIn("social_rules", result)
        client.chat.assert_called_once()

    def test_invalid_input_raises(self):
        client = make_mock_client(MOCK_WORLDVIEW_OUTPUT)
        pipeline = OutputPipeline()
        with self.assertRaises(ValueError):
            worldview_workflow({"idea": "短"}, client, pipeline)  # too short + missing genre


class TestSellingPointWorkflow(unittest.TestCase):
    def test_end_to_end(self):
        client = make_mock_client(MOCK_SELLING_POINT_OUTPUT)
        pipeline = OutputPipeline()
        input_data = {
            "worldview_json": json.dumps(MOCK_WORLDVIEW_OUTPUT, ensure_ascii=False),
            "genre": "悬疑",
            "audience": "18-35岁女性",
        }
        result = selling_point_workflow(input_data, client, pipeline)
        self.assertIn("logline", result)
        self.assertEqual(len(result["selling_points"]), 3)
        client.chat.assert_called_once()


class TestHookWorkflow(unittest.TestCase):
    def test_end_to_end(self):
        client = make_mock_client(MOCK_HOOK_OUTPUT)
        pipeline = OutputPipeline()
        input_data = {
            "worldview_json": json.dumps(MOCK_WORLDVIEW_OUTPUT, ensure_ascii=False),
            "selling_points_json": json.dumps(
                MOCK_SELLING_POINT_OUTPUT, ensure_ascii=False
            ),
            "audience": "18-35岁女性",
            "style_preference": "悬疑+甜宠",
        }
        result = hook_workflow(input_data, client, pipeline)
        self.assertEqual(len(result["highlights"]), 5)
        self.assertEqual(len(result["hooks"]), 5)
        self.assertIn("emotion_curve_suggestion", result)
        client.chat.assert_called_once()


class TestWorkflowRouter(unittest.TestCase):
    def test_register_and_run(self):
        client = make_mock_client(MOCK_WORLDVIEW_OUTPUT)
        pipeline = OutputPipeline()
        router = WorkflowRouter(client, pipeline)
        router.register("worldview", worldview_workflow)

        input_data = {
            "idea": "一个关于记忆交易的赛博朋克世界，女主发现自己的记忆全是假的",
            "genre": "悬疑",
        }
        result = router.run("worldview", input_data)
        self.assertEqual(result["title"], "霓虹帝国")

    def test_unknown_step_raises(self):
        client = make_mock_client({})
        router = WorkflowRouter(client)
        with self.assertRaises(ValueError):
            router.run("nonexistent", {})

    def test_list_steps(self):
        client = make_mock_client({})
        router = WorkflowRouter(client)
        router.register("worldview", worldview_workflow)
        router.register("selling_point", selling_point_workflow)
        self.assertEqual(router.list_steps(), ["worldview", "selling_point"])

    def test_full_pipeline_3_steps(self):
        """模拟完整的 3 步端到端流程"""
        pipeline = OutputPipeline()

        # Step 1: worldview
        client1 = make_mock_client(MOCK_WORLDVIEW_OUTPUT)
        router1 = WorkflowRouter(client1, pipeline)
        router1.register("worldview", worldview_workflow)
        wv_result = router1.run(
            "worldview",
            {
                "idea": "一个关于记忆交易的赛博朋克世界，女主发现自己的记忆全是假的",
                "genre": "悬疑",
            },
        )

        # Step 2: selling_point (uses worldview output)
        client2 = make_mock_client(MOCK_SELLING_POINT_OUTPUT)
        router2 = WorkflowRouter(client2, pipeline)
        router2.register("selling_point", selling_point_workflow)
        sp_result = router2.run(
            "selling_point",
            {
                "worldview_json": json.dumps(wv_result, ensure_ascii=False),
                "genre": "悬疑",
            },
        )

        # Step 3: hook (uses worldview + selling_point output)
        client3 = make_mock_client(MOCK_HOOK_OUTPUT)
        router3 = WorkflowRouter(client3, pipeline)
        router3.register("hook", hook_workflow)
        hook_result = router3.run(
            "hook",
            {
                "worldview_json": json.dumps(wv_result, ensure_ascii=False),
                "selling_points_json": json.dumps(sp_result, ensure_ascii=False),
            },
        )

        # 验证 3 步都成功
        self.assertEqual(wv_result["title"], "霓虹帝国")
        self.assertIn("logline", sp_result)
        self.assertGreaterEqual(len(hook_result["highlights"]), 5)
        self.assertGreaterEqual(len(hook_result["hooks"]), 5)


if __name__ == "__main__":
    unittest.main()
