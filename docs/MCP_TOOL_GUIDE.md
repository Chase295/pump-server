# Pump Server MCP - Detaillierte Tool-Anleitung

Dieses Dokument beschreibt den MCP Server des Pump-Servers im Detail. Es dient als Referenz fuer Claude (Web/Code/Desktop) und andere MCP-Clients.

## Was ist der Pump Server?

Der Pump Server ist ein **Echtzeit-ML-Vorhersage-Service** fuer Kryptowaehrungen. Er:

- Ueberwacht Cryptocurrency-Token ueber `coin_metrics` (Preise, Volumen, Marktdaten)
- Nutzt trainierte ML-Modelle (scikit-learn, XGBoost) um Kursanstiege vorherzusagen
- Bewertet Vorhersagen automatisch nach Ablauf des Zeitfensters
- Sendet Alerts ueber n8n Webhooks wenn ein Coin als vielversprechend eingestuft wird

## Verbindung

- **URL:** `https://pump-server.chase295.de/mcp`
- **Transport:** Streamable HTTP (JSON-RPC ueber POST)
- **Authentifizierung:** Keine (authless)

---

## Konzepte

### IDs verstehen

| ID | Beschreibung | Wo zu finden |
|----|-------------|-------------|
| `active_model_id` | ID in der `prediction_active_models` Tabelle. **Das ist die primaere ID fuer fast alle Tools.** | `list_active_models` → `id` Feld |
| `model_id` | ID im Training-Service. Wird beim Import verwendet. | `list_available_models` → `id` Feld, oder `list_active_models` → `model_id` Feld |
| `coin_id` | Mint-Adresse des Tokens (Solana-Adresse) | z.B. `"So11111111111111111111111111111111111112"` |
| `alert_id` | ID einer Alert-Evaluierung | `get_alerts` → Alert-Eintraege |

### Prediction-Typen

Es gibt zwei Tabellen fuer Vorhersagen:

1. **`predictions`** (alte Architektur) - Rohe Vorhersagen mit Wahrscheinlichkeiten
2. **`model_predictions`** (neue Architektur) - Angereicherte Vorhersagen mit Tags und Status

### Prediction-Tags und Status

- **Tags:** `negativ` (Kursfall erwartet), `positiv` (Kursanstieg erwartet), `alert` (starkes Signal, ueber Alert-Threshold)
- **Status:** `aktiv` (noch nicht evaluiert, Zeitfenster laeuft noch), `inaktiv` (evaluiert oder abgelaufen)

### Alert-Evaluierung

Wenn ein Modell eine positive Vorhersage mit hoher Wahrscheinlichkeit macht (>= `alert_threshold`), wird ein Alert erzeugt. Nach Ablauf des Zeitfensters (`future_minutes`) wird evaluiert ob der Kurs tatsaechlich gestiegen ist:

- **success:** Kurs ist gestiegen - Vorhersage war korrekt
- **failed:** Kurs ist gefallen - Vorhersage war falsch
- **expired:** Keine Preisdaten verfuegbar fuer die Evaluierung
- **pending:** Noch nicht evaluiert (Zeitfenster laeuft noch)

---

## Tools nach Kategorie

### 1. Modell-Management (9 Tools)

#### `list_active_models`
Listet alle aktiven ML-Modelle im Pump-Server.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `include_inactive` | boolean | Nein | Wenn `true`, werden auch pausierte Modelle angezeigt (default: `false`) |

**Rueckgabe:** Liste mit `id`, `model_id`, `name`, `model_type`, `is_active`, `target_direction`, `future_minutes`, `alert_threshold`, `total_predictions`, `stats`, `training_accuracy`, `training_f1`

**Typischer Einsatz:** Erster Aufruf um einen Ueberblick zu bekommen. Die `id` aus der Antwort ist die `active_model_id` fuer alle anderen Tools.

---

#### `list_available_models`
Zeigt Modelle die im Training-Service verfuegbar sind aber noch nicht importiert wurden.

