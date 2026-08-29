"use client";

import React from "react";
import {
  Activity,
  Radio,
  Sliders,
  Wifi,
  CloudDownload,
  RefreshCw,
  Clock,
  Send,
  Layers,
  MapPin,
  AlertTriangle,
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
  activeTab?: string;
  onSelectTab?: (tab: string) => void;
  bhoonidhiStatus?: string;
  fieldActiveCount?: number;
  onOpenBroadcast?: () => void;
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
  activeTab = "overview",
  onSelectTab,
  bhoonidhiStatus = "NOT_CONFIGURED",
  fieldActiveCount = 3,
  onOpenBroadcast,
}: CommandHeaderProps) {
  const isLiveMode = dataMode.toUpperCase() === "LIVE";

  return (
    <header className="bg-slate-950 border-b border-slate-800 font-sans">
      {/* Top Header Strip */}
      <div className="px-4 py-2.5 sm:px-6 flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-850">
        {/* Left: Identification */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-slate-900 border border-slate-750 flex items-center justify-center text-slate-300 font-bold font-mono text-xs">
            NDMA
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold">
                SIH26001 • North Eastern Region Landslide Decision Support System
              </span>
              <span className="bg-slate-900 text-slate-400 border border-slate-800 text-[10px] font-mono px-1.5 py-0.2 rounded">
                prototype-v0.3
              </span>
            </div>
            <h1 className="text-base sm:text-lg font-bold text-slate-100 flex items-center gap-2">
              Disaster Intelligence Command Center
            </h1>
          </div>
        </div>

        {/* Right: Operational Controls */}
        <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
          {/* Mode Switcher */}
          <div className="flex items-center bg-slate-900 p-0.5 rounded-md border border-slate-800 text-xs">
            <button
              onClick={() => onToggleDataMode("LIVE")}
              className={`px-2.5 py-1 rounded transition font-medium flex items-center gap-1.5 ${
                isLiveMode
                  ? "bg-slate-800 text-slate-100 font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Wifi className="w-3 h-3 text-emerald-400" />
              LIVE DATA
            </button>

            <button
              onClick={() => onToggleDataMode("SIMULATION")}
              className={`px-2.5 py-1 rounded transition font-medium flex items-center gap-1.5 ${
                !isLiveMode
                  ? "bg-amber-950 text-amber-300 border border-amber-800 font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sliders className="w-3 h-3 text-amber-400" />
              SIMULATION
            </button>
          </div>

          {/* Ingest Button */}
          {isLiveMode && (
            <button
              onClick={onTriggerBatchIngest}
              disabled={isIngesting}
              className="bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-850 text-xs px-3 py-1.5 rounded-md transition flex items-center gap-1.5"
            >
              <CloudDownload className={`w-3.5 h-3.5 text-slate-400 ${isIngesting ? "animate-spin" : ""}`} />
              {isIngesting ? "Ingesting..." : "Ingest Telemetry"}
            </button>
          )}

          {/* Assessment Trigger */}
          <button
            onClick={onTriggerEngineRun}
            disabled={isRunningEngine}
            className="bg-slate-800 hover:bg-slate-750 text-slate-100 border border-slate-700 text-xs font-medium px-3 py-1.5 rounded-md transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-300 ${isRunningEngine ? "animate-spin" : ""}`} />
            {isRunningEngine ? "Assessing..." : "Run Engine"}
          </button>

          {/* Auto Refresh Select */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-2 py-1.5 rounded-md text-xs">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={autoRefreshInterval}
              onChange={(e) => onToggleAutoRefresh(Number(e.target.value))}
              className="bg-transparent text-slate-300 focus:outline-none text-xs cursor-pointer font-mono"
            >
              <option value={15} className="bg-slate-950">15s</option>
              <option value={30} className="bg-slate-950">30s</option>
              <option value={60} className="bg-slate-950">60s</option>
              <option value={0} className="bg-slate-950">Manual</option>
            </select>
          </div>
        </div>
      </div>

      {/* Understated Mission Control Status Strip (Section 41) */}
      <div className="bg-slate-900/90 px-4 py-1.5 sm:px-6 flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono border-b border-slate-800 text-slate-400">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 uppercase">ENGINE:</span>
            <span className={`font-bold ${engineOnline ? "text-emerald-400" : "text-red-400"}`}>
              {engineOnline ? "ONLINE" : "OFFLINE"}
            </span>
          </div>

          <span className="text-slate-700">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 uppercase">DATA:</span>
            <span className="text-slate-200 font-medium">HEALTHY</span>
          </div>

          <span className="text-slate-700">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 uppercase">BHOONIDHI:</span>
            <span className={`font-bold ${bhoonidhiStatus === 'AVAILABLE' ? 'text-emerald-400' : 'text-slate-400'}`}>
              {bhoonidhiStatus}
            </span>
          </div>

          <span className="text-slate-700">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 uppercase">FIELD:</span>
            <span className="text-slate-200 font-bold">{fieldActiveCount} ACTIVE</span>
          </div>

          <span className="text-slate-700">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 uppercase">BROADCAST:</span>
            <span className="text-emerald-400 font-medium">READY</span>
          </div>
        </div>

        <div className="text-slate-500 text-[10px]">
          Sync Fix: {lastUpdated || "00:00:00 UTC"}
        </div>
      </div>

      {/* Simplified Top Navigation (Section 7: Overview, Stations, Events, Field Operations, Broadcast) */}
      <div className="px-4 sm:px-6 bg-slate-950 flex items-center justify-between text-xs font-mono">
        <nav className="flex items-center gap-1">
          {[
            { id: "overview", label: "Overview", icon: Layers },
            { id: "stations", label: "Stations", icon: MapPin },
            { id: "events", label: "Events", icon: AlertTriangle },
            { id: "field", label: "Field Operations", icon: Radio, isExternal: true, href: "/field" },
            { id: "broadcast", label: "Broadcast", icon: Send, isAction: true },
          ].map((item) => {
            const isActive = activeTab === item.id;
            const Icon = item.icon;

            if (item.isExternal && item.href) {
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  target="_blank"
                  className="px-3 py-2 text-slate-400 hover:text-slate-200 hover:bg-slate-900 border-b-2 border-transparent transition flex items-center gap-1.5"
                >
                  <Icon className="w-3.5 h-3.5 text-slate-400" />
                  <span>{item.label}</span>
                </Link>
              );
            }

            if (item.isAction) {
              return (
                <button
                  key={item.id}
                  onClick={onOpenBroadcast}
                  className="px-3 py-2 text-slate-400 hover:text-slate-200 hover:bg-slate-900 border-b-2 border-transparent transition flex items-center gap-1.5"
                >
                  <Icon className="w-3.5 h-3.5 text-slate-400" />
                  <span>{item.label}</span>
                </button>
              );
            }

            return (
              <button
                key={item.id}
                onClick={() => onSelectTab && onSelectTab(item.id)}
                className={`px-3 py-2 border-b-2 font-medium transition flex items-center gap-1.5 ${
                  isActive
                    ? "border-slate-200 text-slate-100 bg-slate-900"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
