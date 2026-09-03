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
        return "text-red-300 border-red-700 bg-red-950 font-black";
      case "HIGH":
        return "text-orange-300 border-orange-700 bg-orange-950 font-black";
      case "MODERATE":
        return "text-amber-300 border-amber-700 bg-amber-950 font-black";
      default:
        return "text-emerald-300 border-emerald-700 bg-emerald-950 font-black";
    }
  };

  return (
    <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 font-sans">
      {/* 1. Active Events */}
      <div className="bg-zinc-950 border border-zinc-800 p-3.5 rounded flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400 text-[11px] font-mono">
          <span className="uppercase font-bold tracking-wider text-zinc-300">Active Incidents</span>
          <ShieldAlert className="w-3.5 h-3.5 text-orange-400" />
        </div>
        <div className="my-1.5 flex items-baseline gap-2">
          <span className="text-3xl font-black text-white font-mono">
            {activeEventsCount}
          </span>
          {activeEventsCount > 0 && (
            <span className="text-[10px] font-black px-2 py-0.5 rounded bg-orange-950 text-orange-300 border border-orange-700 font-mono">
              ACTION REQ
            </span>
          )}
        </div>
        <div className="text-[10px] text-zinc-500 font-mono">Thresholds Exceeded</div>
      </div>

      {/* 2. Critical Events */}
      <div className={`p-3.5 rounded flex flex-col justify-between border ${criticalEventsCount > 0 ? "bg-red-950/40 border-red-700" : "bg-zinc-950 border-zinc-800"}`}>
        <div className="flex items-center justify-between text-zinc-400 text-[11px] font-mono">
          <span className="uppercase font-bold tracking-wider text-red-300">Critical Alerts</span>
          <AlertOctagon className={`w-3.5 h-3.5 ${criticalEventsCount > 0 ? "text-red-400" : "text-zinc-500"}`} />
        </div>
        <div className="my-1.5 flex items-baseline gap-2">
          <span className={`text-3xl font-black font-mono ${criticalEventsCount > 0 ? "text-red-400" : "text-white"}`}>
            {criticalEventsCount}
          </span>
          {criticalEventsCount > 0 && (
            <span className="text-[10px] font-black px-2 py-0.5 rounded bg-red-950 text-red-200 border border-red-600 font-mono">
              LEVEL 4
            </span>
          )}
        </div>
        <div className="text-[10px] text-zinc-500 font-mono">Score &ge; 75 (Immediate Evacuation)</div>
      </div>

      {/* 3. High Risk Locations */}
      <div className="bg-zinc-950 border border-zinc-800 p-3.5 rounded flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400 text-[11px] font-mono">
          <span className="uppercase font-bold tracking-wider text-orange-300">High Risk Sectors</span>
          <Flame className="w-3.5 h-3.5 text-orange-400" />
        </div>
        <div className="my-1.5 flex items-baseline gap-2">
          <span className="text-3xl font-black text-white font-mono">
            {highRiskCount}
          </span>
          <span className="text-[11px] text-zinc-400 font-mono font-bold">stations</span>
        </div>
        <div className="text-[10px] text-zinc-500 font-mono">Score 50.0 – 74.9</div>
      </div>

      {/* 4. Total Monitored Locations */}
      <div className="bg-zinc-950 border border-zinc-800 p-3.5 rounded flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400 text-[11px] font-mono">
          <span className="uppercase font-bold tracking-wider text-zinc-300">Telemetry Stations</span>
          <MapPin className="w-3.5 h-3.5 text-zinc-400" />
        </div>
        <div className="my-1.5 flex items-baseline gap-2">
          <span className="text-3xl font-black text-white font-mono">
            {totalLocations}
          </span>
          <span className="text-[10px] text-emerald-400 font-mono font-bold">Active</span>
        </div>
        <div className="text-[10px] text-zinc-500 font-mono">NER Corridor Coverage</div>
      </div>

      {/* 5. Peak Regional Risk Index */}
      <div className="bg-zinc-950 border border-zinc-800 p-3.5 rounded flex flex-col justify-between col-span-2 sm:col-span-1">
        <div className="flex items-center justify-between text-zinc-400 text-[11px] font-mono">
          <span className="uppercase font-bold tracking-wider text-zinc-300">Peak Risk Index</span>
          <Gauge className="w-3.5 h-3.5 text-zinc-400" />
        </div>
        <div className="my-1.5 flex items-center justify-between">
          <span className="text-3xl font-black text-white font-mono">
            {highestRiskScore.toFixed(1)}
            <span className="text-xs text-zinc-500 font-normal"> / 100</span>
          </span>
          <span className={`text-[10px] px-2 py-0.5 rounded border font-mono ${getLevelColor(highestRiskLevel)}`}>
            {highestRiskLevel}
          </span>
        </div>
        <div className="text-[10px] text-zinc-500 font-mono">Regional Composite Max</div>
      </div>
    </section>
  );
}