**Parameter:** Keine

**Rueckgabe:** Liste mit `id` (= model_id im Training-Service), `name`, `model_type`, `target_direction`, `future_minutes`, `features_count`, Training-Metriken

**Typischer Einsatz:** Vor einem Import, um zu sehen welche neuen Modelle verfuegbar sind.

---

#### `import_model`
Importiert ein ML-Modell vom Training-Service in den Pump-Server. Das Modell wird heruntergeladen, in der DB registriert und automatisch aktiviert.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `model_id` | integer | Ja | ID des Modells im Training-Service (aus `list_available_models`) |

**Ablauf intern:**
1. Download der Modell-Datei (.joblib) vom Training-Service
2. Speichern unter `/app/models/`
3. Registrierung in `prediction_active_models` Tabelle
4. Modell ist sofort aktiv und macht Vorhersagen

---

#### `get_model_details`
Holt detaillierte Informationen zu einem aktiven Modell inkl. Konfiguration, Features und Statistiken.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**Rueckgabe:** Vollstaendige Modell-Informationen: Name, Typ, Status, Target-Variable, Target-Direction, Features-Liste, Alert-Konfiguration, Ignore-Settings, Webhook-Config, Training-Metriken, Statistiken

---

#### `activate_model`
Aktiviert ein pausiertes Modell, sodass es wieder automatisch Vorhersagen macht.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des zu aktivierenden Modells |

---

#### `deactivate_model`
Pausiert ein aktives Modell. Es macht keine Vorhersagen mehr, bleibt aber gespeichert und kann spaeter wieder aktiviert werden.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des zu pausierenden Modells |

---

#### `rename_model`
Setzt einen benutzerdefinierten Namen fuer ein Modell (`custom_name`).

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `new_name` | string | Ja | Neuer Name |

---

#### `delete_model`
Loescht ein aktives Modell und ALLE zugehoerigen Predictions permanent.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des zu loeschenden Modells |

**ACHTUNG:** Nicht rueckgaengig machbar! Loescht das Modell UND alle Predictions, Alerts und Logs.

---

#### `update_model_metrics`
Aktualisiert die Training-Performance-Metriken (Accuracy, F1, Precision, Recall) eines Modells vom Training-Service.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `model_id` | integer | Ja | ID des Modells im Training-Service |

---

### 2. Vorhersagen (7 Tools)

#### `predict_coin`
Macht eine ML-Vorhersage fuer einen Cryptocurrency-Coin. Gibt Wahrscheinlichkeit fuer Kursanstieg/Kursfall zurueck.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `coin_id` | string | Ja | Coin-ID (Mint-Adresse des Tokens) |
| `model_ids` | array[integer] | Nein | Liste von `active_model_ids`. Wenn leer, werden alle aktiven Modelle verwendet |

**Rueckgabe:** Pro Modell: `prediction` (0=negativ, 1=positiv), `probability` (0.0-1.0), `prediction_label` ("POSITIVE (UP)" oder "NEGATIVE (DOWN)")

**Hinweis:** Damit eine Vorhersage funktioniert, muessen aktuelle `coin_metrics` fuer den Coin in der DB vorliegen. Ohne Metriken schlaegt die Vorhersage fehl.

---

#### `get_predictions`
Holt historische Vorhersagen aus der `predictions` Tabelle (alte Architektur) mit Filtern und Pagination.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `coin_id` | string | Nein | Filter nach Coin-ID |
| `active_model_id` | integer | Nein | Filter nach Modell |
| `prediction` | integer (0 oder 1) | Nein | 0=negativ, 1=positiv |
| `min_probability` | number | Nein | Minimale Wahrscheinlichkeit (0.0-1.0) |
| `limit` | integer | Nein | Max. Ergebnisse (default: 50) |
| `offset` | integer | Nein | Pagination-Offset (default: 0) |

---

