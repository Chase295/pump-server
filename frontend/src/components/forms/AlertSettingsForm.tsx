/**
 * AlertSettingsForm Component
 * Erweiterte Formular für N8N Alert-Konfiguration mit React Hook Form + Zod
 */
import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Switch,
  FormControlLabel,
  RadioGroup,
  Radio,
  FormControl,
  FormLabel,
  Alert,
  Chip,
  Checkbox
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Webhook as WebhookIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import type { Model } from '../../types/model';

// Zod Schema für Form-Validierung
const alertSettingsSchema = z.object({
  n8n_webhook_url: z.union([
    z.string().url('Ungültige URL-Format'),
    z.literal('')
  ]).optional(),
  n8n_enabled: z.boolean(),
  n8n_send_mode: z.array(z.enum(['all', 'alerts_only', 'positive_only', 'negative_only'])).min(1, 'Mindestens ein Send-Modus muss ausgewählt sein'),
  alert_threshold: z.number().min(0).max(1),
  coin_filter_mode: z.enum(['all', 'whitelist']),
  coin_whitelist: z.array(z.string().min(1, 'Coin-Adresse darf nicht leer sein')).optional(),
  send_ignored_to_n8n: z.boolean()
});

type AlertSettingsFormData = z.infer<typeof alertSettingsSchema>;

interface AlertSettingsFormProps {
  model: Model;
  onChange?: (data: AlertSettingsFormData) => void;
  disabled?: boolean;
}

