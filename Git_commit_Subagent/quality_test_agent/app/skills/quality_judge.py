# -*- coding: utf-8 -*-
"""skill-quality-judge：质量结果判定。

根据 lint 扫描结果与用户质量阈值要求，判定整体通过 / 不通过。
默认阈值 80 分且无 error 项；用户可在 requirement 中覆盖阈值。
"""

import re

DEFAULT_THRESHOLD = 80


def judge(lint_result, requirement=""):
    """判定质量结果。

    返回：
      overall_status  pass / fail
      summary         质检总结
      score           质量分
      threshold       采用的阈值
    """
    score = lint_result.get("score", 0)
    issues = lint_result.get("lint_issues", [])
    threshold = _parse_threshold(requirement)

    error_count = sum(1 for it in issues if it.get("level") == "error")
    warn_count = sum(1 for it in issues if it.get("level") == "warn")

    overall = "pass" if (score >= threshold and error_count == 0) else "fail"
    summary = (
        f"质量分 {score}（阈值 {threshold}），error {error_count} 项，"
        f"warn {warn_count} 项，判定 {overall}"
    )
    return {
        "overall_status": overall,
        "summary": summary,
        "score": score,
        "threshold": threshold,
    }


def _parse_threshold(requirement):
    """从 requirement 解析阈值，支持「阈值90」「threshold 90」「score>=90」。"""
    if not requirement:
        return DEFAULT_THRESHOLD
    match = re.search(r"(?:阈值|threshold|score\s*[>=]+\s*)\s*(\d{1,3})",
                      requirement, re.I)
    if match:
        return int(match.group(1))
    return DEFAULT_THRESHOLD
