# Pump Server - Datenbank-Schema Dokumentation

**Version:** 2.0
**Datum:** Februar 2026
**Datenbank:** PostgreSQL

---

## Uebersicht

Dieses Schema erweitert die bestehende `crypto` Datenbank um Tabellen fuer den Pump Server. **Wichtig:** Es werden **KEINE** bestehenden Tabellen geaendert, nur neue Tabellen hinzugefuegt.

### Tabellen:
1. `prediction_active_models` - Verwaltung aktiver Modelle im Prediction Service
2. `predictions` - Speicherung aller Vorhersagen (Legacy)
3. `prediction_webhook_log` - Logging von n8n Webhook-Aufrufen
4. `model_predictions` - Vorhersagen mit Tags, Status und Evaluation (aktuelle Architektur)
5. `alert_evaluations` - Alert-Auswertungen mit Preishistorie
6. `coin_scan_cache` - Cache fuer Coin-Ignore-Logik

### Trigger:
- `coin_metrics_insert_trigger` - LISTEN/NOTIFY fuer Echtzeit-Events

---

## Trigger: `coin_metrics_insert_trigger`

### Was macht der Trigger?

Der Trigger ueberwacht automatisch alle neuen Eintraege in der `coin_metrics` Tabelle und sendet eine Echtzeit-Benachrichtigung an den Pump Server.

### Funktionsweise:

1. **Trigger-Funktion:** `notify_coin_metrics_insert()`
   - Wird automatisch bei jedem `INSERT` in `coin_metrics` ausgefuehrt
   - Erstellt eine JSON-Nachricht mit `mint`, `timestamp`, `phase_id`
   - Sendet ueber PostgreSQL `pg_notify()`

2. **Trigger-Definition:**
   ```sql
   CREATE TRIGGER coin_metrics_insert_trigger
       AFTER INSERT ON coin_metrics
       FOR EACH ROW
       EXECUTE FUNCTION notify_coin_metrics_insert();
   ```

### LISTEN/NOTIFY

PostgreSQL LISTEN/NOTIFY ist ein Push-Mechanismus fuer Echtzeit-Kommunikation:
- Channel: `coin_metrics_insert`
- Latenz: < 100ms
- Fallback: Polling alle 30 Sekunden

---

## Tabelle 1: `prediction_active_models`

### Zweck
Verwaltet alle aktiven Modelle im Prediction Service. Diese Tabelle ist lokal und unabhaengig von `ml_models` im Training Service.

