# -*- coding: utf-8 -*-
"""合规示例：命名规范、有 docstring、无安全风险，应通过质检。"""


def calculate_average(numbers):
    """计算列表平均值。"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


def format_name(first_name, last_name):
    """拼接完整姓名。"""
    return f"{first_name} {last_name}"


class UserProfile:
    """用户信息模型。"""

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def describe(self):
        """返回用户描述。"""
        return f"{self.name}, {self.age} 岁"
