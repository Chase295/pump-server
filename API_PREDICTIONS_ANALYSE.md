# 📊 Analyse: API-Vorhersagen & Coin-Metrics-Deaktivierung

## ✅ Antwort auf deine Frage

**JA!** Coins, die via API (`/api/predict`) an ein Modell geschickt werden:
1. ✅ **Werden in den Logs gespeichert** (`model_predictions` Tabelle)
2. ✅ **Werden automatisch ausgewertet** (Evaluation Job verarbeitet alle `status = 'aktiv'` Einträge)
3. ✅ **Erscheinen in der Web-UI** (Log-Seite)

## 🔍 Aktueller Status

### API-Vorhersagen (`/api/predict`)

**Was passiert:**
1. API-Endpoint macht Vorhersage mit Modell(en)
2. Speichert in `model_predictions` Tabelle (Zeile 954 in `routes.py`)
3. Status: `'aktiv'` (wird später ausgewertet)
4. Evaluation Job findet und verarbeitet automatisch

**Code-Beweis:**
```python
# In routes.py, Zeile 954
await save_model_prediction(
    coin_id=request.coin_id,
    prediction_timestamp=timestamp,
    model_id=result['model_id'],
    active_model_id=model_id,
    prediction=prediction,
    probability=probability,
    alert_threshold=alert_threshold,
    future_minutes=future_minutes,
    metrics=metrics,
    phase_id_at_time=phase_id,
    pool=pool
)
```

**Evaluation Job verarbeitet:**
```python
# In evaluation_job.py, Zeile 76-80
WHERE mp.status = 'aktiv'
  AND mp.active_model_id = $1
  AND mp.evaluation_timestamp <= NOW()
```

→ **Alle API-Vorhersagen werden automatisch ausgewertet!**

## 🎯 Coin-Metrics-Verarbeitung deaktivieren

### Option 1: Whitelist-Modus (AKTUELL MÖGLICH)

**So geht's:**
1. Setze `coin_filter_mode = 'whitelist'`
2. Lasse `coin_whitelist = []` (leer)
3. → Modell verarbeitet **KEINE** Coins aus `coin_metrics`
4. → Nur API-Vorhersagen werden verarbeitet

**Code-Beweis:**
```python
# In event_handler.py, Zeile 241-245
if coin_filter_mode == 'whitelist':
    if not coin_whitelist or coin_id not in coin_whitelist:
        logger.debug(f"🚫 Coin {coin_id[:8]}... nicht in Whitelist von Modell {model_id} - überspringe")
        total_ignored += 1
        continue
```

**Vorteil:**
- ✅ Funktioniert bereits jetzt
- ✅ Keine Code-Änderung nötig

**Nachteil:**
- ⚠️ Nicht ganz intuitiv (leere Whitelist = deaktiviert)

### Option 2: Neue Einstellung `process_coin_metrics` (EMPFOHLEN)

**Vorschlag:**
- Neue Spalte `process_coin_metrics BOOLEAN DEFAULT true`
- Wenn `false`: Modell verarbeitet keine Coins aus `coin_metrics`
- Nur API-Vorhersagen werden verarbeitet

**Vorteil:**
- ✅ Klar und intuitiv
- ✅ Explizite Kontrolle

**Nachteil:**
- ⚠️ Benötigt Migration und Code-Änderung

## 📋 Zusammenfassung

| Frage | Antwort |
|-------|---------|
| API-Vorhersagen in Logs? | ✅ JA |
| API-Vorhersagen ausgewertet? | ✅ JA |
| Coin-Metrics deaktivierbar? | ✅ JA (via Whitelist) |
| Nur API-Vorhersagen möglich? | ✅ JA (Whitelist leer lassen) |

## 🚀 Empfehlung

**Für jetzt:**
- Verwende `coin_filter_mode = 'whitelist'` mit leerer Whitelist
- Funktioniert sofort, keine Änderung nötig

**Für später (optional):**
- Neue Einstellung `process_coin_metrics: bool` für bessere Klarheit
