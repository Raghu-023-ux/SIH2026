"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Shield,
  AlertTriangle,
  Radio,
  MapPin,
  Send,
  LifeBuoy,
  CheckCircle2,
  Clock,
  Compass,
  AlertOctagon,
  RefreshCw,
  Navigation,
  FileText,
  Volume2,
  Layers,
  ChevronRight,
  Activity,
  Wifi,
  WifiOff,
  UserCheck,
} from "lucide-react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FieldTeam {
  id: string;
  team_name: string;
  callsign: string;
  status: string;
  latitude?: number | null;
  longitude?: number | null;
  contact_channel?: string | null;
}

interface OperationalMessage {
  id: string;
  sender_id: string;
  recipient_team: string;
  priority: string;
  message: string;
  created_at: string;
  acknowledged_at?: string | null;
}

interface NearbyIncident {
  event_id?: string | null;
  location_id: string;
  location_name: string;
  hazard_type: string;
  severity: string;
  risk_score: number;
  distance_km: number;
}

interface FieldReport {
  id: string;
  report_type: string;
  severity: string;
  description: string;
  timestamp: string;
  status: string;
  reported_by: string;
}

interface AssignmentData {
  team: FieldTeam;
  assigned_location?: {
    id: string;
    name: string;
    district: string;
    state: string;
    elevation: number;
    slope_angle: number;
  } | null;
  assigned_event?: {
    id: string;
    hazard_type: string;
    severity: string;
    status: string;
    risk_score: number;
    confidence_score: number;
    summary: string;
    updated_at: string;
  } | null;
  immediate_conditions: {
    slope_risk: string;
    rainfall_state: string;
    soil_saturation_state: string;
    road_status: string;
    nearest_hazard_km?: number | null;
  };
  nearby_incidents: NearbyIncident[];
  recent_messages: OperationalMessage[];
  recent_reports: FieldReport[];
}

const REPORT_TYPES = [
  "ROAD_BLOCKED",
  "LANDSLIDE_OBSERVED",
  "WATER_MUD_FLOW",
  "INFRASTRUCTURE_DAMAGE",
  "PEOPLE_TRAPPED",
  "INJURIES",
  "VISIBILITY_ISSUE",
  "COMMUNICATION_FAILURE",
  "OTHER",
];

const ASSISTANCE_TYPES = [
  "MEDICAL",
  "PERSONNEL",
  "EQUIPMENT",
  "TRANSPORT",
  "COMMUNICATION",
  "OTHER",
];

