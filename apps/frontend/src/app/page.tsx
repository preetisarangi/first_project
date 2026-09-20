"use client";

import React, { useRef, useState } from "react";
import { Cpu } from "lucide-react";
import { SpecForm } from "../components/SpecForm";
import { GraphTimeline } from "../components/GraphTimeline";
import { CodeViewer } from "../components/CodeViewer";
import { streamTestGeneration } from "../lib/sse-parser";
import { ExecutionTelemetry, StepId, TimelineStep } from "../lib/types";

const INITIAL_STEPS: TimelineStep[] = [
  {
    id: "plan",
    label: "Planning Test Suite",
    description: "Gemini Flash parses PRD into action steps",
    status: "idle",
  },
  {
    id: "rag",
    label: "Searching Knowledge Base",
    description: "Supabase pgvector retrieves Playwright patterns",
    status: "idle",
  },
  {
    id: "generate",
    label: "Generating Playwright Spec",
    description: "Synthesizing TypeScript test code",
    status: "idle",
  },
  {
    id: "execute",
    label: "Executing Sandbox Test",
    description: "Headless Playwright runner validates assertions",
    status: "idle",
  },
  {
    id: "patch",
    label: "Self-Healing & Patching",
    description: "Diagnosing failure & refactoring locators",
    status: "idle",
  },
  {
    id: "complete",
    label: "Completed / Ready",
    description: "Verified spec and telemetry report ready",
    status: "idle",
  },
];

export default function Dashboard() {
  const [steps, setSteps] = useState<TimelineStep[]>(INITIAL_STEPS);
  const [activeStep, setActiveStep] = useState<StepId>("plan");
  const [isLoading, setIsLoading] = useState(false);
  const [generatedCode, setGeneratedCode] = useState("");
  const [execution, setExecution] = useState<ExecutionTelemetry | null>(null);
  const [diff, setDiff] = useState<string | null>(null);
  const [iterationCount, setIterationCount] = useState(0);
  const [maxRetries, setMaxRetries] = useState(3);
  const [overallStatus, setOverallStatus] = useState<string>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const updateStepStatus = (
    stepId: StepId,
    status: "idle" | "running" | "completed" | "failed",
    detail?: string
  ) => {
    setSteps((prev) =>
      prev.map((s) => (s.id === stepId ? { ...s, status, detail: detail ?? s.detail } : s))
    );
  };

  const handleStartGeneration = async (
    spec: string,
    targetUrl: string,
    selectedMaxRetries: number
  ) => {
    // Reset state
    setIsLoading(true);
    setGeneratedCode("");
    setExecution(null);
    setDiff(null);
    setIterationCount(0);
    setMaxRetries(selectedMaxRetries);
    setOverallStatus("generating");
    setErrorMessage(null);
    setSteps(INITIAL_STEPS.map((s) => ({ ...s, status: "idle", detail: undefined })));
    setActiveStep("plan");

    abortControllerRef.current = new AbortController();

    await streamTestGeneration(
      spec,
      targetUrl,
      selectedMaxRetries,
      {
        onStepChange: (node: string, label: string, data?: string) => {
          if (node === "plan_node") {
            setActiveStep("plan");
            updateStepStatus("plan", "running", data);
          } else if (node === "retrieve_context_node") {
            updateStepStatus("plan", "completed");
            setActiveStep("rag");
            updateStepStatus("rag", "running", data);
          } else if (node === "generate_code_node") {
            updateStepStatus("rag", "completed");
            setActiveStep("generate");
            updateStepStatus("generate", "running", data);
          } else if (node === "execute_test_node") {
            updateStepStatus("generate", "completed");
            setActiveStep("execute");
            updateStepStatus("execute", "running", data);
          } else if (node === "analyze_and_patch_node") {
            updateStepStatus("execute", "failed");
            setActiveStep("patch");
            updateStepStatus("patch", "running", data);
          }
        },

        onCodeToken: (token: string) => {
          setGeneratedCode((prev) => prev + token);
        },

        onPlanReady: (plan: string) => {
          updateStepStatus("plan", "completed", "Test plan finalized.");
        },

        onCodeReady: (code: string) => {
          setGeneratedCode(code);
          updateStepStatus("generate", "completed", "Spec code generated.");
        },

        onExecutionResult: (telemetry: ExecutionTelemetry) => {
          setExecution(telemetry);
          if (telemetry.passed) {
            updateStepStatus("execute", "completed", "Sandbox tests passed successfully!");
          } else {
            updateStepStatus(
              "execute",
              "failed",
              `Failed: [${telemetry.error_type}] ${telemetry.error_message || ""}`
            );
          }
        },

        onPatchDiff: (diffContent: string, diagnosis?: string, iteration?: number) => {
          setDiff(diffContent);
          if (iteration !== undefined) setIterationCount(iteration);
          updateStepStatus("patch", "completed", diagnosis || `Patch #${iteration} applied.`);
        },

        onComplete: (result) => {
          setIsLoading(false);
          setOverallStatus(result.passed ? "success" : "failed");
          if (result.generated_code) setGeneratedCode(result.generated_code);
          if (result.diff) setDiff(result.diff);
          if (result.iterations !== undefined) setIterationCount(result.iterations);
          if (result.execution_output) setExecution(result.execution_output);

          setActiveStep("complete");
          updateStepStatus(
            "complete",
            result.passed ? "completed" : "failed",
            result.passed
              ? "All Playwright assertions verified."
              : `Max retries (${selectedMaxRetries}) reached.`
          );
        },

        onError: (err: string) => {
          setIsLoading(false);
          setErrorMessage(err);
          setOverallStatus("failed");
          updateStepStatus(activeStep, "failed", err);
        },
      },
      abortControllerRef.current.signal
    );

    setIsLoading(false);
  };

  const handleAbort = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setOverallStatus("aborted");
    updateStepStatus(activeStep, "idle", "Aborted by user.");
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white">
                  Spec-to-Playwright AI Agent
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  LangGraph + pgvector
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Autonomous Spec-to-Code Generator with Self-Healing Loop
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-mono text-slate-300">FastAPI SSE Ready</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard: 3 Columns */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Spec Form (4 cols) */}
        <div className="lg:col-span-4 h-full">
          <SpecForm
            onSubmit={handleStartGeneration}
            onAbort={handleAbort}
            isLoading={isLoading}
          />
        </div>

        {/* Center Column: Workflow Timeline (3 cols) */}
        <div className="lg:col-span-3 h-full">
          <GraphTimeline
            activeStep={activeStep}
            steps={steps}
            iterationCount={iterationCount}
            maxRetries={maxRetries}
          />
        </div>

        {/* Right Column: Code & Execution Trace (5 cols) */}
        <div className="lg:col-span-5 h-full flex flex-col gap-3">
          <div className="flex-1">
            <CodeViewer
              code={generatedCode}
              execution={execution}
              diff={diff}
              isStreaming={isLoading}
              status={overallStatus}
              iterations={iterationCount}
            />
          </div>

          {errorMessage && (
            <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl text-rose-300 text-xs">
              <strong>Generation Error:</strong> {errorMessage}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
