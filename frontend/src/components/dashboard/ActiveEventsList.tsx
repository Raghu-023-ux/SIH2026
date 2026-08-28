"use client";

import React, { useState } from "react";
import { DisasterEventItem, LocationMapItem } from "@/components/dashboard/types";
import { AlertOctagon, Flame, ShieldAlert, ArrowUpRight, CheckCircle2, TrendingUp, TrendingDown, Clock, Filter, ArrowUpDown } from "lucide-react";

interface ActiveEventsListProps {
  events: DisasterEventItem[];
  locations: LocationMapItem[];
  selectedEventId: string | null;
  onSelectEvent: (eventId: string, locationId: string) => void;
}

export default function ActiveEventsList({
  events,
  locations,
  selectedEventId,
  onSelectEvent,
}: ActiveEventsListProps) {
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<string>("severity"); // 'severity', 'risk_score', 'recent'

  // Map location IDs to location names for quick lookup
  const locationMap = new Map(locations.map((l) => [l.id, l]));

  // Filtering
  const filteredEvents = events.filter((ev) => {
    if (filterSeverity === "ALL") return true;
    if (filterSeverity === "ACTIVE") return ev.status !== "RESOLVED";
    if (filterSeverity === "RESOLVED") return ev.status === "RESOLVED";
    return (
      ev.severity?.toUpperCase() === filterSeverity ||
      ev.status?.toUpperCase() === filterSeverity
    );
  });

  // Sorting
  const sortedEvents = [...filteredEvents].sort((a, b) => {
    if (sortBy === "risk_score") {
      return b.risk_score - a.risk_score;
    }
    if (sortBy === "recent") {
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    }
    // Default: severity (CRITICAL > HIGH > MODERATE > LOW / RESOLVED)
    const severityRank: Record<string, number> = {
      CRITICAL: 4,
      HIGH: 3,
      MODERATE: 2,
      LOW: 1,
    };
    const rankA = a.status === "RESOLVED" ? 0 : severityRank[a.severity?.toUpperCase()] || 0;
    const rankB = b.status === "RESOLVED" ? 0 : severityRank[b.severity?.toUpperCase()] || 0;
    if (rankB !== rankA) return rankB - rankA;
    return b.risk_score - a.risk_score;
  });

  const getSeverityBadge = (status: string, severity: string) => {
    if (status === "RESOLVED") {
      return "bg-slate-800 text-slate-400 border-slate-700";
    }
    switch (severity?.toUpperCase()) {
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

  const formatTimeAgo = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMin = Math.max(0, Math.floor((now.getTime() - d.getTime()) / 60000));
    if (diffMin < 1) return "Just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur-sm flex flex-col h-[460px] lg:h-[540px]">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-orange-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
            Active Event Queue
          </h2>
          <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            {sortedEvents.length}
          </span>
        </div>

        {/* Sort Selector */}
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <ArrowUpDown className="w-3.5 h-3.5" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-300 text-[11px] focus:outline-none focus:border-indigo-500"
          >
            <option value="severity">Sort: Severity</option>
            <option value="risk_score">Sort: Risk Score</option>
            <option value="recent">Sort: Most Recent</option>
          </select>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-2 text-xs font-mono border-b border-slate-800/60">
        {["ALL", "CRITICAL", "HIGH", "MODERATE", "RESOLVED"].map((tab) => (
          <button
            key={tab}
            onClick={() => setFilterSeverity(tab)}
            className={`px-2.5 py-1 rounded-md transition text-[11px] font-semibold flex-shrink-0 ${
              filterSeverity === tab
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-slate-950/70 text-slate-400 hover:text-slate-200 border border-slate-800/80"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Events Scrollable List */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
        {sortedEvents.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-2">
            <CheckCircle2 className="w-8 h-8 text-slate-600" />
            <div className="text-sm font-medium text-slate-400">No events matching filter</div>
            <div className="text-xs">All monitored locations currently within safe baseline levels.</div>
          </div>
        ) : (
          sortedEvents.map((ev) => {
            const loc = locationMap.get(ev.location_id);
            const isSelected = ev.id === selectedEventId;

            return (
              <div
                key={ev.id}
                onClick={() => onSelectEvent(ev.id, ev.location_id)}
                className={`p-3 rounded-xl border transition cursor-pointer flex flex-col justify-between gap-2.5 ${
                  isSelected
                    ? "bg-indigo-950/40 border-indigo-500 shadow-md ring-1 ring-indigo-500/50"
                    : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/60"
                }`}
              >
                {/* Event Card Top Row */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${getSeverityBadge(
                          ev.status,
                          ev.severity
                        )}`}
                      >
                        {ev.status === "RESOLVED" ? "RESOLVED" : ev.severity}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {ev.status !== "RESOLVED" ? `[${ev.status}]` : ""}
                      </span>
                    </div>
                    <div className="text-sm font-bold text-slate-100 mt-1 leading-snug">
                      {loc ? loc.name : "Station Sector"}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {loc ? `${loc.district}, ${loc.state}` : ev.affected_area || "NER Corridor"}
                    </div>
                  </div>

                  {/* Score Dial */}
                  <div className="text-right flex-shrink-0">
                    <div className="text-[10px] text-slate-500 font-mono">RISK SCORE</div>
                    <div className="text-xl font-extrabold text-slate-100 font-mono">
                      {ev.risk_score.toFixed(1)}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      {(ev.confidence_score * 100).toFixed(0)}% Conf
                    </div>
                  </div>
                </div>

                {/* Event Summary Snippet */}
                <div className="text-[11px] text-slate-400 line-clamp-2 bg-slate-900/60 p-1.5 rounded border border-slate-800/60">
                  {ev.summary}
                </div>

                {/* Footer Metadata */}
                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-900 font-mono">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {formatTimeAgo(ev.detected_at)}
                  </span>
                  <span className="text-indigo-400 hover:underline flex items-center gap-0.5">
                    Inspect Detail <ArrowUpRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
