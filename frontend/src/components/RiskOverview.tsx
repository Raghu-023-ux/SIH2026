"use client";

import React from "react";
import { AlertTriangle, Flame, ShieldCheck, MapPin, Radio } from "lucide-react";

interface MultiLocationData {
  executed_at: string;
  locations_evaluated: number;
  active_events_count: number;
  highest_risk_score: number;
  highest_risk_level: string;
}

export default function RiskOverview({ data }: { data: MultiLocationData | null }) {
  const getRiskBadgeColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case "CRITICAL":
        return "bg-red-950/80 text-red-300 border-red-800";
      case "HIGH":
        return "bg-orange-950/80 text-orange-300 border-orange-800";
      case "MODERATE":
        return "bg-yellow-950/80 text-yellow-300 border-yellow-800";
      default:
        return "bg-emerald-950/80 text-emerald-300 border-emerald-800";
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
        <Radio className="w-5 h-5 text-amber-400 animate-pulse" />
        Regional Intelligence Overview (NER)
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Monitored Locations */}
        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>NER Stations</span>
            <MapPin className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">
            {data ? data.locations_evaluated : "--"}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Sikkim, Meghalaya, Mizoram...</div>
        </div>

        {/* Active Disaster Events */}
        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Active Events</span>
            <AlertTriangle className="w-4 h-4 text-orange-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100 flex items-center gap-2">
            <span>{data ? data.active_events_count : "--"}</span>
            {data && data.active_events_count > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-orange-950 text-orange-400 border border-orange-800 font-normal">
                Active
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Crossing watch threshold</div>
        </div>

        {/* Highest Risk Score */}
        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Peak Risk Score</span>
            <Flame className="w-4 h-4 text-red-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">
            {data ? `${data.highest_risk_score.toFixed(1)} / 100` : "--"}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Composite hazard index</div>
        </div>

        {/* Highest Risk Level */}
        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Peak Risk Level</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2">
            {data ? (
              <span className={`inline-block px-2.5 py-1 text-sm font-bold rounded-md border font-mono ${getRiskBadgeColor(data.highest_risk_level)}`}>
                {data.highest_risk_level}
              </span>
            ) : (
              <span className="text-2xl font-bold text-slate-100">--</span>
            )}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Analytical assessment</div>
        </div>
      </div>
    </div>
  );
}
