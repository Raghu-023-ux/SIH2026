"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Send,
  LifeBuoy,
  AlertOctagon,
  Activity,
  MapPin,
  FileText,
  Bell,
  ChevronRight,
  Shield,
  Clock,
  Camera,
  Image as ImageIcon,
  CheckCircle2,
} from "lucide-react";
import { useField } from "@/components/field/FieldContext";

export default function FieldTacticalOverviewPage() {
  const {
    callsign,
    data,
    loading,
    coords,
    geoStatus,
    geoSource,
    acknowledgeMessage,
    refreshBriefing,
    apiUrl,
  } = useField();

  const [acknowledgingMsgId, setAcknowledgingMsgId] = useState<string | null>(null);

  // Quick report modal
  const [showQuickReport, setShowQuickReport] = useState<boolean>(false);
  const [reportType, setReportType] = useState<string>("LANDSLIDE_OBSERVED");
  const [reportSeverity, setReportSeverity] = useState<string>("HIGH");
  const [reportDesc, setReportDesc] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);

  const unackMessages = data?.recent_messages?.filter((m) => !m.acknowledged_at) || [];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setSelectedFile(f);
      const url = URL.createObjectURL(f);
      setFilePreview(url);
    }
  };

  const handleAcknowledge = async (id: string) => {
    setAcknowledgingMsgId(id);
    await acknowledgeMessage(id);
    setAcknowledgingMsgId(null);
  };

  const handleQuickReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportDesc.trim()) return;

    setIsSubmitting(true);
    try {
      let imageKeys: string[] = [];
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        const upRes = await fetch(`${apiUrl}/api/v1/field/upload-image?uploaded_by=${callsign}`, {
          method: "POST",
          body: formData,
        });
        if (upRes.ok) {
          const upData = await upRes.json();
          imageKeys.push(upData.storage_key);
        }
      }

      const payload = {
        event_id: data?.assigned_event?.id,
        location_id: data?.assigned_location?.id || "NER-SIK-GANGTOK-01",
        team_id: data?.team?.id || "NER-TEAM-ALPHA",
        reported_by: `${data?.team?.team_name || "Rescue Unit"} (${callsign})`,
        report_type: reportType,
        severity: reportSeverity,
        description: reportDesc.trim(),
        latitude: coords?.lat,
        longitude: coords?.lon,
        location_accuracy: coords?.accuracy || 15.0,
        location_source: geoSource,
        image_storage_keys: imageKeys,
      };

      const res = await fetch(`${apiUrl}/api/v1/field/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setReportDesc("");
        setSelectedFile(null);
        setFilePreview(null);
        setShowQuickReport(false);
        await refreshBriefing();
      }
    } catch (err) {
      console.error("Submission error", err);
      alert("Network error: Please retry submission.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex-1 p-3 sm:p-4 space-y-3 font-sans text-white bg-black">
      {/* 1. Urgent Directives Broadcast Banner */}
      {unackMessages.length > 0 && (
        <div className="bg-red-950/90 border border-red-700 rounded p-3 space-y-2">
          {unackMessages.map((msg) => (
            <div key={msg.id} className="flex items-start justify-between gap-3 text-xs font-mono">
              <div className="flex items-start gap-2">
                <AlertOctagon className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                <div>
                  <div className="text-[10px] font-black uppercase text-red-300">
                    URGENT CENTRAL DIRECTIVE [{msg.priority}]:
                  </div>
                  <p className="text-white font-bold leading-snug font-sans">{msg.message}</p>
                </div>
              </div>
              <button
                onClick={() => handleAcknowledge(msg.id)}
                disabled={acknowledgingMsgId === msg.id}
                className="bg-red-600 hover:bg-red-500 text-white font-mono text-[10px] px-2.5 py-1.5 rounded font-black transition shrink-0 shadow-sm"
              >
                {acknowledgingMsgId === msg.id ? "Syncing..." : "ACKNOWLEDGE"}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 2. Active Sector Assignment Card */}
      <div className="bg-zinc-950 border border-zinc-800 rounded p-3.5 space-y-3 shadow-md">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-bold">
            Tactical Sector Assignment
          </span>
          <span className="text-[10px] font-mono text-white font-bold">
            {data?.assigned_location?.name || "Gangtok Hill Station"}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="text-[10px] text-zinc-400 font-mono font-bold">Landslide Hazard Severity</div>
            <div
              className={`text-lg sm:text-xl font-black font-mono mt-0.5 ${
                data?.assigned_event?.severity === "CRITICAL"
                  ? "text-red-400"
                  : data?.assigned_event?.severity === "HIGH"
                  ? "text-orange-400"
                  : "text-amber-400"
              }`}
            >
              {data?.assigned_event?.severity || "HIGH"} LEVEL
            </div>
          </div>

          <div className="text-right">
            <div className="text-[10px] text-zinc-400 font-mono font-bold">Assessment Confidence</div>
            <div className="text-sm sm:text-base font-black text-white font-mono">
              {((data?.assigned_event?.confidence_score ?? 0.88) * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        <p className="text-xs text-zinc-300 leading-relaxed font-sans bg-black p-2.5 rounded border border-zinc-800">
          {data?.assigned_event?.summary ||
            "Deterministic environmental monitoring active. Field rescue units on active patrol."}
        </p>
      </div>

      {/* 3. Immediate Ground Conditions Matrix */}
      <div className="bg-zinc-950 border border-zinc-800 rounded p-3.5 space-y-2">
        <div className="text-[10px] font-mono uppercase text-zinc-300 font-bold flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-zinc-400" />
          Immediate Ground Conditions (At-A-Glance):
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <div className="bg-black p-2 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400 text-[11px] font-bold">Slope Risk:</span>
            <span className="font-black text-orange-400">
              {data?.immediate_conditions?.slope_risk || "HIGH"}
            </span>
          </div>

          <div className="bg-black p-2 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400 text-[11px] font-bold">Rainfall:</span>
            <span className="font-black text-white">
              {data?.immediate_conditions?.rainfall_state || "MODERATE"}
            </span>
          </div>

          <div className="bg-black p-2 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400 text-[11px] font-bold">Soil Moisture:</span>
            <span className="font-black text-red-400">
              {data?.immediate_conditions?.soil_saturation_state || "HIGH"}
            </span>
          </div>

          <div className="bg-black p-2 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400 text-[11px] font-bold">Road Status:</span>
            <span className="font-black text-emerald-400 truncate ml-1">
              {data?.immediate_conditions?.road_status || "PASSABLE WITH CAUTION"}
            </span>
          </div>
        </div>
      </div>

      {/* 4. Primary Action Quick Buttons */}
      <div className="grid grid-cols-2 gap-2.5 pt-1">
        <button
          onClick={() => setShowQuickReport(true)}
          className="bg-white hover:bg-zinc-200 active:bg-zinc-300 text-black font-black py-3 px-3 rounded flex flex-col items-center justify-center gap-1 shadow-md font-mono transition"
        >
          <Send className="w-4 h-4" />
          <span className="text-xs">REPORT SITUATION</span>
        </button>

        <Link
          href="/field/assistance"
          className="bg-red-600 hover:bg-red-500 active:bg-red-700 text-white font-black py-3 px-3 rounded flex flex-col items-center justify-center gap-1 shadow-md font-mono transition text-center"
        >
          <LifeBuoy className="w-4 h-4" />
          <span className="text-xs">NEED ASSISTANCE</span>
        </Link>
      </div>

      {/* 5. Navigation Hub Cards */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
        <Link
          href="/field/reports"
          className="bg-zinc-950 hover:bg-zinc-900 p-3 rounded border border-zinc-800 flex items-center justify-between transition group"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-white" />
            <div>
              <div className="font-black text-white">Reports Feed</div>
              <div className="text-[10px] text-zinc-500">
                {data?.recent_reports?.length || 0} Ground Reports
              </div>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-white" />
        </Link>

        <Link
          href="/field/messages"
          className="bg-zinc-950 hover:bg-zinc-900 p-3 rounded border border-zinc-800 flex items-center justify-between transition group"
        >
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-amber-400" />
            <div>
              <div className="font-black text-white">Directives</div>
              <div className="text-[10px] text-zinc-500">
                {unackMessages.length > 0 ? `${unackMessages.length} Pending` : "All Ack'd"}
              </div>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-white" />
        </Link>
      </div>

      {/* --- QUICK REPORT MODAL --- */}
      {showQuickReport && (
        <div className="fixed inset-0 bg-black/85 z-50 flex items-center justify-center p-3 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-zinc-800 rounded w-full max-w-md p-4 sm:p-5 space-y-3.5 shadow-2xl text-white">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
              <h3 className="text-sm font-black text-white flex items-center gap-2 font-mono uppercase tracking-wider">
                <Send className="w-4 h-4" />
                Submit Ground Observation
              </h3>
              <button
                onClick={() => setShowQuickReport(false)}
                className="text-zinc-400 hover:text-white text-xs font-mono font-bold"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleQuickReportSubmit} className="space-y-3 text-xs font-sans">
              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                  Report Hazard Category:
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full bg-black border border-zinc-800 rounded p-2 text-white font-mono text-xs focus:outline-none focus:border-zinc-600"
                >
                  <option value="LANDSLIDE_OBSERVED">Landslide Movement / Slip</option>
                  <option value="ROAD_BLOCKED">Road Blocked / Debris</option>
                  <option value="WATER_MUD_FLOW">Water / Mud Flow Surge</option>
                  <option value="INFRASTRUCTURE_DAMAGE">Bridge / Structure Damage</option>
                  <option value="PEOPLE_TRAPPED">People Trapped (Urgent)</option>
                  <option value="OTHER">Other Ground Observation</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                  Severity:
                </label>
                <div className="grid grid-cols-3 gap-2 font-mono text-[11px]">
                  {["MODERATE", "HIGH", "CRITICAL"].map((sev) => (
                    <button
                      key={sev}
                      type="button"
                      onClick={() => setReportSeverity(sev)}
                      className={`py-1.5 rounded font-black uppercase transition text-center ${
                        reportSeverity === sev
                          ? "bg-white text-black font-black"
                          : "bg-black text-zinc-400 border border-zinc-800 hover:text-white"
                      }`}
                    >
                      {sev}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                  Field Description:
                </label>
                <textarea
                  rows={3}
                  value={reportDesc}
                  onChange={(e) => setReportDesc(e.target.value)}
                  placeholder="Describe slope movement, road obstruction, mudflow..."
                  required
                  className="w-full bg-black border border-zinc-800 rounded p-2 text-white text-xs focus:outline-none focus:border-zinc-600 leading-relaxed"
                />
              </div>

              {/* Image attachment section */}
              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                  Attach Photo Evidence:
                </label>
                <div className="flex items-center gap-2">
                  <label className="cursor-pointer bg-black hover:bg-zinc-900 border border-zinc-800 text-white px-3 py-1.5 rounded font-mono text-[11px] flex items-center gap-1.5 transition font-bold">
                    <Camera className="w-3.5 h-3.5 text-white" />
                    <span>Camera / Gallery</span>
                    <input
                      type="file"
                      accept="image/*"
                      capture="environment"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                  {filePreview && (
                    <div className="flex items-center gap-2">
                      <img
                        src={filePreview}
                        alt="Preview"
                        className="w-8 h-8 object-cover rounded border border-zinc-700"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedFile(null);
                          setFilePreview(null);
                        }}
                        className="text-[10px] text-red-400 hover:text-red-300 font-mono font-bold"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* GPS metadata banner */}
              <div className="text-[10px] text-zinc-400 font-mono flex items-center gap-1.5 bg-black p-2 rounded border border-zinc-800">
                <MapPin className="w-3 h-3 text-white shrink-0" />
                <span>
                  {coords
                    ? `GPS: ${coords.lat.toFixed(4)}°N, ${coords.lon.toFixed(4)}°E (±${coords.accuracy || 15}m)`
                    : geoStatus}
                </span>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowQuickReport(false)}
                  className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 py-2.5 rounded font-mono text-xs font-bold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !reportDesc.trim()}
                  className="flex-1 bg-white hover:bg-zinc-200 disabled:opacity-50 text-black py-2.5 rounded font-mono font-black text-xs shadow-sm transition"
                >
                  {isSubmitting ? "Submitting..." : "Send Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
