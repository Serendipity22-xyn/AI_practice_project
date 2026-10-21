# -*- coding: utf-8 -*-
"""不合规示例：包含命名混乱、缺 docstring、安全风险，应质检失败。"""

import os
import os  # 重复 import


def GetUserName(Id):  # 函数名非 snake_case，参数命名混乱，缺 docstring
    return "user_" + str(Id)


def runDangerous(cmd):  # 命名混乱，缺 docstring
    try:
        result = eval(cmd)  # eval 代码注入风险
    except:  # 裸 except
        result = None
    return result


PASSWORD = "hardcoded_secret_123"  # 硬编码敏感信息

admin_token = "tok_abcdef"  # 硬编码 token
