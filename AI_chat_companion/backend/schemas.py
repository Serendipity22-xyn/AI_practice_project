"""
Pydantic 请求模型：定义前端传入的请求体结构，自动做参数类型校验。
"""
from typing import Optional

from pydantic import BaseModel, Field


class ManualConfig(BaseModel):
    """分支B：手动添加的三个参数（调用地址 / 模型名字 / APIKey）"""
    url: str = Field(..., description="调用地址")
    model: str = Field(..., description="模型名字")
    api_key: str = Field(..., description="API Key")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    companion_name: str = Field(..., description="伴侣名字")


class LoginRequest(BaseModel):
    """登录请求"""
    user_id: str = Field(..., description="用户 ID")
    password: str = Field(..., description="密码")


class SaveModelConfigRequest(BaseModel):
    """保存模型配置请求"""
    user_id: str = Field(..., description="用户 ID")
    model_type: str = Field(..., description="模型类型：default 或 manual")
    manual_config: Optional[ManualConfig] = Field(None, description="手动添加时的三项参数")


class SavePersonaRequest(BaseModel):
    """保存性格设定请求"""
    user_id: str = Field(..., description="用户 ID")
    persona: dict = Field(..., description="性格设定 {key, label, style}")


class ChatRequest(BaseModel):
    """对话请求"""
    user_id: str = Field(..., description="用户 ID")
    message: str = Field(..., description="本次用户消息")
    # 可选：若前端对话时携带模型选择类型，则覆盖已保存的配置
    model_type: Optional[str] = Field(None, description="模型类型：default 或 manual")
    manual_config: Optional[ManualConfig] = Field(None, description="手动添加的三项参数")
    # 模型名不规范时的二次确认：None=首次；True=用户选「是」；False=用户选「否」
    resolve_invalid_model: Optional[bool] = Field(None, description="厂商关键词确认结果")
