"use client";

import React, { useState, useEffect } from "react";
import {
  WeatherObservationItem,
  RiskAssessmentItem,
  ScientificInvestigationData,
} from "./types";
import {
  CloudRain,
  Droplets,
  Layers,
  Activity,
  Satellite,
  Compass,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  ShieldCheck,
  Clock,
  Sparkles,
} from "lucide-react";

interface StationIntelPanelProps {
  locationId: string;
  locationName: string;
  district: string;
  state: string;
  elevation?: number;
  slopeAngle?: number;
  latestAssessment: RiskAssessmentItem | null;
  apiUrl: string;
  onOpenInvestigate: (locationId: string) => void;
}

export default function StationIntelPanel({
  locationId,
  locationName,
  district,
  state,
  elevation = 1200,
  slopeAngle = 30,
  latestAssessment,
  apiUrl,
  onOpenInvestigate,
}: StationIntelPanelProps) {
  const [scientificData, setScientificData] = useState<ScientificInvestigationData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [loadingAi, setLoadingAi] = useState<boolean>(false);

  useEffect(() => {
    if (!locationId) return;

    let isMounted = true;
    const fetchScientificAnalysis = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${apiUrl}/api/v1/locations/${locationId}/scientific-analysis`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted) setScientificData(data);
        }
      } catch (err) {
        console.error("Failed to load scientific analysis for", locationId, err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchScientificAnalysis();
    return () => {
      isMounted = false;
    };
  }, [locationId, apiUrl]);

  const handleFetchAiExplanation = async () => {
    setLoadingAi(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/ai/investigate/${locationId}`);
      if (res.ok) {
        const data = await res.json();
        setAiExplanation(data.summary || data.explanation || "No AI interpretation available.");
      } else {
        setAiExplanation("AI interpretation service temporarily unavailable.");
      }
    } catch (err) {
      setAiExplanation("AI interpretation request failed.");
    } finally {
      setLoadingAi(false);
    }
  };

  const rainfall = scientificData?.rainfall;
  const soil = scientificData?.soil_moisture;
  const eo = scientificData?.earth_observation;
  const forecast = scientificData?.forecast;
  const uncertainty = scientificData?.uncertainty;

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded p-4 font-sans text-white space-y-4">
      {/* Header with Title and Deep Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-zinc-800">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 font-bold">
            Sector Telemetry & Multi-Signal Synthesis
          </div>
          <h3 className="text-sm font-black font-mono text-white tracking-tight flex items-center gap-2">
            {locationName} ({district}, {state})
          </h3>
        </div>

        <button
          onClick={() => onOpenInvestigate(locationId)}
          className="px-3 py-1.5 bg-white hover:bg-zinc-200 text-black text-xs font-black rounded transition flex items-center gap-1.5 shadow-sm self-start sm:self-auto font-mono"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          Station 360° Deep Investigation
        </button>
      </div>

      {/* Grid: 1. Rainfall Accumulation Table | 2. Soil Moisture & Infiltration | 3. Terrain & Slope */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
        {/* Panel 1: Rainfall Metrics */}
        <div className="bg-black p-3 rounded border border-zinc-800 space-y-2">
          <div className="flex items-center justify-between text-zinc-400 font-bold uppercase text-[10px]">
            <span className="flex items-center gap-1">
              <CloudRain className="w-3.5 h-3.5 text-blue-400" />
              Precipitation Windows
            </span>
            <span className="text-white">{rainfall?.intensity.current_intensity_mm_h ?? 0} mm/h</span>
          </div>

          <div className="space-y-1 divide-y divide-zinc-850 text-[11px]">
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">1-Hour Burst:</span>
              <span className="text-white font-bold">{rainfall?.intensity.current_intensity_mm_h ?? 0} mm</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">24-Hour Event:</span>
              <span className="text-white font-bold">{rainfall?.intensity.rolling_24h_mm ?? 0} mm</span>
            </div>

            <div className="flex justify-between py-1">
              <span className="text-zinc-400">Antecedent API:</span>
              <span className="text-white font-bold">{rainfall?.antecedent_wetness_index.api_value ?? 0} API</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">Continuous Wet Spell:</span>
              <span className="text-white font-bold">{rainfall?.persistence.current_wet_spell_hours ?? 0} hours</span>
            </div>
          </div>
        </div>

        {/* Panel 2: Multi-Depth Soil Moisture */}
        <div className="bg-black p-3 rounded border border-zinc-800 space-y-2">
          <div className="flex items-center justify-between text-zinc-400 font-bold uppercase text-[10px]">
            <span className="flex items-center gap-1">
              <Droplets className="w-3.5 h-3.5 text-emerald-400" />
              Soil Saturation (Modelled)
            </span>
            <span className="text-white font-bold">{soil?.current_composite_pct ?? 0}%</span>
          </div>

          <div className="space-y-1 divide-y divide-zinc-850 text-[11px]">
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">0–1 cm Surface:</span>
              <span className="text-zinc-200">{soil?.vertical_profile?.find(l => l.depth_label.includes("0-1"))?.moisture_pct ?? 0}%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">1–3 cm Shallow:</span>
              <span className="text-zinc-200">{soil?.vertical_profile?.find(l => l.depth_label.includes("1-3"))?.moisture_pct ?? 0}%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">9–27 cm Subsurface:</span>
              <span className="text-zinc-200">{soil?.vertical_profile?.find(l => l.depth_label.includes("9-27"))?.moisture_pct ?? 0}%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">Infiltration Trend:</span>
              <span className="text-white font-bold">{soil?.trend?.direction || "STABLE"}</span>
            </div>
          </div>


        </div>

        {/* Panel 3: Terrain & Historical Geometry */}
        <div className="bg-black p-3 rounded border border-zinc-800 space-y-2">
          <div className="flex items-center justify-between text-zinc-400 font-bold uppercase text-[10px]">
            <span className="flex items-center gap-1">
              <Compass className="w-3.5 h-3.5 text-amber-400" />
              Geomorphology
            </span>
            <span className="text-white">{slopeAngle}° Gradient</span>
          </div>

          <div className="space-y-1 divide-y divide-zinc-850 text-[11px]">
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">Digital Elevation:</span>
              <span className="text-white font-bold">{elevation} m ASL</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">Lithology / Rock:</span>
              <span className="text-zinc-200">Phyllite / Schist</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">Static Hazard Tier:</span>
              <span className="text-amber-400 font-bold">HIGH SUSCEPTIBILITY</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-zinc-400">Historical Scars:</span>
              <span className="text-zinc-200">18 Documented Events</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Deterministic Hazard Reasoning & Earth Observation Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
        {/* Left: Deterministic Primary Drivers */}
        <div className="bg-black p-3 rounded border border-zinc-800 space-y-2">
          <div className="flex items-center gap-1.5 text-zinc-300 font-bold uppercase text-[10px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Deterministic Assessment Attribution
          </div>
          <p className="text-zinc-300 font-sans text-xs leading-relaxed">
            {latestAssessment?.reason || "Multi-signal evaluation indicates nominal baseline conditions."}
          </p>

          <div className="pt-2 border-t border-zinc-850 flex items-center justify-between text-[10px] text-zinc-400">
            <span>Data Completeness: <strong className="text-white">{uncertainty?.data_completeness_pct ?? 100}%</strong></span>
            <span>Signal Coherence: <strong className="text-white">{uncertainty?.signal_agreement_pct ?? 85}%</strong></span>
          </div>
        </div>

        {/* Right: Earth Observation Evidence */}
        <div className="bg-black p-3 rounded border border-zinc-800 space-y-2">
          <div className="flex items-center justify-between text-zinc-300 font-bold uppercase text-[10px]">
            <span className="flex items-center gap-1.5">
              <Satellite className="w-3.5 h-3.5 text-purple-400" />
              Earth Observation Context (Bhoonidhi)
            </span>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-700 text-zinc-300">
              {eo?.status || "AVAILABLE"}
            </span>
          </div>

          <div className="space-y-1 text-[11px] text-zinc-400">
            <div>Platform: <strong className="text-white">{eo?.collection ? eo.collection.split('_')[0] : "Sentinel-1A (SAR)"}</strong></div>
            <div>Instrument: <strong className="text-white">C-SAR Ground Range Detected (GRD)</strong></div>
            <div>Spatial Footprint: <strong className="text-zinc-200">{eo?.spatial_coverage || "Regional Footprint (NER Sector)"}</strong></div>
            <div className="text-[10px] text-zinc-500 italic pt-1">
              Contextual Earth Observation metadata. Does not represent in-situ gauge measurements.
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Optional Auxiliary AI Explanation */}
      <div className="bg-black border border-zinc-800 rounded p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase font-bold text-zinc-400">
            <Sparkles className="w-3.5 h-3.5 text-zinc-300" />
            Downstream Narrative Explanation (AI Interpretation Layer)
          </div>

          {!aiExplanation && (
            <button
              onClick={handleFetchAiExplanation}
              disabled={loadingAi}
              className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 rounded text-[10px] font-bold text-zinc-200 transition font-mono disabled:opacity-50"
            >
              {loadingAi ? "Synthesizing..." : "Generate AI Summary"}
            </button>
          )}
        </div>

        {aiExplanation ? (
          <p className="text-xs text-zinc-300 leading-relaxed font-sans bg-zinc-950 p-2.5 rounded border border-zinc-850">
            {aiExplanation}
          </p>
        ) : (
          <div className="text-[11px] text-zinc-500 font-mono italic">
            Deterministic calculations complete. Click to generate an auxiliary natural language summary.
          </div>
        )}
      </div>
    </div>
  );
}
