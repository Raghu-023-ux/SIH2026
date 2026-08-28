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
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  HelpCircle,
  Info,
  ShieldCheck,
  Zap,
  Clock,
  Layers,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Check,
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
  onAcknowledgeEvent: (eventId: string) => Promise<void>;
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
  const [activeTab, setActiveTab] = useState<"factors" | "charts" | "timeline">("factors");
  const [showConfidenceTooltip, setShowConfidenceTooltip] = useState(false);

  if (!location) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
        <Layers className="w-8 h-8 mx-auto mb-2 opacity-50 text-indigo-400" />
        <p className="text-sm font-medium">Select a monitoring station or active event to inspect multi-signal hazard telemetry.</p>
      </div>
    );
  }

  const riskScore = latestAssessment?.risk_score ?? location.risk_score ?? 0;
  const riskLevel = latestAssessment?.risk_level ?? location.risk_level ?? "LOW";
  const confidence = latestAssessment?.confidence_score ?? location.confidence_score ?? 0.85;
  const trajectory = latestAssessment?.trajectory || event?.trajectory || "STABLE";
  const dataQuality = latestAssessment?.data_quality;
  const signalAgreement = latestAssessment?.signal_agreement;

  const isCritical = riskLevel === "CRITICAL";
  const isHigh = riskLevel === "HIGH";
  const isModerate = riskLevel === "MODERATE";

  const getTrajectoryBadge = (traj: string) => {
    switch (traj.toUpperCase()) {
      case "INCREASING":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-red-950/80 text-red-400 border border-red-800/80">
            <TrendingUp className="w-3 h-3" /> ↑ INCREASING
          </span>
        );
      case "DECREASING":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
            <TrendingDown className="w-3 h-3" /> ↓ DECREASING
          </span>
        );
      case "VOLATILE":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-amber-950/80 text-amber-400 border border-amber-800/80">
            <Activity className="w-3 h-3" /> ~ VOLATILE
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-slate-800 text-slate-300 border border-slate-700">
            <Minus className="w-3 h-3" /> → STABLE
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-xl backdrop-blur-sm space-y-4">
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
              Station Sector:
            </span>
            <h2 className="text-base font-bold text-slate-100">{location.name}</h2>
            <span className="text-xs text-slate-400 font-mono">
              ({location.district}, {location.state})
            </span>
          </div>

          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase ${
                isCritical
                  ? "bg-red-950 text-red-400 border border-red-800"
                  : isHigh
                  ? "bg-orange-950 text-orange-400 border border-orange-800"
                  : isModerate
                  ? "bg-yellow-950 text-yellow-400 border border-yellow-800"
                  : "bg-emerald-950 text-emerald-400 border border-emerald-800"
              }`}
            >
              {riskLevel} RISK ({riskScore.toFixed(1)} / 100)
            </span>

            {/* Trajectory */}
            {getTrajectoryBadge(trajectory)}

            {/* Event Lifecycle Badge */}
            {event && event.status !== "RESOLVED" && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-indigo-950/80 text-indigo-300 border border-indigo-800">
                Active Event [{event.status}]
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {event && event.status !== "RESOLVED" && (
            <button
              onClick={() => onAcknowledgeEvent(event.id)}
              disabled={isAcknowledging || event.summary.includes("[ACKNOWLEDGED BY OFFICER]")}
              className="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 font-medium"
            >
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              {event.summary.includes("[ACKNOWLEDGED BY OFFICER]")
                ? "Acknowledged"
                : isAcknowledging
                ? "Recording..."
                : "Acknowledge Alert"}
            </button>
          )}

          <button
            onClick={() => onOpenInvestigate(location.id)}
            className="bg-indigo-600/90 hover:bg-indigo-500 text-white text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 font-medium shadow-sm"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            360° Station Dossier
          </button>
        </div>
      </div>

      {/* Multi-Signal Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Confidence Gauge */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 relative">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase">
            <span>Assessment Confidence</span>
            <div
              className="cursor-pointer relative"
              onMouseEnter={() => setShowConfidenceTooltip(true)}
              onMouseLeave={() => setShowConfidenceTooltip(false)}
              onClick={() => setShowConfidenceTooltip(!showConfidenceTooltip)}
            >
              <HelpCircle className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300 transition" />
              {showConfidenceTooltip && (
                <div className="absolute right-0 top-5 w-64 p-2.5 bg-slate-800 text-[11px] text-slate-200 rounded-lg shadow-2xl border border-slate-700 z-50 leading-relaxed font-sans">
                  <strong>Assessment Confidence:</strong> Represents data completeness, sensor freshness, and multi-signal coherence across rainfall, pore water, and slope sensors. It is not the probability of a landslide occurring.
                </div>
              )}
            </div>
          </div>
          <div className="text-base font-extrabold text-slate-100 font-mono mt-0.5">
            {(confidence * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
            {signalAgreement ? `Coherence: ${signalAgreement.agreement_level}` : "Signal Agreement: High"}
          </div>
        </div>

        {/* Data Quality & Assurance */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <div className="text-slate-400 text-[10px] font-mono uppercase">Data Quality</div>
          <div className="text-base font-extrabold text-indigo-300 font-mono mt-0.5">
            {dataQuality ? dataQuality.status : "VALID"}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
            Freshness: {dataQuality ? `${(dataQuality.freshness_score * 100).toFixed(0)}%` : "100%"} | Comp: {dataQuality ? `${(dataQuality.completeness_score * 100).toFixed(0)}%` : "100%"}
          </div>
        </div>

        {/* Peak Hazard Recorded */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <div className="text-slate-400 text-[10px] font-mono uppercase">Peak Risk Severity</div>
          <div className="text-base font-extrabold text-slate-100 font-mono mt-0.5">
            {event?.peak_risk ? `${event.peak_risk.toFixed(1)} / 100` : `${riskScore.toFixed(1)} / 100`}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
            Peak Tier: {event?.peak_severity || riskLevel}
          </div>
        </div>

        {/* Engine Version */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <div className="text-slate-400 text-[10px] font-mono uppercase">Engine Version</div>
          <div className="text-base font-bold text-slate-200 font-mono mt-0.5">
            {latestAssessment?.assessment_version || "prototype-v0.2"}
          </div>
          <div className="text-[10px] text-emerald-400 mt-0.5 font-mono">
            Deterministic Multimodal
          </div>
        </div>
      </div>

      {/* Diagnostic Explanation Summary */}
      <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800 text-xs text-slate-300 space-y-1.5">
        <div className="flex items-center gap-1.5 text-indigo-400 font-semibold font-mono text-[11px] uppercase tracking-wider">
          <Zap className="w-3.5 h-3.5" />
          <span>Diagnostic Rationale &amp; Analytical Attribution:</span>
        </div>
        <p className="leading-relaxed text-slate-300">
          {latestAssessment?.reason || event?.summary || "Sensors reporting within normal baseline operating bounds."}
        </p>

        {/* Reason Code Badges */}
        {latestAssessment?.reason_codes && latestAssessment.reason_codes.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap pt-1">
            <span className="text-[10px] font-mono uppercase text-slate-500">Reason Codes:</span>
            {latestAssessment.reason_codes.map((code) => (
              <span
                key={code}
                className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-slate-800 text-indigo-300 border border-slate-700"
              >
                {code}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pt-1">
        <button
          onClick={() => setActiveTab("factors")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-t-lg transition border-b-2 font-mono ${
            activeTab === "factors"
              ? "border-indigo-500 text-indigo-400 bg-slate-800/40"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Factor Scoring ({latestAssessment?.factors?.length ?? 0})
        </button>

        <button
          onClick={() => setActiveTab("charts")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-t-lg transition border-b-2 font-mono ${
            activeTab === "charts"
              ? "border-indigo-500 text-indigo-400 bg-slate-800/40"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Time-Series Telemetry
        </button>

        <button
          onClick={() => setActiveTab("timeline")}
          className={`px-3 py-1.5 text-xs font-semibold rounded-t-lg transition border-b-2 font-mono ${
            activeTab === "timeline"
              ? "border-indigo-500 text-indigo-400 bg-slate-800/40"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Hazard Timeline ({timeline.length})
        </button>
      </div>

      {/* Tab 1: Factors Breakdown Table */}
      {activeTab === "factors" && (
        <div className="space-y-3">
          <div className="text-[11px] text-slate-400">
            Multi-signal factor contribution to composite risk score (0-100). Contributing factors are normalized ($0.0 - 1.0$) and weighted centrally:
          </div>

          <div className="space-y-2">
            {(latestAssessment?.factors || []).map((f) => {
              const statusColor =
                f.status === "CRITICAL"
                  ? "text-red-400 bg-red-950/60 border-red-800"
                  : f.status === "HIGH"
                  ? "text-orange-400 bg-orange-950/60 border-orange-800"
                  : f.status === "MODERATE"
                  ? "text-yellow-400 bg-yellow-950/60 border-yellow-800"
                  : "text-emerald-400 bg-emerald-950/60 border-emerald-800";

              const barColor =
                f.status === "CRITICAL"
                  ? "bg-red-500"
                  : f.status === "HIGH"
                  ? "bg-orange-500"
                  : f.status === "MODERATE"
                  ? "bg-yellow-500"
                  : "bg-emerald-500";

              return (
                <div
                  key={f.name}
                  className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 space-y-1.5 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200">{f.name}</span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-mono uppercase font-bold border ${statusColor}`}
                      >
                        {f.status}
                      </span>
                    </div>

                    <div className="text-right font-mono">
                      <span className="font-bold text-slate-100">+{f.contribution.toFixed(1)} pts</span>
                      <span className="text-slate-500 text-[10px] ml-1.5">
                        (Norm: {f.normalized_score?.toFixed(2) ?? "--"} | W: {(f.weight * 100).toFixed(0)}%)
                      </span>
                    </div>
                  </div>

                  {/* Visual Progress Bar */}
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${barColor} transition-all duration-500`}
                      style={{ width: `${Math.min(100, (f.normalized_score ?? (f.contribution / 20.0)) * 100)}%` }}
                    />
                  </div>

                  {f.description && (
                    <div className="text-[11px] text-slate-400 font-mono pt-0.5">
                      {f.description}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 2: Recharts Trend Curves */}
      {activeTab === "charts" && (
        <TrendCharts weatherHistory={weatherHistory} riskHistory={riskHistory} />
      )}

      {/* Tab 3: Chronological Hazard Timeline */}
      {activeTab === "timeline" && <EventTimeline milestones={timeline} />}
    </div>
  );
}
