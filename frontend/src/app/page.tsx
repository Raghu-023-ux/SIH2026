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
import AssessmentExplanationModal from "@/components/dashboard/AssessmentExplanationModal";
import SimulationPanel from "@/components/dashboard/SimulationPanel";
import FieldOperationsPanel from "@/components/dashboard/FieldOperationsPanel";
import BroadcastModal from "@/components/dashboard/BroadcastModal";
import SitRepModal from "@/components/dashboard/SitRepModal";
import { ShieldCheck, Info, Server, Activity, Database, CheckCircle2, Radio, MapPin, Layers, Sliders } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CommandCenter() {
  // Operational state
  const [summary, setSummary] = useState<DashboardSummaryData | null>(null);
  const [locations, setLocations] = useState<LocationMapItem[]>([]);
  const [events, setEvents] = useState<DisasterEventItem[]>([]);
  const [providers, setProviders] = useState<ProviderHealthItem[]>([]);
  const [bhoonidhiStatus, setBhoonidhiStatus] = useState<string>("NOT_CONFIGURED");
  const [dataMode, setDataMode] = useState<string>("LIVE");
  const [fieldSummary, setFieldSummary] = useState<any>(null);

  // Navigation tab state (Overview, Stations, Events)
  const [activeNavTab, setActiveNavTab] = useState<string>("overview");

  // Selection state
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [latestAssessment, setLatestAssessment] = useState<RiskAssessmentItem | null>(null);
  const [weatherHistory, setWeatherHistory] = useState<WeatherObservationItem[]>([]);
  const [riskHistory, setRiskHistory] = useState<RiskAssessmentItem[]>([]);
  const [timeline, setTimeline] = useState<EventTimelineMilestoneItem[]>([]);

  // Modal & Engine state
  const [investigateLocationId, setInvestigateLocationId] = useState<string | null>(null);
  const [explainModalLocationId, setExplainModalLocationId] = useState<string | null>(null);
  const [engineOnline, setEngineOnline] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [isRunningEngine, setIsRunningEngine] = useState<boolean>(false);
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [isAcknowledging, setIsAcknowledging] = useState<boolean>(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(30);
  const [broadcastTarget, setBroadcastTarget] = useState<{ eventId: string; locationId: string } | null>(null);
  const [sitrepEventId, setSitrepEventId] = useState<string | null>(null);

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

      // 4. Fetch System Provider Health & Bhoonidhi Status
      const sysRes = await fetch(`${API_URL}/api/v1/system/data-sources`);
      if (sysRes.ok) {
        const sysData = await sysRes.json();
        setProviders(sysData.providers || []);
        setDataMode(sysData.data_mode || "LIVE");
      }

      const eoRes = await fetch(`${API_URL}/api/v1/earth-observation/status`);
      if (eoRes.ok) {
        const eoData = await eoRes.json();
        setBhoonidhiStatus(eoData.status || "NOT_CONFIGURED");
      }

      // 5. Fetch Field Operations Summary
      const fieldRes = await fetch(`${API_URL}/api/v1/field/summary`);
      if (fieldRes.ok) {
        const fData = await fieldRes.json();
        setFieldSummary(fData);
      }

      // Format sync time
      const now = new Date();
      setLastUpdated(
        `${now.getUTCHours().toString().padStart(2, "0")}:${now.getUTCMinutes().toString().padStart(2, "0")}:${now
          .getUTCSeconds()
          .toString()
          .padStart(2, "0")} UTC`
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

  // Trigger Batch Ingest across all stations
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
    <div className="min-h-screen bg-black text-white flex flex-col font-sans">
      {/* 1. Header with Mode Switcher & Top-Level Navigation */}
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
        activeTab={activeNavTab}
        onSelectTab={(tab) => setActiveNavTab(tab)}
        bhoonidhiStatus={bhoonidhiStatus}
        fieldActiveCount={fieldSummary?.active_teams ?? 3}
        onOpenBroadcast={() => {
          if (activeSelectedEvent && selectedLocationId) {
            setBroadcastTarget({ eventId: activeSelectedEvent.id, locationId: selectedLocationId });
          } else if (locations.length > 0) {
            setBroadcastTarget({ eventId: events[0]?.id || "EV-BROADCAST", locationId: locations[0].id });
          }
        }}
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

        {/* Dynamic Nav View: OVERVIEW */}
        {activeNavTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Left Column (7 cols): Geographical Risk Map + Factor Details + Field Ops */}
            <div className="lg:col-span-7 space-y-4">
              {/* GIS Tactical Risk Map */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono px-1">
                  <span className="text-zinc-400 font-bold uppercase tracking-wider">
                    Geographical Risk Distribution (NER Corridor)
                  </span>
                  <span className="text-zinc-500 font-normal">Click marker to focus station telemetry</span>
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
                onExplainAssessment={() => selectedLocationId && setExplainModalLocationId(selectedLocationId)}
                onOpenBroadcast={(evId, locId) => setBroadcastTarget({ eventId: evId, locationId: locId })}
                onOpenSitRep={(evId) => setSitrepEventId(evId)}
              />

              {/* Field Operations & Ground Rescue Intelligence Panel */}
              <FieldOperationsPanel
                summary={fieldSummary}
                apiUrl={API_URL}
                onRefresh={refreshDashboardData}
              />
            </div>

            {/* Right Column (5 cols): Active Event Queue + Simulation Console */}
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
              <div className="p-3 bg-zinc-950 border border-zinc-800 rounded text-[11px] text-zinc-400 leading-relaxed flex items-start gap-2.5 font-sans">
                <Info className="w-4 h-4 text-zinc-400 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white font-mono">Prototype Decision Support:</strong> Platform operating in <span className="font-mono font-bold text-white">{dataMode}</span> mode. Hydro-meteorological thresholds and satellite metadata act as contextual decision support and do not replace official disaster management authorities.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Dynamic Nav View: STATIONS */}
        {activeNavTab === "stations" && (
          <div className="space-y-4">
            <div className="bg-zinc-950 border border-zinc-800 rounded p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                <div>
                  <h2 className="text-sm font-black font-mono text-white uppercase tracking-wider">
                    All Monitored Telemetry Stations ({locations.length})
                  </h2>
                  <p className="text-xs text-zinc-400">
                    Continuous environmental monitoring stations across the North Eastern Region corridor.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {locations.map((loc) => (
                  <div
                    key={loc.id}
                    className="bg-black border border-zinc-800 rounded p-3 space-y-2 hover:border-zinc-700 transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-black text-white font-mono text-xs">{loc.name}</span>
                      <span
                        className={`text-[9px] px-1.5 py-0.2 rounded font-black font-mono uppercase ${
                          loc.risk_level === "CRITICAL"
                            ? "bg-red-950 text-red-300 border border-red-700"
                            : loc.risk_level === "HIGH"
                            ? "bg-orange-950 text-orange-300 border border-orange-700"
                            : loc.risk_level === "MODERATE"
                            ? "bg-amber-950 text-amber-300 border border-amber-700"
                            : "bg-emerald-950 text-emerald-300 border border-emerald-700"
                        }`}
                      >
                        {loc.risk_level} ({loc.risk_score.toFixed(1)})
                      </span>
                    </div>

                    <div className="text-[11px] text-zinc-400 font-mono space-y-0.5">
                      <div>Location: {loc.district}, {loc.state}</div>
                      <div>Coordinates: {loc.latitude.toFixed(3)}°N, {loc.longitude.toFixed(3)}°E</div>
                      <div>Elevation: {loc.elevation} m | Slope: {loc.slope_angle}°</div>
                    </div>

                    <div className="pt-2 border-t border-zinc-850 flex items-center justify-between text-xs font-mono">
                      <button
                        onClick={() => {
                          setSelectedLocationId(loc.id);
                          setInvestigateLocationId(loc.id);
                        }}
                        className="text-white hover:text-zinc-300 font-bold transition flex items-center gap-1"
                      >
                        Investigate 360 &rarr;
                      </button>

                      <button
                        onClick={() => {
                          setSelectedLocationId(loc.id);
                          setActiveNavTab("overview");
                        }}
                        className="text-zinc-500 hover:text-zinc-300 transition"
                      >
                        Focus On Map
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Dynamic Nav View: EVENTS */}
        {activeNavTab === "events" && (
          <div className="space-y-4">
            <ActiveEventsList
              events={events}
              locations={locations}
              selectedEventId={activeSelectedEvent?.id || null}
              onSelectEvent={(evId, locId) => {
                handleSelectEvent(evId, locId);
                setActiveNavTab("overview");
              }}
            />
          </div>
        )}
      </main>

      {/* 3. Deep Investigation Modal (Station 360) */}
      <LocationInvestigateModal
        locationId={investigateLocationId}
        apiUrl={API_URL}
        onClose={() => setInvestigateLocationId(null)}
      />

      {/* 4. Assessment Explanation Modal */}
      {explainModalLocationId && (
        <AssessmentExplanationModal
          locationId={explainModalLocationId}
          locationName={locations.find((l) => l.id === explainModalLocationId)?.name || undefined}
          apiUrl={API_URL}
          onClose={() => setExplainModalLocationId(null)}
        />
      )}

      {/* 5. Multi-Channel Emergency Broadcast Modal */}
      {broadcastTarget && (
        <BroadcastModal
          eventId={broadcastTarget.eventId}
          locationId={broadcastTarget.locationId}
          apiUrl={API_URL}
          onClose={() => setBroadcastTarget(null)}
        />
      )}

      {/* 6. Formal NDMA Situation Report Modal */}
      {sitrepEventId && (
        <SitRepModal
          eventId={sitrepEventId}
          apiUrl={API_URL}
          onClose={() => setSitrepEventId(null)}
        />
      )}

      {/* 7. Understated Footer */}
      <footer className="border-t border-zinc-900 px-5 py-2 text-center text-[10px] text-zinc-600 font-mono">
        SIH 2026 Problem Statement SIH26001 | Central Disaster Intelligence Command Center &amp; Field Rescue Network
      </footer>
    </div>
  );
}
