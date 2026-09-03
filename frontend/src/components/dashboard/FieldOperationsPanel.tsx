"use client";

import React, { useState } from "react";
import {
  Radio,
  Send,
  LifeBuoy,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Users,
  Clock,
  Shield,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  MapPin,
  ExternalLink,
  X,
  Image as ImageIcon,
} from "lucide-react";
import Link from "next/link";

interface FieldTeamItem {
  id: string;
  team_name: string;
  callsign: string;
  status: string;
  latitude?: number | null;
  longitude?: number | null;
  contact_channel?: string | null;
}

interface FieldReportImageItem {
  id: string;
  url: string;
  mime_type: string;
  storage_key?: string;
}

interface FieldReportItem {
  id: string;
  event_id?: string | null;
  location_id: string;
  team_id?: string | null;
  reported_by: string;
  report_type: string;
  severity: string;
  description: string;
  timestamp: string;
  status: string;
  latitude?: number | null;
  longitude?: number | null;
  location_accuracy?: number | null;
  images?: FieldReportImageItem[];
  reviewed_by?: string | null;
}

interface AssistanceRequestItem {
  id: string;
  team_id: string;
  request_type: string;
  priority: string;
  description: string;
  latitude?: number | null;
  longitude?: number | null;
  timestamp: string;
  status: string;
}

interface OperationalMessageItem {
  id: string;
  sender_type: string;
  sender_name: string;
  recipient_type: string;
  recipient_id?: string | null;
  priority: string;
  message_text: string;
  timestamp: string;
  status: string;
}

interface FieldOperationsSummary {
  teams_deployed: number;
  teams_on_scene: number;
  teams_need_assistance: number;
  unacknowledged_reports_count: number;
  active_assistance_requests_count: number;
  recent_reports: FieldReportItem[];
  teams: FieldTeamItem[];
  assistance_requests: AssistanceRequestItem[];
  recent_messages: OperationalMessageItem[];
}

interface FieldOperationsPanelProps {
  summary: FieldOperationsSummary | null;
  apiUrl: string;
  onRefresh: () => void;
}

