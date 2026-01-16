-- ============================================================
-- Migration: ATH-Tracking für Alert Evaluations
-- Version: 1.0
-- Datum: 2026-01-11
-- ============================================================

-- Füge ATH-Spalten hinzu
ALTER TABLE alert_evaluations 
ADD COLUMN IF NOT EXISTS ath_price_change_pct NUMERIC(10, 4),  -- Höchste Preisänderung während Evaluierungszeit
ADD COLUMN IF NOT EXISTS ath_timestamp TIMESTAMP WITH TIME ZONE,  -- Zeitpunkt des ATH
ADD COLUMN IF NOT EXISTS ath_price_close NUMERIC(20, 8);  -- Preis zum ATH-Zeitpunkt

-- Kommentare
COMMENT ON COLUMN alert_evaluations.ath_price_change_pct IS 'Höchste Preisänderung (in %) während der Evaluierungszeit (alert_timestamp bis evaluation_timestamp)';
COMMENT ON COLUMN alert_evaluations.ath_timestamp IS 'Zeitpunkt, an dem der ATH erreicht wurde';
COMMENT ON COLUMN alert_evaluations.ath_price_close IS 'Preis (price_close) zum ATH-Zeitpunkt';

-- Erweitere Status-Check um 'non_alert'
ALTER TABLE alert_evaluations 
DROP CONSTRAINT IF EXISTS alert_evaluations_status_check;

ALTER TABLE alert_evaluations 
ADD CONSTRAINT alert_evaluations_status_check 
CHECK (status IN ('pending', 'success', 'failed', 'expired', 'not_applicable', 'non_alert'));
