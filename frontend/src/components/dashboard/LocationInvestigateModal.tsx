"use client";

import React, { useEffect, useState, useMemo } from "react";
import { ScientificInvestigationData, IDCurvePoint } from "@/components/dashboard/types";
import {
  X, Mountain, Droplets, Wind, ShieldAlert, Loader2,
  TrendingUp, TrendingDown, Minus, Info, AlertTriangle, CheckCircle2,
  Layers, Compass, Gauge, Clock, BarChart3, CloudRain, Activity,
  Database, HelpCircle, ArrowUpRight, ArrowDownRight, ExternalLink
} from "lucide-react";

interface LocationInvestigateModalProps {
  locationId: string | null;
  apiUrl: string;
  onClose: () => void;
}

type TabType = "overview" | "rainfall" | "soil" | "timeline" | "evidence" | "provenance";

export default function LocationInvestigateModal({
  locationId,
  apiUrl,
  onClose,
}: LocationInvestigateModalProps) {
  const [data, setData] = useState<ScientificInvestigationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("overview");

  // Timeline series toggles
  const [showRainfall, setShowRainfall] = useState<boolean>(true);
  const [showRain24h, setShowRain24h] = useState<boolean>(true);
  const [showSoil, setShowSoil] = useState<boolean>(true);
  const [showRisk, setShowRisk] = useState<boolean>(true);
  const [showConfidence, setShowConfidence] = useState<boolean>(false);

  // Selected timeline point for inspection
  const [selectedTimelineIndex, setSelectedTimelineIndex] = useState<number | null>(null);

  useEffect(() => {
    if (!locationId) return;

    const fetchInvestigation = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiUrl}/api/v1/locations/${locationId}/scientific-analysis`);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const result = await res.json();
        setData(result);
      } catch (err: any) {
        setError(err.message || "Failed to load scientific investigation payload");
      } finally {
        setLoading(false);
      }
    };

    fetchInvestigation();
  }, [locationId, apiUrl]);

  if (!locationId) return null;

  return (
    <div className="fixed inset-0 z-[2000] bg-black/85 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-6xl max-h-[94vh] shadow-2xl flex flex-col overflow-hidden my-auto">
        
        {/* ====================================================================== */}
        {/* 1. TOP HEADER & SCIENTIFIC STATION ASSESSMENT SUMMARY */}
        {/* ====================================================================== */}
        <div className="p-4 sm:p-5 border-b border-slate-800 bg-slate-950/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 sticky top-0 z-20 backdrop-blur-md">
          <div className="flex items-start sm:items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center shrink-0">
              <Mountain className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-widest text-indigo-400 font-bold bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/50">
                  Scientific Hydro-Terrain Workspace
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Station ID: {data?.station.id || locationId}
                </span>
              </div>
              <h2 className="text-lg font-bold text-slate-100 mt-0.5 flex items-center gap-2">
                {data ? data.station.name : "Retrieving Station Telemetry..."}
                {data && (
                  <span className="text-xs font-normal text-slate-400">
                    ({data.station.district}, {data.station.state})
                  </span>
                )}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            {data && (
              <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-slate-300">{data.data_mode} DATA</span>
              </div>
            )}
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-200 p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 transition"
              title="Close Workspace"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* ====================================================================== */}
        {/* 2. STATION METADATA & PROTOTYPE RISK INDEX BANNER */}
        {/* ====================================================================== */}
        {data && (
          <div className="bg-slate-950/90 px-5 py-3 border-b border-slate-800/80 grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Coordinates &amp; Elev</div>
              <div className="font-mono text-slate-200 font-medium mt-0.5">
                {data.station.latitude.toFixed(4)}°N, {data.station.longitude.toFixed(4)}°E
              </div>
              <div className="text-[11px] text-slate-400 font-mono">{data.station.elevation_m.toFixed(0)}m elevation</div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Prototype Risk Index</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`px-2 py-0.5 rounded font-bold font-mono text-xs ${
                  data.current_assessment.risk_level === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                  data.current_assessment.risk_level === 'HIGH' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                  data.current_assessment.risk_level === 'MODERATE' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40' :
                  'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                }`}>
                  {data.current_assessment.risk_level}
                </span>
                <span className="font-bold text-slate-100 font-mono text-sm">
                  {data.current_assessment.risk_score.toFixed(1)} <span className="text-slate-500 text-xs font-normal">/ 100</span>
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">{data.current_assessment.confidence_pct}% Conf</div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Risk Trajectory</div>
              <div className="font-mono font-medium text-slate-200 mt-0.5 flex items-center gap-1">
                {data.risk_trajectory.direction.includes('INCREASING') ? (
                  <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
                ) : data.risk_trajectory.direction.includes('DECREASING') ? (
                  <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Minus className="w-3.5 h-3.5 text-slate-400" />
                )}
                <span>{data.risk_trajectory.direction}</span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                {data.risk_trajectory.delta_6h >= 0 ? `+${data.risk_trajectory.delta_6h}` : data.risk_trajectory.delta_6h} pts / 6h
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Signal Agreement</div>
              <div className="font-mono font-medium text-indigo-300 mt-0.5">
                {data.hydrometeorological_state.signal_agreement_label}
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                {data.hydrometeorological_state.elevated_signals_count} of 6 factors elevated
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Slope Gradient &amp; Susc</div>
              <div className="font-mono text-slate-200 font-medium mt-0.5">
                {data.terrain.slope_angle_deg.toFixed(1)}° Slope
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                Susc: {data.terrain.historical_susceptibility_rating} ({data.terrain.terrain_susceptibility_score.toFixed(2)})
              </div>
            </div>
          </div>
        )}

        {/* ====================================================================== */}
        {/* 3. SCIENTIFIC WORKSPACE TABS */}
        {/* ====================================================================== */}
        <div className="bg-slate-950 px-5 border-b border-slate-800 flex items-center gap-1 overflow-x-auto text-xs font-mono scrollbar-none">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-3.5 py-2.5 border-b-2 font-medium flex items-center gap-1.5 transition whitespace-nowrap ${
              activeTab === "overview"
                ? "border-indigo-500 text-indigo-300 bg-slate-900/60"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            1. Scientific Overview
          </button>

          <button
            onClick={() => setActiveTab("rainfall")}
            className={`px-3.5 py-2.5 border-b-2 font-medium flex items-center gap-1.5 transition whitespace-nowrap ${
              activeTab === "rainfall"
                ? "border-indigo-500 text-indigo-300 bg-slate-900/60"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
            }`}
          >
            <CloudRain className="w-3.5 h-3.5" />
            2. Rainfall &amp; I-D Analysis
          </button>

          <button
            onClick={() => setActiveTab("soil")}
            className={`px-3.5 py-2.5 border-b-2 font-medium flex items-center gap-1.5 transition whitespace-nowrap ${
              activeTab === "soil"
                ? "border-indigo-500 text-indigo-300 bg-slate-900/60"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
            }`}
          >
            <Droplets className="w-3.5 h-3.5" />
            3. Soil Moisture Profile
          </button>

          <button
            onClick={() => setActiveTab("timeline")}
            className={`px-3.5 py-2.5 border-b-2 font-medium flex items-center gap-1.5 transition whitespace-nowrap ${
              activeTab === "timeline"
                ? "border-indigo-500 text-indigo-300 bg-slate-900/60"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            4. Aligned Risk Timeline
          </button>

          <button
            onClick={() => setActiveTab("evidence")}
            className={`px-3.5 py-2.5 border-b-2 font-medium flex items-center gap-1.5 transition whitespace-nowrap ${
              activeTab === "evidence"
                ? "border-indigo-500 text-indigo-300 bg-slate-900/60"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            5. Drivers &amp; Evidence
          </button>

          <button
            onClick={() => setActiveTab("provenance")}
            className={`px-3.5 py-2.5 border-b-2 font-medium flex items-center gap-1.5 transition whitespace-nowrap ${
              activeTab === "provenance"
                ? "border-indigo-500 text-indigo-300 bg-slate-900/60"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            6. Data Provenance
          </button>
        </div>

        {/* ====================================================================== */}
        {/* 4. MODAL CONTENT BODY */}
        {/* ====================================================================== */}
        <div className="p-5 sm:p-6 overflow-y-auto flex-1 bg-slate-900/50 space-y-6">
          {loading && (
            <div className="py-24 flex flex-col items-center justify-center text-slate-400 gap-3">
              <Loader2 className="w-9 h-9 animate-spin text-indigo-500" />
              <span className="text-xs font-mono">Executing hydro-meteorological indicators &amp; I-D analysis...</span>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-950/50 border border-red-800 rounded-xl text-red-300 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
              <div>
                <div className="font-bold">Investigation Retrieval Error</div>
                <div className="mt-0.5 font-mono text-[11px]">{error}</div>
              </div>
            </div>
          )}

          {data && !loading && (
            <>
              {/* ============================================================== */}
              {/* TAB 1: SCIENTIFIC OVERVIEW */}
              {/* ============================================================== */}
              {activeTab === "overview" && (
                <div className="space-y-6">
                  {/* Synthesis Alert Banner */}
                  <div className="bg-gradient-to-r from-slate-950 to-indigo-950/30 border border-indigo-900/40 rounded-xl p-4 flex items-start gap-3.5">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shrink-0 mt-0.5">
                      <Activity className="w-4 h-4 text-indigo-400" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-indigo-200">
                        Hydro-Meteorological Synthesis &amp; Multi-Signal Agreement
                      </div>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                        {data.hydrometeorological_state.synthesis_summary}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2 text-[11px] font-mono">
                        <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                          Precip Intensity: <strong className="text-amber-400">{data.rainfall.intensity.classification}</strong> ({data.rainfall.intensity.current_intensity_mm_h} mm/h)
                        </span>
                        <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                          Persistence: <strong className="text-amber-400">{data.rainfall.persistence.persistence_level}</strong> ({data.rainfall.persistence.current_wet_spell_hours}h spell)
                        </span>
                        <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                          Soil Wetness: <strong className="text-amber-400">{data.soil_moisture.percentile.status_label}</strong> ({data.soil_moisture.current_composite_pct}%)
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Core 4-Quad Indicator Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Quad 1: Rainfall Intensity */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between text-slate-400 text-xs">
                          <span className="font-mono uppercase text-[10px]">Rainfall Intensity</span>
                          <CloudRain className="w-4 h-4 text-blue-400" />
                        </div>
                        <div className="text-2xl font-bold text-slate-100 font-mono mt-2">
                          {data.rainfall.intensity.current_intensity_mm_h.toFixed(1)}{" "}
                          <span className="text-xs font-normal text-slate-500 font-sans">mm/h</span>
                        </div>
                        <div className="mt-1 flex items-center gap-1.5">
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded font-mono ${
                            data.rainfall.intensity.classification === 'EXTREME' || data.rainfall.intensity.classification === 'HEAVY'
                              ? 'bg-red-500/20 text-red-400'
                              : data.rainfall.intensity.classification === 'MODERATE'
                              ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-emerald-500/20 text-emerald-400'
                          }`}>
                            {data.rainfall.intensity.classification}
                          </span>
                          <span className="text-[11px] text-slate-400 font-mono">
                            6h avg: {data.rainfall.intensity.intensity_6h_avg_mm_h.toFixed(1)} mm/h
                          </span>
                        </div>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-3 pt-2 border-t border-slate-900 leading-tight">
                        Rate of recent hourly precipitation burst.
                      </div>
                    </div>

                    {/* Quad 2: 24h Accumulation */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between text-slate-400 text-xs">
                          <span className="font-mono uppercase text-[10px]">24h Cumulative Rain</span>
                          <Layers className="w-4 h-4 text-cyan-400" />
                        </div>
                        <div className="text-2xl font-bold text-slate-100 font-mono mt-2">
                          {data.rainfall.anomaly.current_24h_mm.toFixed(1)}{" "}
                          <span className="text-xs font-normal text-slate-500 font-sans">mm</span>
                        </div>
                        <div className="mt-1 flex items-center gap-1.5">
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded font-mono ${
                            data.rainfall.anomaly.anomaly_status.includes('ABNORMAL') || data.rainfall.anomaly.anomaly_status.includes('UNUSUAL')
                              ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-emerald-500/20 text-emerald-400'
                          }`}>
                            {data.rainfall.anomaly.z_score >= 0 ? `+${data.rainfall.anomaly.z_score.toFixed(1)}σ` : `${data.rainfall.anomaly.z_score.toFixed(1)}σ`}
                          </span>
                          <span className="text-[11px] text-slate-400 font-mono">
                            {data.rainfall.anomaly.deviation_mm >= 0 ? `+${data.rainfall.anomaly.deviation_mm.toFixed(0)}mm vs base` : `${data.rainfall.anomaly.deviation_mm.toFixed(0)}mm vs base`}
                          </span>
                        </div>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-3 pt-2 border-t border-slate-900 leading-tight">
                        Baseline: {data.rainfall.anomaly.baseline_24h_mm}mm reference.
                      </div>
                    </div>

                    {/* Quad 3: Soil Moisture */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between text-slate-400 text-xs">
                          <span className="font-mono uppercase text-[10px]">Volumetric Soil Moisture</span>
                          <Droplets className="w-4 h-4 text-emerald-400" />
                        </div>
                        <div className="text-2xl font-bold text-slate-100 font-mono mt-2">
                          {data.soil_moisture.current_composite_pct.toFixed(1)}{" "}
                          <span className="text-xs font-normal text-slate-500 font-sans">%</span>
                        </div>
                        <div className="mt-1 flex items-center gap-1.5">
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded font-mono bg-emerald-500/20 text-emerald-400">
                            {data.soil_moisture.percentile.historical_percentile}th %ile
                          </span>
                          <span className="text-[11px] text-slate-300 font-mono">
                            {data.soil_moisture.percentile.status_label}
                          </span>
                        </div>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-3 pt-2 border-t border-slate-900 leading-tight">
                        Trend: {data.soil_moisture.trend.direction} ({data.soil_moisture.trend.delta_6h_pct >= 0 ? `+${data.soil_moisture.trend.delta_6h_pct}` : data.soil_moisture.trend.delta_6h_pct}% / 6h).
                      </div>
                    </div>

                    {/* Quad 4: Intensity-Duration Status */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between text-slate-400 text-xs">
                          <span className="font-mono uppercase text-[10px]">I-D Threshold Curve</span>
                          <Gauge className="w-4 h-4 text-purple-400" />
                        </div>
                        <div className="text-base font-bold text-slate-100 font-mono mt-2 flex items-center gap-1">
                          {data.rainfall.intensity_duration.is_above_prototype_threshold ? (
                            <span className="text-red-400">EXCEEDED</span>
                          ) : (
                            <span className="text-emerald-400">WITHIN LIMITS</span>
                          )}
                        </div>
                        <div className="mt-1 text-[11px] text-slate-300 font-mono">
                          {data.rainfall.intensity_duration.cumulative_rainfall_mm.toFixed(0)}mm over {data.rainfall.intensity_duration.active_duration_hours.toFixed(0)}h
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Ref Thresh: {data.rainfall.intensity_duration.prototype_threshold_rainfall_mm.toFixed(0)}mm
                        </div>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-3 pt-2 border-t border-slate-900 leading-tight">
                        Prototype empirical I-D reference curve.
                      </div>
                    </div>
                  </div>

                  {/* 24-Hour Forward Forecast & Outlook */}
                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-indigo-400" />
                        <h3 className="text-xs font-bold text-slate-200 uppercase font-mono tracking-wider">
                          {data.forecast.forecast_period_label}
                        </h3>
                      </div>
                      <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/50">
                        {data.forecast.provenance_note}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 text-xs font-mono">
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                        <div className="text-slate-500 text-[10px]">Expected 24h Rain</div>
                        <div className="text-base font-bold text-slate-200 mt-1">
                          ~{data.forecast.expected_rainfall_24h_mm.toFixed(1)} mm
                        </div>
                      </div>

                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                        <div className="text-slate-500 text-[10px]">Expected Wet Hours</div>
                        <div className="text-base font-bold text-slate-200 mt-1">
                          {data.forecast.expected_wet_hours_24h} / 24 hours
                        </div>
                      </div>

                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                        <div className="text-slate-500 text-[10px]">Peak Hourly Rate</div>
                        <div className="text-base font-bold text-slate-200 mt-1">
                          {data.forecast.expected_max_hourly_mm.toFixed(1)} mm/h
                        </div>
                      </div>

                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                        <div className="text-slate-500 text-[10px]">Projected Risk Trend</div>
                        <div className="text-xs font-bold text-indigo-300 mt-1">
                          {data.forecast.projected_risk_trajectory}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ============================================================== */}
              {/* TAB 2: RAINFALL & INTENSITY-DURATION ANALYSIS */}
              {/* ============================================================== */}
              {activeTab === "rainfall" && (
                <div className="space-y-6">
                  {/* Short Duration Accumulation Table & Wet Spell Persistence */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* Left: Accumulation Table */}
                    <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                          <div className="flex items-center gap-2">
                            <Layers className="w-4 h-4 text-blue-400" />
                            <h3 className="text-xs font-bold text-slate-200 uppercase font-mono">
                              Short-Duration Rolling Accumulation
                            </h3>
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono">Rolling Windows</span>
                        </div>

                        <div className="mt-4 overflow-hidden rounded-lg border border-slate-800">
                          <table className="w-full text-left text-xs font-mono">
                            <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase">
                              <tr>
                                <th className="p-2.5">Window Period</th>
                                <th className="p-2.5 text-right">Rainfall (mm)</th>
                                <th className="p-2.5 text-right">Status</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/70 text-slate-300">
                              {data.rainfall.short_duration_table.map((item, idx) => (
                                <tr key={idx} className="hover:bg-slate-900/40">
                                  <td className="p-2.5 font-medium text-slate-200">{item.period}</td>
                                  <td className="p-2.5 text-right font-bold text-slate-100">
                                    {item.has_data && item.rainfall_mm !== null ? `${item.rainfall_mm.toFixed(1)} mm` : "Insufficient data"}
                                  </td>
                                  <td className="p-2.5 text-right">
                                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                                      item.status_label.includes("Critical") ? "bg-red-500/20 text-red-400" :
                                      item.status_label.includes("Above") ? "bg-amber-500/20 text-amber-400" :
                                      item.status_label.includes("Elevated") ? "bg-yellow-500/20 text-yellow-400" :
                                      item.status_label === "Insufficient data" ? "bg-slate-800 text-slate-500" :
                                      "bg-emerald-500/20 text-emerald-400"
                                    }`}>
                                      {item.status_label}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      <div className="text-[10px] text-slate-500 mt-4 leading-tight">
                        Rolling calculations over contiguous hourly precipitation records.
                      </div>
                    </div>

                    {/* Right: Persistence & Antecedent Hydrologic Loading */}
                    <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 flex flex-col justify-between space-y-5">
                      {/* Persistence Card */}
                      <div>
                        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4 text-amber-400" />
                            <h3 className="text-xs font-bold text-slate-200 uppercase font-mono">
                              Rainfall Persistence Spell
                            </h3>
                          </div>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                            data.rainfall.persistence.persistence_level === 'CRITICAL' || data.rainfall.persistence.persistence_level === 'HIGH'
                              ? 'bg-red-500/20 text-red-400'
                              : 'bg-emerald-500/20 text-emerald-400'
                          }`}>
                            {data.rainfall.persistence.persistence_level} PERSISTENCE
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-3 mt-4 text-xs font-mono">
                          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                            <div className="text-slate-500 text-[10px]">Current Wet Spell</div>
                            <div className="text-lg font-bold text-amber-400 mt-1">
                              {data.rainfall.persistence.current_wet_spell_hours} hours
                            </div>
                          </div>
                          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                            <div className="text-slate-500 text-[10px]">Wet Hours (Last 12h)</div>
                            <div className="text-lg font-bold text-slate-200 mt-1">
                              {data.rainfall.persistence.wet_hours_last_12h} / 12h
                            </div>
                          </div>
                          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                            <div className="text-slate-500 text-[10px]">Wet Hours (Last 24h)</div>
                            <div className="text-lg font-bold text-slate-200 mt-1">
                              {data.rainfall.persistence.wet_hours_last_24h} / 24h
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Antecedent Pre-event Wetness */}
                      <div>
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <span className="text-xs font-bold text-slate-300 font-mono uppercase">
                            Antecedent Rainfall / Pre-Event Wetness
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {data.rainfall.antecedent.loading_classification} LOADING
                          </span>
                        </div>

                        <div className="grid grid-cols-4 gap-2 mt-3 text-xs font-mono text-center">
                          <div className="bg-slate-900/40 p-2 rounded border border-slate-800/50">
                            <div className="text-[9px] text-slate-500">24h Pre-event</div>
                            <div className="font-bold text-slate-200 mt-0.5">
                              {data.rainfall.antecedent.antecedent_24h_mm !== null ? `${data.rainfall.antecedent.antecedent_24h_mm} mm` : "N/A"}
                            </div>
                          </div>
                          <div className="bg-slate-900/40 p-2 rounded border border-slate-800/50">
                            <div className="text-[9px] text-slate-500">48h Pre-event</div>
                            <div className="font-bold text-slate-200 mt-0.5">
                              {data.rainfall.antecedent.antecedent_48h_mm !== null ? `${data.rainfall.antecedent.antecedent_48h_mm} mm` : "N/A"}
                            </div>
                          </div>
                          <div className="bg-slate-900/40 p-2 rounded border border-slate-800/50">
                            <div className="text-[9px] text-slate-500">72h Pre-event</div>
                            <div className="font-bold text-slate-200 mt-0.5">
                              {data.rainfall.antecedent.antecedent_72h_mm !== null ? `${data.rainfall.antecedent.antecedent_72h_mm} mm` : "N/A"}
                            </div>
                          </div>
                          <div className="bg-slate-900/40 p-2 rounded border border-slate-800/50">
                            <div className="text-[9px] text-slate-500">7-Day Cumulative</div>
                            <div className="font-bold text-slate-200 mt-0.5">
                              {data.rainfall.antecedent.antecedent_7d_mm !== null ? `${data.rainfall.antecedent.antecedent_7d_mm} mm` : "N/A"}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Intensity-Duration (I-D) Threshold Curve Visualization */}
                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
                      <div className="flex items-center gap-2">
                        <Gauge className="w-4 h-4 text-purple-400" />
                        <div>
                          <h3 className="text-xs font-bold text-slate-200 uppercase font-mono">
                            Rainfall Intensity-Duration (I-D) Analysis
                          </h3>
                          <p className="text-[11px] text-slate-400">
                            Current Event ({data.rainfall.intensity_duration.active_duration_hours}h duration, {data.rainfall.intensity_duration.cumulative_rainfall_mm}mm rain) vs Prototype Curve
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold font-mono px-2.5 py-1 rounded border ${
                          data.rainfall.intensity_duration.is_above_prototype_threshold
                            ? "bg-red-500/20 text-red-400 border-red-500/40"
                            : "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                        }`}>
                          {data.rainfall.intensity_duration.status_text}
                        </span>
                      </div>
                    </div>

                    {/* I-D Step Comparison Visualizer */}
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-xs font-mono">
                      {data.rainfall.intensity_duration.reference_curve.map((pt, idx) => {
                        const isMatch = Math.abs(pt.duration_hours - data.rainfall.intensity_duration.active_duration_hours) <= 3;
                        return (
                          <div
                            key={idx}
                            className={`p-3 rounded-lg border flex flex-col justify-between ${
                              isMatch
                                ? "bg-indigo-950/60 border-indigo-500/60 ring-1 ring-indigo-500"
                                : "bg-slate-900/60 border-slate-800"
                            }`}
                          >
                            <div className="text-[10px] text-slate-400 font-bold">{pt.duration_hours}h Window</div>
                            <div className="text-base font-bold text-slate-200 my-1">
                              {pt.threshold_rainfall_mm} <span className="text-[10px] font-normal text-slate-500">mm</span>
                            </div>
                            <div className="text-[10px] text-slate-400">
                              {pt.critical_intensity_mm_h.toFixed(1)} mm/h crit
                            </div>
                            {isMatch && (
                              <div className="mt-2 text-[9px] font-bold text-indigo-300 bg-indigo-900/80 px-1 py-0.5 rounded text-center">
                                CURRENT EVENT
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    <div className="mt-4 p-3 bg-slate-900/40 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2">
                      <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                      <div>
                        <strong>Scientific Note:</strong> {data.rainfall.intensity_duration.disclaimer} Empirical power-law reference $I = 25.0 \cdot D^{'{'}-0.45{'}'}$ represents empirical landslide triggering conditions in steep Himalayan catchment areas.
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ============================================================== */}
              {/* TAB 3: SOIL MOISTURE PROFILE */}
              {/* ============================================================== */}
              {activeTab === "soil" && (
                <div className="space-y-6">
                  {/* Vertical Soil Moisture Depth Profile */}
                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-2">
                        <Droplets className="w-4 h-4 text-emerald-400" />
                        <div>
                          <h3 className="text-xs font-bold text-slate-200 uppercase font-mono">
                            Subsurface Vertical Soil Moisture Profile
                          </h3>
                          <p className="text-[11px] text-slate-400">
                            Multi-depth volumetric water retention ($m^3/m^3$) &amp; saturation gradient
                          </p>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/50">
                        {data.soil_moisture.measurement_type}
                      </span>
                    </div>

                    <div className="mt-5 space-y-4 font-mono text-xs">
                      {data.soil_moisture.vertical_profile.map((layer, idx) => (
                        <div key={idx} className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/70">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-bold text-slate-100">{layer.depth_range}</span>
                              <span className="text-slate-400 text-xs font-sans">({layer.depth_label})</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className="text-slate-400 text-[11px]">{layer.volumetric_m3_m3} m³/m³</span>
                              <span className="text-sm font-bold text-emerald-400">{layer.moisture_pct}%</span>
                              <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                                layer.relative_wetness === 'HIGH' || layer.relative_wetness === 'VERY_HIGH'
                                  ? 'bg-red-500/20 text-red-400'
                                  : layer.relative_wetness === 'ELEVATED'
                                  ? 'bg-amber-500/20 text-amber-400'
                                  : 'bg-emerald-500/20 text-emerald-400'
                              }`}>
                                {layer.relative_wetness}
                              </span>
                            </div>
                          </div>

                          {/* Progress Gauge Bar */}
                          <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800 p-0.5">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-teal-400 to-indigo-500 transition-all duration-500"
                              style={{ width: `${Math.min(100, Math.max(5, layer.bar_fill_pct))}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="mt-5 p-3 bg-slate-900/40 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2">
                      <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                      <div>
                        <strong>Scientific Disclaimer:</strong> {data.soil_moisture.disclaimer} Deep bedrock hydrological pore pressure is estimated from numerical infiltration models rather than direct in-situ piezometers.
                      </div>
                    </div>
                  </div>

                  {/* Infiltration Trends & Seasonal Percentile */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                      <div className="text-slate-500 text-[10px] uppercase">Soil Moisture Infiltration Velocity</div>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-base font-bold text-slate-100">
                          {data.soil_moisture.trend.delta_6h_pct >= 0 ? `+${data.soil_moisture.trend.delta_6h_pct}%` : `${data.soil_moisture.trend.delta_6h_pct}%`}
                        </span>
                        <span className="text-xs text-slate-400">over last 6 hours</span>
                      </div>
                      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[11px]">
                        <div className="bg-slate-900 p-2 rounded border border-slate-800">
                          <div className="text-slate-500 text-[9px]">1h Delta</div>
                          <div className="font-bold text-slate-200 mt-0.5">{data.soil_moisture.trend.delta_1h_pct}%</div>
                        </div>
                        <div className="bg-slate-900 p-2 rounded border border-slate-800">
                          <div className="text-slate-500 text-[9px]">3h Delta</div>
                          <div className="font-bold text-slate-200 mt-0.5">{data.soil_moisture.trend.delta_3h_pct}%</div>
                        </div>
                        <div className="bg-slate-900 p-2 rounded border border-slate-800">
                          <div className="text-slate-500 text-[9px]">24h Delta</div>
                          <div className="font-bold text-slate-200 mt-0.5">{data.soil_moisture.trend.delta_24h_pct}%</div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                      <div className="text-slate-500 text-[10px] uppercase">Seasonal Climatological Percentile</div>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-2xl font-bold text-indigo-400">{data.soil_moisture.percentile.historical_percentile}th</span>
                        <span className="text-xs font-bold text-slate-200">Percentile</span>
                      </div>
                      <p className="text-slate-400 text-[11px] mt-2 font-sans leading-relaxed">
                        Current subsurface soil wetness ranks in the upper {100 - data.soil_moisture.percentile.historical_percentile}% of historical seasonal observations for this sector.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* ============================================================== */}
              {/* TAB 4: ALIGNED RISK TIMELINE */}
              {/* ============================================================== */}
              {activeTab === "timeline" && (
                <div className="space-y-6">
                  {/* Timeline Chart Container */}
                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-3">
                      <div>
                        <h3 className="text-xs font-bold text-slate-200 uppercase font-mono">
                          Aligned Multi-Series Hydro-Risk Timeline
                        </h3>
                        <p className="text-[11px] text-slate-400">
                          Synchronous progression of precipitation rate, cumulative rainfall, soil saturation, and landslide risk score
                        </p>
                      </div>

                      {/* Interactive Series Toggle Checkboxes */}
                      <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
                        <label className="flex items-center gap-1.5 cursor-pointer text-blue-400 hover:text-blue-300">
                          <input
                            type="checkbox"
                            checked={showRainfall}
                            onChange={(e) => setShowRainfall(e.target.checked)}
                            className="rounded border-slate-700 bg-slate-900 text-blue-500"
                          />
                          <span>Rain Rate (mm/h)</span>
                        </label>

                        <label className="flex items-center gap-1.5 cursor-pointer text-cyan-400 hover:text-cyan-300">
                          <input
                            type="checkbox"
                            checked={showRain24h}
                            onChange={(e) => setShowRain24h(e.target.checked)}
                            className="rounded border-slate-700 bg-slate-900 text-cyan-500"
                          />
                          <span>24h Rain (mm)</span>
                        </label>

                        <label className="flex items-center gap-1.5 cursor-pointer text-emerald-400 hover:text-emerald-300">
                          <input
                            type="checkbox"
                            checked={showSoil}
                            onChange={(e) => setShowSoil(e.target.checked)}
                            className="rounded border-slate-700 bg-slate-900 text-emerald-500"
                          />
                          <span>Soil Moist (%)</span>
                        </label>

                        <label className="flex items-center gap-1.5 cursor-pointer text-amber-400 hover:text-amber-300">
                          <input
                            type="checkbox"
                            checked={showRisk}
                            onChange={(e) => setShowRisk(e.target.checked)}
                            className="rounded border-slate-700 bg-slate-900 text-amber-500"
                          />
                          <span>Risk Score (0-100)</span>
                        </label>
                      </div>
                    </div>

                    {/* Timeline Data Table & Visualization */}
                    <div className="mt-4 overflow-x-auto rounded-lg border border-slate-800">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase sticky top-0">
                          <tr>
                            <th className="p-2.5">Time</th>
                            {showRainfall && <th className="p-2.5 text-right text-blue-400">Rain Rate (mm/h)</th>}
                            {showRain24h && <th className="p-2.5 text-right text-cyan-400">24h Rain (mm)</th>}
                            {showSoil && <th className="p-2.5 text-right text-emerald-400">Soil Moisture</th>}
                            {showRisk && <th className="p-2.5 text-right text-amber-400">Risk Score</th>}
                            <th className="p-2.5">Milestone Markers</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 text-slate-300">
                          {data.timeline_series.map((pt, idx) => (
                            <tr
                              key={idx}
                              onClick={() => setSelectedTimelineIndex(idx)}
                              className={`cursor-pointer transition ${
                                selectedTimelineIndex === idx
                                  ? "bg-indigo-950/60 text-white"
                                  : "hover:bg-slate-900/50"
                              }`}
                            >
                              <td className="p-2.5 font-bold text-slate-300">{pt.timestamp_str}</td>
                              {showRainfall && (
                                <td className="p-2.5 text-right font-medium text-blue-300">
                                  {pt.rainfall_rate_mm_h.toFixed(1)}
                                </td>
                              )}
                              {showRain24h && (
                                <td className="p-2.5 text-right font-medium text-cyan-300">
                                  {pt.rainfall_24h_mm.toFixed(1)}
                                </td>
                              )}
                              {showSoil && (
                                <td className="p-2.5 text-right font-medium text-emerald-300">
                                  {pt.soil_moisture_pct.toFixed(1)}%
                                </td>
                              )}
                              {showRisk && (
                                <td className="p-2.5 text-right font-bold text-amber-400">
                                  {pt.risk_score.toFixed(1)}
                                </td>
                              )}
                              <td className="p-2.5">
                                {pt.event_marker ? (
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                                    {pt.event_marker}
                                  </span>
                                ) : (
                                  <span className="text-slate-600 text-[10px]">—</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* ============================================================== */}
              {/* TAB 5: DRIVERS & EVIDENCE SUMMARY */}
              {/* ============================================================== */}
              {activeTab === "evidence" && (
                <div className="space-y-6">
                  {/* Scientific Assessment Drivers Breakdown Table */}
                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
                    <div className="border-b border-slate-800 pb-3">
                      <h3 className="text-xs font-bold text-slate-200 uppercase font-mono">
                        Multi-Signal Assessment Mathematical Contributors
                      </h3>
                      <p className="text-[11px] text-slate-400">
                        Normalized factor weights and direct numerical score contributions
                      </p>
                    </div>

                    <div className="mt-4 overflow-hidden rounded-lg border border-slate-800">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase">
                          <tr>
                            <th className="p-2.5">Factor Description</th>
                            <th className="p-2.5">Classification</th>
                            <th className="p-2.5">Observed Sensor Value</th>
                            <th className="p-2.5 text-right">Points Added</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 text-slate-300">
                          {data.assessment_drivers.map((d, idx) => (
                            <tr key={idx} className="hover:bg-slate-900/40">
                              <td className="p-2.5 font-medium text-slate-200">{d.factor_name}</td>
                              <td className="p-2.5">
                                <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                                  d.level === 'CRITICAL' || d.level === 'High' || d.level === 'Very High'
                                    ? 'bg-red-500/20 text-red-400'
                                    : d.level === 'MODERATE' || d.level === 'Mod'
                                    ? 'bg-amber-500/20 text-amber-400'
                                    : 'bg-emerald-500/20 text-emerald-400'
                                }`}>
                                  {d.level}
                                </span>
                              </td>
                              <td className="p-2.5 text-slate-400">{d.measured_value_str}</td>
                              <td className="p-2.5 text-right font-bold text-amber-400">
                                +{d.contribution_points.toFixed(1)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Professional Evidence Summary 2-Column Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* Supporting Elevated Risk */}
                    <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
                      <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-bold uppercase border-b border-slate-800 pb-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Supporting Elevated Risk Factors</span>
                      </div>
                      <ul className="space-y-2 text-xs text-slate-300">
                        {data.evidence_summary.supporting_elevated_risk.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-emerald-400 mt-0.5">✓</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Limiting & Uncertain Factors */}
                    <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
                      <div className="flex items-center gap-2 text-amber-400 font-mono text-xs font-bold uppercase border-b border-slate-800 pb-2">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Limiting &amp; Uncertain Factors (Missing Data)</span>
                      </div>
                      <ul className="space-y-2 text-xs text-slate-300">
                        {data.evidence_summary.limiting_uncertain_factors.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-amber-400 mt-0.5">⚠</span>
                            <span>{item}</span>
                          </li>
                        ))}
                        {data.evidence_summary.missing_sensor_observations.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-slate-400">
                            <span className="text-red-400 mt-0.5">✗</span>
                            <span className="font-mono text-[11px]">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* ============================================================== */}
              {/* TAB 6: DATA PROVENANCE */}
              {/* ============================================================== */}
              {activeTab === "provenance" && (
                <div className="space-y-6">
                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
                    <div className="border-b border-slate-800 pb-3">
                      <h3 className="text-xs font-bold text-slate-200 uppercase font-mono">
                        Data Provenance &amp; Sensor Telemetry Audit
                      </h3>
                      <p className="text-[11px] text-slate-400">
                        Distinguishes observed, model-derived, simulated, and missing geotechnical observations
                      </p>
                    </div>

                    <div className="mt-4 overflow-hidden rounded-lg border border-slate-800">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase">
                          <tr>
                            <th className="p-2.5">Signal Stream</th>
                            <th className="p-2.5">Source Provider</th>
                            <th className="p-2.5">Category</th>
                            <th className="p-2.5">Obs Time</th>
                            <th className="p-2.5">Freshness</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 text-slate-300">
                          {data.provenance.map((p, idx) => (
                            <tr key={idx} className="hover:bg-slate-900/40">
                              <td className="p-2.5 font-bold text-slate-200">{p.signal_name}</td>
                              <td className="p-2.5 text-slate-300">{p.source_provider}</td>
                              <td className="p-2.5">
                                <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                                  p.data_category === 'OBSERVED' ? 'bg-emerald-500/20 text-emerald-400' :
                                  p.data_category === 'DERIVED' ? 'bg-blue-500/20 text-blue-400' :
                                  p.data_category === 'SIMULATED' ? 'bg-indigo-500/20 text-indigo-400' :
                                  'bg-red-500/20 text-red-400'
                                }`}>
                                  {p.data_category}
                                </span>
                              </td>
                              <td className="p-2.5 text-slate-400">{p.observation_time}</td>
                              <td className="p-2.5">
                                <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                  p.freshness_status === 'FRESH' ? 'text-emerald-400 bg-emerald-950/60' : 'text-amber-400 bg-amber-950/60'
                                }`}>
                                  {p.freshness_status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* ====================================================================== */}
        {/* 5. MODAL FOOTER */}
        {/* ====================================================================== */}
        <div className="p-3.5 px-5 border-t border-slate-800 bg-slate-950/90 flex items-center justify-between text-xs font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Operational Scientific Workspace v1.2</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition font-medium"
            >
              Close Investigation
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
