"use client";

import React, { useState } from "react";
import {
  Code2,
  Terminal,
  GitCompare,
  Copy,
  Check,
  Download,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { ExecutionTelemetry } from "../lib/types";

interface CodeViewerProps {
  code: string;
  execution: ExecutionTelemetry | null;
  diff: string | null;
  isStreaming: boolean;
  status: string;
  iterations: number;
}

export function CodeViewer({
  code,
  execution,
  diff,
  isStreaming,
  status,
  iterations,
}: CodeViewerProps) {
  const [activeTab, setActiveTab] = useState<"code" | "logs" | "diff">("code");
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!code) return;
    const blob = new Blob([code], { type: "text/typescript" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "generated.spec.ts";
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderDiffLines = (diffContent: string) => {
    return diffContent.split("\n").map((line, i) => {
      let lineStyle = "text-slate-300";
      let bgStyle = "bg-transparent";

      if (line.startsWith("+") && !line.startsWith("+++")) {
        lineStyle = "text-emerald-400";
        bgStyle = "bg-emerald-950/30";
      } else if (line.startsWith("-") && !line.startsWith("---")) {
        lineStyle = "text-rose-400";
        bgStyle = "bg-rose-950/30";
      } else if (line.startsWith("@@")) {
        lineStyle = "text-indigo-400 font-bold";
        bgStyle = "bg-indigo-950/20";
      }

      return (
        <div key={i} className={`flex px-3 py-0.5 font-mono text-xs ${lineStyle} ${bgStyle}`}>
          <span className="w-8 select-none opacity-40 shrink-0 text-right pr-3">{i + 1}</span>
          <span className="whitespace-pre flex-1">{line}</span>
        </div>
      );
    });
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-xl shadow-xl backdrop-blur-sm overflow-hidden">
      {/* Header & Tabs */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 bg-slate-950/70 px-4 py-2.5 gap-2">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab("code")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "code"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Generated Spec (.ts)</span>
            {isStreaming && (
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-1" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("logs")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "logs"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Execution Logs</span>
            {execution && (
              <span
                className={`w-2 h-2 rounded-full ml-1 ${
                  execution.passed ? "bg-emerald-400" : "bg-rose-400"
                }`}
              />
            )}
          </button>

          <button
            onClick={() => setActiveTab("diff")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "diff"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>Patch Diff</span>
            {diff && (
              <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 ml-1">
                Active
              </span>
            )}
          </button>
        </div>

        {/* Action Buttons & Status Badge */}
        <div className="flex items-center gap-1.5">
          {status !== "idle" && !execution && (
            <div className="flex items-center gap-1 px-2 py-1 rounded text-xs font-mono bg-indigo-950/40 text-indigo-300 border border-indigo-800/50 uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
              <span>{status}</span>
            </div>
          )}

          {execution && (
            <div
              className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-mono border ${
                execution.passed
                  ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/50"
                  : "bg-rose-950/40 text-rose-400 border-rose-800/50"
              }`}
            >
              {execution.passed ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : (
                <AlertTriangle className="w-3.5 h-3.5" />
              )}
              <span>{execution.passed ? "PASSED" : "FAILED"}</span>
              {execution.duration_ms && (
                <span className="text-slate-500 ml-1">
                  ({(execution.duration_ms / 1000).toFixed(1)}s)
                </span>
              )}
            </div>
          )}

          <button
            onClick={handleCopy}
            disabled={!code}
            title="Copy to clipboard"
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition-colors disabled:opacity-30"
          >
            {copied ? (
              <Check className="w-4 h-4 text-emerald-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>

          <button
            onClick={handleDownload}
            disabled={!code}
            title="Download spec file"
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition-colors disabled:opacity-30"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content Viewer */}
      <div className="flex-1 overflow-auto bg-slate-950/90 p-4 font-mono text-xs leading-relaxed min-h-[400px]">
        {/* Tab 1: Generated Spec Code */}
        {activeTab === "code" && (
          <div>
            {code ? (
              <pre className="text-slate-200 whitespace-pre-wrap select-text">
                {code}
              </pre>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-2 py-20 font-sans">
                <Code2 className="w-8 h-8 opacity-40" />
                <p>Waiting for generation to start...</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Execution Logs */}
        {activeTab === "logs" && (
          <div className="space-y-3">
            {execution ? (
              <div className="space-y-3">
                {execution.error_message && (
                  <div className="p-3 bg-rose-950/30 border border-rose-900/50 rounded-lg text-rose-300">
                    <p className="font-semibold text-xs">Failure Classification: [{execution.error_type}]</p>
                    <p className="text-[11px] mt-1 font-sans">{execution.error_message}</p>
                  </div>
                )}
                {execution.stdout && (
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block mb-1">
                      Stdout
                    </span>
                    <pre className="text-slate-300 whitespace-pre-wrap bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                      {execution.stdout}
                    </pre>
                  </div>
                )}
                {execution.stderr && (
                  <div>
                    <span className="text-rose-400 text-[10px] uppercase font-bold block mb-1">
                      Stderr Trace
                    </span>
                    <pre className="text-rose-300 whitespace-pre-wrap bg-rose-950/20 p-3 rounded-lg border border-rose-900/40">
                      {execution.stderr}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-2 py-20 font-sans">
                <Terminal className="w-8 h-8 opacity-40" />
                <p>No execution logs yet. Sandbox runs after code synthesis.</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Patch Diff */}
        {activeTab === "diff" && (
          <div>
            {diff ? (
              <div className="rounded-lg border border-slate-800 overflow-hidden">
                <div className="bg-slate-900/80 px-3 py-1.5 border-b border-slate-800 text-[11px] text-slate-400 font-mono">
                  Self-Healing Diff (Attempt #{iterations})
                </div>
                {renderDiffLines(diff)}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-2 py-20 font-sans">
                <GitCompare className="w-8 h-8 opacity-40" />
                <p>No patches required yet. If tests fail, self-healing diff will appear here.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