const AlertSettingsForm: React.FC<AlertSettingsFormProps> = ({
  model,
  onChange,
  disabled = false
}) => {
  const {
    control,
    watch,
    formState: { errors, isDirty, isValid }
  } = useForm<AlertSettingsFormData>({
    resolver: zodResolver(alertSettingsSchema),
    defaultValues: {
      n8n_webhook_url: model.n8n_webhook_url || '',
      n8n_enabled: model.n8n_enabled,
      // Konvertiere String zu Array (für Rückwärtskompatibilität)
      n8n_send_mode: Array.isArray(model.n8n_send_mode) 
        ? model.n8n_send_mode 
        : model.n8n_send_mode 
          ? [model.n8n_send_mode] 
          : ['all'],
      alert_threshold: model.alert_threshold,
      coin_filter_mode: model.coin_filter_mode || 'all',
      coin_whitelist: model.coin_whitelist || [],
      send_ignored_to_n8n: model.send_ignored_to_n8n || false
    },
    mode: 'onChange'
  });

  const coinFilterMode = watch('coin_filter_mode');
  const n8nEnabled = watch('n8n_enabled');

  // Form-Änderungen an Parent weitergeben
  React.useEffect(() => {
    if (onChange && isDirty) {
      const subscription = watch((data) => {
        onChange(data as AlertSettingsFormData);
      });
      return () => subscription.unsubscribe();
    }
  }, [watch, onChange, isDirty]);

  const sendModeOptions = [
    { value: 'all', label: 'Alle Vorhersagen senden' },
    { value: 'alerts_only', label: 'Nur Alerts senden (über Schwelle)' },
    { value: 'positive_only', label: 'Nur positive Vorhersagen' },
    { value: 'negative_only', label: 'Nur negative Vorhersagen' },
  ];

  return (
    <Card variant="outlined">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <NotificationsIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            N8N Webhook & Alert Einstellungen
          </Typography>
          {isDirty && (
            <Chip
              label="Ungespeicherte Änderungen"
              size="small"
              color="warning"
              sx={{ ml: 'auto' }}
            />
          )}
        </Box>

        {/* N8N Webhook URL */}
        <Controller
          name="n8n_webhook_url"
          control={control}
          render={({ field, fieldState: { error } }) => (
            <TextField
              {...field}
              label="N8N Webhook URL"
              fullWidth
              margin="normal"
              placeholder="https://your-n8n-instance/webhook/..."
              helperText={error ? error.message : "Leer lassen um globale URL zu verwenden"}
              error={!!error}
              disabled={disabled}
              InputProps={{
                startAdornment: <WebhookIcon sx={{ mr: 1, color: 'action.active' }} />
              }}
            />
          )}
        />

        {/* N8N Aktiviert */}
        <Controller
          name="n8n_enabled"
          control={control}
          render={({ field }) => (
            <FormControlLabel
              control={
                <Switch
                  {...field}
                  checked={field.value}
                  disabled={disabled}
                />
              }
              label="N8N Benachrichtigungen aktivieren"
              sx={{ mt: 2, mb: 2 }}
            />
          )}
        />

        {/* Send-Modus - Mehrfachauswahl */}
        {n8nEnabled && (
          <Controller
            name="n8n_send_mode"
            control={control}
            render={({ field, fieldState: { error } }) => (
              <Box sx={{ mt: 2, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ mb: 1 }}>
                  Send-Modus (mehrere auswählbar):
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {sendModeOptions.map((option) => {
                    const optionValue = option.value as 'all' | 'alerts_only' | 'positive_only' | 'negative_only';
                    return (
                      <FormControlLabel
                        key={option.value}
                        control={
                          <Checkbox
                            checked={field.value?.includes(optionValue) || false}
                            onChange={(e) => {
                              const currentValue = field.value || [];
                              if (e.target.checked) {
                                // Füge hinzu, wenn nicht bereits vorhanden
                                if (!currentValue.includes(optionValue)) {
                                  field.onChange([...currentValue, optionValue]);
                                }
                              } else {
                                // Entferne aus Array
                                field.onChange(currentValue.filter((v) => v !== optionValue));
                              }
                            }}
                            disabled={disabled}
                          />
                        }
                        label={option.label}
                      />
                    );
                  })}
                </Box>
                {error && (
                  <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>
                    {error.message}
                  </Typography>
                )}
                {!error && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Wählen Sie einen oder mehrere Send-Modi aus
                  </Typography>
                )}
              </Box>
            )}
          />
        )}

        {/* Send Ignored to n8n */}
        {n8nEnabled && (
          <Controller
            name="send_ignored_to_n8n"
            control={control}
            render={({ field }) => (
              <FormControlLabel
                control={
                  <Switch
                    checked={field.value || false}
                    onChange={field.onChange}
                    disabled={disabled}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">
                      Auch ignorierten Coins an n8n senden
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Coins die aufgrund von Max-Log-Entries ignoriert werden, werden trotzdem an n8n gesendet (aber nicht in DB gespeichert)
                    </Typography>
                  </Box>
                }
                sx={{ mt: 2 }}
              />
            )}
          />
        )}

        {/* Alert-Schwelle */}
        <Box sx={{ mt: 3, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <FilterIcon sx={{ mr: 1, fontSize: 16 }} />
            Alert-Schwelle (%)
          </Typography>
          <Controller
            name="alert_threshold"
            control={control}
            render={({ field, fieldState: { error } }) => {
              // Konvertiere zwischen Prozent (1-99) und Dezimal (0.01-0.99)
              const percentValue = Math.round((field.value || 0) * 100);
              
              return (
                <TextField
                  type="number"
                  fullWidth
                  label="Alert-Schwelle in Prozent"
                  value={percentValue}
                  onChange={(e) => {
                    const percent = Number(e.target.value);
                    if (percent >= 1 && percent <= 99) {
                      field.onChange(percent / 100);
                    } else if (percent === 0 || percent === 100) {
                      // Erlaube 0% und 100% für Edge-Cases
                      field.onChange(percent / 100);
                    }
                  }}
                  onBlur={field.onBlur}
                  inputRef={field.ref}
                  error={!!error}
                  helperText={error ? error.message : `Wert zwischen 1-99% (aktuell: ${percentValue}%)`}
                  disabled={disabled}
                  inputProps={{
                    min: 1,
                    max: 99,
                    step: 1
                  }}
                  sx={{ mt: 1 }}
                />
              );
            }}
          />
        </Box>

        {/* Coin-Filter */}
        <FormControl component="fieldset" margin="normal" fullWidth>
          <FormLabel component="legend" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <FilterIcon sx={{ mr: 1, fontSize: 16 }} />
            Coin-Filter Modus
          </FormLabel>
          <Controller
            name="coin_filter_mode"
            control={control}
            render={({ field }) => (
              <RadioGroup {...field} row>
                <FormControlLabel
                  value="all"
                  control={<Radio disabled={disabled} />}
                  label="Alle Coins"
                />
                <FormControlLabel
                  value="whitelist"
                  control={<Radio disabled={disabled} />}
                  label="Whitelist (nur ausgewählte Coins)"
                />
              </RadioGroup>
            )}
          />
        </FormControl>

        {/* Coin Whitelist */}
        {coinFilterMode === 'whitelist' && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Coin-Whitelist (eine Adresse pro Zeile)
            </Typography>
            <Controller
              name="coin_whitelist"
              control={control}
              render={({ field, fieldState: { error } }) => (
                <Box>
                  <TextField
                    {...field}
                    multiline
                    rows={4}
                    fullWidth
                    placeholder="Coin-Adressen (z.B. ABCxyz123...)"
                    disabled={disabled}
                    error={!!error}
                    helperText={error ? error.message : `${field.value?.length || 0} Coins in der Whitelist`}
                    value={field.value ? field.value.join('\n') : ''}
                    onChange={(e) => {
                      const lines = e.target.value.split('\n').map(line => line.trim()).filter(line => line.length > 0);
                      field.onChange(lines);
                    }}
                  />
                  {field.value && field.value.length > 0 && (
                    <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {field.value.map((coin, index) => (
                        <Chip
                          key={index}
                          label={coin}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              )}
            />
          </Box>
        )}

        {/* Validierungs-Hinweise */}
        {!isValid && Object.keys(errors).length > 0 && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Bitte korrigieren Sie die Fehler im Formular.
          </Alert>
        )}

        {isDirty && isValid && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Ihre Änderungen sind bereit zum Speichern.
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default AlertSettingsForm;