export default function FieldRescuePage() {
  const [callsign, setCallsign] = useState<string>("ALPHA-1");
  const [data, setData] = useState<AssignmentData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [online, setOnline] = useState<boolean>(true);
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [geoStatus, setGeoStatus] = useState<string>("Locating device...");

  // Modal States
  const [showReportModal, setShowReportModal] = useState<boolean>(false);
  const [showAssistanceModal, setShowAssistanceModal] = useState<boolean>(false);

  // Form States
  const [reportType, setReportType] = useState<string>("LANDSLIDE_OBSERVED");
  const [reportSeverity, setReportSeverity] = useState<string>("HIGH");
  const [reportDesc, setReportDesc] = useState<string>("");
  const [isSubmittingReport, setIsSubmittingReport] = useState<boolean>(false);

  const [assistType, setAssistType] = useState<string>("EQUIPMENT");
  const [assistPriority, setAssistPriority] = useState<string>("CRITICAL");
  const [assistDesc, setAssistDesc] = useState<string>("");
  const [isSubmittingAssist, setIsSubmittingAssist] = useState<boolean>(false);

  const [acknowledgingMsgId, setAcknowledgingMsgId] = useState<string | null>(null);

  // Geolocation
  useEffect(() => {
    if (typeof window !== "undefined" && "geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude });
          setGeoStatus("GPS Acquired");
        },
        (err) => {
          setGeoStatus("GPS Unavailable (Using Station Sector)");
          setCoords({ lat: 27.3389, lon: 88.6065 });
        },
        { enableHighAccuracy: true, timeout: 8000 }
      );
    } else {
      setGeoStatus("Location Unsupported");
    }
  }, []);

  // Fetch Assignment Briefing
  const fetchBriefing = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/field/assignments?callsign=${callsign}`);
      if (res.ok) {
        const briefing: AssignmentData = await res.json();
        setData(briefing);
        setOnline(true);
      } else {
        setOnline(false);
      }
    } catch (err) {
      console.error("Failed to load field briefing", err);
      setOnline(false);
    } finally {
      setLoading(false);
    }
  }, [callsign]);

  useEffect(() => {
    fetchBriefing();
    const interval = setInterval(fetchBriefing, 15000); // 15s polling
    return () => clearInterval(interval);
  }, [fetchBriefing]);

  // Update Team Status
  const handleStatusChange = async (newStatus: string) => {
    if (!data?.team?.id) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/field/teams/${data.team.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: newStatus,
          latitude: coords?.lat,
          longitude: coords?.lon,
        }),
      });
      if (res.ok) {
        fetchBriefing();
      }
    } catch (err) {
      console.error("Status update error", err);
    }
  };

  // Submit Field Report
  const handleSubmitReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!data?.assigned_location?.id || !reportDesc.trim()) return;

    setIsSubmittingReport(true);
    try {
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
      };

      const res = await fetch(`${API_URL}/api/v1/field/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setReportDesc("");
        setShowReportModal(false);
        fetchBriefing();
      }
    } catch (err) {
      console.error("Failed to submit field report", err);
      alert("Network error: Please retry submission.");
    } finally {
      setIsSubmittingReport(false);
    }
  };

  // Submit Assistance SOS Request
  const handleSubmitAssistance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!data?.team?.id || !assistDesc.trim()) return;

    setIsSubmittingAssist(true);
    try {
      const payload = {
        event_id: data.assigned_event?.id,
        team_id: data.team.id,
        request_type: assistType,
        priority: assistPriority,
        description: assistDesc,
        latitude: coords?.lat,
        longitude: coords?.lon,
      };

      const res = await fetch(`${API_URL}/api/v1/field/assistance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setAssistDesc("");
        setShowAssistanceModal(false);
        fetchBriefing();
      }
    } catch (err) {
      console.error("Failed to request assistance", err);
      alert("Network error: Please retry SOS transmission.");
    } finally {
      setIsSubmittingAssist(false);
    }
  };

  // Acknowledge Operational Message
  const handleAcknowledgeMsg = async (msgId: string) => {
    setAcknowledgingMsgId(msgId);
    try {
      const res = await fetch(
        `${API_URL}/api/v1/field/messages/${msgId}/acknowledge?acknowledged_by=${callsign}`,
        { method: "POST" }
      );
      if (res.ok) {
        fetchBriefing();
      }
    } catch (err) {
      console.error("Acknowledgment error", err);
    } finally {
      setAcknowledgingMsgId(null);
    }
  };

  const unackMessages = data?.recent_messages?.filter((m) => !m.acknowledged_at) || [];

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 font-sans flex flex-col max-w-md sm:max-w-2xl mx-auto shadow-2xl border-x border-slate-800">
      {/* 1. Field Tactical Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 sticky top-0 z-40 shadow-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-red-600/20 border border-red-500/40 flex items-center justify-center text-red-400">
              <Radio className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <div className="text-[10px] font-mono tracking-wider uppercase text-red-400 font-bold flex items-center gap-1.5">
                <span>FIELD RESCUE OP</span>
                <span>•</span>
                <span className="text-slate-400">{geoStatus}</span>
              </div>
              <h1 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                {data?.team?.team_name || "Rescue Unit"}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Unit Switcher */}
            <select
              value={callsign}
              onChange={(e) => setCallsign(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs text-indigo-300 rounded px-2 py-1 font-mono focus:outline-none"
            >
              <option value="ALPHA-1">ALPHA-1 (Gangtok)</option>
              <option value="BRAVO-2">BRAVO-2 (Aizawl)</option>
              <option value="CHARLIE-3">CHARLIE-3 (Kohima)</option>
            </select>

            <Link
              href="/"
              className="text-[10px] font-mono text-slate-400 hover:text-slate-200 px-2 py-1 bg-slate-950 rounded border border-slate-800"
            >
              HQ View
            </Link>
          </div>
        </div>

        {/* Status Mode Switcher Bar */}
        <div className="mt-3 grid grid-cols-4 gap-1 text-[11px] font-mono">
          {["AVAILABLE", "DEPLOYED", "ON_SCENE", "NEED_ASSISTANCE"].map((st) => (
            <button
              key={st}
              onClick={() => handleStatusChange(st)}
              className={`py-1.5 rounded font-bold uppercase transition text-center ${
                data?.team?.status === st
                  ? st === "NEED_ASSISTANCE"
                    ? "bg-red-600 text-white shadow-md shadow-red-950"
                    : st === "ON_SCENE"
                    ? "bg-orange-600 text-white shadow-md shadow-orange-950"
                    : "bg-indigo-600 text-white shadow-md shadow-indigo-950"
                  : "bg-slate-950/80 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {st.replace("_", " ")}
            </button>
          ))}
        </div>
      </header>

      {/* 2. Urgent Directives Broadcast Banner */}
      {unackMessages.length > 0 && (
        <div className="bg-red-950/90 border-b border-red-800 p-3 space-y-2 animate-fadeIn">
          {unackMessages.map((msg) => (
            <div key={msg.id} className="flex items-start justify-between gap-3 text-xs">
              <div className="flex items-start gap-2">
                <AlertOctagon className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0 animate-bounce" />
                <div>
                  <div className="font-mono text-[10px] font-bold uppercase text-red-300">
                    URGENT CENTRAL DIRECTIVE [{msg.priority}]:
                  </div>
                  <p className="text-slate-100 font-medium leading-snug">{msg.message}</p>
                </div>
              </div>
              <button
                onClick={() => handleAcknowledgeMsg(msg.id)}
                disabled={acknowledgingMsgId === msg.id}
                className="bg-red-600 hover:bg-red-500 text-white font-mono text-[10px] px-2.5 py-1.5 rounded font-bold transition flex-shrink-0"
              >
                {acknowledgingMsgId === msg.id ? "Syncing..." : "ACKNOWLEDGE"}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 3. Main Field Body */}
      <main className="flex-1 p-3.5 space-y-3.5 overflow-y-auto">
        {/* Active Incident Briefing Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
              Current Sector Assignment
            </span>
            <span className="text-[10px] font-mono text-indigo-400">
              Sector: {data?.assigned_location?.name || "NER Assigned Zone"}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400 font-mono">Landslide Hazard Severity</div>
              <div
                className={`text-xl font-black font-mono mt-0.5 ${
                  data?.assigned_event?.severity === "CRITICAL"
                    ? "text-red-400"
                    : data?.assigned_event?.severity === "HIGH"
                    ? "text-orange-400"
                    : "text-yellow-400"
                }`}
              >
                {data?.assigned_event?.severity || "MONITORING"} RISK
              </div>
            </div>

            <div className="text-right">
              <div className="text-xs text-slate-400 font-mono">Confidence Level</div>
              <div className="text-base font-bold text-slate-200 font-mono">
                {((data?.assigned_event?.confidence_score ?? 0.82) * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            {data?.assigned_event?.summary ||
              "Continuous automated terrain monitoring active. Ground teams on standby."}
          </p>
        </div>

        {/* Immediate Ground Conditions Matrix */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-2">
          <div className="text-[10px] font-mono uppercase text-slate-400 font-bold flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            Immediate Ground Conditions (At-A-Glance):
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Slope Risk:</span>
              <span className="font-bold text-orange-400">
                {data?.immediate_conditions.slope_risk || "UNKNOWN"}
              </span>
            </div>

            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Rainfall:</span>
              <span className="font-bold text-indigo-300">
                {data?.immediate_conditions.rainfall_state || "UNKNOWN"}
              </span>
            </div>

            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Soil Saturation:</span>
              <span className="font-bold text-red-400">
                {data?.immediate_conditions.soil_saturation_state || "UNKNOWN"}
              </span>
            </div>

            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Road Status:</span>
              <span className="font-bold text-emerald-400 truncate ml-1">
                {data?.immediate_conditions.road_status || "UNKNOWN"}
              </span>
            </div>
          </div>
        </div>

        {/* Primary Action Buttons (Large Touch Targets) */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <button
            onClick={() => setShowReportModal(true)}
            className="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-bold py-3.5 px-3 rounded-xl flex flex-col items-center justify-center gap-1 shadow-lg shadow-indigo-950 font-mono transition"
          >
            <Send className="w-5 h-5" />
            <span className="text-xs">REPORT SITUATION</span>
          </button>

          <button
            onClick={() => setShowAssistanceModal(true)}
            className="bg-red-600 hover:bg-red-500 active:bg-red-700 text-white font-bold py-3.5 px-3 rounded-xl flex flex-col items-center justify-center gap-1 shadow-lg shadow-red-950 font-mono transition"
          >
            <LifeBuoy className="w-5 h-5" />
            <span className="text-xs">NEED ASSISTANCE</span>
          </button>
        </div>

        {/* Nearby Active Incidents */}
        {data?.nearby_incidents && data.nearby_incidents.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-2">
            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold flex items-center justify-between">
              <span>Nearby Regional Hazards:</span>
              <span>Radius: 150km</span>
            </div>

            <div className="space-y-1.5">
              {data.nearby_incidents.map((inc, i) => (
                <div
                  key={i}
                  className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between text-xs font-mono"
                >
                  <div className="flex items-center gap-2">
                    <MapPin className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                    <div>
                      <div className="font-semibold text-slate-200">{inc.location_name}</div>
                      <div className="text-[10px] text-slate-500">
                        {inc.hazard_type} • {inc.severity}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-orange-400 font-bold">{inc.distance_km} km</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Ground Reports Feed */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-2">
          <div className="text-[10px] font-mono uppercase text-slate-400 font-bold flex items-center justify-between">
            <span>Recent Ground Reports in Sector:</span>
            <span>{data?.recent_reports?.length || 0} Total</span>
          </div>

          <div className="space-y-2">
            {data?.recent_reports && data.recent_reports.length > 0 ? (
              data.recent_reports.map((rep) => (
                <div
                  key={rep.id}
                  className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 space-y-1 text-xs"
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
                  <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between">
                    <span>By: {rep.reported_by}</span>
                    <span>Status: {rep.status}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-3 text-slate-500 text-xs font-mono">
                No ground observations submitted yet.
              </div>
            )}
          </div>
        </div>
      </main>

      {/* --- MODAL 1: REPORT SITUATION --- */}
      {showReportModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-3 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Send className="w-4 h-4 text-indigo-400" />
                Submit Ground Observation
              </h3>
              <button
                onClick={() => setShowReportModal(false)}
                className="text-slate-400 hover:text-slate-200 text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleSubmitReport} className="space-y-3 text-xs font-sans">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Report Hazard Category:
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
                  Field Description / Coordinates:
                </label>
                <textarea
                  rows={3}
                  value={reportDesc}
                  onChange={(e) => setReportDesc(e.target.value)}
                  placeholder="Describe road blockage, debris volume, water runoff, or visible slope movement..."
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-xs focus:outline-none"
                />
              </div>

              <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                <MapPin className="w-3 h-3 text-indigo-400" />
                <span>
                  GPS Tag: {coords ? `${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}` : "Sector Default"}
                </span>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReportModal(false)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2.5 rounded-xl font-mono text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingReport || !reportDesc.trim()}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white py-2.5 rounded-xl font-mono font-bold text-xs shadow-lg shadow-indigo-950"
                >
                  {isSubmittingReport ? "Transmitting..." : "Send Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL 2: NEED ASSISTANCE SOS --- */}
      {showAssistanceModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-3 backdrop-blur-sm">
          <div className="bg-slate-900 border border-red-800/80 rounded-2xl w-full max-w-md p-5 space-y-4 shadow-2xl shadow-red-950">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-red-400 flex items-center gap-2">
                <LifeBuoy className="w-4 h-4 text-red-400" />
                Request Emergency Field Assistance
              </h3>
              <button
                onClick={() => setShowAssistanceModal(false)}
                className="text-slate-400 hover:text-slate-200 text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleSubmitAssistance} className="space-y-3 text-xs font-sans">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Required Support Type:
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
                      onClick={() => setAssistPriority(p)}
                      className={`py-2 rounded font-bold uppercase transition ${
                        assistPriority === p
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
                  value={assistDesc}
                  onChange={(e) => setAssistDesc(e.target.value)}
                  placeholder="State personnel count, trapped victims, specialized equipment needed, or impassable road..."
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-xs focus:outline-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAssistanceModal(false)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2.5 rounded-xl font-mono text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingAssist || !assistDesc.trim()}
                  className="flex-1 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white py-2.5 rounded-xl font-mono font-bold text-xs shadow-lg shadow-red-950"
                >
                  {isSubmittingAssist ? "Dispatching SOS..." : "Dispatch SOS"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
