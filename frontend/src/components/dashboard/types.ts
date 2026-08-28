export interface LocationMapItem {
  id: string;
  name: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  elevation: number;
  slope_angle: number;
  susceptibility_score: number;
  risk_level: string;
  risk_score: number;
  confidence_score: number;
  active_event: boolean;
  event_id?: string | null;
  event_status?: string | null;
  event_severity?: string | null;
  rainfall_24h?: number;
  rainfall_1h?: number;
  soil_moisture?: number;
  trend_direction: string;
  last_updated: string;
}

export interface FactorDetail {
  name: string;
  raw_value: any;
  normalized_score: number; // 0.0 to 1.0
  weight: number;           // 0.0 to 1.0
  contribution: number;     // Points out of 100
  status: string;           // 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
  impact_type?: string;     // 'INCREASE_RISK', 'DECREASE_RISK', 'NEUTRAL'
  description?: string | null;
}

export interface AnomalyReport {
  metric: string;
  value: number;
  baseline: number;
  anomaly_score: number;
  is_anomalous: boolean;
  description?: string | null;
}

export interface TrendReport {
  metric: string;
  direction: string;
  slope: number;
  description?: string | null;
}

export interface DisasterEventItem {
  id: string;
  event_type: string;
  location_id: string;
  status: string;
  severity: string;
  risk_score: number;
  initial_risk: number;
  peak_risk: number;
  peak_severity: string;
  confidence_score: number;
  trajectory: string;
  detected_at: string;
  updated_at: string;
  expected_start?: string | null;
  expected_peak?: string | null;
  affected_area?: string | null;
  summary: string;
}

export interface WeatherObservationItem {
  id: string;
  location_id: string;
  timestamp: string;
  temperature?: number | null;
  humidity?: number | null;
  pressure?: number | null;
  wind_speed?: number | null;
  wind_direction?: number | null;
  rainfall_1h?: number | null;
  rainfall_6h?: number | null;
  rainfall_24h?: number | null;
  soil_moisture?: number | null;
  source: string;
  source_version?: string;
  freshness_status?: string;
  retrieved_at?: string;
  created_at: string;
}

export interface RiskAssessmentItem {
  id: string;
  location_id: string;
  timestamp: string;
  hazard_type: string;
  risk_level: string;
  risk_score: number;
  confidence_score: number;
  trajectory: string;
  reason: string;
  reason_codes: string[];
  factors: FactorDetail[];
  data_quality?: {
    status: string;
    completeness_score: number;
    freshness_score: number;
    missing_fields: string[];
    invalid_fields: string[];
    quality_notes?: string;
  } | null;
  signal_agreement?: {
    agreement_score: number;
    coherent_signals_count: number;
    conflicting_signals_count: number;
    agreement_level: string;
    details: string;
  } | null;
  assessment_version: string;
  created_at: string;
}

export interface EventTimelineMilestoneItem {
  timestamp: string;
  time_label: string;
  title: string;
  description: string;
  category: string;
  severity?: string | null;
}

export interface ProviderHealthItem {
  name: string;
  status: string;
  source_type: string;
  last_success?: string | null;
  last_failure?: string | null;
  consecutive_failures: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  last_latency_ms?: number | null;
  error_message?: string | null;
}

export interface DashboardSummaryData {
  active_events_count: number;
  critical_events_count: number;
  high_risk_count: number;
  moderate_risk_count: number;
  low_risk_count: number;
  total_monitored_locations: number;
  highest_risk_score: number;
  highest_risk_level: string;
  last_engine_run: string;
  data_sources_status: string;
  data_mode?: string;
}

export interface LocationInvestigationData {
  location: {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    district: string;
    state: string;
    elevation: number;
    slope_angle: number;
    susceptibility_score: number;
    created_at: string;
  };
  latest_assessment: RiskAssessmentItem | null;
  active_event: DisasterEventItem | null;
  weather_history: WeatherObservationItem[];
  risk_history: RiskAssessmentItem[];
  event_timeline: EventTimelineMilestoneItem[];
}
