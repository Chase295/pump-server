/**
 * Coin Details Page
 * Zeigt Preis-Kurve, Vorhersagen und Auswertungen für einen Coin
 */
import React from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Breadcrumbs,
  Link as MuiLink,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  IconButton
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  TrendingUp as UpIcon,
  TrendingDown as DownIcon,
  CheckCircle as SuccessIcon,
  Cancel as FailedIcon,
  HourglassEmpty as WaitIcon,
  ChevronLeft as LeftIcon,
  ChevronRight as RightIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine
} from 'recharts';

import PageContainer from '../components/layout/PageContainer';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { coinsApi, modelsApi } from '../services/api';
import type { CoinDetails } from '../types/model';

const TIME_WINDOW_OPTIONS = [
  { value: 15, label: '15 Minuten' },
  { value: 30, label: '30 Minuten' },
  { value: 60, label: '1 Stunde' },
  { value: 120, label: '2 Stunden' },
  { value: 240, label: '4 Stunden' },
  { value: 480, label: '8 Stunden' },
  { value: 1440, label: '24 Stunden' }
];

const CoinDetails: React.FC = () => {
  const { modelId, coinId } = useParams<{ modelId: string; coinId: string }>();
  const [searchParams] = useSearchParams();
  const predictionIdParam = searchParams.get('prediction_id');
  const predictionId = predictionIdParam ? Number(predictionIdParam) : undefined;

  
  // Wenn prediction_id gesetzt, verwende automatischen Zeitraum (wird vom Backend berechnet)
  // Sonst verwende manuelles Zeitfenster
  const [timeWindow, setTimeWindow] = React.useState<number>(60);
  const [timeOffset, setTimeOffset] = React.useState<number>(0);

  const id = Number(modelId);

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

  // Coin-Details laden
  const {
    data: coinDetails,
    isLoading: isLoadingDetails,
    error: detailsError
  } = useQuery({
    queryKey: ['coinDetails', id, coinId, predictionId, timeWindow, timeOffset],
    queryFn: () => coinsApi.getDetails(id, coinId!, timeWindow, timeOffset, predictionId),
    enabled: !!id && !!coinId,
    refetchInterval: 30000
  });


  // EINFACHE Chart-Daten: Reale Preis-Entwicklung in %
  const chartData = React.useMemo(() => {
    if (!coinDetails?.price_history?.length) {
      return [];
    }

    // Sortiere Preis-Historie chronologisch
    const sortedHistory = [...coinDetails.price_history].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // BASIS-PREIS: Alert-Preis = 0% (wenn verfügbar), sonst erster Preis
    let basePrice = sortedHistory[0]?.price_close ||
                   sortedHistory[0]?.price_high ||
                   sortedHistory[0]?.price_low || 1;

    // Wenn wir Alert-Predictions haben, verwende Alert-Preis als Basis
    const alertPrediction = coinDetails?.predictions?.find(p => p.is_alert);
    if (alertPrediction) {
      const alertTimestamp = alertPrediction.prediction_timestamp || alertPrediction.timestamp;

      if (alertTimestamp) {
        const alertTime = new Date(alertTimestamp).getTime();
        // Finde den letzten Preis vor dem Alert-Zeitpunkt
        const alertPricePoint = sortedHistory
          .filter(point => new Date(point.timestamp).getTime() <= alertTime)
          .pop(); // Nimm den letzten (neueste) vor Alert-Zeit

        if (alertPricePoint) {
          const alertPrice = alertPricePoint.price_close || alertPricePoint.price_high || alertPricePoint.price_low || basePrice;
          basePrice = alertPrice;
        }
      }
    }
    // Fallback: Wenn wir normale Predictions haben, verwende Prediction-Preis
    else if (coinDetails?.predictions?.length) {
      const prediction = coinDetails.predictions[0];
      const predictionTimestamp = prediction.prediction_timestamp || prediction.timestamp;

      if (predictionTimestamp) {
        const predTime = new Date(predictionTimestamp).getTime();
        const predPricePoint = sortedHistory.find(point => {
          const pointTime = new Date(point.timestamp).getTime();
          return pointTime <= predTime;
        });

        if (predPricePoint) {
          basePrice = predPricePoint.price_close || predPricePoint.price_high || predPricePoint.price_low || basePrice;
        }
      }
    }

    // EINFACHE CHART-DATEN: Nur das Nötigste
    return sortedHistory.map((pricePoint) => {
      const timestamp = new Date(pricePoint.timestamp).getTime();
      const price = pricePoint.price_close || pricePoint.price_high || pricePoint.price_low || 0;

      // PROZENTUALE ÄNDERUNG: Entwicklung seit basePrice (Alert-Preis = 0%)
      const priceChangePercent = basePrice > 0 ? ((price - basePrice) / basePrice) * 100 : 0;

      return {
        timestamp: pricePoint.timestamp,
        timestampMs: timestamp,
        time: new Date(pricePoint.timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
        priceChangePercent: Number(priceChangePercent.toFixed(2)),
        price: price,
        priceFormatted: price < 0.0001 ? price.toExponential(3) : price.toFixed(6)
      };
    });
  }, [coinDetails]);

  // Alert- und Evaluation-Zeitpunkte + BASIS-PREIS für Chart
  const evaluationMarkers = React.useMemo(() => {
    // Zuerst versuchen wir alert_evaluations (für bereits ausgewertete Alerts)
    if (coinDetails?.evaluations?.length) {
      const evaluation = coinDetails.evaluations[0];
      const alertTimestamp = (evaluation as any)?.alert_timestamp;
      const evaluationTimestamp = evaluation.evaluation_timestamp;

      if (alertTimestamp && evaluationTimestamp) {
        return {
          startTime: new Date(alertTimestamp).getTime(),
          endTime: new Date(evaluationTimestamp).getTime(),
          startLabel: "🚨 Alert-Start",
          endLabel: "✅ Evaluation-Ende",
          // BASIS-PREIS für Chart: Alert-Preis = 0%
          chartBasePrice: null // Wird später berechnet
        };
      }
    }

    // Zweitens: Schauen nach Alert-Predictions (auch wenn noch nicht ausgewertet)
    const alertPrediction = coinDetails?.predictions?.find(p => (p as any).tag === 'alert' || (p as any).is_alert);
    if (alertPrediction) {
      const alertTimestamp = alertPrediction.prediction_timestamp || alertPrediction.timestamp;
      const evaluationTimestamp = alertPrediction.evaluation_timestamp;

      if (alertTimestamp && evaluationTimestamp) {
        return {
          startTime: new Date(alertTimestamp).getTime(),
          endTime: new Date(evaluationTimestamp).getTime(),
          startLabel: "🚨 Alert-Start",
          endLabel: "⏳ Pending Evaluation",
          // BASIS-PREIS für Chart: Alert-Preis = 0%
          chartBasePrice: null // Wird später berechnet
        };
      }
    }

    // Fallback: Verwende predictions (für normale Vorhersagen)
    if (coinDetails?.predictions?.length) {
      const prediction = coinDetails.predictions[0];
      const predictionTimestamp = prediction.prediction_timestamp || prediction.timestamp;
      const evaluationTimestamp = prediction.evaluation_timestamp;

      if (predictionTimestamp && evaluationTimestamp) {
        return {
          startTime: new Date(predictionTimestamp).getTime(),
          endTime: new Date(evaluationTimestamp).getTime(),
          startLabel: "🔮 Prediction-Start",
          endLabel: "📊 Evaluation-Ende",
          // BASIS-PREIS für Chart: Prediction-Preis = 0%
          chartBasePrice: null // Wird später berechnet
        };
      }
    }

    return null;
  }, [coinDetails]);

  // Y-Achsen-Domain berechnen (für bessere Skalierung bei kleinen Variationen)
  const yAxisDomain = React.useMemo(() => {
    if (!chartData || chartData.length === 0) {
      return [-10, 10] as const; // Standard: ±10%
    }

    const values = chartData
      .map(d => d.priceChangePercent)
      .filter((v): v is number => v !== null && v !== undefined);

    if (values.length === 0) {
      return [-10, 10] as const; // Standard: ±10%
    }

    const dataMin = Math.min(...values);
    const dataMax = Math.max(...values);

    // WENN wir Alert-Predictions oder normale Predictions haben: Symmetrische Darstellung um 0% (Alert/Prediction-Preis)
    if (coinDetails?.predictions?.length) {
      // 0% ist Alert/Prediction-Preis - zeige symmetrisch um diese Linie
      const range = Math.max(Math.abs(dataMin), Math.abs(dataMax));
      const padding = Math.max(range * 0.1, 1); // Mindestens 1% Padding
      const maxRange = range + padding;
      return [-maxRange, maxRange] as const;
    }

    // SONST: Symmetrische Skalierung um 0%
    const range = Math.max(Math.abs(dataMin), Math.abs(dataMax));
    
    // Symmetrische Domain um 0%: Berechne den maximalen absoluten Wert
    // und verwende ±(max + padding) für symmetrische Darstellung
    const padding = Math.max(range * 0.1, 1); // Mindestens 1% Padding
    const maxRange = range + padding;
    
    // Stelle sicher, dass mindestens ±5% angezeigt wird
    const minRange = Math.max(maxRange, 5);
    
    return [-minRange, minRange] as [number, number];
  }, [chartData]);

  // Statistiken berechnen
  const stats = React.useMemo(() => {
    if (!coinDetails) return null;

    const priceHistory = coinDetails.price_history;
    if (priceHistory.length === 0) return null;

    const predictions = coinDetails.predictions;
    const evaluations = coinDetails.evaluations;

    // ECHTE PREISE aus der chartData verwenden!
    const firstDataPoint = chartData[0];
    const lastDataPoint = chartData[chartData.length - 1];

    // Start-Preis: Erster Datenpunkt (0% = Basis)
    const startPrice = firstDataPoint?.price || 0;

    // End-Preis: Letzter Datenpunkt
    const endPrice = lastDataPoint?.price || 0;

    // Prozentuale Änderung: Vom ersten zum letzten Punkt
    const priceChange = lastDataPoint?.priceChangePercent || 0;

    return {
      startPrice,
      endPrice,
      priceChange,
      totalPredictions: predictions.length,
      totalAlerts: predictions.filter(p => p.is_alert).length,
      totalEvaluations: evaluations.length,
      successEvaluations: evaluations.filter(e => e.status === 'success').length,
      failedEvaluations: evaluations.filter(e => e.status === 'failed').length,
      pendingEvaluations: evaluations.filter(e => e.status === 'pending').length
    };
  }, [coinDetails, chartData]);

  if (isLoadingModel || isLoadingDetails) {
    return (
      <PageContainer>
        <LoadingSpinner />
      </PageContainer>
    );
  }

  if (modelError || detailsError) {
    return (
      <PageContainer>
        <Alert severity="error">
          Fehler beim Laden: {modelError?.message || detailsError?.message || 'Unbekannter Fehler'}
        </Alert>
      </PageContainer>
    );
  }

  if (!coinDetails || !model) {
    return (
      <PageContainer>
        <Alert severity="warning">Keine Daten gefunden</Alert>
      </PageContainer>
    );
  }

  const modelName = model.custom_name || model.name;

  return (
    <PageContainer>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <MuiLink component={Link} to="/overview" color="inherit">
          Übersicht
        </MuiLink>
        <MuiLink component={Link} to={`/model/${id}`} color="inherit">
          {modelName}
        </MuiLink>
        <MuiLink component={Link} to={`/model/${id}/logs`} color="inherit">
          Logs
        </MuiLink>
        <Typography color="text.primary" sx={{ fontFamily: 'monospace' }}>
          {coinId?.substring(0, 12)}...
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Coin-Details
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            {coinId}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          {predictionId ? (
            <Chip 
              label="Automatischer Zeitraum (10min vor/nach)" 
              color="primary"
              sx={{ fontWeight: 600 }}
            />
          ) : (
            <>
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Zeitfenster</InputLabel>
                <Select
                  value={timeWindow}
                  onChange={(e) => {
                    setTimeWindow(Number(e.target.value));
                    setTimeOffset(0);
                  }}
                  label="Zeitfenster"
                >
                  {TIME_WINDOW_OPTIONS.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {/* Scroll-Navigation */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <IconButton
                  size="small"
                  onClick={() => setTimeOffset(prev => prev - timeWindow)}
                  sx={{ 
                    border: '1px solid rgba(0, 212, 255, 0.3)',
                    color: '#00d4ff',
                    '&:hover': { backgroundColor: 'rgba(0, 212, 255, 0.2)' }
                  }}
                  title={`${timeWindow} Minuten zurück`}
                >
                  <LeftIcon />
                </IconButton>
                <Typography variant="body2" sx={{ minWidth: 80, textAlign: 'center' }}>
                  {timeOffset !== 0 && (
                    <Chip 
                      label={timeOffset > 0 ? `+${timeOffset}min` : `${timeOffset}min`} 
                      size="small" 
                      color="primary"
                      onDelete={() => setTimeOffset(0)}
                    />
                  )}
                </Typography>
                <IconButton
                  size="small"
                  onClick={() => setTimeOffset(prev => prev + timeWindow)}
                  sx={{ 
                    border: '1px solid rgba(0, 212, 255, 0.3)',
                    color: '#00d4ff',
                    '&:hover': { backgroundColor: 'rgba(0, 212, 255, 0.2)' }
                  }}
                  title={`${timeWindow} Minuten vor`}
                >
                  <RightIcon />
                </IconButton>
              </Box>
            </>
          )}
          
          <MuiLink
            component={Link}
            to={`/model/${id}/logs`}
            sx={{ textDecoration: 'none' }}
          >
            <BackIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Zurück zu Logs
          </MuiLink>
        </Box>
      </Box>

      {/* Info-Karten */}
      {stats && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              md: 'repeat(3, 1fr)'
            },
            gap: 2,
            mb: 3
          }}
        >
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Preis-Entwicklung
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Start: {stats.startPrice.toFixed(6)} SOL
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Aktuell: {stats.endPrice.toFixed(6)} SOL
              </Typography>
              <Typography 
                variant="h5" 
                color={stats.priceChange >= 0 ? 'success.main' : 'error.main'}
                sx={{ mt: 1 }}
              >
                {stats.priceChange >= 0 ? <UpIcon sx={{ verticalAlign: 'middle', mr: 0.5 }} /> : <DownIcon sx={{ verticalAlign: 'middle', mr: 0.5 }} />}
                {stats.priceChange.toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Vorhersagen
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Gesamt: {stats.totalPredictions}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Alerts: {stats.totalAlerts}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Normal: {stats.totalPredictions - stats.totalAlerts}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Auswertungen
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                <Chip 
                  icon={<SuccessIcon />} 
                  label={`${stats.successEvaluations} Success`} 
                  color="success" 
                  size="small"
                />
                <Chip 
                  icon={<FailedIcon />} 
                  label={`${stats.failedEvaluations} Failed`} 
                  color="error" 
                  size="small"
                />
                <Chip 
                  icon={<WaitIcon />} 
                  label={`${stats.pendingEvaluations} Wait`} 
                  color="warning" 
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Grafik */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📈 Reine Preis-Entwicklung in %
          </Typography>
          <Box sx={{ height: 600, width: '100%', mt: 2 }}>
            <ResponsiveContainer>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                {/* 0% Referenzlinie in der Mitte - Alert-Preis */}
                <ReferenceLine
                  y={0}
                  stroke="rgba(255, 255, 255, 0.8)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  label={{
                    value: "0% (Alert)",
                    position: "right",
                    style: { fill: 'rgba(255, 255, 255, 0.7)', fontSize: '12px', fontWeight: 'bold' }
                  }}
                />
                {/* 0% Referenzlinie in der Mitte - wie eine Sinuskurve */}
                <ReferenceLine
                  y={0}
                  stroke="rgba(255, 255, 255, 0.5)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  label={{ value: "0%", position: "right", style: { fill: 'rgba(255, 255, 255, 0.7)', fontSize: '12px' } }}
                />
                {/* START-Zeitpunkt Markierung */}
                {evaluationMarkers && (
                  <ReferenceLine
                    x={evaluationMarkers.startTime}
                    stroke="#ff6b35"
                    strokeWidth={3}
                    strokeDasharray="8 4"
                    label={{
                      value: evaluationMarkers.startLabel,
                      position: "top",
                      style: { fill: '#ff6b35', fontSize: '11px', fontWeight: 'bold' }
                    }}
                  />
                )}
                {/* END-Zeitpunkt Markierung */}
                {evaluationMarkers && (
                  <ReferenceLine
                    x={evaluationMarkers.endTime}
                    stroke="#4ade80"
                    strokeWidth={3}
                    strokeDasharray="8 4"
                    label={{
                      value: evaluationMarkers.endLabel,
                      position: "top",
                      style: { fill: '#4ade80', fontSize: '11px', fontWeight: 'bold' }
                    }}
                  />
                )}
                <XAxis 
                  dataKey="timestampMs" 
                  type="number"
                  scale="time"
                  stroke="rgba(255, 255, 255, 0.5)"
                  tick={{ fill: 'rgba(255, 255, 255, 0.7)' }}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
                  }}
                  domain={['dataMin', 'dataMax']}
                />
                <YAxis 
                  stroke="rgba(255, 255, 255, 0.5)"
                  tick={{ fill: 'rgba(255, 255, 255, 0.7)' }}
                  domain={yAxisDomain}
                  allowDataOverflow={false}
                  tickFormatter={(value: number) => {
                    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
                  }}
                  label={{ value: 'Reale Preis-Entwicklung (%)', angle: -90, position: 'insideLeft', style: { fill: 'rgba(255, 255, 255, 0.7)' } }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 15, 35, 0.95)',
                    border: '1px solid rgba(0, 212, 255, 0.3)',
                    borderRadius: '8px',
                    color: '#fff',
                    padding: '12px'
                  }}
                  formatter={(value: any) => {
                      return [
                      `${Number(value) >= 0 ? '+' : ''}${Number(value).toFixed(2)}%`,
                      `Reale Preis-Entwicklung`
                    ];
                  }}
                  labelFormatter={(value) => {
                    return `Zeit: ${new Date(Number(value)).toLocaleTimeString('de-DE')}`;
                  }}
                />
                <Legend />
                {/* HAUPTLINIE: Reale Preis-Entwicklung in % */}
                <Line 
                  type="monotone" 
                  dataKey="priceChangePercent" 
                  stroke="#00d4ff" 
                  strokeWidth={3}
                  dot={false}
                  name="Reale Preis-Entwicklung (%)"
                  isAnimationActive={false}
                  connectNulls={false}
                  activeDot={{ r: 6, fill: '#00d4ff', stroke: '#fff', strokeWidth: 2 }}
                            />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>
    </PageContainer>
  );
};

export default CoinDetails;
