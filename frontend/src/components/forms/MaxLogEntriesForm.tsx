/**
 * MaxLogEntriesForm Component
 * Formular für Max-Log-Entries-Einstellungen (wie oft ein Coin pro Tag eingetragen werden darf)
 */
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Box,
  TextField,
  Typography,
  Paper,
  Alert
} from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';

import { Model } from '../../types/model';

const maxLogEntriesSchema = z.object({
  max_log_entries_per_coin_negative: z.number().min(0).max(1000, 'Maximal 1000'),
  max_log_entries_per_coin_positive: z.number().min(0).max(1000, 'Maximal 1000'),
  max_log_entries_per_coin_alert: z.number().min(0).max(1000, 'Maximal 1000')
});

type MaxLogEntriesFormData = z.infer<typeof maxLogEntriesSchema>;

interface MaxLogEntriesFormProps {
  model: Model;
  onChange?: (data: MaxLogEntriesFormData) => void;
  disabled?: boolean;
}

const MaxLogEntriesForm: React.FC<MaxLogEntriesFormProps> = ({
  model,
  onChange,
  disabled = false
}) => {
  const {
    register,
    watch,
    reset,
    formState: { errors }
  } = useForm<MaxLogEntriesFormData>({
    resolver: zodResolver(maxLogEntriesSchema),
    defaultValues: {
      max_log_entries_per_coin_negative: model.max_log_entries_per_coin_negative ?? 0,
      max_log_entries_per_coin_positive: model.max_log_entries_per_coin_positive ?? 0,
      max_log_entries_per_coin_alert: model.max_log_entries_per_coin_alert ?? 0
    }
  });

  // Aktualisiere Formular-Werte wenn Modell-Daten geladen werden
  React.useEffect(() => {
    reset({
      max_log_entries_per_coin_negative: model.max_log_entries_per_coin_negative ?? 0,
      max_log_entries_per_coin_positive: model.max_log_entries_per_coin_positive ?? 0,
      max_log_entries_per_coin_alert: model.max_log_entries_per_coin_alert ?? 0
    });
  }, [model.max_log_entries_per_coin_negative, model.max_log_entries_per_coin_positive, model.max_log_entries_per_coin_alert, reset]);

  // Watch alle Felder für onChange
  const watchedValues = watch();

  React.useEffect(() => {
    if (onChange) {
      onChange(watchedValues as MaxLogEntriesFormData);
    }
  }, [watchedValues, onChange]);

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <InfoIcon color="primary" />
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          📊 Max-Log-Entries pro Coin
        </Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Begrenzt wie oft ein Coin als <strong>negativ</strong>, <strong>positiv</strong> oder <strong>alert</strong> in die Logs eingetragen wird.
        Nur <strong>aktive</strong> Einträge zählen (evaluierte Einträge zählen nicht mehr).
        Jede Kategorie wird separat gezählt.
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          label="Max. negative Einträge pro Coin"
          type="number"
          disabled={disabled}
          {...register('max_log_entries_per_coin_negative', {
            valueAsNumber: true
          })}
          error={!!errors.max_log_entries_per_coin_negative}
          helperText={
            errors.max_log_entries_per_coin_negative?.message ||
            '0 = unbegrenzt (Standard), 1 = nur 1x, 2 = maximal 2x, etc.'
          }
          InputProps={{
            inputProps: { min: 0, max: 1000, step: 1 }
          }}
        />

        <TextField
          label="Max. positive Einträge pro Coin"
          type="number"
          disabled={disabled}
          {...register('max_log_entries_per_coin_positive', {
            valueAsNumber: true
          })}
          error={!!errors.max_log_entries_per_coin_positive}
          helperText={
            errors.max_log_entries_per_coin_positive?.message ||
            '0 = unbegrenzt (Standard), 1 = nur 1x, 2 = maximal 2x, etc.'
          }
          InputProps={{
            inputProps: { min: 0, max: 1000, step: 1 }
          }}
        />

        <TextField
          label="Max. Alert-Einträge pro Coin"
          type="number"
          disabled={disabled}
          {...register('max_log_entries_per_coin_alert', {
            valueAsNumber: true
          })}
          error={!!errors.max_log_entries_per_coin_alert}
          helperText={
            errors.max_log_entries_per_coin_alert?.message ||
            '0 = unbegrenzt (Standard), 1 = nur 1x, 2 = maximal 2x, etc.'
          }
          InputProps={{
            inputProps: { min: 0, max: 1000, step: 1 }
          }}
        />
      </Box>

      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2" component="div">
          <strong>Beispiele:</strong>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            <li><code>0</code> = Unbegrenzt (Standard)</li>
            <li><code>1</code> = Coin wird nur 1x als negativ/positiv/alert eingetragen</li>
            <li><code>2</code> = Coin kann maximal 2x eingetragen werden</li>
            <li><code>5</code> = Coin kann maximal 5x eingetragen werden</li>
          </ul>
          <strong>Funktionsweise:</strong>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            <li>Jede Kategorie wird separat gezählt (negativ, positiv, alert)</li>
            <li>Nur aktive Einträge zählen (evaluierte Einträge zählen nicht mehr)</li>
            <li>Wenn Limit erreicht: Kein Eintrag in die Logs, keine Auswertung</li>
            <li>Coin wird weiterhin verarbeitet (für andere Modelle)</li>
          </ul>
        </Typography>
      </Alert>
    </Paper>
  );
};

export default MaxLogEntriesForm;
