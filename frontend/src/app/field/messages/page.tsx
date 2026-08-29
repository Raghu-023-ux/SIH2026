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
    <main className="flex-1 p-3 sm:p-4 space-y-3.5 font-sans text-white bg-black">
      {/* 1. Header */}
      <div>
        <h2 className="text-sm font-black text-white flex items-center gap-2 font-mono uppercase tracking-wider">
          <Bell className="w-4 h-4 text-amber-400" />
          Command Directives &amp; Operational Messages
        </h2>
        <p className="text-[11px] text-zinc-400 font-mono">
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
                className={`rounded p-3.5 space-y-2 text-xs border shadow-md transition font-mono ${
                  isUrgent && !isAcked
                    ? "bg-red-950/80 border-red-700"
                    : isAcked
                    ? "bg-zinc-950 border-zinc-850 opacity-80"
                    : "bg-zinc-950 border-zinc-800"
                }`}
              >
                <div className="flex items-center justify-between font-mono text-[10px]">
                  <div className="flex items-center gap-1.5">
                    {isUrgent ? (
                      <AlertOctagon className="w-3.5 h-3.5 text-red-400" />
                    ) : (
                      <Radio className="w-3.5 h-3.5 text-white" />
                    )}
                    <span
                      className={`font-black ${
                        isUrgent ? "text-red-300" : "text-white"
                      }`}
                    >
                      {msg.sender_id}
                    </span>
                  </div>

                  <span
                    className={`px-1.5 py-0.5 rounded font-black uppercase ${
                      isUrgent
                        ? "bg-red-600 text-white"
                        : "bg-zinc-800 text-zinc-300"
                    }`}
                  >
                    {msg.priority}
                  </span>
                </div>

                <p className="text-zinc-100 text-xs leading-relaxed font-sans font-medium">{msg.message}</p>

                <div className="flex items-center justify-between pt-1 border-t border-zinc-800 font-mono text-[10px] text-zinc-400">
                  <span className="flex items-center gap-1 text-zinc-500">
                    <Clock className="w-3 h-3 text-zinc-600" />
                    {new Date(msg.created_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>

                  {isAcked ? (
                    <span className="flex items-center gap-1 text-emerald-400 font-bold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Acknowledged
                    </span>
                  ) : (
                    <button
                      onClick={() => handleAcknowledge(msg.id)}
                      disabled={acknowledgingId === msg.id}
                      className="bg-white hover:bg-zinc-200 text-black font-black text-[10px] px-2.5 py-1 rounded transition shadow-sm"
                    >
                      {acknowledgingId === msg.id ? "Syncing..." : "Acknowledge"}
                    </button>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="bg-zinc-950 border border-zinc-800 rounded p-6 text-center space-y-2 font-mono">
            <Radio className="w-6 h-6 text-zinc-600 mx-auto" />
            <div className="text-zinc-400 text-xs font-bold">No active directives in queue</div>
            <p className="text-zinc-600 text-[11px]">
              Directives from the Central Command Officer will appear here in real-time.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
