# -*- coding: utf-8 -*-
"""quality-test 固定工作流编排。

节点顺序：
1. skill-code-lint          代码规范扫描
2. skill-quality-judge      质量结果判定
3. 分支判断：
   - pass -> skill-write-quality-flag 写入 .code_quality_pass.flag
   - fail -> 输出问题清单，禁止写标识文件

输出统一携带【QUALITY_TEST_RESULT】头部。
"""

import os

from app.skills import code_lint, quality_judge, write_quality_flag

RESULT_HEADER = "【QUALITY_TEST_RESULT】"


def run(source_code, lang="python", requirement="", target_path=None):
    """执行完整质检工作流，返回结构化结果字典。"""
    report = {"header": RESULT_HEADER, "agent": "quality-test"}

    # ---- 1. 代码扫描 ----
    lint_result = code_lint.lint(source_code, lang)
    report["lint_issues"] = lint_result["lint_issues"]
    report["score"] = lint_result["score"]
    if lint_result.get("error"):
        report["overall_status"] = "fail"
        report["report"] = f"[fail] 扫描阶段：{lint_result['error']}"
        return report

    # ---- 2. 质量判定 ----
    judge_result = quality_judge.judge(lint_result, requirement)
    report["overall_status"] = judge_result["overall_status"]
    report["summary"] = judge_result["summary"]
    report["threshold"] = judge_result["threshold"]
    report["report"] = judge_result["summary"]

    # ---- 3. 分支判断 ----
    if judge_result["overall_status"] == "pass":
        _remove_old_flag(target_path)
        report["flag"] = write_quality_flag.write_quality_flag(target_path, judge_result)
    else:
        report["flag"] = None
        report["issue_list"] = _format_issue_list(lint_result["lint_issues"])

    return report


def _remove_old_flag(target_path):
    """重复提交复检：删除目标代码同级目录下的旧标识文件。"""
    if not target_path:
        return
    old_flag = os.path.join(os.path.dirname(target_path),
                            write_quality_flag.FLAG_FILE_NAME)
    if os.path.exists(old_flag):
        os.remove(old_flag)


def _format_issue_list(issues):
    """格式化问题清单。"""
    lines = ["问题清单："]
    for item in issues:
        level = "ERROR" if item["level"] == "error" else "WARN"
        lines.append(f"- [{level}] {item['pos']} {item['msg']}")
    return "\n".join(lines)
