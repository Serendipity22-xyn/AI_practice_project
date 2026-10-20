"""
用户登录注册路由
"""
import hashlib
import random

from fastapi import APIRouter

import config
import storage
from schemas import LoginRequest, RegisterRequest, SavePersonaRequest

router = APIRouter()


def _hash_password(password: str) -> str:
    """密码哈希（sha256），避免明文存储"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _gen_user_id() -> str:
    """生成 8 位纯数字且不重复的用户 ID"""
    while True:
        uid = str(random.randint(10000000, 99999999))
        if not storage.user_id_exists(uid):
            return uid


def _ok(data=None, message="ok"):
    return {"code": config.CODE_OK, "message": message, "data": data}


def _err(code: int, message: str):
    return {"code": code, "message": message, "data": None}


@router.post("/register")
async def register(req: RegisterRequest):
    username = req.username.strip()
    password = req.password.strip()
    companion_name = req.companion_name.strip()

    # 参数校验
    if not username or not password or not companion_name:
        return _err(config.CODE_PARAM_ERROR, "用户名、密码、伴侣名字均不能为空")

    user_id = _gen_user_id()
    user = {
        "user_id": user_id,
        "username": username,
        "password": _hash_password(password),
        "companion_name": companion_name,
        "persona": None,        # 尚未选择性格
        "model_config": None,   # 尚未配置模型
        "chat_history": [],     # 聊天历史
    }
    storage.create_user(user)
    return _ok({"user_id": user_id, "companion_name": companion_name}, "注册成功")


@router.post("/login")
async def login(req: LoginRequest):
    user_id = req.user_id.strip()
    password = req.password.strip()

    if not user_id or not password:
        return _err(config.CODE_PARAM_ERROR, "用户 ID 和密码不能为空")

    user = storage.get_user(user_id)
    if not user:
        return _err(config.CODE_USER_NOT_FOUND, "用户不存在，请先注册")

    if user.get("password") != _hash_password(password):
        return _err(config.CODE_PASSWORD_ERROR, "密码错误")

    # 返回用户历史配置，前端据此恢复人设/模型配置，无需重复选择
    data = {
        "user_id": user_id,
        "username": user.get("username"),
        "companion_name": user.get("companion_name"),
        "persona": user.get("persona"),
        "model_config": user.get("model_config"),
        "chat_history": storage.get_chat_history(user_id),
    }
    return _ok(data, "登录成功")


@router.post("/persona")
async def save_persona(req: SavePersonaRequest):
    """保存用户选定的性格设定"""
    user = storage.get_user(req.user_id)
    if not user:
        return _err(config.CODE_USER_NOT_FOUND, "用户不存在，请先登录")

    if not req.persona or not req.persona.get("label"):
        return _err(config.CODE_PARAM_ERROR, "性格设定不能为空")

    storage.update_user(req.user_id, {"persona": req.persona})
    return _ok(req.persona, "性格已保存")
