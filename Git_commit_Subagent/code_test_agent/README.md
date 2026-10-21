# code-test 单元测试子 Agent

独立的单元测试专家子 Agent 项目，纯 Python 函数编排实现。职责：代码静态分析 → 单元测试生成 → 执行校验 → 生成测试通过标识文件。

对外提供两种调用方式：**CLI**（跨项目主通道）与 **FastAPI**（HTTP 方式）。

## 目录结构

```
code_test_agent/
├── cli.py                  # CLI 入口（子 Agent 跨项目调用主通道）
├── app/
│   ├── workflow.py         # 固定工作流编排（4 步，顺序不可乱）
│   ├── main.py             # FastAPI 入口
│   ├── schemas.py          # 输入输出数据契约（Pydantic）
│   └── skills/
│       ├── code_analyze.py # skill-code-analyze 静态分析（ast）
│       ├── gen_unit_test.py# skill-gen-unit-test 生成单测
│       ├── run_test_exec.py# skill-run-test-exec 执行&统计
│       └── write_flag.py   # skill-write-flag 写通过标识
├── agents/code-test.md     # 子 Agent 标准定义（复制到 ~/.claude/agents/ 全局可用）
├── examples/calculator.py  # 示例待测模块
└── tests/test_workflow.py  # 本项目自测
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方式

### 1. CLI（推荐，子 Agent 调用）

```bash
# 待测文件路径（flag 生成在同级目录）
python cli.py --source examples/calculator.py

# 源码字符串
python cli.py --source "def add(a, b): return a + b" --inline --module-name foo

# 附加测试约束
python cli.py --source examples/calculator.py --requirement "覆盖所有异常分支"
```

输出统一以 `【CODE_TEST_RESULT】` 开头，退出码 0=passed / 1=failed。

### 2. FastAPI

```bash
uvicorn app.main:app --reload
```

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/code-test/run` | 完整工作流（主调度） |
| POST | `/code-test/analyze` | 静态分析 |
| POST | `/code-test/gen-test` | 生成单测 |
| POST | `/code-test/run-test` | 执行测试 |
| POST | `/code-test/write-flag` | 写通过标识 |

请求体示例：

```json
{
  "source_code": "def add(a, b):\n    return a + b\n",
  "lang": "python",
  "requirement": "",
  "module_name": "foo"
}
```

## 四个内置 Skill 契约

| skill | 入参 | 输出 |
|---|---|---|
| code-analyze | source_code, lang | func_list / branch_points / external_deps / exception_raise |
| gen-unit-test | analyze_result | test_code / mock_list / run_cmd / install_deps |
| run-test-exec | source_code, test_code | overall_status / case_detail / coverage_rate |
| write-flag | test_target, test_result | flag_file_name / flag_content / operate_status |

## 全局子 Agent 接入

将 `agents/code-test.md` 复制到 `C:\Users\<用户>\.claude\agents\` 目录，即可让所有项目通过主 Agent 调用 `code-test` 子 Agent。

## 关键约束

- 外部网络 / 数据库一律 mock 隔离，**严禁请求真实线上资源**。
- 测试整体失败时**禁止**写 `.code_test_pass.flag`。
- 重复提交复测会自动删除旧标识文件再重跑。
