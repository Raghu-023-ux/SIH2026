"use client";

import React, { useState } from "react";
import {
  LifeBuoy,
  AlertTriangle,
  Send,
  CheckCircle2,
  Clock,
  MapPin,
  Plus,
  Shield,
  LocateFixed,
} from "lucide-react";
import { useField } from "@/components/field/FieldContext";

const ASSISTANCE_TYPES = [
  "MEDICAL",
  "PERSONNEL",
  "EQUIPMENT",
  "TRANSPORT",
  "COMMUNICATION",
  "EVACUATION_SUPPORT",
  "OTHER",
];

export default function FieldAssistancePage() {
  const {
    callsign,
    data,
    coords,
    geoStatus,
    refreshBriefing,
    apiUrl,
  } = useField();

  const [showModal, setShowModal] = useState<boolean>(false);
  const [assistType, setAssistType] = useState<string>("EQUIPMENT");
  const [priority, setPriority] = useState<string>("CRITICAL");
  const [description, setDescription] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setIsSubmitting(true);
    try {
      const payload = {
        event_id: data?.assigned_event?.id,
        team_id: data?.team?.id || "NER-TEAM-ALPHA",
        request_type: assistType,
        priority: priority,
        description: description.trim(),
        latitude: coords?.lat,
        longitude: coords?.lon,
      };

      const res = await fetch(`${apiUrl}/api/v1/field/assistance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setDescription("");
        setShowModal(false);
        await refreshBriefing();
      }
    } catch (err) {
      console.error("Failed to dispatch SOS", err);
      alert("Failed to transmit SOS request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isNeedAssist = data?.team?.status === "NEED_ASSISTANCE";

  return (
    <main className="flex-1 p-3 sm:p-4 space-y-3.5">
      {/* 1. Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <LifeBuoy className="w-4 h-4 text-red-400" />
            Field Assistance &amp; SOS Portal
          </h2>
          <p className="text-[11px] text-slate-400 font-mono">
            Emergency reinforcements &amp; logistics dispatch
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="bg-red-600 hover:bg-red-500 text-white font-mono font-bold text-xs px-3 py-2 rounded-xl flex items-center gap-1.5 shadow-md shadow-red-950 transition"
        >
          <Plus className="w-4 h-4" />
          <span>Dispatch SOS</span>
        </button>
      </div>

      {/* 2. Unit Status SOS Banner */}
      {isNeedAssist && (
        <div className="bg-red-950/90 border border-red-800 rounded-xl p-3.5 space-y-1 shadow-lg">
          <div className="flex items-center gap-2 text-xs font-bold text-red-300 font-mono">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span>UNIT BROADCASTING ACTIVE SOS</span>
          </div>
          <p className="text-xs text-slate-200">
            Headquarters and neighboring response units have been alerted to your distress call.
          </p>
        </div>
      )}

      {/* 3. Instructions / Quick Guide */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-2 text-xs">
        <span className="font-mono text-[10px] font-bold text-indigo-400 uppercase">
          Tactical SOS Protocol
        </span>
        <ul className="space-y-1 text-slate-300 text-[11px] list-disc list-inside">
          <li>Select <strong className="text-slate-100">CRITICAL</strong> priority for life-threatening or trapped victim scenarios.</li>
          <li>Specify road blockages, heavy excavation requirements, or aerial medical evacuation needs.</li>
          <li>GPS coordinates are continuously transmitted to the Central Duty Officer.</li>
        </ul>
      </div>

      {/* 4. Active Emergency SOS Form Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-3 backdrop-blur-sm">
          <div className="bg-slate-900 border border-red-800/80 rounded-2xl w-full max-w-md p-4 sm:p-5 space-y-3.5 shadow-2xl shadow-red-950">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-red-400 flex items-center gap-2">
                <LifeBuoy className="w-4 h-4 text-red-400" />
                Request Emergency Assistance
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-200 text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs font-sans">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Assistance Category:
                </label>
                <select
                  value={assistType}
                  onChange={(e) => setAssistType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono text-xs focus:outline-none"
                >
                  {ASSISTANCE_TYPES.map((a) => (
                    <option key={a} value={a}>
                      {a.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Urgency Priority:
                </label>
                <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                  {["HIGH", "CRITICAL"].map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPriority(p)}
                      className={`py-2 rounded font-bold uppercase transition ${
                        priority === p
                          ? "bg-red-600 text-white"
                          : "bg-slate-950 text-slate-400 border border-slate-800"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Situation Details:
                </label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="State personnel count, trapped victims, specialized equipment needed, or impassable road..."
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-xs focus:outline-none"
                />
              </div>

              <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1 bg-slate-950 p-2 rounded-lg border border-slate-800">
                <MapPin className="w-3 h-3 text-red-400" />
                <span>
                  {coords
                    ? `GPS: ${coords.lat.toFixed(4)}°N, ${coords.lon.toFixed(4)}°E`
                    : geoStatus}
                </span>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2.5 rounded-xl font-mono text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !description.trim()}
                  className="flex-1 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white py-2.5 rounded-xl font-mono font-bold text-xs shadow-md shadow-red-950"
                >
                  {isSubmitting ? "Transmitting SOS..." : "Dispatch SOS"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
