"""ERNIE / Qianfan Client 封装

使用百度千帆 v2 OpenAI 兼容接口。
支持 ernie-5.0（推理模型）和 deepseek-v3 等模型。
"""

import json
import urllib.error
import urllib.request
import time
from dataclasses import dataclass, field
from typing import Any, Generator, Optional


@dataclass
class ErnieConfig:
    """千帆 API 配置"""

    api_key: str = ""  # Bearer token (bce-v3/...)
    base_url: str = "https://qianfan.baidubce.com/v2"
    model: str = "ernie-5.0"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    # Legacy fields kept for backward compatibility
    secret_key: str = ""
    top_p: float = 0.9
    max_output_tokens: int = 4096
    token_url: str = ""
    chat_url: str = ""


@dataclass
class ChatMessage:
    role: str  # "user", "assistant", or "system"
    content: str


@dataclass
class ChatResponse:
    content: str
    reasoning_content: str = ""
    usage: dict = field(default_factory=dict)
    is_truncated: bool = False
    raw: dict = field(default_factory=dict)


class ErnieClient:
    """千帆 v2 API 客户端

    用法:
        config = ErnieConfig(api_key="bce-v3/...")
        client = ErnieClient(config)

        # 非流式调用
        resp = client.chat([ChatMessage(role="user", content="你好")])

        # 流式调用
        for chunk in client.chat_stream([ChatMessage(role="user", content="你好")]):
            print(chunk, end="")
    """

    def __init__(self, config: Optional[ErnieConfig] = None):
        self.config = config or ErnieConfig()

    def _build_payload(
        self,
        messages: list[ChatMessage],
        system: str = "",
        stream: bool = False,
        **kwargs: Any,
    ) -> dict:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend([{"role": m.role, "content": m.content} for m in messages])

        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": msgs,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": stream,
        }

        # ernie-5.0 is a reasoning model — don't set temperature
        model = payload["model"]
        if "ernie-5.0" not in model:
            payload["temperature"] = kwargs.get("temperature", self.config.temperature)

        return payload

    def _request_with_retry(
        self,
        payload: dict,
        stream: bool = False,
    ) -> Any:
        url = f"{self.config.base_url}/chat/completions"
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                resp = urllib.request.urlopen(req, timeout=self.config.timeout)
                if stream:
                    return resp
                raw = json.loads(resp.read().decode("utf-8"))
                if "error" in raw:
                    raise RuntimeError(f"API error: {raw['error']}")
                return raw
            except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))

        raise RuntimeError(
            f"API failed after {self.config.max_retries} retries: {last_error}"
        )

    def chat(
        self,
        messages: list[ChatMessage],
        system: str = "",
        **kwargs: Any,
    ) -> ChatResponse:
        """非流式调用"""
        payload = self._build_payload(messages, system=system, stream=False, **kwargs)
        raw = self._request_with_retry(payload, stream=False)
        choice = raw.get("choices", [{}])[0]
        msg = choice.get("message", {})
        return ChatResponse(
            content=msg.get("content", ""),
            reasoning_content=msg.get("reasoning_content", ""),
            usage=raw.get("usage", {}),
            is_truncated=choice.get("finish_reason") == "length",
            raw=raw,
        )

    def chat_stream(
        self,
        messages: list[ChatMessage],
        system: str = "",
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """流式调用，逐 chunk 返回文本"""
        payload = self._build_payload(messages, system=system, stream=True, **kwargs)
        resp = self._request_with_retry(payload, stream=True)

        for line_bytes in resp:
            line = line_bytes.decode("utf-8").strip()
            if not line:
                continue
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    text = delta.get("content", "")
                    if text:
                        yield text
                except json.JSONDecodeError:
                    continue

        resp.close()
