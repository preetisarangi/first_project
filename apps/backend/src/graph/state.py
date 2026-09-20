"""State definition for the LangGraph Spec-to-Playwright Agent."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict  # type: ignore


class ExecutionOutput(TypedDict, total=False):
    passed: bool
    stdout: str
    stderr: str
    error_type: str  # 'locator_timeout' | 'assertion_failure' | 'syntax_error' | 'environment_error' | 'none'
    error_message: Optional[str]
    duration_ms: Optional[float]


class AgentState(TypedDict):
    """The central state of the Spec-to-Playwright self-healing agent."""
    spec: str
    target_url: str
    retrieved_context: List[str]
    test_plan: str
    generated_code: str
    execution_output: ExecutionOutput
    iteration_count: int
    max_retries: int
    status: str
    diff: Optional[str]
    error_diagnosis: Optional[str]
