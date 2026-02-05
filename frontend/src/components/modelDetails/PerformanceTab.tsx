/**
 * PerformanceTab Component
 * Performance-Metriken und Analyse für ein Modell
 * Mit Sub-Tabs: Live (echte Alert-Daten) und Training (ML-Metriken)
 */
import React from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Chip
} from '@mui/material';
import {
  TableChart as TableIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ShowChart as ChartIcon,
  CheckCircle as SuccessIcon,
  Cancel as FailedIcon
} from '@mui/icons-material';
import type { Model, AlertStatistics } from '../../types/model';

interface PerformanceTabProps {
  model: Model;
  alertStats?: AlertStatistics;
}

const PerformanceTab: React.FC<PerformanceTabProps> = ({ model, alertStats }) => {
  const [subTab, setSubTab] = React.useState(0);

  // Training-Metriken (aus dem ML-Training)
  const trainingMetrics = {
    accuracy: model.accuracy || 0,
    f1Score: model.f1_score || 0,
    precision: model.precision || 0,
    recall: model.recall || 0,
    rocAuc: model.roc_auc || 0,
    mcc: model.mcc || 0,
    simulatedProfit: model.simulated_profit_pct || 0
  };

  // Live-Metriken (aus echten Alerts)
  const liveMetrics = React.useMemo(() => {
    if (!alertStats) {
      return {
        totalPerformancePct: 0,
        alertsProfitPct: 0,
        alertsLossPct: 0,
        alertsSuccess: 0,
        alertsFailed: 0,
        alertsSuccessRate: 0,
        nonAlertsSuccess: 0,
        nonAlertsFailed: 0,
        nonAlertsSuccessRate: 0,
        totalAlerts: 0,
        pending: 0,
        hasData: false
      };
    }

    return {
      totalPerformancePct: alertStats.total_performance_pct || 0,
      alertsProfitPct: alertStats.alerts_profit_pct || 0,
      alertsLossPct: alertStats.alerts_loss_pct || 0,
      alertsSuccess: alertStats.alerts_success || 0,
      alertsFailed: alertStats.alerts_failed || 0,
      alertsSuccessRate: alertStats.alerts_success_rate || 0,
      nonAlertsSuccess: alertStats.non_alerts_success || 0,
      nonAlertsFailed: alertStats.non_alerts_failed || 0,
      nonAlertsSuccessRate: alertStats.non_alerts_success_rate || 0,
      totalAlerts: alertStats.total_alerts || 0,
      pending: alertStats.pending || 0,
      hasData: (alertStats.alerts_success || 0) + (alertStats.alerts_failed || 0) > 0
    };
  }, [alertStats]);

  const formatPercentage = (value: number, decimals: number = 1): string => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(decimals)}%`;
  };

  const formatProfitPct = (value: number): string => {
    const formatted = value.toFixed(1);
    return value >= 0 ? `+${formatted}%` : `${formatted}%`;
  };

  const handleSubTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setSubTab(newValue);
  };

  return (
    <Box>
      <Typography
        variant="h5"
        gutterBottom
        sx={{ fontWeight: 600, fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
      >
        🎯 Performance-Metriken
      </Typography>

      {/* Sub-Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs
          value={subTab}
          onChange={handleSubTabChange}
          aria-label="performance sub-tabs"
          sx={{
            '& .MuiTab-root': {
              textTransform: 'none',
              fontSize: { xs: '0.8rem', sm: '0.9rem' },
              fontWeight: 500,
              minWidth: { xs: 'auto', sm: 120 }
            }
          }}
        >
          <Tab label="📊 Live-Daten" />
          <Tab label="📈 Training-Metriken" />
        </Tabs>
      </Box>

      {/* Live-Daten Tab */}
      {subTab === 0 && (
        <Box>
          {!liveMetrics.hasData ? (
            <Alert severity="info" sx={{ mb: 3 }}>
              Noch keine ausgewerteten Alerts vorhanden. Die Live-Performance wird angezeigt,
              sobald Alerts ausgewertet wurden.
            </Alert>
          ) : (
            <>
              {/* Alert-Performance Übersicht */}
              <Typography
                variant="h6"
                gutterBottom
                sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' }, mt: 2 }}
              >
                🎯 Alert-Performance
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: 'repeat(2, 1fr)',
                    sm: 'repeat(4, 1fr)'
                  },
                  gap: { xs: 2, sm: 3 },
                  mb: 4
                }}
              >
                <Card sx={{ textAlign: 'center' }}>
                  <CardContent sx={{ py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                    <Typography
                      sx={{
                        fontWeight: 700,
                        fontSize: { xs: '1.25rem', sm: '1.75rem' },
                        color: liveMetrics.totalPerformancePct >= 0 ? 'success.main' : 'error.main'
                      }}
                    >
                      {formatProfitPct(liveMetrics.totalPerformancePct)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>
                      Gesamt-Profit
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ textAlign: 'center' }}>
                  <CardContent sx={{ py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                    <Typography
                      color="primary.main"
                      sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.75rem' } }}
                    >
                      {liveMetrics.alertsSuccessRate.toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>
                      Success-Rate
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ textAlign: 'center' }}>
                  <CardContent sx={{ py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      <SuccessIcon sx={{ color: 'success.main', fontSize: { xs: 18, sm: 24 } }} />
                      <Typography
                        color="success.main"
                        sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.75rem' } }}
                      >
                        {liveMetrics.alertsSuccess}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>
                      Erfolgreiche Alerts
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ textAlign: 'center' }}>
                  <CardContent sx={{ py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      <FailedIcon sx={{ color: 'error.main', fontSize: { xs: 18, sm: 24 } }} />
                      <Typography
                        color="error.main"
                        sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.75rem' } }}
                      >
                        {liveMetrics.alertsFailed}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>
                      Fehlgeschlagene Alerts
                    </Typography>
                  </CardContent>
                </Card>
              </Box>

              {/* Profit-Aufteilung */}
              <Typography
                variant="h6"
                gutterBottom
                sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' } }}
              >
                💰 Profit-Aufteilung
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr',
                    sm: 'repeat(3, 1fr)'
                  },
                  gap: { xs: 2, sm: 3 },
                  mb: 4
                }}
              >
                <Card>
                  <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                      <TrendingUpIcon sx={{ color: 'success.main', fontSize: { xs: 24, sm: 32 } }} />
                      <Typography
                        color="success.main"
                        sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                      >
                        +{liveMetrics.alertsProfitPct.toFixed(1)}%
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Gewinne (Success)
                    </Typography>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                      <TrendingDownIcon sx={{ color: 'error.main', fontSize: { xs: 24, sm: 32 } }} />
                      <Typography
                        color="error.main"
                        sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                      >
                        {liveMetrics.alertsLossPct.toFixed(1)}%
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Verluste (Failed)
                    </Typography>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                      <ChartIcon sx={{ color: liveMetrics.totalPerformancePct >= 0 ? 'success.main' : 'error.main', fontSize: { xs: 24, sm: 32 } }} />
                      <Typography
                        sx={{
                          fontWeight: 700,
                          fontSize: { xs: '1.25rem', sm: '1.5rem' },
                          color: liveMetrics.totalPerformancePct >= 0 ? 'success.main' : 'error.main'
                        }}
                      >
                        {formatProfitPct(liveMetrics.totalPerformancePct)}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Netto-Performance
                    </Typography>
                  </CardContent>
                </Card>
              </Box>

              {/* Confusion Matrix */}
              <Typography
                variant="h6"
                gutterBottom
                sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' } }}
              >
                📊 Confusion Matrix (Live-Daten)
              </Typography>
              <Card sx={{ mb: 3 }}>
                <CardContent sx={{ px: { xs: 1, sm: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <TableIcon sx={{ mr: 1, color: 'primary.main', fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
                    <Typography
                      variant="body1"
                      sx={{ fontWeight: 500, fontSize: { xs: '0.85rem', sm: '1rem' } }}
                    >
                      Auswertung der Alert-Vorhersagen
                    </Typography>
                  </Box>

                  <TableContainer component={Paper} sx={{ maxWidth: { xs: '100%', sm: 450 }, mx: 'auto' }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell align="center" sx={{ fontWeight: 600, fontSize: { xs: '0.7rem', sm: '0.875rem' }, px: { xs: 0.5, sm: 2 } }}>
                            Tatsächlich
                          </TableCell>
                          <TableCell align="center" sx={{ fontWeight: 600, fontSize: { xs: '0.7rem', sm: '0.875rem' }, px: { xs: 0.5, sm: 2 } }}>
                            Alert ✅
                          </TableCell>
                          <TableCell align="center" sx={{ fontWeight: 600, fontSize: { xs: '0.7rem', sm: '0.875rem' }, px: { xs: 0.5, sm: 2 } }}>
                            Kein Alert
                          </TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell align="center" sx={{ fontWeight: 600, fontSize: { xs: '0.7rem', sm: '0.875rem' }, px: { xs: 0.5, sm: 2 } }}>
                            Eingetroffen
                          </TableCell>
                          <TableCell
                            align="center"
                            sx={{ bgcolor: 'success.light', color: 'success.contrastText', fontWeight: 600, fontSize: { xs: '0.8rem', sm: '1rem' }, px: { xs: 0.5, sm: 2 } }}
                          >
                            {liveMetrics.alertsSuccess}
                          </TableCell>
                          <TableCell align="center" sx={{ fontSize: { xs: '0.8rem', sm: '1rem' }, px: { xs: 0.5, sm: 2 } }}>
                            {liveMetrics.nonAlertsSuccess}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell align="center" sx={{ fontWeight: 600, fontSize: { xs: '0.7rem', sm: '0.875rem' }, px: { xs: 0.5, sm: 2 } }}>
                            Nicht eingetroffen
                          </TableCell>
                          <TableCell align="center" sx={{ fontSize: { xs: '0.8rem', sm: '1rem' }, px: { xs: 0.5, sm: 2 } }}>
                            {liveMetrics.alertsFailed}
                          </TableCell>
                          <TableCell
                            align="center"
                            sx={{ bgcolor: 'info.light', color: 'info.contrastText', fontWeight: 600, fontSize: { xs: '0.8rem', sm: '1rem' }, px: { xs: 0.5, sm: 2 } }}
                          >
                            {liveMetrics.nonAlertsFailed}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  <Box sx={{
                    mt: 2,
                    display: 'grid',
                    gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' },
                    gap: { xs: 1, sm: 2 },
                    justifyItems: 'center'
                  }}>
                    <Chip
                      size="small"
                      icon={<SuccessIcon />}
                      label={`TP: ${liveMetrics.alertsSuccess}`}
                      color="success"
                      variant="outlined"
                      sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                    />
                    <Chip
                      size="small"
                      icon={<FailedIcon />}
                      label={`FP: ${liveMetrics.alertsFailed}`}
                      color="error"
                      variant="outlined"
                      sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                    />
                    <Chip
                      size="small"
                      label={`FN: ${liveMetrics.nonAlertsSuccess}`}
                      color="warning"
                      variant="outlined"
                      sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                    />
                    <Chip
                      size="small"
                      label={`TN: ${liveMetrics.nonAlertsFailed}`}
                      color="info"
                      variant="outlined"
                      sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                    />
                  </Box>

                  {liveMetrics.pending > 0 && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      {liveMetrics.pending} Alert(s) noch ausstehend (werden noch ausgewertet)
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </Box>
      )}

      {/* Training-Metriken Tab */}
      {subTab === 1 && (
        <Box>
          <Alert severity="info" sx={{ mb: 3 }}>
            Diese Metriken stammen aus dem ML-Training und zeigen die theoretische Leistung des Modells
            basierend auf historischen Trainingsdaten.
          </Alert>

          {/* Kern-Metriken */}
          <Typography
            variant="h6"
            gutterBottom
            sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' }, mt: 2 }}
          >
            📊 Kern-Metriken
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: 'repeat(2, 1fr)',
                sm: 'repeat(4, 1fr)'
              },
              gap: { xs: 2, sm: 3 },
              mb: 4
            }}
          >
            <Card sx={{ textAlign: 'center' }}>
              <CardContent sx={{ py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                <Typography
                  color="primary.main"
                  sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.75rem' } }}
                >
                  {trainingMetrics.accuracy > 0 ? formatPercentage(trainingMetrics.accuracy) : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>
                  Accuracy
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ textAlign: 'center' }}>
              <CardContent sx={{ py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                <Typography
                  color="success.main"
                  sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.75rem' } }}
                >
                  {trainingMetrics.f1Score > 0 ? formatPercentage(trainingMetrics.f1Score) : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>
                  F1-Score
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ textAlign: 'center' }}>
              <CardContent sx={{ py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                <Typography
                  color="info.main"
                  sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.75rem' } }}
                >
                  {trainingMetrics.precision > 0 ? formatPercentage(trainingMetrics.precision) : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>
                  Precision
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ textAlign: 'center' }}>
              <CardContent sx={{ py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                <Typography
                  color="warning.main"
                  sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.75rem' } }}
                >
                  {trainingMetrics.recall > 0 ? formatPercentage(trainingMetrics.recall) : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.875rem' } }}>
                  Recall
                </Typography>
              </CardContent>
            </Card>
          </Box>

          {/* Erweiterte Metriken */}
          <Typography
            variant="h6"
            gutterBottom
            sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' } }}
          >
            🔬 Erweiterte Metriken
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(3, 1fr)'
              },
              gap: { xs: 2, sm: 3 },
              mb: 4
            }}
          >
            <Card>
              <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                <Typography
                  color="secondary.main"
                  sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                >
                  {trainingMetrics.rocAuc > 0 ? formatPercentage(trainingMetrics.rocAuc, 2) : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                  ROC AUC Score
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
                  Area Under Curve - Je höher, desto besser
                </Typography>
              </CardContent>
            </Card>

            <Card>
              <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                <Typography
                  color="error.main"
                  sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                >
                  {trainingMetrics.mcc > 0 ? formatPercentage(trainingMetrics.mcc, 2) : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                  Matthews Correlation
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
                  Balanced Accuracy-Metric (-1 bis +1)
                </Typography>
              </CardContent>
            </Card>

            <Card>
              <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
                <Typography
                  color="success.main"
                  sx={{ fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                >
                  {trainingMetrics.simulatedProfit > 0 ? `${trainingMetrics.simulatedProfit}%` : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                  Simulierter Profit
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
                  Basierend auf historischen Daten
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default PerformanceTab;
