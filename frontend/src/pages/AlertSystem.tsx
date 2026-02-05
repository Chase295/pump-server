/**
 * AlertSystem Page
 * Übersicht über das Alert-System mit echten Statistiken pro Modell
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Alert,
  Chip,
  Button,
  LinearProgress
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Cancel as FailedIcon,
  HourglassEmpty as WaitIcon,
  TrendingUp as UpIcon,
  TrendingDown as DownIcon,
  OpenInNew as OpenIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

// Components
import PageContainer from '../components/layout/PageContainer';
import LoadingSpinner from '../components/common/LoadingSpinner';

// Services
import { modelsApi, alertsApi } from '../services/api';
import type { Model, AlertStatistics } from '../types/model';

const AlertSystem: React.FC = () => {
  const navigate = useNavigate();

  // Alle Modelle laden (inkl. inaktive)
  const { data: models, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['models', 'all'],
    queryFn: () => modelsApi.getAll()
  });

  // Alert-Statistiken pro Modell laden
  const { data: modelStats } = useQuery({
    queryKey: ['alert-stats-all', models?.map(m => m.id)],
    queryFn: async () => {
      if (!models || models.length === 0) return {};
      const statsMap: Record<number, AlertStatistics> = {};
      await Promise.all(
        models.map(async (model) => {
          try {
            const stats = await alertsApi.getStatistics(undefined, model.id);
            statsMap[model.id] = stats;
          } catch {
            // Ignore errors for individual models
          }
        })
      );
      return statsMap;
    },
    enabled: !!models && models.length > 0,
    refetchInterval: 30000
  });

  if (modelsLoading) {
    return <LoadingSpinner message="Alert-System wird geladen..." />;
  }

  if (modelsError) {
    return (
      <PageContainer>
        <Alert severity="error">
          Fehler beim Laden: {modelsError.message}
        </Alert>
      </PageContainer>
    );
  }

  // Aggregierte Statistiken berechnen
  const totalPredictions = models?.reduce((sum, m) => sum + (m.total_predictions || 0), 0) || 0;
  const totalAlerts = models?.reduce((sum, m) => sum + (m.positive_predictions || 0), 0) || 0;
  const totalSuccess = modelStats
    ? Object.values(modelStats).reduce((sum, s) => sum + (s.alerts_success || 0), 0)
    : 0;
  const totalFailed = modelStats
    ? Object.values(modelStats).reduce((sum, s) => sum + (s.alerts_failed || 0), 0)
    : 0;
  const totalPending = modelStats
    ? Object.values(modelStats).reduce((sum, s) => sum + (s.alerts_pending || 0), 0)
    : 0;
  const overallSuccessRate = (totalSuccess + totalFailed) > 0
    ? (totalSuccess / (totalSuccess + totalFailed) * 100)
    : 0;
  const totalProfit = modelStats
    ? Object.values(modelStats).reduce((sum, s) => sum + (s.alerts_profit_pct || 0), 0)
    : 0;
  const totalLoss = modelStats
    ? Object.values(modelStats).reduce((sum, s) => sum + (s.alerts_loss_pct || 0), 0)
    : 0;
  const netPerformance = totalProfit + totalLoss;
  const activeModelsCount = models?.filter(m => m.is_active).length || 0;

  const formatPct = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;

  return (
    <PageContainer>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, fontSize: { xs: '1.3rem', sm: '2.125rem' }, mb: 0.5 }}>
          Alert-System
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {activeModelsCount} aktive{activeModelsCount === 1 ? 's' : ''} Modell{activeModelsCount === 1 ? '' : 'e'} · {totalPredictions.toLocaleString('de-DE')} Vorhersagen · {totalAlerts.toLocaleString('de-DE')} Alerts
        </Typography>
      </Box>

      {/* Quick Stats */}
      <Box sx={{
        display: 'grid',
        gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(6, 1fr)' },
        gap: { xs: 1, sm: 2 },
        mb: 3
      }}>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: 1 }}>
            <Typography color="primary.main" sx={{ fontWeight: 700, fontSize: { xs: '1.3rem', sm: '1.75rem' } }}>
              {totalAlerts}
            </Typography>
            <Typography variant="caption" color="text.secondary">Alerts gesamt</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: 1 }}>
            <Typography color="success.main" sx={{ fontWeight: 700, fontSize: { xs: '1.3rem', sm: '1.75rem' } }}>
              {totalSuccess}
            </Typography>
            <Typography variant="caption" color="text.secondary">Success</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: 1 }}>
            <Typography color="error.main" sx={{ fontWeight: 700, fontSize: { xs: '1.3rem', sm: '1.75rem' } }}>
              {totalFailed}
            </Typography>
            <Typography variant="caption" color="text.secondary">Failed</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: 1 }}>
            <Typography color="warning.main" sx={{ fontWeight: 700, fontSize: { xs: '1.3rem', sm: '1.75rem' } }}>
              {totalPending}
            </Typography>
            <Typography variant="caption" color="text.secondary">Ausstehend</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: 1 }}>
            <Typography color="info.main" sx={{ fontWeight: 700, fontSize: { xs: '1.3rem', sm: '1.75rem' } }}>
              {overallSuccessRate.toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">Success-Rate</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: 1 }}>
            <Typography
              sx={{ fontWeight: 700, fontSize: { xs: '1.3rem', sm: '1.75rem' } }}
              color={netPerformance >= 0 ? 'success.main' : 'error.main'}
            >
              {formatPct(netPerformance)}
            </Typography>
            <Typography variant="caption" color="text.secondary">Netto-Profit</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Performance-Zusammenfassung */}
      {(totalProfit !== 0 || totalLoss !== 0) && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ py: { xs: 1.5, sm: 2 } }}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5 }}>
              Performance-Zusammenfassung
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: { xs: 2, sm: 4 }, alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <UpIcon sx={{ color: 'success.main', fontSize: 20 }} />
                <Typography variant="body2" color="success.main" fontWeight={600}>
                  Gewinne: {formatPct(totalProfit)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <DownIcon sx={{ color: 'error.main', fontSize: 20 }} />
                <Typography variant="body2" color="error.main" fontWeight={600}>
                  Verluste: {totalLoss.toFixed(1)}%
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="body2" fontWeight={700} color={netPerformance >= 0 ? 'success.main' : 'error.main'}>
                  = Netto: {formatPct(netPerformance)}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Modell-Karten */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
        Modelle ({models?.length || 0})
      </Typography>

      {!models || models.length === 0 ? (
        <Alert severity="info">Keine Modelle vorhanden.</Alert>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {models.map((model: Model) => {
            const stats = modelStats?.[model.id];
            const alerts = model.positive_predictions || 0;
            const mSuccess = stats?.alerts_success || 0;
            const mFailed = stats?.alerts_failed || 0;
            const mPending = stats?.alerts_pending || 0;
            const mRate = (mSuccess + mFailed) > 0 ? (mSuccess / (mSuccess + mFailed) * 100) : 0;
            const mProfit = stats?.alerts_profit_pct || 0;
            const mLoss = stats?.alerts_loss_pct || 0;
            const mNet = stats?.total_performance_pct || (mProfit + mLoss);
            const threshold = (model.alert_threshold || 0.7) * 100;

            return (
              <Card
                key={model.id}
                sx={{
                  border: model.is_active
                    ? '1px solid rgba(0, 212, 255, 0.2)'
                    : '1px solid rgba(255, 255, 255, 0.05)',
                  opacity: model.is_active ? 1 : 0.7
                }}
              >
                <CardContent sx={{ py: { xs: 2, sm: 2.5 }, px: { xs: 2, sm: 3 } }}>
                  {/* Modell-Header */}
                  <Box sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', sm: 'row' },
                    justifyContent: 'space-between',
                    alignItems: { xs: 'flex-start', sm: 'center' },
                    gap: 1,
                    mb: 2
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                      <Typography variant="h6" sx={{ fontWeight: 700, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                        {model.custom_name || model.name}
                      </Typography>
                      <Chip
                        label={model.is_active ? 'Aktiv' : 'Inaktiv'}
                        color={model.is_active ? 'success' : 'default'}
                        size="small"
                        sx={{ height: 22, fontSize: '0.7rem' }}
                      />
                      <Chip
                        label={`${threshold.toFixed(0)}% Threshold`}
                        variant="outlined"
                        size="small"
                        sx={{ height: 22, fontSize: '0.7rem' }}
                      />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<OpenIcon />}
                        onClick={() => navigate(`/model/${model.id}/logs`)}
                        sx={{ fontSize: '0.75rem', textTransform: 'none' }}
                      >
                        Logs
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<SettingsIcon />}
                        onClick={() => navigate(`/model/${model.id}/alert-config`)}
                        sx={{ fontSize: '0.75rem', textTransform: 'none' }}
                      >
                        Config
                      </Button>
                    </Box>
                  </Box>

                  {/* Statistik-Grid */}
                  <Box sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: 'repeat(3, 1fr)', sm: 'repeat(6, 1fr)' },
                    gap: { xs: 1, sm: 2 },
                    mb: 2
                  }}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="body1" color="primary" fontWeight={700} sx={{ fontSize: { xs: '1rem', sm: '1.2rem' } }}>
                        {(model.total_predictions || 0).toLocaleString('de-DE')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                        Vorhersagen
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="body1" color="warning.main" fontWeight={700} sx={{ fontSize: { xs: '1rem', sm: '1.2rem' } }}>
                        {alerts}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                        Alerts
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="body1" color="info.main" fontWeight={700} sx={{ fontSize: { xs: '1rem', sm: '1.2rem' } }}>
                        {mRate.toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                        Success-Rate
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.3 }}>
                        <SuccessIcon sx={{ fontSize: 14, color: 'success.main' }} />
                        <Typography variant="body1" color="success.main" fontWeight={700} sx={{ fontSize: { xs: '1rem', sm: '1.2rem' } }}>
                          {mSuccess}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                        Success
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.3 }}>
                        <FailedIcon sx={{ fontSize: 14, color: 'error.main' }} />
                        <Typography variant="body1" color="error.main" fontWeight={700} sx={{ fontSize: { xs: '1rem', sm: '1.2rem' } }}>
                          {mFailed}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                        Failed
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.3 }}>
                        <WaitIcon sx={{ fontSize: 14, color: 'warning.main' }} />
                        <Typography variant="body1" color="warning.main" fontWeight={700} sx={{ fontSize: { xs: '1rem', sm: '1.2rem' } }}>
                          {mPending}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                        Ausstehend
                      </Typography>
                    </Box>
                  </Box>

                  {/* Success-Rate Bar */}
                  {(mSuccess + mFailed) > 0 && (
                    <Box sx={{ mb: 1.5 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          Success-Rate: {mRate.toFixed(1)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {mSuccess} / {mSuccess + mFailed} ausgewertet
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={mRate}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          bgcolor: 'rgba(255, 255, 255, 0.08)',
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 3,
                            bgcolor: mRate >= 50 ? 'success.main' : mRate >= 25 ? 'warning.main' : 'error.main'
                          }
                        }}
                      />
                    </Box>
                  )}

                  {/* Performance */}
                  {(mProfit !== 0 || mLoss !== 0) && (
                    <Box sx={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: { xs: 1.5, sm: 3 },
                      py: 1,
                      px: 1.5,
                      borderRadius: 1,
                      bgcolor: 'rgba(255, 255, 255, 0.03)'
                    }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block' }}>
                          Gewinne
                        </Typography>
                        <Typography variant="body2" color="success.main" fontWeight={600}>
                          {formatPct(mProfit)}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block' }}>
                          Verluste
                        </Typography>
                        <Typography variant="body2" color="error.main" fontWeight={600}>
                          {mLoss.toFixed(1)}%
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem', display: 'block' }}>
                          Netto
                        </Typography>
                        <Typography variant="body2" fontWeight={700} color={mNet >= 0 ? 'success.main' : 'error.main'}>
                          {formatPct(mNet)}
                        </Typography>
                      </Box>
                    </Box>
                  )}

                  {/* N8N Status */}
                  <Box sx={{ mt: 1.5, display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                    <Chip
                      label={model.n8n_enabled ? 'n8n aktiv' : 'n8n inaktiv'}
                      color={model.n8n_enabled ? 'success' : 'default'}
                      size="small"
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.65rem' }}
                    />
                    {model.n8n_webhook_url && (
                      <Chip
                        label="Webhook konfiguriert"
                        size="small"
                        variant="outlined"
                        sx={{ height: 20, fontSize: '0.65rem' }}
                      />
                    )}
                    <Chip
                      label={`${model.model_type} · ${model.target_direction?.toUpperCase()} · ${model.future_minutes || '?'}min`}
                      size="small"
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.65rem' }}
                    />
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}
    </PageContainer>
  );
};

export default AlertSystem;
