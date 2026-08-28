"use client";

import React, { useEffect, useState } from "react";
import { Activity, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";

interface HealthData {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  disclaimer: string;
}

export default function SystemStatus({ apiUrl }: { apiUrl: string }) {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/health`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || "Failed to reach backend engine");
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            System & Engine Status
          </h2>
        </div>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="text-xs text-slate-400 hover:text-slate-200 transition flex items-center gap-1 bg-slate-800/60 px-2.5 py-1 rounded-md border border-slate-700"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Check Health
        </button>
      </div>

      {loading && !health && !error && (
        <div className="text-sm text-slate-400 animate-pulse py-2">
          Connecting to Disaster Intelligence Engine API...
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 bg-red-950/40 border border-red-800/60 rounded-lg p-3 text-red-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400 mt-0.5" />
          <div>
            <div className="font-medium">Backend Offline or Unreachable</div>
            <div className="text-xs text-red-400/80 mt-0.5">{error}</div>
            <div className="text-xs text-slate-400 mt-1">Ensure backend is running at {apiUrl}</div>
          </div>
        </div>
      )}

      {health && (
        <div className="space-y-3">
          <div className="flex items-center justify-between bg-slate-950/50 p-3 rounded-lg border border-slate-800/80">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-sm font-medium text-slate-200">Engine API Online</span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-800 font-mono">
              {health.status.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
            <div className="bg-slate-950/40 p-2.5 rounded border border-slate-800/50">
              <span className="text-slate-500 block">Version</span>
              <span className="font-mono text-slate-200">{health.version}</span>
            </div>
            <div className="bg-slate-950/40 p-2.5 rounded border border-slate-800/50">
              <span className="text-slate-500 block">Environment</span>
              <span className="font-mono text-slate-200">{health.environment}</span>
            </div>
          </div>

          <div className="text-[11px] text-amber-400/80 bg-amber-950/20 border border-amber-800/40 p-2 rounded">
            <strong>Disclaimer:</strong> {health.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
}
