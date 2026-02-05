/**
 * Model Logs Page
 * Zeigt die Alert-Auswertungen für ein spezifisches Modell
 */
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  Button,
  Breadcrumbs,
  Link as MuiLink,
  Paper,
  Pagination,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Switch,
  FormControlLabel,
  Tooltip,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Cancel as FailedIcon,
  HourglassEmpty as WaitIcon,
  TrendingUp as UpIcon,
  TrendingDown as DownIcon,
  Clear as ClearIcon,
  Delete as DeleteIcon,
  OpenInNew as OpenIcon
} from '@mui/icons-material';

import PageContainer from '../components/layout/PageContainer';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { modelsApi, modelPredictionsApi, alertsApi } from '../services/api';
import type { AlertEvaluation } from '../types/model';

const ITEMS_PER_PAGE = 50;

const ModelLogs: React.FC = () => {
  const { modelId } = useParams<{ modelId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const id = Number(modelId);
  const [page, setPage] = React.useState(1);
  const [showAll, setShowAll] = React.useState(false); // Option: Alle Einträge anzeigen
  const queryClient = useQueryClient();
  
  // Erweiterter Filter-State für alle neuen Filter-Optionen
  const [filters, setFilters] = React.useState<{
    // Coin ID
    coinId?: string;
    // Wahrscheinlichkeit
    probabilityOperator?: '>' | '<' | '=';
    probabilityValue?: number;
    // Vorhersage-Status (Mehrfachauswahl)
    predictionStatuses?: ('negativ' | 'positiv' | 'alert')[];
    // Auswertung (Mehrfachauswahl)
    evaluationStatuses?: ('success' | 'failed' | 'wait')[];
    // ATH Highest
    athHighestOperator?: '>' | '<' | '=';
    athHighestValue?: number;
    // ATH Lowest
    athLowestOperator?: '>' | '<' | '=';
    athLowestValue?: number;
    // Tatsächliche Änderung
    actualChangeOperator?: '>' | '<' | '=';
    actualChangeValue?: number;
    // Alert-Zeit (von-bis)
    alertTimeFrom?: string;
    alertTimeTo?: string;
    // Auswertungs-Zeit (von-bis)
    evaluationTimeFrom?: string;
    evaluationTimeTo?: string;
  }>({});
  
  // Reset-Dialog State
  const [resetDialogOpen, setResetDialogOpen] = React.useState(false);
  
  // Snackbar State
  const [snackbar, setSnackbar] = React.useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

  // Modell-Daten laden
  const {
    data: model,
    isLoading: isLoadingModel,
    error: modelError
  } = useQuery({
    queryKey: ['model', id],
    queryFn: () => modelsApi.getById(id),
    enabled: !!id
  });

  // Predictions laden - NEUE EINFACHE API (model_predictions)
  const {
    data: predictionsData,
    isLoading: isLoadingAlerts,
    error: alertsError,
    refetch: refetchAlerts
  } = useQuery({
    queryKey: ['model-predictions', 'model', id, page, showAll,
      // Alle neuen Filter-Eigenschaften
      filters.coinId,
      filters.probabilityOperator, filters.probabilityValue,
      filters.predictionStatuses?.join(','),
      filters.evaluationStatuses?.join(','),
      filters.athHighestOperator, filters.athHighestValue,
      filters.athLowestOperator, filters.athLowestValue,
      filters.actualChangeOperator, filters.actualChangeValue,
      filters.alertTimeFrom, filters.alertTimeTo,
      filters.evaluationTimeFrom, filters.evaluationTimeTo
    ],
    queryFn: () => {
      // Wenn "Alle anzeigen" aktiviert, lade alle Einträge (limit = 10000)
      const limit = showAll ? 10000 : ITEMS_PER_PAGE;
      const offset = showAll ? 0 : (page - 1) * ITEMS_PER_PAGE;
      return modelPredictionsApi.getForModel(id, limit, offset, {
        // Neue erweiterte Filter
        coinId: filters.coinId,
        probabilityOperator: filters.probabilityOperator,
        probabilityValue: filters.probabilityValue,
        predictionStatuses: filters.predictionStatuses,
        evaluationStatuses: filters.evaluationStatuses,
        athHighestOperator: filters.athHighestOperator,
        athHighestValue: filters.athHighestValue,
        athLowestOperator: filters.athLowestOperator,
        athLowestValue: filters.athLowestValue,
        actualChangeOperator: filters.actualChangeOperator,
        actualChangeValue: filters.actualChangeValue,
        alertTimeFrom: filters.alertTimeFrom,
        alertTimeTo: filters.alertTimeTo,
        evaluationTimeFrom: filters.evaluationTimeFrom,
        evaluationTimeTo: filters.evaluationTimeTo
      });
    },
    enabled: !!id,
    refetchInterval: 30000 // Alle 30 Sekunden aktualisieren
  });

  // Statistiken für ALLE Einträge laden (nicht nur die aktuell angezeigten)
  const {
    data: statisticsData
  } = useQuery({
    queryKey: ['alert-statistics', 'model', id],
    queryFn: () => alertsApi.getStatistics(undefined, id), // Verwendet active_model_id (zweiter Parameter)
    enabled: !!id,
    refetchInterval: 30000 // Alle 30 Sekunden aktualisieren
  });

  const handleBack = () => {
    navigate('/overview');
  };

  const handleRefresh = async () => {
    // WICHTIG: Entferne Cache-Einträge komplett und lade neu
    queryClient.removeQueries({ queryKey: ['model-predictions', 'model', id] });
    queryClient.removeQueries({ queryKey: ['alert-statistics', 'model', id] });
    // Dann sofort neu laden
    await refetchAlerts();
  };

  // Reset-Mutation (LÖSCHT ALLE ALTEN LOGS: alert_evaluations + predictions + model_predictions)
  const resetMutation = useMutation({
    mutationFn: () => modelPredictionsApi.deleteOldLogs(id),
    onSuccess: (data) => {
      // WICHTIG: Entferne ALLE Cache-Einträge komplett (nicht nur für dieses Modell)
      queryClient.removeQueries({ queryKey: ['model-predictions'] });
      queryClient.removeQueries({ queryKey: ['alert-statistics'] });
      queryClient.removeQueries({ queryKey: ['model', id] });
      
      // Warte kurz, damit der Cache wirklich geleert ist
      setTimeout(() => {
        // Dann sofort neu laden
        refetchAlerts();
      }, 100);
      
      setResetDialogOpen(false);
      setPage(1); // Zurück zur ersten Seite
      
      // Zeige Erfolgsmeldung
      setSnackbar({
        open: true,
        message: `${data.total_deleted} Einträge erfolgreich gelöscht (Predictions: ${data.deleted_model_predictions}, Alerts: ${data.deleted_alert_evaluations}). Die Seite wird aktualisiert.`,
        severity: 'success'
      });
    },
    onError: (error: any) => {
      console.error('Fehler beim Zurücksetzen der Logs:', error);
      setSnackbar({
        open: true,
        message: `Fehler beim Zurücksetzen der Logs: ${error?.response?.data?.detail || error.message || 'Unbekannter Fehler'}`,
        severity: 'error'
      });
    }
  });

  const handleResetClick = () => {
    setResetDialogOpen(true);
  };

  const handleResetConfirm = () => {
    resetMutation.mutate();
  };

  const handleResetCancel = () => {
    setResetDialogOpen(false);
  };

  const handleFilterChange = (key: keyof typeof filters, value: any) => {
    setFilters(prev => {
      const newFilters = { ...prev };
      if (value === '' || value === null || value === undefined) {
        delete newFilters[key];
      } else {
        newFilters[key] = value;
      }
      return newFilters;
    });
    setPage(1); // Zurück zur ersten Seite bei Filteränderung
  };

  const handleClearFilters = () => {
    setFilters({});
    setPage(1);
  };

  const hasActiveFilters = Object.keys(filters).length > 0;

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('de-DE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  const formatPercentage = (value?: number | null) => {
    if (value === undefined || value === null) return 'N/A';
    return `${value.toFixed(2)}%`;
  };

  // Status: Tag wird bereits vom Backend berechnet (negativ/positiv/alert)
  const getAlertStatus = (prediction: any): { label: string; color: 'success' | 'warning' | 'error' | 'default' } => {
    const tag = prediction.tag || 'negativ';
    
    if (tag === 'alert') {
      return { label: 'Alert', color: 'warning' }; // Orange/Gelb für Alerts
    } else if (tag === 'positiv') {
      return { label: 'Positiv', color: 'success' }; // Grün für Positiv
    } else {
      return { label: 'Negativ', color: 'error' }; // Rot für Negativ
    }
  };

  // Auswertung: pending/wait, success, failed
  // WICHTIG: 'non_alert' Einträge werden auch evaluiert (mit ATH-Tracking)!
  const getEvaluationStatus = (alert: AlertEvaluation): { label: string; color: 'default' | 'success' | 'error' | 'warning'; icon?: React.ReactElement } => {
    // Priorität 1: evaluation_result (success/failed)
    if (alert.evaluation_result === 'success') {
      return {
        label: 'Success',
        color: 'success',
        icon: <SuccessIcon fontSize="small" />
      };
    } else if (alert.evaluation_result === 'failed') {
      return {
        label: 'Failed',
        color: 'error',
        icon: <FailedIcon fontSize="small" />
      };
    }

    // Priorität 2: status Feld (aktiv/inaktiv)
    const status = alert.status;
    const normalizedStatus = status?.toString().toLowerCase() || '';

    if (normalizedStatus === 'expired') {
      return {
        label: 'Expired',
        color: 'warning',
        icon: <WaitIcon fontSize="small" />
      };
    }

    // 'non_alert' oder 'pending': Prüfe ob evaluation_timestamp erreicht wurde
    // WICHTIG: Alle nicht-evaluierten Einträge zeigen "Wait"
    if (normalizedStatus === 'non_alert' || normalizedStatus === 'pending' || !normalizedStatus) {
      const evalTimestamp = alert.evaluation_timestamp ? new Date(alert.evaluation_timestamp) : null;
      const now = new Date();
      
      if (evalTimestamp && evalTimestamp <= now) {
        // Sollte bereits evaluiert sein, aber noch nicht - zeige als "Wait" (wird evaluiert)
        return {
          label: 'Wait',
          color: 'warning',
          icon: <WaitIcon fontSize="small" />
        };
      } else {
        // Noch nicht evaluierbar (Zeit noch nicht erreicht)
        return {
          label: 'Wait',
          color: 'default',
          icon: <WaitIcon fontSize="small" />
        };
      }
    }
    
    // Fallback: Wenn Status unbekannt, aber evaluation_timestamp vorhanden → "Wait"
    if (alert.evaluation_timestamp) {
      return {
        label: 'Wait',
        color: 'default',
        icon: <WaitIcon fontSize="small" />
      };
    }
    
    // Letzter Fallback für wirklich unbekannte Status
    return {
      label: 'Wait',
      color: 'default',
      icon: <WaitIcon fontSize="small" />
    };
  };

  // ATH Highest formatieren
  const formatATHHighest = (prediction: any): { text: string; color: string; icon?: React.ReactNode } => {
    const change = prediction.ath_highest_pct;
    
    if (change === undefined || change === null) {
      return { text: 'N/A', color: 'text.secondary' };
    }
    
    const isPositive = change > 0;
    const formatted = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    
    return {
      text: formatted,
      color: isPositive ? 'success.main' : 'error.main',
      icon: isPositive ? <UpIcon fontSize="small" /> : <DownIcon fontSize="small" />
    };
  };

  // ATH Lowest formatieren
  const formatATHLowest = (prediction: any): { text: string; color: string; icon?: React.ReactNode } => {
    const change = prediction.ath_lowest_pct;
    
    if (change === undefined || change === null) {
      return { text: 'N/A', color: 'text.secondary' };
    }
    
    const formatted = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    
    // 0% oder positiv = gut (kein Verlust) → grün
    // Negativ = schlecht (Verlust) → rot
    const isGood = change >= 0;
    
    return {
      text: formatted,
      color: isGood ? 'success.main' : 'error.main',
      icon: isGood ? <UpIcon fontSize="small" /> : <DownIcon fontSize="small" />
    };
  };

  // Tatsächliche Änderung formatieren (zum evaluation_timestamp)
  const formatActualChange = (prediction: any): { text: string; color: string; icon?: React.ReactNode } => {
    const actualChange = prediction.actual_price_change_pct;
    
    if (actualChange === undefined || actualChange === null) {
      return { text: 'N/A', color: 'text.secondary' };
    }
    
    const isPositive = actualChange > 0;
    
    return {
      text: `${isPositive ? '+' : ''}${actualChange.toFixed(2)}%`,
      color: isPositive ? 'success.main' : 'error.main',
      icon: isPositive ? <UpIcon fontSize="small" /> : <DownIcon fontSize="small" />
    };
  };

  if (isLoadingModel || isLoadingAlerts) {
    return <LoadingSpinner message="Alert-Logs werden geladen..." />;
  }

  if (modelError || alertsError) {
    return (
      <PageContainer>
        <Alert severity="error" sx={{ mb: 3 }}>
          Fehler beim Laden der Alert-Logs: {modelError?.message || alertsError?.message || 'Unbekannter Fehler'}
        </Alert>
        <Alert severity="info" sx={{ mb: 3 }}>
          Debug: ID={id}, Model={model ? 'geladen' : 'nicht geladen'}, PredictionsData={predictionsData ? `${predictionsData.predictions?.length || 0} Predictions` : 'keine Daten'}
        </Alert>
        <Button startIcon={<BackIcon />} onClick={handleBack}>
          Zurück zur Übersicht
        </Button>
      </PageContainer>
    );
  }

  // NEUE API: predictionsData enthält bereits gefilterte Daten
  const allPredictions = predictionsData?.predictions || [];
  
  // Keine zusätzliche Filterung nötig - Backend filtert bereits nach tag und status
  const alerts = allPredictions;
  
  // Total-Alerts: Wenn gefiltert, verwende gefilterte Anzahl, sonst Gesamtanzahl aus Backend
  // WICHTIG: Backend liefert IMMER die Gesamtanzahl aller Vorhersagen (unabhängig von predictionStatus-Filter)
  const totalAlerts = predictionsData?.total || 0;
  
  // Debug-Info
  if (alerts.length === 0 && !isLoadingAlerts) {
    console.log('ModelLogs Debug:', {
      id,
      model,
      predictionsData,
      alertsError,
      modelError
    });
  }
  const totalPages = Math.ceil(totalAlerts / ITEMS_PER_PAGE);
  const modelName = model?.custom_name || model?.name || `Modell ${id}`;

  // Statistiken: Verwende API-Statistiken (ALLE Einträge) statt nur geladene
  const stats = statisticsData ? {
    total: statisticsData.total_alerts || totalAlerts,
    pending: (statisticsData.alerts_pending || 0) + (statisticsData.non_alerts_pending || 0),
    success: (statisticsData.alerts_success || 0) + (statisticsData.non_alerts_success || 0),
    failed: (statisticsData.alerts_failed || 0) + (statisticsData.non_alerts_failed || 0),
    expired: statisticsData.expired || 0,
    alert: statisticsData.alerts_above_threshold || 0,
    nonAlert: statisticsData.non_alerts_count || 0,
    alertsSuccess: statisticsData.alerts_success || 0,
    alertsFailed: statisticsData.alerts_failed || 0,
    alertsPending: statisticsData.alerts_pending || 0,
    nonAlertsSuccess: statisticsData.non_alerts_success || 0,
    nonAlertsFailed: statisticsData.non_alerts_failed || 0,
    nonAlertsPending: statisticsData.non_alerts_pending || 0,
    alertsSuccessRate: statisticsData.alerts_success_rate || 0,
    nonAlertsSuccessRate: statisticsData.non_alerts_success_rate || 0,
    totalPerformancePct: statisticsData.total_performance_pct || 0,
    alertsProfitPct: statisticsData.alerts_profit_pct || 0,
    alertsLossPct: statisticsData.alerts_loss_pct || 0
  } : {
    // Fallback: Berechne aus geladenen Einträgen (wenn API noch lädt)
    total: totalAlerts,
    pending: alerts.filter(a => a.status === 'aktiv').length,
    success: alerts.filter(a => a.evaluation_result === 'success').length,
    failed: alerts.filter(a => a.evaluation_result === 'failed').length,
    expired: 0,
    alert: alerts.filter(a => a.tag === 'alert').length,
    nonAlert: alerts.filter(a => a.tag !== 'alert').length,
    alertsSuccess: alerts.filter(a => a.tag === 'alert' && a.evaluation_result === 'success').length,
    alertsFailed: alerts.filter(a => a.tag === 'alert' && a.evaluation_result === 'failed').length,
    alertsPending: alerts.filter(a => a.tag === 'alert' && a.status === 'aktiv').length,
    nonAlertsSuccess: alerts.filter(a => a.tag !== 'alert' && a.evaluation_result === 'success').length,
    nonAlertsFailed: alerts.filter(a => a.tag !== 'alert' && a.evaluation_result === 'failed').length,
    nonAlertsPending: alerts.filter(a => a.tag !== 'alert' && a.status === 'aktiv').length,
    alertsSuccessRate: 0,
    nonAlertsSuccessRate: 0,
    totalPerformancePct: 0,
    alertsProfitPct: 0,
    alertsLossPct: 0
  };


  return (
    <PageContainer>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <MuiLink
          component="button"
          variant="body2"
          onClick={() => navigate('/overview')}
          sx={{ cursor: 'pointer' }}
        >
          Übersicht
        </MuiLink>
        <MuiLink
          component="button"
          variant="body2"
          onClick={() => navigate(`/model/${id}`)}
          sx={{ cursor: 'pointer' }}
        >
          {modelName}
        </MuiLink>
        <Typography color="text.primary">Alert-Logs</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: { xs: 1, sm: 0 }, mb: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, fontSize: { xs: '1.3rem', sm: '2.125rem' } }}>
            📋 Alert-Logs: {modelName}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap', width: { xs: '100%', sm: 'auto' } }}>
            <Tooltip title={showAll ? "Zeigt alle Einträge (bis zu 10.000)" : "Zeigt 50 Einträge pro Seite"}>
              <FormControlLabel
                control={
                  <Switch
                    checked={showAll}
                    onChange={(e) => {
                      setShowAll(e.target.checked);
                      setPage(1); // Zurück zur ersten Seite
                    }}
                    size="small"
                  />
                }
                label="Alle anzeigen"
                sx={{ mr: 1 }}
              />
            </Tooltip>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleResetClick}
              disabled={resetMutation.isPending || totalAlerts === 0}
              size="small"
            >
              Reset
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={isLoadingAlerts}
              size="small"
            >
              {isLoadingAlerts ? 'Aktualisiere...' : 'Aktualisieren'}
            </Button>
          </Box>
        </Box>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Detaillierte Historie der Alert-Auswertungen für Modell {modelName}.
        </Typography>


        {/* Erweiterte Statistiken */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Übersicht
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(3, 1fr)'
              },
              gap: 2,
              mb: 3
            }}
          >
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Gesamt
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Alle Vorhersagen des Modells
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.alert}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Alerts (≥{((model?.alert_threshold || 0.7) * 100).toFixed(0)}%)
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Vorhersagen über dem Alert-Threshold
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.nonAlert}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Nicht-Alerts
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Vorhersagen unter dem Alert-Threshold
                </Typography>
              </CardContent>
            </Card>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>
            Alerts-Details (≥{((model?.alert_threshold || 0.7) * 100).toFixed(0)}%)
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(4, 1fr)'
              },
              gap: 2,
              mb: 3
            }}
          >
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.alertsSuccess}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Alerts: Success
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Alerts, die erfolgreich waren
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.alertsFailed}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Alerts: Failed
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Alerts, die fehlgeschlagen sind
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="default" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.alertsPending}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Alerts: Wait
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Alerts, die noch ausstehen
                </Typography>
              </CardContent>
            </Card>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="info.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                    {stats.alertsSuccess + stats.alertsFailed > 0
                      ? `${stats.alertsSuccessRate.toFixed(1)}%`
                      : 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Alerts Success-Rate
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    {stats.alertsPending > 0 
                      ? `Erfolgsquote (${stats.alertsSuccess + stats.alertsFailed} ausgewertet, ${stats.alertsPending} ausstehend)`
                      : 'Erfolgsquote der ausgewerteten Alerts'}
                  </Typography>
                </CardContent>
              </Card>
          </Box>

          <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>
            Nicht-Alerts-Details (&lt;{((model?.alert_threshold || 0.7) * 100).toFixed(0)}%)
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(4, 1fr)'
              },
              gap: 2,
              mb: 3
            }}
          >
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.nonAlertsSuccess}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Nicht-Alerts: Success
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Richtig als "nicht Alert" erkannt
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.nonAlertsFailed}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Nicht-Alerts: Failed
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Übersehener Gewinn (falsch negativ)
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="default" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.nonAlertsPending}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Nicht-Alerts: Wait
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Nicht-Alerts, die noch ausstehen
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="info.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.nonAlertsSuccess + stats.nonAlertsFailed > 0
                    ? `${stats.nonAlertsSuccessRate.toFixed(1)}%`
                    : '0%'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Nicht-Alerts Success-Rate
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Erfolgsquote der Nicht-Alerts
                </Typography>
              </CardContent>
            </Card>
          </Box>
          
          {/* Performance-Summen */}
          <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>
            Performance-Summen (Tatsächliche Änderungen)
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(3, 1fr)'
              },
              gap: 2,
              mb: 3
            }}
          >
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color={stats.totalPerformancePct >= 0 ? 'success.main' : 'error.main'} sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.totalPerformancePct >= 0 ? '+' : ''}{stats.totalPerformancePct.toFixed(2)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Gesamt-Performance
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Summe aller tatsächlichen Änderungen (Gewinne + Verluste)
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  +{stats.alertsProfitPct.toFixed(2)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Gewinn-Summe
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Summe aller tatsächlichen Änderungen für Success-Alerts
                </Typography>
              </CardContent>
            </Card>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
                  {stats.alertsLossPct.toFixed(2)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Verlust-Summe
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  Summe aller tatsächlichen Änderungen für Failed-Alerts
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Box>

      {/* Filter Card */}
      <Card sx={{ mb: 2, boxShadow: 2 }}>
        <CardContent sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              <Typography variant="h6" color="primary.main" sx={{ fontWeight: 'bold' }}>
                🔍 Filter
              </Typography>
              {hasActiveFilters && (
                <Typography variant="caption" color="text.secondary">
                  {totalAlerts} Coins entsprechen den aktiven Filtern
                </Typography>
              )}
            </Box>
            {hasActiveFilters && (
              <Button
                size="small"
                variant="outlined"
                color="secondary"
                startIcon={<ClearIcon />}
                onClick={handleClearFilters}
              >
                Zurücksetzen
              </Button>
            )}
          </Box>

          {/* Filter Sections - Mehrere Zeilen für bessere Übersichtlichkeit */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>

            {/* Zeile 1: Basis-Filter */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'end' }}>
              <TextField
                size="small"
                label="Coin ID"
                value={filters.coinId || ''}
                onChange={(e) => handleFilterChange('coinId', e.target.value || undefined)}
                placeholder="z.B. F8t3Wmk9..."
                sx={{ minWidth: { xs: '100%', sm: 200 } }}
              />

              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Vorhersage-Status</InputLabel>
                <Select
                  multiple
                  value={filters.predictionStatuses || []}
                  label="Vorhersage-Status"
                  onChange={(e) => handleFilterChange('predictionStatuses', e.target.value as ('negativ' | 'positiv' | 'alert')[])}
                  renderValue={(selected) => (selected as string[]).join(', ')}
                >
                  <MenuItem value="negativ">Negativ</MenuItem>
                  <MenuItem value="positiv">Positiv</MenuItem>
                  <MenuItem value="alert">Alert</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Auswertung</InputLabel>
                <Select
                  multiple
                  value={filters.evaluationStatuses || []}
                  label="Auswertung"
                  onChange={(e) => handleFilterChange('evaluationStatuses', e.target.value as ('success' | 'failed' | 'wait')[])}
                  renderValue={(selected) => (selected as string[]).join(', ')}
                >
                  <MenuItem value="success">Success</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="wait">Wait</MenuItem>
                </Select>
              </FormControl>
            </Box>

            {/* Zeile 2: Wahrscheinlichkeit & Tatsächliche Änderung */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'end' }}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'end' }}>
                <FormControl size="small" sx={{ minWidth: 80 }}>
                  <InputLabel>Operator</InputLabel>
                  <Select
                    value={filters.probabilityOperator || ''}
                    label="Operator"
                    onChange={(e) => handleFilterChange('probabilityOperator', e.target.value || undefined)}
                  >
                    <MenuItem value="">-</MenuItem>
                    <MenuItem value=">">&gt;</MenuItem>
                    <MenuItem value="<">&lt;</MenuItem>
                    <MenuItem value="=">=</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  size="small"
                  type="number"
                  label="Wahrscheinlichkeit"
                  value={filters.probabilityValue || ''}
                  onChange={(e) => handleFilterChange('probabilityValue', e.target.value ? parseFloat(e.target.value) : undefined)}
                  sx={{ minWidth: 120 }}
                />
              </Box>

              <Box sx={{ display: 'flex', gap: 1, alignItems: 'end' }}>
                <FormControl size="small" sx={{ minWidth: 80 }}>
                  <InputLabel>Operator</InputLabel>
                  <Select
                    value={filters.actualChangeOperator || ''}
                    label="Operator"
                    onChange={(e) => handleFilterChange('actualChangeOperator', e.target.value || undefined)}
                  >
                    <MenuItem value="">-</MenuItem>
                    <MenuItem value=">">&gt;</MenuItem>
                    <MenuItem value="<">&lt;</MenuItem>
                    <MenuItem value="=">=</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  size="small"
                  type="number"
                  label="Tatsächliche Änderung %"
                  value={filters.actualChangeValue || ''}
                  onChange={(e) => handleFilterChange('actualChangeValue', e.target.value ? parseFloat(e.target.value) : undefined)}
                  sx={{ minWidth: 120 }}
                />
              </Box>
            </Box>

            {/* Zeile 3: ATH Werte */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'end' }}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'end' }}>
                <FormControl size="small" sx={{ minWidth: 80 }}>
                  <InputLabel>Operator</InputLabel>
                  <Select
                    value={filters.athHighestOperator || ''}
                    label="Operator"
                    onChange={(e) => handleFilterChange('athHighestOperator', e.target.value || undefined)}
                  >
                    <MenuItem value="">-</MenuItem>
                    <MenuItem value=">">&gt;</MenuItem>
                    <MenuItem value="<">&lt;</MenuItem>
                    <MenuItem value="=">=</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  size="small"
                  type="number"
                  label="ATH Highest %"
                  value={filters.athHighestValue || ''}
                  onChange={(e) => handleFilterChange('athHighestValue', e.target.value ? parseFloat(e.target.value) : undefined)}
                  sx={{ minWidth: 120 }}
                />
              </Box>

              <Box sx={{ display: 'flex', gap: 1, alignItems: 'end' }}>
                <FormControl size="small" sx={{ minWidth: 80 }}>
                  <InputLabel>Operator</InputLabel>
                  <Select
                    value={filters.athLowestOperator || ''}
                    label="Operator"
                    onChange={(e) => handleFilterChange('athLowestOperator', e.target.value || undefined)}
                  >
                    <MenuItem value="">-</MenuItem>
                    <MenuItem value=">">&gt;</MenuItem>
                    <MenuItem value="<">&lt;</MenuItem>
                    <MenuItem value="=">=</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  size="small"
                  type="number"
                  label="ATH Lowest %"
                  value={filters.athLowestValue || ''}
                  onChange={(e) => handleFilterChange('athLowestValue', e.target.value ? parseFloat(e.target.value) : undefined)}
                  sx={{ minWidth: 120 }}
                />
              </Box>
            </Box>

            {/* Zeile 4: Zeitbereiche */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'end' }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'end', width: { xs: '100%', sm: 'auto' } }}>
                <TextField
                  size="small"
                  type="datetime-local"
                  label="Alert-Zeit von"
                  value={filters.alertTimeFrom || ''}
                  onChange={(e) => handleFilterChange('alertTimeFrom', e.target.value || undefined)}
                  InputLabelProps={{ shrink: true }}
                  sx={{ width: { xs: '100%', sm: 'auto' } }}
                />
                <TextField
                  size="small"
                  type="datetime-local"
                  label="Alert-Zeit bis"
                  value={filters.alertTimeTo || ''}
                  onChange={(e) => handleFilterChange('alertTimeTo', e.target.value || undefined)}
                  InputLabelProps={{ shrink: true }}
                  sx={{ width: { xs: '100%', sm: 'auto' } }}
                />
              </Box>

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'end', width: { xs: '100%', sm: 'auto' } }}>
                <TextField
                  size="small"
                  type="datetime-local"
                  label="Auswertungs-Zeit von"
                  value={filters.evaluationTimeFrom || ''}
                  onChange={(e) => handleFilterChange('evaluationTimeFrom', e.target.value || undefined)}
                  InputLabelProps={{ shrink: true }}
                  sx={{ width: { xs: '100%', sm: 'auto' } }}
                />
                <TextField
                  size="small"
                  type="datetime-local"
                  label="Auswertungs-Zeit bis"
                  value={filters.evaluationTimeTo || ''}
                  onChange={(e) => handleFilterChange('evaluationTimeTo', e.target.value || undefined)}
                  InputLabelProps={{ shrink: true }}
                  sx={{ width: { xs: '100%', sm: 'auto' } }}
                />
              </Box>
            </Box>

          </Box>
        </CardContent>
      </Card>

      {/* Alerts Tabelle / Cards */}
      {alerts.length === 0 ? (
        <Alert severity="info">
          Es sind keine Alerts für dieses Modell verfügbar.
        </Alert>
      ) : (
        <>
          {/* Mobile: Card-Layout */}
          {isMobile ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 3 }}>
              {alerts.map((alert) => {
                const alertStatus = getAlertStatus(alert);
                const evalStatus = getEvaluationStatus(alert);
                const athHighest = formatATHHighest(alert);
                const athLowest = formatATHLowest(alert);
                const actualChange = formatActualChange(alert);
                return (
                  <Card
                    key={alert.id}
                    sx={{
                      cursor: 'pointer',
                      border: alertStatus.label === 'Alert'
                        ? '1px solid rgba(255, 152, 0, 0.4)'
                        : '1px solid rgba(255, 255, 255, 0.08)',
                      '&:active': { transform: 'scale(0.99)' }
                    }}
                    onClick={() => navigate(`/model/${id}/coin/${alert.coin_id}?prediction_id=${alert.id}`)}
                  >
                    <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                      {/* Zeile 1: Coin-ID + Status-Chips */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <OpenIcon sx={{ fontSize: 14, color: '#00d4ff' }} />
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#00d4ff', fontWeight: 600, fontSize: '0.8rem' }}>
                            {alert.coin_id && alert.coin_id.length > 0 ? `${alert.coin_id.substring(0, 12)}...` : '(Keine Coin-ID)'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Chip
                            label={alertStatus.label}
                            color={alertStatus.color}
                            size="small"
                            sx={{
                              fontWeight: 600,
                              height: 22,
                              fontSize: '0.7rem',
                              ...(alertStatus.label === 'Alert' && {
                                backgroundColor: '#ff9800',
                                color: '#fff',
                                fontWeight: 700,
                                border: '1px solid #f57c00',
                              })
                            }}
                          />
                          <Chip
                            {...(evalStatus.icon ? { icon: evalStatus.icon } : {})}
                            label={evalStatus.label}
                            color={evalStatus.color}
                            size="small"
                            sx={{ height: 22, fontSize: '0.7rem', '& .MuiChip-icon': { fontSize: 14 } }}
                          />
                        </Box>
                      </Box>

                      {/* Zeile 2: Wahrscheinlichkeit groß + Ziel */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', mb: 1.5 }}>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem', display: 'block', lineHeight: 1 }}>
                            Wahrscheinlichkeit
                          </Typography>
                          <Typography variant="h6" fontWeight={700} color="primary" sx={{ fontSize: '1.2rem', lineHeight: 1.3 }}>
                            {formatPercentage(alert.probability ? alert.probability * 100 : null)}
                          </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'right' }}>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem', display: 'block', lineHeight: 1 }}>
                            Ziel
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                            {alert.price_change_percent && alert.target_direction
                              ? `${alert.target_direction === 'up' ? '↑' : '↓'} ${formatPercentage(alert.price_change_percent)}`
                              : 'N/A'}
                          </Typography>
                        </Box>
                      </Box>

                      {/* Zeile 3: ATH Highest / ATH Lowest / Tatsächliche Änderung */}
                      <Box sx={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: 1,
                        mb: 1.5,
                        py: 1,
                        px: 1,
                        borderRadius: 1,
                        bgcolor: 'rgba(255, 255, 255, 0.03)'
                      }}>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block', lineHeight: 1, mb: 0.3 }}>
                            ATH High
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3, '& .MuiSvgIcon-root': { fontSize: 14 } }}>
                            {athHighest.icon}
                            <Typography variant="body2" color={athHighest.color} fontWeight={600} sx={{ fontSize: '0.8rem' }}>
                              {athHighest.text}
                            </Typography>
                          </Box>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block', lineHeight: 1, mb: 0.3 }}>
                            ATH Low
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3, '& .MuiSvgIcon-root': { fontSize: 14 } }}>
                            {athLowest.icon}
                            <Typography variant="body2" color={athLowest.color} fontWeight={600} sx={{ fontSize: '0.8rem' }}>
                              {athLowest.text}
                            </Typography>
                          </Box>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block', lineHeight: 1, mb: 0.3 }}>
                            Änderung
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3, '& .MuiSvgIcon-root': { fontSize: 14 } }}>
                            {actualChange.icon}
                            <Typography variant="body2" color={actualChange.color} fontWeight={600} sx={{ fontSize: '0.8rem' }}>
                              {actualChange.text}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>

                      {/* Zeile 4: Zeitstempel */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Alert:</Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                            {formatTimestamp(alert.prediction_timestamp)}
                          </Typography>
                        </Box>
                        {alert.evaluation_timestamp && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>Eval:</Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                              {formatTimestamp(alert.evaluation_timestamp)}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                );
              })}
            </Box>
          ) : (
          /* Desktop: Tabelle */
          <TableContainer component={Paper} sx={{ mb: 3, overflowX: 'auto' }}>
            <Table size="small" sx={{ minWidth: 900 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Coin ID</TableCell>
                  <TableCell>Wahrscheinlichkeit</TableCell>
                  <TableCell>Vorhersage-Status</TableCell>
                  <TableCell>Auswertung</TableCell>
                  <TableCell>ATH Highest</TableCell>
                  <TableCell>ATH Lowest</TableCell>
                  <TableCell>Tatsächliche Änderung</TableCell>
                  <TableCell>Ziel</TableCell>
                  <TableCell>Alert-Zeit</TableCell>
                  <TableCell>Auswertungs-Zeit</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {alerts.map((alert) => {
                  const alertStatus = getAlertStatus(alert);
                  const evalStatus = getEvaluationStatus(alert);
                  const athHighest = formatATHHighest(alert);
                  const athLowest = formatATHLowest(alert);
                  const actualChange = formatActualChange(alert);

                  return (
                    <TableRow key={alert.id} hover>
                      <TableCell>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => navigate(`/model/${id}/coin/${alert.coin_id}?prediction_id=${alert.id}`)}
                          startIcon={<OpenIcon />}
                          sx={{
                            fontFamily: 'monospace',
                            color: '#00d4ff',
                            borderColor: '#00d4ff',
                            textTransform: 'none',
                            fontWeight: 600,
                            '&:hover': {
                              backgroundColor: 'rgba(0, 212, 255, 0.2)',
                              borderColor: '#00d4ff',
                              color: '#00d4ff',
                            }
                          }}
                        >
                          {alert.coin_id && alert.coin_id.length > 0 ? `${alert.coin_id.substring(0, 12)}...` : '(Keine Coin-ID)'}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight={500} color="primary">
                          {formatPercentage(alert.probability ? alert.probability * 100 : null)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={alertStatus.label}
                          color={alertStatus.color}
                          size="small"
                          sx={{
                            fontWeight: 600,
                            minWidth: 80,
                            // Alerts besonders hervorheben mit Orange
                            ...(alertStatus.label === 'Alert' && {
                              backgroundColor: '#ff9800',
                              color: '#fff',
                              fontWeight: 700,
                              border: '2px solid #f57c00',
                              boxShadow: '0 2px 4px rgba(255, 152, 0, 0.3)',
                              '&:hover': {
                                backgroundColor: '#f57c00',
                                boxShadow: '0 4px 8px rgba(255, 152, 0, 0.5)'
                              }
                            })
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          {...(evalStatus.icon ? { icon: evalStatus.icon } : {})}
                          label={evalStatus.label}
                          color={evalStatus.color}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {athHighest.icon}
                          <Typography variant="body2" color={athHighest.color} fontWeight={500}>
                            {athHighest.text}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {athLowest.icon}
                          <Typography variant="body2" color={athLowest.color} fontWeight={500}>
                            {athLowest.text}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {actualChange.icon}
                          <Typography variant="body2" color={actualChange.color} fontWeight={500}>
                            {actualChange.text}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {alert.price_change_percent && alert.target_direction ? (
                          <Typography variant="body2" color="text.secondary">
                            {alert.target_direction === 'up' ? '↑' : '↓'} {formatPercentage(alert.price_change_percent)}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatTimestamp(alert.prediction_timestamp)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {alert.evaluation_timestamp ? formatTimestamp(alert.evaluation_timestamp) : 'N/A'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
          )}
          
          {/* Pagination - nur anzeigen wenn nicht "Alle anzeigen" aktiviert */}
          {!showAll && totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_event, value) => setPage(value)}
                color="primary"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </>
      )}

      {/* Reset-Dialog */}
      <Dialog
        open={resetDialogOpen}
        onClose={handleResetCancel}
        aria-labelledby="reset-dialog-title"
        aria-describedby="reset-dialog-description"
      >
        <DialogTitle id="reset-dialog-title">
          Logs zurücksetzen?
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="reset-dialog-description">
            Möchten Sie wirklich alle Alert-Logs für dieses Modell löschen? 
            Diese Aktion kann nicht rückgängig gemacht werden.
            <br /><br />
            <strong>Gelöscht werden:</strong>
            <br />• Alle Model-Predictions ({totalAlerts} Einträge)
            <br />• Alle Statistiken werden zurückgesetzt
            <br /><br />
            <strong>Nicht gelöscht werden:</strong>
            <br />• Die Modell-Konfiguration
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleResetCancel} disabled={resetMutation.isPending}>
            Abbrechen
          </Button>
          <Button 
            onClick={handleResetConfirm} 
            color="error" 
            variant="contained"
            disabled={resetMutation.isPending}
            startIcon={<DeleteIcon />}
          >
            {resetMutation.isPending ? 'Löschen...' : 'Ja, zurücksetzen'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar für Benachrichtigungen */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </PageContainer>
  );
};

export default ModelLogs;
