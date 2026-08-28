"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  DashboardSummaryData,
  LocationMapItem,
  DisasterEventItem,
  RiskAssessmentItem,
  WeatherObservationItem,
  EventTimelineMilestoneItem,
  ProviderHealthItem,
} from "@/components/dashboard/types";
import CommandHeader from "@/components/dashboard/CommandHeader";
import KPICards from "@/components/dashboard/KPICards";
import RiskMap from "@/components/dashboard/RiskMap";
import ActiveEventsList from "@/components/dashboard/ActiveEventsList";
import EventDetailPanel from "@/components/dashboard/EventDetailPanel";
import LocationInvestigateModal from "@/components/dashboard/LocationInvestigateModal";
import SimulationPanel from "@/components/dashboard/SimulationPanel";
import { ShieldCheck, Info, Server, Activity, Database, CheckCircle2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CommandCenter() {
  // Operational state
  const [summary, setSummary] = useState<DashboardSummaryData | null>(null);
  const [locations, setLocations] = useState<LocationMapItem[]>([]);
  const [events, setEvents] = useState<DisasterEventItem[]>([]);
  const [providers, setProviders] = useState<ProviderHealthItem[]>([]);
  const [dataMode, setDataMode] = useState<string>("LIVE");

  // Selection state
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [latestAssessment, setLatestAssessment] = useState<RiskAssessmentItem | null>(null);
  const [weatherHistory, setWeatherHistory] = useState<WeatherObservationItem[]>([]);
  const [riskHistory, setRiskHistory] = useState<RiskAssessmentItem[]>([]);
  const [timeline, setTimeline] = useState<EventTimelineMilestoneItem[]>([]);

  // Modal & Engine state
  const [investigateLocationId, setInvestigateLocationId] = useState<string | null>(null);
  const [engineOnline, setEngineOnline] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [isRunningEngine, setIsRunningEngine] = useState<boolean>(false);
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [isAcknowledging, setIsAcknowledging] = useState<boolean>(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(30); // 30s auto-refresh

  // Fetch full location investigation & telemetry details
  const loadLocationTelemetry = useCallback(
    async (locId: string) => {
      try {
        const res = await fetch(`${API_URL}/api/v1/locations/${locId}/investigate`);
        if (res.ok) {
          const inv = await res.json();
          setLatestAssessment(inv.latest_assessment);
          setWeatherHistory(inv.weather_history || []);
          setRiskHistory(inv.risk_history || []);
          setTimeline(inv.event_timeline || []);
        }
      } catch (err) {
        console.error("Failed to load telemetry for location", locId, err);
      }
    },
    []
  );

  // Fetch event specific timeline if available
  const loadEventTimeline = useCallback(
    async (evId: string) => {
      try {
        const res = await fetch(`${API_URL}/api/v1/events/${evId}/timeline`);
        if (res.ok) {
          const tl = await res.json();
          setTimeline(tl);
        }
      } catch (err) {
        console.error("Failed to load timeline for event", evId, err);
      }
    },
    []
  );

  // Master refresh function
  const refreshDashboardData = useCallback(async () => {
    try {
      // 1. Fetch Summary KPIs
      const sumRes = await fetch(`${API_URL}/api/v1/dashboard/summary`);
      if (sumRes.ok) {
        const sumData: DashboardSummaryData = await sumRes.json();
        setSummary(sumData);
        setEngineOnline(true);
      } else {
        setEngineOnline(false);
      }

      // 2. Fetch Map Locations
      const mapRes = await fetch(`${API_URL}/api/v1/locations/map`);
      let mapData: LocationMapItem[] = [];
      if (mapRes.ok) {
        mapData = await mapRes.json();
        setLocations(mapData);
      }

      // 3. Fetch Events
      const evRes = await fetch(`${API_URL}/api/v1/events`);
      let evData: DisasterEventItem[] = [];
      if (evRes.ok) {
        evData = await evRes.json();
        setEvents(evData);
      }

      // 4. Fetch System Provider Health
      const sysRes = await fetch(`${API_URL}/api/v1/system/data-sources`);
      if (sysRes.ok) {
        const sysData = await sysRes.json();
        setProviders(sysData.providers || []);
        setDataMode(sysData.data_mode || "LIVE");
      }

      // Format sync time
      const now = new Date();
      setLastUpdated(
        `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now
          .getSeconds()
          .toString()
          .padStart(2, "0")}`
      );

      // Auto-select active or critical station if none selected
      setSelectedLocationId((prev) => {
        if (prev && mapData.some((l) => l.id === prev)) {
          return prev;
        }
        if (mapData.length > 0) {
          const highest = [...mapData].sort((a, b) => b.risk_score - a.risk_score)[0];
          return highest.id;
        }
        return null;
      });
    } catch (err) {
      console.error("Dashboard refresh error:", err);
      setEngineOnline(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    refreshDashboardData();
  }, [refreshDashboardData]);

  // Telemetry loader when selected location changes
  useEffect(() => {
    if (selectedLocationId) {
      loadLocationTelemetry(selectedLocationId);
    }
  }, [selectedLocationId, loadLocationTelemetry]);

  // Auto-refresh polling loop
  useEffect(() => {
    if (autoRefreshInterval <= 0) return;
    const interval = setInterval(refreshDashboardData, autoRefreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefreshInterval, refreshDashboardData]);

  // Toggle Live vs Simulation Data Mode
  const handleToggleDataMode = async (mode: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/ingestion/mode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      if (res.ok) {
        const data = await res.json();
        setDataMode(data.current_mode);
        await refreshDashboardData();
      }
    } catch (err) {
      console.error("Failed to toggle data mode:", err);
    }
  };

  // Trigger Batch Live Ingestion across all stations
  const handleTriggerBatchIngest = async () => {
    setIsIngesting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/ingestion/batch`, {
        method: "POST",
      });
      if (res.ok) {
        await refreshDashboardData();
        if (selectedLocationId) {
          await loadLocationTelemetry(selectedLocationId);
        }
      }
    } catch (err) {
      console.error("Batch ingestion error:", err);
    } finally {
      setIsIngesting(false);
    }
  };

  // Trigger manual engine evaluation run
  const handleTriggerEngineRun = async () => {
    setIsRunningEngine(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/engine/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force_fresh_fetch: true }),
      });
      if (res.ok) {
        await refreshDashboardData();
        if (selectedLocationId) {
          await loadLocationTelemetry(selectedLocationId);
        }
      }
    } catch (err) {
      console.error("Engine run error:", err);
    } finally {
      setIsRunningEngine(false);
    }
  };

  // Run simulation scenario
  const handleRunSimulation = async (scenario: string, locId: string) => {
    setIsSimulating(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/simulation/scenario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario,
          location_id: locId,
          seed: 42,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Simulation execution failed");
      }
      setSelectedLocationId(locId);
      await refreshDashboardData();
      await loadLocationTelemetry(locId);
    } finally {
      setIsSimulating(false);
    }
  };

  // Handle Event Selection
  const handleSelectEvent = (eventId: string, locId: string) => {
    setSelectedEventId(eventId);
    setSelectedLocationId(locId);
    loadEventTimeline(eventId);
    loadLocationTelemetry(locId);
  };

  // Handle Location Selection from map
  const handleSelectLocation = (locId: string) => {
    setSelectedLocationId(locId);
    const relatedEvent = events.find((e) => e.location_id === locId && e.status !== "RESOLVED");
    setSelectedEventId(relatedEvent ? relatedEvent.id : null);
    loadLocationTelemetry(locId);
    if (relatedEvent) {
      loadEventTimeline(relatedEvent.id);
    }
  };

  // Acknowledge Event
  const handleAcknowledgeEvent = async (eventId: string) => {
    setIsAcknowledging(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/events/${eventId}/acknowledge`, {
        method: "POST",
      });
      if (res.ok) {
        await refreshDashboardData();
        if (selectedLocationId) {
          await loadLocationTelemetry(selectedLocationId);
        }
      }
    } catch (err) {
      console.error("Failed to acknowledge event:", err);
    } finally {
      setIsAcknowledging(false);
    }
  };

  const activeSelectedLocation = locations.find((l) => l.id === selectedLocationId) || null;
  const activeSelectedEvent =
    events.find((e) => e.id === selectedEventId) ||
    events.find((e) => e.location_id === selectedLocationId && e.status !== "RESOLVED") ||
    null;

  return (
    <div className="min-h-screen bg-[#06090e] text-slate-100 flex flex-col font-sans">
      {/* 1. Header with Mode Switcher & Ingest */}
      <CommandHeader
        engineOnline={engineOnline}
        lastUpdated={lastUpdated}
        dataSourcesStatus={summary?.data_sources_status || "OPEN-METEO LIVE / NER STATIONS"}
        dataMode={dataMode}
        onToggleDataMode={handleToggleDataMode}
        onTriggerEngineRun={handleTriggerEngineRun}
        onTriggerBatchIngest={handleTriggerBatchIngest}
        isRunningEngine={isRunningEngine}
        isIngesting={isIngesting}
        autoRefreshInterval={autoRefreshInterval}
        onToggleAutoRefresh={(sec) => setAutoRefreshInterval(sec)}
      />

      {/* 2. Main Dashboard Content */}
      <main className="flex-1 p-3.5 sm:p-5 max-w-[1700px] w-full mx-auto space-y-4">
        {/* KPI Counter Row */}
        <KPICards
          activeEventsCount={summary?.active_events_count ?? 0}
          criticalEventsCount={summary?.critical_events_count ?? 0}
          highRiskCount={summary?.high_risk_count ?? 0}
          moderateRiskCount={summary?.moderate_risk_count ?? 0}
          totalLocations={summary?.total_monitored_locations ?? 0}
          highestRiskScore={summary?.highest_risk_score ?? 0.0}
          highestRiskLevel={summary?.highest_risk_level ?? "LOW"}
        />

        {/* Data Sources & Ingestion Health Strip */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate-400">
            <Server className="w-4 h-4 text-indigo-400" />
            <span className="font-bold uppercase text-slate-300">Data Sources &amp; Providers:</span>
          </div>

          <div className="flex items-center gap-4 flex-wrap">
            {providers.map((p) => (
              <div key={p.name} className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    p.status === "HEALTHY"
                      ? "bg-emerald-400"
                      : p.status === "SIMULATED"
                      ? "bg-amber-400"
                      : "bg-red-400"
                  }`}
                />
                <span className="text-slate-300 font-medium capitalize">{p.name}:</span>
                <span className="text-slate-400">{p.status}</span>
                {p.last_latency_ms && (
                  <span className="text-[10px] text-slate-500">({p.last_latency_ms.toFixed(0)}ms)</span>
                )}
              </div>
            ))}
          </div>

          <div className="text-[11px] text-slate-500 flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <span>Cache: In-Memory TTL (600s)</span>
          </div>
        </div>

        {/* Core Tactical Grid: Map & Details on Left, Event Queue & Simulation on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left Column: Geographical Risk Map + Factor Details (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            {/* GIS Tactical Risk Map */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono px-1">
                <span className="text-slate-400 font-bold uppercase tracking-wider">
                  Geographical Risk Distribution (NER Corridor)
                </span>
                <span className="text-slate-500 font-normal">Click marker to focus station telemetry</span>
              </div>
              <RiskMap
                locations={locations}
                selectedLocationId={selectedLocationId}
                onSelectLocation={handleSelectLocation}
                onOpenInvestigate={(id) => setInvestigateLocationId(id)}
              />
            </div>

            {/* Event & Factor Deep Detail Panel */}
            <EventDetailPanel
              event={activeSelectedEvent}
              location={activeSelectedLocation}
              latestAssessment={latestAssessment}
              weatherHistory={weatherHistory}
              riskHistory={riskHistory}
              timeline={timeline}
              onAcknowledgeEvent={handleAcknowledgeEvent}
              isAcknowledging={isAcknowledging}
              onOpenInvestigate={(id) => setInvestigateLocationId(id)}
            />
          </div>

          {/* Right Column: Active Event Queue + Simulation Console (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            {/* Active Event Queue */}
            <ActiveEventsList
              events={events}
              locations={locations}
              selectedEventId={activeSelectedEvent?.id || null}
              onSelectEvent={handleSelectEvent}
            />

            {/* Scenario Simulation Console */}
            <SimulationPanel
              locations={locations}
              selectedLocationId={selectedLocationId}
              onSelectLocation={(id) => {
                setSelectedLocationId(id);
                loadLocationTelemetry(id);
              }}
              onRunSimulation={handleRunSimulation}
              isSimulating={isSimulating}
            />

            {/* Decision Support Compliance Notice */}
            <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl text-[11px] text-slate-400 leading-relaxed flex items-start gap-2.5">
              <Info className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-300">Operational Notice:</strong> The platform is currently operating in <strong className="text-indigo-300">{dataMode}</strong> mode. Real meteorological observations from public APIs are evaluated against an analytical prototype landslide-risk assessment pipeline. Output scores provide situational hazard assessment and do not supersede official state authority disaster bulletins.
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 3. Deep Investigation Modal */}
      <LocationInvestigateModal
        locationId={investigateLocationId}
        apiUrl={API_URL}
        onClose={() => setInvestigateLocationId(null)}
      />

      {/* 4. Footer */}
      <footer className="border-t border-slate-900 px-5 py-2.5 text-center text-[11px] text-slate-600 font-mono">
        SIH 2026 Problem Statement SIH26001 | Central Disaster Intelligence Command Center | Open-Meteo &amp; NER Ground Sensors
      </footer>
    </div>
  );
}
