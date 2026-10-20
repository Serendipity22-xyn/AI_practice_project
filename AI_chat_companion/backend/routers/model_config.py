"""
模型配置路由：保存用户的模型配置方案（默认 / 手动）
"""
from fastapi import APIRouter

import config
import storage
from schemas import SaveModelConfigRequest

router = APIRouter()


@router.post("/config")
async def save_model_config(req: SaveModelConfigRequest):
    user = storage.get_user(req.user_id)
    if not user:
        return {"code": config.CODE_USER_NOT_FOUND, "message": "用户不存在", "data": None}

    if req.model_type not in ("default", "manual"):
        return {"code": config.CODE_PARAM_ERROR, "message": "模型类型不正确（应为 default 或 manual）", "data": None}

    if req.model_type == "default":
        # 分支A：默认设置 -> 智谱 GLM-4.6V-Flash + 内置默认 Key
        model_config = {
            "type": "default",
            "url": config.ZHIPU_DEFAULT_URL,
            "model": config.ZHIPU_DEFAULT_MODEL,
            "api_key": config.ZHIPU_DEFAULT_API_KEY,
        }
    else:
        # 分支B：手动添加 -> 使用用户填写的三项
        if not req.manual_config:
            return {"code": config.CODE_PARAM_ERROR, "message": "手动添加缺少配置参数", "data": None}
        model_config = {
            "type": "manual",
            "url": req.manual_config.url.strip(),
            "model": req.manual_config.model.strip(),
            "api_key": req.manual_config.api_key.strip(),
        }

    storage.update_user(req.user_id, {"model_config": model_config})
    return {"code": config.CODE_OK, "message": "模型配置已保存", "data": model_config}
