"""
大模型调用服务：
1. 厂商关键词识别（模型名不规范检测）
2. 人设系统 prompt 构建
3. 流式调用大模型（含异常捕获）
"""
import asyncio
import json
from typing import Optional

import httpx

import config


class LLMError(Exception):
    """大模型调用相关异常，携带错误码，便于返回友好提示给前端"""
    def __init__(self, message: str, code: int = config.CODE_LLM_ERROR):
        super().__init__(message)
        self.message = message
        self.code = code


def detect_invalid_model(model_name: str) -> Optional[dict]:
    """
    识别模型名是否是不规范的厂商名称（如「智谱」「通义」「豆包」）。
    返回厂商信息 dict（含 vendor/model/url），若为合法标准模型名则返回 None。
    注意：此函数只做「识别」，不做替换；替换由上层在用户确认「是」之后执行。
    """
    if not model_name:
        return None
    normalized = model_name.strip().lower()
    for keyword, info in config.VENDOR_KEYWORDS.items():
        if normalized == keyword:
            return info
    return None


def build_system_prompt(persona: Optional[dict], companion_name: str) -> str:
    """根据伴侣人设和名字构建系统 prompt，保证对话风格固定"""
    name = companion_name or "伴侣"
    if persona and persona.get("label"):
        style = persona.get("style", "")
        return (
            f"你是用户的AI伴侣「{name}」，性格人设：{persona['label']}（{style}）。"
            f"请始终以这个人设和风格自然、温柔地回复用户，语气贴合角色，不要跳出人设。"
        )
    return f"你是用户的AI伴侣「{name}」，请友好、自然地回复用户。"


async def stream_chat(messages: list, model_config: dict, max_retries: int = 3):
    """
    流式调用大模型，逐段 yield 回复文本内容。
    遇到限流（429）时自动退避重试，最多 max_retries 次；其余错误直接抛出。
    """
    for attempt in range(max_retries):
        try:
            async for chunk in _stream_once(messages, model_config):
                yield chunk
            return  # 成功，直接返回
        except LLMError as e:
            # 限流则等待后重试，其余错误直接抛出
            if e.code == config.CODE_RATE_LIMIT and attempt < max_retries - 1:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            raise


async def _stream_once(messages: list, model_config: dict):
    """单次流式调用（OpenAI 兼容格式），不做重试"""
    url = model_config["url"]
    model = model_config["model"]
    api_key = model_config["api_key"]

    payload = {"model": model, "messages": messages, "stream": True}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                # ---- 状态码异常处理 ----
                if resp.status_code == 401:
                    raise LLMError("API Key 错误或已过期，请检查密钥", config.CODE_API_KEY_ERROR)
                if resp.status_code == 429:
                    raise LLMError("请求过于频繁或触发限流，请稍后再试", config.CODE_RATE_LIMIT)
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", errors="ignore")
                    raise LLMError(f"大模型返回错误({resp.status_code})：{body[:200]}", config.CODE_LLM_ERROR)

                # ---- 解析 SSE 流，逐段提取增量内容 ----
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        delta = obj.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                        # 忽略无法解析的数据帧
                        continue
    except httpx.ConnectError as e:
        raise LLMError("无法连接到模型接口地址，请检查调用地址是否正确", config.CODE_URL_UNREACHABLE) from e
    except httpx.TimeoutException as e:
        raise LLMError("请求大模型超时，请稍后再试", config.CODE_TIMEOUT) from e
