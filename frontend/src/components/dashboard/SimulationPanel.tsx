"use client";

import React, { useState } from "react";
import { LocationMapItem } from "@/components/dashboard/types";
import { Play, Sliders, AlertTriangle, CheckCircle2, ChevronDown } from "lucide-react";

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
    { id: "normal", name: "1. Normal Baseline (Safe, Minimal Rain)" },
    { id: "heavy_rain", name: "2. Heavy Rain Burst (Moderate / Watch)" },
    { id: "persistent_rain", name: "3. Persistent Rain 48h (High Risk)" },
    { id: "landslide_risk_increasing", name: "4. Escalating Multi-Factor Threat" },
    { id: "critical", name: "5. Critical Emergency (>75 Score)" },
    { id: "recovery", name: "6. Recovery (Moisture Drainage & Resolution)" },
  ];

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded p-4 space-y-3 font-sans text-white">
      {/* Collapsible Header */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-zinc-400" />
          <h3 className="text-xs font-black uppercase tracking-wider text-white font-mono">
            Disaster Scenario Simulation (Demo Controls)
          </h3>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-zinc-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </div>

      {isOpen && (
        <div className="pt-2 border-t border-zinc-850 space-y-3 text-xs font-mono">
          {/* Target Station Selector */}
          <div>
            <label className="block text-[10px] text-zinc-500 uppercase font-bold mb-1">
              Target Station Sector:
            </label>
            <select
              value={selectedLocationId || ""}
              onChange={(e) => onSelectLocation(e.target.value)}
              className="w-full bg-black border border-zinc-800 rounded p-2 text-xs text-white focus:outline-none focus:border-zinc-600 font-mono font-bold"
            >
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id} className="bg-zinc-950">
                  {loc.name} ({loc.district}, {loc.state}) — Risk: {loc.risk_score.toFixed(0)}
                </option>
              ))}
            </select>
          </div>

          {/* Scenario Selector */}
          <div>
            <label className="block text-[10px] text-zinc-500 uppercase font-bold mb-1">
              Hazard Scenario:
            </label>
            <div className="grid grid-cols-1 gap-1.5">
              {scenariosList.map((sc) => (
                <button
                  key={sc.id}
                  onClick={() => setScenario(sc.id)}
                  className={`p-2 rounded border text-left text-xs transition font-bold flex items-center justify-between ${
                    scenario === sc.id
                      ? "bg-white text-black border-white shadow-sm"
                      : "bg-black border-zinc-850 text-zinc-400 hover:text-white"
                  }`}
                >
                  <span>{sc.name}</span>
                  {scenario === sc.id && <span className="text-[10px] uppercase font-black font-mono">SELECTED</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Execution Button */}
          <button
            onClick={handleExecute}
            disabled={isSimulating}
            className="w-full bg-white hover:bg-zinc-200 active:bg-zinc-300 disabled:opacity-50 text-black font-black py-2 rounded transition flex items-center justify-center gap-2 shadow-sm font-mono"
          >
            <Play className={`w-3.5 h-3.5 ${isSimulating ? "animate-spin" : ""}`} />
            {isSimulating ? "Injecting Scenario Telemetry..." : "Inject Scenario & Evaluate Engine"}
          </button>

          {/* Feedback */}
          {feedback && (
            <div className="p-2.5 rounded bg-black border border-zinc-800 text-[11px] text-zinc-300 flex items-center gap-1.5 font-sans">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
              <span>{feedback}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
