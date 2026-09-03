"use client";

import React, { useState, useEffect } from "react";
import { Play, RotateCcw, AlertOctagon, TrendingUp, Info, ChevronRight } from "lucide-react";

interface LocationOption {
  id: string;
  name: string;
  district: string;
  state: string;
}

interface Factor {
  name: string;
  contribution: number;
  raw_value: any;
  status: string;
  description: string;
}

interface Anomaly {
  metric: string;
  value: number;
  baseline: number;
  anomaly_score: number;
  is_anomalous: boolean;
  description: string;
}

interface SimulationResponse {
  scenario: string;
  location_id: string;
  location_name: string;
  message: string;
  observations_injected: number;
  assessment: {
    location_id: string;
    location: string;
    state: string;
    hazard: string;
    risk_level: string;
    risk_score: number;
    confidence: number;
    trend: string;
    active_event: boolean;
    event_id: string | null;
    event_status: string | null;
    anomalies: Anomaly[];
    factors: Factor[];
    summary: string;
    timestamp: string;
  };
  timestamp: string;
}

export default function SimulationControl({
  apiUrl,
  onAssessmentCompleted,
}: {
  apiUrl: string;
  onAssessmentCompleted: () => void;
}) {
  const [locations, setLocations] = useState<LocationOption[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<string>("");
  const [scenario, setScenario] = useState<string>("critical");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/v1/locations`);
        if (res.ok) {
          const data = await res.json();
          setLocations(data);
          if (data.length > 0) {
            setSelectedLocation(data[0].id);
          }
        }
      } catch (err) {
        console.error("Failed to load locations", err);
      }
    };
    fetchLocations();
  }, [apiUrl]);

  const handleRunSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/simulation/scenario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario,
          location_id: selectedLocation || undefined,
          seed: 42,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || `Simulation failed with code ${res.status}`);
      }

      const data: SimulationResponse = await res.json();
      setResult(data);
      onAssessmentCompleted();
    } catch (err: any) {
      setError(err.message || "Failed to execute scenario simulation");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "critical":
        return "bg-red-950 text-red-400 border-red-800";
      case "high":
        return "bg-orange-950 text-orange-400 border-orange-800";
      case "moderate":
        return "bg-yellow-950 text-yellow-400 border-yellow-800";
      default:
        return "bg-emerald-950 text-emerald-400 border-emerald-800";
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm space-y-6">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Play className="w-5 h-5 text-emerald-400" />
          Disaster Scenario Simulation & Engine Execution
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Inject deterministic meteorological and terrain time-series to test risk scoring, anomaly detection, and automated event state management.
        </p>
      </div>

      {/* Controls Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">
            1. Target Monitoring Station
          </label>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name} ({loc.state})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">
            2. Simulation Scenario
          </label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
          >
            <option value="normal">Normal Baseline (Safe, Minimal Rain)</option>
            <option value="heavy_rain">Heavy Rain Burst (Moderate Risk)</option>
            <option value="persistent_rain">Persistent Rain 48h (High Risk)</option>
            <option value="landslide_risk_increasing">Escalating Multi-Factor Threat</option>
            <option value="critical">Critical Landslide Emergency (&gt;75 Score)</option>
            <option value="recovery">Recovery &amp; Event Resolution</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={handleRunSimulation}
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-lg text-sm transition flex items-center justify-center gap-2 shadow-md shadow-indigo-950"
          >
            <Play className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Injecting & Evaluating..." : "Run Scenario Simulation"}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Assessment Output Display */}
      {result && (
        <div className="space-y-4 border-t border-slate-800 pt-5">
          <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div>
              <div className="text-xs text-slate-500">Evaluated Location</div>
              <div className="text-base font-bold text-slate-100 flex items-center gap-2">
                {result.assessment.location}
                <span className="text-xs font-normal text-slate-400 font-mono">({result.assessment.state})</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-xs text-slate-500">Calculated Risk Score</div>
                <div className="text-2xl font-black text-slate-100 font-mono">
                  {result.assessment.risk_score.toFixed(1)}
                  <span className="text-xs text-slate-500 font-normal"> / 100</span>
                </div>
              </div>

              <div className={`px-3 py-1.5 rounded-lg border font-mono text-sm font-bold ${getStatusBadge(result.assessment.risk_level)}`}>
                {result.assessment.risk_level}
              </div>
            </div>
          </div>

          {/* Event Status Banner */}
          {result.assessment.active_event ? (
            <div className="bg-orange-950/40 border border-orange-800/80 rounded-xl p-3.5 flex items-start gap-3 text-orange-200 text-xs">
              <AlertOctagon className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-sm text-orange-300">
                  Active Disaster Event [{result.assessment.event_status}]
                </div>
                <div className="mt-0.5 text-slate-300">{result.assessment.summary}</div>
                <div className="mt-1 font-mono text-[11px] text-orange-400/80">Event ID: {result.assessment.event_id}</div>
              </div>
            </div>
          ) : (
            <div className="bg-emerald-950/30 border border-emerald-800/60 rounded-xl p-3 flex items-center gap-2 text-emerald-300 text-xs">
              <Info className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>No active disaster event. Parameters within stable baseline tolerance.</span>
            </div>
          )}

          {/* Anomalies Detected */}
          {result.assessment.anomalies.filter((a) => a.is_anomalous).length > 0 && (
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-amber-400" />
                Detected Statistical Anomalies (Z-Score &gt; Threshold)
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {result.assessment.anomalies
                  .filter((a) => a.is_anomalous)
                  .map((anom, idx) => (
                    <div key={idx} className="bg-slate-950/70 border border-amber-800/40 p-2.5 rounded-lg text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-amber-300 uppercase">{anom.metric}</span>
                        <span className="font-mono text-amber-400">z = {anom.anomaly_score.toFixed(2)}</span>
                      </div>
                      <div className="text-slate-400 mt-1 text-[11px]">{anom.description}</div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Contributing Factors Breakdown Table */}
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Explainable Risk Factor Breakdown
            </div>
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/40">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/90 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-2.5">Indicator / Factor</th>
                    <th className="p-2.5">Impact Level</th>
                    <th className="p-2.5">Contribution Points</th>
                    <th className="p-2.5">Diagnostic Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {result.assessment.factors.map((factor, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40 transition">
                      <td className="p-2.5 font-medium text-slate-200">{factor.name}</td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-mono border ${getStatusBadge(factor.status)}`}>
                          {factor.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-2.5 font-mono font-bold text-slate-100">
                        +{factor.contribution.toFixed(1)} pts
                      </td>
                      <td className="p-2.5 text-slate-400 text-[11px]">{factor.description || "--"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
