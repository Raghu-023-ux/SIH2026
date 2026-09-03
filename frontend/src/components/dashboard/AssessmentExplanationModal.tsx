"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface EvidenceRef {
  evidence_type: string;
  id_reference?: string | null;
  metric?: string | null;
  value?: any;
  timestamp?: string | null;
  source?: string | null;
}

interface Finding {
  type: string;
  title: string;
  description: string;
  evidence: EvidenceRef[];
}

interface Uncertainty {
  factor: string;
  reason: string;
  impact: string;
}

interface Recommendation {
  priority: string;
  action: string;
  rationale: string;
}

interface AIResponse {
  answer: string;
  analysis: {
    summary: string;
    risk_level: string;
    risk_score: number;
    confidence: number;
    findings: Finding[];
    uncertainties: Uncertainty[];
    recommendations: Recommendation[];
    data_mode: string;
  };
  evidence: EvidenceRef[];
  agent: string;
  data_mode: string;
  latency_ms: number;
}

interface AssessmentExplanationModalProps {
  locationId: string | null;
  locationName?: string;
  apiUrl: string;
  onClose: () => void;
}

export default function AssessmentExplanationModal({
  locationId,
  locationName,
  apiUrl,
  onClose,
}: AssessmentExplanationModalProps) {
  const [data, setData] = useState<AIResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [showEvidence, setShowEvidence] = useState<boolean>(false);

  useEffect(() => {
    async function fetchExplanation() {
      if (!locationId) return;
      try {
        setLoading(true);
        const res = await fetch(`${apiUrl}/api/v1/ai/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            location_id: locationId,
            query_type: "EXPLAIN_ASSESSMENT",
          }),
        });
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (err) {
        console.error("Failed to load explanation", err);
      } finally {
        setLoading(false);
      }
    }
    fetchExplanation();
  }, [locationId, apiUrl]);

  if (!locationId) return null;

  return (
    <div className="fixed inset-0 bg-black/85 z-50 flex items-center justify-center p-3 sm:p-5">
      <div className="bg-zinc-950 border border-zinc-800 rounded w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh] font-sans text-white">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-zinc-800 flex items-center justify-between bg-black">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-zinc-400" />
            <div>
              <h2 className="text-sm font-black text-white font-mono uppercase tracking-wider">
                Assessment Synthesis &amp; Physical Explanation
              </h2>
              <p className="text-[11px] text-zinc-400 font-mono">
                Sector: <span className="text-zinc-200 font-bold">{locationName || locationId}</span>
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

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs font-sans">
          {loading ? (
            <div className="py-12 text-center text-zinc-500 font-mono text-xs space-y-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" />
              <p>Synthesizing multi-signal telemetry evidence...</p>
            </div>
          ) : data ? (
            <>
              {/* Primary Synthesis Prose */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-mono text-zinc-400 uppercase font-bold">
                  Physical Mechanism Interpretation:
                </div>
                <div className="bg-black border border-zinc-800 p-3.5 rounded leading-relaxed text-zinc-200 text-xs">
                  {data.answer}
                </div>
              </div>

              {/* Diagnostic Findings */}
              {data.analysis.findings && data.analysis.findings.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-mono text-zinc-400 uppercase font-bold">
                    Key Telemetry Findings:
                  </div>
                  <div className="space-y-1.5">
                    {data.analysis.findings.map((f, i) => (
                      <div
                        key={i}
                        className="bg-black border border-zinc-800 p-2.5 rounded space-y-1"
                      >
                        <div className="font-bold text-zinc-200 flex items-center gap-1.5 font-mono text-xs">
                          <CheckCircle2 className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />
                          {f.title}
                        </div>
                        <p className="text-[11px] text-zinc-400 leading-normal">{f.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Operational Actions & Uncertainties */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Recommendations */}
                {data.analysis.recommendations && data.analysis.recommendations.length > 0 && (
                  <div className="bg-black border border-zinc-800 p-3 rounded space-y-1.5">
                    <div className="text-[10px] font-mono text-zinc-300 uppercase font-bold flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> Operational Directives:
                    </div>
                    <ul className="space-y-1.5">
                      {data.analysis.recommendations.map((r, i) => (
                        <li key={i} className="text-zinc-300 flex items-start gap-1.5 text-[11px]">
                          <ArrowRight className="w-3 h-3 text-zinc-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-mono font-bold text-zinc-200">[{r.priority}]</span> {r.action}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Uncertainties */}
                {data.analysis.uncertainties && data.analysis.uncertainties.length > 0 && (
                  <div className="bg-black border border-zinc-800 p-3 rounded space-y-1.5">
                    <div className="text-[10px] font-mono text-zinc-300 uppercase font-bold flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Known Uncertainties:
                    </div>
                    <ul className="space-y-1">
                      {data.analysis.uncertainties.map((u, i) => (
                        <li key={i} className="text-zinc-400 text-[11px]">
                          • <strong className="text-zinc-300">{u.factor}:</strong> {u.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Citations Toggle */}
              <div className="pt-2 border-t border-zinc-850">
                <button
                  onClick={() => setShowEvidence(!showEvidence)}
                  className="text-[11px] font-mono text-zinc-400 hover:text-white flex items-center gap-1"
                >
                  {showEvidence ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  <span>{showEvidence ? "Hide Telemetry Citations" : "View Telemetry Citations"} ({data.evidence.length})</span>
                </button>

                {showEvidence && (
                  <div className="mt-2 space-y-1 max-h-40 overflow-y-auto bg-black p-2 rounded border border-zinc-800 font-mono text-[10px]">
                    {data.evidence.map((ev, i) => (
                      <div key={i} className="text-zinc-400 flex justify-between py-0.5 border-b border-zinc-900">
                        <span className="text-zinc-300 font-bold">{ev.metric || ev.evidence_type}:</span>
                        <span>{String(ev.value ?? "N/A")} ({ev.source || "Sensor"})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="py-8 text-center text-zinc-500 font-mono">
              Unable to generate physical assessment explanation.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-zinc-800 bg-black flex items-center justify-between text-xs font-mono">
          <span className="text-[10px] text-zinc-500">
            Engine Version: prototype-v0.3 • Latency: {data?.latency_ms ?? 0}ms
          </span>
          <button
            onClick={onClose}
            className="bg-white hover:bg-zinc-200 text-black font-bold px-3 py-1.5 rounded transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
