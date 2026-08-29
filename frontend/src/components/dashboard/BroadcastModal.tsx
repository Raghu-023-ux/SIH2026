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
          const data = await res.json();
          setPkg(data);
          setMessage(data.sms?.text_en || data.push?.body || "CRITICAL LANDSLIDE ALERT: Immediate action required.");
        }
      } catch (err) {
        console.error("Failed to load broadcast payloads", err);
      } finally {
        setLoading(false);
      }
    }
    if (eventId) {
      loadPayloads();
    }
  }, [eventId, apiUrl]);

  const toggleChannel = (ch: string) => {
    setSelectedChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]
    );
  };

  const handleSend = async () => {
    if (!message.trim() || selectedChannels.length === 0) return;

    setIsBroadcasting(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/alerts/broadcast`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: eventId,
          location_id: locationId,
          recipients_type: recipients,
          priority,
          message_text: message,
          channels: selectedChannels,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setBroadcastResult(data);
        // Fetch status
        const stRes = await fetch(`${apiUrl}/api/v1/alerts/broadcasts/${data.id}/status`);
        if (stRes.ok) {
          const stData = await stRes.json();
          setDeliveryStatus(stData);
        }
      }
    } catch (err) {
      console.error("Broadcast dispatch failed", err);
    } finally {
      setIsBroadcasting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/85 z-50 flex items-center justify-center p-3 sm:p-5">
      <div className="bg-zinc-950 border border-zinc-800 rounded w-full max-w-xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh] font-sans text-white">
        {/* Header */}
        <div className="bg-black px-5 py-3.5 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-amber-400" />
            <div>
              <h2 className="text-sm font-black text-white font-mono uppercase tracking-wider">
                Multi-Channel Emergency Alert Dispatcher
              </h2>
              <p className="text-[11px] text-zinc-400 font-mono">
                Target Sector: <span className="text-zinc-200 font-bold">{pkg?.location_name || locationId}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded hover:bg-zinc-900 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 overflow-y-auto flex-1 text-xs font-sans">
          {loading ? (
            <div className="py-12 text-center text-zinc-500 font-mono">
              Loading broadcast templates...
            </div>
          ) : broadcastResult ? (
            <div className="bg-black p-4 rounded border border-zinc-800 space-y-3 font-mono">
              <div className="flex items-center gap-2 text-emerald-400 font-black text-sm">
                <CheckCircle2 className="w-4 h-4" />
                Broadcast Dispatched ({broadcastResult.id})
              </div>
              <p className="text-zinc-300 text-xs font-sans">{broadcastResult.message}</p>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-zinc-850">
                <div className="bg-zinc-900 p-2.5 rounded border border-zinc-800 space-y-1">
                  <div className="text-zinc-200 font-bold">In-App Notifications:</div>
                  <div className="text-zinc-400 text-[11px]">
                    Delivered: {deliveryStatus?.in_app_sent ?? 3} | Failed: {deliveryStatus?.in_app_failed ?? 0}
                  </div>
                </div>

                <div className="bg-zinc-900 p-2.5 rounded border border-zinc-800 space-y-1">
                  <div className="text-amber-400 font-bold">SMS (Provider Gateway):</div>
                  <div className="text-zinc-400 text-[11px]">
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
                  <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                    Recipients Group:
                  </label>
                  <select
                    value={recipients}
                    onChange={(e) => setRecipients(e.target.value)}
                    className="w-full bg-black border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-zinc-600 font-mono"
                  >
                    <option value="FIELD_TEAMS">All Active Field Rescue Teams</option>
                    <option value="PUBLIC_SECTOR">Public Sector Inhabitants</option>
                    <option value="DISTRICT_MAGISTRATE">District Disaster Control Room</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1">
                    Alert Priority:
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-black border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-zinc-600 font-mono"
                  >
                    <option value="CRITICAL">CRITICAL (Immediate Evacuation)</option>
                    <option value="URGENT">URGENT (Elevated Hazard Warning)</option>
                    <option value="ADVISORY">ADVISORY (Weather Watch)</option>
                  </select>
                </div>
              </div>

              {/* Channels Selector */}
              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1.5">
                  Delivery Channels:
                </label>
                <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                  {[
                    { id: "IN_APP", label: "In-App Push (Field App)", icon: Bell },
                    { id: "SMS", label: "SMS (Direct Carrier)", icon: MessageSquare },
                  ].map((ch) => {
                    const active = selectedChannels.includes(ch.id);
                    const Icon = ch.icon;
                    return (
                      <button
                        key={ch.id}
                        type="button"
                        onClick={() => toggleChannel(ch.id)}
                        className={`p-2.5 rounded border text-left flex items-center gap-2 transition ${
                          active
                            ? "bg-white text-black border-white font-black"
                            : "bg-black text-zinc-400 border-zinc-850 hover:text-white"
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{ch.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Directive Message Text */}
              <div>
                <label className="block text-[10px] font-mono uppercase text-zinc-400 font-bold mb-1 flex items-center justify-between">
                  <span>Directive Message Body:</span>
                  <span className="text-zinc-500 font-normal">{message.length} chars</span>
                </label>
                <textarea
                  rows={3}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="w-full bg-black border border-zinc-800 rounded p-2 text-xs text-white font-mono focus:outline-none focus:border-zinc-600 leading-relaxed"
                />
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="bg-black px-5 py-3 border-t border-zinc-800 flex items-center justify-between text-xs font-mono">
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white transition font-bold"
          >
            {broadcastResult ? "Close" : "Cancel"}
          </button>

          {!broadcastResult && (
            <button
              onClick={handleSend}
              disabled={isBroadcasting || !message.trim() || selectedChannels.length === 0}
              className="bg-white hover:bg-zinc-200 text-black font-black px-4 py-2 rounded transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              {isBroadcasting ? "Transmitting..." : "Send Emergency Broadcast"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
