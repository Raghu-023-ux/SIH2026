"use client";

import React from "react";
import { AlertOctagon, Flame, ShieldAlert, MapPin, Gauge } from "lucide-react";

interface KPICardsProps {
  activeEventsCount: number;
  criticalEventsCount: number;
  highRiskCount: number;
  moderateRiskCount: number;
  totalLocations: number;
  highestRiskScore: number;
  highestRiskLevel: string;
}

export default function KPICards({
  activeEventsCount,
  criticalEventsCount,
  highRiskCount,
  moderateRiskCount,
  totalLocations,
  highestRiskScore,
  highestRiskLevel,
}: KPICardsProps) {
  const getLevelColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case "CRITICAL":
        return "text-red-400 border-red-800 bg-red-950/40";
      case "HIGH":
        return "text-orange-400 border-orange-800 bg-orange-950/40";
      case "MODERATE":
        return "text-yellow-400 border-yellow-800 bg-yellow-950/40";
      default:
        return "text-emerald-400 border-emerald-800 bg-emerald-950/40";
    }
  };

  return (
    <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {/* 1. Active Events */}
      <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-semibold uppercase tracking-wider">Active Events</span>
          <ShieldAlert className="w-4 h-4 text-orange-400" />
        </div>
        <div className="my-2 flex items-baseline gap-2">
          <span className="text-2xl sm:text-3xl font-extrabold text-slate-100 font-mono">
            {activeEventsCount}
          </span>
          {activeEventsCount > 0 && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-orange-950 text-orange-400 border border-orange-800 font-mono animate-pulse">
              ACTION REQ
            </span>
          )}
        </div>
        <div className="text-[11px] text-slate-400">Crossing watch thresholds</div>
      </div>

      {/* 2. Critical Events */}
      <div className={`p-3.5 rounded-xl shadow-sm flex flex-col justify-between border ${criticalEventsCount > 0 ? "bg-red-950/30 border-red-800/80" : "bg-slate-900/80 border-slate-800"}`}>
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-semibold uppercase tracking-wider text-red-300">Critical Alerts</span>
          <AlertOctagon className={`w-4 h-4 ${criticalEventsCount > 0 ? "text-red-400 animate-bounce" : "text-slate-500"}`} />
        </div>
        <div className="my-2 flex items-baseline gap-2">
          <span className={`text-2xl sm:text-3xl font-extrabold font-mono ${criticalEventsCount > 0 ? "text-red-400" : "text-slate-100"}`}>
            {criticalEventsCount}
          </span>
          {criticalEventsCount > 0 && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-red-950 text-red-300 border border-red-700 font-mono">
              LEVEL 4
            </span>
          )}
        </div>
        <div className="text-[11px] text-slate-400">Score &ge; 75.0 (High Hazard)</div>
      </div>

      {/* 3. High Risk Locations */}
      <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-semibold uppercase tracking-wider text-orange-300">High Risk Sectors</span>
          <Flame className="w-4 h-4 text-orange-400" />
        </div>
        <div className="my-2 flex items-baseline gap-2">
          <span className="text-2xl sm:text-3xl font-extrabold text-slate-100 font-mono">
            {highRiskCount}
          </span>
          <span className="text-[11px] text-slate-400">stations</span>
        </div>
        <div className="text-[11px] text-slate-400">Score 50.0 - 74.9</div>
      </div>

      {/* 4. Total Monitored Locations */}
      <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl shadow-sm flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-semibold uppercase tracking-wider">Monitored Stations</span>
          <MapPin className="w-4 h-4 text-blue-400" />
        </div>
        <div className="my-2 flex items-baseline gap-2">
          <span className="text-2xl sm:text-3xl font-extrabold text-slate-100 font-mono">
            {totalLocations}
          </span>
          <span className="text-[11px] text-emerald-400 font-medium">Telemetry Active</span>
        </div>
        <div className="text-[11px] text-slate-400">Across 8 NER States</div>
      </div>

      {/* 5. Peak Regional Risk Index */}
      <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl shadow-sm flex flex-col justify-between col-span-2 sm:col-span-1">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span className="font-semibold uppercase tracking-wider">Peak Regional Risk</span>
          <Gauge className="w-4 h-4 text-purple-400" />
        </div>
        <div className="my-2 flex items-center justify-between">
          <span className="text-2xl sm:text-3xl font-extrabold text-slate-100 font-mono">
            {highestRiskScore.toFixed(1)}
            <span className="text-xs text-slate-500 font-normal">/100</span>
          </span>
          <span className={`text-xs font-bold px-2 py-0.5 rounded border font-mono ${getLevelColor(highestRiskLevel)}`}>
            {highestRiskLevel}
          </span>
        </div>
        <div className="text-[11px] text-slate-400">Composite maximum index</div>
      </div>
    </section>
  );
}
