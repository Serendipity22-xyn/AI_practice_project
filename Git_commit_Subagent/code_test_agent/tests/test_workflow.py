# -*- coding: utf-8 -*-
"""code-test 项目自测：验证工作流对示例模块能正确分析、跑通并生成标识文件。"""

import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import workflow  # noqa: E402

EXAMPLES = os.path.join(PROJECT_ROOT, "examples")


def _read_calculator():
    with open(os.path.join(EXAMPLES, "calculator.py"), "r", encoding="utf-8") as fh:
        return fh.read()


def _tmp_copy():
    """把示例复制到临时目录，避免污染 examples/。"""
    tmp = tempfile.mkdtemp(prefix="code_test_self_")
    target = os.path.join(tmp, "calculator.py")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(_read_calculator())
    return tmp, target


def test_analyze_identifies_functions_and_deps():
    result = workflow.run(source_code=_read_calculator(), module_name="calculator",
                          workspace=tempfile.mkdtemp())
    analyze = result["analyze_result"]
    assert analyze["error"] is None
    assert len(analyze["func_list"]) == 4
    # 识别到外部依赖 requests
    assert any(d["name"] == "requests" for d in analyze["external_deps"])


def test_workflow_passes_and_writes_flag():
    tmp, target = _tmp_copy()
    result = workflow.run(source_code=_read_calculator(), module_name="calculator",
                          test_target=target, workspace=tmp)

    assert result["overall_status"] == "passed", result.get("report")
    assert result["flag"]["operate_status"] == "success"
    assert os.path.exists(os.path.join(tmp, ".code_test_pass.flag"))
    assert result["case_detail"], "应收集到用例明细"


def test_syntax_error_returns_clear_report():
    result = workflow.run(source_code="def broken(:", module_name="bad",
                          workspace=tempfile.mkdtemp())
    assert result["overall_status"] == "failed"
    assert result["analyze_result"]["error"]
    assert "语法" in result["report"]
