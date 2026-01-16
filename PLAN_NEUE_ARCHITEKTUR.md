# Plan: Neue, einfache Architektur für Predictions & Logs

## 🎯 Ziel
**EINE einfache Tabelle für ALLE Vorhersagen mit klaren Tags und Status**

## 📊 Aktuelle Probleme

### Was ist jetzt falsch:
1. **Zwei Tabellen** (`predictions` + `alert_evaluations`) → zu komplex
2. **Verschachtelte Logik** in `create_alert_if_needed` → schwer zu verstehen
3. **UNION-Queries** zwischen beiden Tabellen → langsam und fehleranfällig
4. **Mehrere Status-Werte** (pending, success, failed, expired, non_alert) → verwirrend
5. **Komplexe Parameter-Nummerierung** in SQL-Queries → fehleranfällig

### Was der Benutzer will:
- ✅ **ALLE Coins** die durch das Model gehen → in DB
- ✅ **Klare Tags**: `positiv`, `negativ`, `alert`
- ✅ **Einfacher Status**: `aktiv` (wartet auf Auswertung) / `inaktiv` (ausgewertet)
- ✅ **Automatische Auswertung** nach x Minuten → Ergebnis eintragen, auf `inaktiv` setzen

---

## 🏗️ Neue Architektur

### 1. EINE Tabelle: `model_predictions`

```sql
CREATE TABLE model_predictions (
    id BIGSERIAL PRIMARY KEY,
    
    -- Basis-Informationen
    coin_id VARCHAR(255) NOT NULL,
    model_id BIGINT NOT NULL,
    active_model_id BIGINT,
    
    -- Vorhersage-Ergebnis
    prediction INTEGER NOT NULL CHECK (prediction IN (0, 1)),  -- 0 = negativ, 1 = positiv
    probability NUMERIC(5, 4) NOT NULL,  -- 0.0 - 1.0
    
    -- Tag (automatisch berechnet)
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
    evaluation_result VARCHAR(20),  -- 'success', 'failed', 'not_applicable' (nur für tag='alert')
    evaluation_note TEXT,  -- Zusätzliche Info
    
    -- Metadaten
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indizes
CREATE INDEX idx_model_predictions_coin_timestamp 
ON model_predictions(coin_id, prediction_timestamp DESC);

CREATE INDEX idx_model_predictions_model 
ON model_predictions(model_id, prediction_timestamp DESC);

CREATE INDEX idx_model_predictions_status 
ON model_predictions(status) WHERE status = 'aktiv';

CREATE INDEX idx_model_predictions_tag 
ON model_predictions(tag);

CREATE INDEX idx_model_predictions_evaluation_timestamp 
ON model_predictions(evaluation_timestamp) WHERE status = 'aktiv';
```

---

## 🔄 Workflow

### Schritt 1: Vorhersage erstellen
```
1. Coin kommt durch Event-Handler
2. Model macht Vorhersage → prediction (0/1), probability (0.0-1.0)
3. Berechne Tag:
   - probability < 0.5 → tag = 'negativ'
   - probability >= 0.5 AND probability < alert_threshold → tag = 'positiv'
   - probability >= alert_threshold → tag = 'alert'
4. Berechne evaluation_timestamp = prediction_timestamp + future_minutes
5. Speichere in model_predictions:
   - status = 'aktiv'
   - tag = (berechnet)
   - evaluation_timestamp = (berechnet)
```

### Schritt 2: Auswertung (Background-Job)
```
1. Suche alle Einträge mit:
   - status = 'aktiv'
   - evaluation_timestamp <= NOW()
2. Für jeden Eintrag:
   a. Hole aktuelle Coin-Metriken
   b. Berechne actual_price_change_pct
   c. Bestimme evaluation_result:
      - Wenn tag = 'alert' UND prediction = 1:
        * actual_price_change_pct >= target → 'success'
        * actual_price_change_pct < target → 'failed'
      - Wenn tag = 'negativ' oder 'positiv':
        * 'not_applicable' (nur für Statistiken)
   d. Update Eintrag:
      - status = 'inaktiv'
      - evaluated_at = NOW()
      - evaluation_result = (berechnet)
      - actual_price_change_pct = (berechnet)
      - price_*_at_evaluation = (aktuelle Werte)
```

---

## 📝 Implementierungs-Schritte

### Phase 1: Datenbank-Migration
1. ✅ Erstelle neue Tabelle `model_predictions`
2. ✅ Migriere bestehende Daten von `predictions` + `alert_evaluations` → `model_predictions`
3. ✅ Erstelle Indizes
4. ⚠️ **WICHTIG**: Alte Tabellen behalten (für Rollback), aber nicht mehr verwenden

