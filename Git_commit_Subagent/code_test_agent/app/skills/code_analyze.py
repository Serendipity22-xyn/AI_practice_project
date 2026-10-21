# -*- coding: utf-8 -*-
"""skill-code-analyze：代码静态分析器。

基于 Python 标准库 ast 静态解析源码，产出四类信息：
- func_list       函数列表（含参数、默认值、抛出的异常、外部调用）
- branch_points   逻辑分支点（if / for / while / try / bool）
- external_deps   外部依赖（数据库、三方 API 等，需 mock 隔离）
- exception_raise 异常抛出点

对外部依赖的识别基于「模块名 + 调用点」双维度：
既识别 import 引入的外部模块，也识别形如 requests.get 的调用。
"""

import ast

# 需要 mock 隔离的外部依赖模块（数据库 / 三方 API / 网络 / 消息队列等）
EXTERNAL_MODULES = {
    # 网络 / HTTP
    "requests", "httpx", "urllib3", "aiohttp", "urllib", "socket", "http",
    # 数据库
    "sqlalchemy", "pymysql", "mysql", "psycopg2", "sqlite3", "cx_Oracle",
    "pymongo", "motor", "redis", "pymemcache",
    # 云 / 第三方
    "boto3", "google", "azure", "stripe",
    # 消息 / 通信
    "kafka", "pika", "stomp", "smtplib", "paramiko", "ftplib",
}

_OPERATOR_NAMES = {
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
    ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**",
}


def analyze(source_code, lang="python"):
    """静态解析源代码。

    返回规格约定的 JSON 结构；解析失败时返回带 error 字段的结果。
    """
    result = {
        "func_list": [],
        "branch_points": [],
        "external_deps": [],
        "exception_raise": [],
        "error": None,
    }

    if lang != "python":
        result["error"] = f"暂不支持语言：{lang}（当前仅支持 python）"
        return result

    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        result["error"] = f"源码语法错误：{exc.msg}（第 {exc.lineno} 行）"
        return result

    # 1. 收集 import 引入的模块名
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])

    # 2. 建立 parent 映射，用于定位 raise 所属的 if 触发条件
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    # 3. 遍历 AST 收集信息
    for node in ast.walk(tree):
        # 分支点（全局统计，含函数体内）
        if isinstance(node, ast.If):
            result["branch_points"].append({"kind": "if", "line": node.lineno})
        elif isinstance(node, ast.For):
            result["branch_points"].append({"kind": "for", "line": node.lineno})
        elif isinstance(node, ast.While):
            result["branch_points"].append({"kind": "while", "line": node.lineno})
        elif isinstance(node, ast.Try):
            result["branch_points"].append({"kind": "try", "line": node.lineno})
            for handler in node.handlers:
                result["exception_raise"].append({
                    "kind": "except",
                    "exception_type": _except_name(handler),
                    "line": handler.lineno,
                    "func": _enclosing_func(node, parents),
                })
        elif isinstance(node, ast.BoolOp):
            result["branch_points"].append({"kind": "bool", "line": node.lineno})

        # 函数（含嵌套）
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_info = _collect_func(node, imported, parents)
            result["func_list"].append(func_info)
            for raise_item in func_info["raises"]:
                result["exception_raise"].append({
                    "kind": "raise",
                    "exception_type": raise_item["exc"],
                    "line": raise_item["line"],
                    "func": node.name,
                })

    # 4. 模块级外部依赖 import
    for mod in sorted(imported):
        if mod in EXTERNAL_MODULES:
            result["external_deps"].append({
                "name": mod, "kind": "import", "line": -1, "func": None,
            })

    return result


def _collect_func(node, imported, parents):
    """收集单个函数的信息：参数、默认值、抛出的异常、外部调用、返回值模式。"""
    args = [arg.arg for arg in node.args.args]

    # 参数默认值（与 args 尾部对齐）
    defaults = [None] * len(args)
    if node.args.defaults:
        offset = len(args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            defaults[offset + i] = _const_to_py(default)

    raises = []
    external_calls = []
    return_pattern = None

    for sub in ast.walk(node):
        if isinstance(sub, ast.Raise):
            raises.append({
                "exc": _raise_name(sub),
                "line": sub.lineno,
                "trigger": _find_trigger(sub, parents),
            })
        elif isinstance(sub, ast.Call):
            call_name = _call_external_name(sub)
            if call_name and call_name.split(".")[0] in imported:
                external_calls.append(call_name)
        elif isinstance(sub, ast.Return) and return_pattern is None:
            return_pattern = _infer_return(sub.value, args)

    return {
        "name": node.name,
        "line": node.lineno,
        "args": args,
        "defaults": defaults,
        "raises": raises,
        "external_calls": sorted(set(external_calls)),
        "return_pattern": return_pattern,
    }


def _enclosing_func(node, parents):
    """返回节点所属的最近函数名，无则返回 None。"""
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur.name
        cur = parents.get(cur)
    return None


def _find_trigger(raise_node, parents):
    """定位 raise 的触发条件，例如 if b == 0 中的 (变量名, 常量值)。"""
    cur = parents.get(raise_node)
    while cur is not None:
        if isinstance(cur, ast.If):
            return _parse_compare(cur.test)
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            break
        cur = parents.get(cur)
    return None


def _parse_compare(test):
    """解析形如 `b == 0` 的比较，返回 (变量名, 常量值)。"""
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and len(test.comparators) == 1:
        op = test.ops[0]
        if isinstance(op, ast.Eq):
            left, right = test.left, test.comparators[0]
            if isinstance(left, ast.Name) and isinstance(right, ast.Constant):
                return (left.id, right.value)
            if isinstance(right, ast.Name) and isinstance(left, ast.Constant):
                return (right.id, left.value)
    return None


def _infer_return(value, args):
    """推断返回值模式：若为 `return a + b` 这类参数二元运算，返回描述。

    用于让生成器产出有意义的断言；无法推断时返回 None。
    """
    if isinstance(value, ast.BinOp) and isinstance(value.op, tuple(_OPERATOR_NAMES)):
        left = _name_of(value.left)
        right = _name_of(value.right)
        if left in args and right in args:
            return {"kind": "binop", "op": _OPERATOR_NAMES[type(value.op)],
                    "left": left, "right": right}
    return None


def _name_of(node):
    """提取节点对应的参数名，非简单 Name 时返回 None。"""
    if isinstance(node, ast.Name):
        return node.id
    return None


def _call_external_name(node):
    """提取外部调用名，如 requests.get；非外部调用返回 None。"""
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        if func.value.id in EXTERNAL_MODULES:
            return f"{func.value.id}.{func.attr}"
    return None


def _raise_name(node):
    """提取 raise 的异常类型名，默认 Exception。"""
    if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
        return node.exc.func.id
    if isinstance(node.exc, ast.Name):
        return node.exc.id
    return "Exception"


def _except_name(handler):
    """提取 except 捕获的异常类型名，默认 Exception。"""
    if handler.type is None:
        return "Exception"
    if isinstance(handler.type, ast.Name):
        return handler.type.id
    if isinstance(handler.type, ast.Tuple):
        names = [elt.id for elt in handler.type.elts if isinstance(elt, ast.Name)]
        return ",".join(names) or "Exception"
    return "Exception"


def _const_to_py(node):
    """把 ast 常量节点转成 Python 值。"""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _const_to_py(node.operand)
        return -inner if isinstance(inner, (int, float)) else None
    return None
