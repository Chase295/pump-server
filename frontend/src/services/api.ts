/**
 * API-Service Layer
 * Zentralisiert alle API-Calls mit Axios und React Query
 */
import axios from 'axios';
import type { AxiosResponse } from 'axios';
import type {
  Model,
  ModelsListResponse,
  ModelResponse,
  AlertConfig,
  IgnoreSettings,
  IgnoreSettingsResponse,
  MaxLogEntriesSettings,
  MaxLogEntriesResponse,
  PredictionsResponse,
  HealthResponse,
  ApiError,
  AlertsResponse,
  AlertStatistics,
  CoinDetails
} from '../types/model';

// API-Konfiguration
// Verwende relative URL, wenn die App auf derselben Domain läuft, sonst Environment Variable oder localhost
const getApiBaseUrl = () => {
  // Wenn Environment Variable gesetzt ist, verwende diese
  if (import.meta.env.REACT_APP_API_URL) {
    return import.meta.env.REACT_APP_API_URL;
  }
  
  // Wenn im Browser, verwende die aktuelle Domain
  if (typeof window !== 'undefined') {
    // Wenn auf test.local.chase295.de, verwende diese Domain
    if (window.location.origin.includes('test.local.chase295.de')) {
      return `${window.location.origin}/api`;
    }
    // Sonst verwende relative URL (funktioniert, wenn Frontend und API auf derselben Domain sind)
    return '/api';
  }
  
  // Fallback für SSR oder Tests
  return 'http://localhost:3000/api';
};

const API_BASE_URL = getApiBaseUrl();

// Axios-Instanz mit Standard-Konfiguration
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response Interceptor für Error-Handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 404-Fehler für Predictions werden speziell behandelt (Modell noch nicht importiert)
    if (error.response?.status === 404 && error.config?.url?.includes('/predictions/')) {
      // Für Predictions-Requests: Werfe einen speziellen Fehler, der als "nicht gefunden" erkannt wird
      const customError = new Error('Ressource nicht gefunden') as any;
      customError.response = error.response;
      customError.isNotFound = true;
      throw customError;
    }
    if (error.response?.status === 404) {
      throw new Error('Ressource nicht gefunden');
    }
    if (error.response?.status === 422) {
      // 422 Unprocessable Entity - Validierungsfehler
      const detail = error.response.data?.detail;
      if (Array.isArray(detail)) {
        // Pydantic Validierungsfehler als Array
        const messages = detail.map((err: any) => {
          const field = err.loc?.join('.') || 'Feld';
          return `${field}: ${err.msg}`;
        }).join(', ');
        throw new Error(`Validierungsfehler: ${messages}`);
      } else if (typeof detail === 'string') {
        throw new Error(detail);
      } else {
        throw new Error('Validierungsfehler. Bitte überprüfen Sie die Eingaben.');
      }
    }
    if (error.response?.status === 500) {
      throw new Error('Server-Fehler. Bitte später erneut versuchen.');
    }
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    throw new Error('Netzwerk-Fehler. Bitte überprüfen Sie Ihre Verbindung.');
  }
);

// ============================================================================
// MODELS API
// ============================================================================

