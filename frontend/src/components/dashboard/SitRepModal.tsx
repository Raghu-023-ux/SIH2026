"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  Printer,
  Copy,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Shield,
  Activity,
  Users,
  Compass,
  Clock,
} from "lucide-react";

interface SitRepDetail {
  report_number: string;
  incident_name: string;
  location_name: string;
  state: string;
  reporting_officer: string;
  generated_at: string;
  operational_period: string;
  executive_summary: string;
  sections: {
    heading: string;
    content: string;
    key_metrics?: Record<string, any> | null;
  }[];
  data_mode: string;
}

interface SitRepModalProps {
  eventId: string;
  apiUrl: string;
  onClose: () => void;
}

export default function SitRepModal({ eventId, apiUrl, onClose }: SitRepModalProps) {
  const [sitrep, setSitrep] = useState<SitRepDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    async function loadSitRep() {
      try {
        setLoading(true);
        const res = await fetch(`${apiUrl}/api/v1/alerts/sitrep/${eventId}`);
        if (res.ok) {
          const data: SitRepDetail = await res.json();
          setSitrep(data);
        }
      } catch (err) {
        console.error("Failed to load SitRep", err);
      } finally {
        setLoading(false);
      }
    }
    loadSitRep();
  }, [apiUrl, eventId]);

  const handleCopy = () => {
    if (!sitrep) return;
    const text = `SITUATION REPORT: ${sitrep.report_number}\n${sitrep.incident_name}\n\nEXECUTIVE SUMMARY:\n${sitrep.executive_summary}\n\n${sitrep.sections
      .map((s) => `${s.heading}\n${s.content}`)
      .join("\n\n")}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-3 sm:p-5 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh] font-sans">
        {/* Header */}
        <div className="bg-slate-950 px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-orange-600/20 border border-orange-500/40 flex items-center justify-center text-orange-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                Operational Situation Report (SitRep)
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                {sitrep?.report_number || "Generating..."} • NDMA / SDRF Format
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="text-xs font-mono px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-lg border border-slate-700 flex items-center gap-1.5 transition"
            >
              {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>

            <button
              onClick={handlePrint}
              className="text-xs font-mono px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-lg border border-slate-700 flex items-center gap-1.5 transition"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print</span>
            </button>

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-200 text-xs font-mono px-2.5 py-1.5 bg-slate-900 rounded-lg border border-slate-800"
            >
              ✕
            </button>
          </div>
        </div>

        {/* SitRep Document Content */}
        <div className="p-5 sm:p-6 space-y-4 overflow-y-auto flex-1 text-xs font-sans bg-slate-950/60">
          {loading ? (
            <div className="py-16 text-center text-slate-500 font-mono">
              Compiling formal tactical Situation Report...
            </div>
          ) : sitrep ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-lg">
              {/* Document Meta Header */}
              <div className="border-b border-slate-800 pb-3 space-y-1 font-mono text-[11px]">
                <div className="flex justify-between items-center text-indigo-400 font-bold">
                  <span>DISASTER MANAGEMENT ADVISORY BRIEFING</span>
                  <span>{sitrep.data_mode} MODE</span>
                </div>
                <h1 className="text-base font-black text-slate-100 font-sans">{sitrep.incident_name}</h1>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-slate-400 pt-1 text-[10px]">
                  <div>Report No: <strong className="text-slate-200">{sitrep.report_number}</strong></div>
                  <div>Period: <strong className="text-slate-200">{sitrep.operational_period}</strong></div>
                  <div>Officer: <strong className="text-slate-200">{sitrep.reporting_officer}</strong></div>
                </div>
              </div>

              {/* Executive Summary */}
              <div className="space-y-1.5 bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                <h3 className="text-xs font-bold font-mono text-orange-400 uppercase">
                  Executive Summary
                </h3>
                <p className="text-slate-200 leading-relaxed text-xs">{sitrep.executive_summary}</p>
              </div>

              {/* Formatted Sections */}
              <div className="space-y-4 pt-2">
                {sitrep.sections.map((sec, idx) => (
                  <div key={idx} className="space-y-2 border-b border-slate-800/80 pb-3 last:border-b-0">
                    <h4 className="text-xs font-bold font-mono text-slate-200 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                      {sec.heading}
                    </h4>
                    <p className="text-slate-300 leading-relaxed whitespace-pre-line pl-3 text-[11px]">
                      {sec.content}
                    </p>

                    {sec.key_metrics && (
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 pl-3 pt-1 font-mono text-[10px]">
                        {Object.entries(sec.key_metrics).map(([k, v]) => (
                          <div key={k} className="bg-slate-950 p-1.5 rounded border border-slate-800 flex justify-between">
                            <span className="text-slate-400 capitalize">{k.replace(/_/g, " ")}:</span>
                            <span className="text-indigo-300 font-bold ml-1">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Document Signoff */}
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>Generated by SIH26001 Multi-Signal Intelligence Pipeline</span>
                <span>Verified by {sitrep.reporting_officer}</span>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
