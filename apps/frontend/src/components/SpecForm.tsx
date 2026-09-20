"use client";

import React, { useState } from "react";
import { Sparkles, Globe, FileText, RefreshCw, Square } from "lucide-react";

interface SpecFormProps {
  onSubmit: (spec: string, targetUrl: string, maxRetries: number) => void;
  onAbort: () => void;
  isLoading: boolean;
}

const PRESETS = [
  {
    title: "Auth & Session Token",
    targetUrl: "https://demo.playwright.dev",
    spec: "User logs in with email 'qa@example.com' and password, verifies session auth token in cookies, and asserts redirect to dashboard heading.",
  },
  {
    title: "Todo App Interaction",
    targetUrl: "https://demo.playwright.dev/todomvc",
    spec: "Add two todo items ('Buy groceries', 'Write test specs'), mark the first item as completed, and assert remaining item count is 1.",
  },
  {
    title: "Form Validation & Error",
    targetUrl: "https://the-internet.herokuapp.com/login",
    spec: "Submit login form with invalid username and password, asserting the red validation error banner appears with 'Your username is invalid!'.",
  },
];

export function SpecForm({ onSubmit, onAbort, isLoading }: SpecFormProps) {
  const [targetUrl, setTargetUrl] = useState("https://demo.playwright.dev/todomvc");
  const [spec, setSpec] = useState(
    "Add two todo items ('Buy groceries', 'Write test specs'), mark the first item as completed, and assert remaining item count is 1."
  );
  const [maxRetries, setMaxRetries] = useState(3);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUrl.trim() || !spec.trim()) return;
    onSubmit(spec.trim(), targetUrl.trim(), maxRetries);
  };

  const handleApplyPreset = (preset: typeof PRESETS[0]) => {
    if (isLoading) return;
    setTargetUrl(preset.targetUrl);
    setSpec(preset.spec);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-5">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm tracking-wide uppercase">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span>Spec & Requirement Input</span>
        </div>
      </div>

      {/* Preset Quick-Buttons */}
      <div className="mb-5">
        <label className="text-xs font-medium text-slate-400 mb-2 block">
          Quick Templates
        </label>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.title}
              type="button"
              disabled={isLoading}
              onClick={() => handleApplyPreset(preset)}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800/70 border border-slate-700/60 text-slate-300 hover:bg-slate-700/60 hover:text-white transition-colors disabled:opacity-50"
            >
              {preset.title}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col flex-1 gap-4">
        {/* Target URL */}
        <div>
          <label className="flex items-center gap-1.5 text-xs font-medium text-slate-300 mb-1.5">
            <Globe className="w-3.5 h-3.5 text-indigo-400" />
            Target Web Application URL
          </label>
          <input
            type="url"
            required
            disabled={isLoading}
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="https://app.example.com"
            className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all disabled:opacity-50 font-mono text-xs"
          />
        </div>

        {/* PRD Spec / Scenario Description */}
        <div className="flex-1 flex flex-col min-h-[140px]">
          <label className="flex items-center gap-1.5 text-xs font-medium text-slate-300 mb-1.5">
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            PRD Specification / User Story
          </label>
          <textarea
            required
            disabled={isLoading}
            value={spec}
            onChange={(e) => setSpec(e.target.value)}
            placeholder="Describe the steps, user actions, locators, and assertions..."
            rows={5}
            className="w-full flex-1 px-3.5 py-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all disabled:opacity-50 resize-none font-sans text-xs leading-relaxed"
          />
        </div>

        {/* Configuration: Max Retries */}
        <div className="flex items-center justify-between pt-2">
          <label className="text-xs text-slate-400">
            Self-Healing Max Retries
          </label>
          <select
            disabled={isLoading}
            value={maxRetries}
            onChange={(e) => setMaxRetries(Number(e.target.value))}
            className="px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-md text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value={1}>1 retry</option>
            <option value={2}>2 retries</option>
            <option value={3}>3 retries (recommended)</option>
            <option value={5}>5 retries</option>
          </select>
        </div>

        {/* Actions */}
        <div className="pt-2">
          {isLoading ? (
            <button
              type="button"
              onClick={onAbort}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-rose-600/20 border border-rose-500/40 hover:bg-rose-600/30 text-rose-300 font-medium text-sm rounded-lg transition-all"
            >
              <Square className="w-4 h-4 fill-current" />
              <span>Cancel / Stop Generation</span>
            </button>
          ) : (
            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-lg shadow-lg shadow-indigo-600/25 transition-all hover:shadow-indigo-600/40 active:scale-[0.99]"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Generate & Verify Test</span>
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

