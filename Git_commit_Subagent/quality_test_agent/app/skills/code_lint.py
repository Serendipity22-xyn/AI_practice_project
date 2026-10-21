# -*- coding: utf-8 -*-
"""skill-code-lint：代码规范扫描。

基于 ast 轻量扫描，聚焦代码规范、可读性、基础安全，不做复杂深度逻辑测试。
产出问题清单（区分 error / warn）与质量分数。

评分规则：满分 100，每个 error 扣 15 分、每个 warn 扣 5 分，下限 0；
语法错误直接判 0 分。
"""

import ast

# 敏感信息关键字（按变量名小写匹配）
SECRET_KEYWORDS = ("password", "passwd", "secret", "token",
                   "api_key", "apikey", "access_key")

# 危险内置函数（代码注入风险）
DANGEROUS_BUILTINS = {"eval", "exec", "compile"}

# subprocess 相关调用（需检查 shell=True）
SUBPROCESS_CALLS = {"run", "Popen", "call", "check_output", "check_call"}


def lint(source_code, lang="python"):
    """扫描源代码，返回问题清单与质量分数。"""
    result = {"lint_issues": [], "score": 100, "error": None}

    if lang != "python":
        result["error"] = f"暂不支持语言：{lang}（当前仅支持 python）"
        result["score"] = 0
        return result

    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        result["lint_issues"].append({
            "level": "error",
            "msg": f"语法错误：{exc.msg}",
            "pos": f"line:{exc.lineno}",
        })
        result["score"] = 0
        return result

    issues = []
    _check_naming(tree, issues)
    _check_docstring(tree, issues)
    _check_complexity(tree, issues)
    _check_security(tree, issues)
    _check_redundant_import(tree, issues)

    result["lint_issues"] = issues
    result["score"] = _calc_score(issues)
    return result


def _calc_score(issues):
    score = 100
    for issue in issues:
        score -= 15 if issue["level"] == "error" else 5
    return max(0, score)


# ---- 命名规范 ----
def _check_naming(tree, issues):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_snake(node.name):
                issues.append({"level": "warn",
                               "msg": f"函数名应使用 snake_case：'{node.name}'",
                               "pos": f"line:{node.lineno}"})
            for arg in node.args.args:
                if _is_mixed_case(arg.arg):
                    issues.append({"level": "warn",
                                   "msg": f"参数命名混乱：'{arg.arg}'",
                                   "pos": f"line:{node.lineno}"})
        elif isinstance(node, ast.ClassDef):
            if not _is_camel(node.name):
                issues.append({"level": "warn",
                               "msg": f"类名应使用 CamelCase：'{node.name}'",
                               "pos": f"line:{node.lineno}"})
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _is_mixed_case(target.id):
                    issues.append({"level": "warn",
                                   "msg": f"变量命名混乱：'{target.id}'",
                                   "pos": f"line:{node.lineno}"})


def _is_snake(name):
    return name == name.lower()


def _is_camel(name):
    return bool(name) and name[0].isupper() and "_" not in name


def _is_mixed_case(name):
    return any(c.isupper() for c in name) and name != name.upper()


# ---- docstring ----
def _check_docstring(tree, issues):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue  # 豁免私有成员 / dunder 方法
            if ast.get_docstring(node) is None:
                kind = "函数" if isinstance(node, ast.FunctionDef) else "类"
                issues.append({"level": "warn",
                               "msg": f"{kind}缺少 docstring：'{node.name}'",
                               "pos": f"line:{node.lineno}"})


# ---- 复杂度 / 可读性 ----
def _check_complexity(tree, issues):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines = (node.end_lineno or node.lineno) - node.lineno + 1
            if lines > 50:
                issues.append({"level": "warn",
                               "msg": f"函数过长（{lines} 行）：'{node.name}'",
                               "pos": f"line:{node.lineno}"})
            nargs = len(node.args.args) + len(node.args.kwonlyargs)
            if nargs > 5:
                issues.append({"level": "warn",
                               "msg": f"函数参数过多（{nargs} 个）：'{node.name}'",
                               "pos": f"line:{node.lineno}"})


# ---- 基础安全 ----
def _check_security(tree, issues):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            _check_dangerous_call(node, issues)
        elif isinstance(node, ast.Assign):
            _check_hardcoded_secret(node, issues)
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append({"level": "warn",
                               "msg": "裸 except 未指定异常类型",
                               "pos": f"line:{node.lineno}"})


def _check_dangerous_call(node, issues):
    func = node.func
    if isinstance(func, ast.Name) and func.id in DANGEROUS_BUILTINS:
        issues.append({"level": "error",
                       "msg": f"使用 {func.id} 存在代码注入风险",
                       "pos": f"line:{node.lineno}"})
        return
    if isinstance(func, ast.Attribute):
        if func.attr in SUBPROCESS_CALLS and _has_shell_true(node):
            issues.append({"level": "warn",
                           "msg": "subprocess 使用 shell=True 存在命令注入风险",
                           "pos": f"line:{node.lineno}"})
        if func.attr in ("load", "loads") and \
                isinstance(func.value, ast.Name) and func.value.id == "pickle":
            issues.append({"level": "warn",
                           "msg": "pickle 反序列化不可信数据存在风险",
                           "pos": f"line:{node.lineno}"})


def _has_shell_true(call):
    for kw in call.keywords:
        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and \
                kw.value.value is True:
            return True
    return False


def _check_hardcoded_secret(node, issues):
    if not isinstance(node.value, ast.Constant) or \
            not isinstance(node.value.value, str):
        return
    for target in node.targets:
        if isinstance(target, ast.Name) and _is_secret_name(target.id):
            issues.append({"level": "error",
                           "msg": f"硬编码敏感信息：'{target.id}'",
                           "pos": f"line:{node.lineno}"})


def _is_secret_name(name):
    low = name.lower()
    return any(keyword in low for keyword in SECRET_KEYWORDS)


# ---- 冗余 ----
def _check_redundant_import(tree, issues):
    seen = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in seen:
                    issues.append({"level": "warn",
                                   "msg": f"重复 import：'{alias.name}'",
                                   "pos": f"line:{node.lineno}"})
                else:
                    seen[alias.name] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ""
            if name in seen:
                issues.append({"level": "warn",
                               "msg": f"重复 import：'{name}'",
                               "pos": f"line:{node.lineno}"})
            elif name:
                seen[name] = node.lineno
