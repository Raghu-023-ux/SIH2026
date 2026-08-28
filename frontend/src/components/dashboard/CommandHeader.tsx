"use client";

import React from "react";
import { Activity, RefreshCw, ShieldAlert, Radio, UserCheck, Clock, CheckCircle2 } from "lucide-react";

interface CommandHeaderProps {
  engineOnline: boolean;
  lastUpdated: string | null;
  dataSourcesStatus: string;
  onTriggerEngineRun: () => void;
  isRunningEngine: boolean;
  autoRefreshInterval: number; // in seconds, 0 = paused
  onToggleAutoRefresh: (sec: number) => void;
}

export default function CommandHeader({
  engineOnline,
  lastUpdated,
  dataSourcesStatus,
  onTriggerEngineRun,
  isRunningEngine,
  autoRefreshInterval,
  onToggleAutoRefresh,
}: CommandHeaderProps) {
  return (
    <header className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-md">
      {/* Left: Branding & Sub-label */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-600 border border-indigo-400/40 flex items-center justify-center shadow-md shadow-indigo-950 flex-shrink-0">
          <ShieldAlert className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-slate-100 tracking-tight">
              Disaster Intelligence
            </span>
            <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800">
              COMMAND CENTER
            </span>
          </div>
          <div className="text-[11px] text-slate-400 font-medium">
            SIH26001 | North Eastern Region Landslide Risk Monitoring
          </div>
        </div>
      </div>

      {/* Center/Right: Operational Indicators & Officer Controls */}
      <div className="flex flex-wrap items-center gap-2.5 text-xs">
        {/* Engine Status Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950 border border-slate-800 font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              engineOnline ? "bg-emerald-400 animate-ping" : "bg-red-500"
            }`}
          />
          <span className={engineOnline ? "text-emerald-300 font-bold" : "text-red-400 font-bold"}>
            {engineOnline ? "ENGINE ONLINE" : "ENGINE OFFLINE"}
          </span>
        </div>

        {/* Data Source Indicator */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950/70 border border-slate-800 text-slate-300 font-mono text-[11px]">
          <Radio className="w-3 h-3 text-amber-400 animate-pulse" />
          <span className="text-slate-400">TELEMETRY:</span>
          <span className="text-slate-200 truncate max-w-[160px]">{dataSourcesStatus}</span>
        </div>

        {/* Last Updated */}
        <div className="flex items-center gap-1 text-slate-400 px-2 py-1 bg-slate-950/40 rounded border border-slate-800/60 font-mono text-[11px]">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>{lastUpdated ? `Sync: ${lastUpdated}` : "Syncing..."}</span>
        </div>

        {/* Auto Refresh Selector */}
        <div className="flex items-center bg-slate-950 rounded border border-slate-800 p-0.5 text-[11px]">
          <button
            onClick={() => onToggleAutoRefresh(autoRefreshInterval === 30 ? 0 : 30)}
            className={`px-2 py-0.5 rounded transition font-mono ${
              autoRefreshInterval > 0
                ? "bg-indigo-950 text-indigo-300 font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Toggle 30s auto-refresh polling"
          >
            {autoRefreshInterval > 0 ? `${autoRefreshInterval}s Auto` : "Paused"}
          </button>
        </div>

        {/* Run Assessment Button */}
        <button
          onClick={onTriggerEngineRun}
          disabled={isRunningEngine}
          className="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white font-medium px-3 py-1.5 rounded-md transition flex items-center gap-1.5 shadow-sm shadow-indigo-950"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRunningEngine ? "animate-spin" : ""}`} />
          <span>{isRunningEngine ? "Evaluating..." : "Run Assessment"}</span>
        </button>

        {/* Officer Profile Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-slate-200">
          <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-medium text-[11px]">Monitoring Desk</span>
        </div>
      </div>
    </header>
  );
}