### Phase 2: Backend-Anpassungen

#### 2.1 Event-Handler (`event_handler.py`)
```python
# Statt save_prediction() → save_model_prediction()

async def save_model_prediction(
    coin_id: str,
    model_id: int,
    active_model_id: Optional[int],
    prediction: int,
    probability: float,
    alert_threshold: float,
    future_minutes: int,
    prediction_timestamp: datetime,
    metrics: Dict[str, Any]
) -> int:
    """
    Speichert Vorhersage in model_predictions.
    Berechnet automatisch tag und evaluation_timestamp.
    """
    # Berechne tag
    if probability < 0.5:
        tag = 'negativ'
    elif probability < alert_threshold:
        tag = 'positiv'
    else:
        tag = 'alert'
    
    # Berechne evaluation_timestamp
    evaluation_timestamp = prediction_timestamp + timedelta(minutes=future_minutes)
    
    # Speichere in DB
    prediction_id = await pool.fetchval("""
        INSERT INTO model_predictions (
            coin_id, model_id, active_model_id,
            prediction, probability, tag, status,
            prediction_timestamp, evaluation_timestamp,
            price_close_at_prediction, price_open_at_prediction,
            price_high_at_prediction, price_low_at_prediction,
            market_cap_at_prediction, volume_at_prediction,
            phase_id_at_prediction
        ) VALUES (
            $1, $2, $3, $4, $5, $6, 'aktiv',
            $7, $8, $9, $10, $11, $12, $13, $14, $15
        )
        RETURNING id
    """, ...)
    
    return prediction_id
```

#### 2.2 Auswertungs-Job (`evaluation_job.py`)
```python
async def evaluate_pending_predictions(batch_size: int = 100):
    """
    Prüft alle 'aktiv' Einträge und wertet sie aus.
    """
    pool = await get_pool()
    
    # Hole alle ausstehenden Einträge
    rows = await pool.fetch("""
        SELECT * FROM model_predictions
        WHERE status = 'aktiv'
          AND evaluation_timestamp <= NOW()
        ORDER BY evaluation_timestamp ASC
        LIMIT $1
    """, batch_size)
    
    for row in rows:
        # Hole aktuelle Metriken
        current_metrics = await get_coin_metrics_at_time(
            row['coin_id'], 
            row['evaluation_timestamp']
        )
        
        # Berechne Ergebnis
        actual_change = calculate_price_change(
            row['price_close_at_prediction'],
            current_metrics['price_close']
        )
        
        # Bestimme evaluation_result
        if row['tag'] == 'alert' and row['prediction'] == 1:
            target_change = row['model'].get('price_change_percent', 30.0)
            if actual_change >= target_change:
                evaluation_result = 'success'
            else:
                evaluation_result = 'failed'
        else:
            evaluation_result = 'not_applicable'
        
        # Update Eintrag
        await pool.execute("""
            UPDATE model_predictions
            SET status = 'inaktiv',
                evaluated_at = NOW(),
                evaluation_result = $1,
                actual_price_change_pct = $2,
                price_close_at_evaluation = $3,
                price_open_at_evaluation = $4,
                price_high_at_evaluation = $5,
                price_low_at_evaluation = $6,
                market_cap_at_evaluation = $7,
                volume_at_evaluation = $8,
                phase_id_at_evaluation = $9,
                updated_at = NOW()
            WHERE id = $10
        """, evaluation_result, actual_change, ...)
```

#### 2.3 API-Endpoint (`routes.py`)
```python
@router.get("/api/model-predictions")
async def get_model_predictions(
    model_id: Optional[int] = None,
    tag: Optional[str] = None,  # 'negativ', 'positiv', 'alert'
    status: Optional[str] = None,  # 'aktiv', 'inaktiv'
    limit: int = 100,
    offset: int = 0
):
    """
    Hole alle Vorhersagen - EINFACH, ohne UNION-Queries!
    """
    pool = await get_pool()
    
    conditions = []
    params = []
    param_idx = 1
    
    if model_id:
        conditions.append(f"model_id = ${param_idx}")
        params.append(model_id)
        param_idx += 1
    
    if tag:
        conditions.append(f"tag = ${param_idx}")
        params.append(tag)
        param_idx += 1
    
    if status:
        conditions.append(f"status = ${param_idx}")
        params.append(status)
        param_idx += 1
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT * FROM model_predictions
        {where_clause}
        ORDER BY prediction_timestamp DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    
    params.extend([limit, offset])
    rows = await pool.fetch(query, *params)
    
    return {
        "predictions": [dict(row) for row in rows],
        "total": await pool.fetchval(f"SELECT COUNT(*) FROM model_predictions {where_clause}", *params[:-2])
    }
```

