"use client";

import React, { useEffect, useState } from "react";
import { LocationInvestigationData } from "@/components/dashboard/types";
import { X, Mountain, MapPin, Gauge, Droplets, Wind, Compass, ShieldAlert, Loader2 } from "lucide-react";
import TrendCharts from "@/components/dashboard/TrendCharts";
import EventTimeline from "@/components/dashboard/EventTimeline";

interface LocationInvestigateModalProps {
  locationId: string | null;
  apiUrl: string;
  onClose: () => void;
}

export default function LocationInvestigateModal({
  locationId,
  apiUrl,
  onClose,
}: LocationInvestigateModalProps) {
  const [data, setData] = useState<LocationInvestigationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!locationId) return;

    const fetchInvestigation = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiUrl}/api/v1/locations/${locationId}/investigate`);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const result = await res.json();
        setData(result);
      } catch (err: any) {
        setError(err.message || "Failed to load station investigation payload");
      } finally {
        setLoading(false);
      }
    };

    fetchInvestigation();
  }, [locationId, apiUrl]);

  if (!locationId) return null;

  return (
    <div className="fixed inset-0 z-[2000] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
        {/* Modal Top Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900/95 backdrop-blur z-10">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/50 flex items-center justify-center">
              <Mountain className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase text-indigo-400 font-bold">
                Station Investigation File
              </div>
              <h2 className="text-base font-bold text-slate-100">
                {data ? data.location.name : "Loading Station..."}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 flex-1">
          {loading && (
            <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-2">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              <span className="text-xs font-mono">Retrieving 360° telemetry &amp; historical models...</span>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-950/50 border border-red-800 rounded-xl text-red-300 text-xs">
              {error}
            </div>
          )}

          {data && (
            <div className="space-y-6">
              {/* Station Geographic & Terrain Parameters Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-slate-500 text-[10px] uppercase font-mono">Coordinates</div>
                  <div className="font-bold text-slate-200 mt-1 font-mono">
                    {data.location.latitude.toFixed(4)}°N, {data.location.longitude.toFixed(4)}°E
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{data.location.district}, {data.location.state}</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-slate-500 text-[10px] uppercase font-mono">Elevation &amp; Topography</div>
                  <div className="font-bold text-slate-200 mt-1 font-mono">
                    {data.location.elevation.toFixed(0)} meters
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Slope Angle: {data.location.slope_angle}°</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-slate-500 text-[10px] uppercase font-mono">Geological Susceptibility</div>
                  <div className="font-bold text-slate-200 mt-1 font-mono">
                    {(data.location.susceptibility_score * 100).toFixed(0)}% Index
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">High baseline hazard zone</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-slate-500 text-[10px] uppercase font-mono">Evaluated Risk Score</div>
                  <div className="font-extrabold text-slate-100 mt-1 text-base font-mono">
                    {data.latest_assessment ? `${data.latest_assessment.risk_score.toFixed(1)} / 100` : "--"}
                  </div>
                  <div className="text-[11px] text-orange-400 font-bold font-mono">
                    {data.latest_assessment?.risk_level || "LOW"}
                  </div>
                </div>
              </div>

              {/* Time-Series Charts */}
              <div>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                  Meteorological &amp; Soil Sensor Telemetry
                </div>
                <TrendCharts
                  weatherHistory={data.weather_history}
                  riskHistory={data.risk_history}
                />
              </div>

              {/* Audit Timeline */}
              {data.event_timeline.length > 0 && (
                <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                  <EventTimeline milestones={data.event_timeline} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
