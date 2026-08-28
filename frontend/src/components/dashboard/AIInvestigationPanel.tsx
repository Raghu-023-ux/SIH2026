"use client";

import React, { useState } from "react";
import {
  BrainCircuit,
  Sparkles,
  Send,
  HelpCircle,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  Clock,
  Compass,
  ArrowRight,
} from "lucide-react";

interface EvidenceRef {
  evidence_type: string;
  id_reference?: string | null;
  metric?: string | null;
  value?: any;
  timestamp?: string | null;
  source?: string | null;
  notes?: string | null;
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

interface AIAnalysisData {
  summary: string;
  risk_level: string;
  risk_score: number;
  confidence: number;
  trajectory: string;
  findings: Finding[];
  uncertainties: Uncertainty[];
  recommendations: Recommendation[];
  data_mode: string;
  all_evidence: EvidenceRef[];
}

interface AIResponse {
  answer: string;
  analysis: AIAnalysisData;
  evidence: EvidenceRef[];
  agent: string;
  data_mode: string;
  model_used: string;
  latency_ms: number;
}

interface AIInvestigationPanelProps {
  locationId: string | null;
  locationName: string | null;
  eventId: string | null;
  apiUrl: string;
  activeQuestion?: string | null;
  onQuestionResolved?: () => void;
}

const SUGGESTED_QUESTIONS = [
  "Why is the risk increasing?",
  "What are the main risk drivers?",
  "What changed in the last 6 hours?",
  "How confident is the assessment?",
  "What data is missing?",
  "Are nearby locations showing similar conditions?",
];

export default function AIInvestigationPanel({
  locationId,
  locationName,
  eventId,
  apiUrl,
  activeQuestion,
  onQuestionResolved,
}: AIInvestigationPanelProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIResponse | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);

