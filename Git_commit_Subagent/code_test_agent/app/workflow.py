# -*- coding: utf-8 -*-
"""code-test 固定工作流编排。

节点顺序（不可乱）：
1. skill-code-analyze   静态分析源代码
2. skill-gen-unit-test  生成单元测试代码
3. skill-run-test-exec  执行测试并统计
4. 分支判断：
   - passed -> skill-write-flag 写入 .code_test_pass.flag
   - failed -> 输出缺陷报告，禁止写标识文件

对外返回统一带上【CODE_TEST_RESULT】头部，输出顺序为：
汇总报告 -> 单元测试源码 -> 执行指令 ->（通过时）flag 信息。
"""

import os

from app.skills import code_analyze, gen_unit_test, run_test_exec, write_flag

RESULT_HEADER = "【CODE_TEST_RESULT】"


def run(source_code, lang="python", requirement="", module_name=None,
        test_target=None, workspace=None):
    """执行完整工作流，返回结构化结果字典。"""
    report = {"header": RESULT_HEADER, "agent": "code-test"}

    # ---- 1. 静态分析 ----
    analyze_result = code_analyze.analyze(source_code, lang)
    report["analyze_result"] = analyze_result
    if analyze_result.get("error"):
        report["overall_status"] = "failed"
        report["report"] = f"[失败] 静态分析阶段：{analyze_result['error']}"
        return report

    # ---- 2. 生成单测 ----
    module = module_name or _infer_module_name(test_target) or "target_module"
    gen_result = gen_unit_test.gen_unit_test(analyze_result, module)
    report["test_code"] = gen_result["test_code"]
    report["mock_list"] = gen_result["mock_list"]
    report["run_cmd"] = gen_result["run_cmd"]
    report["install_deps"] = gen_result["install_deps"]

    # ---- 3. 执行测试 ----
    run_result = run_test_exec.run_test_exec(
        source_code, gen_result["test_code"], module, workspace)
    report["case_detail"] = run_result.get("case_detail", [])
    report["coverage_rate"] = run_result.get("coverage_rate", "N/A")

    # ---- 4. 分支判断 ----
    if run_result.get("overall_status") == "passed":
        target = test_target or run_result.get("src_path")
        _remove_old_flag(target)
        flag = write_flag.write_flag(target, run_result)
        report["overall_status"] = "passed"
        report["flag"] = flag
        report["report"] = _build_report(run_result, flag=flag)
    else:
        report["overall_status"] = "failed"
        report["defect_report"] = _build_defect_report(run_result)
        report["report"] = _build_report(run_result, flag=None)

    return report


def _infer_module_name(test_target):
    """从待测文件路径推断模块名（去掉目录与 .py 后缀）。"""
    if not test_target:
        return None
    base = os.path.basename(test_target)
    return os.path.splitext(base)[0]


def _remove_old_flag(test_target):
    """重复提交复测：删除待测代码同级目录下的旧标识文件。"""
    if not test_target:
        return
    flag_dir = os.path.dirname(test_target)
    old_flag = os.path.join(flag_dir, write_flag.FLAG_FILE_NAME)
    if os.path.exists(old_flag):
        os.remove(old_flag)


def _build_report(run_result, flag=None):
    """生成文本汇总报告。"""
    cases = run_result.get("case_detail", [])
    total = len(cases)
    passed = sum(1 for c in cases if c.get("result") == "passed")
    status = run_result.get("overall_status")
    coverage = run_result.get("coverage_rate", "N/A")

    lines = [
        f"整体状态：{status}",
        f"用例总数：{total}，通过：{passed}，失败：{total - passed}",
        f"代码覆盖率：{coverage}",
    ]
    if flag:
        lines.append(f"标识文件：{flag.get('flag_path')}")
    return "\n".join(lines)


def _build_defect_report(run_result):
    """生成缺陷报告，列出失败用例与报错信息。"""
    failed = [c for c in run_result.get("case_detail", [])
              if c.get("result") in ("failed", "error")]
    lines = ["缺陷报告：以下用例未通过"]
    if run_result.get("error"):
        lines.append(f"- 执行错误：{run_result['error']}")
    for case in failed:
        lines.append(f"- {case['case_name']} [{case['result']}]: {case.get('error_msg', '')}")
    if not failed and not run_result.get("error"):
        lines.append("- 未收集到用例明细，请检查测试脚本或依赖")
    return "\n".join(lines)
