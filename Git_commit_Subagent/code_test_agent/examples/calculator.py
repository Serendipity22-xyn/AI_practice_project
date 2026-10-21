# -*- coding: utf-8 -*-
"""示例待测模块：演示 code-test 子 Agent 的静态分析与单测生成。

覆盖三类场景：
- 简单算术函数：可生成正常 / 边界 / 异常三类用例
- 外部三方 API 调用：requests.get 将被 unittest.mock 隔离，严禁真实请求
"""

import requests


def add(a, b):
    """两数相加。"""
    return a + b


def subtract(a, b):
    """两数相减。"""
    return a - b


def divide(a, b):
    """两数相除；除数为 0 时抛出 ZeroDivisionError。"""
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b


def fetch_price(symbol):
    """从外部行情 API 拉取价格（外部依赖，测试时须 mock 隔离）。"""
    resp = requests.get(f"https://api.example.com/price/{symbol}", timeout=5)
    return resp.json()["price"]
