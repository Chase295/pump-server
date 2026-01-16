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
  IconButton,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Switch,
  FormControlLabel,
  Tooltip
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Cancel as FailedIcon,
  HourglassEmpty as WaitIcon,
  TrendingUp as UpIcon,
  TrendingDown as DownIcon,
  FilterList as FilterIcon,
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
  const id = Number(modelId);
  const [page, setPage] = React.useState(1);
  const [showAll, setShowAll] = React.useState(false); // Option: Alle Einträge anzeigen
  const queryClient = useQueryClient();
  
  // Filter-State
  // WICHTIG: predictionStatus wird NUR Frontend-seitig gefiltert (nicht an Backend gesendet)
  // includeNonAlerts ist immer true (wird nicht mehr als Filter-State gespeichert)
  const [filters, setFilters] = React.useState<{
    status?: 'pending' | 'success' | 'failed' | 'expired';
    predictionStatus?: 'negativ' | 'positiv' | 'alert';  // NUR Frontend-Filter (blendet nur aus)
    coinId?: string;
    predictionType?: 'time_based' | 'classic';
    dateFrom?: string;
    dateTo?: string;
  }>({});
  const [filtersExpanded, setFiltersExpanded] = React.useState(false);
  
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
    queryKey: ['model-predictions', 'model', id, page, showAll, filters.status, filters.predictionStatus, filters.coinId],
    queryFn: () => {
      // Wenn "Alle anzeigen" aktiviert, lade alle Einträge (limit = 10000)
      const limit = showAll ? 10000 : ITEMS_PER_PAGE;
      const offset = showAll ? 0 : (page - 1) * ITEMS_PER_PAGE;
      return modelPredictionsApi.getForModel(id, limit, offset, {
        tag: filters.predictionStatus,  // 'negativ' | 'positiv' | 'alert'
        status: filters.status ? (filters.status === 'pending' ? 'aktiv' : 'inaktiv') : undefined,  // Map old status to new
        coinId: filters.coinId
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
    const status = alert.status;
    
    // Normalisiere Status (kann String oder undefined sein)
    const normalizedStatus = status?.toString().toLowerCase() || '';
    
    // Wenn bereits evaluiert (success/failed), zeige das Ergebnis
    if (normalizedStatus === 'success') {
      return {
        label: 'Success',
        color: 'success',
        icon: <SuccessIcon fontSize="small" />
      };
    } else if (normalizedStatus === 'failed') {
      return {
        label: 'Failed',
        color: 'error',
        icon: <FailedIcon fontSize="small" />
      };
    } else if (normalizedStatus === 'expired') {
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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            📋 Alert-Logs: {modelName}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
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

        {/* Filter-Section */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: filtersExpanded ? 2 : 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <FilterIcon />
                <Typography variant="h6">Filter</Typography>
                {hasActiveFilters && (
                  <Chip
                    label={`${Object.keys(filters).length} aktiv`}
                    size="small"
                    color="primary"
                  />
                )}
              </Box>
              <Box>
                {hasActiveFilters && (
                  <Button
                    size="small"
                    startIcon={<ClearIcon />}
                    onClick={handleClearFilters}
                    sx={{ mr: 1 }}
                  >
                    Filter zurücksetzen
                  </Button>
                )}
                <IconButton
                  onClick={() => setFiltersExpanded(!filtersExpanded)}
                  size="small"
                >
                  <FilterIcon />
                </IconButton>
              </Box>
            </Box>

            <Collapse in={filtersExpanded}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr',
                    sm: 'repeat(2, 1fr)',
                    md: 'repeat(3, 1fr)'
                  },
                  gap: 2
                }}
              >
                <FormControl fullWidth size="small">
                  <InputLabel>Auswertungs-Status</InputLabel>
                  <Select
                    value={filters.status || ''}
                    label="Auswertungs-Status"
                    onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
                  >
                    <MenuItem value="">Alle</MenuItem>
                    <MenuItem value="pending">Wait</MenuItem>
                    <MenuItem value="success">Success</MenuItem>
                    <MenuItem value="failed">Failed</MenuItem>
                    <MenuItem value="expired">Expired</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small">
                  <InputLabel>Vorhersage-Status</InputLabel>
                  <Select
                    value={filters.predictionStatus || ''}
                    label="Vorhersage-Status"
                    onChange={(e) => handleFilterChange('predictionStatus', e.target.value || undefined)}
                  >
                    <MenuItem value="">Alle</MenuItem>
                    <MenuItem value="negativ">Negativ (&lt;50%)</MenuItem>
                    <MenuItem value="positiv">Positiv (≥50%)</MenuItem>
                    <MenuItem value="alert">Alert (≥{((model?.alert_threshold || 0.7) * 100).toFixed(0)}%)</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small">
                  <InputLabel>Vorhersage-Typ</InputLabel>
                  <Select
                    value={filters.predictionType || ''}
                    label="Vorhersage-Typ"
                    onChange={(e) => handleFilterChange('predictionType', e.target.value || undefined)}
                  >
                    <MenuItem value="">Alle</MenuItem>
                    <MenuItem value="time_based">Zeitbasiert</MenuItem>
                    <MenuItem value="classic">Klassisch</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  fullWidth
                  size="small"
                  label="Coin-ID"
                  value={filters.coinId || ''}
                  onChange={(e) => handleFilterChange('coinId', e.target.value || undefined)}
                  placeholder="z.B. F8t3Wmk9..."
                />

                <TextField
                  fullWidth
                  size="small"
                  label="Von Datum"
                  type="datetime-local"
                  value={filters.dateFrom || ''}
                  onChange={(e) => handleFilterChange('dateFrom', e.target.value || undefined)}
                  InputLabelProps={{ shrink: true }}
                />

                <TextField
                  fullWidth
                  size="small"
                  label="Bis Datum"
                  type="datetime-local"
                  value={filters.dateTo || ''}
                  onChange={(e) => handleFilterChange('dateTo', e.target.value || undefined)}
                  InputLabelProps={{ shrink: true }}
                />
              </Box>
              
              {/* Info: Alle Vorhersagen werden geladen */}
              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={true}
                      disabled={true}
                      color="primary"
                    />
                  }
                  label="Alle Vorhersagen werden geladen (Alerts + Non-Alerts)"
                />
              </Box>
            </Collapse>
          </CardContent>
        </Card>

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
                <Typography variant="h4" color="primary">
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
                <Typography variant="h4" color="success.main">
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
                <Typography variant="h4" color="warning.main">
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
                <Typography variant="h4" color="success.main">
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
                <Typography variant="h4" color="error.main">
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
                <Typography variant="h4" color="default">
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
                  <Typography variant="h4" color="info.main">
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
                <Typography variant="h4" color="success.main">
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
                <Typography variant="h4" color="error.main">
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
                <Typography variant="h4" color="default">
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
                <Typography variant="h4" color="info.main">
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
                <Typography variant="h4" color={stats.totalPerformancePct >= 0 ? 'success.main' : 'error.main'}>
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
                <Typography variant="h4" color="success.main">
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
                <Typography variant="h4" color="error.main">
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

      {/* Alerts Tabelle */}
      {alerts.length === 0 ? (
        <Alert severity="info">
          Es sind keine Alerts für dieses Modell verfügbar.
        </Alert>
      ) : (
        <>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
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
