"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  ScientificInvestigationData,
  IDCurvePoint,
  TimelineSeriesItem,
  TriggerFactor,
  ConditioningFactor,
} from "@/components/dashboard/types";
import {
  X,
  Mountain,
  Droplets,
  Wind,
  ShieldAlert,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  Info,
  AlertTriangle,
  CheckCircle2,
  Layers,
  Compass,
  Gauge,
  Clock,
  BarChart3,
  CloudRain,
  Activity,
  Database,
  HelpCircle,
  ArrowUpRight,
  ArrowDownRight,
  ExternalLink,
  LocateFixed,
  Satellite,
  Radio,
} from "lucide-react";

interface LocationInvestigateModalProps {
  locationId: string | null;
  apiUrl: string;
  onClose: () => void;
}

type TabType = "overview" | "rainfall" | "soil" | "terrain" | "timeline" | "forecast" | "quality";

export default function LocationInvestigateModal({
  locationId,
  apiUrl,
  onClose,
}: LocationInvestigateModalProps) {
  const [data, setData] = useState<ScientificInvestigationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("overview");

  // Chart range & toggles
  const [rainfallRangeHours, setRainfallRangeHours] = useState<number>(24);
  const [selectedSoilDepth, setSelectedSoilDepth] = useState<string>("surface");
  const [hoveredTimelinePoint, setHoveredTimelinePoint] = useState<TimelineSeriesItem | null>(null);
  const [selectedTimelineIndex, setSelectedTimelineIndex] = useState<number | null>(null);

  // Multi-signal timeline series toggles
  const [showRainfallSignal, setShowRainfallSignal] = useState<boolean>(true);
  const [showSoilSignal, setShowSoilSignal] = useState<boolean>(true);
  const [showRiskSignal, setShowRiskSignal] = useState<boolean>(true);

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

  // Filtered timeline points based on selected range
  const timelinePoints = useMemo(() => {
    if (!data?.timeline_series) return [];
    return data.timeline_series;
  }, [data]);

  const observedPoints = useMemo(() => {
    return timelinePoints.filter((p) => p.is_observed);
  }, [timelinePoints]);

  const forecastPoints = useMemo(() => {
    return timelinePoints.filter((p) => !p.is_observed);
  }, [timelinePoints]);

  if (!locationId) return null;

  return (
    <div className="fixed inset-0 z-[2000] bg-black/85 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-6xl max-h-[94vh] shadow-2xl flex flex-col overflow-hidden my-auto font-sans">
        
        {/* ====================================================================== */}
        {/* 1. TOP HEADER & STATION IDENTITY */}
        {/* ====================================================================== */}
        <div className="p-3.5 sm:p-4 border-b border-slate-800 bg-slate-950/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3 sticky top-0 z-20 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center shrink-0">
              <Mountain className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-widest text-indigo-400 font-bold bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/50">
                  Station 360 Analytical Investigation
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Station ID: {data?.station.id || locationId}
                </span>
              </div>
              <h2 className="text-base sm:text-lg font-bold text-slate-100 mt-0.5 flex items-center gap-2">
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
              <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1 rounded-lg text-xs font-mono">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-slate-300">{data.data_mode} DATA</span>
              </div>
            )}
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 transition"
              title="Close Workspace"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* ====================================================================== */}
        {/* 2. STATS KPI STRIP */}
        {/* ====================================================================== */}
        {data && (
          <div className="bg-slate-950/90 px-4 py-2.5 border-b border-slate-800 grid grid-cols-2 md:grid-cols-5 gap-2.5 text-xs">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Coordinates &amp; Elev</div>
              <div className="font-mono text-slate-200 font-medium mt-0.5 text-xs">
                {data.station.latitude.toFixed(4)}°N, {data.station.longitude.toFixed(4)}°E
              </div>
              <div className="text-[10px] text-slate-400 font-mono">{(data.station.elevation_m ?? 1200).toFixed(0)}m elevation</div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Prototype Risk Index</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`px-2 py-0.2 rounded font-bold font-mono text-[11px] ${
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
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Signal Agreement</div>
              <div className="font-mono font-medium text-indigo-300 mt-0.5">
                {data.hydrometeorological_state.signal_agreement_label}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Slope Gradient &amp; Susc</div>
              <div className="font-mono text-slate-200 font-medium mt-0.5">
                {(data.terrain.slope_angle_deg ?? 30).toFixed(1)}° Slope
              </div>
              <div className="text-[10px] text-slate-400 font-mono">
                Susc: {data.terrain.historical_susceptibility_rating}
              </div>
            </div>
          </div>
        )}

        {/* ====================================================================== */}
        {/* 3. SCIENTIFIC WORKSPACE 7 TABS */}
        {/* ====================================================================== */}
        <div className="bg-slate-950 px-4 border-b border-slate-800 flex items-center gap-1 overflow-x-auto text-xs font-mono scrollbar-none">
          {[
            { id: "overview", label: "1. Overview", icon: Activity },
            { id: "rainfall", label: "2. Rainfall Timeline", icon: CloudRain },
            { id: "soil", label: "3. Soil Moisture", icon: Droplets },
            { id: "terrain", label: "4. Terrain", icon: Mountain },
            { id: "timeline", label: "5. Risk Timeline", icon: BarChart3 },
            { id: "forecast", label: "6. Forecast", icon: Clock },
            { id: "quality", label: "7. Data Quality & Uncertainty", icon: Database },
          ].map((tab) => {
            const active = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`px-3 py-2.5 border-b-2 font-medium flex items-center gap-1.5 transition whitespace-nowrap ${
                  active
                    ? "border-indigo-500 text-indigo-300 bg-slate-900/60"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ====================================================================== */}
        {/* 4. TAB CONTENT PANELS */}
        {/* ====================================================================== */}
        <div className="p-4 sm:p-5 overflow-y-auto flex-1 space-y-4 text-xs font-sans">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-2 text-slate-400 font-mono">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
              <span>Analyzing Station Telemetry...</span>
            </div>
          ) : error ? (
            <div className="p-6 bg-red-950/40 border border-red-800 rounded-xl text-center text-red-300 font-mono">
              {error}
            </div>
          ) : data ? (
            <>
              {/* --- TAB 1: OVERVIEW --- */}
              {activeTab === "overview" && (
                <div className="space-y-4">
                  {/* Top Key Metrics Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase">Current Rainfall Rate</div>
                      <div className="text-lg font-bold text-indigo-300">
                        {data.rainfall.intensity.current_intensity_mm_h} <span className="text-xs font-normal">mm/h</span>
                      </div>
                      <div className="text-[10px] text-slate-500">
                        {data.rainfall.intensity.classification} intensity
                      </div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-md border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase">24h Rainfall Accumulation</div>
                      <div className="text-lg font-bold text-slate-100">
                        {data.rainfall.intensity.rolling_24h_mm} <span className="text-xs font-normal">mm</span>
                      </div>
                      <div className="text-[10px] text-amber-400">
                        +{data.rainfall.anomaly.anomaly_score_sigma} sigma anomaly
                      </div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase">Soil Moisture (Composite)</div>
                      <div className="text-lg font-bold text-red-400">
                        {data.soil_moisture.current_composite_pct}%
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {data.soil_moisture.trend.direction}
                      </div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-md border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400 uppercase">Assessment Confidence</div>
                      <div className="text-lg font-bold text-emerald-400">
                        {data.current_assessment.confidence_pct ?? Math.round(data.current_assessment.confidence_score * 100)}%
                      </div>
                      <div className="text-[10px] text-slate-500">
                        Data Completeness: {data.uncertainty?.data_completeness_pct ?? 88}%
                      </div>
                    </div>
                  </div>

                  {/* Scientific Triggers vs Conditioning Factors */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Triggers */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <span className="font-mono text-xs font-bold text-red-400 uppercase flex items-center gap-1.5">
                          <CloudRain className="w-3.5 h-3.5" />
                          Dynamic Trigger Indicators
                        </span>
                        <span className="text-[10px] font-mono text-slate-500">Short-Term Driving Forces</span>
                      </div>
                      <div className="space-y-2">
                        {data.triggers && data.triggers.length > 0 ? (
                          data.triggers.map((trig, idx) => (
                            <div key={idx} className="bg-slate-900 p-2 rounded-lg border border-slate-800 flex items-start justify-between gap-2">
                              <div>
                                <div className="font-bold text-slate-200 text-xs">{trig.name}</div>
                                <div className="text-[11px] text-slate-400">{trig.description}</div>
                              </div>
                              <span className="font-mono font-bold text-xs text-red-300 shrink-0 bg-red-950 px-2 py-0.5 rounded border border-red-800">
                                {trig.value}
                              </span>
                            </div>
                          ))
                        ) : (
                          <div className="text-slate-500 text-xs font-mono">No active extreme triggers.</div>
                        )}
                      </div>
                    </div>

                    {/* Conditioning Factors */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <span className="font-mono text-xs font-bold text-amber-400 uppercase flex items-center gap-1.5">
                          <Mountain className="w-3.5 h-3.5" />
                          Conditioning Susceptibility Factors
                        </span>
                        <span className="text-[10px] font-mono text-slate-500">Slope Vulnerability</span>
                      </div>
                      <div className="space-y-2">
                        {data.conditioning_factors && data.conditioning_factors.length > 0 ? (
                          data.conditioning_factors.map((cond, idx) => (
                            <div key={idx} className="bg-slate-900 p-2 rounded-lg border border-slate-800 flex items-start justify-between gap-2">
                              <div>
                                <div className="font-bold text-slate-200 text-xs">{cond.name}</div>
                                <div className="text-[11px] text-slate-400">{cond.description}</div>
                              </div>
                              <span className="font-mono font-bold text-xs text-amber-300 shrink-0 bg-amber-950 px-2 py-0.5 rounded border border-amber-800">
                                {cond.value}
                              </span>
                            </div>
                          ))
                        ) : (
                          <div className="text-slate-500 text-xs font-mono">Conditioning factors within baseline.</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Summary Narrative */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                      Physical Assessment Synthesis:
                    </div>
                    <p className="text-slate-200 text-xs leading-relaxed font-sans">
                      {data.hydrometeorological_state.synthesis_summary}
                    </p>
                  </div>
                </div>
              )}

              {/* --- TAB 2: RAINFALL TIMELINE (GRAPH A) --- */}
              {activeTab === "rainfall" && (
                <div className="space-y-4">
                  {/* Graph Controls */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                        <CloudRain className="w-4 h-4 text-indigo-400" />
                        Graph A — Rainfall Timeline &amp; Rolling Accumulation
                      </h3>
                      <p className="text-[11px] text-slate-400 font-mono">
                        Hourly precipitation bars (mm/h) + 24h rolling cumulative line (mm)
                      </p>
                    </div>

                    <div className="flex items-center gap-1 font-mono text-[10px]">
                      {[24, 48, 72].map((h) => (
                        <button
                          key={h}
                          onClick={() => setRainfallRangeHours(h)}
                          className={`px-2.5 py-1 rounded-lg transition ${
                            rainfallRangeHours === h
                              ? "bg-indigo-600 text-white font-bold"
                              : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                          }`}
                        >
                          {h}h Window
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* GRAPH A: SVG Chart */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pb-1">
                      <span className="flex items-center gap-2">
                        <span className="w-3 h-3 bg-indigo-500 rounded-sm inline-block" />
                        <span>Hourly Intensity (mm/h)</span>
                        <span className="w-3 h-1 bg-cyan-400 rounded-full inline-block ml-3" />
                        <span>24h Rolling Accumulation (mm)</span>
                      </span>
                      <span>Common Timeline Axis</span>
                    </div>

                    {/* SVG Chart Container */}
                    <div className="w-full h-56 relative bg-slate-900/60 rounded-lg p-2 flex items-end">
                      <svg className="w-full h-full overflow-visible" viewBox="0 0 600 180" preserveAspectRatio="none">
                        {/* Grid lines */}
                        <line x1="0" y1="45" x2="600" y2="45" stroke="#334155" strokeDasharray="3 3" strokeWidth="0.8" />
                        <line x1="0" y1="90" x2="600" y2="90" stroke="#334155" strokeDasharray="3 3" strokeWidth="0.8" />
                        <line x1="0" y1="135" x2="600" y2="135" stroke="#334155" strokeDasharray="3 3" strokeWidth="0.8" />

                        {/* Bars for Hourly Precip */}
                        {timelinePoints.slice(-rainfallRangeHours).map((pt, idx, arr) => {
                          const w = 600 / arr.length;
                          const x = idx * w;
                          const maxRate = 40.0;
                          const barH = Math.min(160, ((pt.rainfall_rate_mm_h || 0) / maxRate) * 160);
                          const y = 170 - barH;

                          return (
                            <g key={idx} className="cursor-pointer group">
                              <rect
                                x={x + 1}
                                y={y}
                                width={Math.max(2, w - 2)}
                                height={barH}
                                fill={pt.is_observed ? "#6366f1" : "#818cf8"}
                                fillOpacity={pt.is_observed ? "0.85" : "0.4"}
                                rx="1"
                              />
                            </g>
                          );
                        })}

                        {/* Line for 24h Accumulation */}
                        {(() => {
                          const pts = timelinePoints.slice(-rainfallRangeHours);
                          if (pts.length < 2) return null;
                          const maxAcc = 250.0;
                          const dStr = pts
                            .map((pt, idx) => {
                              const x = idx * (600 / pts.length) + (600 / pts.length) / 2;
                              const y = 170 - Math.min(160, (pt.rainfall_24h_mm / maxAcc) * 160);
                              return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                            })
                            .join(" ");

                          return (
                            <path
                              d={dStr}
                              fill="none"
                              stroke="#22d3ee"
                              strokeWidth="2.5"
                              strokeLinecap="round"
                            />
                          );
                        })()}
                      </svg>
                    </div>

                    {/* Timeline Legend & Range */}
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1">
                      <span>Past {rainfallRangeHours} Hours Observation</span>
                      <span className="text-slate-400">NOW (Current Fix)</span>
                    </div>
                  </div>

                  {/* Rainfall Detail Metrics */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400">Max 1h Rainfall</div>
                      <div className="text-base font-bold text-indigo-300 mt-0.5">
                        {data.rainfall.max_short_duration?.max_1h_mm ?? data.rainfall.intensity.current_intensity_mm_h} mm
                      </div>
                    </div>

                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400">Max 6h Rainfall</div>
                      <div className="text-base font-bold text-slate-100 mt-0.5">
                        {data.rainfall.max_short_duration?.max_6h_mm ?? 45.0} mm
                      </div>
                    </div>

                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400">Continuous Wet Spell</div>
                      <div className="text-base font-bold text-amber-400 mt-0.5">
                        {data.rainfall.persistence.current_wet_spell_hours} hours
                      </div>
                    </div>

                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400">Antecedent Wetness Index</div>
                      <div className="text-base font-bold text-red-400 mt-0.5">
                        {data.rainfall.antecedent_wetness_index?.api_value ?? 78.4} API
                      </div>
                    </div>
                  </div>

                  {/* Intensity-Duration Analysis Summary */}
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-indigo-300">
                        Prototype Intensity-Duration (I-D) Threshold Evaluation:
                      </span>
                      <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                        data.rainfall.intensity_duration.is_above_prototype_threshold
                          ? "bg-red-500/20 text-red-400 border border-red-500/40"
                          : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                      }`}>
                        {data.rainfall.intensity_duration.status_text}
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] leading-relaxed">
                      Cumulative {data.rainfall.intensity_duration.cumulative_rainfall_mm}mm over {data.rainfall.intensity_duration.active_duration_hours}h active duration vs {data.rainfall.intensity_duration.prototype_threshold_rainfall_mm}mm prototype reference.
                    </p>
                  </div>
                </div>
              )}

              {/* --- TAB 3: SOIL MOISTURE TIMELINE (GRAPH B) --- */}
              {activeTab === "soil" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                        <Droplets className="w-4 h-4 text-indigo-400" />
                        Graph B — Soil Moisture Timeline &amp; Vertical Profile
                      </h3>
                      <p className="text-[11px] text-slate-400 font-mono">
                        Volumetric soil moisture (%) and infiltration rate of change
                      </p>
                    </div>

                    <div className="flex items-center gap-1 font-mono text-[10px]">
                      {["surface", "shallow", "medium", "deep"].map((d) => (
                        <button
                          key={d}
                          onClick={() => setSelectedSoilDepth(d)}
                          className={`px-2.5 py-1 rounded-lg uppercase transition ${
                            selectedSoilDepth === d
                              ? "bg-indigo-600 text-white font-bold"
                              : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                          }`}
                        >
                          {d}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* GRAPH B: SVG Chart */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="w-full h-52 relative bg-slate-900/60 rounded-lg p-2 flex items-end">
                      <svg className="w-full h-full overflow-visible" viewBox="0 0 600 160" preserveAspectRatio="none">
                        {/* Saturation Level Zones */}
                        <rect x="0" y="0" width="600" height="40" fill="#ef4444" fillOpacity="0.08" />
                        <rect x="0" y="40" width="600" height="45" fill="#f59e0b" fillOpacity="0.06" />

                        {/* Curve for Soil Moisture */}
                        {(() => {
                          const pts = timelinePoints.slice(-24);
                          if (pts.length < 2) return null;
                          const dStr = pts
                            .map((pt, idx) => {
                              const x = idx * (600 / pts.length) + (600 / pts.length) / 2;
                              const y = 150 - Math.min(140, (pt.soil_moisture_pct / 100.0) * 140);
                              return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                            })
                            .join(" ");

                          return (
                            <path
                              d={dStr}
                              fill="none"
                              stroke="#f43f5e"
                              strokeWidth="3"
                              strokeLinecap="round"
                            />
                          );
                        })()}
                      </svg>
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                      <span>Rate of Change: {data.soil_moisture.trend.delta_6h_pct >= 0 ? `+${data.soil_moisture.trend.delta_6h_pct}` : data.soil_moisture.trend.delta_6h_pct}% / 6h</span>
                      <span className="text-red-400 font-bold">{data.soil_moisture.percentile.status_label}</span>
                    </div>
                  </div>

                  {/* Vertical Soil Moisture Depth Layers */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {data.soil_moisture.vertical_profile.map((layer, i) => (
                      <div key={i} className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1.5 font-mono text-xs">
                        <div className="text-[10px] text-slate-400">{layer.depth_label}</div>
                        <div className="text-[10px] text-slate-500">{layer.depth_range}</div>
                        <div className="text-lg font-bold text-slate-100">{layer.moisture_pct}%</div>
                        <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-indigo-500 h-full rounded-full"
                            style={{ width: `${layer.bar_fill_pct}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Model Derived Label */}
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-[10px] font-mono text-slate-500 text-center">
                    MODEL-DERIVED VOLUMETRIC SOIL SATURATION • IN-SITU PIEZOMETER PORE PRESSURE SENSORS NOT DEPLOYED
                  </div>
                </div>
              )}

              {/* --- TAB 4: TERRAIN SUSCEPTIBILITY --- */}
              {activeTab === "terrain" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                        <Mountain className="w-4 h-4 text-indigo-400" />
                        Terrain Susceptibility &amp; Geotechnical Parameters
                      </h3>
                      <p className="text-[11px] text-slate-400 font-mono">
                        Slope angle, aspect, digital elevation, and lithological susceptibility
                      </p>
                    </div>

                    <span className="text-[10px] font-mono px-2 py-1 bg-amber-950/80 border border-amber-800 text-amber-300 rounded font-bold">
                      DEMO TERRAIN DATA
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400">Slope Gradient</div>
                      <div className="text-lg font-bold text-slate-100">{data.terrain.slope_angle_deg}°</div>
                      <div className="text-[10px] text-amber-400">{data.terrain.slope_classification}</div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400">Elevation</div>
                      <div className="text-lg font-bold text-slate-100">{data.terrain.elevation_m} m</div>
                      <div className="text-[10px] text-slate-500">SRTM-30m DEM</div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400">Slope Aspect</div>
                      <div className="text-lg font-bold text-indigo-300">{data.terrain.aspect_label || "SE (South-East)"}</div>
                      <div className="text-[10px] text-slate-500">Solar / Wind Exposure</div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400">Susceptibility Score</div>
                      <div className="text-lg font-bold text-red-400">{data.terrain.terrain_susceptibility_score} / 1.0</div>
                      <div className="text-[10px] text-slate-400">{data.terrain.historical_susceptibility_rating} Susceptibility</div>
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
                    <div className="font-mono font-bold text-slate-300 text-[10px] uppercase">Geotechnical Analysis:</div>
                    <p className="text-slate-300 leading-relaxed font-sans">{data.terrain.geotechnical_notes}</p>
                  </div>
                </div>
              )}

              {/* --- TAB 5: RISK TIMELINE (GRAPH C & D) --- */}
              {activeTab === "timeline" && (
                <div className="space-y-4">
                  {/* Graph D: Multi-Signal Synchronized Timeline */}
                  <div>
                    <div className="flex items-center justify-between pb-1">
                      <div>
                        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                          <BarChart3 className="w-4 h-4 text-indigo-400" />
                          Graph D — Multi-Signal Synchronized Timeline
                        </h3>
                        <p className="text-[11px] text-slate-400 font-mono">
                          Rainfall • Soil Moisture • Risk Index (Temporal relationship comparison)
                        </p>
                      </div>

                      {/* Signal Toggles */}
                      <div className="flex items-center gap-2 font-mono text-[10px]">
                        <button
                          onClick={() => setShowRainfallSignal(!showRainfallSignal)}
                          className={`px-2 py-0.5 rounded transition ${showRainfallSignal ? "bg-indigo-600 text-white" : "bg-slate-950 text-slate-500"}`}
                        >
                          Rainfall
                        </button>
                        <button
                          onClick={() => setShowSoilSignal(!showSoilSignal)}
                          className={`px-2 py-0.5 rounded transition ${showSoilSignal ? "bg-red-600 text-white" : "bg-slate-950 text-slate-500"}`}
                        >
                          Soil Saturation
                        </button>
                        <button
                          onClick={() => setShowRiskSignal(!showRiskSignal)}
                          className={`px-2 py-0.5 rounded transition ${showRiskSignal ? "bg-amber-600 text-white" : "bg-slate-950 text-slate-500"}`}
                        >
                          Risk Index
                        </button>
                      </div>
                    </div>

                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                      <div className="w-full h-56 relative bg-slate-900/60 rounded-lg p-2 flex items-end">
                        <svg className="w-full h-full overflow-visible" viewBox="0 0 600 180" preserveAspectRatio="none">
                          {/* Forecast Dividing Line (NOW Boundary) */}
                          <line x1="450" y1="0" x2="450" y2="180" stroke="#f59e0b" strokeDasharray="4 4" strokeWidth="1.5" />
                          <text x="455" y="15" fill="#f59e0b" fontSize="9" fontFamily="monospace">NOW | FORECAST</text>

                          {/* Shaded Forecast Background */}
                          <rect x="450" y="0" width="150" height="180" fill="#f59e0b" fillOpacity="0.04" />

                          {/* Risk Score Line */}
                          {showRiskSignal && (() => {
                            const pts = timelinePoints;
                            if (pts.length < 2) return null;
                            const dStr = pts
                              .map((pt, idx) => {
                                const x = (idx / (pts.length - 1)) * 600;
                                const y = 170 - (pt.risk_score / 100.0) * 160;
                                return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                              })
                              .join(" ");

                            return <path d={dStr} fill="none" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" />;
                          })()}

                          {/* Soil Moisture Line */}
                          {showSoilSignal && (() => {
                            const pts = timelinePoints;
                            if (pts.length < 2) return null;
                            const dStr = pts
                              .map((pt, idx) => {
                                const x = (idx / (pts.length - 1)) * 600;
                                const y = 170 - (pt.soil_moisture_pct / 100.0) * 160;
                                return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                              })
                              .join(" ");

                            return <path d={dStr} fill="none" stroke="#ef4444" strokeWidth="2" strokeDasharray="2 2" strokeLinecap="round" />;
                          })()}

                          {/* Rainfall Line */}
                          {showRainfallSignal && (() => {
                            const pts = timelinePoints;
                            if (pts.length < 2) return null;
                            const maxR = 40.0;
                            const dStr = pts
                              .map((pt, idx) => {
                                const x = (idx / (pts.length - 1)) * 600;
                                const y = 170 - Math.min(160, ((pt.rainfall_rate_mm_h || 0) / maxR) * 160);
                                return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                              })
                              .join(" ");

                            return <path d={dStr} fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" />;
                          })()}
                        </svg>
                      </div>

                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                        <span className="text-slate-500">← Past 48 Hours Observations</span>
                        <span className="text-amber-400 font-bold">Temporal relationship (Non-causal)</span>
                        <span className="text-slate-500">24h Model Forecast →</span>
                      </div>
                    </div>
                  </div>

                  {/* Interactive Time-Point Inspector */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                      Timeline Series Point Inspector:
                    </div>
                    <div className="flex items-center gap-1.5 overflow-x-auto text-[10px] font-mono pb-1 scrollbar-none">
                      {timelinePoints.map((pt, idx) => (
                        <button
                          key={idx}
                          onClick={() => setSelectedTimelineIndex(idx)}
                          className={`px-2 py-1 rounded transition whitespace-nowrap ${
                            selectedTimelineIndex === idx
                              ? "bg-indigo-600 text-white font-bold"
                              : "bg-slate-900 text-slate-400 hover:text-slate-200"
                          }`}
                        >
                          {pt.timestamp_str}
                        </button>
                      ))}
                    </div>

                    {selectedTimelineIndex !== null && timelinePoints[selectedTimelineIndex] && (
                      <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                        <div>
                          <span className="text-slate-400 text-[10px]">Timestamp:</span>
                          <div className="font-bold text-slate-100">{timelinePoints[selectedTimelineIndex].timestamp_str}</div>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px]">Risk Index:</span>
                          <div className="font-bold text-amber-400">{timelinePoints[selectedTimelineIndex].risk_score.toFixed(1)} / 100</div>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px]">Rainfall Rate:</span>
                          <div className="font-bold text-indigo-300">{timelinePoints[selectedTimelineIndex].rainfall_rate_mm_h} mm/h</div>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px]">Soil Saturation:</span>
                          <div className="font-bold text-red-400">{timelinePoints[selectedTimelineIndex].soil_moisture_pct}%</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* --- TAB 6: FORECAST --- */}
              {activeTab === "forecast" && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                      <Clock className="w-4 h-4 text-indigo-400" />
                      Numerical Weather Forecast &amp; Risk Projection
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono">
                      {data.forecast.forecast_period_label} • {data.forecast.provenance_note}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400">Expected 24h Rainfall</div>
                      <div className="text-lg font-bold text-indigo-300">{data.forecast.expected_rainfall_24h_mm} mm</div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400">Expected Wet Hours</div>
                      <div className="text-lg font-bold text-slate-100">{data.forecast.expected_wet_hours_24h} hours</div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400">Soil Moisture Trend</div>
                      <div className="text-lg font-bold text-red-400">{data.forecast.expected_moisture_trend}</div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-400">Projected Risk Trajectory</div>
                      <div className="text-lg font-bold text-amber-400">{data.forecast.projected_risk_trajectory}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* --- TAB 7: DATA QUALITY & UNCERTAINTY --- */}
              {activeTab === "quality" && (
                <div className="space-y-4">
                  {/* Explicit Uncertainty Breakdown */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="font-mono text-xs font-bold text-indigo-400 uppercase">
                        Explicit Assessment Uncertainty &amp; Limitations
                      </span>
                      <span className="font-mono text-xs text-emerald-400 font-bold">
                        Confidence: {data.uncertainty?.assessment_confidence_pct ?? 82}%
                      </span>
                    </div>

                    <p className="text-slate-200 text-xs leading-relaxed font-sans">
                      {data.uncertainty?.summary || "Assessment confidence is supported by high telemetry freshness."}
                    </p>

                    <div className="space-y-1.5 pt-1">
                      <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                        Known Missing Sensory Inputs:
                      </div>
                      <ul className="space-y-1 text-slate-300 text-xs list-disc list-inside font-mono">
                        {(data.uncertainty?.known_missing_inputs || [
                          "In-situ borehole piezometer pore pressure",
                          "Continuous subsurface inclinometer/displacement array",
                          "High-resolution InSAR surface deformation"
                        ]).map((inp, idx) => (
                          <li key={idx} className="text-slate-400">{inp}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Data Completeness Matrix Table */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                    <div className="font-mono text-xs font-bold text-slate-300 uppercase">
                      Data Availability &amp; Completeness Matrix:
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left font-mono text-[11px] border-collapse">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-500">
                            <th className="py-1.5 px-2">Parameter</th>
                            <th className="py-1.5 px-2">Status</th>
                            <th className="py-1.5 px-2">Source / Provider</th>
                            <th className="py-1.5 px-2">Freshness</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-900 text-slate-300">
                          {(data.data_quality_matrix || []).map((row, idx) => (
                            <tr key={idx} className="hover:bg-slate-900/50">
                              <td className="py-2 px-2 font-bold text-slate-200">{row.parameter}</td>
                              <td className="py-2 px-2">
                                <span className={`px-1.5 py-0.2 rounded font-bold text-[10px] ${
                                  row.status === "AVAILABLE" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                                  row.status === "SIMULATED" ? "bg-indigo-950 text-indigo-400 border border-indigo-800" :
                                  row.status === "PARTIAL" ? "bg-yellow-950 text-yellow-400 border border-yellow-800" :
                                  "bg-slate-900 text-slate-500 border border-slate-800"
                                }`}>
                                  {row.status}
                                </span>
                              </td>
                              <td className="py-2 px-2 text-slate-400">{row.data_source}</td>
                              <td className="py-2 px-2 text-slate-500">{row.last_updated}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Earth Observation (ISRO / NRSC Bhoonidhi) */}
                  <div className="bg-slate-950 p-4 rounded-md border border-slate-800 space-y-3 font-mono text-xs">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="font-bold text-slate-200 uppercase flex items-center gap-1.5">
                        <Satellite className="w-4 h-4 text-slate-400" />
                        Earth Observation (Bhoonidhi Gateway)
                      </span>
                      <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                        data.earth_observation?.status === "AVAILABLE"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : data.earth_observation?.status === "MOCK_MODE"
                          ? "bg-slate-900 text-slate-300 border border-slate-700"
                          : "bg-slate-900 text-slate-500 border border-slate-800"
                      }`}>
                        {data.earth_observation?.status || "NOT_CONFIGURED"}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
                      <div>
                        <span className="text-slate-500 text-[10px]">Provider:</span>
                        <div className="text-slate-200">{data.earth_observation?.provider || "Bhoonidhi (ISRO / NRSC)"}</div>
                      </div>
                      <div>
                        <span className="text-slate-500 text-[10px]">Collection:</span>
                        <div className="text-slate-200">{data.earth_observation?.collection || "Sentinel-1A_SAR-IW_GRD"}</div>
                      </div>
                      <div>
                        <span className="text-slate-500 text-[10px]">Coverage Area:</span>
                        <div className="text-slate-200">{data.earth_observation?.spatial_coverage || "NER Sector"}</div>
                      </div>
                      <div>
                        <span className="text-slate-500 text-[10px]">Product Status:</span>
                        <div className="text-slate-200">{data.earth_observation?.product_status || "ONLINE"}</div>
                      </div>
                    </div>

                    <div className="text-[10px] text-slate-400 font-sans bg-slate-900/60 p-2.5 rounded border border-slate-850">
                      {data.earth_observation?.note || "Satellite observations provide remote sensing context and do not replace real-time telemetry."}
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
