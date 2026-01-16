import React from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Typography,
  Paper,
  Box,
  TextField,
  Button,
  Alert
} from '@mui/material';
import { RestartAlt as RestartIcon } from '@mui/icons-material';
import PageContainer from '../components/layout/PageContainer';

// Services
import { modelsApi } from '../services/api';
import { queryClient } from '../services/queryClient';

const Settings: React.FC = () => {
  // Persistente Konfiguration (wird im Backend gespeichert)
  const [databaseUrl, setDatabaseUrl] = React.useState('');
  const [trainingServiceUrl, setTrainingServiceUrl] = React.useState('');
  const [n8nWebhookUrl, setN8nWebhookUrl] = React.useState('');
  const [apiPort, setApiPort] = React.useState(8000);
  const [streamlitPort, setStreamlitPort] = React.useState(8501);
  const [saved, setSaved] = React.useState(false);

  // Service neu starten
  const restartMutation = useMutation({
    mutationFn: modelsApi.restartService,
    onSuccess: (data) => {
      console.log('Service restart initiated:', data);
      // Zeige Bestätigung und lade Seite nach 3 Sekunden neu
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    },
    onError: (error) => {
      console.error('Fehler beim Service-Neustart:', error);
    }
  });

  // Konfiguration laden
  const configQuery = useQuery({
    queryKey: ['config'],
    queryFn: modelsApi.getConfig,
    staleTime: 30000, // 30 Sekunden cache
  });

  // Konfiguration speichern
  const saveConfigMutation = useMutation({
    mutationFn: modelsApi.updateConfig,
    onSuccess: (data) => {
      console.log('Config saved:', data);
      setSaved(true);
      // Invalidate config query um neue Daten zu laden
      queryClient.invalidateQueries({ queryKey: ['config'] });
      // Wenn auto_restart aktiviert ist, warte kurz und lade dann neu
      if (data.auto_restart) {
        setTimeout(() => {
          window.location.reload();
        }, 3000);
      }
    },
    onError: (error) => {
      console.error('Fehler beim Speichern der Konfiguration:', error);
      setSaved(false);
    }
  });

  const handleSave = () => {
    // Speichere persistente Konfiguration über API
    const configUpdate = {
      database_url: databaseUrl,
      training_service_url: trainingServiceUrl,
      n8n_webhook_url: n8nWebhookUrl,
      api_port: apiPort,
      streamlit_port: streamlitPort,
    };

    saveConfigMutation.mutate(configUpdate);
  };

  const handleReset = () => {
    // Setze auf Standardwerte zurück
    setDatabaseUrl('postgresql://user:password@db:5432/ml_predictions');
    setTrainingServiceUrl('http://localhost:8001/api');
    setN8nWebhookUrl('');
    setApiPort(8000);
    setStreamlitPort(8501);
  };

  const handleRestart = () => {
    restartMutation.mutate();
  };

  // Lade Konfiguration beim ersten Laden
  React.useEffect(() => {
    if (configQuery.data?.config) {
      const config = configQuery.data.config;
      setDatabaseUrl(config.database_url || '');
      setTrainingServiceUrl(config.training_service_url || '');
      setN8nWebhookUrl(config.n8n_webhook_url || '');
      setApiPort(config.api_port || 8000);
      setStreamlitPort(config.streamlit_port || 8501);
    }
  }, [configQuery.data]);

  return (
    <PageContainer>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Einstellungen
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Konfiguriere die Anwendung nach deinen Bedürfnissen
        </Typography>
      </Box>


      {/* Datenbank Einstellungen */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Datenbank-Konfiguration
        </Typography>
        <Box sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Datenbank-URL"
            value={databaseUrl}
            onChange={(e) => setDatabaseUrl(e.target.value)}
            variant="outlined"
            sx={{ mb: 2 }}
            helperText="PostgreSQL-Verbindungsstring (wird persistent gespeichert)"
            placeholder="postgresql://user:password@host:port/database"
          />
          <TextField
            fullWidth
            label="Training-Service-URL"
            value={trainingServiceUrl}
            onChange={(e) => setTrainingServiceUrl(e.target.value)}
            variant="outlined"
            sx={{ mb: 2 }}
            helperText="URL des Training-Services für Modell-Downloads"
            placeholder="http://training-service:8001/api"
          />
          <TextField
            fullWidth
            label="n8n Webhook-URL (optional)"
            value={n8nWebhookUrl}
            onChange={(e) => setN8nWebhookUrl(e.target.value)}
            variant="outlined"
            sx={{ mb: 2 }}
            helperText="Webhook-URL für n8n-Integration"
            placeholder="https://n8n.example.com/webhook/..."
          />
          <Alert severity="info" sx={{ mb: 0 }}>
            <strong>💾 Persistente Konfiguration:</strong> Diese Einstellungen werden dauerhaft gespeichert und überleben Service-Neustarts. Ein Neustart ist nach Änderungen erforderlich.
          </Alert>
        </Box>
      </Paper>

      {/* Speichern-Buttons */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSave}
            disabled={saveConfigMutation.isPending || restartMutation.isPending || configQuery.isLoading}
            size="large"
          >
            {saveConfigMutation.isPending ? 'Speichere...' : 'Konfiguration speichern'}
          </Button>
          <Button
            variant="outlined"
            onClick={handleReset}
            disabled={saveConfigMutation.isPending || restartMutation.isPending || configQuery.isLoading}
            size="large"
          >
            Auf Standard zurücksetzen
          </Button>
          <Button
            variant="contained"
            color="warning"
            startIcon={<RestartIcon />}
            onClick={handleRestart}
            disabled={restartMutation.isPending || saveConfigMutation.isPending}
            size="large"
          >
            {restartMutation.isPending ? 'Starte neu...' : 'Service neu starten'}
          </Button>

          {saved && (
            <Alert severity="success" sx={{ ml: 2 }}>
              ✅ Konfiguration gespeichert!
            </Alert>
          )}

          {saveConfigMutation.isSuccess && (
            <Alert severity="success" sx={{ ml: 2 }}>
              <strong>✅ Konfiguration gespeichert!</strong><br/>
              Service-Neustart erforderlich um Änderungen zu aktivieren.
            </Alert>
          )}

          {saveConfigMutation.isError && (
            <Alert severity="error" sx={{ ml: 2 }}>
              Fehler beim Speichern der Konfiguration: {saveConfigMutation.error?.message}
            </Alert>
          )}

          {restartMutation.isSuccess && (
            <Alert severity="success" sx={{ ml: 2 }}>
              <strong>✅ Service wird neu gestartet!</strong><br/>
              Die Seite wird in wenigen Sekunden automatisch neu geladen...
            </Alert>
          )}

          {restartMutation.isError && (
            <Alert severity="error" sx={{ ml: 2 }}>
              Fehler beim Neustart: {restartMutation.error?.message}
            </Alert>
          )}
        </Box>
      </Paper>
    </PageContainer>
  );
};

export default Settings;
