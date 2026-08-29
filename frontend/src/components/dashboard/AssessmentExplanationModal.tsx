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
  locationName: string | null;
  eventId?: string | null;
  apiUrl: string;
  onClose: () => void;
}

export default function AssessmentExplanationModal({
  locationId,
  locationName,
  eventId,
  apiUrl,
  onClose,
}: AssessmentExplanationModalProps) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<AIResponse | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);

  useEffect(() => {
    if (!locationId) return;

    let isMounted = true;
    const fetchExplanation = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${apiUrl}/api/v1/ai/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            location_id: locationId,
            event_id: eventId,
            question: "Provide an objective scientific explanation of the risk indicators, triggering thresholds, and data uncertainties for this sector.",
            agent_type: "explanation",
          }),
        });
        if (res.ok && isMounted) {
          const result = await res.json();
          setData(result);
        }
      } catch (err) {
        console.error("Failed to load assessment explanation:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchExplanation();
    return () => {
      isMounted = false;
    };
  }, [locationId, eventId, apiUrl]);

  if (!locationId) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-md w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl font-sans text-slate-100">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-400" />
            <div>
              <h2 className="text-sm font-bold text-slate-100 font-mono">
                Assessment Synthesis &amp; Physical Explanation
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                Sector: <span className="text-slate-200">{locationName || locationId}</span>
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

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs font-sans">
          {loading ? (
            <div className="py-12 text-center text-slate-500 font-mono text-xs space-y-2">
              <div className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin mx-auto" />
              <p>Synthesizing multi-signal telemetry evidence...</p>
            </div>
          ) : data ? (
            <>
              {/* Primary Synthesis Prose */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">
                  Physical Mechanism Interpretation:
                </div>
                <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-md leading-relaxed text-slate-200 text-xs">
                  {data.answer}
                </div>
              </div>

              {/* Diagnostic Findings */}
              {data.analysis.findings && data.analysis.findings.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">
                    Key Telemetry Findings:
                  </div>
                  <div className="space-y-1.5">
                    {data.analysis.findings.map((f, i) => (
                      <div
                        key={i}
                        className="bg-slate-950/60 border border-slate-800/80 p-2.5 rounded-md space-y-1"
                      >
                        <div className="font-semibold text-slate-200 flex items-center gap-1.5 font-mono text-xs">
                          <CheckCircle2 className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                          {f.title}
                        </div>
                        <p className="text-[11px] text-slate-400 leading-normal">{f.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Operational Actions & Uncertainties */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Recommendations */}
                {data.analysis.recommendations && data.analysis.recommendations.length > 0 && (
                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-md space-y-1.5">
                    <div className="text-[10px] font-mono text-slate-300 uppercase font-bold flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> Operational Directives:
                    </div>
                    <ul className="space-y-1.5">
                      {data.analysis.recommendations.map((r, i) => (
                        <li key={i} className="text-slate-300 flex items-start gap-1.5 text-[11px]">
                          <ArrowRight className="w-3 h-3 text-slate-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-mono font-bold text-slate-200">[{r.priority}]</span> {r.action}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Uncertainties */}
                {data.analysis.uncertainties && data.analysis.uncertainties.length > 0 && (
                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-md space-y-1.5">
                    <div className="text-[10px] font-mono text-slate-300 uppercase font-bold flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Known Uncertainties:
                    </div>
                    <ul className="space-y-1">
                      {data.analysis.uncertainties.map((u, i) => (
                        <li key={i} className="text-slate-400 text-[11px]">
                          • <strong className="text-slate-300">{u.factor}:</strong> {u.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Citations Toggle */}
              <div className="border-t border-slate-800 pt-2 font-mono">
                <button
                  onClick={() => setShowEvidence(!showEvidence)}
                  className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1 transition"
                >
                  {showEvidence ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  {showEvidence ? "Hide" : "Inspect"} System Telemetry Evidence Citations ({data.evidence.length} items)
                </button>

                {showEvidence && (
                  <div className="mt-2 bg-slate-950 border border-slate-800 rounded-md p-2.5 text-[10px] space-y-1 max-h-40 overflow-y-auto">
                    {data.evidence.map((ev, i) => (
                      <div key={i} className="flex items-center justify-between border-b border-slate-850 py-1 last:border-0">
                        <span className="text-slate-300 font-semibold">{ev.evidence_type}</span>
                        <span className="text-slate-400">{ev.metric || ev.id_reference || "-"}: {ev.value}</span>
                        {ev.timestamp && <span className="text-slate-500">{ev.timestamp.slice(11, 19)}</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-slate-500 font-mono text-xs py-8 text-center">
              Unable to generate diagnostic explanation for this station.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-2.5 border-t border-slate-800 flex items-center justify-between bg-slate-950 text-[10px] font-mono text-slate-500">
          <span>AI Advisory Layer • Deterministic Engine Grounding</span>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