### Felder:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | BIGSERIAL | Primaerschluessel (lokal) |
| `model_id` | BIGINT | Referenz zu `ml_models.id` (kein FK!) |
| `model_name` | VARCHAR(255) | Name des Modells |
| `model_type` | VARCHAR(50) | `random_forest` oder `xgboost` |
| `target_variable` | VARCHAR(100) | Ziel-Variable (z.B. `price_close`) |
| `target_operator` | VARCHAR(10) | Operator (`>`, `<`, `>=`, `<=`, `=`) oder NULL |
| `target_value` | NUMERIC(20,2) | Ziel-Wert oder NULL |
| `future_minutes` | INTEGER | Minuten in die Zukunft |
| `price_change_percent` | NUMERIC(10,4) | Prozentuale Aenderung |
| `target_direction` | VARCHAR(10) | `up` oder `down` |
| `features` | JSONB | Liste der Features (Array) |
| `phases` | JSONB | Liste der Phasen (Array) oder NULL |
| `params` | JSONB | Modell-Parameter (Object) |
| `local_model_path` | TEXT | Pfad zur lokalen `.pkl` Datei |
| `model_file_url` | TEXT | URL zum Download (optional) |
| `is_active` | BOOLEAN | Ist Modell aktiv? (Default: `true`) |
| `last_prediction_at` | TIMESTAMP | Letzte Vorhersage |
| `total_predictions` | BIGINT | Anzahl Vorhersagen (Counter) |
| `downloaded_at` | TIMESTAMP | Wann wurde Modell heruntergeladen? |
| `activated_at` | TIMESTAMP | Wann wurde Modell aktiviert? |
| `created_at` | TIMESTAMP | Erstellt am |
| `updated_at` | TIMESTAMP | Aktualisiert am |
| `custom_name` | VARCHAR(255) | Optional: Lokaler Name (falls umbenannt) |
| **Alert-Konfiguration** | | |
| `alert_threshold` | NUMERIC(5,4) | Alert-Schwellenwert (Default: 0.7) |
| `n8n_webhook_url` | TEXT | n8n Webhook-URL |
| `n8n_enabled` | BOOLEAN | Webhook aktiviert? |
| `n8n_send_mode` | JSONB | Send-Modus als Array (`["alerts_only"]`) |
| `n8n_last_status` | VARCHAR(20) | Letzter Webhook-Status |
| `n8n_last_error` | TEXT | Letzter Webhook-Fehler |
| `coin_filter_mode` | VARCHAR(20) | `all` oder `whitelist` |
| `coin_whitelist` | JSONB | Liste erlaubter Coin-Adressen |
| **Ignore-Einstellungen** | | |
| `ignore_bad_seconds` | INTEGER | Sekunden: negative Coins ignorieren (Default: 0) |
| `ignore_positive_seconds` | INTEGER | Sekunden: positive Coins ignorieren (Default: 0) |
| `ignore_alert_seconds` | INTEGER | Sekunden: Alert-Coins ignorieren (Default: 0) |
| `send_ignored_to_n8n` | BOOLEAN | Ignorierte trotzdem an n8n senden? |
| `min_scan_interval_seconds` | INTEGER | Minimaler Scan-Intervall |
| **Max-Log-Entries** | | |
| `max_log_entries_per_coin_negative` | INTEGER | Max negative Eintraege pro Coin (0=unbegrenzt) |
| `max_log_entries_per_coin_positive` | INTEGER | Max positive Eintraege pro Coin (0=unbegrenzt) |
| `max_log_entries_per_coin_alert` | INTEGER | Max Alert-Eintraege pro Coin (0=unbegrenzt) |
| **Performance-Metriken** | | |
| `training_accuracy` | NUMERIC(10,6) | Training Accuracy |
| `training_f1` | NUMERIC(10,6) | Training F1 Score |
| `training_precision` | NUMERIC(10,6) | Training Precision |
| `training_recall` | NUMERIC(10,6) | Training Recall |
| `training_roc_auc` | NUMERIC(10,6) | Training ROC-AUC |
| `training_mcc` | NUMERIC(10,6) | Training MCC |

### Constraints:

- **`chk_model_type`:** Nur `random_forest` oder `xgboost`
- **`chk_operator`:** Nur gueltige Operatoren oder NULL
- **`chk_direction`:** Nur `up`, `down` oder NULL
- **`UNIQUE(model_id)`:** Ein Modell kann nur einmal aktiv sein

### Indizes:

| Index | Spalten | Zweck |
|-------|---------|-------|
| `idx_active_models_active` | `is_active` (WHERE true) | Schnelle Abfrage aktiver Modelle |
| `idx_active_models_model_id` | `model_id` | Suche nach Modell-ID |
| `idx_active_models_custom_name` | `custom_name` (WHERE NOT NULL) | Suche nach umbenannten Modellen |
| `idx_active_models_coin_filter` | `coin_filter_mode` | Filter nach Coin-Modus |

---

## Tabelle 2: `predictions`

### Zweck
Speichert alle Vorhersagen (Legacy-Tabelle, wird weiterhin befuellt).

### Felder:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | BIGSERIAL | Primaerschluessel |
| `coin_id` | VARCHAR(255) | Coin-ID (mint) |
| `data_timestamp` | TIMESTAMP | Zeitstempel der Daten |
| `model_id` | BIGINT | Referenz zu `ml_models.id` (kein FK!) |
| `active_model_id` | BIGINT | FK zu `prediction_active_models.id` |
| `prediction` | INTEGER | `0` (negativ) oder `1` (positiv) |
| `probability` | NUMERIC(5,4) | Wahrscheinlichkeit (0.0-1.0) |
| `phase_id_at_time` | INTEGER | Phase zum Zeitpunkt der Vorhersage |
| `features` | JSONB | Features (optional) |
| `prediction_duration_ms` | INTEGER | Dauer in Millisekunden |
| `created_at` | TIMESTAMP | Erstellt am |

