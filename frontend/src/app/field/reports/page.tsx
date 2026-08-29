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
        team_id: data?.team?.id || "NER-TEAM-ALPHA",
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
      console.error("Failed to submit report", err);
      alert("Failed to transmit field observation.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const reports = data?.recent_reports || [];
  const filteredReports =
    activeFilter === "ALL"
      ? reports
      : reports.filter((r) => r.report_type === activeFilter || r.severity === activeFilter);

  return (
    <main className="flex-1 p-3 sm:p-4 space-y-3.5 font-sans text-white bg-black">
      {/* 1. Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-black text-white flex items-center gap-2 font-mono uppercase tracking-wider">
            <FileText className="w-4 h-4 text-white" />
            Field Ground Truth Reports
          </h2>
          <p className="text-[11px] text-zinc-400 font-mono">
            Ground observations, geotagged photos, and structural damage reports
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="bg-white hover:bg-zinc-200 text-black font-mono font-black text-xs px-3 py-2 rounded flex items-center gap-1.5 shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Report</span>
        </button>
      </div>

      {/* 2. Filter Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] font-mono scrollbar-none">
        <span className="text-zinc-500 text-[10px] uppercase font-bold flex items-center gap-1 pl-1">
          <Filter className="w-3 h-3 text-zinc-400" /> Filter:
        </span>
        {["ALL", "CRITICAL", "HIGH", "LANDSLIDE_OBSERVED", "ROAD_BLOCKED"].map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={`px-2.5 py-1 rounded font-bold uppercase transition whitespace-nowrap ${
              activeFilter === f
                ? "bg-white text-black font-black shadow-sm"
                : "bg-zinc-950 text-zinc-400 border border-zinc-800 hover:text-white"
            }`}
          >
            {f.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {/* 3. Reports Stream */}
      <div className="space-y-2.5">
        {filteredReports.length > 0 ? (
          filteredReports.map((rep) => (
            <div
              key={rep.id}
              className="bg-zinc-950 border border-zinc-800 rounded p-3.5 space-y-2.5 shadow-md text-xs font-mono"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${
                      rep.severity === "CRITICAL"
                        ? "bg-red-950 text-red-300 border border-red-700"
                        : rep.severity === "HIGH"
                        ? "bg-orange-950 text-orange-300 border border-orange-700"
                        : "bg-amber-950 text-amber-300 border border-amber-700"
                    }`}
                  >
                    {rep.severity}
                  </span>
                  <span className="font-bold text-white text-[11px]">
                    {rep.report_type.replace(/_/g, " ")}
                  </span>
                </div>

                <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(rep.timestamp).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>

              <p className="text-zinc-200 text-xs font-sans leading-relaxed">{rep.description}</p>

              {/* Photo Evidence Thumbnails */}
              {rep.images && rep.images.length > 0 && (
                <div className="flex items-center gap-2 pt-1">
                  {rep.images.map((img) => (
                    <button
                      key={img.id}
                      type="button"
                      onClick={() => setSelectedImageModal(img.url)}
                      className="relative w-14 h-14 rounded overflow-hidden border border-zinc-700 hover:border-white transition shrink-0 group"
                    >
                      <img
                        src={img.url}
                        alt="Evidence"
                        className="w-full h-full object-cover group-hover:scale-105 transition"
                      />
                    </button>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-between pt-1 border-t border-zinc-800 text-[10px] text-zinc-400">
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-zinc-500" />
                  <span>
                    {rep.latitude && rep.longitude
                      ? `${rep.latitude.toFixed(4)}°N, ${rep.longitude.toFixed(4)}°E`
                      : "GPS Sector Assigned"}
                  </span>
                </div>
                <span className="text-zinc-500 font-bold">{rep.reported_by}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-zinc-950 border border-zinc-800 rounded p-6 text-center space-y-2 font-mono">
            <FileText className="w-6 h-6 text-zinc-600 mx-auto" />
            <div className="text-zinc-400 text-xs font-bold">No ground reports filed yet</div>
            <p className="text-zinc-600 text-[11px]">
              Ground situation reports submitted by your unit or neighbor teams will appear here.
            </p>
          </div>
        )}
      </div>

      {/* 4. Full Geotagged Report Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/85 z-50 flex items-center justify-center p-3 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-zinc-800 rounded w-full max-w-md p-4 sm:p-5 space-y-3.5 shadow-2xl text-white font-sans">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
              <h3 className="text-sm font-black text-white flex items-center gap-2 font-mono uppercase">
                <Send className="w-4 h-4" />
                Submit Ground Observation
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
                  Observation Type:
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full bg-black border border-zinc-800 rounded p-2 text-white font-mono text-xs focus:outline-none focus:border-zinc-600"
                >
                  {REPORT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
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
                      onClick={() => setSeverity(sev)}
                      className={`py-1.5 rounded font-black uppercase transition ${
                        severity === sev
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
                  Field Notes &amp; Description:
                </label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detail slope movement, debris blockage, water flow surge, or affected population..."
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
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 py-2.5 rounded font-mono text-xs font-bold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !description.trim()}
                  className="flex-1 bg-white hover:bg-zinc-200 disabled:opacity-50 text-black py-2.5 rounded font-mono font-black text-xs shadow-sm transition"
                >
                  {isSubmitting ? "Transmitting..." : "Send Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 5. Image Lightbox Modal */}
      {selectedImageModal && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-3 backdrop-blur-md"
          onClick={() => setSelectedImageModal(null)}
        >
          <div className="relative max-w-2xl max-h-[85vh] overflow-hidden rounded border border-zinc-800 bg-black">
            <img
              src={selectedImageModal}
              alt="Full evidence view"
              className="max-h-[80vh] w-auto object-contain mx-auto"
            />
            <button
              onClick={() => setSelectedImageModal(null)}
              className="absolute top-2 right-2 bg-black/80 text-white p-1 rounded font-mono text-xs border border-zinc-700"
            >
              ✕ Close
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
