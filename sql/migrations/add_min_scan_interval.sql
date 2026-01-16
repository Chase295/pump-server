-- Migration: min_scan_interval_seconds zu prediction_active_models hinzufügen
-- Datum: 2026-01-11
-- Zweck: Verhindert, dass derselbe Coin innerhalb von X Sekunden erneut gescannt wird

ALTER TABLE prediction_active_models
ADD COLUMN IF NOT EXISTS min_scan_interval_seconds INTEGER DEFAULT 20 
  CHECK (min_scan_interval_seconds >= 0 AND min_scan_interval_seconds <= 86400);

-- Kommentar hinzufügen
COMMENT ON COLUMN prediction_active_models.min_scan_interval_seconds IS 
  'Minimaler Zeitabstand zwischen zwei Scans desselben Coins (in Sekunden). 0 = deaktiviert. Max: 86400 (24h)';

-- Index für Performance (optional, falls häufig gefiltert wird)
CREATE INDEX IF NOT EXISTS idx_active_models_min_scan_interval 
  ON prediction_active_models(min_scan_interval_seconds) 
  WHERE min_scan_interval_seconds > 0;
