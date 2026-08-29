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
        hasActiveEvent
          ? `<span class="${pulseClass}" style="position: absolute; width: ${
              size + 14
            }px; height: ${
              size + 14
            }px; border-radius: 9999px; background-color: ${color}; opacity: 0.35;"></span>`
          : ""
      }
      <div style="
        width: ${size}px;
        height: ${size}px;
        border-radius: 9999px;
        background-color: ${color};
        border: ${isSelected ? "3px solid #ffffff" : `2px solid ${borderColor}`};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-weight: bold;
        font-size: ${isSelected ? "11px" : "9px"};
        font-family: monospace;
      ">
        ${riskLevel ? riskLevel.slice(0, 1) : "L"}
      </div>
    </div>
  `;

  return L.divIcon({
    className: "custom-map-marker",
    html,
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
  const selectedLocation = locations.find((l) => l.id === selectedLocationId);
  const defaultCenter: [number, number] = [26.2006, 92.9376];
  const defaultZoom = 7;

  return (
    <div className="relative w-full h-[460px] lg:h-[540px] rounded overflow-hidden border border-zinc-800 shadow-xl bg-black">
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        className="w-full h-full"
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          maxZoom={19}
        />

        <MapController selectedLocation={selectedLocation} />

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
                <div className="p-3.5 space-y-2.5 max-w-[260px] text-white bg-black font-sans">
                  {/* Popup Header */}
                  <div className="border-b border-zinc-800 pb-2">
                    <div className="text-[11px] font-mono text-zinc-400">
                      {loc.district}, {loc.state}
                    </div>
                    <div className="text-sm font-black text-white leading-tight">
                      {loc.name}
                    </div>
                  </div>

                  {/* Risk Badge & Score */}
                  <div className="flex items-center justify-between bg-zinc-950 p-2 rounded border border-zinc-800 font-mono">
                    <div>
                      <div className="text-[10px] text-zinc-400">RISK SCORE</div>
                      <div className="text-lg font-black text-white">
                        {loc.risk_score.toFixed(1)}
                        <span className="text-[10px] text-zinc-500 font-normal"> / 100</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${
                          loc.risk_level === "CRITICAL"
                            ? "bg-red-950 text-red-300 border border-red-700"
                            : loc.risk_level === "HIGH"
                            ? "bg-orange-950 text-orange-300 border border-orange-700"
                            : loc.risk_level === "MODERATE"
                            ? "bg-amber-950 text-amber-300 border border-amber-700"
                            : "bg-emerald-950 text-emerald-300 border border-emerald-700"
                        }`}
                      >
                        {loc.risk_level}
                      </span>
                      <div className="text-[10px] text-zinc-400 mt-0.5">
                        {(loc.confidence_score * 100).toFixed(0)}% Conf
                      </div>
                    </div>
                  </div>

                  {/* Telemetry Snapshot */}
                  <div className="grid grid-cols-2 gap-1.5 text-[11px] text-zinc-400 font-mono">
                    <div className="bg-zinc-950 p-1.5 rounded border border-zinc-800 flex items-center gap-1.5">
                      <Droplets className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                      <div>
                        <div className="text-[9px] text-zinc-500 font-bold">24h RAIN</div>
                        <div className="text-white font-bold">{loc.rainfall_24h ?? 0} mm</div>
                      </div>
                    </div>
                    <div className="bg-zinc-950 p-1.5 rounded border border-zinc-800 flex items-center gap-1.5">
                      <Mountain className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                      <div>
                        <div className="text-[9px] text-zinc-500 font-bold">SOIL MOIST</div>
                        <div className="text-white font-bold">{loc.soil_moisture ?? "--"}%</div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-1 flex gap-2">
                    <button
                      onClick={() => onOpenInvestigate(loc.id)}
                      className="w-full bg-white hover:bg-zinc-200 text-black text-[11px] font-black py-1.5 px-2.5 rounded transition flex items-center justify-center gap-1 shadow-sm font-mono"
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
      <div className="absolute top-3 right-3 z-[1000] bg-black/90 border border-zinc-800 rounded px-3 py-2 text-xs shadow-lg space-y-1.5 font-mono">
        <div className="text-[10px] uppercase font-bold text-zinc-400 tracking-wider">
          Risk Severity (NER)
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
            <span className="text-zinc-200">Critical (&ge;75)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
            <span className="text-zinc-200">High (50-74)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
            <span className="text-zinc-200">Moderate (25-49)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-zinc-200">Low (0-24)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