#### `get_latest_prediction`
Holt die neueste Vorhersage fuer einen bestimmten Coin.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `coin_id` | string | Ja | Coin-ID (Mint-Adresse) |
| `model_id` | integer | Nein | Filter nach Modell-ID |

---

#### `get_model_predictions`
Holt Vorhersagen aus der `model_predictions` Tabelle (neue Architektur) mit Filtern nach Tag, Status, Coin.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Nein | Filter nach aktivem Modell |
| `tag` | string | Nein | `"negativ"`, `"positiv"`, oder `"alert"` |
| `status` | string | Nein | `"aktiv"` (noch laufend) oder `"inaktiv"` (evaluiert) |
| `coin_id` | string | Nein | Filter nach Coin-ID |
| `limit` | integer | Nein | Max. Ergebnisse (default: 100) |
| `offset` | integer | Nein | Pagination-Offset (default: 0) |

---

#### `delete_model_predictions`
Loescht ALLE Eintraege in `model_predictions` fuer ein Modell (aktive UND inaktive).

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**ACHTUNG:** Nicht rueckgaengig machbar!

---

#### `reset_model_statistics`
Setzt die Statistiken eines Modells zurueck: Loescht alle Predictions aus der `predictions` Tabelle und setzt `total_predictions` auf 0.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**ACHTUNG:** Nicht rueckgaengig machbar!

---

#### `get_coin_details`
Holt detaillierte Coin-Informationen: Preishistorie, alle Predictions und Evaluierungen fuer einen bestimmten Coin und ein bestimmtes Modell in einem Zeitfenster.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `coin_id` | string | Ja | Coin-ID (Mint-Adresse) |
| `start_timestamp` | string | Nein | ISO-Format (default: 24h zurueck) |
| `end_timestamp` | string | Nein | ISO-Format (default: jetzt) |

**Rueckgabe:** `price_history` (Preisverlauf), `predictions` (Vorhersagen), `evaluations` (Bewertungen)

---

### 3. Konfiguration (7 Tools)

#### `update_alert_config`
Aktualisiert die Alert-Konfiguration eines Modells: Webhook-URL, Threshold, Filter, Send-Mode.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `n8n_webhook_url` | string | Nein | n8n Webhook URL (leerer String = deaktivieren) |
| `n8n_enabled` | boolean | Nein | Webhook ein/aus |
| `n8n_send_mode` | array[string] | Nein | `"all"`, `"alerts_only"`, `"positive_only"`, `"negative_only"` |
| `alert_threshold` | number | Nein | Schwellenwert 0.0-1.0 (z.B. 0.7 = nur Vorhersagen mit >70% Wahrscheinlichkeit als Alert) |
| `coin_filter_mode` | string | Nein | `"all"` oder `"whitelist"` |

---

#### `get_model_statistics`
Holt detaillierte Statistiken: Predictions-Zaehler, Positive/Negative Rate, Durchschnittliche Wahrscheinlichkeit, Alert-Anzahl, Webhook-Statistiken.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**Rueckgabe:** `total_predictions`, `positive_rate_percent`, `negative_rate_percent`, `avg_probability`, `unique_coins`, `alerts_count`, `webhook_stats` (total/success/failed)

---

#### `get_n8n_status`
Prueft den aktuellen n8n Webhook-Status fuer ein Modell.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**Rueckgabe:** Status: `"ok"`, `"error"`, `"unknown"`, oder `"no_url"`

---

#### `get_ignore_settings`
Holt die Coin-Ignore-Einstellungen. Nach einer Vorhersage wird der gleiche Coin fuer eine konfigurierbare Zeit ignoriert, um Spam zu vermeiden.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**Rueckgabe:** `ignore_bad_seconds`, `ignore_positive_seconds`, `ignore_alert_seconds`

---

#### `update_ignore_settings`
Setzt die Coin-Ignore-Zeiten (wie lange ein Coin nach einer Vorhersage ignoriert wird).

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `ignore_bad_seconds` | integer | Ja | Sekunden fuer negative Coins (0-86400) |
| `ignore_positive_seconds` | integer | Ja | Sekunden fuer positive Coins (0-86400) |
| `ignore_alert_seconds` | integer | Ja | Sekunden fuer Alert-Coins (0-86400) |

