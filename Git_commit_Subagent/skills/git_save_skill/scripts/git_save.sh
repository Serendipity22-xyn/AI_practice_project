#!/usr/bin/env bash
# git_save.sh — git 一键保存并推送
# 用法: bash git_save.sh [备注信息]
# 在当前工作目录执行: init → .gitignore → add → commit → push
# 任何 git 异常(冲突/权限/网络)会立即停止并输出错误, 不继续后续步骤

set -euo pipefail

log() { echo "[git_save] $*"; }
err() { echo "[git_save][错误] $*" >&2; }
on_err() { err "执行失败, 已终止后续操作"; }
trap on_err ERR

NOTE="${*:-}"

# 1. 检测是否已初始化 git 仓库
if [ ! -d .git ]; then
  log "未检测到 .git, 执行 git init"
  git init
else
  log "已存在 .git 仓库"
fi

# 2. 生成 .gitignore (不存在时才生成, 避免覆盖已有配置)
if [ ! -f .gitignore ]; then
  log "生成默认 .gitignore"
  cat > .gitignore <<'EOF'
# === 日志 ===
*.log
logs/
*.tmp

# === 缓存 ===
__pycache__/
*.py[cod]
.cache/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
Thumbs.db

# === 环境配置 ===
.env
.env.*
!.env.example
*.local

# === 虚拟环境 / 依赖 ===
venv/
.venv/
env/
ENV/
node_modules/

# === 编译产物 ===
dist/
build/
*.o
*.so
*.class
*.exe
*.dll
*.dylib
target/
out/

# === 密钥 / 隐私文件 ===
*.pem
*.key
*.p12
*.pfx
*.jks
*.keystore
*.secret
secrets.*
credentials.json
service-account*.json
id_rsa
id_rsa.pub
id_ed25519
id_ed25519.pub
*.ppk
EOF
else
  log "已存在 .gitignore, 保留不覆盖"
fi

# 3. 暂存所有改动
log "git add ."
git add .

# 4. 提交 (时间戳 + 可选备注)
TS="$(date '+%Y-%m-%d %H:%M:%S')"
if [ -n "$NOTE" ]; then
  MSG="git save: $TS - $NOTE"
else
  MSG="git save: $TS"
fi

if git diff --cached --quiet; then
  log "没有需要提交的变更, 跳过 commit"
else
  log "git commit -m \"$MSG\""
  git commit -m "$MSG"
fi

# 5. 检查远程仓库
if ! git remote get-url origin >/dev/null 2>&1; then
  err "未配置远程仓库 origin, 终止推送流程 (本地 commit 已完成)"
  exit 0
fi

# 6. 推送
log "git push"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  git push
else
  log "当前分支无 upstream, 执行 git push -u origin $BRANCH"
  git push -u origin "$BRANCH"
fi

log "完成: 已提交并推送至 origin/$BRANCH"
