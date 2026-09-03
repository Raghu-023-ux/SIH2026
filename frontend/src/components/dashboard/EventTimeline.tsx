"use client";

import React from "react";
import { EventTimelineMilestoneItem } from "@/components/dashboard/types";
import { Clock, AlertTriangle, ShieldCheck, Info, Flame, CheckCircle2 } from "lucide-react";

interface EventTimelineProps {
  milestones: EventTimelineMilestoneItem[];
}

export default function EventTimeline({ milestones }: EventTimelineProps) {
  const getIconForCategory = (category: string, severity?: string | null) => {
    switch (category) {
      case "event":
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case "anomaly":
        return <Flame className="w-4 h-4 text-amber-400" />;
      case "escalation":
        return <AlertTriangle className="w-4 h-4 text-orange-400" />;
      case "resolution":
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      default:
        return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  const getBorderColor = (category: string) => {
    switch (category) {
      case "event":
        return "border-red-800 bg-red-950/40";
      case "anomaly":
        return "border-amber-800 bg-amber-950/30";
      case "escalation":
        return "border-orange-800 bg-orange-950/30";
      case "resolution":
        return "border-emerald-800 bg-emerald-950/30";
      default:
        return "border-slate-800 bg-slate-900/50";
    }
  };

  return (
    <div className="space-y-3">
      <div className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5 border-b border-slate-800 pb-2">
        <Clock className="w-4 h-4 text-indigo-400" />
        Chronological Event &amp; Anomaly Audit Trail
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {milestones.map((m, idx) => (
          <div key={idx} className="relative group">
            {/* Timeline node icon */}
            <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-slate-950 border border-slate-700 flex items-center justify-center">
              {getIconForCategory(m.category, m.severity)}
            </div>

            {/* Content card */}
            <div className={`p-3 rounded-lg border text-xs ${getBorderColor(m.category)}`}>
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-bold text-slate-100">{m.title}</span>
                <span className="font-mono text-[11px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                  {m.time_label}
                </span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">{m.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