### Indizes:

| Index | Spalten | Zweck |
|-------|---------|-------|
| `idx_predictions_coin_timestamp` | `coin_id`, `data_timestamp DESC` | Neueste Vorhersagen pro Coin |
| `idx_predictions_model` | `model_id`, `created_at DESC` | Vorhersagen eines Modells |
| `idx_predictions_active_model` | `active_model_id`, `created_at DESC` | Vorhersagen eines aktiven Modells |
| `idx_predictions_created` | `created_at DESC` | Neueste Vorhersagen |

---

## Tabelle 3: `prediction_webhook_log`

### Zweck
Loggt alle n8n Webhook-Aufrufe fuer Debugging und Monitoring.

### Felder:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | BIGSERIAL | Primaerschluessel |
| `coin_id` | VARCHAR(255) | Coin-ID |
| `data_timestamp` | TIMESTAMP | Zeitstempel der Daten |
| `webhook_url` | TEXT | n8n Webhook-URL |
| `payload` | JSONB | Gesendeter JSON-Payload |
| `response_status` | INTEGER | HTTP-Status-Code |
| `response_body` | TEXT | Response-Body |
| `error_message` | TEXT | Fehler-Message |
| `created_at` | TIMESTAMP | Erstellt am |

---

## Tabelle 4: `model_predictions`

### Zweck
Speichert ALLE Vorhersagen mit klaren Tags (negativ/positiv/alert) und Status (aktiv/inaktiv). Ersetzt die komplexe Struktur aus predictions + alert_evaluations durch EINE einfache Tabelle. Enthaelt ATH-Tracking und Evaluation-Ergebnisse.

### Felder:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | BIGSERIAL | Primaerschluessel |
| **Basis** | | |
| `coin_id` | VARCHAR(255) | Coin-ID (mint) |
| `model_id` | BIGINT | Referenz zu `ml_models.id` |
| `active_model_id` | BIGINT | FK zu `prediction_active_models.id` |
| **Vorhersage** | | |
| `prediction` | INTEGER | `0` (negativ) oder `1` (positiv) |
| `probability` | NUMERIC(5,4) | Wahrscheinlichkeit (0.0-1.0) |
| `tag` | VARCHAR(20) | `negativ`, `positiv` oder `alert` (automatisch berechnet) |
| `status` | VARCHAR(20) | `aktiv` (wartet) oder `inaktiv` (ausgewertet) |
| **Zeitstempel** | | |
| `prediction_timestamp` | TIMESTAMP | Wann wurde Vorhersage gemacht |
| `evaluation_timestamp` | TIMESTAMP | Wann soll ausgewertet werden |
| `evaluated_at` | TIMESTAMP | Wann wurde tatsaechlich ausgewertet |
| **Werte bei Vorhersage** | | |
| `price_close_at_prediction` | NUMERIC(20,8) | Preis bei Vorhersage |
| `price_open_at_prediction` | NUMERIC(20,8) | Open-Preis |
| `price_high_at_prediction` | NUMERIC(20,8) | High-Preis |
| `price_low_at_prediction` | NUMERIC(20,8) | Low-Preis |
| `market_cap_at_prediction` | NUMERIC(20,2) | Market Cap |
| `volume_at_prediction` | NUMERIC(20,2) | Volume |
| `phase_id_at_prediction` | INTEGER | Phase-ID |
| **Werte bei Evaluation** | | |
| `price_close_at_evaluation` | NUMERIC(20,8) | Preis bei Evaluation |
| `price_open_at_evaluation` | NUMERIC(20,8) | Open-Preis |
| `price_high_at_evaluation` | NUMERIC(20,8) | High-Preis |
| `price_low_at_evaluation` | NUMERIC(20,8) | Low-Preis |
| `market_cap_at_evaluation` | NUMERIC(20,2) | Market Cap |
| `volume_at_evaluation` | NUMERIC(20,2) | Volume |
| `phase_id_at_evaluation` | INTEGER | Phase-ID |
| **ATH-Tracking** | | |
| `ath_price` | NUMERIC(20,8) | Hoechster Preis seit Vorhersage |
| `ath_price_timestamp` | TIMESTAMP | Zeitpunkt des ATH |
| `ath_change_pct` | NUMERIC(10,4) | ATH-Aenderung in % |
| `atl_price` | NUMERIC(20,8) | Niedrigster Preis seit Vorhersage |
| `atl_price_timestamp` | TIMESTAMP | Zeitpunkt des ATL |
| `atl_change_pct` | NUMERIC(10,4) | ATL-Aenderung in % |
| **Evaluation** | | |
| `actual_price_change_pct` | NUMERIC(10,4) | Tatsaechliche Preisaenderung in % |
| `evaluation_result` | VARCHAR(20) | `success`, `failed` oder `not_applicable` |
| `evaluation_note` | TEXT | Zusaetzliche Info |
| **Meta** | | |
| `created_at` | TIMESTAMP | Erstellt am |
| `updated_at` | TIMESTAMP | Aktualisiert am |

