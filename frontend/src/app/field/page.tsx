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
    if (!data?.assigned_location?.id || !reportDesc.trim()) return;

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
        event_id: data.assigned_event?.id,
        location_id: data.assigned_location.id,
        team_id: data.team.id,
        reported_by: `${data.team.team_name} (${data.team.callsign})`,
        report_type: reportType,
        severity: reportSeverity,
        description: reportDesc,
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
    <main className="flex-1 p-3 sm:p-4 space-y-3">
      {/* 1. Urgent Directives Broadcast Banner */}
      {unackMessages.length > 0 && (
        <div className="bg-red-950/90 border border-red-800 rounded-xl p-3 space-y-2">
          {unackMessages.map((msg) => (
            <div key={msg.id} className="flex items-start justify-between gap-3 text-xs">
              <div className="flex items-start gap-2">
                <AlertOctagon className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                <div>
                  <div className="font-mono text-[10px] font-bold uppercase text-red-300">
                    URGENT CENTRAL DIRECTIVE [{msg.priority}]:
                  </div>
                  <p className="text-slate-100 font-medium leading-snug">{msg.message}</p>
                </div>
              </div>
              <button
                onClick={() => handleAcknowledge(msg.id)}
                disabled={acknowledgingMsgId === msg.id}
                className="bg-red-600 hover:bg-red-500 text-white font-mono text-[10px] px-2.5 py-1.5 rounded font-bold transition shrink-0"
              >
                {acknowledgingMsgId === msg.id ? "Syncing..." : "ACKNOWLEDGE"}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 2. Active Sector Assignment Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-3 shadow-md">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
            Tactical Sector Assignment
          </span>
          <span className="text-[10px] font-mono text-indigo-400">
            {data?.assigned_location?.name || "NER Assigned Sector"}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-mono">Landslide Hazard Severity</div>
            <div
              className={`text-lg sm:text-xl font-bold font-mono mt-0.5 ${
                data?.assigned_event?.severity === "CRITICAL"
                  ? "text-red-400"
                  : data?.assigned_event?.severity === "HIGH"
                  ? "text-amber-400"
                  : "text-yellow-400"
              }`}
            >
              {data?.assigned_event?.severity || "MONITORING"} LEVEL
            </div>
          </div>

          <div className="text-right">
            <div className="text-[10px] text-slate-400 font-mono">Assessment Confidence</div>
            <div className="text-sm sm:text-base font-bold text-slate-200 font-mono">
              {((data?.assigned_event?.confidence_score ?? 0.82) * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80">
          {data?.assigned_event?.summary ||
            "Deterministic environmental monitoring active. Field rescue units on active patrol."}
        </p>
      </div>

      {/* 3. Immediate Ground Conditions Matrix */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-2">
        <div className="text-[10px] font-mono uppercase text-slate-400 font-bold flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
          Immediate Ground Conditions (At-A-Glance):
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400 text-[11px]">Slope Risk:</span>
            <span className="font-bold text-amber-400">
              {data?.immediate_conditions?.slope_risk || "UNKNOWN"}
            </span>
          </div>

          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400 text-[11px]">Rainfall:</span>
            <span className="font-bold text-indigo-300">
              {data?.immediate_conditions?.rainfall_state || "UNKNOWN"}
            </span>
          </div>

          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400 text-[11px]">Soil Moisture:</span>
            <span className="font-bold text-red-400">
              {data?.immediate_conditions?.soil_saturation_state || "UNKNOWN"}
            </span>
          </div>

          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400 text-[11px]">Road Passability:</span>
            <span className="font-bold text-emerald-400 truncate ml-1">
              {data?.immediate_conditions?.road_status || "UNKNOWN"}
            </span>
          </div>
        </div>
      </div>

      {/* 4. Primary Action Quick Buttons */}
      <div className="grid grid-cols-2 gap-2.5 pt-1">
        <button
          onClick={() => setShowQuickReport(true)}
          className="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-bold py-3 px-3 rounded-xl flex flex-col items-center justify-center gap-1 shadow-md shadow-indigo-950 font-mono transition"
        >
          <Send className="w-4 h-4" />
          <span className="text-xs">REPORT SITUATION</span>
        </button>

        <Link
          href="/field/assistance"
          className="bg-red-600 hover:bg-red-500 active:bg-red-700 text-white font-bold py-3 px-3 rounded-xl flex flex-col items-center justify-center gap-1 shadow-md shadow-red-950 font-mono transition text-center"
        >
          <LifeBuoy className="w-4 h-4" />
          <span className="text-xs">NEED ASSISTANCE</span>
        </Link>
      </div>

      {/* 5. Navigation Hub Cards */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
        <Link
          href="/field/reports"
          className="bg-slate-900 hover:bg-slate-850 p-3 rounded-xl border border-slate-800 flex items-center justify-between transition group"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            <div>
              <div className="font-bold text-slate-200">Reports Feed</div>
              <div className="text-[10px] text-slate-500">
                {data?.recent_reports?.length || 0} Ground Reports
              </div>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-300" />
        </Link>

        <Link
          href="/field/messages"
          className="bg-slate-900 hover:bg-slate-850 p-3 rounded-xl border border-slate-800 flex items-center justify-between transition group"
        >
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-amber-400" />
            <div>
              <div className="font-bold text-slate-200">Directives</div>
              <div className="text-[10px] text-slate-500">
                {unackMessages.length > 0 ? `${unackMessages.length} Pending` : "All Ack'd"}
              </div>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-300" />
        </Link>
      </div>

      {/* --- QUICK REPORT MODAL --- */}
      {showQuickReport && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-3 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-4 sm:p-5 space-y-3.5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Send className="w-4 h-4 text-indigo-400" />
                Submit Ground Observation
              </h3>
              <button
                onClick={() => setShowQuickReport(false)}
                className="text-slate-400 hover:text-slate-200 text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleQuickReportSubmit} className="space-y-3 text-xs font-sans">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Report Hazard Category:
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono text-xs focus:outline-none"
                >
                  {[
                    "LANDSLIDE_OBSERVED",
                    "ROAD_BLOCKED",
                    "WATER_MUD_FLOW",
                    "INFRASTRUCTURE_DAMAGE",
                    "PEOPLE_TRAPPED",
                    "INJURIES",
                    "OTHER",
                  ].map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Observed Severity:
                </label>
                <div className="grid grid-cols-4 gap-1 font-mono text-[11px]">
                  {["LOW", "MODERATE", "HIGH", "CRITICAL"].map((sev) => (
                    <button
                      key={sev}
                      type="button"
                      onClick={() => setReportSeverity(sev)}
                      className={`py-1.5 rounded font-bold uppercase transition ${
                        reportSeverity === sev
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-950 text-slate-400 border border-slate-800"
                      }`}
                    >
                      {sev}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Description / Situation:
                </label>
                <textarea
                  rows={3}
                  value={reportDesc}
                  onChange={(e) => setReportDesc(e.target.value)}
                  placeholder="Describe slope movement, road obstruction, mudflow..."
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-xs focus:outline-none"
                />
              </div>

              {/* Image attachment section */}
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Attach Photo Evidence:
                </label>
                <div className="flex items-center gap-2">
                  <label className="cursor-pointer bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 px-3 py-1.5 rounded-lg font-mono text-[11px] flex items-center gap-1.5 transition">
                    <Camera className="w-3.5 h-3.5 text-indigo-400" />
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
                        className="w-8 h-8 object-cover rounded border border-slate-700"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedFile(null);
                          setFilePreview(null);
                        }}
                        className="text-[10px] text-red-400 hover:text-red-300 font-mono"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* GPS metadata banner */}
              <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1.5 bg-slate-950 p-2 rounded-lg border border-slate-800">
                <MapPin className="w-3 h-3 text-indigo-400 shrink-0" />
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
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2.5 rounded-xl font-mono text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !reportDesc.trim()}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white py-2.5 rounded-xl font-mono font-bold text-xs shadow-md shadow-indigo-950"
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
