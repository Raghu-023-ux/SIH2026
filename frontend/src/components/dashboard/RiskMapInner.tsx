"use client";

import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { LocationMapItem } from "@/components/dashboard/types";
import { AlertTriangle, Droplets, Mountain, ArrowUpRight, ShieldCheck, Flame } from "lucide-react";

interface RiskMapInnerProps {
  locations: LocationMapItem[];
  selectedLocationId: string | null;
  onSelectLocation: (locationId: string) => void;
  onOpenInvestigate: (locationId: string) => void;
}

// Helper component to smoothly center on selected location
function MapController({ selectedLocation }: { selectedLocation: LocationMapItem | undefined }) {
  const map = useMap();
  useEffect(() => {
    if (selectedLocation) {
      map.flyTo([selectedLocation.latitude, selectedLocation.longitude], 9, {
        duration: 1.2,
      });
    }
  }, [selectedLocation, map]);
  return null;
}

// Generate custom SVG marker based on risk level
function createCustomMarker(riskLevel: string, isSelected: boolean, hasActiveEvent: boolean) {
  let color = "#10b981"; // emerald
  let borderColor = "#059669";
  let pulseClass = "";

  switch (riskLevel?.toUpperCase()) {
    case "CRITICAL":
      color = "#ef4444"; // red
      borderColor = "#b91c1c";
      pulseClass = "animate-ping";
      break;
    case "HIGH":
      color = "#f97316"; // orange
      borderColor = "#c2410c";
      pulseClass = "animate-pulse";
      break;
    case "MODERATE":
      color = "#eab308"; // amber/yellow
      borderColor = "#a16207";
      break;
    default:
      color = "#10b981"; // green
      borderColor = "#047857";
      break;
  }

  const size = isSelected ? 34 : 26;

  const html = `
    <div style="position: relative; width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center;">
      ${
        hasActiveEvent || riskLevel === "CRITICAL"
          ? `<div style="position: absolute; width: 100%; height: 100%; border-radius: 50%; background-color: ${color}; opacity: 0.5;" class="${pulseClass}"></div>`
          : ""
      }
      <div style="
        position: relative;
        width: ${size - 4}px;
        height: ${size - 4}px;
        background-color: ${color};
        border: 2px solid ${isSelected ? "#ffffff" : borderColor};
        border-radius: 50%;
        box-shadow: 0 0 10px ${color}80, 0 2px 4px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="width: 6px; height: 6px; border-radius: 50%; background: #ffffff;"></div>
      </div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: "custom-leaflet-risk-marker",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

export default function RiskMapInner({
  locations,
  selectedLocationId,
  onSelectLocation,
  onOpenInvestigate,
}: RiskMapInnerProps) {
  // NER Region center
  const centerLat = 26.0;
  const centerLng = 92.5;
  const zoomLevel = 7;

  const selectedLoc = locations.find((l) => l.id === selectedLocationId);

  return (
    <div className="relative w-full h-[460px] lg:h-[540px] rounded-xl overflow-hidden border border-slate-800 shadow-inner">
      <MapContainer
        center={[centerLat, centerLng]}
        zoom={zoomLevel}
        scrollWheelZoom={true}
        style={{ width: "100%", height: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />

        <MapController selectedLocation={selectedLoc} />

        {locations.map((loc) => {
          const isSelected = loc.id === selectedLocationId;
          const markerIcon = createCustomMarker(loc.risk_level, isSelected, loc.active_event);

          return (
            <Marker
              key={loc.id}
              position={[loc.latitude, loc.longitude]}
              icon={markerIcon}
              eventHandlers={{
                click: () => onSelectLocation(loc.id),
              }}
            >
              <Popup>
                <div className="p-3.5 space-y-2.5 max-w-[260px] text-slate-200">
                  {/* Popup Header */}
                  <div className="border-b border-slate-700/80 pb-2">
                    <div className="text-[11px] font-mono text-slate-400">
                      {loc.district}, {loc.state}
                    </div>
                    <div className="text-sm font-bold text-slate-100 leading-tight">
                      {loc.name}
                    </div>
                  </div>

                  {/* Risk Badge & Score */}
                  <div className="flex items-center justify-between bg-slate-900/90 p-2 rounded-md border border-slate-800">
                    <div>
                      <div className="text-[10px] text-slate-400 font-mono">RISK SCORE</div>
                      <div className="text-lg font-black text-slate-100 font-mono">
                        {loc.risk_score.toFixed(1)}
                        <span className="text-[10px] text-slate-500 font-normal"> / 100</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-mono font-bold ${
                          loc.risk_level === "CRITICAL"
                            ? "bg-red-950 text-red-300 border border-red-800"
                            : loc.risk_level === "HIGH"
                            ? "bg-orange-950 text-orange-300 border border-orange-800"
                            : loc.risk_level === "MODERATE"
                            ? "bg-yellow-950 text-yellow-300 border border-yellow-800"
                            : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                        }`}
                      >
                        {loc.risk_level}
                      </span>
                      <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                        {(loc.confidence_score * 100).toFixed(0)}% Conf
                      </div>
                    </div>
                  </div>

                  {/* Telemetry Snapshot */}
                  <div className="grid grid-cols-2 gap-1.5 text-[11px] text-slate-400">
                    <div className="bg-slate-900/60 p-1.5 rounded border border-slate-800/80 flex items-center gap-1.5">
                      <Droplets className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                      <div>
                        <div className="text-[9px] text-slate-500">24h RAIN</div>
                        <div className="font-mono text-slate-200">{loc.rainfall_24h ?? 0} mm</div>
                      </div>
                    </div>
                    <div className="bg-slate-900/60 p-1.5 rounded border border-slate-800/80 flex items-center gap-1.5">
                      <Mountain className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                      <div>
                        <div className="text-[9px] text-slate-500">SOIL MOIST</div>
                        <div className="font-mono text-slate-200">{loc.soil_moisture ?? "--"}%</div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-1 flex gap-2">
                    <button
                      onClick={() => onOpenInvestigate(loc.id)}
                      className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-medium py-1.5 px-2.5 rounded transition flex items-center justify-center gap-1 shadow"
                    >
                      <span>Investigate Station</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Map Overlay Legend */}
      <div className="absolute top-3 right-3 z-[1000] bg-slate-950/90 border border-slate-800 rounded-lg px-3 py-2 text-xs backdrop-blur-md shadow-lg space-y-1.5">
        <div className="text-[10px] font-mono uppercase font-bold text-slate-400 tracking-wider">
          Risk Severity (NER)
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
            <span className="text-slate-200">Critical (&ge;75)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
            <span className="text-slate-200">High (50-74)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
            <span className="text-slate-200">Moderate (25-49)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-200">Low (0-24)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
