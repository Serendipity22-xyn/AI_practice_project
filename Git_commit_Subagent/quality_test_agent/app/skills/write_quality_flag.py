# -*- coding: utf-8 -*-
"""skill-write-quality-flag：写入质检标识文件。

约束：仅 overall_status == pass 时允许调用；失败返回 skipped，绝不写标识文件。
"""

import json
import os
from datetime import datetime

FLAG_FILE_NAME = ".code_quality_pass.flag"


def write_quality_flag(target_path, judge_result, flag_dir=None):
    """在目标代码同级目录写入 .code_quality_pass.flag。

    返回：
      flag_file_name  标识文件名
      flag_content    标识文件 JSON 字符串
      operate_status  success / skipped
    """
    if judge_result.get("overall_status") != "pass":
        return {
            "flag_file_name": None,
            "flag_content": None,
            "operate_status": "skipped",
            "reason": "质检未通过，禁止写标识文件",
        }

    flag_dir = flag_dir or os.path.dirname(target_path)
    os.makedirs(flag_dir, exist_ok=True)
    flag_path = os.path.join(flag_dir, FLAG_FILE_NAME)

    content = {
        "target": target_path,
        "agent": "quality-test",
        "time": datetime.now().isoformat(timespec="seconds"),
        "score": judge_result.get("score", 0),
        "status": "pass",
        "summary": judge_result.get("summary", ""),
    }

    with open(flag_path, "w", encoding="utf-8") as fh:
        json.dump(content, fh, ensure_ascii=False, indent=2)

    return {
        "flag_file_name": FLAG_FILE_NAME,
        "flag_content": json.dumps(content, ensure_ascii=False),
        "operate_status": "success",
        "flag_path": flag_path,
    }
