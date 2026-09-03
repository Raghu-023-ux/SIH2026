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
    <main className="flex-1 p-3 sm:p-4 space-y-3.5 font-sans text-white bg-black">
      {/* 1. Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-black text-white flex items-center gap-2 font-mono uppercase tracking-wider">
            <LifeBuoy className="w-4 h-4 text-red-500" />
            Field Assistance &amp; SOS Portal
          </h2>
          <p className="text-[11px] text-zinc-400 font-mono">
            Emergency reinforcements &amp; logistics dispatch for {callsign}
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="bg-red-600 hover:bg-red-500 text-white font-mono font-black text-xs px-3 py-2 rounded flex items-center gap-1.5 shadow-md shadow-red-950 transition"
        >
          <Plus className="w-4 h-4" />
          <span>Dispatch SOS</span>
        </button>
      </div>

      {/* 2. Unit Status SOS Banner */}
      {isNeedAssist && (
        <div className="bg-red-950 border border-red-700 rounded p-3.5 space-y-1 shadow-lg">
          <div className="flex items-center gap-2 text-xs font-black text-red-300 font-mono">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span>UNIT BROADCASTING ACTIVE SOS</span>
          </div>
          <p className="text-xs text-zinc-200">
            Headquarters and neighboring response units have been alerted to your distress call.
          </p>
        </div>
      )}

      {/* 3. Instructions / Quick Guide */}
      <div className="bg-zinc-950 border border-zinc-800 rounded p-3.5 space-y-2 text-xs font-mono">
        <span className="text-[10px] font-black text-white uppercase tracking-wider">
          Tactical SOS Protocol
        </span>
        <ul className="space-y-1 text-zinc-400 text-[11px] list-disc list-inside font-sans">
          <li>Select <strong className="text-white">CRITICAL</strong> priority for life-threatening or trapped victim scenarios.</li>
          <li>Specify road blockages, heavy excavation requirements, or aerial medical evacuation needs.</li>
          <li>GPS coordinates are continuously transmitted to the Central Duty Officer.</li>
        </ul>
      </div>

      {/* 4. Active Emergency SOS Form Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/85 z-50 flex items-center justify-center p-3 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-red-700 rounded w-full max-w-md p-4 sm:p-5 space-y-3.5 shadow-2xl text-white font-sans">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
              <h3 className="text-sm font-black text-red-400 flex items-center gap-2 font-mono uppercase">
                <LifeBuoy className="w-4 h-4 text-red-400" />
                Request Emergency Assistance
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-zinc-400 hover:text-white text-xs font-mono font-bold"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3 text-xs font-sans">
              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                  Assistance Category:
                </label>
                <select
                  value={assistType}
                  onChange={(e) => setAssistType(e.target.value)}
                  className="w-full bg-black border border-zinc-800 rounded p-2 text-white font-mono text-xs focus:outline-none focus:border-zinc-600"
                >
                  {ASSISTANCE_TYPES.map((a) => (
                    <option key={a} value={a}>
                      {a.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                  Urgency Priority:
                </label>
                <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                  {["HIGH", "CRITICAL"].map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPriority(p)}
                      className={`py-2 rounded font-black uppercase transition ${
                        priority === p
                          ? "bg-red-600 text-white"
                          : "bg-black text-zinc-400 border border-zinc-800 hover:text-white"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                  Situation Details:
                </label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="State personnel count, trapped victims, specialized equipment needed, or impassable road..."
                  required
                  className="w-full bg-black border border-zinc-800 rounded p-2 text-white text-xs focus:outline-none focus:border-zinc-600 leading-relaxed"
                />
              </div>

              <div className="text-[10px] text-zinc-400 font-mono flex items-center gap-1 bg-black p-2 rounded border border-zinc-800">
                <MapPin className="w-3 h-3 text-red-400" />
                <span>
                  {coords
                    ? `GPS: ${coords.lat.toFixed(4)}°N, ${coords.lon.toFixed(4)}°E (±${coords.accuracy || 15}m)`
                    : geoStatus}
                </span>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 py-2.5 rounded font-mono text-xs font-bold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !description.trim()}
                  className="flex-1 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white py-2.5 rounded font-mono font-black text-xs shadow-md transition"
                >
                  {isSubmitting ? "Transmitting..." : "DISPATCH SOS NOW"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
