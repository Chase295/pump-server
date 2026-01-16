-- Migration: n8n_send_mode von VARCHAR zu JSONB Array
-- Erlaubt mehrere Send-Modi gleichzeitig

-- 1. Erstelle temporäre Spalte
ALTER TABLE prediction_active_models
ADD COLUMN IF NOT EXISTS n8n_send_mode_new JSONB;

-- 2. Migriere bestehende Daten (konvertiere String zu Array)
UPDATE prediction_active_models
SET n8n_send_mode_new = CASE
    WHEN n8n_send_mode = 'all' THEN '["all"]'::jsonb
    WHEN n8n_send_mode = 'alerts_only' THEN '["alerts_only"]'::jsonb
    WHEN n8n_send_mode = 'positive_only' THEN '["positive_only"]'::jsonb
    WHEN n8n_send_mode = 'negative_only' THEN '["negative_only"]'::jsonb
    ELSE '["all"]'::jsonb
END
WHERE n8n_send_mode_new IS NULL;

-- 3. Setze Default für neue Einträge
ALTER TABLE prediction_active_models
ALTER COLUMN n8n_send_mode_new SET DEFAULT '["all"]'::jsonb;

-- 4. Entferne alte Spalte
ALTER TABLE prediction_active_models
DROP COLUMN IF EXISTS n8n_send_mode;

-- 5. Benenne neue Spalte um
ALTER TABLE prediction_active_models
RENAME COLUMN n8n_send_mode_new TO n8n_send_mode;

-- 6. Kommentar hinzufügen
COMMENT ON COLUMN prediction_active_models.n8n_send_mode IS 'Send-Mode als JSONB Array: ["all", "alerts_only", "positive_only", "negative_only"] - mehrere Modi können gleichzeitig aktiv sein';