---

#### `get_max_log_entries`
Holt die maximale Anzahl an Log-Eintraegen pro Coin pro Typ.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `update_max_log_entries`
Setzt die maximale Anzahl an Log-Eintraegen pro Coin (0 = unbegrenzt).

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `max_log_entries_per_coin_negative` | integer | Ja | Max negative Eintraege (0-1000) |
| `max_log_entries_per_coin_positive` | integer | Ja | Max positive Eintraege (0-1000) |
| `max_log_entries_per_coin_alert` | integer | Ja | Max Alert-Eintraege (0-1000) |

---

### 4. Alerts (5 Tools)

#### `get_alerts`
Holt Alert-Eintraege mit umfangreichen Filtern und Pagination.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `status` | string | Nein | `"pending"`, `"success"`, `"failed"`, `"expired"` |
| `model_id` | integer | Nein | Filter nach active_model_id |
| `coin_id` | string | Nein | Filter nach Coin-ID |
| `prediction_type` | string | Nein | `"time_based"` oder `"classic"` |
| `date_from` | string | Nein | Ab Datum (ISO-Format) |
| `date_to` | string | Nein | Bis Datum (ISO-Format) |
| `unique_coins` | boolean | Nein | Nur aeltester Alert pro Coin (default: `true`) |
| `include_non_alerts` | boolean | Nein | Auch Predictions unter Threshold (default: `false`) |
| `limit` | integer | Nein | Max. Ergebnisse (default: 100) |
| `offset` | integer | Nein | Pagination-Offset (default: 0) |

---

#### `get_alert_details`
Holt detaillierte Informationen zu einem einzelnen Alert: Metriken zum Zeitpunkt der Vorhersage, Preishistorie vor/nach dem Alert, Evaluierungsergebnis.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `alert_id` | integer | Ja | ID des Alerts |
| `chart_before_minutes` | integer | Nein | Minuten Preisdaten vor Alert (default: 10) |
| `chart_after_minutes` | integer | Nein | Minuten Preisdaten nach Evaluation (default: 10) |

---

#### `get_alert_statistics`
Holt aggregierte Alert-Statistiken (Erfolgsrate, Anzahl, etc.), optional gefiltert.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `model_id` | integer | Nein | Filter nach active_model_id |
| `date_from` | string | Nein | Ab Datum (ISO-Format) |
| `date_to` | string | Nein | Bis Datum (ISO-Format) |

---

