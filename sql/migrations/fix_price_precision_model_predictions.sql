-- ============================================================================
-- Migration: Fix Price Precision in model_predictions
-- Datum: 2026-01-14
-- Beschreibung: Erhöht die Präzision der price-Spalten von NUMERIC(20, 8) auf NUMERIC(20, 12)
--               um sehr kleine Preise (z.B. 2.8e-08) korrekt speichern zu können
-- ============================================================================

-- Erhöhe Präzision für alle price-Spalten in model_predictions
ALTER TABLE model_predictions
    ALTER COLUMN price_close_at_prediction TYPE NUMERIC(20, 12),
    ALTER COLUMN price_open_at_prediction TYPE NUMERIC(20, 12),
    ALTER COLUMN price_high_at_prediction TYPE NUMERIC(20, 12),
    ALTER COLUMN price_low_at_prediction TYPE NUMERIC(20, 12),
    ALTER COLUMN price_close_at_evaluation TYPE NUMERIC(20, 12),
    ALTER COLUMN price_open_at_evaluation TYPE NUMERIC(20, 12),
    ALTER COLUMN price_high_at_evaluation TYPE NUMERIC(20, 12),
    ALTER COLUMN price_low_at_evaluation TYPE NUMERIC(20, 12);

COMMENT ON COLUMN model_predictions.price_close_at_prediction IS 'Preis zum Zeitpunkt der Vorhersage (NUMERIC(20, 12) für hohe Präzision bei sehr kleinen Preisen)';
COMMENT ON COLUMN model_predictions.price_close_at_evaluation IS 'Preis zum Zeitpunkt der Auswertung (NUMERIC(20, 12) für hohe Präzision bei sehr kleinen Preisen)';
