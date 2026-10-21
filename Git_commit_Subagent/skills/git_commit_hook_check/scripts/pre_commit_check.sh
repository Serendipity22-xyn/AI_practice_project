#!/usr/bin/env bash
# prepare-commit-msg — git commit 前置拦截钩子
# 用 prepare-commit-msg 而非 pre-commit: pre-commit 在 message 生成前触发, 读不到本次提交信息,
# 无法区分 AI/手动提交; prepare-commit-msg 在 message 就绪后触发, 可读取本次 commit message
# 仅拦截 AI 自动提交(commit message 含 "Co-Authored-By: Claude Code"), 手动提交直接放行
# AI 提交时递归校验 3 类验收标识文件, 全部存在才放行(exit 0); 任一缺失则阻断(exit 1)
# 仅做文件存在性校验, 不修改代码、不执行任何 agent, 不影响 git add

set -u

# $1 = COMMIT_EDITMSG 文件路径(含本次 commit message)
MSG_FILE="${1:-$(git rev-parse --git-path COMMIT_EDITMSG)}"
MSG="$(cat "$MSG_FILE" 2>/dev/null || true)"

# 手动提交(不含 Claude Code 标记) -> 静默放行
if ! printf '%s' "$MSG" | grep -q "Co-Authored-By: Claude Code"; then
  exit 0
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"

find_flag() { find "$ROOT" -name "$1" -not -path '*/.git/*' 2>/dev/null | head -n1; }

MISSING=()

# 1. code_test_agent 测试通过标识
[ -n "$(find_flag '.code_test_pass.flag')" ] || \
  MISSING+=(".code_test_pass.flag    (code_test_agent 测试通过标识)")

# 2. quality_test_agent 质检通过标识
[ -n "$(find_flag '.code_quality_pass.flag')" ] || \
  MISSING+=(".code_quality_pass.flag  (quality_test_agent 质检通过标识)")

# 3. handoff 报告
[ -n "$(find "$ROOT/.claude/handoffs" -maxdepth 1 -name '*.md' 2>/dev/null | head -n1)" ] || \
  MISSING+=(".claude/handoffs/*.md    (handoff 报告)")

if [ "${#MISSING[@]}" -gt 0 ]; then
  echo "[commit 拦截] AI 提交校验不通过, 禁止提交:" >&2
  for m in "${MISSING[@]}"; do
    echo "  缺少 $m" >&2
  done
  echo "" >&2
  echo "请先执行对应环节补齐验收产物后再提交:" >&2
  echo "  code_test_agent    -> .code_test_pass.flag" >&2
  echo "  quality_test_agent -> .code_quality_pass.flag" >&2
  echo "  handoff skill      -> .claude/handoffs/*.md" >&2
  echo "  临时跳过本次校验: git commit --no-verify" >&2
  exit 1
fi

echo "[commit 校验通过] 3 类验收文件齐全, 放行 AI 提交"
exit 0
