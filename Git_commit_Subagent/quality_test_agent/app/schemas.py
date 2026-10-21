# -*- coding: utf-8 -*-
"""数据契约：quality-test 各 skill 与 workflow 的输入输出模型。"""

from typing import List, Optional

from pydantic import BaseModel, Field


class LintIssue(BaseModel):
    """单条质检问题。"""
    level: str  # warn / error
    msg: str
    pos: str = ""


class LintResult(BaseModel):
    """扫描结果。"""
    lint_issues: List[LintIssue] = Field(default_factory=list)
    score: int = 100
    error: Optional[str] = None


class JudgeResult(BaseModel):
    """判定结果。"""
    overall_status: str  # pass / fail
    summary: str
    score: int = 0
    threshold: int = 80


class QualityRunRequest(BaseModel):
    """子 Agent 调度入参。"""
    source_code: str
    lang: str = "python"
    requirement: str = ""
    target_path: Optional[str] = None
