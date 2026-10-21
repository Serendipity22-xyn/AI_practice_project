# -*- coding: utf-8 -*-
"""FastAPI 入口：对外提供 code-test 子 Agent 调用能力。

接口：
- GET  /health               健康检查
- POST /code-test/run        完整工作流（主调度接口）
- POST /code-test/analyze    静态分析
- POST /code-test/gen-test   生成单测
- POST /code-test/run-test   执行测试
- POST /code-test/write-flag 写通过标识
"""

from fastapi import FastAPI

from app import workflow
from app.schemas import RunRequest
from app.skills import code_analyze, gen_unit_test, run_test_exec, write_flag

app = FastAPI(title="code-test 单元测试子 Agent", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "agent": "code-test"}


@app.post("/code-test/run")
def run(req: RunRequest):
    """完整工作流：分析 -> 生成 -> 执行 -> 分支判断。"""
    return workflow.run(
        source_code=req.source_code,
        lang=req.lang,
        requirement=req.requirement,
        module_name=req.module_name,
        test_target=req.test_target,
    )


@app.post("/code-test/analyze")
def analyze(req: RunRequest):
    return code_analyze.analyze(req.source_code, req.lang)


@app.post("/code-test/gen-test")
def gen_test(req: RunRequest):
    result = code_analyze.analyze(req.source_code, req.lang)
    if result.get("error"):
        return result
    module = req.module_name or "target_module"
    return gen_unit_test.gen_unit_test(result, module)


@app.post("/code-test/run-test")
def run_test(req: RunRequest):
    result = code_analyze.analyze(req.source_code, req.lang)
    if result.get("error"):
        return result
    module = req.module_name or "target_module"
    gen = gen_unit_test.gen_unit_test(result, module)
    return run_test_exec.run_test_exec(req.source_code, gen["test_code"], module)


@app.post("/code-test/write-flag")
def write_flag_api(req: RunRequest):
    result = code_analyze.analyze(req.source_code, req.lang)
    if result.get("error"):
        return result
    module = req.module_name or "target_module"
    gen = gen_unit_test.gen_unit_test(result, module)
    run_result = run_test_exec.run_test_exec(req.source_code, gen["test_code"], module)
    target = req.test_target or run_result.get("src_path")
    return write_flag.write_flag(target, run_result)
