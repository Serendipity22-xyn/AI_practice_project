---
name: git_save_skill
description: 在当前工作目录一键执行 git 保存并推送（自动 init、生成 .gitignore、add、commit、push）。当用户要求"git 保存""一键提交""保存并推送""存档代码""快速 commit 并 push"等场景时使用。
---

# git_save_skill — git 一键保存推送

在当前工作目录完成 git 的保存与推送全流程。核心是一个可复用的 shell 脚本，确保每一步可预期、可追溯、异常即停。

## 适用场景

- 用户想快速把当前目录的改动 commit 并 push
- 目录尚未初始化 git 仓库，需要一并完成初始化
- 需要防止日志、密钥、环境配置等文件被误传

## 执行流程

运行 `scripts/git_save.sh`，脚本在**当前工作目录**依次完成：

1. 检测 `.git`，不存在则 `git init`
2. 不存在 `.gitignore` 时生成默认模板（日志、缓存、环境配置、虚拟环境、编译产物、密钥/隐私文件）；已存在则保留不覆盖
3. `git add .`
4. `git commit`，信息格式 `git save: <时间戳> [- 备注]`
5. 检查 `origin`，未配置则提示并终止（本地 commit 已保留，不报错崩溃）
6. `git push`（无 upstream 时自动 `-u origin <分支>`）

脚本使用 `set -e`，任何 git 异常（冲突、权限、网络失败）会立即停止并输出错误，不继续后续步骤。

## 使用方式

```bash
bash "<本 skill 目录>/scripts/git_save.sh" [备注信息]
```

- 备注信息可选，会追加到时间戳后；不带备注则 commit 信息仅含时间戳
- 脚本在当前工作目录执行，调用前确保 cwd 已切换到目标项目目录

## 调用前必做：防密钥泄露扫描

脚本生成的 `.gitignore` 已覆盖常见敏感文件，但为保险，调用前先扫描目标目录，识别未覆盖的密钥/隐私文件并追加进 `.gitignore`：

- 用 Glob/Grep 检查是否存在 `.env`、`*.pem`、`*.key`、`id_rsa*`、`secrets.*`、`credentials*`、`*.ppk`、含密码/token 的 `config.*` 等
- 若发现 `.gitignore` 未覆盖的敏感文件，先追加对应规则到 `.gitignore` 再运行脚本
- 若发现明显是密钥的文件已被 `git add`（处于暂存或已被跟踪），先提示用户处理

## 结果汇报

脚本执行结束后，向用户简要汇报：是否初始化、commit 哈希与信息、是否成功 push、或失败的步骤与原因。
