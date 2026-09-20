"""LangGraph Workflow Compilation for Spec-to-Playwright Self-Healing Agent.

Constructs the state machine with cyclic self-healing loops and conditional edges.
"""

from __future__ import annotations

from typing import Any, Dict, Literal

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = Any  # type: ignore
    END = "__end__"

from src.graph.nodes import (
    analyze_and_patch_node,
    execute_test_node,
    generate_code_node,
    plan_node,
    retrieve_context_node,
)
from src.graph.state import AgentState


def should_continue(state: AgentState) -> Literal["end_success", "analyze_and_patch", "end_max_retries"]:
    """Evaluate execution results to determine state machine progression.

    Routes:
        - If passed == True -> Route to END (success).
        - If passed == False and iteration_count < max_retries -> Route to analyze_and_patch_node.
        - Otherwise -> Route to END with max retries reached.
    """
    execution = state.get("execution_output", {})
    passed = execution.get("passed", False)
    iteration = state.get("iteration_count", 0)
    max_retries = state.get("max_retries", 3)

    if passed:
        return "end_success"
    if iteration < max_retries:
        return "analyze_and_patch"
    return "end_max_retries"


def create_graph():
    """Build and compile the LangGraph state machine."""
    if StateGraph is Any or StateGraph is None:
        raise RuntimeError(
            "The 'langgraph' package is not installed. "
            "Please install it using 'pip install langgraph' or 'pip install -r requirements.txt'."
        )

    builder = StateGraph(AgentState)

    # 1. Register graph nodes
    builder.add_node("plan_node", plan_node)
    builder.add_node("retrieve_context_node", retrieve_context_node)
    builder.add_node("generate_code_node", generate_code_node)
    builder.add_node("execute_test_node", execute_test_node)
    builder.add_node("analyze_and_patch_node", analyze_and_patch_node)

    # 2. Configure sequential execution pipeline
    builder.set_entry_point("plan_node")
    builder.add_edge("plan_node", "retrieve_context_node")
    builder.add_edge("retrieve_context_node", "generate_code_node")
    builder.add_edge("generate_code_node", "execute_test_node")

    # 3. Add conditional edge for the self-healing loop
    builder.add_conditional_edges(
        "execute_test_node",
        should_continue,
        {
            "end_success": END,
            "analyze_and_patch": "analyze_and_patch_node",
            "end_max_retries": END,
        },
    )

    # 4. Circular edge: routing from patch node back to test execution
    builder.add_edge("analyze_and_patch_node", "execute_test_node")

    return builder.compile()


# Lazy-loaded compiled workflow instance
_compiled_graph = None


def get_compiled_graph():
    """Retrieve or compile the singleton LangGraph workflow."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_graph()
    return _compiled_graph

