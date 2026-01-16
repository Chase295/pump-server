-- ============================================================================
-- Migration: Add Send Ignored to n8n Setting
-- Datum: 2026-01-14
-- Beschreibung: Fügt Spalte hinzu um ignorierten Coins trotzdem an n8n zu senden
-- ============================================================================

ALTER TABLE prediction_active_models
ADD COLUMN IF NOT EXISTS send_ignored_to_n8n BOOLEAN DEFAULT false;

COMMENT ON COLUMN prediction_active_models.send_ignored_to_n8n IS 'Wenn true: Coins die aufgrund von Max-Log-Entries ignoriert werden, werden trotzdem an n8n gesendet (aber nicht in DB gespeichert)';
