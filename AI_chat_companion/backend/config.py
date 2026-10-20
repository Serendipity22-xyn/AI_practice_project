"""
配置块
集中管理大模型相关的所有配置，方便统一修改，避免散落在代码各处。
"""

# ============ 智谱默认配置（分支A：用户选择【默认设置】） ============
# 智谱 GLM-4.6V-Flash 官方标准接口地址
ZHIPU_DEFAULT_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
# 默认模型名（GLM-4.6V-Flash 的标准模型标识）
ZHIPU_DEFAULT_MODEL = "glm-4.6v-flash"
# 内置默认 API Key（请勿泄露；如需更换，改这里即可）
ZHIPU_DEFAULT_API_KEY = "9a803f3dbf4642c1a26745a2bbefa7ab.3lbOQUpTF4hCDy5P"

# ============ 其他厂商 OpenAI 兼容接口地址 ============
QWEN_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DOUBAO_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

# ============ 厂商关键词 → 该厂商可用模型 ============
# 当用户【手动添加】填写了厂商名称（而非标准模型名），后端识别后
# 通知前端弹窗确认，用户选「是」才用这里对应的可用模型自动替换（不静默替换）。
VENDOR_KEYWORDS = {
    "智谱": {"vendor": "智谱", "model": ZHIPU_DEFAULT_MODEL, "url": ZHIPU_DEFAULT_URL},
    "zhipu": {"vendor": "智谱", "model": ZHIPU_DEFAULT_MODEL, "url": ZHIPU_DEFAULT_URL},
    "glm": {"vendor": "智谱", "model": ZHIPU_DEFAULT_MODEL, "url": ZHIPU_DEFAULT_URL},
    "通义": {"vendor": "通义千问", "model": "qwen-turbo", "url": QWEN_URL},
    "千问": {"vendor": "通义千问", "model": "qwen-turbo", "url": QWEN_URL},
    "qwen": {"vendor": "通义千问", "model": "qwen-turbo", "url": QWEN_URL},
    "豆包": {"vendor": "豆包", "model": "doubao-pro-32k", "url": DOUBAO_URL},
    "doubao": {"vendor": "豆包", "model": "doubao-pro-32k", "url": DOUBAO_URL},
}

# ============ 其他配置 ============
# 大模型请求超时（秒）
LLM_TIMEOUT = 60.0
# 每次请求携带的历史消息条数上限
MAX_HISTORY = 20

# ============ 错误码 ============
CODE_OK = 0
CODE_USER_NOT_FOUND = 1001      # 用户不存在
CODE_USER_EXISTS = 1002         # 用户已存在
CODE_PASSWORD_ERROR = 1003      # 密码错误
CODE_PARAM_ERROR = 1004         # 参数错误
CODE_MODEL_NAME_INVALID = 4001  # 模型名不规范（通知前端弹窗确认）
CODE_API_KEY_ERROR = 4002       # API Key 错误
CODE_URL_UNREACHABLE = 4003     # 接口地址不通
CODE_RATE_LIMIT = 4004          # 高峰期限流
CODE_LLM_ERROR = 4005           # 大模型返回错误
CODE_MODEL_RESOLVE_NO = 4006    # 用户选「否」：需填写正确模型名
CODE_TIMEOUT = 4007             # 请求超时
