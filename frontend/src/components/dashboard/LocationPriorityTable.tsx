"use client";

import React, { useState, useMemo } from "react";
import { LocationMapItem } from "./types";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  ChevronUp,
  ChevronDown,
  Filter,
  Eye,
  SlidersHorizontal,
} from "lucide-react";

interface LocationPriorityTableProps {
  locations: LocationMapItem[];
  selectedLocationId: string | null;
  onSelectLocation: (locationId: string) => void;
  onOpenInvestigate: (locationId: string) => void;
}

type SortField = "risk_score" | "trend" | "confidence" | "name" | "rainfall";
type SortOrder = "asc" | "desc";

export default function LocationPriorityTable({
  locations,
  selectedLocationId,
  onSelectLocation,
  onOpenInvestigate,
}: LocationPriorityTableProps) {
  const [filterLevel, setFilterLevel] = useState<string>("ALL");
  const [filterTrend, setFilterTrend] = useState<string>("ALL");
  const [sortField, setSortField] = useState<SortField>("risk_score");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  const filteredAndSortedLocations = useMemo(() => {
    return locations
      .filter((loc) => {
        if (filterLevel !== "ALL" && loc.risk_level?.toUpperCase() !== filterLevel) {
          return false;
        }
        const locTrend = (loc.trajectory || loc.trend_direction || "STABLE").toUpperCase();
        if (filterTrend !== "ALL" && locTrend !== filterTrend) {
          return false;
        }
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchesName = loc.name.toLowerCase().includes(q);
          const matchesDistrict = loc.district?.toLowerCase().includes(q);
          const matchesState = loc.state?.toLowerCase().includes(q);
          const matchesId = loc.id.toLowerCase().includes(q);
          if (!matchesName && !matchesDistrict && !matchesState && !matchesId) return false;
        }
        return true;
      })
      .sort((a, b) => {
        let valA: any = a[sortField as keyof LocationMapItem];
        let valB: any = b[sortField as keyof LocationMapItem];

        if (sortField === "risk_score") {
          valA = a.risk_score ?? 0;
          valB = b.risk_score ?? 0;
        } else if (sortField === "confidence") {
          valA = a.confidence_score ?? 0;
          valB = b.confidence_score ?? 0;
        } else if (sortField === "rainfall") {
          valA = a.rainfall_24h ?? 0;
          valB = b.rainfall_24h ?? 0;
        } else if (sortField === "trend") {
          const weights: Record<string, number> = { INCREASING: 3, VOLATILE: 2, STABLE: 1, DECREASING: 0 };
          const trendA = (a.trajectory || a.trend_direction || "STABLE").toUpperCase();
          const trendB = (b.trajectory || b.trend_direction || "STABLE").toUpperCase();
          valA = weights[trendA] ?? 1;
          valB = weights[trendB] ?? 1;
        }


        if (valA < valB) return sortOrder === "asc" ? -1 : 1;
        if (valA > valB) return sortOrder === "asc" ? 1 : -1;
        return 0;
      });
  }, [locations, filterLevel, filterTrend, sortField, sortOrder, searchQuery]);

  const getRiskBadge = (level: string, score: number) => {
    switch (level?.toUpperCase()) {
      case "CRITICAL":
        return "bg-red-950 text-red-300 border-red-700 font-black";
      case "HIGH":
        return "bg-orange-950 text-orange-300 border-orange-700 font-black";
      case "MODERATE":
        return "bg-amber-950 text-amber-300 border-amber-700 font-black";
      default:
        return "bg-emerald-950 text-emerald-300 border-emerald-700 font-black";
    }
  };

  const getTrendIcon = (traj?: string) => {
    switch (traj?.toUpperCase()) {
      case "INCREASING":
        return <span className="text-red-400 font-mono flex items-center gap-0.5 font-bold"><TrendingUp className="w-3.5 h-3.5" /> Rising</span>;
      case "DECREASING":
        return <span className="text-emerald-400 font-mono flex items-center gap-0.5 font-bold"><TrendingDown className="w-3.5 h-3.5" /> Draining</span>;
      default:
        return <span className="text-zinc-400 font-mono flex items-center gap-0.5"><Minus className="w-3.5 h-3.5" /> Stable</span>;
    }
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded font-sans text-white overflow-hidden space-y-0">
      {/* Table Header Controls */}
      <div className="p-3 bg-black border-b border-zinc-800 flex flex-col md:flex-row md:items-center justify-between gap-2.5 text-xs font-mono">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-zinc-400" />
          <h3 className="font-bold text-white uppercase tracking-wider">
            Operational Priority Ranking ({filteredAndSortedLocations.length} Stations)
          </h3>
        </div>

        {/* Filter & Search Toolbar */}
        <div className="flex items-center gap-2 flex-wrap">
          <input
            type="text"
            placeholder="Filter by station/district..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-zinc-900 border border-zinc-750 text-zinc-200 text-xs px-2.5 py-1 rounded focus:outline-none focus:border-zinc-500 font-mono"
          />

          <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-750 px-2 py-1 rounded">
            <span className="text-zinc-400 text-[11px]">Level:</span>
            <select
              value={filterLevel}
              onChange={(e) => setFilterLevel(e.target.value)}
              className="bg-transparent text-white font-bold focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-zinc-950">ALL</option>
              <option value="CRITICAL" className="bg-zinc-950 text-red-400">CRITICAL</option>
              <option value="HIGH" className="bg-zinc-950 text-orange-400">HIGH</option>
              <option value="MODERATE" className="bg-zinc-950 text-amber-400">MODERATE</option>
              <option value="LOW" className="bg-zinc-950 text-emerald-400">LOW</option>
            </select>
          </div>

          <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-750 px-2 py-1 rounded">
            <span className="text-zinc-400 text-[11px]">Trend:</span>
            <select
              value={filterTrend}
              onChange={(e) => setFilterTrend(e.target.value)}
              className="bg-transparent text-white font-bold focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-zinc-950">ALL</option>
              <option value="INCREASING" className="bg-zinc-950 text-red-400">RISING</option>
              <option value="STABLE" className="bg-zinc-950">STABLE</option>
              <option value="DECREASING" className="bg-zinc-950 text-emerald-400">DRAINING</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono divide-y divide-zinc-850">
          <thead className="bg-zinc-900 text-zinc-400 text-[10px] uppercase tracking-wider font-bold">
            <tr>
              <th className="px-3 py-2.5"># Priority</th>
              <th className="px-3 py-2.5 cursor-pointer hover:text-white" onClick={() => handleSort("name")}>
                Station / Sector {sortField === "name" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th className="px-3 py-2.5 cursor-pointer hover:text-white" onClick={() => handleSort("risk_score")}>
                Risk Tier & Score {sortField === "risk_score" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th className="px-3 py-2.5 cursor-pointer hover:text-white" onClick={() => handleSort("trend")}>
                Trajectory {sortField === "trend" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th className="px-3 py-2.5 cursor-pointer hover:text-white" onClick={() => handleSort("confidence")}>
                Confidence {sortField === "confidence" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th className="px-3 py-2.5 cursor-pointer hover:text-white" onClick={() => handleSort("rainfall")}>
                24h Rain {sortField === "rainfall" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th className="px-3 py-2.5">Soil Wetness (Modelled)</th>
              <th className="px-3 py-2.5">Primary Driver</th>
              <th className="px-3 py-2.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-850 bg-black">
            {filteredAndSortedLocations.map((loc, idx) => {
              const isSelected = loc.id === selectedLocationId;
              const isCritical = loc.risk_level === "CRITICAL" || (loc.risk_score ?? 0) >= 75;
              const isHigh = loc.risk_level === "HIGH" || ((loc.risk_score ?? 0) >= 50 && (loc.risk_score ?? 0) < 75);

              return (
                <tr
                  key={loc.id}
                  onClick={() => onSelectLocation(loc.id)}
                  className={`cursor-pointer transition ${
                    isSelected
                      ? "bg-zinc-850 text-white"
                      : "hover:bg-zinc-900/70 text-zinc-300"
                  }`}
                >
                  <td className="px-3 py-2.5 font-bold text-zinc-400">
                    <span className={`inline-flex items-center justify-center w-5 h-5 rounded text-[10px] ${
                      idx === 0 ? "bg-red-950 text-red-300 border border-red-700 font-black" : "bg-zinc-900 text-zinc-300 border border-zinc-800"
                    }`}>
                      {idx + 1}
                    </span>
                  </td>

                  <td className="px-3 py-2.5">
                    <div className="font-bold text-white">{loc.name}</div>
                    <div className="text-[10px] text-zinc-500">{loc.district}, {loc.state} • ID: {loc.id}</div>
                  </td>

                  <td className="px-3 py-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] uppercase border ${getRiskBadge(loc.risk_level || "LOW", loc.risk_score || 0)}`}>
                      {loc.risk_level || "LOW"} ({(loc.risk_score ?? 0).toFixed(1)})
                    </span>
                  </td>

                  <td className="px-3 py-2.5">
                    {getTrendIcon(loc.trajectory || loc.trend_direction)}
                  </td>


                  <td className="px-3 py-2.5 font-bold text-zinc-200">
                    {((loc.confidence_score ?? 0.8) * 100).toFixed(0)}%
                  </td>

                  <td className="px-3 py-2.5 text-zinc-200 font-bold">
                    {(loc.rainfall_24h ?? 0).toFixed(1)} mm
                  </td>

                  <td className="px-3 py-2.5 text-zinc-400">
                    {loc.soil_moisture !== undefined && loc.soil_moisture !== null ? (
                      <span className="text-zinc-200 font-bold">{loc.soil_moisture.toFixed(1)}%</span>
                    ) : (
                      <span className="text-zinc-600 italic">N/A</span>
                    )}
                  </td>

                  <td className="px-3 py-2.5 text-zinc-300 max-w-[200px] truncate text-[11px]">
                    {loc.primary_factor ? loc.primary_factor.replace(/_/g, " ") : "Baseline Stability"}
                  </td>

                  <td className="px-3 py-2.5 text-right space-x-1.5 whitespace-nowrap">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectLocation(loc.id);
                      }}
                      className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 rounded text-[10px] font-bold text-zinc-200 transition"
                      title="Focus on Map"
                    >
                      <Eye className="w-3 h-3 inline mr-1" />
                      Focus
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenInvestigate(loc.id);
                      }}
                      className="px-2 py-1 bg-white hover:bg-zinc-200 text-black rounded text-[10px] font-black transition shadow-sm"
                      title="Open Station 360"
                    >
                      <ExternalLink className="w-3 h-3 inline mr-1" />
                      360°
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
