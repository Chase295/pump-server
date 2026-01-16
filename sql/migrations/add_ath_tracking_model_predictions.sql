-- ============================================================
-- Migration: ATH-Tracking für model_predictions
-- Version: 1.0
-- Datum: 13. Januar 2026
-- ============================================================
-- Fügt ATH Highest und ATH Lowest Tracking hinzu

-- Füge ATH-Spalten hinzu
ALTER TABLE model_predictions 
ADD COLUMN IF NOT EXISTS ath_highest_pct NUMERIC(10, 4),  -- Höchster %-Wert während der Auswertungszeit
ADD COLUMN IF NOT EXISTS ath_lowest_pct NUMERIC(10, 4),   -- Niedrigster %-Wert während der Auswertungszeit
ADD COLUMN IF NOT EXISTS ath_highest_timestamp TIMESTAMP WITH TIME ZONE,  -- Zeitpunkt des höchsten Werts
ADD COLUMN IF NOT EXISTS ath_lowest_timestamp TIMESTAMP WITH TIME ZONE;   -- Zeitpunkt des niedrigsten Werts

-- Kommentare
COMMENT ON COLUMN model_predictions.ath_highest_pct IS 'Höchster %-Wert (Preisänderung) den der Coin während der Auswertungszeit erreicht hat';
COMMENT ON COLUMN model_predictions.ath_lowest_pct IS 'Niedrigster %-Wert (Preisänderung) den der Coin während der Auswertungszeit erreicht hat';
COMMENT ON COLUMN model_predictions.ath_highest_timestamp IS 'Zeitpunkt, an dem der höchste %-Wert erreicht wurde';
COMMENT ON COLUMN model_predictions.ath_lowest_timestamp IS 'Zeitpunkt, an dem der niedrigste %-Wert erreicht wurde';
