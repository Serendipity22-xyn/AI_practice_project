# -*- coding: utf-8 -*-
"""quality-test 项目自测：验证合规代码通过、不合规代码失败、语法错误兜底。"""

import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import workflow  # noqa: E402

EXAMPLES = os.path.join(PROJECT_ROOT, "examples")


def _read(name):
    with open(os.path.join(EXAMPLES, name), "r", encoding="utf-8") as fh:
        return fh.read()


def _tmp_copy(name):
    tmp = tempfile.mkdtemp(prefix="quality_self_")
    target = os.path.join(tmp, name)
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(_read(name))
    return tmp, target


def test_good_code_passes_and_writes_flag():
    tmp, target = _tmp_copy("good_code.py")
    result = workflow.run(source_code=_read("good_code.py"),
                          target_path=target)

    assert result["overall_status"] == "pass", result.get("summary")
    assert result["score"] == 100
    assert result["flag"]["operate_status"] == "success"
    assert os.path.exists(os.path.join(tmp, ".code_quality_pass.flag"))


def test_bad_code_fails_with_issue_list():
    tmp, target = _tmp_copy("bad_code.py")
    result = workflow.run(source_code=_read("bad_code.py"),
                          target_path=target)

    assert result["overall_status"] == "fail"
    assert result["flag"] is None
    assert result["issue_list"], "失败时应输出问题清单"
    assert not os.path.exists(os.path.join(tmp, ".code_quality_pass.flag"))
    # 应识别出至少一个 error 级问题（硬编码 / eval）
    assert any(it["level"] == "error" for it in result["lint_issues"])


def test_syntax_error_returns_clear_report():
    result = workflow.run(source_code="def broken(:")
    assert result["overall_status"] == "fail"
    assert result["score"] == 0
    assert any("语法" in it["msg"] for it in result["lint_issues"])


def test_threshold_override():
    # 阈值 100 时，即便无 error，warn 项也会导致 fail
    src = "def f():\n    return 1\n"
    result = workflow.run(source_code=src, requirement="阈值100")
    assert result["threshold"] == 100
    assert result["overall_status"] == "fail"
