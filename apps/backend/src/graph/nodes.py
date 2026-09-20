"""LangGraph Node Implementations for the Self-Healing Test Generation Loop."""

from __future__ import annotations

import difflib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import settings
from src.graph.state import AgentState, ExecutionOutput
from src.rag.retriever import retrieve_relevant_context
from src.sandbox.runner import run_playwright_test

# ---------------------------------------------------------------------------
# LLM Initialization Factory (Gemini Flash with OpenRouter fallback)
# ---------------------------------------------------------------------------
def get_llm():
    """Retrieve primary ChatGoogleGenerativeAI or fallback ChatOpenAI."""
    if settings.GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            # Use gemini-1.5-flash or gemini-2.5-flash
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1,
            )
        except Exception as err:
            print(f"[!] Warning: Failed to init ChatGoogleGenerativeAI: {err}")

    if settings.OPENROUTER_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
                model="meta-llama/llama-3.3-70b-instruct:free",
                temperature=0.1,
            )
        except Exception as err:
            print(f"[!] Warning: Failed to init OpenRouter ChatOpenAI: {err}")

    # Fallback / mock when no API keys are present in offline dev
    return None


def _clean_code_block(raw_text: str) -> str:
    """Extract raw code from markdown fences if present."""
    pattern = r"```(?:typescript|ts)?\s*([\s\S]*?)```"
    match = re.search(pattern, raw_text)
    if match:
        return match.group(1).strip()
    return raw_text.strip()


# ---------------------------------------------------------------------------
# Node 1: Plan Node
# ---------------------------------------------------------------------------
def plan_node(state: AgentState) -> Dict[str, Any]:
    """Generates a structured, step-by-step test plan from the user spec and target URL."""
    spec = state.get("spec", "")
    target_url = state.get("target_url", "")

    llm = get_llm()
    if llm is None:
        # Structured fallback plan when running without API keys
        test_plan = (
            f"1. Navigate to target URL: '{target_url}'\n"
            f"2. Wait for page load state 'domcontentloaded'\n"
            f"3. Identify and interact with elements based on spec: '{spec}'\n"
            f"4. Assert URL and visible success state"
        )
    else:
        prompt = (
            "You are a Lead QA Automation Engineer. Create a concise, numbered step-by-step "
            "Playwright test plan for the following requirement and target URL.\n\n"
            f"Target URL: {target_url}\n"
            f"Requirement Spec: {spec}\n\n"
            "Format your response as a numbered list specifying:\n"
            "1. Page navigation & load readiness checks\n"
            "2. Locators & user action sequence\n"
            "3. Assertions & verification checkpoints"
        )
        response = llm.invoke(prompt)
        test_plan = response.content if hasattr(response, "content") else str(response)

    return {
        "test_plan": test_plan,
        "status": "plan_generated",
    }


# ---------------------------------------------------------------------------
# Node 2: Retrieve Context Node
# ---------------------------------------------------------------------------
def retrieve_context_node(state: AgentState) -> Dict[str, Any]:
    """Queries Supabase pgvector for top relevant reference snippets with fallback."""
    spec = state.get("spec", "")
    retrieved: List[str] = []

    try:
        retrieved = retrieve_relevant_context(query=spec, top_k=3)
    except Exception as exc:
        print(f"[*] RAG search notice: {exc}. Reading local test fixtures as baseline...")
        # Local fallback: read reference files from packages/test-fixtures
        fixtures_dir = Path(__file__).resolve().parents[4] / "packages" / "test-fixtures"
        if fixtures_dir.exists():
            for sample_file in fixtures_dir.rglob("*.ts"):
                try:
                    code = sample_file.read_text(encoding="utf-8")
                    retrieved.append(f"// Reference: {sample_file.name}\n{code[:800]}")
                    if len(retrieved) >= 3:
                        break
                except Exception:
                    pass

    return {
        "retrieved_context": retrieved,
        "status": "context_retrieved",
    }


