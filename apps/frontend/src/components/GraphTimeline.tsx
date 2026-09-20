"use client";

import React from "react";
import {
  FileCode2,
  Database,
  Code,
  PlayCircle,
  Wrench,
  CheckCircle,
  Clock,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { StepId, StepStatus, TimelineStep } from "../lib/types";

interface GraphTimelineProps {
  activeStep: StepId;
  steps: TimelineStep[];
  iterationCount: number;
  maxRetries: number;
}

const STEP_ICONS: Record<StepId, React.ComponentType<{ className?: string }>> = {
  plan: FileCode2,
  rag: Database,
  generate: Code,
  execute: PlayCircle,
  patch: Wrench,
  complete: CheckCircle,
};

export function GraphTimeline({
  activeStep,
  steps,
  iterationCount,
  maxRetries,
}: GraphTimelineProps) {
  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-5">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm tracking-wide uppercase">
          <Clock className="w-4 h-4 text-indigo-400" />
          <span>Agent Workflow Timeline</span>
        </div>
        {iterationCount > 0 && (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Self-Healing Loop #{iterationCount}/{maxRetries}
          </span>
        )}
      </div>

      <div className="relative flex-1 flex flex-col justify-between space-y-4">
        {/* Connecting vertical rail */}
        <div className="absolute left-[19px] top-4 bottom-4 w-0.5 bg-slate-800 -z-0" />

        {steps.map((step, idx) => {
          const Icon = STEP_ICONS[step.id] || Clock;
          const isCurrent = activeStep === step.id && step.status === "running";
          const isCompleted = step.status === "completed";
          const isFailed = step.status === "failed";

          return (
            <div
              key={step.id}
              className={`relative z-10 flex items-start gap-3 p-3 rounded-xl transition-all ${
                isCurrent
                  ? "bg-indigo-950/40 border border-indigo-500/40 shadow-md shadow-indigo-900/20"
                  : isCompleted
                  ? "bg-slate-900/40 border border-slate-800/80"
                  : "bg-slate-950/30 border border-transparent opacity-60"
              }`}
            >
              {/* Status Circle Badge */}
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border transition-all ${
                  isCurrent
                    ? "bg-indigo-600 text-white border-indigo-400 animate-pulse"
                    : isCompleted
                    ? "bg-emerald-950 text-emerald-400 border-emerald-600/50"
                    : isFailed
                    ? "bg-rose-950 text-rose-400 border-rose-600/50"
                    : "bg-slate-900 text-slate-500 border-slate-800"
                }`}
              >
                {isCurrent ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : isCompleted ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                ) : isFailed ? (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>

              {/* Step Information */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <h4
                    className={`text-xs font-semibold ${
                      isCurrent
                        ? "text-indigo-300"
                        : isCompleted
                        ? "text-slate-200"
                        : "text-slate-400"
                    }`}
                  >
                    {idx + 1}. {step.label}
                  </h4>
                  {step.status === "completed" && (
                    <span className="text-[10px] text-emerald-400 font-mono">Done</span>
                  )}
                  {isCurrent && (
                    <span className="text-[10px] text-indigo-400 font-mono animate-pulse">
                      Running
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                  {step.description}
                </p>
                {step.detail && (
                  <p className="text-[10px] font-mono text-indigo-300/80 mt-1 bg-slate-950/60 px-2 py-1 rounded border border-slate-800/60 truncate">
                    {step.detail}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

