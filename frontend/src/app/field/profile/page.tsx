"use client";

import React from "react";
import {
  UserCheck,
  Shield,
  Radio,
  MapPin,
  LocateFixed,
  RefreshCw,
  Clock,
  Compass,
} from "lucide-react";
import { useField } from "@/components/field/FieldContext";

export default function FieldProfilePage() {
  const {
    callsign,
    setCallsign,
    data,
    coords,
    geoStatus,
    geoSource,
    updateTeamStatus,
    requestGPSLocation,
    refreshBriefing,
  } = useField();

  const team = data?.team;

  return (
    <main className="flex-1 p-3 sm:p-4 space-y-3.5">
      {/* 1. Header */}
      <div>
        <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-indigo-400" />
          Field Unit Profile &amp; Telemetry
        </h2>
        <p className="text-[11px] text-slate-400 font-mono">
          Assigned callsign, GPS telemetry, and communication configuration
        </p>
      </div>

      {/* 2. Unit Callsign Switcher Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-3 shadow-md">
        <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold">
          Active Unit Callsign:
        </label>
        <div className="grid grid-cols-3 gap-2 font-mono text-xs">
          {[
            { sign: "ALPHA-1", label: "Unit Alpha (Gangtok)", state: "Sikkim" },
            { sign: "BRAVO-2", label: "Unit Bravo (Aizawl)", state: "Mizoram" },
            { sign: "CHARLIE-3", label: "Unit Charlie (Kohima)", state: "Nagaland" },
          ].map((u) => (
            <button
              key={u.sign}
              onClick={() => setCallsign(u.sign)}
              className={`p-2.5 rounded-xl border text-left transition ${
                callsign === u.sign
                  ? "bg-indigo-600/20 border-indigo-500 text-white font-bold ring-1 ring-indigo-400"
                  : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              <div className="text-indigo-300 font-bold text-xs">{u.sign}</div>
              <div className="text-[10px] text-slate-400 truncate mt-0.5">{u.state}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 3. Detailed Telemetry Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-3 shadow-md text-xs font-mono">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
            Unit Telemetry &amp; Status
          </span>
          <span className="text-emerald-400 font-bold">{team?.status || "AVAILABLE"}</span>
        </div>

        <div className="space-y-2 text-slate-300">
          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">Unit Name:</span>
            <span className="font-bold text-slate-100">{team?.team_name || "Rescue Unit"}</span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">Primary Channel:</span>
            <span className="font-bold text-indigo-300">
              {team?.contact_channel || "VHF Ch 4 / Satellite"}
            </span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">GPS Coordinates:</span>
            <span className="font-bold text-slate-100">
              {coords ? `${coords.lat.toFixed(4)}°N, ${coords.lon.toFixed(4)}°E` : "Acquiring..."}
            </span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">Location Source / Accuracy:</span>
            <span className="font-bold text-slate-100">
              {geoSource} {coords?.accuracy ? `(±${coords.accuracy}m)` : ""}
            </span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">Assigned Sector:</span>
            <span className="font-bold text-indigo-400 truncate max-w-[180px]">
              {data?.assigned_location?.name || "NER Regional Zone"}
            </span>
          </div>
        </div>

        <button
          onClick={() => requestGPSLocation()}
          className="w-full bg-slate-950 hover:bg-slate-800 border border-slate-800 text-indigo-300 py-2 rounded-lg font-mono text-xs flex items-center justify-center gap-1.5 transition"
        >
          <LocateFixed className="w-3.5 h-3.5 text-indigo-400" />
          <span>Re-acquire GPS Fix</span>
        </button>
      </div>
    </main>
  );
}