  // Trigger analysis
  const executeQuery = async (customPrompt?: string, agentType: string = "auto") => {
    if (!locationId) return;
    const q = customPrompt || question || "Provide a situational analysis.";
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/api/v1/ai/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          location_id: locationId,
          event_id: eventId,
          question: q,
          agent_type: agentType,
        }),
      });

      if (res.ok) {
        const data: AIResponse = await res.json();
        setResponse(data);
      }
    } catch (err) {
      console.error("AI Analysis error:", err);
    } finally {
      setLoading(false);
      if (onQuestionResolved) onQuestionResolved();
    }
  };

  // Quick Action triggers
  const handleExplainAssessment = () => {
    setQuestion("Explain the primary physical and terrain factors determining this risk score.");
    executeQuery("Explain the primary physical and terrain factors determining this risk score.", "explanation");
  };

  const handleInvestigateChange = () => {
    setQuestion("Investigate what factors changed to cause this hazard trajectory.");
    executeQuery("Investigate what factors changed to cause this hazard trajectory.", "investigation");
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg font-sans">
      {/* Header */}
      <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <BrainCircuit className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                AI Disaster Analyst &amp; Investigation Layer
              </h3>
              <span className="bg-indigo-950 text-indigo-400 border border-indigo-800 text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold">
                READ-ONLY
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">
              Target: <span className="text-indigo-300 font-bold">{locationName || "No Station Selected"}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono bg-slate-900 border border-slate-800 text-slate-400 px-2 py-1 rounded">
            AI MODE: <strong className="text-emerald-400">DETERMINISTIC</strong>
          </span>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Quick Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleExplainAssessment}
            disabled={!locationId || loading}
            className="px-3 py-1.5 rounded-lg bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-700/60 text-indigo-200 text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50 font-mono"
          >
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            Explain Assessment
          </button>

          <button
            onClick={handleInvestigateChange}
            disabled={!locationId || loading}
            className="px-3 py-1.5 rounded-lg bg-purple-950/80 hover:bg-purple-900 border border-purple-700/60 text-purple-200 text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50 font-mono"
          >
            <Compass className="w-3.5 h-3.5 text-purple-400" />
            Investigate Change
          </button>
        </div>

        {/* Suggested Question Chips */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-mono text-slate-400 uppercase font-semibold">
            Suggested Operational Queries:
          </div>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_QUESTIONS.map((sq, i) => (
              <button
                key={i}
                onClick={() => {
                  setQuestion(sq);
                  executeQuery(sq);
                }}
                disabled={!locationId || loading}
                className="text-[11px] bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 px-2.5 py-1 rounded-md transition font-sans text-left disabled:opacity-50"
              >
                {sq}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask AI Analyst about this station or event..."
            onKeyDown={(e) => e.key === "Enter" && executeQuery()}
            disabled={!locationId || loading}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-sans"
          />
          <button
            onClick={() => executeQuery()}
            disabled={!locationId || loading || !question.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition flex items-center gap-1.5 font-mono"
          >
            <Send className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Analyzing..." : "Ask AI"}
          </button>
        </div>

        {/* Response Display */}
        {response && (
          <div className="bg-slate-950 border border-slate-800/90 rounded-xl p-4 space-y-4">
            {/* Answer Summary */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                <span className="flex items-center gap-1.5 text-indigo-400 font-bold uppercase">
                  <Sparkles className="w-3.5 h-3.5" />
                  Agent [{response.agent.toUpperCase()}]:
                </span>
                <span>Latency: {response.latency_ms.toFixed(0)}ms • {response.data_mode} Mode</span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                {response.answer}
              </p>
            </div>

            {/* Structured Findings */}
            {response.analysis.findings && response.analysis.findings.length > 0 && (
              <div className="space-y-2">
                <div className="text-[11px] font-mono text-slate-400 uppercase font-bold">
                  Key Diagnostic Findings:
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {response.analysis.findings.map((f, i) => (
                    <div
                      key={i}
                      className="bg-slate-900/80 border border-slate-800 p-2.5 rounded-lg space-y-1 text-xs"
                    >
                      <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                        {f.title}
                      </div>
                      <p className="text-[11px] text-slate-400 leading-normal">{f.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations & Uncertainties */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Recommendations */}
              {response.analysis.recommendations && response.analysis.recommendations.length > 0 && (
                <div className="bg-slate-900/40 border border-slate-800/80 p-3 rounded-lg space-y-1.5">
                  <div className="text-[11px] font-mono text-emerald-400 uppercase font-bold flex items-center gap-1">
                    <ShieldAlert className="w-3.5 h-3.5" /> Operational Recommendations:
                  </div>
                  <ul className="space-y-1 text-xs">
                    {response.analysis.recommendations.map((r, i) => (
                      <li key={i} className="text-slate-300 flex items-start gap-1.5 text-[11px]">
                        <ArrowRight className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <strong className="text-slate-200">[{r.priority}]</strong> {r.action}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Uncertainties */}
              {response.analysis.uncertainties && response.analysis.uncertainties.length > 0 && (
                <div className="bg-slate-900/40 border border-slate-800/80 p-3 rounded-lg space-y-1.5">
                  <div className="text-[11px] font-mono text-amber-400 uppercase font-bold flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Sensor &amp; Model Uncertainties:
                  </div>
                  <ul className="space-y-1 text-xs">
                    {response.analysis.uncertainties.map((u, i) => (
                      <li key={i} className="text-slate-400 text-[11px]">
                        • <strong className="text-slate-300">{u.factor}:</strong> {u.reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Collapsible Evidence References */}
            <div className="border-t border-slate-800/80 pt-2">
              <button
                onClick={() => setShowEvidence(!showEvidence)}
                className="text-[11px] font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1 transition"
              >
                {showEvidence ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {showEvidence ? "Hide" : "Inspect"} System Telemetry Evidence Citations ({response.evidence.length} items)
              </button>

              {showEvidence && (
                <div className="mt-2 bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-[10px] font-mono space-y-1 max-h-48 overflow-y-auto">
                  {response.evidence.map((ev, i) => (
                    <div key={i} className="flex items-center justify-between border-b border-slate-800/50 py-1 last:border-0">
                      <span className="text-indigo-400 font-semibold">{ev.evidence_type}</span>
                      <span className="text-slate-300">{ev.metric || ev.id_reference || "-"}: {ev.value}</span>
                      {ev.timestamp && <span className="text-slate-500">{ev.timestamp.slice(11, 19)}</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
