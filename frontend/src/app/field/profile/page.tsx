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
    <main className="flex-1 p-3 sm:p-4 space-y-3.5 font-sans text-white bg-black">
      {/* 1. Header */}
      <div>
        <h2 className="text-sm font-black text-white flex items-center gap-2 font-mono uppercase tracking-wider">
          <UserCheck className="w-4 h-4 text-white" />
          Field Unit Profile &amp; Telemetry
        </h2>
        <p className="text-[11px] text-zinc-400 font-mono">
          Assigned callsign, GPS telemetry, and communication configuration
        </p>
      </div>

      {/* 2. Unit Callsign Switcher Card */}
      <div className="bg-zinc-950 border border-zinc-800 rounded p-3.5 space-y-3 shadow-md">
        <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold">
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
              className={`p-2.5 rounded border text-left transition ${
                callsign === u.sign
                  ? "bg-white text-black font-black border-white shadow-sm"
                  : "bg-black border-zinc-800 text-zinc-400 hover:text-white"
              }`}
            >
              <div className={callsign === u.sign ? "text-black font-black text-xs" : "text-white font-bold text-xs"}>
                {u.sign}
              </div>
              <div className={callsign === u.sign ? "text-[10px] text-zinc-700 truncate mt-0.5" : "text-[10px] text-zinc-500 truncate mt-0.5"}>
                {u.state}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 3. Detailed Telemetry Card */}
      <div className="bg-zinc-950 border border-zinc-800 rounded p-3.5 space-y-3 shadow-md text-xs font-mono">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <span className="text-[10px] font-mono uppercase text-zinc-400 font-bold">
            Unit Telemetry &amp; Status
          </span>
          <span className="text-emerald-400 font-bold">{team?.status || "DEPLOYED"}</span>
        </div>

        <div className="space-y-2 text-zinc-300">
          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400">Unit Name:</span>
            <span className="font-bold text-white">{team?.team_name || "SDRF Quick Response Unit Alpha"}</span>
          </div>

          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400">Primary Channel:</span>
            <span className="font-bold text-white">
              {team?.contact_channel || "VHF Ch 4 / Satellite"}
            </span>
          </div>

          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400">GPS Coordinates:</span>
            <span className="font-bold text-white">
              {coords ? `${coords.lat.toFixed(4)}°N, ${coords.lon.toFixed(4)}°E` : "Acquiring..."}
            </span>
          </div>

          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400">Position Accuracy:</span>
            <span className="font-bold text-emerald-400">
              {coords?.accuracy ? `±${coords.accuracy} meters (${geoSource})` : geoStatus}
            </span>
          </div>

          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400">Assigned Sector:</span>
            <span className="font-bold text-white">
              {data?.assigned_location?.name || "Gangtok Hill Station"}
            </span>
          </div>
        </div>

        <div className="pt-2 flex gap-2">
          <button
            onClick={() => requestGPSLocation()}
            className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white font-mono text-xs py-2 rounded border border-zinc-700 flex items-center justify-center gap-1.5 transition font-bold"
          >
            <LocateFixed className="w-3.5 h-3.5" />
            <span>Re-Acquire GPS</span>
          </button>

          <button
            onClick={() => refreshBriefing()}
            className="flex-1 bg-white hover:bg-zinc-200 text-black font-mono font-black text-xs py-2 rounded flex items-center justify-center gap-1.5 transition shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync Briefing</span>
          </button>
        </div>
      </div>
    </main>
  );
}
