"use client";

import React from "react";
import {
  DisasterEventItem,
  RiskAssessmentItem,
  WeatherObservationItem,
  EventTimelineMilestoneItem,
} from "./types";
import {
  TrendingUp,
  TrendingDown,
  Layers,
  Check,
  ExternalLink,
  CheckCircle2,
  Minus,
  FileText,
  Radio,
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
  onExplainAssessment?: () => void;
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
  onExplainAssessment,
  onOpenBroadcast,
  onOpenSitRep,
}: EventDetailPanelProps) {
  if (!location) {
    return (
      <div className="bg-zinc-950 border border-zinc-800 rounded p-6 text-center text-zinc-500 font-mono text-xs flex flex-col items-center justify-center gap-2">
        Select a station on the tactical map or active event queue to inspect factor diagnostics.
      </div>
    );
  }

  const riskScore = latestAssessment?.risk_score ?? 0;
  const riskLevel = latestAssessment?.risk_level ?? "LOW";
  const confidenceScore = latestAssessment?.confidence_score ?? 0.8;
  const trajectory = latestAssessment?.trajectory ?? "STABLE";
  const factors = latestAssessment?.factors ?? [];
  const dataQuality = latestAssessment?.data_quality;
  const signalAgreement = latestAssessment?.signal_agreement;

  const isCritical = riskLevel === "CRITICAL" || riskScore >= 75;
  const isHigh = riskLevel === "HIGH" || (riskScore >= 50 && riskScore < 75);
  const isModerate = riskLevel === "MODERATE" || (riskScore >= 25 && riskScore < 50);

  const getTrajectoryBadge = (traj: string) => {
    switch (traj) {
      case "INCREASING":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-black font-mono bg-red-950 text-red-300 border border-red-700">
            <TrendingUp className="w-3 h-3" /> ↑ INCREASING
          </span>
        );
      case "DECREASING":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-black font-mono bg-emerald-950 text-emerald-300 border border-emerald-700">
            <TrendingDown className="w-3 h-3" /> ↓ DECREASING
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-zinc-900 text-zinc-300 border border-zinc-750">
            <Minus className="w-3 h-3" /> → STABLE
          </span>
        );
    }
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded p-4 space-y-4 font-sans text-white">
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-800">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 font-bold">
              Station Sector:
            </span>
            <h2 className="text-base font-black text-white font-mono tracking-tight">{location.name}</h2>
            <span className="text-xs text-zinc-400 font-mono">
              ({location.district}, {location.state})
            </span>
          </div>

          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-black font-mono uppercase ${
                isCritical
                  ? "bg-red-950 text-red-300 border border-red-700"
                  : isHigh
                  ? "bg-orange-950 text-orange-300 border border-orange-700"
                  : isModerate
                  ? "bg-amber-950 text-amber-300 border border-amber-700"
                  : "bg-emerald-950 text-emerald-300 border border-emerald-700"
              }`}
            >
              {riskLevel} RISK ({riskScore.toFixed(1)} / 100)
            </span>

            {/* Trajectory */}
            {getTrajectoryBadge(trajectory)}

            {/* Event Lifecycle Badge */}
            {event && event.status !== "RESOLVED" && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-black text-orange-400 border border-orange-700">
                Incident [{event.status}]
              </span>
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
          <button
            onClick={() => onOpenInvestigate(location.id)}
            className="bg-white hover:bg-zinc-200 text-black font-black px-3 py-1.5 rounded transition flex items-center gap-1.5 shadow-sm"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Station 360
          </button>

          {onExplainAssessment && (
            <button
              onClick={onExplainAssessment}
              className="bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 font-bold px-3 py-1.5 rounded transition flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5 text-zinc-400" />
              Explain
            </button>
          )}

          {event && onOpenBroadcast && (
            <button
              onClick={() => onOpenBroadcast(event.id, location.id)}
              className="bg-amber-500 hover:bg-amber-400 text-black font-black px-3 py-1.5 rounded transition flex items-center gap-1.5 shadow-sm"
            >
              <Radio className="w-3.5 h-3.5" />
              Broadcast
            </button>
          )}

          {event && onOpenSitRep && (
            <button
              onClick={() => onOpenSitRep(event.id)}
              className="bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 font-bold px-3 py-1.5 rounded transition flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5 text-zinc-400" />
              NDMA SitRep
            </button>
          )}

          {event && event.status === "ACTIVE" && (
            <button
              onClick={() => onAcknowledgeEvent(event.id)}
              disabled={isAcknowledging}
              className="bg-zinc-800 hover:bg-zinc-700 text-white font-bold border border-zinc-650 px-3 py-1.5 rounded transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              {isAcknowledging ? "Acking..." : "Acknowledge"}
            </button>
          )}
        </div>
      </div>

      {/* Primary Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-mono">
        <div className="bg-black p-2.5 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase font-bold">Assessment Confidence</div>
          <div className="text-sm font-black text-white mt-0.5">
            {(confidenceScore * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-zinc-500">Multi-factor density</div>
        </div>

        <div className="bg-black p-2.5 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase font-bold">Signal Agreement</div>
          <div className="text-sm font-black text-white mt-0.5">
            {signalAgreement?.agreement_level || "STRONG"}
          </div>
          <div className="text-[10px] text-zinc-500">
            Score: {((signalAgreement?.agreement_score ?? 0.85) * 100).toFixed(0)}%
          </div>
        </div>

        <div className="bg-black p-2.5 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase font-bold">Data Completeness</div>
          <div className="text-sm font-black text-white mt-0.5">
            {((dataQuality?.completeness_score ?? 1.0) * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-zinc-500">{dataQuality?.status || "HEALTHY"}</div>
        </div>

        <div className="bg-black p-2.5 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase font-bold">Terrain Geometry</div>
          <div className="text-sm font-black text-white mt-0.5">
            {location.slope_angle}° Slope
          </div>
          <div className="text-[10px] text-zinc-500">Elev: {location.elevation} m</div>
        </div>
      </div>

      {/* Normalized Factor Breakdown Table */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-300 font-black flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-zinc-400" />
            Normalized Factor Attribution (0.0 to 1.0)
          </h3>
          <span className="text-[10px] font-mono text-zinc-500">
            Total Score: <strong className="text-white font-bold">{riskScore.toFixed(1)} / 100</strong>
          </span>
        </div>

        {factors.length > 0 ? (
          <div className="overflow-x-auto rounded border border-zinc-800 bg-black">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-zinc-900 text-zinc-400 border-b border-zinc-800 text-[10px] uppercase font-bold">
                <tr>
                  <th className="px-3 py-2">Indicator</th>
                  <th className="px-3 py-2">Measured Telemetry</th>
                  <th className="px-3 py-2">0–1 Score</th>
                  <th className="px-3 py-2">Weight</th>
                  <th className="px-3 py-2">Contribution</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-850">
                {factors.map((f) => (
                  <tr key={f.name} className="hover:bg-zinc-900/50 transition">
                    <td className="px-3 py-2 text-zinc-200 font-bold capitalize">
                      {f.name.replace(/_/g, " ")}
                    </td>
                    <td className="px-3 py-2 text-zinc-400">
                      {typeof f.raw_value === "number" ? f.raw_value.toFixed(1) : String(f.raw_value)}
                    </td>
                    <td className="px-3 py-2 text-zinc-300 font-bold">
                      {(f.normalized_score ?? 0).toFixed(2)}
                    </td>
                    <td className="px-3 py-2 text-zinc-400">{(f.weight * 100).toFixed(0)}%</td>
                    <td className="px-3 py-2 font-black text-white">
                      +{f.contribution.toFixed(1)} pts
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`text-[9px] px-1.5 py-0.2 rounded font-black uppercase ${
                          f.status === "CRITICAL"
                            ? "bg-red-950 text-red-300 border border-red-700"
                            : f.status === "HIGH"
                            ? "bg-orange-950 text-orange-300 border border-orange-700"
                            : f.status === "MODERATE"
                            ? "bg-amber-950 text-amber-300 border border-amber-700"
                            : "bg-emerald-950 text-emerald-300 border border-emerald-700"
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
          <div className="text-xs text-zinc-500 font-mono italic">
            No factor breakdown available for this evaluation.
          </div>
        )}
      </div>

      {/* Analytical Diagnostic Prose */}
      {latestAssessment?.reason && (
        <div className="bg-black border border-zinc-800 rounded p-3 space-y-1">
          <div className="text-[10px] font-mono uppercase text-zinc-400 font-black flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Deterministic Assessment Synthesis:
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed font-sans">
            {latestAssessment.reason}
          </p>
        </div>
      )}
    </div>
  );
}