### Phase 3: Frontend-Anpassungen

#### 3.1 ModelLogs.tsx
```typescript
// Statt komplexer UNION-Queries → einfache Filter

const { data: predictionsData } = useQuery({
  queryKey: ['model-predictions', id, filters],
  queryFn: () => predictionsApi.getForModel(id, {
    tag: filters.tag,  // 'negativ' | 'positiv' | 'alert' | undefined
    status: filters.status,  // 'aktiv' | 'inaktiv' | undefined
    limit: 100,
    offset: 0
  })
});

// Anzeige:
// - Tag als Chip (negativ=rot, positiv=grün, alert=orange)
// - Status als Badge (aktiv=blau, inaktiv=grau)
// - Keine komplexe Logik mehr!
```

---

## ✅ Vorteile der neuen Architektur

1. **EINE Tabelle** → keine UNION-Queries mehr
2. **Klare Tags** → `negativ`, `positiv`, `alert` (automatisch berechnet)
3. **Einfacher Status** → `aktiv` / `inaktiv`
4. **Einfache Queries** → keine komplexe Parameter-Nummerierung
5. **Einfache Logik** → tag wird beim Speichern berechnet
6. **Einfache Auswertung** → Background-Job prüft nur `status='aktiv'` + `evaluation_timestamp <= NOW()`
7. **Einfache API** → ein Endpoint, einfache Filter

---

## 🚀 Migrations-Plan

### Schritt 1: Neue Tabelle erstellen
```sql
-- Migration: create_model_predictions.sql
CREATE TABLE model_predictions (...);
CREATE INDEX ...;
```

### Schritt 2: Daten migrieren
```python
# Migration-Script: migrate_to_model_predictions.py
async def migrate():
    # Hole alle predictions + alert_evaluations
    # Kombiniere zu model_predictions
    # Berechne tag basierend auf probability + alert_threshold
    # Setze status basierend auf evaluation_timestamp
```

### Schritt 3: Backend umstellen
- Event-Handler: `save_prediction()` → `save_model_prediction()`
- Auswertungs-Job: `evaluate_pending_alerts()` → `evaluate_pending_predictions()`
- API: `get_alerts()` → `get_model_predictions()`

### Schritt 4: Frontend umstellen
- ModelLogs.tsx: Neue API verwenden
- Filter: tag + status (statt komplexe Logik)

### Schritt 5: Alte Tabellen entfernen (nach Test)
```sql
-- Nur nach erfolgreichem Test!
DROP TABLE alert_evaluations;
DROP TABLE predictions;  -- Oder behalten für Historische Daten
```

---

## 📋 Checkliste

- [ ] Phase 1: Datenbank-Migration
  - [ ] Neue Tabelle `model_predictions` erstellen
  - [ ] Indizes erstellen
  - [ ] Migrations-Script schreiben
  - [ ] Test-Migration durchführen

- [ ] Phase 2: Backend-Anpassungen
  - [ ] `save_model_prediction()` Funktion erstellen
  - [ ] Event-Handler anpassen
  - [ ] Auswertungs-Job anpassen
  - [ ] API-Endpoint anpassen
  - [ ] Tests schreiben

- [ ] Phase 3: Frontend-Anpassungen
  - [ ] API-Client anpassen
  - [ ] ModelLogs.tsx umstellen
  - [ ] Filter anpassen
  - [ ] UI-Tests

- [ ] Phase 4: Deployment
  - [ ] Migration auf Produktion
  - [ ] Backend deployen
  - [ ] Frontend deployen
  - [ ] Monitoring

---

## 🎯 Zusammenfassung

**Vorher (komplex):**
- 2 Tabellen (`predictions` + `alert_evaluations`)
- UNION-Queries
- Komplexe Status-Logik
- Verschachtelte Funktionen

**Nachher (einfach):**
- 1 Tabelle (`model_predictions`)
- Einfache SELECT-Queries
- Klare Tags (negativ/positiv/alert)
- Einfacher Status (aktiv/inaktiv)
- Einfache Logik

**Ergebnis:**
- ✅ Alle Coins werden gespeichert
- ✅ Klare Tags
- ✅ Einfache Anzeige
- ✅ Einfache Auswertung
- ✅ Keine komplexen Queries mehr
