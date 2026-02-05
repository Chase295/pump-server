/**
 * AvailableModelDetails Page
 * Vollständige Detailansicht eines verfügbaren Modells (vor dem Import) - 1:1 wie ModelDetails
 */
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Typography,
  Box,
  Tabs,
  Tab,
  Breadcrumbs,
  Link as MuiLink,
  Chip,
  Alert,
  Button,
  Card,
  CardContent
} from '@mui/material';
import { ArrowBack as BackIcon, CloudDownload as ImportIcon } from '@mui/icons-material';

// Components
import PageContainer from '../components/layout/PageContainer';
import LoadingSpinner from '../components/common/LoadingSpinner';
import OverviewTab from '../components/modelDetails/OverviewTab';
import PerformanceTab from '../components/modelDetails/PerformanceTab';
import PredictionsTab from '../components/modelDetails/PredictionsTab';
import JsonExportTab from '../components/modelDetails/JsonExportTab';

// Services
import { modelsApi } from '../services/api';
import type { Model } from '../types/model';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`available-model-details-tabpanel-${index}`}
      aria-labelledby={`available-model-details-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const AvailableModelDetails: React.FC = () => {
  const { modelId } = useParams<{ modelId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = React.useState(0);

  const id = Number(modelId);

  // Modell-Daten laden
  const {
    data: availableModel,
    isLoading,
    error
  } = useQuery({
    queryKey: ['available-model', id],
    queryFn: () => modelsApi.getAvailableModelDetails(id),
    enabled: !!id
  });

  // Konvertiere verfügbares Modell in Model-Format für die Tab-Komponenten
  const model: Model | null = React.useMemo(() => {
    if (!availableModel) return null;

    return {
      id: availableModel.id,
      model_id: availableModel.id,
      name: availableModel.name,
      custom_name: availableModel.name,
      model_type: availableModel.model_type,
      target_variable: availableModel.target_variable,
      target_operator: availableModel.target_operator || undefined,
      target_value: availableModel.target_value || undefined,
      future_minutes: availableModel.future_minutes || 0,
      price_change_percent: availableModel.price_change_percent || 0,
      target_direction: availableModel.target_direction || 'up',
      features: availableModel.features || [],
      phases: availableModel.phases || undefined,

      // Status (verfügbare Modelle sind noch nicht aktiv)
      is_active: false,

      // Alert-Konfiguration (Standardwerte)
      n8n_webhook_url: undefined,
      n8n_enabled: false,
      n8n_send_mode: 'all',
      alert_threshold: 0.7,
      coin_filter_mode: 'all',
      coin_whitelist: undefined,

      // Ignore-Settings (Standardwerte)
      ignore_bad_seconds: 0,
      ignore_positive_seconds: 0,
      ignore_alert_seconds: 0,

      // Performance-Metriken (aus Training)
      accuracy: availableModel.training_accuracy,
      f1_score: availableModel.training_f1,
      precision: undefined,
      recall: undefined,
      roc_auc: undefined,
      mcc: undefined,
      simulated_profit_pct: undefined,

      // Live-Performance-Metriken (noch keine, da nicht importiert)
      total_predictions: 0,
      positive_predictions: 0,
      average_probability: undefined,
      last_prediction_at: undefined,

      // Timestamps
      created_at: availableModel.created_at,
      updated_at: undefined
    };
  }, [availableModel]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleBack = () => {
    navigate('/model-import');
  };

  const handleImport = () => {
    // Navigiere zurück zur Import-Seite und öffne den Import-Dialog
    navigate('/model-import', { state: { importModelId: id } });
  };

  if (isLoading) {
    return <LoadingSpinner message="Modell-Details werden geladen..." />;
  }

  if (error || !model || !availableModel) {
    return (
      <PageContainer>
        <Alert severity="error" sx={{ mb: 3 }}>
          Fehler beim Laden der Modell-Details: {error?.message || 'Modell nicht gefunden'}
        </Alert>
        <Button startIcon={<BackIcon />} onClick={handleBack}>
          Zurück zum Import
        </Button>
      </PageContainer>
    );
  }

  const modelName = model.custom_name || model.name;
  const isActive = model.is_active;

  return (
    <PageContainer>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <MuiLink
          component="button"
          variant="body2"
          onClick={() => navigate('/model-import')}
          sx={{ cursor: 'pointer' }}
        >
          Modell Import
        </MuiLink>
        <Typography color="text.primary">{modelName}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'flex-start' },
          gap: { xs: 2, sm: 0 },
          mb: 2
        }}>
          <Box sx={{ mb: { xs: 1, sm: 0 } }}>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                mb: 1,
                fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
              }}
            >
              🔍 {modelName}
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.85rem', sm: '1rem' } }}
            >
              ID: {model.id} • Typ: {model.model_type} • Ziel: {model.target_direction?.toUpperCase()}
            </Typography>
          </Box>

          <Box sx={{
            display: 'flex',
            gap: { xs: 1, sm: 2 },
            alignItems: 'center',
            flexWrap: 'wrap',
            width: { xs: '100%', sm: 'auto' }
          }}>
            <Chip
              label={isActive ? 'Aktiv' : 'Verfügbar'}
              color={isActive ? 'success' : 'info'}
              variant={isActive ? 'filled' : 'outlined'}
              size="medium"
            />
            <Button
              variant="contained"
              color="primary"
              startIcon={<ImportIcon />}
              onClick={handleImport}
              size="small"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Importieren
            </Button>
            <Button
              startIcon={<BackIcon />}
              onClick={handleBack}
              variant="outlined"
              size="small"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Zurück
            </Button>
          </Box>
        </Box>

        {/* Quick Stats - GENAU WIE IN ModelDetails */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(4, 1fr)'
            },
            gap: 3
          }}
        >
          <Card>
            <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
              <Typography
                color="primary"
                sx={{ fontSize: { xs: '1.5rem', sm: '2rem' }, fontWeight: 600 }}
              >
                {model.total_predictions || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                Vorhersagen Gesamt
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
              <Typography
                color="success.main"
                sx={{ fontSize: { xs: '1.5rem', sm: '2rem' }, fontWeight: 600 }}
              >
                {model.average_probability ? `${(model.average_probability * 100).toFixed(1)}%` : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                Ø Wahrscheinlichkeit
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
              <Typography
                color="info.main"
                sx={{ fontSize: { xs: '1.5rem', sm: '2rem' }, fontWeight: 600 }}
              >
                {model.accuracy ? `${(model.accuracy * 100).toFixed(1)}%` : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                Accuracy
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent sx={{ textAlign: 'center', py: { xs: 1.5, sm: 2 }, px: { xs: 1, sm: 2 } }}>
              <Typography
                color="warning.main"
                sx={{ fontSize: { xs: '1.5rem', sm: '2rem' }, fontWeight: 600 }}
              >
                {model.positive_predictions || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                Positive Vorhersagen
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Tabs - GENAU WIE IN ModelDetails */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="model details tabs"
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{
            '& .MuiTab-root': {
              textTransform: 'none',
              fontSize: { xs: '0.8rem', sm: '0.95rem' },
              fontWeight: 500,
              minWidth: { xs: 'auto', sm: 90 },
              px: { xs: 1.5, sm: 2 }
            }
          }}
        >
          <Tab label="📊 Übersicht" />
          <Tab label="🎯 Performance" />
          <Tab label="🔮 Vorhersagen" />
          <Tab label="📋 JSON Export" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={activeTab} index={0}>
        <OverviewTab model={model} />
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <PerformanceTab model={model} />
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <PredictionsTab modelId={id} />
      </TabPanel>

      <TabPanel value={activeTab} index={3}>
        <JsonExportTab model={model} />
      </TabPanel>
    </PageContainer>
  );
};

export default AvailableModelDetails;
