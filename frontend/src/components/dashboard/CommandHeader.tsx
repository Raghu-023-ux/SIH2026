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
    <header className="bg-black border-b border-zinc-800 font-sans text-white">
      {/* Top Header Strip */}
      <div className="px-4 py-3 sm:px-6 flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-zinc-800">
        {/* Left: Identification */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-white text-black flex items-center justify-center font-black font-mono text-xs shadow-sm">
            NDMA
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono tracking-widest text-zinc-400 uppercase font-bold">
                SIH26001 • North Eastern Region Landslide Decision Support System
              </span>
              <span className="bg-zinc-900 text-zinc-300 border border-zinc-700 text-[10px] font-mono px-1.5 py-0.2 rounded font-bold">
                prototype-v0.3
              </span>
            </div>
            <h1 className="text-base sm:text-lg font-black tracking-tight text-white flex items-center gap-2">
              Disaster Intelligence Command Center
            </h1>
          </div>
        </div>

        {/* Right: Operational Controls */}
        <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
          {/* Mode Switcher */}
          <div className="flex items-center bg-zinc-900 p-0.5 rounded border border-zinc-800 text-xs">
            <button
              onClick={() => onToggleDataMode("LIVE")}
              className={`px-3 py-1 rounded transition font-bold flex items-center gap-1.5 ${
                isLiveMode
                  ? "bg-white text-black shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Wifi className="w-3 h-3 text-emerald-600" />
              LIVE
            </button>

            <button
              onClick={() => onToggleDataMode("SIMULATION")}
              className={`px-3 py-1 rounded transition font-bold flex items-center gap-1.5 ${
                !isLiveMode
                  ? "bg-amber-500 text-black shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Sliders className="w-3 h-3" />
              SIMULATION
            </button>
          </div>

          {/* Ingest Button */}
          {isLiveMode && (
            <button
              onClick={onTriggerBatchIngest}
              disabled={isIngesting}
              className="bg-zinc-900 hover:bg-zinc-800 text-white border border-zinc-700 text-xs font-bold px-3 py-1.5 rounded transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <CloudDownload className={`w-3.5 h-3.5 ${isIngesting ? "animate-spin" : ""}`} />
              {isIngesting ? "Ingesting..." : "Ingest Telemetry"}
            </button>
          )}

          {/* Assessment Trigger */}
          <button
            onClick={onTriggerEngineRun}
            disabled={isRunningEngine}
            className="bg-white hover:bg-zinc-200 text-black text-xs font-black px-3.5 py-1.5 rounded transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRunningEngine ? "animate-spin" : ""}`} />
            {isRunningEngine ? "Assessing..." : "Run Engine"}
          </button>

          {/* Auto Refresh Select */}
          <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 px-2 py-1.5 rounded text-xs">
            <Clock className="w-3.5 h-3.5 text-zinc-400" />
            <select
              value={autoRefreshInterval}
              onChange={(e) => onToggleAutoRefresh(Number(e.target.value))}
              className="bg-transparent text-zinc-200 focus:outline-none text-xs cursor-pointer font-mono font-bold"
            >
              <option value={15} className="bg-zinc-950 text-white">15s</option>
              <option value={30} className="bg-zinc-950 text-white">30s</option>
              <option value={60} className="bg-zinc-950 text-white">60s</option>
              <option value={0} className="bg-zinc-950 text-white">Manual</option>
            </select>
          </div>
        </div>
      </div>

      {/* Understated Mission Control Status Strip */}
      <div className="bg-zinc-950 px-4 py-1.5 sm:px-6 flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono border-b border-zinc-850 text-zinc-400">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="text-zinc-500 uppercase font-semibold">ENGINE:</span>
            <span className={`font-black ${engineOnline ? "text-emerald-400" : "text-red-400"}`}>
              {engineOnline ? "ONLINE" : "OFFLINE"}
            </span>
          </div>

          <span className="text-zinc-700">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-zinc-500 uppercase font-semibold">DATA:</span>
            <span className="text-zinc-200 font-bold">HEALTHY</span>
          </div>

          <span className="text-zinc-700">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-zinc-500 uppercase font-semibold">BHOONIDHI:</span>
            <span className={`font-bold ${bhoonidhiStatus === 'AVAILABLE' ? 'text-emerald-400' : 'text-zinc-400'}`}>
              {bhoonidhiStatus}
            </span>
          </div>

          <span className="text-zinc-700">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-zinc-500 uppercase font-semibold">FIELD:</span>
            <span className="text-white font-bold">{fieldActiveCount} ACTIVE</span>
          </div>

          <span className="text-zinc-700">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-zinc-500 uppercase font-semibold">BROADCAST:</span>
            <span className="text-emerald-400 font-bold">READY</span>
          </div>
        </div>

        <div className="text-zinc-500 text-[10px]">
          Sync Fix: {lastUpdated || "00:00:00 UTC"}
        </div>
      </div>

      {/* Simplified Top Navigation Tabs */}
      <div className="px-4 sm:px-6 bg-black flex items-center justify-between text-xs font-mono">
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
                  className="px-3.5 py-2 text-zinc-400 hover:text-white hover:bg-zinc-900 border-b-2 border-transparent transition flex items-center gap-1.5 font-bold"
                >
                  <Icon className="w-3.5 h-3.5 text-zinc-400" />
                  <span>{item.label}</span>
                </Link>
              );
            }

            if (item.isAction) {
              return (
                <button
                  key={item.id}
                  onClick={onOpenBroadcast}
                  className="px-3.5 py-2 text-zinc-400 hover:text-white hover:bg-zinc-900 border-b-2 border-transparent transition flex items-center gap-1.5 font-bold"
                >
                  <Icon className="w-3.5 h-3.5 text-zinc-400" />
                  <span>{item.label}</span>
                </button>
              );
            }

            return (
              <button
                key={item.id}
                onClick={() => onSelectTab && onSelectTab(item.id)}
                className={`px-3.5 py-2 border-b-2 font-bold transition flex items-center gap-1.5 ${
                  isActive
                    ? "border-white text-white bg-zinc-900"
                    : "border-transparent text-zinc-400 hover:text-white hover:bg-zinc-900/50"
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
