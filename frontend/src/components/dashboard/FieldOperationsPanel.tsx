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
  reviewed_by?: string | null;
}

interface AssistanceRequestItem {
  id: string;
  event_id?: string | null;
  team_id: string;
  request_type: string;
  priority: string;
  description: string;
  status: string;
  assigned_unit?: string | null;
  created_at: string;
}

interface FieldOperationsPanelProps {
  summary: {
    total_teams: number;
    teams_deployed: number;
    teams_on_scene: number;
    teams_need_assistance: number;
    unacknowledged_reports_count: number;
    active_assistance_requests_count: number;
    teams: FieldTeamItem[];
    recent_reports: FieldReportItem[];
    assistance_requests: AssistanceRequestItem[];
  } | null;
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

  // Broadcast Operational Message
  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!directiveText.trim()) return;

    setIsBroadcasting(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/field/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender_id: "Central Command Duty Officer",
          recipient_team: recipient,
          priority: priority,
          message: directiveText,
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
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg font-sans space-y-3">
      {/* Header */}
      <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-orange-600/20 border border-orange-500/30 flex items-center justify-center text-orange-400">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              On-Ground Rescue Intelligence &amp; Field Coordination
            </h3>
            <p className="text-[11px] text-slate-400 font-mono">
              Live feedback loop with deployed SDRF / NDRF units
            </p>
          </div>
        </div>

        <Link
          href="/field"
          target="_blank"
          className="text-xs font-mono bg-indigo-950 hover:bg-indigo-900 border border-indigo-800 text-indigo-300 px-3 py-1.5 rounded-lg transition flex items-center gap-1.5"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          Launch Field Unit App
        </Link>
      </div>

      <div className="p-4 space-y-4">
        {/* Metric Counters Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">Deployed Units:</span>
            <span className="font-bold text-indigo-400">{summary?.teams_deployed ?? 3}</span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">On Scene:</span>
            <span className="font-bold text-orange-400">{summary?.teams_on_scene ?? 1}</span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">Need Assistance:</span>
            <span
              className={`font-bold ${
                (summary?.teams_need_assistance ?? 0) > 0 ? "text-red-400 animate-pulse" : "text-slate-400"
              }`}
            >
              {summary?.teams_need_assistance ?? 0}
            </span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
            <span className="text-slate-400">Pending Reports:</span>
            <span
              className={`font-bold ${
                (summary?.unacknowledged_reports_count ?? 0) > 0 ? "text-yellow-400" : "text-emerald-400"
              }`}
            >
              {summary?.unacknowledged_reports_count ?? 0}
            </span>
          </div>
        </div>

        {/* Urgent Assistance SOS Alerts */}
        {summary?.assistance_requests && summary.assistance_requests.some((a) => a.status === "REQUESTED") && (
          <div className="bg-red-950/80 border border-red-800 p-3 rounded-xl space-y-2">
            <div className="text-[11px] font-mono uppercase text-red-300 font-bold flex items-center gap-1.5">
              <AlertOctagon className="w-4 h-4 text-red-400 animate-bounce" />
              URGENT FIELD ASSISTANCE REQUESTED:
            </div>
            {summary.assistance_requests
              .filter((a) => a.status === "REQUESTED")
              .map((a) => (
                <div
                  key={a.id}
                  className="bg-slate-950/80 p-2.5 rounded-lg border border-red-900 flex items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="font-mono text-[10px] text-red-400 font-bold">
                      [{a.priority}] {a.request_type} • Team: {a.team_id}
                    </div>
                    <p className="text-slate-200 mt-0.5">{a.description}</p>
                  </div>
                  <button
                    onClick={() => handleResolveAssistance(a.id)}
                    disabled={actionLoadingId === a.id}
                    className="bg-red-600 hover:bg-red-500 text-white text-[10px] font-mono font-bold px-3 py-1.5 rounded transition flex-shrink-0"
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
            <div className="text-[11px] font-mono uppercase text-slate-400 font-bold flex items-center justify-between">
              <span>Incoming Ground Observations ({summary?.recent_reports?.length || 0}):</span>
              <span className="text-slate-500 font-normal">Acts as Context Evidence</span>
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {summary?.recent_reports && summary.recent_reports.length > 0 ? (
                summary.recent_reports.map((rep) => (
                  <div
                    key={rep.id}
                    className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className="text-indigo-400 font-bold">
                        {rep.report_type.replace(/_/g, " ")}
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded uppercase font-bold ${
                          rep.severity === "CRITICAL"
                            ? "bg-red-950 text-red-400"
                            : rep.severity === "HIGH"
                            ? "bg-orange-950 text-orange-400"
                            : "bg-yellow-950 text-yellow-400"
                        }`}
                      >
                        {rep.severity}
                      </span>
                    </div>

                    <p className="text-slate-300 text-[11px] leading-normal">{rep.description}</p>

                    <div className="flex items-center justify-between font-mono text-[10px] text-slate-500 pt-1 border-t border-slate-800/60">
                      <span>Reported by: {rep.reported_by}</span>
                      <div className="flex items-center gap-2">
                        <span>Status: <strong className="text-slate-300">{rep.status}</strong></span>
                        {rep.status === "SUBMITTED" && (
                          <button
                            onClick={() => handleAcknowledgeReport(rep.id)}
                            disabled={actionLoadingId === rep.id}
                            className="text-indigo-400 hover:text-indigo-300 font-bold bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800"
                          >
                            {actionLoadingId === rep.id ? "..." : "Acknowledge"}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-slate-950/60 p-4 rounded-lg text-center text-xs font-mono text-slate-500">
                  No field observations received yet.
                </div>
              )}
            </div>
          </div>

          {/* Right: Broadcast Operational Directive (5 cols) */}
          <div className="lg:col-span-5 space-y-2">
            <div className="text-[11px] font-mono uppercase text-slate-400 font-bold">
              Broadcast Operational Directive:
            </div>

            <form
              onSubmit={handleBroadcast}
              className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2.5 text-xs font-sans"
            >
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                    Target Unit:
                  </label>
                  <select
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-200 font-mono text-xs focus:outline-none"
                  >
                    <option value="ALL_FIELD_TEAMS">ALL FIELD UNITS</option>
                    <option value="ALPHA-1">ALPHA-1 (Gangtok)</option>
                    <option value="BRAVO-2">BRAVO-2 (Aizawl)</option>
                    <option value="CHARLIE-3">CHARLIE-3 (Kohima)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                    Priority:
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-200 font-mono text-xs focus:outline-none"
                  >
                    <option value="NORMAL">NORMAL</option>
                    <option value="IMPORTANT">IMPORTANT</option>
                    <option value="URGENT">URGENT</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Directive / Caution Notice:
                </label>
                <textarea
                  rows={2}
                  value={directiveText}
                  onChange={(e) => setDirectiveText(e.target.value)}
                  placeholder="e.g. Avoid Sector 4 arterial road. Severe debris flow reported..."
                  required
                  className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-slate-200 text-xs focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={isBroadcasting || !directiveText.trim()}
                className="w-full bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white py-2 rounded-lg font-mono font-semibold text-xs transition flex items-center justify-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                {isBroadcasting ? "Transmitting..." : "Send Directive to Field"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
