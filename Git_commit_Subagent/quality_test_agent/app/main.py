# -*- coding: utf-8 -*-
"""FastAPI 入口：对外提供 quality-test 质检子 Agent 调用能力。

接口：
- GET  /health                  健康检查
- POST /quality-test/run        完整质检工作流（主调度）
- POST /quality-test/lint       代码规范扫描
- POST /quality-test/judge      质量结果判定
- POST /quality-test/write-flag 写质检标识
"""

from fastapi import FastAPI

from app import workflow
from app.schemas import QualityRunRequest
from app.skills import code_lint, quality_judge, write_quality_flag

app = FastAPI(title="quality-test 质检子 Agent", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "agent": "quality-test"}


@app.post("/quality-test/run")
def run(req: QualityRunRequest):
    """完整质检：扫描 -> 判定 -> (pass)写flag / (fail)问题清单。"""
    return workflow.run(
        source_code=req.source_code,
        lang=req.lang,
        requirement=req.requirement,
        target_path=req.target_path,
    )


@app.post("/quality-test/lint")
def lint(req: QualityRunRequest):
    return code_lint.lint(req.source_code, req.lang)


@app.post("/quality-test/judge")
def judge(req: QualityRunRequest):
    lint_result = code_lint.lint(req.source_code, req.lang)
    return quality_judge.judge(lint_result, req.requirement)


@app.post("/quality-test/write-flag")
def write_flag(req: QualityRunRequest):
    lint_result = code_lint.lint(req.source_code, req.lang)
    judge_result = quality_judge.judge(lint_result, req.requirement)
    return write_quality_flag.write_quality_flag(req.target_path, judge_result)
