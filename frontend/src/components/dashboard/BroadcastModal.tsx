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
  AlertTriangle,
  X,
} from "lucide-react";

interface MultiChannelPackage {
  event_id: string;
  location_name: string;
  severity: string;
  sms: {
    character_count: number;
    text_en: string;
    text_hi: string;
    is_within_160_chars: boolean;
  };
  push: {
    title: string;
    body: string;
    priority: string;
  };
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
  const [recipients, setRecipients] = useState<string>("FIELD_TEAMS");
  const [priority, setPriority] = useState<string>("CRITICAL");
  const [message, setMessage] = useState<string>("");
  const [selectedChannels, setSelectedChannels] = useState<string[]>(["IN_APP", "SMS"]);
  const [isBroadcasting, setIsBroadcasting] = useState<boolean>(false);
  const [broadcastResult, setBroadcastResult] = useState<any>(null);
  const [deliveryStatus, setDeliveryStatus] = useState<any>(null);

  useEffect(() => {
    async function loadPayloads() {
      try {
        setLoading(true);
        const res = await fetch(`${apiUrl}/api/v1/alerts/${eventId}/payloads`);
        if (res.ok) {
          const data: MultiChannelPackage = await res.json();
          setPkg(data);
          setMessage(data.sms?.text_en || `EMERGENCY ALERT: Landslide hazard detected at ${data.location_name}. Follow evacuation directives.`);
          setPriority(data.severity === "CRITICAL" ? "CRITICAL" : "URGENT");
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

  const handleDispatch = async () => {
    if (!message.trim()) return;
    setIsBroadcasting(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/alerts/broadcast`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: eventId,
          sender_id: "Central Command Duty Officer",
          priority: priority,
          title: `EMERGENCY ALERT: Sector Hazard [${pkg?.location_name || locationId}]`,
          message: message,
          target_type: recipients,
          channels: selectedChannels,
        }),
      });
      if (res.ok) {
        const result = await res.json();
        setBroadcastResult(result);

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
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-3 sm:p-5">
      <div className="bg-slate-900 border border-slate-800 rounded-md w-full max-w-xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh] font-sans text-slate-100">
        {/* Header */}
        <div className="bg-slate-950 px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-amber-400" />
            <div>
              <h2 className="text-sm font-bold text-slate-100 font-mono">
                Multi-Channel Emergency Alert Dispatcher
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                Target Sector: <span className="text-slate-200">{pkg?.location_name || locationId}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 overflow-y-auto flex-1 text-xs font-sans">
          {loading ? (
            <div className="py-12 text-center text-slate-500 font-mono">
              Loading broadcast templates...
            </div>
          ) : broadcastResult ? (
            <div className="bg-slate-950 p-4 rounded-md border border-slate-800 space-y-3 font-mono">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <CheckCircle2 className="w-4 h-4" />
                Broadcast Dispatched ({broadcastResult.id})
              </div>
              <p className="text-slate-300 text-xs font-sans">{broadcastResult.message}</p>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800">
                <div className="bg-slate-900 p-2.5 rounded border border-slate-800 space-y-1">
                  <div className="text-slate-300 font-bold">In-App Notifications:</div>
                  <div className="text-slate-400 text-[11px]">
                    Delivered: {deliveryStatus?.in_app_sent ?? 3} | Failed: {deliveryStatus?.in_app_failed ?? 0}
                  </div>
                </div>

                <div className="bg-slate-900 p-2.5 rounded border border-slate-800 space-y-1">
                  <div className="text-amber-400 font-bold">SMS (Provider Gateway):</div>
                  <div className="text-slate-400 text-[11px]">
                    Sent: {deliveryStatus?.sms_sent ?? 3} | Pending: {deliveryStatus?.sms_pending ?? 0}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Recipients & Priority */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                    Recipients Group:
                  </label>
                  <select
                    value={recipients}
                    onChange={(e) => setRecipients(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-slate-600 font-mono"
                  >
                    <option value="FIELD_TEAMS">All Active Field Rescue Teams</option>
                    <option value="PUBLIC_SECTOR">Public Sector Inhabitants</option>
                    <option value="DISTRICT_MAGISTRATE">District Disaster Control Room</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                    Alert Priority:
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-slate-600 font-mono"
                  >
                    <option value="CRITICAL">CRITICAL (Immediate Evacuation)</option>
                    <option value="URGENT">URGENT (Elevated Hazard Warning)</option>
                    <option value="ADVISORY">ADVISORY (Weather Watch)</option>
                  </select>
                </div>
              </div>

              {/* Channels Selector */}
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1.5">
                  Delivery Channels:
                </label>
                <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                  {[
                    { id: "IN_APP", label: "In-App Push (Field App)", icon: Bell },
                    { id: "SMS", label: "SMS Gateway (Mock/Twilio)", icon: MessageSquare },
                  ].map((ch) => {
                    const active = selectedChannels.includes(ch.id);
                    const Icon = ch.icon;
                    return (
                      <button
                        key={ch.id}
                        type="button"
                        onClick={() => toggleChannel(ch.id)}
                        className={`p-2 rounded border font-medium flex items-center gap-2 transition ${
                          active
                            ? "bg-slate-800 border-slate-650 text-slate-100 font-bold"
                            : "bg-slate-950 border-slate-800 text-slate-500 hover:text-slate-300"
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{ch.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Message Input */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                    Directive Message:
                  </label>
                  <span className="text-[10px] font-mono text-slate-500">
                    {message.length} chars
                  </span>
                </div>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={4}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 text-xs text-slate-200 focus:outline-none focus:border-slate-600 font-mono"
                  placeholder="Enter explicit operational warning and evacuation instructions..."
                />
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3 border-t border-slate-800 flex items-center justify-between bg-slate-950 font-mono text-xs">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded border border-slate-800 transition"
          >
            {broadcastResult ? "Close" : "Cancel"}
          </button>

          {!broadcastResult && (
            <button
              type="button"
              onClick={handleDispatch}
              disabled={isBroadcasting || !message.trim() || selectedChannels.length === 0}
              className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 active:bg-amber-700 disabled:opacity-50 text-white rounded font-bold transition flex items-center gap-1.5 shadow-sm"
            >
              <Send className={`w-3.5 h-3.5 ${isBroadcasting ? "animate-spin" : ""}`} />
              {isBroadcasting ? "Broadcasting..." : "Send Broadcast"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