export default function FieldOperationsPanel({
  summary,
  apiUrl,
  onRefresh,
}: FieldOperationsPanelProps) {
  const [recipient, setRecipient] = useState<string>("ALL_FIELD_TEAMS");
  const [priority, setPriority] = useState<string>("IMPORTANT");
  const [directiveText, setDirectiveText] = useState<string>("");
  const [isBroadcasting, setIsBroadcasting] = useState<boolean>(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [selectedImageModal, setSelectedImageModal] = useState<string | null>(null);

  // Handle Broadcast Directive to Field
  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!directiveText.trim()) return;

    setIsBroadcasting(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/field/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender_type: "CENTRAL_COMMAND",
          sender_name: "Central Intelligence HQ",
          recipient_type: recipient === "ALL_FIELD_TEAMS" ? "ALL_FIELD_TEAMS" : "SPECIFIC_TEAM",
          recipient_id: recipient === "ALL_FIELD_TEAMS" ? null : recipient,
          priority,
          message_text: directiveText,
        }),
      });
      if (res.ok) {
        setDirectiveText("");
        onRefresh();
      }
    } catch (err) {
      console.error("Broadcast error", err);
    } finally {
      setIsBroadcasting(false);
    }
  };

  // Acknowledge Field Report
  const handleAcknowledgeReport = async (reportId: string) => {
    setActionLoadingId(reportId);
    try {
      const res = await fetch(`${apiUrl}/api/v1/field/reports/${reportId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: "ACKNOWLEDGED",
          reviewed_by: "Central Expert Team",
          review_notes: "Incorporated into situational context.",
        }),
      });
      if (res.ok) {
        onRefresh();
      }
    } catch (err) {
      console.error("Acknowledge report error", err);
    } finally {
      setActionLoadingId(null);
    }
  };

  // Resolve Assistance Request
  const handleResolveAssistance = async (requestId: string) => {
    setActionLoadingId(requestId);
    try {
      const res = await fetch(`${apiUrl}/api/v1/field/assistance/${requestId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: "RESOLVED",
          assigned_unit: "SDRF Tactical Backup Unit 4",
          resolution_notes: "Support unit reached scene.",
        }),
      });
      if (res.ok) {
        onRefresh();
      }
    } catch (err) {
      console.error("Resolve assist error", err);
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded overflow-hidden font-sans text-white space-y-3">
      {/* Header */}
      <div className="bg-black px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded bg-zinc-900 border border-zinc-700 flex items-center justify-center text-white font-bold">
            <Radio className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-black uppercase tracking-wider text-white font-mono flex items-center gap-2">
              On-Ground Rescue Intelligence &amp; Field Coordination
            </h3>
            <p className="text-[10px] text-zinc-400 font-mono">
              Live ground truth loop with deployed SDRF / NDRF units
            </p>
          </div>
        </div>

        <Link
          href="/field"
          target="_blank"
          className="text-xs font-mono bg-white hover:bg-zinc-200 text-black font-black px-3 py-1.5 rounded transition flex items-center gap-1.5 shadow-sm"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          Launch Field Unit App
        </Link>
      </div>

      <div className="p-4 space-y-4">
        {/* Metric Counters Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400 font-bold">Deployed Units:</span>
            <span className="font-black text-white">{summary?.teams_deployed ?? 3}</span>
          </div>

          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400 font-bold">On Scene:</span>
            <span className="font-black text-orange-400">{summary?.teams_on_scene ?? 1}</span>
          </div>

          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400 font-bold">Need Assistance:</span>
            <span
              className={`font-black ${
                (summary?.teams_need_assistance ?? 0) > 0 ? "text-red-400" : "text-zinc-500"
              }`}
            >
              {summary?.teams_need_assistance ?? 0}
            </span>
          </div>

          <div className="bg-black p-2.5 rounded border border-zinc-800 flex justify-between items-center">
            <span className="text-zinc-400 font-bold">Pending Reports:</span>
            <span
              className={`font-black ${
                (summary?.unacknowledged_reports_count ?? 0) > 0 ? "text-amber-400" : "text-emerald-400"
              }`}
            >
              {summary?.unacknowledged_reports_count ?? 0}
            </span>
          </div>
        </div>

        {/* Urgent Assistance SOS Alerts */}
        {summary?.assistance_requests && summary.assistance_requests.some((a) => a.status === "REQUESTED") && (
          <div className="bg-red-950/80 border border-red-700 p-3 rounded space-y-2">
            <div className="text-[11px] font-mono uppercase text-red-300 font-black flex items-center gap-1.5">
              <AlertOctagon className="w-4 h-4 text-red-400" />
              URGENT FIELD ASSISTANCE REQUESTED:
            </div>
            {summary.assistance_requests
              .filter((a) => a.status === "REQUESTED")
              .map((a) => (
                <div
                  key={a.id}
                  className="bg-black p-2.5 rounded border border-red-800 flex items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="font-mono text-[10px] text-red-400 font-black">
                      [{a.priority}] {a.request_type} • Team: {a.team_id}
                    </div>
                    <p className="text-zinc-200 mt-0.5">{a.description}</p>
                  </div>
                  <button
                    onClick={() => handleResolveAssistance(a.id)}
                    disabled={actionLoadingId === a.id}
                    className="bg-red-600 hover:bg-red-500 text-white text-[10px] font-mono font-black px-3 py-1.5 rounded transition flex-shrink-0"
                  >
                    {actionLoadingId === a.id ? "Updating..." : "DISPATCH BACKUP"}
                  </button>
                </div>
              ))}
          </div>
        )}

        {/* Live Field Reports & Broadcast Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left: Incoming Ground Observations Queue (7 cols) */}
          <div className="lg:col-span-7 space-y-2">
            <div className="text-[11px] font-mono uppercase text-zinc-400 font-bold flex items-center justify-between">
              <span>Incoming Ground Observations ({summary?.recent_reports?.length || 0}):</span>
              <span className="text-zinc-500 font-normal">Context Evidence</span>
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {summary?.recent_reports && summary.recent_reports.length > 0 ? (
                summary.recent_reports.map((rep) => (
                  <div
                    key={rep.id}
                    className="bg-black p-2.5 rounded border border-zinc-800 space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className="text-white font-bold">
                        {rep.report_type.replace(/_/g, " ")}
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded uppercase font-black ${
                          rep.severity === "CRITICAL"
                            ? "bg-red-950 text-red-300 border border-red-700"
                            : rep.severity === "HIGH"
                            ? "bg-orange-950 text-orange-300 border border-orange-700"
                            : "bg-amber-950 text-amber-300 border border-amber-700"
                        }`}
                      >
                        {rep.severity}
                      </span>
                    </div>

                    <p className="text-zinc-300 text-[11px] leading-normal">{rep.description}</p>

                    {/* Image thumbnails */}
                    {rep.images && rep.images.length > 0 && (
                      <div className="flex items-center gap-2 pt-1">
                        {rep.images.map((img) => (
                          <button
                            key={img.id}
                            type="button"
                            onClick={() => setSelectedImageModal(`${apiUrl}${img.url}`)}
                            className="group relative rounded overflow-hidden border border-zinc-700 hover:border-white transition"
                          >
                            <img
                              src={`${apiUrl}${img.url}`}
                              alt="Evidence"
                              className="w-12 h-12 object-cover group-hover:scale-105 transition"
                            />
                          </button>
                        ))}
                      </div>
                    )}

                    {rep.latitude && rep.longitude && (
                      <div className="text-[10px] text-zinc-400 font-mono flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-zinc-400" />
                        <span>
                          {rep.latitude.toFixed(4)}°N, {rep.longitude.toFixed(4)}°E
                          {rep.location_accuracy ? ` (±${rep.location_accuracy.toFixed(0)}m)` : ""}
                        </span>
                      </div>
                    )}

                    <div className="flex items-center justify-between font-mono text-[10px] text-zinc-500 pt-1 border-t border-zinc-850">
                      <span>Reported by: {rep.reported_by}</span>
                      <div className="flex items-center gap-2">
                        <span>Status: <strong className="text-zinc-300">{rep.status}</strong></span>
                        {rep.status === "SUBMITTED" && (
                          <button
                            onClick={() => handleAcknowledgeReport(rep.id)}
                            disabled={actionLoadingId === rep.id}
                            className="text-black font-bold bg-white hover:bg-zinc-200 px-2 py-0.5 rounded transition"
                          >
                            {actionLoadingId === rep.id ? "..." : "Acknowledge"}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-black p-4 rounded text-center text-xs font-mono text-zinc-500 border border-zinc-800">
                  No field observations received yet.
                </div>
              )}
            </div>
          </div>

          {/* Right: Broadcast Operational Directive (5 cols) */}
          <div className="lg:col-span-5 space-y-2">
            <div className="text-[11px] font-mono uppercase text-zinc-400 font-bold">
              Broadcast Operational Directive:
            </div>

            <form
              onSubmit={handleBroadcast}
              className="bg-black p-3 rounded border border-zinc-800 space-y-2.5 text-xs font-sans"
            >
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] font-mono uppercase text-zinc-400 mb-1 font-bold">
                    Target Unit:
                  </label>
                  <select
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded p-1.5 text-zinc-200 font-mono text-xs focus:outline-none"
                  >
                    <option value="ALL_FIELD_TEAMS">ALL FIELD UNITS</option>
                    <option value="ALPHA-1">ALPHA-1 (Gangtok)</option>
                    <option value="BRAVO-2">BRAVO-2 (Aizawl)</option>
                    <option value="CHARLIE-3">CHARLIE-3 (Kohima)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono uppercase text-zinc-400 mb-1 font-bold">
                    Priority:
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded p-1.5 text-zinc-200 font-mono text-xs focus:outline-none"
                  >
                    <option value="NORMAL">NORMAL</option>
                    <option value="IMPORTANT">IMPORTANT</option>
                    <option value="URGENT">URGENT</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 mb-1 font-bold">
                  Directive / Caution Notice:
                </label>
                <textarea
                  rows={2}
                  value={directiveText}
                  onChange={(e) => setDirectiveText(e.target.value)}
                  placeholder="e.g. Avoid Sector 4 arterial road. Severe debris flow reported..."
                  required
                  className="w-full bg-zinc-900 border border-zinc-800 rounded p-2 text-zinc-200 text-xs focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={isBroadcasting || !directiveText.trim()}
                className="w-full bg-white hover:bg-zinc-200 active:bg-zinc-300 disabled:opacity-50 text-black py-2 rounded font-mono font-black text-xs transition flex items-center justify-center gap-1.5 shadow-sm"
              >
                <Send className="w-3.5 h-3.5" />
                {isBroadcasting ? "Transmitting..." : "Send Directive to Field"}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Full Resolution Ground Evidence Inspection Modal */}
      {selectedImageModal && (
        <div
          className="fixed inset-0 bg-black/90 z-[3000] flex items-center justify-center p-4 backdrop-blur-sm"
          onClick={() => setSelectedImageModal(null)}
        >
          <div className="relative max-w-2xl w-full bg-zinc-950 border border-zinc-850 rounded overflow-hidden shadow-2xl">
            <div className="p-3 bg-black border-b border-zinc-800 flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-zinc-200">
                Ground Evidence Inspection
              </span>
              <button
                onClick={() => setSelectedImageModal(null)}
                className="bg-zinc-800 hover:bg-zinc-700 text-white p-1 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-2 flex items-center justify-center bg-black">
              <img
                src={selectedImageModal}
                alt="Ground Evidence Full View"
                className="w-full h-auto max-h-[75vh] object-contain rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
