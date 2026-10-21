---
name: git_commit_hook_check
description: git commit 前置拦截钩子，仅拦截 AI 自动提交（commit message 含 "Co-Authored-By: Claude Code"），手动提交直接放行。AI 提交时校验 code_test_agent、quality_test_agent 标识文件与 handoff 报告三者齐全才放行，缺失则阻断。当用户要求安装 commit 钩子、配置提交拦截、开启提交前验收校验时使用。
---

# git_commit_hook_check — commit 前置拦截钩子

在 `git commit` 时拦截** AI 自动提交**：commit message 含 `Co-Authored-By: Claude Code` 标记则执行验收校验；手动提交直接放行。

## 为什么用 prepare-commit-msg 而非 pre-commit

`pre-commit` 钩子在「获取 commit message 之前」触发，读不到本次提交信息，无法判断是 AI 还是手动提交；`prepare-commit-msg` 在 message 就绪后触发，可读取本次 message。二者都能通过非 0 退出码中止 commit，效果等价。

## 触发判定

- **AI 自动提交**（commit message 含 `Co-Authored-By: Claude Code`）→ 执行校验
- **手动提交**（无该标记）→ 静默放行，不校验

## 校验规则

在 git 仓库内**递归查找**以下 3 类标识文件，必须全部存在才放行 AI 提交：

| 验收环节 | 标识文件 | 产生方 |
|---|---|---|
| 单元测试 | `.code_test_pass.flag` | code_test_agent |
| 代码质检 | `.code_quality_pass.flag` | quality_test_agent |
| 会话交接 | `.claude/handoffs/*.md` | handoff skill |

- 校验**只做文件存在性判断**，不修改代码、不自动执行任何 agent
- 任意一个缺失 → 输出缺失清单并退出非 0，阻断 commit
- 全部存在 → 退出 0，放行 commit
- 仅拦截 commit，不影响 `git add`

## 安装方式

把脚本装为目标仓库的 prepare-commit-msg 钩子（在**目标仓库根目录**执行）：

```bash
cp "<本 skill 目录>/scripts/pre_commit_check.sh" .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

安装后每次 `git commit` 自动触发。可手动验证：

```bash
bash .git/hooks/prepare-commit-msg
```

## 手动执行 / 测试

不安装也可直接跑脚本，校验当前目录所属仓库是否达标：

```bash
bash "<本 skill 目录>/scripts/pre_commit_check.sh"
```

## 跳过 / 卸载

- 临时跳过本次校验：`git commit --no-verify`
- 卸载钩子：删除 `.git/hooks/prepare-commit-msg`

## 结果说明

脚本退出码：`0` 放行、非 `0` 阻断。阻断时输出会明确列出**缺失的文件名称**及对应补齐环节，方便用户定位。
