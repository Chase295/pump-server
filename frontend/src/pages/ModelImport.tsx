/**
 * ModelImport Page
 * Importiert neue Modelle aus dem Training-Service
 * Kachel-Ansicht (Card-Grid) für bessere Übersicht
 */
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Alert,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Snackbar
} from '@mui/material';
import {
  CloudDownload as ImportIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

// Components
import PageContainer from '../components/layout/PageContainer';
import LoadingSpinner from '../components/common/LoadingSpinner';
import AvailableModelCard from '../components/models/AvailableModelCard';

// Services
import { modelsApi } from '../services/api';

interface AvailableModel {
  id: number;
  name: string;
  model_type: string;
  target_variable: string;
  target_operator?: string | null;
  target_value?: number | null;
  future_minutes: number;
  price_change_percent: number;
  target_direction: string;
  features: string[];
  phases?: number[] | null;
  training_accuracy?: number;
  training_f1?: number;
  training_precision?: number;
  training_recall?: number;
  created_at: string;
}

interface ImportResponse {
  active_model_id: number;
  model_id: number;
  model_name: string;
  local_model_path: string;
  message: string;
}

const ModelImport: React.FC = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedModel, setSelectedModel] = useState<AvailableModel | null>(null);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // Verfügbare Modelle laden
  const { data: availableModels, isLoading, error, refetch, isRefetching } = useQuery<AvailableModel[], Error>({
    queryKey: ['available-models'],
    queryFn: modelsApi.getAvailable
  });

  // Prüfe ob ein Modell zum Importieren übergeben wurde (von Detail-Seite)
  useEffect(() => {
    const importModelId = (location.state as any)?.importModelId;
    if (importModelId && availableModels) {
      const modelToImport = availableModels.find(m => m.id === importModelId);
      if (modelToImport) {
        setSelectedModel(modelToImport);
        setConfirmDialogOpen(true);
        // Lösche den State, damit es nicht erneut ausgelöst wird
        navigate(location.pathname, { replace: true, state: {} });
      }
    }
  }, [location.state, availableModels, navigate, location.pathname]);

  // Bereits importierte Modelle laden
  const { data: activeModels } = useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.getAll
  });

  // Import-Mutation
  const importMutation = useMutation<ImportResponse, Error, number>({
    mutationFn: (modelId: number) => modelsApi.importModel(modelId),
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: data.message,
        severity: 'success'
      });
      setConfirmDialogOpen(false);
      setSelectedModel(null);
      // Refresh verfügbare Modelle und aktive Modelle
      queryClient.invalidateQueries({ queryKey: ['available-models'] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (error) => {
      setSnackbar({
        open: true,
        message: `Import fehlgeschlagen: ${error.message}`,
        severity: 'error'
      });
    }
  });

  const handleImportClick = (model: AvailableModel) => {
    setSelectedModel(model);
    setConfirmDialogOpen(true);
  };

  const handleDetailsClick = (modelId: number) => {
    navigate(`/model-import/${modelId}`);
  };

  const handleConfirmImport = () => {
    if (selectedModel) {
      importMutation.mutate(selectedModel.id);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const isAlreadyImported = (modelId: number) => {
    return activeModels?.some(model => model.model_id === modelId) || false;
  };

  const getModelTypeLabel = (type: string) => {
    const labels: { [key: string]: string } = {
      'random_forest': 'Random Forest',
      'xgboost': 'XGBoost',
      'neural_network': 'Neural Network',
      'svm': 'SVM'
    };
    return labels[type] || type;
  };

  const formatPercentage = (value: number | undefined): string => {
    if (value === undefined) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  // Statistiken berechnen
  // HINWEIS: Die API /api/models/available gibt nur nicht-importierte Modelle zurück
  // Daher zeigen wir die Anzahl der bereits importierten Modelle aus activeModels
  const stats = React.useMemo(() => {
    const available = availableModels?.length || 0;
    const imported = activeModels?.length || 0;

    return {
      total: available + imported, // Gesamt = Verfügbar + Bereits importiert
      ready: available,            // Bereit = Verfügbare (nicht importierte)
      imported: imported           // Bereits importiert = Aktive Modelle
    };
  }, [availableModels, activeModels]);

  if (isLoading) {
    return <LoadingSpinner message="Lade verfügbare Modelle..." />;
  }

  if (error) {
    return (
      <PageContainer>
        <Alert severity="error" sx={{ mb: 3 }}>
          Fehler beim Laden der verfügbaren Modelle: {error.message}
        </Alert>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Erneut versuchen
        </Button>
      </PageContainer>
    );
  }

  const readyModels = availableModels || [];

  return (
    <PageContainer>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            📥 Modell-Import
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            disabled={isRefetching}
            size="small"
          >
            {isRefetching ? 'Aktualisiere...' : 'Aktualisieren'}
          </Button>
        </Box>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Importiere neue Modelle aus dem Training-Service in deinen Pump Server
        </Typography>

        {/* Statistiken */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Chip
            label={`${stats.total} Gesamt`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`${stats.ready} Bereit`}
            color="success"
            variant="filled"
          />
          <Chip
            label={`${stats.imported} Bereits importiert`}
            color="default"
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Info Alert */}
      {activeModels && activeModels.length > 0 && stats.imported > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Du hast bereits {activeModels.length} Modell(e) importiert. Bereits importierte Modelle sind ausgegraut dargestellt.
        </Alert>
      )}

      {/* Modelle Grid */}
      {readyModels.length === 0 ? (
        <Card sx={{ textAlign: 'center', py: 6 }}>
          <CardContent>
            <InfoIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Keine Modelle verfügbar
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Aktuell sind keine neuen Modelle zum Import verfügbar.
              Neue Modelle werden automatisch nach dem Training hier angezeigt.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              lg: 'repeat(3, 1fr)'
            },
            gap: 3
          }}
        >
          {readyModels.map((model) => (
            <AvailableModelCard
              key={model.id}
              model={model}
              onDetailsClick={handleDetailsClick}
              onImportClick={handleImportClick}
              isAlreadyImported={isAlreadyImported(model.id)}
              isImporting={importMutation.isPending && selectedModel?.id === model.id}
            />
          ))}
        </Box>
      )}

      {/* Footer Info */}
      <Box sx={{ mt: 4, p: 2, backgroundColor: 'background.paper', borderRadius: 2 }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Modelle werden vom Training-Service geladen •
          Letzte Aktualisierung: {new Date().toLocaleTimeString()}
        </Typography>
      </Box>

      {/* Confirm Import Dialog */}
      <Dialog
        open={confirmDialogOpen}
        onClose={() => !importMutation.isPending && setConfirmDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          📥 Modell importieren
        </DialogTitle>
        <DialogContent>
          {selectedModel && (
            <Box sx={{ pt: 1 }}>
              <Typography variant="body1" sx={{ mb: 2, color: 'text.primary' }}>
                Möchtest du das Modell <strong>{selectedModel.name}</strong> wirklich importieren?
              </Typography>

              <Box sx={{ bgcolor: 'action.hover', p: 2, borderRadius: 1, mb: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 500, mb: 1, color: 'text.primary' }}>
                  Modell-Details:
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1 }}>
                  <Typography variant="caption" sx={{ color: 'text.primary' }}>
                    Typ: {getModelTypeLabel(selectedModel.model_type)}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.primary' }}>
                    Accuracy: {formatPercentage(selectedModel.training_accuracy)}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.primary' }}>
                    F1-Score: {formatPercentage(selectedModel.training_f1)}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.primary' }}>
                    Features: {selectedModel.features.length}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.primary' }}>
                    Ziel: {selectedModel.target_direction?.toUpperCase()} {selectedModel.price_change_percent}%
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.primary' }}>
                    Zeitfenster: {selectedModel.future_minutes} min
                  </Typography>
                </Box>
              </Box>

              <Alert severity="info" sx={{ mb: 2 }}>
                Nach dem Import ist das Modell sofort einsatzbereit und kann in der Übersicht aktiviert werden.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setConfirmDialogOpen(false)}
            disabled={importMutation.isPending}
          >
            Abbrechen
          </Button>
          <Button
            onClick={handleConfirmImport}
            variant="contained"
            color="success"
            disabled={importMutation.isPending}
            startIcon={importMutation.isPending ? <CircularProgress size={16} /> : <ImportIcon />}
          >
            {importMutation.isPending ? 'Importiere...' : 'Importieren'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </PageContainer>
  );
};

export default ModelImport;
