# quality-test 质检子 Agent

独立的代码质量检查子 Agent 项目，纯 Python 函数编排实现。职责：代码规范扫描 → 质量判定 → 生成质检标识文件。

对外提供两种调用方式：**CLI**（跨项目主通道）与 **FastAPI**（HTTP 方式）。

## 目录结构

```
quality_test_agent/
├── cli.py                        # CLI 入口（跨项目调用主通道）
├── app/
│   ├── workflow.py               # 固定工作流编排（3 步）
│   ├── main.py                   # FastAPI 入口
│   ├── schemas.py                # 数据契约（Pydantic）
│   └── skills/
│       ├── code_lint.py          # skill-code-lint 规范扫描（ast）
│       ├── quality_judge.py      # skill-quality-judge 质量判定
│       └── write_quality_flag.py # skill-write-quality-flag 写质检标识
├── agents/quality-test.md        # 子 Agent 标准定义（复制到 ~/.claude/agents/）
├── examples/good_code.py         # 合规示例
├── examples/bad_code.py          # 不合规示例
└── tests/test_workflow.py        # 本项目自测
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方式

### 1. CLI（推荐，子 Agent 调用）

```bash
# 待质检文件路径（flag 生成在同级目录）
python cli.py --source examples/good_code.py

# 源码字符串
python cli.py --source "def f(): return 1" --inline

# 指定质量阈值
python cli.py --source examples/good_code.py --requirement "阈值90"
```

输出统一以 `【QUALITY_TEST_RESULT】` 开头，退出码 0=pass / 1=fail。

### 2. FastAPI

```bash
uvicorn app.main:app --reload
```

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/quality-test/run` | 完整质检工作流（主调度） |
| POST | `/quality-test/lint` | 代码规范扫描 |
| POST | `/quality-test/judge` | 质量结果判定 |
| POST | `/quality-test/write-flag` | 写质检标识 |

## 三个内置 Skill 契约

| skill | 入参 | 输出 |
|---|---|---|
| code-lint | source_code, lang | lint_issues（level/msg/pos）/ score |
| quality-judge | lint 结果, requirement | overall_status / summary |
| write-quality-flag | target_path, judge_result | flag_file_name / flag_content / operate_status |

## 质量检查项与评分

- **error 级（-15 分）**：语法错误、eval/exec 注入风险、硬编码密钥/token
- **warn 级（-5 分）**：命名混乱、缺 docstring、函数过长、参数过多、裸 except、shell=True、pickle 反序列化、重复 import
- 满分 100，默认 **score ≥ 80 且无 error → pass**

## 全局子 Agent 接入

将 `agents/quality-test.md` 复制到 `C:\Users\<用户>\.claude\agents\` 目录，即可让所有项目通过主 Agent 调用 `quality-test` 子 Agent。

## 关键约束

- 只做代码质量质检，**不跑单元测试**。
- 质检失败时**禁止**写 `.code_quality_pass.flag`。
- 重复提交复检会自动删除旧标识文件再重跑。
- 轻量化：聚焦规范、可读性、基础安全，不做深度逻辑测试。
