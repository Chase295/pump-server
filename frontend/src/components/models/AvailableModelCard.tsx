/**
 * AvailableModelCard Component
 * Darstellung eines verfügbaren Modells zum Import
 * Design konsistent mit ModelCard für aktive Modelle
 */
import React, { useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  CircularProgress
} from '@mui/material';
import {
  CloudDownload as ImportIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckCircleIcon,
  Psychology as PsychologyIcon,
  Speed as SpeedIcon,
  BarChart as BarChartIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Timer as TimerIcon,
  Category as CategoryIcon,
  Layers as LayersIcon
} from '@mui/icons-material';

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

interface AvailableModelCardProps {
  model: AvailableModel;
  onDetailsClick: (modelId: number) => void;
  onImportClick: (model: AvailableModel) => void;
  isAlreadyImported: boolean;
  isImporting: boolean;
}

const AvailableModelCard: React.FC<AvailableModelCardProps> = React.memo(({
  model,
  onDetailsClick,
  onImportClick,
  isAlreadyImported,
  isImporting
}) => {
  const modelTypeLabel = useMemo(() => {
    const typeLabels: { [key: string]: string } = {
      'random_forest': 'RF',
      'xgboost': 'XGB',
      'neural_network': 'NN',
      'svm': 'SVM',
      'linear': 'LIN',
      'logistic': 'LOG'
    };
    return typeLabels[model.model_type] || model.model_type.toUpperCase();
  }, [model.model_type]);

  const formatPercentage = (value: number | undefined): string => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  const directionIcon = model.target_direction === 'up' ? (
    <TrendingUpIcon fontSize="small" sx={{ color: 'success.main' }} />
  ) : (
    <TrendingDownIcon fontSize="small" sx={{ color: 'error.main' }} />
  );

  const directionColor = model.target_direction === 'up' ? 'success.main' : 'error.main';

  return (
    <Card
      variant="outlined"
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        cursor: 'pointer',
        background: isAlreadyImported
          ? 'rgba(255, 255, 255, 0.02)'
          : 'linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(76, 175, 80, 0.02) 100%)',
        border: `1px solid ${isAlreadyImported ? 'rgba(255, 255, 255, 0.1)' : 'rgba(76, 175, 80, 0.3)'}`,
        position: 'relative',
        overflow: 'hidden',
        opacity: isAlreadyImported ? 0.7 : 1,
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: isAlreadyImported
            ? 'rgba(158, 158, 158, 0.5)'
            : 'linear-gradient(90deg, #4caf50 0%, #66bb6a 100%)',
          transition: 'all 0.3s ease'
        },
        '&:hover': {
          transform: isAlreadyImported ? 'none' : 'translateY(-4px)',
          boxShadow: isAlreadyImported
            ? 'none'
            : '0 8px 24px rgba(76, 175, 80, 0.2)',
          borderColor: isAlreadyImported ? 'rgba(255, 255, 255, 0.1)' : 'rgba(76, 175, 80, 0.5)',
          '&::before': {
            height: isAlreadyImported ? '3px' : '4px'
          }
        }
      }}
      onClick={() => onDetailsClick(model.id)}
    >
      <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 1 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                background: isAlreadyImported
                  ? 'rgba(158, 158, 158, 0.2)'
                  : 'linear-gradient(135deg, #4caf50 0%, #66bb6a 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: isAlreadyImported ? 'none' : '0 4px 12px rgba(76, 175, 80, 0.3)'
              }}
            >
              <PsychologyIcon sx={{ color: isAlreadyImported ? 'rgba(255, 255, 255, 0.4)' : '#fff', fontSize: 28 }} />
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography
                variant="h6"
                component="div"
                sx={{
                  fontWeight: 700,
                  fontSize: '1.1rem',
                  color: isAlreadyImported ? 'text.secondary' : 'text.primary',
                  mb: 0.5,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                {model.name}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label={modelTypeLabel}
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    bgcolor: 'rgba(76, 175, 80, 0.15)',
                    color: 'success.main',
                    border: '1px solid rgba(76, 175, 80, 0.3)'
                  }}
                />
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  ID: {model.id}
                </Typography>
              </Box>
            </Box>
          </Box>
          {isAlreadyImported && (
            <Chip
              label="Importiert"
              color="default"
              size="small"
              icon={<CheckCircleIcon />}
              sx={{ fontWeight: 600 }}
            />
          )}
        </Box>

        {/* Training-Metriken */}
        <Box
          sx={{
            mb: 2,
            p: 2,
            background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.08) 0%, rgba(76, 175, 80, 0.03) 100%)',
            borderRadius: 2,
            border: '1px solid rgba(76, 175, 80, 0.2)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <Typography
            variant="caption"
            sx={{
              mb: 1.5,
              display: 'block',
              fontWeight: 700,
              fontSize: '0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              color: 'success.main'
            }}
          >
            📊 Training-Metriken
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 2
            }}
          >
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: 1.5,
                    bgcolor: 'rgba(76, 175, 80, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <SpeedIcon fontSize="small" sx={{ color: 'success.main' }} />
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: 'success.main' }}>
                  {formatPercentage(model.training_accuracy)}
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', ml: 5 }}>
                Accuracy
              </Typography>
            </Box>

            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: 1.5,
                    bgcolor: 'rgba(33, 150, 243, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <BarChartIcon fontSize="small" sx={{ color: 'info.main' }} />
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: 'info.main' }}>
                  {formatPercentage(model.training_f1)}
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', ml: 5 }}>
                F1-Score
              </Typography>
            </Box>

            {model.training_precision !== undefined && (
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: 1.5,
                      bgcolor: 'rgba(156, 39, 176, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <TrendingUpIcon fontSize="small" sx={{ color: 'secondary.main' }} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: 'secondary.main' }}>
                    {formatPercentage(model.training_precision)}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', ml: 5 }}>
                  Precision
                </Typography>
              </Box>
            )}

            {model.training_recall !== undefined && (
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: 1.5,
                      bgcolor: 'rgba(255, 152, 0, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <TrendingDownIcon fontSize="small" sx={{ color: 'warning.main' }} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: 'warning.main' }}>
                    {formatPercentage(model.training_recall)}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', ml: 5 }}>
                  Recall
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Ziel-Konfiguration */}
        <Box
          sx={{
            mb: 2,
            p: 2,
            background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 212, 255, 0.03) 100%)',
            borderRadius: 2,
            border: '1px solid rgba(0, 212, 255, 0.2)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <Typography
            variant="caption"
            sx={{
              mb: 1.5,
              display: 'block',
              fontWeight: 700,
              fontSize: '0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              color: 'primary.main'
            }}
          >
            🎯 Ziel-Konfiguration
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 2
            }}
          >
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: 1.5,
                    bgcolor: model.target_direction === 'up' ? 'rgba(76, 175, 80, 0.15)' : 'rgba(244, 67, 54, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  {directionIcon}
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: directionColor }}>
                  {model.target_direction?.toUpperCase()} {model.price_change_percent}%
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', ml: 5 }}>
                Richtung & Schwelle
              </Typography>
            </Box>

            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: 1.5,
                    bgcolor: 'rgba(0, 212, 255, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <TimerIcon fontSize="small" sx={{ color: 'primary.main' }} />
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>
                  {model.future_minutes} min
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', ml: 5 }}>
                Zeitfenster
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Features & Phasen */}
        <Box
          sx={{
            mb: 2,
            p: 1.5,
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 2,
            border: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 1
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CategoryIcon fontSize="small" sx={{ color: 'text.secondary' }} />
            <Typography variant="body2" color="text.secondary">
              {model.features.length} Features
            </Typography>
          </Box>
          {model.phases && model.phases.length > 0 && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LayersIcon fontSize="small" sx={{ color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Phase {model.phases.join(', ')}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Action Buttons */}
        <Box
          sx={{
            display: 'flex',
            gap: 1,
            justifyContent: 'space-between',
            alignItems: 'center',
            pt: 1.5,
            borderTop: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <Button
            variant="outlined"
            size="small"
            startIcon={<ViewIcon />}
            onClick={(e) => {
              e.stopPropagation();
              onDetailsClick(model.id);
            }}
            sx={{
              minWidth: 'auto',
              borderColor: 'rgba(0, 212, 255, 0.3)',
              color: 'primary.main',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'rgba(0, 212, 255, 0.1)'
              }
            }}
          >
            Details
          </Button>

          <Button
            variant="contained"
            size="small"
            color={isAlreadyImported ? 'inherit' : 'success'}
            startIcon={isImporting ? <CircularProgress size={16} color="inherit" /> : <ImportIcon />}
            onClick={(e) => {
              e.stopPropagation();
              if (!isAlreadyImported && !isImporting) {
                onImportClick(model);
              }
            }}
            disabled={isAlreadyImported || isImporting}
            sx={{
              minWidth: 'auto',
              fontWeight: 600,
              boxShadow: isAlreadyImported ? 'none' : '0 2px 8px rgba(76, 175, 80, 0.3)',
              '&:hover': {
                boxShadow: isAlreadyImported ? 'none' : '0 4px 12px rgba(76, 175, 80, 0.4)'
              },
              '&.Mui-disabled': {
                bgcolor: isAlreadyImported ? 'rgba(158, 158, 158, 0.2)' : undefined,
                color: isAlreadyImported ? 'text.secondary' : undefined
              }
            }}
          >
            {isImporting ? 'Importiere...' : isAlreadyImported ? 'Bereits importiert' : 'Importieren'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
});

AvailableModelCard.displayName = 'AvailableModelCard';

export default AvailableModelCard;