#### `get_all_models_alert_statistics`
Holt Alert-Statistiken fuer mehrere/alle Modelle in einer optimierten Batch-Abfrage.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_ids` | array[integer] | Nein | Liste von IDs (leer = alle aktiven Modelle) |

---

#### `delete_model_alerts`
Loescht alle Alert-Evaluierungen fuer ein Modell aus der `alert_evaluations` Tabelle.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**ACHTUNG:** Nicht rueckgaengig machbar!

---

### 5. System (10 Tools)

#### `health_check`
Prueft den Gesamtstatus: DB-Verbindung (+ Latenz), aktive Modelle, Predictions der letzten Stunde, Uptime.

**Parameter:** Keine

**Rueckgabe:** `status` ("healthy"/"degraded"/"unhealthy"), DB-Latenz, aktive Modelle, Predictions/Stunde, Uptime

---

#### `get_stats`
Holt umfassende Service-Statistiken ueber alle Modelle hinweg.

**Parameter:** Keine

**Rueckgabe:**
- **Predictions:** total, letzte Stunde/24h/7 Tage, positiv/negativ Rate, durchschnittliche Wahrscheinlichkeit, unique Coins
- **Modelle:** total, aktiv, inaktiv
- **Webhooks (24h):** gesendet, erfolgreich, fehlgeschlagen
- **Alerts:** total, letzte 24h

---

#### `get_system_config`
Holt die aktuelle persistente Konfiguration aus der Config-Datei.

**Parameter:** Keine

**Rueckgabe:** `database_url`, `training_service_url`, `n8n_webhook_url`, `api_port`, `streamlit_port`

---

#### `update_configuration`
Speichert eine neue persistente Konfiguration.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `config` | object | Ja | Dict mit Schluesseln: `database_url`, `training_service_url`, `n8n_webhook_url`, `api_port`, `streamlit_port` |

---

#### `get_logs`
Holt die letzten Log-Zeilen des Services (Docker-Logs oder Dateien).

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `tail` | integer | Nein | Anzahl der Zeilen (default: 100) |

---

#### `restart_system`
Initiiert einen Service-Neustart ueber SIGTERM. Supervisor startet den Prozess automatisch neu.

**Parameter:** Keine

**Hinweis:** Nach dem Aufruf ist der Service kurz nicht erreichbar.

---

#### `delete_old_logs`
Loescht ALLE Logs fuer ein Modell: `alert_evaluations`, `predictions`, und `model_predictions`.

**Parameter:**
| Name | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**ACHTUNG:** Loescht alle drei Tabellen gleichzeitig! Nicht rueckgaengig machbar!

**Rueckgabe:** Anzahl geloeschter Eintraege pro Tabelle (`deleted_alerts`, `deleted_predictions`, `deleted_model_predictions`)

---

#### `migrate_performance_metrics`
Fuehrt eine DB-Migration aus: Fuegt Spalten fuer Training-Metriken (Accuracy, F1, Precision, Recall, ROC AUC, MCC, Confusion Matrix, Simulated Profit) zur `prediction_active_models` Tabelle hinzu.

**Parameter:** Keine

**Hinweis:** Idempotent - kann mehrfach aufgerufen werden (`ADD COLUMN IF NOT EXISTS`).

---

#### `debug_active_models`
Debug-Tool: Zeigt alle aktiven Modelle mit vollstaendigen Rohdaten aus der Datenbank.

**Parameter:** Keine

---

#### `debug_coin_metrics`
Debug-Tool: Zeigt `coin_metrics` Statistiken - Gesamtanzahl Eintraege, neuester/aeltester Zeitstempel, Anzahl unique Coins.

**Parameter:** Keine

**Nuetzlich um zu pruefen:** Ob Coin-Metriken aktuell sind und ob genug Daten fuer Vorhersagen vorliegen.

---

## Typische Workflows

### Status-Check
```
1. health_check          → Ist der Service gesund?
2. list_active_models    → Welche Modelle laufen?
3. get_stats             → Wie viele Predictions in letzter Zeit?
```

### Neues Modell importieren
```
1. list_available_models → Welche Modelle gibt es im Training-Service?
2. import_model          → Modell importieren (model_id angeben)
3. list_active_models    → Pruefen ob es aktiv ist
4. get_model_details     → Konfiguration anschauen
```

### Modell-Performance analysieren
```
1. list_active_models            → active_model_id finden
2. get_model_statistics          → Predictions-Statistiken
3. get_alert_statistics          → Alert-Erfolgsrate
4. get_alerts (status="success") → Erfolgreiche Alerts anschauen
5. get_alert_details             → Einzelnen Alert im Detail
```

### Alert-Konfiguration aendern
```
1. get_model_details             → Aktuelle Config sehen
2. update_alert_config           → Threshold/Webhook/Filter aendern
3. get_n8n_status                → Webhook-Verbindung pruefen
```

### Debugging: Warum macht ein Modell keine Vorhersagen?
```
1. health_check                  → DB-Verbindung ok?
2. debug_active_models           → Ist das Modell aktiv?
3. debug_coin_metrics            → Gibt es aktuelle Coin-Metriken?
4. get_logs                      → Fehlermeldungen im Log?
5. get_ignore_settings           → Werden Coins zu lange ignoriert?
```
