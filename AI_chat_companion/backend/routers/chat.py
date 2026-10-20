"""
对话请求路由：流式输出，含厂商关键词识别与前端二次确认逻辑
"""
import json
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import config
import llm
import storage
from schemas import ChatRequest

router = APIRouter()


def _sse(payload: dict) -> str:
    """构造 SSE 数据帧"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _build_model_config(user: dict, req: ChatRequest):
    """
    确定本次对话使用的模型配置。
    优先使用请求携带的 model_type/manual_config（覆盖），否则用已保存的配置。
    """
    if req.model_type == "default":
        return {
            "type": "default",
            "url": config.ZHIPU_DEFAULT_URL,
            "model": config.ZHIPU_DEFAULT_MODEL,
            "api_key": config.ZHIPU_DEFAULT_API_KEY,
        }
    if req.model_type == "manual" and req.manual_config:
        return {
            "type": "manual",
            "url": req.manual_config.url.strip(),
            "model": req.manual_config.model.strip(),
            "api_key": req.manual_config.api_key.strip(),
        }
    return user.get("model_config")


@router.post("/chat")
async def chat(req: ChatRequest):
    user = storage.get_user(req.user_id)
    if not user:
        return {"code": config.CODE_USER_NOT_FOUND, "message": "用户不存在，请先登录", "data": None}

    model_config = _build_model_config(user, req)
    if not model_config:
        return {"code": config.CODE_PARAM_ERROR, "message": "尚未配置模型，请先完成模型配置", "data": None}

    # ---- 厂商关键词识别（仅手动添加时） ----
    if model_config.get("type") == "manual":
        invalid = llm.detect_invalid_model(model_config.get("model", ""))
        if invalid:
            if req.resolve_invalid_model is None:
                # 首次：识别到不规范模型名，返回标识通知前端弹窗确认（不静默替换）
                return {
                    "code": config.CODE_MODEL_NAME_INVALID,
                    "message": f"你填写的模型名称【{model_config['model']}】不规范，是否自动为你匹配该厂商下可用大模型？",
                    "data": {
                        "vendor": invalid["vendor"],
                        "invalid_model": model_config["model"],
                        "matched_model": invalid["model"],
                    },
                }
            if req.resolve_invalid_model is False:
                # 用户选「否」：报错，提示填写正确模型名
                return {"code": config.CODE_MODEL_RESOLVE_NO, "message": "请填写正确的标准模型名称（如 glm-4.6v-flash）", "data": None}
            # 用户选「是」：替换为该厂商可用模型
            model_config = dict(model_config)
            model_config["model"] = invalid["model"]

    # ---- 构建消息：system 人设 + 历史 + 本次消息 ----
    system_prompt = llm.build_system_prompt(user.get("persona"), user.get("companion_name"))
    history = storage.get_chat_history(req.user_id)[-config.MAX_HISTORY:]
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": req.message})

    # 先保存用户消息
    storage.append_chat_history(
        req.user_id,
        [{"role": "user", "content": req.message, "time": int(time.time())}],
    )

    async def generate():
        """流式生成器：逐段转发 AI 回复，结束后保存历史"""
        full_reply = ""
        try:
            async for chunk in llm.stream_chat(messages, model_config):
                full_reply += chunk
                yield _sse({"content": chunk})
            if full_reply:
                storage.append_chat_history(
                    req.user_id,
                    [{"role": "assistant", "content": full_reply, "time": int(time.time())}],
                )
            yield _sse({"done": True})
        except llm.LLMError as e:
            # 捕获大模型相关异常，返回友好提示
            yield _sse({"error": e.message, "code": e.code})

    return StreamingResponse(generate(), media_type="text/event-stream")
