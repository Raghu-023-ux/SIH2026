"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  AlertTriangle,
  AlertOctagon,
  Bell,
  MapPin,
  Clock,
  ArrowLeft,
  ChevronRight,
  Info,
} from "lucide-react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PublicAlertItem {
  alert_id: string;
  event_id: string;
  location_id: string;
  location_name: string;
  district: string;
  state: string;
  hazard_type: string;
  public_status: string;
  message_title: string;
  message_summary: string;
  affected_radius_km: number;
  detected_at: string;
  updated_at: string;
  data_mode: string;
}

export default function PublicAlertsNotificationCenter() {
  const [alerts, setAlerts] = useState<PublicAlertItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadAlerts() {
      try {
        setLoading(true);
        const res = await fetch(`${API_URL}/api/v1/public/alerts`);
        if (res.ok) {
          const data: PublicAlertItem[] = await res.json();
          setAlerts(data);
        }
      } catch (err) {
        console.error("Failed to load public alerts", err);
      } finally {
        setLoading(false);
      }
    }
    loadAlerts();
  }, []);

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 font-sans flex flex-col max-w-md sm:max-w-xl mx-auto shadow-2xl border-x border-slate-800">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 sticky top-0 z-40 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <Link
            href="/public"
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-300 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">
              PUBLIC NOTIFICATION CENTER
            </div>
            <h1 className="text-sm font-bold text-slate-100">Active Regional Warnings</h1>
          </div>
        </div>

        <div className="text-[10px] font-mono text-indigo-400 font-bold bg-indigo-950 px-2 py-1 rounded border border-indigo-800">
          {alerts.length} Active Alerts
        </div>
      </header>

      {/* Alerts Stream */}
      <main className="flex-1 p-4 space-y-3 overflow-y-auto">
        <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs font-mono text-slate-400 flex items-start gap-2">
          <Info className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
          <span>
            Select any active alert below to review the localized safety checklist, danger zone perimeter, and safer assembly points.
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs font-mono text-slate-500">
            Loading public alerts...
          </div>
        ) : alerts.length > 0 ? (
          alerts.map((alert) => {
            const isUrgent = alert.public_status === "URGENT";
            return (
              <Link
                key={alert.alert_id}
                href={`/public`}
                className={`block rounded-2xl border p-4 space-y-2.5 transition transform hover:scale-[1.01] shadow-lg ${
                  isUrgent
                    ? "bg-red-950/70 border-red-800/80 hover:border-red-600"
                    : "bg-orange-950/70 border-orange-800/80 hover:border-orange-600"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {isUrgent ? (
                      <AlertOctagon className="w-4 h-4 text-red-400 animate-pulse" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-orange-400" />
                    )}
                    <span className="text-xs font-bold font-mono uppercase tracking-wider">
                      {alert.public_status} WARNING
                    </span>
                  </div>

                  <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {new Date(alert.updated_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-100">{alert.message_title}</h3>
                <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed font-sans">
                  {alert.message_summary}
                </p>

                <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-indigo-400" />
                    {alert.district}, {alert.state}
                  </span>
                  <span className="text-indigo-300 font-bold flex items-center gap-0.5">
                    View Safety Plan <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Link>
            );
          })
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-2">
            <Shield className="w-8 h-8 text-emerald-400 mx-auto" />
            <h3 className="text-sm font-bold text-slate-200">No Active Public Warnings</h3>
            <p className="text-xs text-slate-400 font-sans max-w-xs mx-auto">
              All monitored North Eastern Region terrain slopes are operating within normal baseline moisture and stability parameters.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
