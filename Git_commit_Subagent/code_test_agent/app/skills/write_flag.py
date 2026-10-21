# -*- coding: utf-8 -*-
"""skill-write-flag：写入测试通过标识文件。

约束：仅整体测试通过（overall_status == passed）时才允许调用；
失败时返回 skipped，绝不写标识文件。
"""

import json
import os
from datetime import datetime

FLAG_FILE_NAME = ".code_test_pass.flag"


def write_flag(test_target, test_result, flag_dir=None):
    """在待测代码同级目录写入 .code_test_pass.flag。

    返回：
      flag_file_name  标识文件名
      flag_content    标识文件 JSON 字符串
      operate_status  success / skipped
    """
    if test_result.get("overall_status") != "passed":
        return {
            "flag_file_name": None,
            "flag_content": None,
            "operate_status": "skipped",
            "reason": "整体测试未通过，禁止写标识文件",
        }

    flag_dir = flag_dir or os.path.dirname(test_target)
    os.makedirs(flag_dir, exist_ok=True)
    flag_path = os.path.join(flag_dir, FLAG_FILE_NAME)

    case_detail = test_result.get("case_detail", [])
    total = len(case_detail)
    passed = sum(1 for c in case_detail if c.get("result") == "passed")

    content = {
        "test_target": test_target,
        "agent": "code-test",
        "test_time": datetime.now().isoformat(timespec="seconds"),
        "coverage": test_result.get("coverage_rate", "N/A"),
        "status": "passed",
        "case_count": total,
        "pass_count": passed,
        "summary": f"共 {total} 个用例，通过 {passed} 个，覆盖率 {test_result.get('coverage_rate', 'N/A')}",
    }

    with open(flag_path, "w", encoding="utf-8") as fh:
        json.dump(content, fh, ensure_ascii=False, indent=2)

    return {
        "flag_file_name": FLAG_FILE_NAME,
        "flag_content": json.dumps(content, ensure_ascii=False),
        "operate_status": "success",
        "flag_path": flag_path,
    }
