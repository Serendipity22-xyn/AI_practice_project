# -*- coding: utf-8 -*-
"""数据契约：定义各 skill 与 workflow 的输入输出模型。

skill 内部返回原生 dict（与规格中的 JSON 契约一一对应），
这里的 Pydantic 模型主要用于 FastAPI 接口的参数校验与文档生成。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---- skill-code-analyze ----
class AnalyzeResult(BaseModel):
    """静态分析结果。"""
    func_list: List[Dict[str, Any]] = Field(default_factory=list)
    branch_points: List[Dict[str, Any]] = Field(default_factory=list)
    external_deps: List[Dict[str, Any]] = Field(default_factory=list)
    exception_raise: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


# ---- skill-gen-unit-test ----
class GenTestResult(BaseModel):
    """单测生成结果。"""
    test_code: str
    mock_list: List[str] = Field(default_factory=list)
    run_cmd: str = ""
    install_deps: str = ""


# ---- skill-run-test-exec ----
class CaseDetail(BaseModel):
    """单个用例执行结果。"""
    case_name: str
    result: str  # passed / failed / error / skipped
    error_msg: str = ""


class RunTestResult(BaseModel):
    """测试执行统计结果。"""
    overall_status: str  # passed / failed
    case_detail: List[CaseDetail] = Field(default_factory=list)
    coverage_rate: str = "N/A"
    error: Optional[str] = None


# ---- skill-write-flag ----
class WriteFlagResult(BaseModel):
    """写标识文件结果。"""
    flag_file_name: Optional[str] = None
    flag_content: Optional[str] = None
    operate_status: str  # success / skipped


# ---- workflow / FastAPI ----
class RunRequest(BaseModel):
    """子 Agent 调度入参。"""
    source_code: str
    lang: str = "python"
    requirement: str = ""
    module_name: Optional[str] = None
    test_target: Optional[str] = None
