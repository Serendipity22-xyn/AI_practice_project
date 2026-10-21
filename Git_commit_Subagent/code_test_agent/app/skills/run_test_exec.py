# -*- coding: utf-8 -*-
"""skill-run-test-exec：测试执行 & 结果统计。

把待测源码与测试代码物化到独立 workspace，用 subprocess 运行 pytest，
解析 junit 报告与覆盖率，产出整体状态与逐用例明细。

完善异常兜底：源码语法错误、测试脚本报错、依赖缺失均返回清晰错误报告。
"""

import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def run_test_exec(source_code, test_code, module_name="target_module", workspace=None):
    """执行单元测试并统计结果。

    返回：
      overall_status  passed / failed
      case_detail     逐用例 {case_name, result, error_msg}
      coverage_rate   覆盖率字符串（如 "87%"，无法统计时为 N/A）
    """
    if workspace is None:
        workspace = tempfile.mkdtemp(prefix="code_test_")
    os.makedirs(workspace, exist_ok=True)

    src_path = os.path.join(workspace, f"{module_name}.py")
    test_path = os.path.join(workspace, f"test_{module_name}.py")
    junit_path = os.path.join(workspace, "report.xml")

    with open(src_path, "w", encoding="utf-8") as fh:
        fh.write(source_code)
    with open(test_path, "w", encoding="utf-8") as fh:
        fh.write(test_code)

    base_cmd = [sys.executable, "-m", "pytest", test_path,
                f"--junitxml={junit_path}", "-q"]
    cov_cmd = base_cmd + [f"--cov={module_name}", "--cov-report=term"]

    # 优先带覆盖率运行；若 pytest-cov 缺失则退化为普通运行
    proc = _run(cov_cmd, workspace)
    if proc is None:
        return _fail(workspace, src_path, "缺少 python/pytest，请先执行：pip install pytest pytest-cov")

    stderr = proc.stderr or ""
    stdout = proc.stdout or ""

    if "No module named pytest" in stderr:
        return _fail(workspace, src_path,
                     "缺少依赖 pytest，请先执行：pip install pytest pytest-cov")

    if "unrecognized arguments" in stderr or "pytest_cov" in stderr:
        proc = _run(base_cmd, workspace)
        if proc is None:
            return _fail(workspace, src_path, "缺少 python/pytest，请先执行：pip install pytest pytest-cov")
        coverage_rate = "N/A"
        stderr = proc.stderr or ""
        stdout = proc.stdout or ""
    else:
        coverage_rate = _parse_coverage(stdout + stderr)

    case_detail = _parse_junit(junit_path)
    overall = "passed" if proc.returncode == 0 else "failed"

    result = {
        "overall_status": overall,
        "case_detail": case_detail,
        "coverage_rate": coverage_rate,
        "workspace": workspace,
        "src_path": src_path,
        "stdout": stdout,
        "stderr": stderr,
    }

    # 测试脚本 / 源码自身错误兜底
    if not case_detail and overall == "failed":
        result["error"] = _extract_error(stdout + stderr)

    return result


def _run(cmd, cwd):
    """运行命令，返回 CompletedProcess；解释器缺失时返回 None。"""
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              cwd=cwd, timeout=180)
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        # 超时也视为失败，用占位结果
        return subprocess.CompletedProcess(cmd, returncode=1,
                                           stdout="", stderr="测试执行超时（180s）")


def _parse_junit(path):
    """解析 junit 报告，返回逐用例明细。"""
    cases = []
    if not os.path.exists(path):
        return cases
    try:
        root = ET.parse(path).getroot()
        for testcase in root.iter("testcase"):
            name = testcase.get("name", "")
            if testcase.find("skipped") is not None:
                cases.append({"case_name": name, "result": "skipped", "error_msg": ""})
            elif testcase.find("failure") is not None:
                msg = testcase.find("failure").get("message", "") or ""
                cases.append({"case_name": name, "result": "failed", "error_msg": msg[:500]})
            elif testcase.find("error") is not None:
                msg = testcase.find("error").get("message", "") or ""
                cases.append({"case_name": name, "result": "error", "error_msg": msg[:500]})
            else:
                cases.append({"case_name": name, "result": "passed", "error_msg": ""})
    except ET.ParseError:
        pass
    return cases


def _parse_coverage(text):
    """从 pytest-cov 输出中提取 TOTAL 行覆盖率。"""
    for line in text.splitlines():
        m = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", line)
        if m:
            return f"{m.group(1)}%"
    return "N/A"


def _extract_error(text):
    """从输出中提取一句可读的错误摘要。"""
    for line in text.splitlines():
        if line.strip().startswith(("E ", "Error", "ModuleNotFoundError",
                                    "SyntaxError", "ImportError", "NameError")):
            return line.strip()[:300]
    return "测试执行失败，详见 stdout/stderr"


def _fail(workspace, src_path, message):
    """构造失败结果。"""
    return {
        "overall_status": "failed",
        "case_detail": [],
        "coverage_rate": "N/A",
        "workspace": workspace,
        "src_path": src_path,
        "error": message,
    }
