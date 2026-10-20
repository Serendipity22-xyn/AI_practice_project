"""
FastAPI 入口：注册路由、开启跨域
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import storage
from routers import auth, chat, model_config

app = FastAPI(title="AI 智能伴侣后端服务", version="1.0.0")

# 初始化数据库表结构
storage.init_db()

# 允许跨域（前端联调用，可后续收紧为具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["用户登录注册"])
app.include_router(model_config.router, prefix="/api/model", tags=["模型配置"])
app.include_router(chat.router, prefix="/api", tags=["对话"])


@app.get("/")
async def root():
    return {"code": 0, "message": "AI 智能伴侣后端服务运行中", "data": None}
