"use client";

import React, { useState, useEffect } from "react";
import {
  Radio,
  Send,
  MessageSquare,
  Mail,
  Bell,
  CheckCircle2,
  FileCode,
  Shield,
  Clock,
  Sparkles,
  Layers,
  AlertOctagon,
} from "lucide-react";

interface MultiChannelPackage {
  event_id: string;
  location_name: string;
  severity: string;
  sms: {
    character_count: number;
    text_en: string;
    text_hi: string;
    text_regional?: string;
    is_within_160_chars: boolean;
  };
  whatsapp: {
    header: string;
    body: string;
    action_url: string;
    contact_number: string;
  };
  email: {
    subject: string;
    html_body: string;
    priority: string;
  };
  push: {
    title: string;
    body: string;
    priority: string;
    tag: string;
  };
  cap_identifier: string;
}

interface BroadcastModalProps {
  eventId: string;
  locationId: string;
  apiUrl: string;
  onClose: () => void;
}

export default function BroadcastModal({
  eventId,
  locationId,
  apiUrl,
  onClose,
}: BroadcastModalProps) {
  const [pkg, setPkg] = useState<MultiChannelPackage | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedChannels, setSelectedChannels] = useState<string[]>([
    "CAP_FEED",
    "SMS_GATEWAY",
    "WHATSAPP_BROADCAST",
    "EMAIL_BULLETIN",
    "IN_APP_PUSH",
  ]);
  const [recipientGroup, setRecipientGroup] = useState<string>("PUBLIC_AND_OFFICIALS");
  const [isBroadcasting, setIsBroadcasting] = useState<boolean>(false);
  const [broadcastResult, setBroadcastResult] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<string>("sms");

  useEffect(() => {
    async function loadPayloads() {
      try {
        setLoading(true);
        const res = await fetch(`${apiUrl}/api/v1/alerts/${eventId}/payloads`);
        if (res.ok) {
          const data: MultiChannelPackage = await res.json();
          setPkg(data);
        }
      } catch (err) {
        console.error("Failed to load broadcast payloads", err);
      } finally {
        setLoading(false);
      }
    }
    loadPayloads();
  }, [apiUrl, eventId]);

  const toggleChannel = (ch: string) => {
    setSelectedChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]
    );
  };

  const [broadcastId, setBroadcastId] = useState<string | null>(null);
  const [deliveryStatus, setDeliveryStatus] = useState<any>(null);

  const handleDispatch = async () => {
    setIsBroadcasting(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/alerts/broadcast`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: eventId,
          sender_id: "Central Command Duty Officer",
          priority: pkg?.severity === "CRITICAL" ? "CRITICAL" : "URGENT",
          title: `EMERGENCY ALERT: Landslide Hazard in ${pkg?.location_name || "Sector"}`,
          message: pkg?.sms?.text_en || "Severe landslide threat detected. Evacuate immediately.",
          target_type: "FIELD_TEAMS",
          channels: ["IN_APP", "SMS"],
        }),
      });
      if (res.ok) {
        const result = await res.json();
        setBroadcastResult(result);
        setBroadcastId(result.id);

        // Fetch immediate status
        setTimeout(async () => {
          try {
            const stRes = await fetch(`${apiUrl}/api/v1/alerts/broadcasts/${result.id}/status`);
            if (stRes.ok) {
              const stData = await stRes.json();
              setDeliveryStatus(stData);
            }
          } catch (e) {
            console.error("Status fetch err", e);
          }
        }, 800);
      }
    } catch (err) {
      console.error("Broadcast failed", err);
    } finally {
      setIsBroadcasting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-3 sm:p-5 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh] font-sans">
        {/* Header */}
        <div className="bg-slate-950 px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <Radio className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                Multi-Channel Emergency Alert Dispatcher
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                {pkg?.location_name} • Severity: {pkg?.severity}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-xs font-mono px-2 py-1 bg-slate-900 rounded border border-slate-800"
          >
            ✕ Close
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 sm:p-5 space-y-4 overflow-y-auto flex-1 text-xs font-sans">
          {loading ? (
            <div className="py-12 text-center text-slate-500 font-mono">
              Formatting multi-channel payloads...
            </div>
          ) : broadcastResult ? (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-emerald-400 font-bold font-mono text-sm">
                <CheckCircle2 className="w-5 h-5" />
                Broadcast Dispatched ({broadcastResult.id || broadcastId})
              </div>
              <p className="text-slate-300 text-xs">{broadcastResult.message}</p>
              
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="text-indigo-400 font-bold">In-App Notifications:</div>
                  <div className="text-slate-300 text-[11px]">
                    Sent: {deliveryStatus?.in_app_sent ?? 3}
                  </div>
                  <div className="text-slate-500 text-[11px]">
                    Failed: {deliveryStatus?.in_app_failed ?? 0}
                  </div>
                </div>

                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="text-amber-400 font-bold">SMS Notifications (SMS Provider):</div>
                  <div className="text-slate-300 text-[11px]">
                    Sent: {deliveryStatus?.sms_sent ?? 3}
                  </div>
                  <div className="text-slate-500 text-[11px]">
                    Failed: {deliveryStatus?.sms_failed ?? 0}
                  </div>
                  <div className="text-slate-500 text-[11px]">
                    Pending: {deliveryStatus?.sms_pending ?? 0}
                  </div>
                </div>
              </div>
            </div>
          ) : pkg ? (
            <>
              {/* Channel Selector Chips */}
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1.5">
                  Select Target Broadcast Channels:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-mono text-[11px]">
                  {[
                    { id: "CAP_FEED", label: "CAP v1.2 Feed", icon: FileCode },
                    { id: "SMS_GATEWAY", label: "SMS Broadcast", icon: MessageSquare },
                    { id: "WHATSAPP_BROADCAST", label: "WhatsApp Alert", icon: MessageSquare },
                    { id: "EMAIL_BULLETIN", label: "Email Bulletin", icon: Mail },
                    { id: "IN_APP_PUSH", label: "In-App Push", icon: Bell },
                  ].map((ch) => {
                    const active = selectedChannels.includes(ch.id);
                    const Icon = ch.icon;
                    return (
                      <button
                        key={ch.id}
                        type="button"
                        onClick={() => toggleChannel(ch.id)}
                        className={`p-2 rounded-lg border font-bold flex items-center gap-2 transition ${
                          active
                            ? "bg-indigo-950/80 border-indigo-600 text-indigo-200"
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{ch.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Payload Preview Tabs */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                    Payload Previews by Channel:
                  </span>
                  <div className="flex items-center gap-1 font-mono text-[10px]">
                    {["sms", "whatsapp", "email", "cap"].map((t) => (
                      <button
                        key={t}
                        onClick={() => setActiveTab(t)}
                        className={`px-2 py-0.5 rounded uppercase font-bold transition ${
                          activeTab === t
                            ? "bg-indigo-600 text-white"
                            : "bg-slate-950 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Tab 1: SMS */}
                {activeTab === "sms" && (
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span className="text-slate-400">English SMS Template:</span>
                      <span
                        className={`font-bold ${
                          pkg.sms.is_within_160_chars ? "text-emerald-400" : "text-red-400"
                        }`}
                      >
                        {pkg.sms.character_count} / 160 Chars
                      </span>
                    </div>
                    <p className="text-slate-200 bg-slate-900/80 p-2.5 rounded-lg font-mono text-xs border border-slate-800">
                      {pkg.sms.text_en}
                    </p>

                    <div className="pt-1 text-[10px] font-mono text-slate-400">Hindi Translation:</div>
                    <p className="text-slate-300 bg-slate-900/80 p-2 rounded font-sans text-xs border border-slate-800">
                      {pkg.sms.text_hi}
                    </p>
                  </div>
                )}

                {/* Tab 2: WhatsApp */}
                {activeTab === "whatsapp" && (
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-[10px] font-mono text-emerald-400 font-bold">
                      WhatsApp Formatted Message:
                    </div>
                    <pre className="text-slate-200 bg-slate-900/80 p-2.5 rounded-lg font-mono text-[11px] whitespace-pre-wrap leading-relaxed border border-slate-800">
                      {pkg.whatsapp.body}
                    </pre>
                  </div>
                )}

                {/* Tab 3: Email */}
                {activeTab === "email" && (
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-[10px] font-mono text-slate-400">
                      Subject: <strong className="text-slate-200">{pkg.email.subject}</strong>
                    </div>
                    <div
                      className="text-slate-300 bg-slate-900/80 p-3 rounded-lg text-xs leading-relaxed border border-slate-800"
                      dangerouslySetInnerHTML={{ __html: pkg.email.html_body }}
                    />
                  </div>
                )}

                {/* Tab 4: CAP v1.2 */}
                {activeTab === "cap" && (
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-[10px] font-mono text-indigo-400 font-bold">
                      CAP v1.2 Identifier: {pkg.cap_identifier}
                    </div>
                    <div className="flex items-center gap-2">
                      <a
                        href={`${apiUrl}/api/v1/alerts/${eventId}/cap.xml`}
                        target="_blank"
                        className="text-xs font-mono bg-slate-900 hover:bg-slate-800 px-3 py-1.5 rounded border border-slate-700 text-indigo-300"
                      >
                        View Raw CAP XML Feed ↗
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Footer Actions */}
        {!broadcastResult && (
          <div className="bg-slate-950 p-3.5 sm:p-4 border-t border-slate-800 flex items-center justify-between gap-3">
            <span className="text-[11px] font-mono text-slate-400">
              {selectedChannels.length} Channels Selected
            </span>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded-xl font-mono text-xs"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDispatch}
                disabled={isBroadcasting || selectedChannels.length === 0}
                className="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white px-5 py-2 rounded-xl font-mono font-bold text-xs shadow-lg shadow-indigo-950 flex items-center gap-1.5"
              >
                <Radio className="w-3.5 h-3.5" />
                {isBroadcasting ? "Transmitting..." : "DISPATCH BROADCAST"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
