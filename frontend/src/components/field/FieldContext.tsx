"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface FieldTeam {
  id: string;
  team_name: string;
  callsign: string;
  status: string;
  latitude?: number | null;
  longitude?: number | null;
  contact_channel?: string | null;
}

export interface OperationalMessage {
  id: string;
  sender_id: string;
  recipient_team: string;
  priority: string;
  message: string;
  created_at: string;
  acknowledged_at?: string | null;
}

export interface NearbyIncident {
  event_id?: string | null;
  location_id: string;
  location_name: string;
  hazard_type: string;
  severity: string;
  risk_score: number;
  distance_km: number;
}

export interface FieldReportImageItem {
  id: string;
  report_id: string;
  storage_key: string;
  mime_type: string;
  file_size: number;
  url: string;
  uploaded_by?: string | null;
  created_at: string;
}

export interface FieldReport {
  id: string;
  report_type: string;
  severity: string;
  description: string;
  timestamp: string;
  status: string;
  reported_by: string;
  latitude?: number | null;
  longitude?: number | null;
  location_accuracy?: number | null;
  location_source?: string;
  images?: FieldReportImageItem[];
}

export interface AssistanceRequest {
  id: string;
  team_id: string;
  request_type: string;
  priority: string;
  description: string;
  status: string;
  latitude?: number | null;
  longitude?: number | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface AssignmentData {
  team: FieldTeam;
  assigned_location?: {
    id: string;
    name: string;
    district: string;
    state: string;
    elevation: number;
    slope_angle: number;
  } | null;
  assigned_event?: {
    id: string;
    hazard_type: string;
    severity: string;
    status: string;
    risk_score: number;
    confidence_score: number;
    summary: string;
    updated_at: string;
  } | null;
  immediate_conditions: {
    slope_risk: string;
    rainfall_state: string;
    soil_saturation_state: string;
    road_status: string;
    nearest_hazard_km?: number | null;
  };
  nearby_incidents: NearbyIncident[];
  recent_messages: OperationalMessage[];
  recent_reports: FieldReport[];
}

interface FieldContextType {
  callsign: string;
  setCallsign: (c: string) => void;
  data: AssignmentData | null;
  loading: boolean;
  online: boolean;
  coords: { lat: number; lon: number; accuracy?: number } | null;
  geoStatus: string;
  geoSource: "GPS" | "MANUAL" | "UNKNOWN";
  refreshBriefing: () => Promise<void>;
  updateTeamStatus: (status: string) => Promise<void>;
  acknowledgeMessage: (id: string) => Promise<void>;
  requestGPSLocation: () => Promise<void>;
  apiUrl: string;
}

const FieldContext = createContext<FieldContextType | undefined>(undefined);

export function FieldProvider({ children }: { children: ReactNode }) {
  const [callsign, setCallsign] = useState<string>("ALPHA-1");
  const [data, setData] = useState<AssignmentData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [online, setOnline] = useState<boolean>(true);
  const [coords, setCoords] = useState<{ lat: number; lon: number; accuracy?: number } | null>(null);
  const [geoStatus, setGeoStatus] = useState<string>("Locating device...");
  const [geoSource, setGeoSource] = useState<"GPS" | "MANUAL" | "UNKNOWN">("UNKNOWN");

  const requestGPSLocation = useCallback(async () => {
    if (typeof window !== "undefined" && "geolocation" in navigator) {
      setGeoStatus("Acquiring GPS fix...");
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            accuracy: Math.round(pos.coords.accuracy || 10),
          });
          setGeoStatus(`GPS Acquired (±${Math.round(pos.coords.accuracy || 10)}m)`);
          setGeoSource("GPS");
        },
        (err) => {
          console.warn("Geolocation fallback:", err.message);
          setGeoStatus("GPS Unavailable (Sector Default)");
          setCoords({ lat: 27.3389, lon: 88.6065, accuracy: 50 });
          setGeoSource("MANUAL");
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 }
      );
    } else {
      setGeoStatus("Location Unsupported");
      setCoords({ lat: 27.3389, lon: 88.6065, accuracy: 100 });
      setGeoSource("UNKNOWN");
    }
  }, []);

  useEffect(() => {
    requestGPSLocation();
  }, [requestGPSLocation]);

  const refreshBriefing = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/field/assignments?callsign=${callsign}`);
      if (res.ok) {
        const briefing: AssignmentData = await res.json();
        setData(briefing);
        setOnline(true);
      } else {
        setOnline(false);
      }
    } catch (err) {
      console.error("Failed to load field briefing", err);
      setOnline(false);
    } finally {
      setLoading(false);
    }
  }, [callsign]);

  useEffect(() => {
    refreshBriefing();
    const interval = setInterval(refreshBriefing, 15000);
    return () => clearInterval(interval);
  }, [refreshBriefing]);

  const updateTeamStatus = async (newStatus: string) => {
    if (!data?.team?.id) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/field/teams/${data.team.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: newStatus,
          latitude: coords?.lat,
          longitude: coords?.lon,
        }),
      });
      if (res.ok) {
        await refreshBriefing();
      }
    } catch (err) {
      console.error("Status update error", err);
    }
  };

  const acknowledgeMessage = async (msgId: string) => {
    try {
      const res = await fetch(
        `${API_URL}/api/v1/field/messages/${msgId}/acknowledge?acknowledged_by=${callsign}`,
        { method: "POST" }
      );
      if (res.ok) {
        await refreshBriefing();
      }
    } catch (err) {
      console.error("Message acknowledgment error", err);
    }
  };

  return (
    <FieldContext.Provider
      value={{
        callsign,
        setCallsign,
        data,
        loading,
        online,
        coords,
        geoStatus,
        geoSource,
        refreshBriefing,
        updateTeamStatus,
        acknowledgeMessage,
        requestGPSLocation,
        apiUrl: API_URL,
      }}
    >
      {children}
    </FieldContext.Provider>
  );
}

export function useField() {
  const context = useContext(FieldContext);
  if (!context) {
    throw new Error("useField must be used within a FieldProvider");
  }
  return context;
}
