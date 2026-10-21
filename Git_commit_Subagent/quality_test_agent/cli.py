# -*- coding: utf-8 -*-
"""CLI 入口：quality-test 质检子 Agent 跨项目调用主通道。

用法示例：
  # 传入待质检文件路径（flag 生成在该文件同级目录）
  python cli.py --source path/to/foo.py

  # 传入源码字符串（--inline）
  python cli.py --source "def f(): return 1" --inline

  # 指定质量阈值
  python cli.py --source path/to/foo.py --requirement "阈值90"

输出统一以【QUALITY_TEST_RESULT】开头，退出码 0=pass / 1=fail。
"""

import argparse
import json
import os
import sys

# Windows 控制台默认 GBK，强制 stdout 输出 UTF-8，避免中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import workflow  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="quality-test 质检子 Agent")
    parser.add_argument("--source", required=True,
                        help="待质检文件路径，或（配合 --inline）源码字符串")
    parser.add_argument("--inline", action="store_true",
                        help="标记 --source 传入的是源码字符串而非文件路径")
    parser.add_argument("--lang", default="python", help="编程语言，默认 python")
    parser.add_argument("--requirement", default="",
                        help="质检阈值要求，如 '阈值90'")
    args = parser.parse_args()

    source_code = args.source
    target_path = None

    if not args.inline:
        path = os.path.abspath(args.source)
        if not os.path.exists(path):
            _emit({"header": "【QUALITY_TEST_RESULT】", "overall_status": "fail",
                   "report": f"[fail] 待质检文件不存在：{path}"})
            return 1
        with open(path, "r", encoding="utf-8") as fh:
            source_code = fh.read()
        target_path = path

    result = workflow.run(source_code=source_code, lang=args.lang,
                          requirement=args.requirement, target_path=target_path)
    _emit(result)
    return 0 if result.get("overall_status") == "pass" else 1


def _emit(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
