"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  LineChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { WeatherObservationItem, RiskAssessmentItem } from "@/components/dashboard/types";
import { CloudRain, Droplets, TrendingUp } from "lucide-react";

interface TrendChartsProps {
  weatherHistory: WeatherObservationItem[];
  riskHistory: RiskAssessmentItem[];
}

export default function TrendCharts({ weatherHistory, riskHistory }: TrendChartsProps) {
  const [activeTab, setActiveTab] = useState<"rainfall" | "soil_moisture" | "risk_score">("rainfall");

  // Format weather series for charts
  const weatherChartData = weatherHistory.map((obs) => {
    const d = new Date(obs.timestamp);
    return {
      time: `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`,
      rainfall_1h: obs.rainfall_1h ?? 0,
      rainfall_24h: obs.rainfall_24h ?? 0,
      soil_moisture: obs.soil_moisture ?? 30,
      pressure: obs.pressure ?? 1012,
    };
  });

  // Format risk score history for charts
  const riskChartData = riskHistory.map((item) => {
    const d = new Date(item.timestamp);
    return {
      time: `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`,
      risk_score: item.risk_score,
      level: item.risk_level,
    };
  });

  return (
    <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 space-y-3">
      {/* Chart Category Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-indigo-400" />
          Time-Series Analytical Curves
        </div>

        <div className="flex items-center gap-1 text-xs font-mono">
          <button
            onClick={() => setActiveTab("rainfall")}
            className={`px-2.5 py-1 rounded transition flex items-center gap-1 ${
              activeTab === "rainfall"
                ? "bg-indigo-600 text-white font-bold"
                : "bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            <CloudRain className="w-3.5 h-3.5" />
            Rainfall Dynamics
          </button>

          <button
            onClick={() => setActiveTab("soil_moisture")}
            className={`px-2.5 py-1 rounded transition flex items-center gap-1 ${
              activeTab === "soil_moisture"
                ? "bg-indigo-600 text-white font-bold"
                : "bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            <Droplets className="w-3.5 h-3.5" />
            Soil Moisture %
          </button>

          <button
            onClick={() => setActiveTab("risk_score")}
            className={`px-2.5 py-1 rounded transition flex items-center gap-1 ${
              activeTab === "risk_score"
                ? "bg-indigo-600 text-white font-bold"
                : "bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            Risk Timeline
          </button>
        </div>
      </div>

      {/* 1. Rainfall Dynamics Chart */}
      {activeTab === "rainfall" && (
        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 font-mono">
            <span className="text-slate-300 font-semibold">1h Precipitation (bars, mm) vs 24h Cumulative (line, mm)</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1 text-cyan-400">■ 1h Rate</span>
              <span className="flex items-center gap-1 text-indigo-400">● 24h Acc</span>
            </div>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={weatherChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.5rem", fontSize: "12px" }}
                  labelStyle={{ color: "#94a3b8", fontWeight: "bold" }}
                />
                <Bar dataKey="rainfall_1h" name="1h Rain (mm)" fill="#06b6d4" radius={[3, 3, 0, 0]} barSize={14} />
                <Line type="monotone" dataKey="rainfall_24h" name="24h Cumulative (mm)" stroke="#818cf8" strokeWidth={2.5} dot={{ r: 2 }} />
                <ReferenceLine y={120} stroke="#f97316" strokeDasharray="4 4" label={{ value: "Warning Threshold (120mm)", fill: "#f97316", fontSize: 10 }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* 2. Soil Moisture Saturation Curve */}
      {activeTab === "soil_moisture" && (
        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 font-mono">
            <span className="text-slate-300 font-semibold">Volumetric Soil Moisture Saturation Rate (%)</span>
            <span className="text-amber-400">● Critical Pore Saturation &ge; 80%</span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weatherChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.5rem", fontSize: "12px" }}
                  labelStyle={{ color: "#94a3b8", fontWeight: "bold" }}
                />
                <Line type="monotone" dataKey="soil_moisture" name="Soil Moisture (%)" stroke="#38bdf8" strokeWidth={2.5} dot={{ r: 3 }} />
                <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "Critical Saturation (80%)", fill: "#ef4444", fontSize: 10 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* 3. Risk Score Progression Timeline */}
      {activeTab === "risk_score" && (
        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 font-mono">
            <span className="text-slate-300 font-semibold">Composite Landslide Risk Score Evolution (0-100)</span>
            <div className="flex items-center gap-2 text-[10px]">
              <span className="text-yellow-400">25 (Watch)</span>
              <span className="text-orange-400">50 (High)</span>
              <span className="text-red-400">75 (Critical)</span>
            </div>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={riskChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "0.5rem", fontSize: "12px" }}
                  labelStyle={{ color: "#94a3b8", fontWeight: "bold" }}
                />
                <Line type="monotone" dataKey="risk_score" name="Risk Score" stroke="#f43f5e" strokeWidth={3} dot={{ r: 3 }} />
                <ReferenceLine y={75} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "Critical", fill: "#ef4444", fontSize: 10 }} />
                <ReferenceLine y={50} stroke="#f97316" strokeDasharray="4 4" label={{ value: "High", fill: "#f97316", fontSize: 10 }} />
                <ReferenceLine y={25} stroke="#eab308" strokeDasharray="4 4" label={{ value: "Moderate", fill: "#eab308", fontSize: 10 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