# ---------------------------------------------------------------------------
# Node 3: Generate Code Node
# ---------------------------------------------------------------------------
def generate_code_node(state: AgentState) -> Dict[str, Any]:
    """Generates complete, executable Playwright TypeScript code."""
    spec = state.get("spec", "")
    target_url = state.get("target_url", "")
    test_plan = state.get("test_plan", "")
    context_blocks = "\n\n".join(state.get("retrieved_context", []))

    llm = get_llm()
    if llm is None:
        # Deterministic baseline template when running offline
        code = f"""import {{ test, expect }} from '@playwright/test';

test.describe('Automated Spec Verification', () => {{
  test('verify spec scenario: {spec[:50]}', async ({{ page }}) => {{
    await page.goto('{target_url}');
    await page.waitForLoadState('domcontentloaded');

    // Verification checkpoint
    await expect(page).toHaveURL(/{target_url.replace("https://", "").replace("http://", "")}/);
  }});
}});
"""
    else:
        system_instruction = (
            "You are a Principal AI Test Automation Engineer writing modern Playwright TypeScript tests.\n"
            "Rules:\n"
            "1. Output ONLY runnable TypeScript code inside a single ```typescript block.\n"
            "2. Always import { test, expect } from '@playwright/test'.\n"
            "3. Use resilient locators: page.getByRole, page.getByTestId, page.getByLabel, or page.locator.\n"
            "4. Follow the provided step-by-step test plan and leverage patterns from the reference context.\n"
            "5. Never use arbitrary page.waitForTimeout(); use web-first assertions like await expect(locator).toBeVisible()."
        )
        user_prompt = (
            f"Target URL: {target_url}\n\n"
            f"Requirement Spec: {spec}\n\n"
            f"Test Plan:\n{test_plan}\n\n"
            f"Reference Code Patterns:\n{context_blocks}\n\n"
            "Generate the complete Playwright spec file."
        )
        response = llm.invoke(f"{system_instruction}\n\n{user_prompt}")
        raw_text = response.content if hasattr(response, "content") else str(response)
        code = _clean_code_block(raw_text)

    return {
        "generated_code": code,
        "status": "code_generated",
    }


# ---------------------------------------------------------------------------
# Node 4: Execute Test Node
# ---------------------------------------------------------------------------
def execute_test_node(state: AgentState) -> Dict[str, Any]:
    """Runs the generated code inside the headless Playwright sandbox."""
    code = state.get("generated_code", "")
    output: Dict[str, Any] = run_playwright_test(code)

    return {
        "execution_output": output,
        "status": "test_executed",
    }


# ---------------------------------------------------------------------------
# Node 5: Analyze and Patch Node
# ---------------------------------------------------------------------------
def analyze_and_patch_node(state: AgentState) -> Dict[str, Any]:
    """Diagnoses failure cause, rewrites broken code, and generates diff."""
    current_code = state.get("generated_code", "")
    execution = state.get("execution_output", {})
    iteration = state.get("iteration_count", 0) + 1
    target_url = state.get("target_url", "")
    error_type = execution.get("error_type", "unknown")
    error_message = execution.get("error_message", "")
    stderr = execution.get("stderr", "")

    llm = get_llm()
    diagnosis = f"Categorized as [{error_type}]: {error_message or 'Failure in execution.'}"

    if llm is None:
        # Fallback patch adjustment
        patched_code = current_code + f"\n// Self-healing attempt #{iteration}: handled {error_type}"
    else:
        prompt = (
            "You are an Autonomous Self-Healing Test Agent.\n"
            "A Playwright test failed during execution. Diagnose the root cause and provide a fixed version.\n\n"
            f"Target URL: {target_url}\n"
            f"Failure Type: {error_type}\n"
            f"Error Details: {error_message}\n"
            f"Stderr / Trace:\n{stderr[-1200:]}\n\n"
            f"Current Broken Code:\n```typescript\n{current_code}\n```\n\n"
            "Instructions:\n"
            "1. If locator timed out, substitute with a more flexible or resilient locator (getByRole, getByText, or broader CSS).\n"
            "2. If assertion failed, adjust timeout or refine expected attribute/state.\n"
            "3. Output ONLY the fixed TypeScript code inside ```typescript ... ```."
        )
        response = llm.invoke(prompt)
        raw_text = response.content if hasattr(response, "content") else str(response)
        patched_code = _clean_code_block(raw_text)

    # Compute unified diff between old and new code
    old_lines = current_code.splitlines(keepends=True)
    new_lines = patched_code.splitlines(keepends=True)
    diff_generator = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"iteration_{iteration - 1}.spec.ts",
        tofile=f"iteration_{iteration}.spec.ts",
    )
    diff_text = "".join(diff_generator)

    return {
        "generated_code": patched_code,
        "iteration_count": iteration,
        "diff": diff_text,
        "error_diagnosis": diagnosis,
        "status": f"patched_iteration_{iteration}",
    }

