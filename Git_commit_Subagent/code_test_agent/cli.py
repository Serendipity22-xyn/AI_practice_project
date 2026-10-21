# -*- coding: utf-8 -*-
"""CLI 入口：code-test 子 Agent 跨项目调用的主通道。

用法示例：
  # 传入待测文件路径（flag 生成在该文件同级目录）
  python cli.py --source path/to/foo.py

  # 传入源码字符串（--inline）
  python cli.py --source "def add(a, b): return a + b" --inline --module-name foo

  # 附加测试约束
  python cli.py --source path/to/foo.py --requirement "覆盖所有异常分支"

输出统一以【CODE_TEST_RESULT】开头，便于主 Agent 解析。
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
    parser = argparse.ArgumentParser(description="code-test 单元测试子 Agent")
    parser.add_argument("--source", required=True,
                        help="待测源码文件路径，或（配合 --inline）源码字符串")
    parser.add_argument("--inline", action="store_true",
                        help="标记 --source 传入的是源码字符串而非文件路径")
    parser.add_argument("--lang", default="python", help="编程语言，默认 python")
    parser.add_argument("--requirement", default="", help="额外测试约束")
    parser.add_argument("--module-name", default=None,
                        help="模块名（--inline 时建议指定）")
    args = parser.parse_args()

    source_code = args.source
    test_target = None

    if not args.inline:
        path = os.path.abspath(args.source)
        if not os.path.exists(path):
            _emit({"header": "【CODE_TEST_RESULT】", "overall_status": "failed",
                   "report": f"[失败] 待测文件不存在：{path}"})
            return 1
        with open(path, "r", encoding="utf-8") as fh:
            source_code = fh.read()
        test_target = path
        module_name = args.module_name or _module_from_path(path)
    else:
        module_name = args.module_name or "target_module"

    result = workflow.run(
        source_code=source_code,
        lang=args.lang,
        requirement=args.requirement,
        module_name=module_name,
        test_target=test_target,
    )

    _emit(result)
    return 0 if result.get("overall_status") == "passed" else 1


def _module_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


def _emit(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
