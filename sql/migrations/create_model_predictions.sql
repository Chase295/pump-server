-- ============================================================
-- Neue Tabelle: model_predictions
-- Version: 1.0
-- Datum: 13. Januar 2026
-- ============================================================
-- Ersetzt die komplexe Struktur aus predictions + alert_evaluations
-- durch EINE einfache Tabelle mit klaren Tags und Status

CREATE TABLE IF NOT EXISTS model_predictions (
    id BIGSERIAL PRIMARY KEY,
    
    -- Basis-Informationen
    coin_id VARCHAR(255) NOT NULL,
    model_id BIGINT NOT NULL,
    active_model_id BIGINT,
    
    -- Vorhersage-Ergebnis
    prediction INTEGER NOT NULL CHECK (prediction IN (0, 1)),  -- 0 = negativ, 1 = positiv
    probability NUMERIC(5, 4) NOT NULL CHECK (probability >= 0.0 AND probability <= 1.0),
    
    -- Tag (automatisch berechnet beim Speichern)
    tag VARCHAR(20) NOT NULL CHECK (tag IN ('negativ', 'positiv', 'alert')),
    -- Logik: 
    --   - probability < 0.5 → 'negativ'
    --   - probability >= 0.5 AND probability < alert_threshold → 'positiv'
    --   - probability >= alert_threshold → 'alert'
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'aktiv' CHECK (status IN ('aktiv', 'inaktiv')),
    -- 'aktiv' = wartet auf Auswertung (evaluation_timestamp noch nicht erreicht)
    -- 'inaktiv' = ausgewertet (Ergebnis eingetragen)
    
    -- Zeitstempel
    prediction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,  -- Wann wurde die Vorhersage gemacht
    evaluation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,  -- Wann soll ausgewertet werden (prediction_timestamp + future_minutes)
    evaluated_at TIMESTAMP WITH TIME ZONE,  -- Wann wurde tatsächlich ausgewertet
    
    -- Werte zum Zeitpunkt der Vorhersage
    price_close_at_prediction NUMERIC(20, 8),
    price_open_at_prediction NUMERIC(20, 8),
    price_high_at_prediction NUMERIC(20, 8),
    price_low_at_prediction NUMERIC(20, 8),
    market_cap_at_prediction NUMERIC(20, 2),
    volume_at_prediction NUMERIC(20, 2),
    phase_id_at_prediction INTEGER,
    
    -- Werte nach Auswertung (wenn status = 'inaktiv')
    price_close_at_evaluation NUMERIC(20, 8),
    price_open_at_evaluation NUMERIC(20, 8),
    price_high_at_evaluation NUMERIC(20, 8),
    price_low_at_evaluation NUMERIC(20, 8),
    market_cap_at_evaluation NUMERIC(20, 2),
    volume_at_evaluation NUMERIC(20, 2),
    phase_id_at_evaluation INTEGER,
    
    -- Ergebnis der Auswertung
    actual_price_change_pct NUMERIC(10, 4),  -- Tatsächliche Preisänderung in %
    evaluation_result VARCHAR(20) CHECK (evaluation_result IN ('success', 'failed', 'not_applicable')),  -- Nur für tag='alert'
    evaluation_note TEXT,  -- Zusätzliche Info
    
    -- Metadaten
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_model_predictions_coin_timestamp 
ON model_predictions(coin_id, prediction_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_model_predictions_model 
ON model_predictions(model_id, prediction_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_model_predictions_active_model 
ON model_predictions(active_model_id, prediction_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_model_predictions_status 
ON model_predictions(status) WHERE status = 'aktiv';

CREATE INDEX IF NOT EXISTS idx_model_predictions_tag 
ON model_predictions(tag);

CREATE INDEX IF NOT EXISTS idx_model_predictions_evaluation_timestamp 
ON model_predictions(evaluation_timestamp) WHERE status = 'aktiv';

-- Kommentare für Dokumentation
COMMENT ON TABLE model_predictions IS 'Speichert ALLE Vorhersagen mit klaren Tags (negativ/positiv/alert) und Status (aktiv/inaktiv)';
COMMENT ON COLUMN model_predictions.tag IS 'Automatisch berechnet: negativ (<50%), positiv (50%-threshold), alert (>=threshold)';
COMMENT ON COLUMN model_predictions.status IS 'aktiv = wartet auf Auswertung, inaktiv = ausgewertet';
