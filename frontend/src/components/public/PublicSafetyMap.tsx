"use client";

import React, { useState } from "react";
import {
  MapPin,
  Shield,
  Navigation,
  Info,
  AlertTriangle,
  Compass,
  Layers,
  Phone,
  CheckCircle2,
} from "lucide-react";

interface SafetyPointItem {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  point_type: string;
  capacity?: number | null;
  availability: string;
  source: string;
  contact_number?: string | null;
  distance_km?: number | null;
  is_simulated: boolean;
}

interface PublicSafetyMapProps {
  userCoords: { lat: number; lon: number } | null;
  locationName: string;
  hazardCoords?: { lat: number; lon: number } | null;
  hazardSeverity: string;
  affectedRadiusKm: number;
  safetyPoints: SafetyPointItem[];
  onSelectSafetyPoint?: (point: SafetyPointItem) => void;
}

export default function PublicSafetyMap({
  userCoords,
  locationName,
  hazardCoords,
  hazardSeverity,
  affectedRadiusKm,
  safetyPoints,
  onSelectSafetyPoint,
}: PublicSafetyMapProps) {
  const [selectedPoint, setSelectedPoint] = useState<SafetyPointItem | null>(null);

  const uLat = userCoords?.lat ?? 27.3389;
  const uLon = userCoords?.lon ?? 88.6065;
  const hLat = hazardCoords?.lat ?? uLat;
  const hLon = hazardCoords?.lon ?? uLon;

  const isUrgent = hazardSeverity === "CRITICAL" || hazardSeverity === "URGENT";
  const isAlert = hazardSeverity === "HIGH" || hazardSeverity === "ALERT";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl font-sans space-y-3">
      {/* Map Header */}
      <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold font-mono uppercase text-slate-200">
            Public Safety &amp; Evacuation Map
          </span>
        </div>
        <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Safer Points Active</span>
        </div>
      </div>

      {/* Visual Graphical Radar / Coordinate Layout */}
      <div className="relative w-full h-72 bg-gradient-to-b from-slate-950 via-[#0a1120] to-slate-950 flex items-center justify-center overflow-hidden border-y border-slate-800/80">
        {/* Concentric Safety & Hazard Zones */}
        {isUrgent && (
          <>
            {/* Outer Watch Perimeter */}
            <div className="absolute w-64 h-64 rounded-full border-2 border-orange-500/20 bg-orange-950/10 animate-pulse flex items-center justify-center">
              <span className="text-[9px] font-mono text-orange-400/60 uppercase tracking-widest absolute top-2">
                Watch Perimeter (25km)
              </span>
            </div>

            {/* Inner Critical Hazard Perimeter */}
            <div className="absolute w-44 h-44 rounded-full border-2 border-dashed border-red-500/40 bg-red-950/25 flex items-center justify-center">
              <span className="text-[9px] font-mono font-bold text-red-400 uppercase tracking-wider absolute top-2">
                Hazard Danger Zone (12km)
              </span>
            </div>
          </>
        )}

        {isAlert && !isUrgent && (
          <div className="absolute w-52 h-52 rounded-full border-2 border-dashed border-orange-500/40 bg-orange-950/20 flex items-center justify-center">
            <span className="text-[9px] font-mono font-bold text-orange-400 uppercase tracking-wider absolute top-2">
              High Risk Perimeter (15km)
            </span>
          </div>
        )}

        {/* Hazard Epicenter Marker */}
        <div className="absolute flex flex-col items-center z-10">
          <div className="w-8 h-8 rounded-full bg-red-600/30 border-2 border-red-500 flex items-center justify-center shadow-lg shadow-red-900/50">
            <AlertTriangle className="w-4 h-4 text-red-400 animate-bounce" />
          </div>
          <span className="mt-1 text-[10px] font-bold font-mono text-red-300 bg-slate-950/90 px-2 py-0.5 rounded border border-red-800/60 shadow">
            {locationName} (Hazard Center)
          </span>
        </div>

        {/* User GPS Pin (Offset visually) */}
        <div className="absolute top-12 left-10 flex flex-col items-center z-20">
          <div className="relative flex items-center justify-center">
            <span className="w-4 h-4 rounded-full bg-blue-500 animate-ping absolute" />
            <div className="w-5 h-5 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center shadow-md shadow-blue-900">
              <Navigation className="w-2.5 h-2.5 text-white" />
            </div>
          </div>
          <span className="mt-1 text-[9px] font-bold font-mono text-blue-200 bg-blue-950/90 px-1.5 py-0.5 rounded border border-blue-700 shadow">
            Your Location
          </span>
        </div>

        {/* Safety Point Markers */}
        {safetyPoints.map((pt, idx) => {
          const offsets = [
            "bottom-6 right-8",
            "top-8 right-12",
            "bottom-8 left-12",
          ];
          const posClass = offsets[idx % offsets.length];

          return (
            <div
              key={pt.id}
              onClick={() => {
                setSelectedPoint(pt);
                if (onSelectSafetyPoint) onSelectSafetyPoint(pt);
              }}
              className={`absolute ${posClass} flex flex-col items-center z-20 cursor-pointer group transition transform hover:scale-105`}
            >
              <div className="w-7 h-7 rounded-full bg-emerald-600/30 border-2 border-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-950 group-hover:bg-emerald-500/50">
                <Shield className="w-3.5 h-3.5 text-emerald-300" />
              </div>
              <span className="mt-1 text-[9px] font-bold font-mono text-emerald-300 bg-slate-950/90 px-2 py-0.5 rounded border border-emerald-800/80 shadow max-w-[130px] truncate text-center">
                {pt.name} ({pt.distance_km ?? 2.1} km)
              </span>
            </div>
          );
        })}

        {/* Legend Overlay */}
        <div className="absolute bottom-2 left-2 bg-slate-950/80 backdrop-blur-sm border border-slate-800 p-2 rounded-lg text-[9px] font-mono text-slate-400 space-y-1">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            <span>Your GPS Location</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span>Hazard Danger Perimeter</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Safer Reference Point</span>
          </div>
        </div>
      </div>

      {/* Selected Safety Point Card */}
      {selectedPoint && (
        <div className="p-3 bg-slate-950 mx-3 rounded-xl border border-emerald-900/60 space-y-2 animate-fadeIn">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-emerald-400 font-mono flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {selectedPoint.name}
            </span>
            <span className="font-mono text-[10px] bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800 uppercase font-bold">
              {selectedPoint.point_type.replace(/_/g, " ")} • {selectedPoint.availability}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-300">
            <div>
              <span className="text-slate-500">Straight-line Distance:</span>{" "}
              <strong className="text-slate-100">{selectedPoint.distance_km ?? 2.1} km</strong>
            </div>
            <div>
              <span className="text-slate-500">Authority:</span>{" "}
              <strong className="text-slate-100">{selectedPoint.source}</strong>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-slate-900 text-[10px] text-slate-400 font-mono">
            <span>Help Contact: {selectedPoint.contact_number || "112 / 1070"}</span>
            <span className="text-amber-400/80">Suggested destination — verify road clearances</span>
          </div>
        </div>
      )}
    </div>
  );
}
