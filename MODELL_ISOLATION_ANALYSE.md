# 🔍 Analyse: Modell-Isolation & Potenzielle Probleme

## 📋 Aktueller Status

### ✅ Was IST isoliert:

1. **Modell-Konfiguration:**
   - Jedes Modell hat eigene Einstellungen (alert_threshold, n8n_webhook, ignore_settings, etc.)
   - Jedes Modell hat eigene `active_model_id` in der DB
   - Jedes Modell hat eigene Modell-Datei

2. **Coin-Ignore-Cache:**
   - `coin_scan_cache` ist pro Modell (`active_model_id`)
   - Jedes Modell ignoriert Coins unabhängig

3. **Vorhersagen-Speicherung:**
   - `model_predictions` speichert `active_model_id` - jede Vorhersage ist einem Modell zugeordnet

### ❌ Was NICHT isoliert ist:

1. **Event Handler (Vorhersagen):**
   ```python
   # In event_handler.py, Zeile 301
   results = await predict_coin_all_models(
       coin_id=coin_id,
       timestamp=timestamp,
       active_models=models_to_process,  # Alle Modelle zusammen
       pool=pool
   )
   ```
   - **Problem:** Alle Modelle verarbeiten denselben Coin zur gleichen Zeit
   - **Problem:** Sequenzielle Verarbeitung (`for model_config in active_models`)
   - **Problem:** Wenn ein Modell langsam ist, verzögert es die anderen (trotz async)

2. **Evaluation Job:**
   ```python
   # In evaluation_job.py, Zeile 31-62
   rows = await pool.fetch("""
       SELECT mp.*, ...
       FROM model_predictions mp
       WHERE mp.status = 'aktiv'
         AND mp.evaluation_timestamp <= NOW()
       ORDER BY mp.evaluation_timestamp ASC
       LIMIT $1
   """, batch_size)
   ```
   - **Problem:** Verarbeitet ALLE Modelle zusammen in einem Query
   - **Problem:** Keine Trennung nach `active_model_id`
   - **Problem:** Wenn Modell A 1000 Predictions hat und Modell B 10, werden sie zusammen verarbeitet
   - **Problem:** Ein langsames Modell kann andere blockieren

3. **coin_metrics Lesen:**
   - Alle Modelle lesen aus derselben `coin_metrics` Tabelle
   - Keine Isolation - aber das ist OK (nur Lesen)

4. **ATH-Tracker:**
   ```python
   # In ath_tracker_model_predictions.py
   rows = await pool.fetch("""
       SELECT mp.*, ...
       FROM model_predictions mp
       WHERE mp.status = 'aktiv'
       ...
   """)
   ```
   - **Problem:** Verarbeitet ALLE Modelle zusammen

## ⚠️ Potenzielle Probleme:

### 1. **Rückstau bei Vorhersagen:**
- Wenn Modell A sehr langsam ist (z.B. komplexe Features), verzögert es alle anderen Modelle
- Sequenzielle Verarbeitung bedeutet: Modell 1 → Modell 2 → Modell 3
- Wenn Modell 1 5 Sekunden braucht, müssen Modell 2 und 3 warten

### 2. **Rückstau bei Evaluierungen:**
- Evaluation Job verarbeitet alle Modelle zusammen
- Wenn Modell A 1000 ausstehende Evaluierungen hat, werden diese zuerst verarbeitet
- Modell B mit 10 Evaluierungen muss warten, bis Modell A fertig ist

### 3. **Ungleiche Ressourcen-Nutzung:**
- Ein Modell mit vielen Coins kann die DB belasten
- Andere Modelle werden dadurch verlangsamt

## 🔧 Lösungsvorschläge:

### Option 1: Parallele Verarbeitung im Event Handler (EMPFOHLEN)

```python
# Statt sequenziell:
for model_config in active_models:
    result = await predict_coin(...)

# Parallel:
tasks = [
    predict_coin(coin_id, timestamp, model_config, pool)
    for model_config in active_models
]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Vorteil:** Alle Modelle laufen parallel, kein Blockieren

### Option 2: Evaluation Job pro Modell (EMPFOHLEN)

```python
# Statt alle zusammen:
rows = await pool.fetch("""
    SELECT * FROM model_predictions
    WHERE status = 'aktiv'
    LIMIT 100
""")

# Pro Modell:
for active_model_id in active_model_ids:
    rows = await pool.fetch("""
        SELECT * FROM model_predictions
        WHERE status = 'aktiv'
          AND active_model_id = $1
        ORDER BY evaluation_timestamp ASC
        LIMIT 50  # Pro Modell
    """, active_model_id)
    # Verarbeite nur dieses Modell
```

**Vorteil:** Jedes Modell wird separat verarbeitet, kein Blockieren

### Option 3: Separate Queues pro Modell

- Jedes Modell bekommt eigene Queue
- Eigene Worker pro Modell
- Maximale Isolation

**Vorteil:** Vollständige Isolation, aber komplexer

## 📊 Empfehlung:

**Kurzfristig (einfach):**
1. ✅ Parallele Verarbeitung im Event Handler
2. ✅ Evaluation Job pro Modell (mit `active_model_id` Filter)

**Langfristig (optimal):**
1. Separate Queues pro Modell
2. Eigene Worker pro Modell
3. Priorisierung nach Modell
