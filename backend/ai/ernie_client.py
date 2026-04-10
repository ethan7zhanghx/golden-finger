"""ERNIE-5.0 Client 封装

提供统一的 chat() 接口，支持 stream/non-stream 模式。
- HTTP 调用百度 ERNIE API
- OAuth2 token 自动管理与刷新
- 流式输出支持
- 失败自动重试（最多 3 次）
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Generator, Optional


@dataclass
class ErnieConfig:
    """ERNIE API 配置"""

    api_key: str = ""
    secret_key: str = ""
    base_url: str = "https://aip.baidubce.com"
    model: str = "ernie-5.0"
    token_url: str = "/oauth/2.0/token"
    chat_url: str = "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}"
    temperature: float = 0.7
    top_p: float = 0.9
    max_output_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ChatResponse:
    content: str
    usage: dict = field(default_factory=dict)
    is_truncated: bool = False
    raw: dict = field(default_factory=dict)


class ErnieTokenManager:
    """OAuth2 access_token 管理，自动缓存和刷新"""

    def __init__(self, config: ErnieConfig):
        self._config = config
        self._access_token: Optional[str] = None
        self._expires_at: float = 0

    def get_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 60:
            return self._access_token
        self._refresh_token()
        return self._access_token

    def _refresh_token(self) -> None:
        params = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self._config.api_key,
                "client_secret": self._config.secret_key,
            }
        )
        url = f"{self._config.base_url}{self._config.token_url}?{params}"
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if "access_token" not in data:
            raise RuntimeError(f"Failed to get access_token: {data}")

        self._access_token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 2592000)

    def set_token(self, token: str, expires_in: int = 2592000) -> None:
        """手动设置 token（测试用）"""
        self._access_token = token
        self._expires_at = time.time() + expires_in


class ErnieClient:
    """ERNIE-5.0 统一客户端

    用法:
        config = ErnieConfig(api_key="...", secret_key="...")
        client = ErnieClient(config)

        # 非流式调用
        resp = client.chat([ChatMessage(role="user", content="你好")])

        # 流式调用
        for chunk in client.chat_stream([ChatMessage(role="user", content="你好")]):
            print(chunk, end="")
    """

    def __init__(self, config: Optional[ErnieConfig] = None):
        self.config = config or ErnieConfig()
        self._token_manager = ErnieTokenManager(self.config)

    def _build_url(self, stream: bool = False) -> str:
        path = self.config.chat_url.format(model=self.config.model)
        token = self._token_manager.get_token()
        url = f"{self.config.base_url}{path}?access_token={token}"
        return url

    def _build_payload(
        self,
        messages: list[ChatMessage],
        system: str = "",
        stream: bool = False,
        **kwargs: Any,
    ) -> dict:
        payload: dict[str, Any] = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "max_output_tokens": kwargs.get(
                "max_output_tokens", self.config.max_output_tokens
            ),
            "stream": stream,
        }
        if system:
            payload["system"] = system
        return payload

    def _request_with_retry(
        self,
        url: str,
        payload: dict,
        stream: bool = False,
    ) -> Any:
        body = json.dumps(payload).encode("utf-8")
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                resp = urllib.request.urlopen(req, timeout=self.config.timeout)
                if stream:
                    return resp  # caller handles streaming
                raw = json.loads(resp.read().decode("utf-8"))
                if "error_code" in raw:
                    raise RuntimeError(
                        f"ERNIE API error {raw['error_code']}: {raw.get('error_msg')}"
                    )
                return raw
            except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))

        raise RuntimeError(
            f"ERNIE API failed after {self.config.max_retries} retries: {last_error}"
        )

    def chat(
        self,
        messages: list[ChatMessage],
        system: str = "",
        **kwargs: Any,
    ) -> ChatResponse:
        """非流式调用"""
        url = self._build_url(stream=False)
        payload = self._build_payload(messages, system=system, stream=False, **kwargs)
        raw = self._request_with_retry(url, payload, stream=False)
        return ChatResponse(
            content=raw.get("result", ""),
            usage=raw.get("usage", {}),
            is_truncated=raw.get("is_truncated", False),
            raw=raw,
        )

    def chat_stream(
        self,
        messages: list[ChatMessage],
        system: str = "",
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """流式调用，逐 chunk 返回文本"""
        url = self._build_url(stream=True)
        payload = self._build_payload(messages, system=system, stream=True, **kwargs)
        resp = self._request_with_retry(url, payload, stream=True)

        buffer = ""
        for line_bytes in resp:
            line = line_bytes.decode("utf-8").strip()
            if not line:
                continue
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    text = chunk.get("result", "")
                    if text:
                        buffer += text
                        yield text
                except json.JSONDecodeError:
                    continue

        resp.close()