export const modelsApi = {
  // Alle Modelle abrufen
  getAll: async (): Promise<Model[]> => {
    const response: AxiosResponse<ModelsListResponse> = await apiClient.get('/models?include_inactive=true');
    return response.data.models;
  },

  // Verfügbare Modelle zum Importieren abrufen
  getAvailable: async (): Promise<any[]> => {
    const response: AxiosResponse<{ models: any[]; total: number }> = await apiClient.get('/models/available');
    return response.data.models;
  },

  // Details eines verfügbaren Modells abrufen
  getAvailableModelDetails: async (modelId: number): Promise<any> => {
    const response = await apiClient.get(`/models/available/${modelId}`);
    return response.data;
  },

  // Modell importieren
  importModel: async (modelId: number): Promise<any> => {
    const response = await apiClient.post('/models/import', { model_id: modelId });
    return response.data;
  },

  // Service neu starten (erfordert manuelle Bestätigung)
  restartService: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/system/restart');
    return response.data;
  },

  // Konfiguration
  getConfig: async (): Promise<any> => {
    const response = await apiClient.get('/config');
    return response.data;
  },

  updateConfig: async (config: any): Promise<any> => {
    const response = await apiClient.post('/config', config);
    return response.data;
  },

  // Einzelnes Modell abrufen
  getById: async (id: number): Promise<Model> => {
    const response: AxiosResponse<ModelResponse> = await apiClient.get(`/models/${id}`);
    return response.data;
  },

  // Alert-Konfiguration aktualisieren
  updateAlertConfig: async (id: number, config: AlertConfig): Promise<{ message: string }> => {
    const response = await apiClient.patch(`/models/${id}/alert-config`, config);
    return response.data;
  },

  // Ignore-Settings aktualisieren
  updateIgnoreSettings: async (id: number, settings: IgnoreSettings): Promise<{ message: string }> => {
    const response = await apiClient.patch(`/models/${id}/ignore-settings`, settings);
    return response.data;
  },

  // Ignore-Settings abrufen
  getIgnoreSettings: async (id: number): Promise<IgnoreSettingsResponse> => {
    const response: AxiosResponse<IgnoreSettingsResponse> = await apiClient.get(`/models/${id}/ignore-settings`);
    return response.data;
  },
  updateMaxLogEntries: async (id: number, settings: MaxLogEntriesSettings): Promise<{ message: string }> => {
    const response = await apiClient.patch(`/models/${id}/max-log-entries`, settings);
    return response.data;
  },
  getMaxLogEntries: async (id: number): Promise<MaxLogEntriesResponse> => {
    const response: AxiosResponse<MaxLogEntriesResponse> = await apiClient.get(`/models/${id}/max-log-entries`);
    return response.data;
  },

  // Modell umbenennen
  rename: async (id: number, customName: string): Promise<{ message: string }> => {
    const response = await apiClient.patch(`/models/${id}/rename`, { custom_name: customName });
    return response.data;
  },

  // Modell aktivieren/deaktivieren
  toggleActive: async (id: number, active: boolean): Promise<{ message: string }> => {
    const endpoint = active ? `/models/${id}/deactivate` : `/models/${id}/activate`;
    const response = await apiClient.post(endpoint);
    return response.data;
  },

  // Modell löschen
  delete: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/models/${id}`);
    return response.data;
  }
};

// ============================================================================
// PREDICTIONS API
// ============================================================================

export const predictionsApi = {
  // Predictions für ein Modell abrufen
  getForModel: async (
    modelId: number,
    page: number = 1,
    perPage: number = 50
  ): Promise<PredictionsResponse> => {
    const response: AxiosResponse<PredictionsResponse> = await apiClient.get(
      `/predictions/model/${modelId}?page=${page}&per_page=${perPage}`
    );
    return response.data;
  },

  // Einzelne Prediction abrufen
  getById: async (id: number) => {
    const response = await apiClient.get(`/predictions/${id}`);
    return response.data;
  },

  // Neue Prediction erstellen (für Tests)
  create: async (modelId: number, coinId: string) => {
    const response = await apiClient.post('/predict', {
      active_model_id: modelId,
      coin_id: coinId
    });
    return response.data;
  }
};

// ============================================================================
// HEALTH & SYSTEM API
// ============================================================================

export const systemApi = {
  // Health-Check
  health: async (): Promise<HealthResponse> => {
    const response: AxiosResponse<HealthResponse> = await apiClient.get('/health');
    return response.data;
  },

  // System-Stats
  stats: async () => {
    const response = await apiClient.get('/stats');
    return response.data;
  }
};

// ============================================================================
// ALERTS API
// ============================================================================

export const coinsApi = {
  // Coin-Details abrufen
  getDetails: async (
    modelId: number,
    coinId: string,
    timeWindowMinutes: number = 60,
    timeOffsetMinutes: number = 0,
    predictionId?: number  // NEU: Optional prediction_id
  ): Promise<CoinDetails> => {
    const params: any = {};
    if (predictionId) {
      params.prediction_id = predictionId;
    } else {
      params.time_window_minutes = timeWindowMinutes;
      params.time_offset_minutes = timeOffsetMinutes;
    }
    
    const response = await apiClient.get(
      `/models/${modelId}/coins/${coinId}/details`,
      { params }
    );
    return response.data;
  }
};

// ============================================================================
// MODEL PREDICTIONS API (NEUE EINFACHE ARCHITEKTUR)
// ============================================================================

export const modelPredictionsApi = {
  // Vorhersagen für ein Modell abrufen
  getForModel: async (
    activeModelId: number,
    limit: number = 100,
    offset: number = 0,
    filters?: {
      // Alte Filter (für Kompatibilität)
      tag?: 'negativ' | 'positiv' | 'alert';
      status?: 'aktiv' | 'inaktiv';
      coinId?: string;
      // Neue erweiterte Filter
      probabilityOperator?: '>' | '<' | '=';
      probabilityValue?: number;
      predictionStatuses?: ('negativ' | 'positiv' | 'alert')[];
      evaluationStatuses?: ('success' | 'failed' | 'wait')[];
      athHighestOperator?: '>' | '<' | '=';
      athHighestValue?: number;
      athLowestOperator?: '>' | '<' | '=';
      athLowestValue?: number;
      actualChangeOperator?: '>' | '<' | '=';
      actualChangeValue?: number;
      alertTimeFrom?: string;
      alertTimeTo?: string;
      evaluationTimeFrom?: string;
      evaluationTimeTo?: string;
    }
  ): Promise<{ predictions: any[]; model_target?: string; total: number; limit: number; offset: number }> => {
    const params = new URLSearchParams({
      active_model_id: activeModelId.toString(),
      limit: limit.toString(),
      offset: offset.toString()
    });

    // Alte Filter (für Kompatibilität)
    if (filters?.tag) {
      params.append('tag', filters.tag);
    }
    if (filters?.status) {
      params.append('status', filters.status);
    }
    if (filters?.coinId) {
      params.append('coin_id', filters.coinId);
    }

    // Neue erweiterte Filter
    if (filters?.probabilityOperator && filters.probabilityValue !== undefined) {
      params.append('probability_operator', filters.probabilityOperator);
      params.append('probability_value', filters.probabilityValue.toString());
    }
    if (filters?.predictionStatuses && filters.predictionStatuses.length > 0) {
      filters.predictionStatuses.forEach(status => {
        params.append('prediction_statuses', status);
      });
    }
    if (filters?.evaluationStatuses && filters.evaluationStatuses.length > 0) {
      filters.evaluationStatuses.forEach(status => {
        params.append('evaluation_statuses', status);
      });
    }
    if (filters?.athHighestOperator && filters.athHighestValue !== undefined) {
      params.append('ath_highest_operator', filters.athHighestOperator);
      params.append('ath_highest_value', filters.athHighestValue.toString());
    }
    if (filters?.athLowestOperator && filters.athLowestValue !== undefined) {
      params.append('ath_lowest_operator', filters.athLowestOperator);
      params.append('ath_lowest_value', filters.athLowestValue.toString());
    }
    if (filters?.actualChangeOperator && filters.actualChangeValue !== undefined) {
      params.append('actual_change_operator', filters.actualChangeOperator);
      params.append('actual_change_value', filters.actualChangeValue.toString());
    }
    if (filters?.alertTimeFrom) {
      params.append('alert_time_from', filters.alertTimeFrom);
    }
    if (filters?.alertTimeTo) {
      params.append('alert_time_to', filters.alertTimeTo);
    }
    if (filters?.evaluationTimeFrom) {
      params.append('evaluation_time_from', filters.evaluationTimeFrom);
    }
    if (filters?.evaluationTimeTo) {
      params.append('evaluation_time_to', filters.evaluationTimeTo);
    }

    const response = await apiClient.get(`/model-predictions?${params.toString()}`);
    return response.data;
  },
  
  // Alle Predictions für ein Modell löschen
  deleteForModel: async (activeModelId: number): Promise<{ success: boolean; deleted_predictions: number }> => {
    const response = await apiClient.delete(`/model-predictions/${activeModelId}`);
    return response.data;
  },
  
  // Alle alten Logs löschen (alert_evaluations + predictions + model_predictions)
  deleteOldLogs: async (activeModelId: number): Promise<{ success: boolean; deleted_alert_evaluations: number; deleted_predictions: number; deleted_model_predictions: number; total_deleted: number }> => {
    const response = await apiClient.delete(`/admin/delete-old-logs/${activeModelId}`);
    return response.data;
  }
};

export const alertsApi = {
  // Alerts für ein Modell abrufen
  getForModel: async (
    activeModelId: number,
    limit: number = 100,
    offset: number = 0,
    filters?: {
      status?: 'pending' | 'success' | 'failed' | 'expired';
      coinId?: string;
      predictionType?: 'time_based' | 'classic';
      dateFrom?: string;
      dateTo?: string;
      includeNonAlerts?: boolean;  // NEU: Auch Vorhersagen unter Threshold anzeigen
    }
  ): Promise<AlertsResponse> => {
    const params = new URLSearchParams({
      active_model_id: activeModelId.toString(),
      limit: limit.toString(),
      offset: offset.toString(),
      unique_coins: 'false'
    });

    if (filters?.status) {
      params.append('status', filters.status);
    }
    if (filters?.coinId) {
      params.append('coin_id', filters.coinId);
    }
    if (filters?.predictionType) {
      params.append('prediction_type', filters.predictionType);
    }
    if (filters?.includeNonAlerts) {
      params.append('include_non_alerts', 'true');
    }
    if (filters?.dateFrom) {
      params.append('date_from', filters.dateFrom);
    }
    if (filters?.dateTo) {
      params.append('date_to', filters.dateTo);
    }

    const response: AxiosResponse<AlertsResponse> = await apiClient.get(
      `/alerts?${params.toString()}`
    );
    return response.data;
  },

  // Alert-Statistiken für ein Modell abrufen
  getStatistics: async (
    modelId?: number,
    activeModelId?: number,  // NEU: Unterstützung für active_model_id
    dateFrom?: string,
    dateTo?: string
  ): Promise<AlertStatistics> => {
    const params = new URLSearchParams();
    if (activeModelId) {
      params.append('active_model_id', activeModelId.toString());
    } else if (modelId) {
      params.append('model_id', modelId.toString());
    }
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    
    const response: AxiosResponse<AlertStatistics> = await apiClient.get(
      `/alerts/statistics?${params.toString()}`
    );
    return response.data;
  },

  // Einzelnen Alert abrufen
  getById: async (alertId: number) => {
    const response = await apiClient.get(`/alerts/${alertId}`);
    return response.data;
  },

  // Alle Alerts für ein Modell löschen (Reset)
  deleteForModel: async (activeModelId: number): Promise<{ success: boolean; deleted_alerts: number }> => {
    const response = await apiClient.delete(`/models/${activeModelId}/alerts`);
    return response.data;
  }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export const apiUtils = {
  // URL für direkten Zugriff auf Modelle
  getModelUrl: (id: number) => `${API_BASE_URL}/models/${id}`,

  // URL für direkten Zugriff auf Predictions
  getPredictionsUrl: (modelId: number) => `${API_BASE_URL}/predictions/model/${modelId}`,

  // Error-Handling Helper
  isApiError: (error: any): error is ApiError => {
    return error && typeof error.detail === 'string';
  }
};

export default apiClient;
