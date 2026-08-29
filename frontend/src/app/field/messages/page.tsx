"use client";

import React, { useState } from "react";
import {
  Bell,
  CheckCircle2,
  Clock,
  Radio,
  AlertOctagon,
  Shield,
  Check,
} from "lucide-react";
import { useField } from "@/components/field/FieldContext";

export default function FieldMessagesPage() {
  const {
    callsign,
    data,
    acknowledgeMessage,
  } = useField();

  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const messages = data?.recent_messages || [];

  const handleAcknowledge = async (id: string) => {
    setAcknowledgingId(id);
    await acknowledgeMessage(id);
    setAcknowledgingId(null);
  };

  return (
    <main className="flex-1 p-3 sm:p-4 space-y-3.5">
      {/* 1. Header */}
      <div>
        <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <Bell className="w-4 h-4 text-amber-400" />
          Command Directives &amp; Operational Messages
        </h2>
        <p className="text-[11px] text-slate-400 font-mono">
          Directives dispatched from Central Expert Command to {callsign}
        </p>
      </div>

      {/* 2. Messages Stream */}
      <div className="space-y-2.5">
        {messages.length > 0 ? (
          messages.map((msg) => {
            const isAcked = !!msg.acknowledged_at;
            const isUrgent = msg.priority === "URGENT" || msg.priority === "CRITICAL";

            return (
              <div
                key={msg.id}
                className={`rounded-xl p-3.5 space-y-2 text-xs border shadow-md transition ${
                  isUrgent && !isAcked
                    ? "bg-red-950/80 border-red-800"
                    : isAcked
                    ? "bg-slate-900/60 border-slate-800/80 opacity-80"
                    : "bg-slate-900 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between font-mono text-[10px]">
                  <div className="flex items-center gap-1.5">
                    {isUrgent ? (
                      <AlertOctagon className="w-3.5 h-3.5 text-red-400" />
                    ) : (
                      <Radio className="w-3.5 h-3.5 text-indigo-400" />
                    )}
                    <span
                      className={`font-bold ${
                        isUrgent ? "text-red-300" : "text-indigo-400"
                      }`}
                    >
                      {msg.sender_id}
                    </span>
                  </div>

                  <span
                    className={`px-1.5 py-0.5 rounded font-bold uppercase ${
                      isUrgent
                        ? "bg-red-600 text-white"
                        : "bg-slate-800 text-slate-300"
                    }`}
                  >
                    {msg.priority}
                  </span>
                </div>

                <p className="text-slate-100 text-xs leading-relaxed font-sans">{msg.message}</p>

                <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 font-mono text-[10px] text-slate-400">
                  <span className="flex items-center gap-1 text-slate-500">
                    <Clock className="w-3 h-3 text-slate-600" />
                    {new Date(msg.created_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>

                  {isAcked ? (
                    <span className="flex items-center gap-1 text-emerald-400 font-bold">
                      <Check className="w-3 h-3" />
                      <span>ACKNOWLEDGED</span>
                    </span>
                  ) : (
                    <button
                      onClick={() => handleAcknowledge(msg.id)}
                      disabled={acknowledgingId === msg.id}
                      className="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 shadow-sm"
                    >
                      {acknowledgingId === msg.id ? "Syncing..." : "ACKNOWLEDGE"}
                    </button>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs font-mono">
            No directives or operational messages received yet.
          </div>
        )}
      </div>
    </main>
  );
}
