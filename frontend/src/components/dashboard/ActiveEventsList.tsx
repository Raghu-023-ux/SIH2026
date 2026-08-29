"use client";

import React, { useState } from "react";
import { DisasterEventItem, LocationMapItem } from "@/components/dashboard/types";
import { AlertOctagon, Flame, ShieldAlert, CheckCircle2, TrendingUp, TrendingDown, Clock, Filter } from "lucide-react";

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
  const [sortBy, setSortBy] = useState<string>("severity");

  const locationMap = new Map(locations.map((l) => [l.id, l]));

  const filteredEvents = events.filter((ev) => {
    if (filterSeverity === "ALL") return true;
    if (filterSeverity === "ACTIVE") return ev.status !== "RESOLVED";
    if (filterSeverity === "RESOLVED") return ev.status === "RESOLVED";
    return (
      ev.severity?.toUpperCase() === filterSeverity ||
      ev.status?.toUpperCase() === filterSeverity
    );
  });

  const sortedEvents = [...filteredEvents].sort((a, b) => {
    if (sortBy === "risk_score") {
      return b.risk_score - a.risk_score;
    }
    if (sortBy === "recent") {
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    }
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
      return "bg-zinc-900 text-zinc-400 border-zinc-750 font-bold";
    }
    switch (severity?.toUpperCase()) {
      case "CRITICAL":
        return "bg-red-950 text-red-300 border-red-700 font-black";
      case "HIGH":
        return "bg-orange-950 text-orange-300 border-orange-700 font-black";
      case "MODERATE":
        return "bg-amber-950 text-amber-300 border-amber-700 font-black";
      default:
        return "bg-emerald-950 text-emerald-300 border-emerald-700 font-bold";
    }
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded p-4 space-y-3 font-sans text-white">
      {/* Header & Controls */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-orange-400" />
          <h3 className="text-xs font-black uppercase tracking-wider text-white font-mono">
            Active Incidents &amp; Alerts ({sortedEvents.length})
          </h3>
        </div>

        {/* Filter Toggle */}
        <div className="flex items-center gap-1 font-mono text-[10px]">
          {["ALL", "ACTIVE", "CRITICAL"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilterSeverity(lvl)}
              className={`px-2 py-0.5 rounded transition font-bold ${
                filterSeverity === lvl
                  ? "bg-white text-black font-black"
                  : "bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800"
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Events List */}
      <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
        {sortedEvents.length === 0 ? (
          <div className="py-8 text-center text-zinc-500 font-mono text-xs">
            No matching disaster events found.
          </div>
        ) : (
          sortedEvents.map((ev) => {
            const loc = locationMap.get(ev.location_id);
            const isSelected = selectedEventId === ev.id;

            return (
              <div
                key={ev.id}
                onClick={() => onSelectEvent(ev.id, ev.location_id)}
                className={`p-3 rounded border transition cursor-pointer font-mono text-xs space-y-1.5 ${
                  isSelected
                    ? "bg-zinc-900 border-white"
                    : "bg-black border-zinc-850 hover:border-zinc-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-black text-white text-xs">
                    {loc ? loc.name : ev.location_id}
                  </span>
                  <span
                    className={`text-[9px] px-2 py-0.5 rounded border uppercase ${getSeverityBadge(
                      ev.status,
                      ev.severity
                    )}`}
                  >
                    {ev.status === "RESOLVED" ? "RESOLVED" : ev.severity} ({ev.risk_score.toFixed(0)})
                  </span>
                </div>

                <div className="text-[11px] text-zinc-400 font-sans line-clamp-1">
                  {ev.summary || "Landslide threshold crossed. Continuous monitoring active."}
                </div>

                <div className="flex items-center justify-between text-[10px] text-zinc-500 pt-1 border-t border-zinc-900">
                  <span>ID: {ev.id.slice(0, 12)}</span>
                  <span>{ev.status} • {new Date(ev.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