### Tag-Logik:
- `probability < 0.5` -> `negativ`
- `probability >= 0.5 AND probability < alert_threshold` -> `positiv`
- `probability >= alert_threshold` -> `alert`

### Status-Logik:
- `aktiv` = Wartet auf Auswertung (`evaluation_timestamp` noch nicht erreicht)
- `inaktiv` = Ausgewertet (Ergebnis eingetragen)

### Indizes:

| Index | Spalten | Zweck |
|-------|---------|-------|
| `idx_model_predictions_coin_timestamp` | `coin_id`, `prediction_timestamp DESC` | Neueste Vorhersagen pro Coin |
| `idx_model_predictions_model` | `model_id`, `prediction_timestamp DESC` | Vorhersagen eines Modells |
| `idx_model_predictions_active_model` | `active_model_id`, `prediction_timestamp DESC` | Vorhersagen eines aktiven Modells |
| `idx_model_predictions_status` | `status` (WHERE `aktiv`) | Offene Vorhersagen |
| `idx_model_predictions_tag` | `tag` | Filter nach Tag |
| `idx_model_predictions_evaluation_timestamp` | `evaluation_timestamp` (WHERE `aktiv`) | Faellige Evaluierungen |

---

## Tabelle 5: `alert_evaluations`

### Zweck
Speichert Alert-Auswertungen mit umfassenden Marktdaten zum Zeitpunkt des Alerts und der Evaluation. Unterstuetzt zeitbasierte und klassische Vorhersagen.

