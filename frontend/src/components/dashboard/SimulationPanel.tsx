"use client";

import React, { useState } from "react";
import { LocationMapItem } from "@/components/dashboard/types";
import { Play, Sparkles, AlertTriangle, CheckCircle2, RotateCcw, ChevronDown } from "lucide-react";

interface SimulationPanelProps {
  locations: LocationMapItem[];
  selectedLocationId: string | null;
  onSelectLocation: (locationId: string) => void;
  onRunSimulation: (scenario: string, locationId: string) => Promise<void>;
  isSimulating: boolean;
}

export default function SimulationPanel({
  locations,
  selectedLocationId,
  onSelectLocation,
  onRunSimulation,
  isSimulating,
}: SimulationPanelProps) {
  const [scenario, setScenario] = useState<string>("critical");
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleExecute = async () => {
    const targetLoc = selectedLocationId || (locations[0]?.id ?? "");
    if (!targetLoc) return;

    setFeedback(null);
    try {
      await onRunSimulation(scenario, targetLoc);
      setFeedback(`Scenario '${scenario}' applied. Engine reassessed risk & updated events.`);
    } catch (err: any) {
      setFeedback(`Simulation error: ${err.message || "Failed"}`);
    }
  };

  const scenariosList = [
    { id: "normal", name: "1. Normal Baseline (Safe, Minimal Rain)", color: "text-emerald-400" },
    { id: "heavy_rain", name: "2. Heavy Rain Burst (Moderate / Watch)", color: "text-yellow-400" },
    { id: "persistent_rain", name: "3. Persistent Rain 48h (High Risk)", color: "text-orange-400" },
    { id: "landslide_risk_increasing", name: "4. Escalating Multi-Factor Threat", color: "text-orange-400" },
    { id: "critical", name: "5. Critical Emergency (>75 Score)", color: "text-red-400" },
    { id: "recovery", name: "6. Recovery (Moisture Drainage & Resolution)", color: "text-emerald-400" },
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur-sm space-y-3">
      {/* Collapsible Header */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Operational Disaster Simulation Console (Demo Controls)
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-500">
            {isOpen ? "Hide Controls" : "Configure Scenarios"}
          </span>
          <ChevronDown
            className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
          />
        </div>
      </div>

      {/* Console Controls */}
      {isOpen && (
        <div className="pt-2 border-t border-slate-800 space-y-3">
          <p className="text-[11px] text-slate-400">
            Inject deterministic meteorological &amp; pore saturation profiles to demonstrate risk model behavior, statistical anomaly detection, and automated event state escalation/resolution.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            {/* Target Location */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Target Station
              </label>
              <select
                value={selectedLocationId || ""}
                onChange={(e) => onSelectLocation(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
              >
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name} ({loc.state})
                  </option>
                ))}
              </select>
            </div>

            {/* Scenario */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Hazard Profile Scenario
              </label>
              <select
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
              >
                {scenariosList.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Action Button */}
            <div className="flex items-end">
              <button
                onClick={handleExecute}
                disabled={isSimulating}
                className="w-full bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold py-2 px-3 rounded-lg transition flex items-center justify-center gap-1.5 shadow-md shadow-indigo-950"
              >
                <Play className={`w-3.5 h-3.5 ${isSimulating ? "animate-spin" : ""}`} />
                {isSimulating ? "Injecting & Evaluating..." : "Run Scenario Simulation"}
              </button>
            </div>
          </div>

          {feedback && (
            <div className="p-2.5 bg-slate-950 border border-indigo-900/60 rounded-lg text-xs text-indigo-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-indigo-400 flex-shrink-0" />
              <span>{feedback}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
