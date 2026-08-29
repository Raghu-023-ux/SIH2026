"use client";

import React, { useState } from "react";
import {
  FileText,
  Camera,
  Image as ImageIcon,
  MapPin,
  Send,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Plus,
  LocateFixed,
  Filter,
  X,
} from "lucide-react";
import { useField } from "@/components/field/FieldContext";

const REPORT_TYPES = [
  "LANDSLIDE_OBSERVED",
  "ROAD_BLOCKED",
  "WATER_MUD_FLOW",
  "INFRASTRUCTURE_DAMAGE",
  "PEOPLE_TRAPPED",
  "INJURIES",
  "VISIBILITY_ISSUE",
  "COMMUNICATION_FAILURE",
  "OTHER",
];

export default function FieldReportsPage() {
  const {
    callsign,
    data,
    coords,
    geoStatus,
    geoSource,
    requestGPSLocation,
    refreshBriefing,
    apiUrl,
  } = useField();

  // Form State
  const [showModal, setShowModal] = useState<boolean>(false);
  const [reportType, setReportType] = useState<string>("LANDSLIDE_OBSERVED");
  const [severity, setSeverity] = useState<string>("HIGH");
  const [description, setDescription] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<string>("ALL");
  const [selectedImageModal, setSelectedImageModal] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setSelectedFile(f);
      const url = URL.createObjectURL(f);
      setFilePreview(url);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

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
        team_id: data?.team?.id,
        reported_by: `${data?.team?.team_name || "Rescue Unit"} (${callsign})`,
        report_type: reportType,
        severity: severity,
        description: description.trim(),
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
        setDescription("");
        setSelectedFile(null);
        setFilePreview(null);
        setShowModal(false);
        await refreshBriefing();
      }
    } catch (err) {
      console.error("Report submit error", err);
      alert("Submission failed. Please check connection.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const reports = data?.recent_reports || [];
  const filteredReports = activeFilter === "ALL"
    ? reports
    : reports.filter((r) => r.status === activeFilter || r.severity === activeFilter);

  return (
    <main className="flex-1 p-3 sm:p-4 space-y-3.5">
      {/* 1. Header & Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            Field &amp; Citizen Reports Log
          </h2>
          <p className="text-[11px] text-slate-400 font-mono">
            Ground observations submitted in current sector
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-mono font-bold text-xs px-3 py-2 rounded-xl flex items-center gap-1.5 shadow-md shadow-indigo-950 transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Report</span>
        </button>
      </div>

      {/* 2. Filter Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto text-[11px] font-mono pb-1 scrollbar-none">
        {["ALL", "SUBMITTED", "UNDER_REVIEW", "REVIEWED", "CRITICAL", "HIGH"].map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={`px-2.5 py-1 rounded-lg transition whitespace-nowrap ${
              activeFilter === f
                ? "bg-indigo-600 text-white font-bold"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            {f.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* 3. Reports List */}
      <div className="space-y-2.5">
        {filteredReports.length > 0 ? (
          filteredReports.map((rep) => (
            <div
              key={rep.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-2 text-xs shadow-md"
            >
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="font-bold text-indigo-400">
                  {rep.report_type.replace(/_/g, " ")}
                </span>
                <div className="flex items-center gap-1.5">
                  <span
                    className={`px-1.5 py-0.5 rounded uppercase font-bold text-[9px] ${
                      rep.severity === "CRITICAL"
                        ? "bg-red-500/20 text-red-400 border border-red-500/40"
                        : rep.severity === "HIGH"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        : "bg-yellow-500/20 text-yellow-400 border border-yellow-500/40"
                    }`}
                  >
                    {rep.severity}
                  </span>
                  <span className="px-1.5 py-0.5 rounded uppercase font-bold text-[9px] bg-slate-950 text-slate-400 border border-slate-800">
                    {rep.status}
                  </span>
                </div>
              </div>

              <p className="text-slate-200 text-xs leading-relaxed">{rep.description}</p>

              {/* Photo Evidence Thumbnails */}
              {rep.images && rep.images.length > 0 && (
                <div className="flex items-center gap-2 pt-1">
                  {rep.images.map((img) => (
                    <button
                      key={img.id}
                      type="button"
                      onClick={() => setSelectedImageModal(`${apiUrl}${img.url}`)}
                      className="group relative rounded-lg overflow-hidden border border-slate-700 hover:border-indigo-400 transition"
                    >
                      <img
                        src={`${apiUrl}${img.url}`}
                        alt="Evidence"
                        className="w-14 h-14 object-cover group-hover:scale-105 transition"
                      />
                      <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                        <ImageIcon className="w-3.5 h-3.5 text-white" />
                      </div>
                    </button>
                  ))}
                </div>
              )}

              <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between pt-1 border-t border-slate-800/80">
                <span className="truncate max-w-[180px]">By: {rep.reported_by}</span>
                <span className="flex items-center gap-1 shrink-0">
                  <Clock className="w-3 h-3 text-slate-600" />
                  {new Date(rep.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>

              {rep.latitude && rep.longitude && (
                <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-indigo-400" />
                  <span>
                    {rep.latitude.toFixed(4)}°N, {rep.longitude.toFixed(4)}°E
                    {rep.location_accuracy ? ` (±${rep.location_accuracy.toFixed(0)}m)` : ""}
                  </span>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs font-mono">
            No field reports found matching the selected filter.
          </div>
        )}
      </div>

      {/* --- SUBMIT REPORT MODAL --- */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-3 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-4 sm:p-5 space-y-3.5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Send className="w-4 h-4 text-indigo-400" />
                Submit Ground Observation Report
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
                  Hazard Category:
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono text-xs focus:outline-none"
                >
                  {REPORT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Severity Level:
                </label>
                <div className="grid grid-cols-4 gap-1 font-mono text-[11px]">
                  {["LOW", "MODERATE", "HIGH", "CRITICAL"].map((sev) => (
                    <button
                      key={sev}
                      type="button"
                      onClick={() => setSeverity(sev)}
                      className={`py-1.5 rounded font-bold uppercase transition ${
                        severity === sev
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
                  Field Description / Ground Observation:
                </label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe slope movement, cracks in road, debris volume, trapped vehicles..."
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-xs focus:outline-none"
                />
              </div>

              {/* Photo Evidence Capture (Camera / Gallery) */}
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

              {/* GPS Location Tagging */}
              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between text-[10px] font-mono">
                <div className="flex items-center gap-1.5 text-slate-400 truncate">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span className="truncate">
                    {coords
                      ? `GPS: ${coords.lat.toFixed(4)}°N, ${coords.lon.toFixed(4)}°E (±${coords.accuracy || 15}m)`
                      : geoStatus}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => requestGPSLocation()}
                  className="text-indigo-400 hover:text-indigo-300 font-bold shrink-0 ml-2"
                >
                  Refresh GPS
                </button>
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
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white py-2.5 rounded-xl font-mono font-bold text-xs shadow-md shadow-indigo-950"
                >
                  {isSubmitting ? "Transmitting..." : "Submit Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- IMAGE FULL PREVIEW MODAL --- */}
      {selectedImageModal && (
        <div
          className="fixed inset-0 bg-black/90 z-[60] flex items-center justify-center p-4 backdrop-blur-md"
          onClick={() => setSelectedImageModal(null)}
        >
          <div className="relative max-w-lg w-full bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
            <button
              onClick={() => setSelectedImageModal(null)}
              className="absolute top-2 right-2 bg-slate-950/80 hover:bg-slate-800 text-white p-1.5 rounded-full"
            >
              <X className="w-4 h-4" />
            </button>
            <img
              src={selectedImageModal}
              alt="Evidence Full View"
              className="w-full h-auto max-h-[75vh] object-contain"
            />
          </div>
        </div>
      )}
    </main>
  );
}