### Felder:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | BIGSERIAL | Primaerschluessel |
| `prediction_id` | BIGINT | FK zu `predictions.id` |
| `coin_id` | VARCHAR(255) | Coin-ID |
| `model_id` | BIGINT | Modell-ID |
| **Typ** | | |
| `prediction_type` | VARCHAR(20) | `time_based` oder `classic` |
| `target_variable` | VARCHAR(100) | z.B. `price_close` (time_based) |
| `future_minutes` | INTEGER | Vorhersage-Horizont (time_based) |
| `price_change_percent` | NUMERIC(10,4) | Ziel-Aenderung (time_based) |
| `target_direction` | VARCHAR(10) | `up` oder `down` (time_based) |
| `target_operator` | VARCHAR(10) | Operator (classic) |
| `target_value` | NUMERIC(20,2) | Ziel-Wert (classic) |
| **Werte bei Alert** | | |
| `alert_timestamp` | TIMESTAMP | Zeitpunkt des Alerts |
| `price_close_at_alert` | NUMERIC(20,8) | Preis bei Alert |
| `volume_sol_at_alert` | NUMERIC(20,2) | Volume bei Alert |
| `phase_id_at_alert` | INTEGER | Phase bei Alert |
| *(weitere Marktdaten)* | | |
| **Werte bei Evaluation** | | |
| `evaluation_timestamp` | TIMESTAMP | alert_timestamp + future_minutes |
| `price_close_at_evaluation` | NUMERIC(20,8) | Preis bei Evaluation |
| *(weitere Marktdaten)* | | |
| **Ergebnis** | | |
| `actual_price_change_pct` | NUMERIC(10,4) | Tatsaechliche Preisaenderung |
| `status` | VARCHAR(20) | `pending`, `success`, `failed`, `expired`, `not_applicable` |
| `evaluated_at` | TIMESTAMP | Wann ausgewertet |
| `evaluation_note` | TEXT | Zusaetzliche Info |
| **ATH-Tracking** | | |
| `ath_price` | NUMERIC(20,8) | Hoechster Preis seit Alert |
| `ath_timestamp` | TIMESTAMP | Zeitpunkt des ATH |
| `ath_change_pct` | NUMERIC(10,4) | ATH-Aenderung in % |
| `atl_price` | NUMERIC(20,8) | Niedrigster Preis seit Alert |
| `atl_timestamp` | TIMESTAMP | Zeitpunkt des ATL |
| `atl_change_pct` | NUMERIC(10,4) | ATL-Aenderung in % |

### Status-Werte:
- `pending` - Wartet auf Auswertung
- `success` - Vorhersage war korrekt
- `failed` - Vorhersage war falsch
- `expired` - Keine Daten zum Evaluationszeitpunkt
- `not_applicable` - Nicht auswertbar (z.B. Modell geloescht)

### Indizes:

| Index | Spalten | Zweck |
|-------|---------|-------|
| `idx_alert_evaluations_coin_timestamp` | `coin_id`, `alert_timestamp ASC` | Aelteste zuerst |
| `idx_alert_evaluations_status` | `status` (WHERE `pending`) | Offene Evaluierungen |
| `idx_alert_evaluations_prediction` | `prediction_id` | Join mit predictions |
| `idx_alert_evaluations_evaluation_timestamp` | `evaluation_timestamp` (WHERE `pending`) | Faellige Evaluierungen |

---

## Tabelle 6: `coin_scan_cache`

### Zweck
Cache fuer zuletzt gescannte Coins und deren Ignore-Status. Verhindert zu haeufige Scans desselben Coins pro Modell.

### Felder:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | BIGSERIAL | Primaerschluessel |
| `coin_id` | VARCHAR(255) | Coin-Mint-Adresse |
| `active_model_id` | BIGINT | FK zu `prediction_active_models.id` (CASCADE) |
| `last_scan_at` | TIMESTAMP | Letzte Verarbeitung |
| `last_prediction` | INTEGER | Letzte Vorhersage (0/1) |
| `last_probability` | NUMERIC(5,4) | Letzte Wahrscheinlichkeit |
| `was_alert` | BOOLEAN | Ob Alert ausgeloest wurde |
| `ignore_until` | TIMESTAMP | Bis wann ignorieren (NULL = nicht) |
| `ignore_reason` | VARCHAR(20) | `bad`, `positive` oder `alert` |
| `created_at` | TIMESTAMP | Erstellt am |
| `updated_at` | TIMESTAMP | Aktualisiert am |

### Constraints:
- **`UNIQUE(coin_id, active_model_id)`** - Ein Coin kann nur einmal pro Modell gecached werden
- **FK** `active_model_id` -> `prediction_active_models.id` ON DELETE CASCADE

### Indizes:

| Index | Spalten | Zweck |
|-------|---------|-------|
| `idx_coin_scan_cache_coin_model` | `coin_id`, `active_model_id` | Schnelle Lookup |
| `idx_coin_scan_cache_ignore_until` | `ignore_until` (WHERE NOT NULL) | Aktive Ignores |
| `idx_coin_scan_cache_last_scan` | `last_scan_at DESC` | Neueste Scans |
| `idx_coin_scan_cache_alerts` | `was_alert` (WHERE true) | Alert-Coins |

