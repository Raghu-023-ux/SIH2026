"use client";

import React from "react";
import {
  Activity,
  AlertOctagon,
  CheckCircle2,
  RefreshCw,
  Sliders,
  Shield,
  Clock,
  Radio,
  CloudLightning,
  CloudDownload,
  Wifi,
  Users,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";

interface CommandHeaderProps {
  engineOnline: boolean;
  lastUpdated: string | null;
  dataSourcesStatus: string;
  dataMode: string;
  onToggleDataMode: (mode: string) => Promise<void>;
  onTriggerEngineRun: () => void;
  onTriggerBatchIngest: () => void;
  isRunningEngine: boolean;
  isIngesting: boolean;
  autoRefreshInterval: number;
  onToggleAutoRefresh: (interval: number) => void;
}

export default function CommandHeader({
  engineOnline,
  lastUpdated,
  dataSourcesStatus,
  dataMode,
  onToggleDataMode,
  onTriggerEngineRun,
  onTriggerBatchIngest,
  isRunningEngine,
  isIngesting,
  autoRefreshInterval,
  onToggleAutoRefresh,
}: CommandHeaderProps) {
  const isLiveMode = dataMode.toUpperCase() === "LIVE";

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 sm:px-6 shadow-lg">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Brand / Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shadow-inner">
            <CloudLightning className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono tracking-widest text-indigo-400 uppercase font-bold">
                SIH26001 • Landslide Early Warning
              </span>
              <span className="bg-indigo-950 text-indigo-300 border border-indigo-800 text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold">
                NER DSS v0.3
              </span>
            </div>
            <h1 className="text-lg sm:text-xl font-black tracking-tight text-slate-100 flex items-center gap-2">
              Disaster Intelligence Command Center
            </h1>
          </div>
        </div>

        {/* Center: Multi-Layer Portal Links */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-mono">
          <span className="px-2 py-1 bg-slate-900 text-indigo-300 font-bold rounded">
            HQ Command
          </span>

          <Link
            href="/field"
            target="_blank"
            className="px-2 py-1 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded transition flex items-center gap-1"
          >
            <Radio className="w-3 h-3 text-orange-400" />
            <span>Field Units</span>
          </Link>

          <Link
            href="/public"
            target="_blank"
            className="px-2 py-1 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded transition flex items-center gap-1"
          >
            <Shield className="w-3 h-3 text-emerald-400" />
            <span>Public Safety</span>
          </Link>

          <Link
            href="/analytics"
            target="_blank"
            className="px-2 py-1 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded transition flex items-center gap-1"
          >
            <Sliders className="w-3 h-3 text-purple-400" />
            <span>Model Studio</span>
          </Link>
        </div>

        {/* Right: Operational Controls & Mode Selector */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Live vs Simulation Mode Switcher */}
          <div className="flex items-center bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-xs font-mono">
            <button
              onClick={() => onToggleDataMode("LIVE")}
              className={`px-2.5 py-1 rounded-md transition font-bold flex items-center gap-1.5 ${
                isLiveMode
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Wifi className="w-3 h-3" />
              LIVE DATA
            </button>

            <button
              onClick={() => onToggleDataMode("SIMULATION")}
              className={`px-2.5 py-1 rounded-md transition font-bold flex items-center gap-1.5 ${
                !isLiveMode
                  ? "bg-amber-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sliders className="w-3 h-3" />
              SIMULATION
            </button>
          </div>

          {/* Engine Status Indicator */}
          <div className="flex items-center gap-2 bg-slate-950/90 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono">
            <span
              className={`w-2 h-2 rounded-full ${
                engineOnline ? "bg-emerald-400 animate-pulse shadow-emerald-500/50 shadow-sm" : "bg-red-500"
              }`}
            />
            <span className="text-slate-300 font-medium">
              {engineOnline ? "ENGINE ONLINE" : "OFFLINE"}
            </span>
          </div>

          {/* Ingest Live Feeds Button */}
          {isLiveMode && (
            <button
              onClick={onTriggerBatchIngest}
              disabled={isIngesting}
              className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 shadow-sm font-mono"
            >
              <CloudDownload className={`w-3.5 h-3.5 ${isIngesting ? "animate-spin" : ""}`} />
              {isIngesting ? "Ingesting..." : "Ingest Feeds"}
            </button>
          )}

          {/* Assessment Trigger Button */}
          <button
            onClick={onTriggerEngineRun}
            disabled={isRunningEngine}
            className="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 shadow-md shadow-indigo-950 font-mono"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRunningEngine ? "animate-spin" : ""}`} />
            {isRunningEngine ? "Assessing..." : "Run Assessment"}
          </button>

          {/* Auto Refresh Select */}
          <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 px-2 py-1.5 rounded-lg text-xs font-mono">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={autoRefreshInterval}
              onChange={(e) => onToggleAutoRefresh(Number(e.target.value))}
              className="bg-transparent text-slate-300 focus:outline-none text-xs cursor-pointer font-mono"
            >
              <option value={15} className="bg-slate-900">15s</option>
              <option value={30} className="bg-slate-900">30s</option>
              <option value={60} className="bg-slate-900">60s</option>
              <option value={0} className="bg-slate-900">Paused</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
}
