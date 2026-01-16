/**
 * TypeScript-Typen für ML-Modelle und API-Responses
 * Migriert von Streamlit-Utils
 */

// Basis-Modell-Interface
export interface Model {
  id: number;
  model_id: number;
  name: string;
  custom_name?: string;
  model_type: string;
  target_variable: string;
  target_operator?: string;
  target_value?: number;
  future_minutes: number;
  price_change_percent: number;
  target_direction: string;
  features: string[];

  // Status
  is_active: boolean;

  // Alert-Konfiguration
  n8n_webhook_url?: string;
  n8n_enabled: boolean;
  n8n_send_mode: ('all' | 'alerts_only' | 'positive_only' | 'negative_only')[] | 'all' | 'alerts_only' | 'positive_only' | 'negative_only'; // Array oder String (für Rückwärtskompatibilität)
  alert_threshold: number;
  coin_filter_mode: 'all' | 'whitelist';
  coin_whitelist?: string[];

  // Ignore-Settings
  ignore_bad_seconds: number;
  ignore_positive_seconds: number;
  ignore_alert_seconds: number;

  // Max-Log-Entries-Settings
  max_log_entries_per_coin_negative?: number;
  max_log_entries_per_coin_positive?: number;
  max_log_entries_per_coin_alert?: number;
  send_ignored_to_n8n?: boolean;

  // Performance-Metriken (Training)
  accuracy?: number;
  f1_score?: number;
  precision?: number;
  recall?: number;
  roc_auc?: number;
  mcc?: number;
  simulated_profit_pct?: number;

  // Live-Performance-Metriken
  total_predictions?: number;
  positive_predictions?: number;
  average_probability?: number;
  last_prediction_at?: string;

  // Alert-Statistiken (optional, werden separat geladen)
  alert_stats?: {
    total_alerts: number;
    alerts_above_threshold: number;
    non_alerts_count: number;
    alerts_success: number;
    alerts_failed: number;
    alerts_pending: number;
    alerts_success_rate: number;
    non_alerts_success: number;
    non_alerts_failed: number;
    non_alerts_pending: number;
    non_alerts_success_rate: number;
    success_rate: number;
    // Performance-Summen (in Prozent)
    total_performance_pct?: number;
    alerts_profit_pct?: number;
    alerts_loss_pct?: number;
  };

  // Timestamps
  created_at?: string;
  updated_at?: string;
}

// Alert-Konfiguration für Updates
export interface AlertConfig {
  n8n_webhook_url?: string;
  n8n_enabled: boolean;
  n8n_send_mode: string[]; // Array von Send-Modi
  alert_threshold: number;
  coin_filter_mode: 'all' | 'whitelist';
  coin_whitelist?: string[];
}

// Ignore-Settings für Updates
export interface IgnoreSettings {
  ignore_bad_seconds: number;
  ignore_positive_seconds: number;
  ignore_alert_seconds: number;
}

// Kombinierte Response für Ignore-Settings
export interface IgnoreSettingsResponse {
  ignore_bad_seconds: number;
  ignore_positive_seconds: number;
  ignore_alert_seconds: number;
}

export interface MaxLogEntriesSettings {
  max_log_entries_per_coin_negative: number;
  max_log_entries_per_coin_positive: number;
  max_log_entries_per_coin_alert: number;
}

export interface MaxLogEntriesResponse {
  max_log_entries_per_coin_negative: number;
  max_log_entries_per_coin_positive: number;
  max_log_entries_per_coin_alert: number;
}

// Modell-Liste Response
export interface ModelsListResponse {
  models: Model[];
  total: number;
}

// Einzelnes Modell Response
export interface ModelResponse extends Model {}

// Prediction-Interface
export interface Prediction {
  id: number;
  active_model_id: number;
  coin_id: string;
  prediction: number; // 0 = negativ, 1 = positiv
  probability: number; // 0.0 - 1.0
  features_used: string[];
  predicted_at: string;
  created_at: string;
}

// Prediction-Liste Response
export interface PredictionsResponse {
  predictions: Prediction[];
  total: number;
  page: number;
  per_page: number;
}

// API-Error Response
export interface ApiError {
  detail: string;
  status_code?: number;
}

// Health-Check Response
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version?: string;
  uptime?: number;
}

// Alert-Evaluation Interface
export interface AlertEvaluation {
  id: number;
  model_id: number;
  active_model_id?: number;
  coin_id: string;
  prediction_id?: number;
  probability: number;
  status: 'pending' | 'success' | 'failed' | 'expired' | 'not_applicable' | 'non_alert' | 'aktiv' | 'inaktiv';
  evaluation_result?: 'success' | 'failed' | null;
  alert_timestamp: string;
  evaluation_timestamp?: string;
  predicted_price_change?: number;
  actual_price_change?: number;
  actual_price_change_pct?: number; // Tatsächliche Preisänderung in % (zum evaluation_timestamp)
  ath_price_change_pct?: number; // ATH (All-Time-High) Preisänderung in % während Evaluierungszeit
  ath_timestamp?: string; // Zeitpunkt des ATH
  price_change_percent?: number; // Ziel-Preisänderung in %
  target_direction?: 'up' | 'down'; // Richtung der Ziel-Änderung
  prediction_type?: 'time_based' | 'classic';
  remaining_seconds?: number;
  model_name?: string;
  alert_threshold?: number; // Alert-Threshold des Modells (für Status-Anzeige)
}

// Alert-Liste Response
export interface AlertsResponse {
  alerts: AlertEvaluation[];
  total: number;
  pending?: number;
  success?: number;
  failed?: number;
  expired?: number;
}

// Alert-Statistiken
// Coin Details Types
export interface PriceDataPoint {
  timestamp: string;
  price_open?: number;
  price_high?: number;
  price_low?: number;
  price_close?: number;
  volume_sol?: number;
  market_cap_close?: number;
}

export interface PredictionMarker {
  id: number;
  timestamp: string;
  prediction_timestamp?: string;
  evaluation_timestamp?: string;
  prediction: number;
  probability: number;
  alert_threshold: number;
  is_alert: boolean;
}

export interface EvaluationMarker {
  id: number;
  evaluation_timestamp?: string;
  prediction_timestamp: string;
  status: 'success' | 'failed' | 'pending' | 'expired';
  actual_price_change?: number;
  expected_price_change?: number;
  probability?: number;
}

export interface CoinDetails {
  coin_id: string;
  model_id: number;
  prediction_timestamp: string;
  price_history: PriceDataPoint[];
  predictions: PredictionMarker[];
  evaluations: EvaluationMarker[];
}

export interface AlertStatistics {
  total_alerts: number;
  pending: number;
  success: number;
  failed: number;
  expired: number;
  alerts_above_threshold?: number;
  non_alerts_count?: number;
  // Alerts (>= threshold) Statistiken
  alerts_success?: number;
  alerts_failed?: number;
  alerts_pending?: number;
  // Nicht-Alerts (< threshold) Statistiken
  non_alerts_success?: number;
  non_alerts_failed?: number;
  non_alerts_pending?: number;
  // Success Rates
  alerts_success_rate?: number;
  non_alerts_success_rate?: number;
  success_rate?: number;
  // Performance-Summen (in Prozent)
  total_performance_pct?: number;
  alerts_profit_pct?: number;
  alerts_loss_pct?: number;
}