---

## Beziehungen zwischen Tabellen

### `prediction_active_models` <-> `ml_models`
- **Beziehung:** Logische Referenz (kein Foreign Key!)
- **Grund:** Separater Server, keine direkte DB-Verbindung

### `predictions` <-> `prediction_active_models`
- **Beziehung:** Foreign Key (`active_model_id`)
- **Verhalten:** `ON DELETE SET NULL`

### `model_predictions` <-> `prediction_active_models`
- **Beziehung:** Logische Referenz (`active_model_id`)

### `alert_evaluations` <-> `predictions`
- **Beziehung:** Foreign Key (`prediction_id`)
- **Verhalten:** `ON DELETE CASCADE`

### `coin_scan_cache` <-> `prediction_active_models`
- **Beziehung:** Foreign Key (`active_model_id`)
- **Verhalten:** `ON DELETE CASCADE`

---

## Migrations

Alle Migrations befinden sich in `sql/migrations/`:

| Migration | Beschreibung |
|-----------|--------------|
| `create_model_predictions.sql` | model_predictions Tabelle |
| `create_alert_evaluations.sql` | alert_evaluations Tabelle |
| `create_coin_scan_cache.sql` | coin_scan_cache Tabelle |
| `add_alert_threshold.sql` | alert_threshold Spalte |
| `add_n8n_settings.sql` | n8n Webhook-Spalten |
| `add_alert_config.sql` | coin_filter_mode, coin_whitelist |
| `add_coin_ignore_settings.sql` | ignore_*_seconds Spalten |
| `add_max_log_entries_per_coin.sql` | max_log_entries Spalten |
| `add_performance_metrics.sql` | Training-Metriken Spalten |
| `add_ath_tracking.sql` | ATH-Tracking fuer alert_evaluations |
| `add_ath_tracking_model_predictions.sql` | ATH-Tracking fuer model_predictions |
| `add_send_ignored_to_n8n.sql` | send_ignored_to_n8n Spalte |
| `add_min_scan_interval.sql` | min_scan_interval_seconds Spalte |
| `migrate_n8n_send_mode_to_array.sql` | n8n_send_mode VARCHAR -> JSONB Array |
| `fix_price_precision_model_predictions.sql` | Preis-Precision erhoehen |

---

## Test-Queries

### Tabellen pruefen:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'prediction_active_models', 'predictions', 'prediction_webhook_log',
    'model_predictions', 'alert_evaluations', 'coin_scan_cache'
)
ORDER BY table_name;
```

### Aktive Modelle:
```sql
SELECT id, model_id, model_name, model_type, is_active,
       total_predictions, alert_threshold, n8n_enabled
FROM prediction_active_models
WHERE is_active = true;
```

### Offene Evaluierungen:
```sql
SELECT COUNT(*), active_model_id
FROM model_predictions
WHERE status = 'aktiv' AND evaluation_timestamp <= NOW()
GROUP BY active_model_id;
```

### Alert-Statistiken:
```sql
SELECT
    status,
    COUNT(*) as count,
    AVG(actual_price_change_pct) as avg_change
FROM alert_evaluations
WHERE status != 'pending'
GROUP BY status;
```

---

## Wichtige Hinweise

### 1. Keine Foreign Keys zu `ml_models`
- Prediction Service und Training Service sind separate Server
- Referenzen sind logisch (ueber `model_id`)

### 2. Trigger auf bestehender Tabelle
- Trigger auf `coin_metrics` kann jederzeit entfernt werden ohne Datenverlust

### 3. JSONB Felder
- `features`, `params`, `n8n_send_mode`, `coin_whitelist` verwenden JSONB
- Beispiel: `SELECT * FROM prediction_active_models WHERE features @> '["price_close"]'::jsonb;`

### 4. Zeitzone
- Alle Timestamps nutzen `TIMESTAMP WITH TIME ZONE`
- Immer UTC speichern

---

**Erstellt:** Januar 2025
**Letzte Aktualisierung:** Februar 2026
