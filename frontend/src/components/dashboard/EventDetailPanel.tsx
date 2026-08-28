"use client";

import React from "react";
import {
  DisasterEventItem,
  RiskAssessmentItem,
  WeatherObservationItem,
  EventTimelineMilestoneItem,
} from "./types";
import {
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Activity,
  Layers,
  Clock,
  Check,
  ExternalLink,
  Shield,
  Gauge,
  Info,
  Calendar,
  Minus,
  Sparkles,
  FileText,
  Compass,
} from "lucide-react";

interface EventDetailPanelProps {
  event: DisasterEventItem | null;
  location: {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    district: string;
    state: string;
    elevation: number;
    slope_angle: number;
    susceptibility_score: number;
  } | null;
  latestAssessment: RiskAssessmentItem | null;
  weatherHistory: WeatherObservationItem[];
  riskHistory: RiskAssessmentItem[];
  timeline: EventTimelineMilestoneItem[];
  onAcknowledgeEvent: (eventId: string) => Promise<void>;
  isAcknowledging: boolean;
  onOpenInvestigate: (locationId: string) => void;
  onAskAI?: (question: string, agentType?: string) => void;
  onOpenBroadcast?: (eventId: string, locationId: string) => void;
  onOpenSitRep?: (eventId: string) => void;
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
  onAskAI,
}: EventDetailPanelProps) {
  if (!location) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center text-slate-500 font-mono text-xs flex flex-col items-center justify-center gap-2">
        <Activity className="w-6 h-6 text-slate-600 animate-pulse" />
        Select a monitoring location on the tactical map or active event queue to inspect factor diagnostics.
      </div>
    );
  }

  const riskScore = latestAssessment?.risk_score ?? 0;
  const riskLevel = latestAssessment?.risk_level ?? "LOW";
  const confidenceScore = latestAssessment?.confidence_score ?? 0.8;
  const trajectory = latestAssessment?.trajectory ?? "STABLE";
  const reasonCodes = latestAssessment?.reason_codes ?? [];
  const factors = latestAssessment?.factors ?? [];
  const dataQuality = latestAssessment?.data_quality;
  const signalAgreement = latestAssessment?.signal_agreement;

  const isCritical = riskLevel === "CRITICAL" || riskScore >= 75;
  const isHigh = riskLevel === "HIGH" || (riskScore >= 50 && riskScore < 75);
  const isModerate = riskLevel === "ELEVATED" || (riskScore >= 25 && riskScore < 50);

  const getTrajectoryBadge = (traj: string) => {
    switch (traj) {
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
          {onAskAI && (
            <button
              onClick={() => onAskAI("Explain the primary physical and terrain factors determining this risk score.", "explanation")}
              className="bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 border border-indigo-700/60 text-xs px-2.5 py-1.5 rounded-lg transition flex items-center gap-1.5 font-medium font-mono"
            >
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              Explain
            </button>
          )}

          {onAskAI && (
            <button
              onClick={() => onAskAI("Investigate what factors changed to cause this hazard trajectory.", "investigation")}
              className="bg-purple-950/80 hover:bg-purple-900 text-purple-300 border border-purple-700/60 text-xs px-2.5 py-1.5 rounded-lg transition flex items-center gap-1.5 font-medium font-mono"
            >
              <Compass className="w-3.5 h-3.5 text-purple-400" />
              Investigate
            </button>
          )}

          {event && onOpenBroadcast && (
            <button
              onClick={() => onOpenBroadcast(event.id, location.id)}
              className="bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-700/60 text-xs px-2.5 py-1.5 rounded-lg transition flex items-center gap-1.5 font-medium font-mono"
            >
              <Radio className="w-3.5 h-3.5 text-amber-400" />
              Broadcast
            </button>
          )}

          {event && onOpenSitRep && (
            <button
              onClick={() => onOpenSitRep(event.id)}
              className="bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-700 text-xs px-2.5 py-1.5 rounded-lg transition flex items-center gap-1.5 font-medium font-mono"
            >
              <FileText className="w-3.5 h-3.5 text-orange-400" />
              SitRep
            </button>
          )}

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
            className="bg-indigo-600/90 hover:bg-indigo-500 text-white text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 font-medium shadow-sm font-mono"
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
            <Gauge className="w-3 h-3 text-indigo-400" />
          </div>
          <div className="text-base font-bold text-slate-100 mt-1">
            {(confidenceScore * 100).toFixed(0)}%
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            {confidenceScore >= 0.8 ? "High Signal Agreement" : "Partial Sensor Agreement"}
          </p>
        </div>

        {/* Data Quality Status */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase">
            <span>Data Assurance</span>
            <Shield className="w-3 h-3 text-emerald-400" />
          </div>
          <div className="text-base font-bold text-slate-100 mt-1">
            {dataQuality?.status || "VALID"}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Completeness: {((dataQuality?.completeness_score ?? 1) * 100).toFixed(0)}%
          </p>
        </div>

        {/* Signal Coherence Level */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase">
            <span>Signal Coherence</span>
            <Layers className="w-3 h-3 text-purple-400" />
          </div>
          <div className="text-base font-bold text-slate-100 mt-1">
            {signalAgreement?.agreement_level || "COHERENT"}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Score: {((signalAgreement?.agreement_score ?? 0.85) * 100).toFixed(0)}%
          </p>
        </div>

        {/* Event Evolution (Peak vs Current) */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase">
            <span>Event Evolution</span>
            <Clock className="w-3 h-3 text-orange-400" />
          </div>
          <div className="text-base font-bold text-slate-100 mt-1">
            {event?.peak_risk ? `${event.peak_risk.toFixed(0)} Peak` : `${riskScore.toFixed(0)} Current`}
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            Initial: {event?.initial_risk ? event.initial_risk.toFixed(0) : riskScore.toFixed(0)}
          </p>
        </div>
      </div>

      {/* Reason Codes Badge Bar */}
      {reasonCodes.length > 0 && (
        <div className="space-y-1.5 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
          <div className="text-[10px] font-mono uppercase text-slate-400 font-bold flex items-center gap-1.5">
            <Info className="w-3 h-3 text-indigo-400" />
            Machine Reason Codes:
          </div>
          <div className="flex flex-wrap gap-1.5">
            {reasonCodes.map((code) => (
              <span
                key={code}
                className="bg-indigo-950/70 border border-indigo-800 text-indigo-300 text-[10px] font-mono px-2 py-0.5 rounded-md font-semibold"
              >
                {code}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Normalized Factor Breakdown Table */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            Normalized Factor Attribution (0.0 to 1.0)
          </h3>
          <span className="text-[10px] font-mono text-slate-500">
            Total Score: <strong className="text-slate-200">{riskScore.toFixed(1)} / 100</strong>
          </span>
        </div>

        {factors.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 text-[10px] uppercase">
                <tr>
                  <th className="px-3 py-2">Indicator</th>
                  <th className="px-3 py-2">Measured Telemetry</th>
                  <th className="px-3 py-2">0–1 Score</th>
                  <th className="px-3 py-2">Weight</th>
                  <th className="px-3 py-2">Contribution</th>
                  <th className="px-3 py-2">Hazard State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                {factors.map((f) => (
                  <tr key={f.name} className="hover:bg-slate-900/60 transition">
                    <td className="px-3 py-2 text-slate-200 font-medium capitalize">
                      {f.name.replace(/_/g, " ")}
                    </td>
                    <td className="px-3 py-2 text-slate-400">
                      {typeof f.raw_value === "number" ? f.raw_value.toFixed(1) : String(f.raw_value)}
                    </td>
                    <td className="px-3 py-2 text-slate-300">
                      <div className="flex items-center gap-1.5">
                        <div className="w-12 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-indigo-500 h-full rounded-full"
                            style={{ width: `${Math.min(100, f.normalized_score * 100)}%` }}
                          />
                        </div>
                        <span>{(f.normalized_score ?? 0).toFixed(2)}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-slate-400">{(f.weight * 100).toFixed(0)}%</td>
                    <td className="px-3 py-2 font-bold text-indigo-300">
                      +{f.contribution.toFixed(1)} pts
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                          f.status === "CRITICAL"
                            ? "bg-red-950 text-red-400 border border-red-800"
                            : f.status === "HIGH"
                            ? "bg-orange-950 text-orange-400 border border-orange-800"
                            : f.status === "MODERATE"
                            ? "bg-yellow-950 text-yellow-400 border border-yellow-800"
                            : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                        }`}
                      >
                        {f.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-xs text-slate-500 font-mono italic">
            No factor breakdown available for this evaluation.
          </div>
        )}
      </div>

      {/* Analytical Diagnostic Prose */}
      {latestAssessment?.reason && (
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3 space-y-1">
          <div className="text-[10px] font-mono uppercase text-slate-400 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Disaster Engine Synthesis:
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            {latestAssessment.reason}
          </p>
        </div>
      )}
    </div>
  );
}
