-- ============================================================
-- Migration: max_log_entries_per_coin Limits
-- Datum: 2026-01-14
-- Beschreibung: Fügt Einstellungen hinzu, um zu begrenzen wie oft ein Coin
--               pro Tag (negativ/positiv/alert) in die Logs eingetragen werden darf
-- ============================================================

-- Erweitere prediction_active_models Tabelle
ALTER TABLE prediction_active_models 
ADD COLUMN IF NOT EXISTS max_log_entries_per_coin_negative INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_log_entries_per_coin_positive INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_log_entries_per_coin_alert INTEGER DEFAULT 0;

-- Kommentare hinzufügen
COMMENT ON COLUMN prediction_active_models.max_log_entries_per_coin_negative IS 'Maximale Anzahl negativer Einträge pro Coin (0 = unbegrenzt)';
COMMENT ON COLUMN prediction_active_models.max_log_entries_per_coin_positive IS 'Maximale Anzahl positiver Einträge pro Coin (0 = unbegrenzt)';
COMMENT ON COLUMN prediction_active_models.max_log_entries_per_coin_alert IS 'Maximale Anzahl Alert-Einträge pro Coin (0 = unbegrenzt)';

-- CHECK Constraints für gültige Werte (0-1000 sollte ausreichen)
ALTER TABLE prediction_active_models
ADD CONSTRAINT chk_max_log_entries_negative CHECK (max_log_entries_per_coin_negative >= 0 AND max_log_entries_per_coin_negative <= 1000),
ADD CONSTRAINT chk_max_log_entries_positive CHECK (max_log_entries_per_coin_positive >= 0 AND max_log_entries_per_coin_positive <= 1000),
ADD CONSTRAINT chk_max_log_entries_alert CHECK (max_log_entries_per_coin_alert >= 0 AND max_log_entries_per_coin_alert <= 1000);

-- Index für schnelle Prüfung (coin_id + active_model_id + tag + status)
CREATE INDEX IF NOT EXISTS idx_model_predictions_coin_model_tag_status 
ON model_predictions(coin_id, active_model_id, tag, status) 
WHERE status = 'aktiv';
