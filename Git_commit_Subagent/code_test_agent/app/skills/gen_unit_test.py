# -*- coding: utf-8 -*-
"""skill-gen-unit-test：单元测试代码生成器。

根据静态分析结果生成 pytest 单元测试代码，覆盖三类用例：
1. 正常用例（normal）：默认参数调用不抛异常，可推断返回值时做精确断言
2. 边界用例（boundary）：边界参数（0 / 空值）不导致非预期崩溃
3. 异常用例（exception）：针对 raise 点用 pytest.raises 精确断言

对外部依赖（数据库、三方 API 等）自动使用 unittest.mock 隔离，
严禁请求真实线上资源。
"""


def gen_unit_test(analyze_result, module_name="target_module",
                  framework="pytest", coverage_target="branch"):
    """生成单元测试代码。

    返回：
      test_code     完整测试代码文本
      mock_list     需要 mock 的外部依赖列表
      run_cmd       执行命令
      install_deps  依赖安装命令
    """
    funcs = analyze_result.get("func_list", [])

    lines = [
        '# -*- coding: utf-8 -*-',
        '"""自动生成的单元测试代码。',
        '',
        '覆盖三类用例：正常 / 边界 / 异常；外部依赖已用 mock 隔离。',
        '注意：语义类断言为生成器的推断值，建议按实际业务补充。',
        '"""',
        'import pytest',
        'from unittest import mock',
        '',
        f'import {module_name}',
        '',
    ]

    # 收集需要 mock 的外部调用点
    call_mocks = sorted({
        call for f in funcs for call in f.get("external_calls", [])
    })
    if call_mocks:
        lines.append('# 外部依赖的 mock 响应（严禁请求真实线上资源）')
        lines.append('_MOCK_RESPONSE = mock.MagicMock()')
        lines.append('_MOCK_RESPONSE.json.return_value = {"price": 100.0}')
        lines.append('')

    if not funcs:
        lines.append('# 未识别到可测试函数，请检查待测源码')
        lines.append('def test_placeholder():')
        lines.append('    assert True')
    else:
        for func in funcs:
            lines.extend(_gen_func_cases(func, module_name, call_mocks))

    test_code = "\n".join(lines) + "\n"

    return {
        "test_code": test_code,
        "mock_list": call_mocks,
        "run_cmd": f"python -m pytest test_{module_name}.py --cov={module_name} --cov-report=term -q",
        "install_deps": "pip install pytest pytest-cov",
    }


def _gen_func_cases(func, module_name, call_mocks):
    """为单个函数生成测试类（正常 / 边界 / 异常用例）。"""
    name = func["name"]
    args = func.get("args", [])
    defaults = func.get("defaults", [])
    raises = func.get("raises", [])
    ext_calls = func.get("external_calls", [])
    pattern = func.get("return_pattern")

    normal_vals = _normal_vals(args, defaults)
    normal_call = _format_call(normal_vals)

    out = [f"class Test{_camel(name)}:"]

    # ---- 正常用例 ----
    out.append(f"    def test_{name}_normal(self):")
    out.append(f'        """正常用例：默认参数调用不抛异常。"""')
    if ext_calls:
        for call in ext_calls:
            out.append(f'        with mock.patch("{call}", return_value=_MOCK_RESPONSE):')
            out.append(f'            result = {module_name}.{name}({normal_call})')
        out.append('        # 返回值断言建议按业务补充')
    else:
        out.append(f'        result = {module_name}.{name}({normal_call})')
        assertion = _binop_assertion(pattern, normal_vals, args)
        if assertion:
            out.append(f'        assert result == {assertion}')
        else:
            out.append('        # 返回值断言建议按业务补充')

    # ---- 边界用例（会抛异常的函数跳过，其边界场景由异常用例覆盖）----
    if not raises and args:
        boundary_vals = [0] * len(args)
        boundary_call = _format_call(boundary_vals)
        out.append("")
        out.append(f"    def test_{name}_boundary(self):")
        out.append('        """边界用例：全零 / 边界参数不导致非预期崩溃。"""')
        if ext_calls:
            for call in ext_calls:
                out.append(f'        with mock.patch("{call}", return_value=_MOCK_RESPONSE):')
                out.append(f'            result = {module_name}.{name}({boundary_call})')
        else:
            out.append(f'        result = {module_name}.{name}({boundary_call})')
        assertion = _binop_assertion(pattern, boundary_vals, args)
        if assertion:
            out.append(f'        assert result == {assertion}')
        else:
            out.append('        # 边界值应正常返回或由异常用例覆盖')

    # ---- 异常用例 ----
    for raise_item in raises:
        exc = raise_item.get("exc") or "Exception"
        trigger = raise_item.get("trigger")
        exc_vals = _exception_vals(args, defaults, normal_vals, trigger)
        exc_call = _format_call(exc_vals)
        out.append("")
        out.append(f"    def test_{name}_raises_{_safe_id(exc)}(self):")
        out.append(f'        """异常用例：触发 {exc}。"""')
        out.append(f'        with pytest.raises({exc}):')
        out.append(f'            {module_name}.{name}({exc_call})')

    out.append("")
    return out


def _normal_vals(args, defaults):
    """正常用例的参数值：优先用默认值，否则用占位值 1。"""
    vals = []
    for i, _ in enumerate(args):
        if i < len(defaults) and defaults[i] is not None:
            vals.append(defaults[i])
        else:
            vals.append(1)
    return vals


def _exception_vals(args, defaults, normal_vals, trigger):
    """异常用例的参数值：触发参数用触发值，其余沿用正常值。"""
    trig_var, trig_val = (trigger[0], trigger[1]) if trigger else (None, 0)
    vals = []
    for i, arg in enumerate(args):
        if arg == trig_var:
            vals.append(trig_val)
        elif i < len(defaults) and defaults[i] is not None:
            vals.append(defaults[i])
        else:
            vals.append(normal_vals[i])
    return vals


def _format_call(vals):
    """把参数值列表格式化成调用实参串。"""
    return ", ".join(_py_repr(v) for v in vals)


def _py_repr(value):
    """转成可直接写进代码的字面量。"""
    if isinstance(value, str):
        return repr(value)
    return str(value)


def _binop_assertion(pattern, vals, args):
    """若返回值是可推断的参数二元运算，生成期望值表达式。"""
    if not pattern or pattern.get("kind") != "binop":
        return None
    left, right = pattern["left"], pattern["right"]
    op = pattern["op"]
    if left in args and right in args:
        li, ri = args.index(left), args.index(right)
        return f"{_py_repr(vals[li])} {op} {_py_repr(vals[ri])}"
    return None


def _camel(name):
    """把 snake_case 转成 CamelCase，用于测试类名。"""
    return "".join(part.capitalize() for part in name.split("_")) or "Target"


def _safe_id(name):
    """把异常类型名清洗成合法标识符。"""
    return name.replace(",", "_").replace(".", "_") or "Exception"
