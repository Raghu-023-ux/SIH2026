"use client";

import React, { useState } from "react";
import {
  DisasterEventItem,
  LocationMapItem,
  RiskAssessmentItem,
  WeatherObservationItem,
  EventTimelineMilestoneItem,
} from "@/components/dashboard/types";
import {
  ShieldAlert,
  Info,
  CheckCircle2,
  TrendingUp,
  CloudRain,
  Mountain,
  FileText,
  Clock,
  Layers,
  ArrowUpRight,
  UserCheck,
} from "lucide-react";
import TrendCharts from "@/components/dashboard/TrendCharts";
import EventTimeline from "@/components/dashboard/EventTimeline";

interface EventDetailPanelProps {
  event: DisasterEventItem | null;
  location: LocationMapItem | null;
  latestAssessment: RiskAssessmentItem | null;
  weatherHistory: WeatherObservationItem[];
  riskHistory: RiskAssessmentItem[];
  timeline: EventTimelineMilestoneItem[];
  onAcknowledgeEvent: (eventId: string) => void;
  isAcknowledging: boolean;
  onOpenInvestigate: (locationId: string) => void;
}

export default function EventDetailPanel({
  event,
  location,
  latestAssessment,
  weatherHistory,
  riskHistory,
  timeline,
  onAcknowledgeEvent,
  isAcknowledging,
  onOpenInvestigate,
}: EventDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<"factors" | "charts" | "timeline" | "geometry">("factors");
  const [showConfidenceTooltip, setShowConfidenceTooltip] = useState<boolean>(false);

  if (!location && !event) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-8 text-center text-slate-500 flex flex-col items-center justify-center h-[420px] space-y-3">
        <Layers className="w-10 h-10 text-slate-600" />
        <div className="text-base font-bold text-slate-400">No Location or Event Selected</div>
        <p className="text-xs max-w-md">
          Select a monitored station from the GIS Risk Map or click an active alert in the Event Queue to inspect scientific factor breakdowns, multi-metric time-series, and hazard audit trails.
        </p>
      </div>
    );
  }

  const riskScore = event ? event.risk_score : latestAssessment?.risk_score ?? 10.0;
  const riskLevel = event ? event.severity : latestAssessment?.risk_level ?? "LOW";
  const confidence = event ? event.confidence_score : latestAssessment?.confidence_score ?? 0.85;
  const isAcknowledged = event?.summary.includes("[ACKNOWLEDGED BY OFFICER]");

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "CRITICAL":
        return "bg-red-950/90 text-red-300 border-red-800";
      case "HIGH":
      case "HIGH_RISK":
        return "bg-orange-950/90 text-orange-300 border-orange-800";
      case "MODERATE":
      case "ELEVATED":
      case "WATCH":
        return "bg-yellow-950/90 text-yellow-300 border-yellow-800";
      default:
        return "bg-emerald-950/90 text-emerald-300 border-emerald-800";
    }
  };

  const getFactorBarColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "critical":
        return "bg-red-500";
      case "high":
        return "bg-orange-500";
      case "moderate":
        return "bg-yellow-400";
      default:
        return "bg-emerald-500";
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm space-y-5">
      {/* 1. Header & Operational Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-indigo-400 uppercase tracking-wider">
              {event ? "ACTIVE DISASTER INCIDENT" : "MONITORED STATION TELEMETRY"}
            </span>
            {event && (
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${getStatusBadge(event.status)}`}>
                {event.status}
              </span>
            )}
            {isAcknowledged && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 flex items-center gap-1">
                <UserCheck className="w-3 h-3" /> ACKNOWLEDGED
              </span>
            )}
          </div>
          <h2 className="text-lg font-bold text-slate-100 mt-1">
            {location ? location.name : "Station Sector"}
          </h2>
          <div className="text-xs text-slate-400">
            {location ? `${location.district}, ${location.state}` : event?.affected_area}
            {location && (
              <span className="ml-2 font-mono text-slate-500">
                (Elev: {location.elevation}m | Slope: {location.slope_angle}°)
              </span>
            )}
          </div>
        </div>

        {/* Risk Score & Model Confidence Gauge */}
        <div className="flex items-center gap-4 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div className="text-right">
            <div className="text-[10px] font-mono text-slate-500 uppercase">Composite Risk</div>
            <div className="text-2xl font-black text-slate-100 font-mono">
              {riskScore.toFixed(1)}
              <span className="text-xs text-slate-500 font-normal"> / 100</span>
            </div>
          </div>

          <div className="text-center">
            <div className={`px-3 py-1 rounded text-xs font-mono font-bold border ${getStatusBadge(riskLevel)}`}>
              {riskLevel}
            </div>
            {/* Confidence Tooltip */}
            <div className="relative mt-1">
              <button
                onMouseEnter={() => setShowConfidenceTooltip(true)}
                onMouseLeave={() => setShowConfidenceTooltip(false)}
                className="text-[10px] text-slate-400 hover:text-slate-200 font-mono flex items-center justify-center gap-1 mx-auto"
              >
                <span>{(confidence * 100).toFixed(0)}% Confidence</span>
                <Info className="w-3 h-3 text-slate-500" />
              </button>

              {showConfidenceTooltip && (
                <div className="absolute right-0 top-6 z-50 w-64 bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-[11px] text-slate-300 shadow-2xl backdrop-blur-md">
                  <strong>Assessment Confidence:</strong> Reflects agreement among currently available sensor telemetry and data density. It is an analytical signal agreement metric, not a guaranteed probability of disaster occurrence.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab("factors")}
          className={`px-3 py-1.5 rounded-lg transition font-semibold flex items-center gap-1.5 ${
            activeTab === "factors"
              ? "bg-indigo-600 text-white"
              : "text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-800"
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          Why This Risk Was Detected
        </button>

        <button
          onClick={() => setActiveTab("charts")}
          className={`px-3 py-1.5 rounded-lg transition font-semibold flex items-center gap-1.5 ${
            activeTab === "charts"
              ? "bg-indigo-600 text-white"
              : "text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-800"
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5" />
          Time-Series Charts
        </button>

        <button
          onClick={() => setActiveTab("timeline")}
          className={`px-3 py-1.5 rounded-lg transition font-semibold flex items-center gap-1.5 ${
            activeTab === "timeline"
              ? "bg-indigo-600 text-white"
              : "text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-800"
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          Hazard Timeline
        </button>

        {location && (
          <button
            onClick={() => onOpenInvestigate(location.id)}
            className="ml-auto text-indigo-400 hover:text-indigo-300 transition text-[11px] font-mono flex items-center gap-1 bg-indigo-950/60 px-2.5 py-1.5 rounded-lg border border-indigo-800/80"
          >
            <span>Deep 360° Inspection</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* 3. Tab Contents */}

      {/* TAB A: Scientific Factor Breakdown */}
      {activeTab === "factors" && (
        <div className="space-y-4">
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
              <span>Scientific / Analytical Factor Attribution</span>
              <span className="text-[11px] font-mono text-slate-500 font-normal">Score Contribution (Max 100)</span>
            </div>

            {latestAssessment && latestAssessment.factors ? (
              <div className="space-y-3">
                {latestAssessment.factors.map((factor, idx) => {
                  const percent = Math.min(100, (factor.contribution / 20.0) * 100);
                  return (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-200">{factor.name}</span>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${getStatusBadge(
                              factor.status
                            )}`}
                          >
                            {factor.status}
                          </span>
                          <span className="font-mono font-bold text-slate-100">
                            +{factor.contribution.toFixed(1)} pts
                          </span>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all duration-500 ${getFactorBarColor(factor.status)}`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>

                      <div className="text-[11px] text-slate-400">{factor.description}</div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-4 text-center">
                Loading factor details from disaster engine...
              </div>
            )}
          </div>

          {/* Diagnostic Assessment Explanation */}
          <div className="bg-indigo-950/30 border border-indigo-800/60 rounded-xl p-3.5 space-y-1 text-xs">
            <div className="font-bold text-indigo-300 uppercase tracking-wider text-[11px]">
              Diagnostic Rationale Summary
            </div>
            <p className="text-slate-200 leading-relaxed">
              {latestAssessment ? latestAssessment.reason : event?.summary || "Baseline parameters normal."}
            </p>
          </div>
        </div>
      )}

      {/* TAB B: Trend Charts */}
      {activeTab === "charts" && (
        <TrendCharts weatherHistory={weatherHistory} riskHistory={riskHistory} />
      )}

      {/* TAB C: Timeline Audit */}
      {activeTab === "timeline" && <EventTimeline milestones={timeline} />}

      {/* 4. Officer Action Bar */}
      {event && event.status !== "RESOLVED" && (
        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-400 font-mono">
            Event ID: <span className="text-slate-300">{event.id}</span>
          </div>

          <div className="flex items-center gap-2">
            {!isAcknowledged && (
              <button
                onClick={() => onAcknowledgeEvent(event.id)}
                disabled={isAcknowledging}
                className="bg-emerald-700 hover:bg-emerald-600 active:bg-emerald-800 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition flex items-center gap-1.5 shadow"
              >
                <CheckCircle2 className="w-4 h-4" />
                {isAcknowledging ? "Acknowledging..." : "Acknowledge Event"}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
