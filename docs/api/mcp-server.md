# MCP Server API

Der pump-server bietet einen integrierten MCP (Model Context Protocol) Server, der es KI-Clients wie Claude Code, Cursor oder anderen MCP-kompatiblen Anwendungen ermoeglicht, direkt mit dem Service zu interagieren.

---

## Uebersicht

| Eigenschaft | Wert |
|-------------|------|
| **Protokoll** | MCP (Model Context Protocol) |
| **Transport** | SSE (Server-Sent Events) |
| **Base URL** | `http://localhost:3003/mcp` (via Nginx-Proxy) |
| **SSE Endpoint** | `GET /mcp/sse` |
| **Messages Endpoint** | `POST /mcp/messages/` |
| **Tools** | 38 verfuegbare Tools in 5 Kategorien |
| **Authentifizierung** | Keine (lokaler Zugriff) |

---

## Schnellstart

### 1. Server-Status pruefen

```bash
curl http://localhost:3003/mcp/info
curl http://localhost:3003/mcp/health
```

### 2. Client konfigurieren

**Claude Code** - `.mcp.json` im Projektroot:

```json
{
  "mcpServers": {
    "pump-server": {
      "type": "sse",
      "url": "https://dein-server.example.com/mcp/sse"
    }
  }
}
```

**Cursor IDE** - `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pump-server": {
      "transport": "sse",
      "url": "https://dein-server.example.com/mcp/sse"
    }
  }
}
```

### 3. Client neu starten

Nach dem Speichern der Konfiguration den KI-Client neu starten. Die 38 MCP Tools erscheinen dann in der Tool-Liste.

---

## Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/mcp/info` | GET | Server-Informationen und komplette Tool-Liste |
| `/mcp/sse` | GET | SSE-Stream fuer bidirektionale MCP-Kommunikation |
| `/mcp/messages/` | POST | Empfaengt JSON-RPC Messages vom Client (mit `session_id`) |
| `/mcp/health` | GET | Health-Check mit DB-Status und Uptime |

### `/mcp/info` Response

```json
{
  "name": "pump-server-mcp",
  "version": "1.0.0",
  "description": "MCP Server for Pump-Server",
  "transport": "sse",
  "sse_endpoint": "/mcp/sse",
  "messages_endpoint": "/mcp/messages/",
  "tools": [...],
  "tools_count": 38
}
```

---

## Verfuegbare Tools (38)

### Modell-Management (9 Tools)

#### `list_active_models`
Liste aller aktiven (und optional inaktiven) ML-Modelle.

| Parameter | Typ | Required | Default | Beschreibung |
|-----------|-----|----------|---------|--------------|
| `include_inactive` | boolean | Nein | `false` | Auch pausierte Modelle anzeigen |

---

#### `list_available_models`
Liste aller verfuegbaren Modelle zum Import vom Training-Service.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| - | - | - | Keine Parameter |

---

#### `import_model`
Importiert ein ML-Modell vom Training-Service in den Pump-Server.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `model_id` | integer | Ja | ID des Modells im Training-Service |

---

#### `get_model_details`
Holt detaillierte Informationen zu einem aktiven Modell inkl. Konfiguration, Features und Statistiken.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `activate_model`
Aktiviert ein pausiertes Modell, sodass es wieder Vorhersagen macht.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des zu aktivierenden Modells |

---

#### `deactivate_model`
Pausiert ein aktives Modell. Das Modell macht keine Vorhersagen mehr, bleibt aber gespeichert.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des zu pausierenden Modells |

---

#### `rename_model`
Benennt ein aktives Modell um (setzt custom_name).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `new_name` | string | Ja | Neuer Name fuer das Modell |

---

#### `delete_model`
Loescht ein aktives Modell und ALLE zugehoerigen Predictions. **Nicht rueckgaengig machbar!**

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des zu loeschenden Modells |

---

#### `update_model_metrics`
Aktualisiert die Performance-Metriken eines Modells vom Training-Service (Accuracy, F1, etc.).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `model_id` | integer | Ja | ID des Modells im Training-Service |

---

### Vorhersagen (7 Tools)

#### `predict_coin`
Macht eine ML-Vorhersage fuer einen Cryptocurrency-Coin.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `coin_id` | string | Ja | Coin-ID (Mint-Adresse des Tokens) |
| `model_ids` | integer[] | Nein | Liste von active_model_ids (wenn leer: alle aktiven) |

---

#### `get_predictions`
Holt historische Vorhersagen mit Filtern. Unterstuetzt Pagination.

| Parameter | Typ | Required | Default | Beschreibung |
|-----------|-----|----------|---------|--------------|
| `coin_id` | string | Nein | - | Filter nach Coin-ID |
| `active_model_id` | integer | Nein | - | Filter nach Modell |
| `prediction` | integer | Nein | - | 0=negativ, 1=positiv |
| `min_probability` | number | Nein | - | Minimale Wahrscheinlichkeit (0.0-1.0) |
| `limit` | integer | Nein | 50 | Max. Anzahl Ergebnisse |
| `offset` | integer | Nein | 0 | Offset fuer Pagination |

---

#### `get_latest_prediction`
Holt die neueste Vorhersage fuer einen bestimmten Coin.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `coin_id` | string | Ja | Coin-ID (Mint-Adresse) |
| `model_id` | integer | Nein | Filter nach Modell-ID |

---

#### `get_model_predictions`
Holt Model-Predictions mit Filtern nach Tag, Status, Coin etc.

| Parameter | Typ | Required | Default | Beschreibung |
|-----------|-----|----------|---------|--------------|
| `active_model_id` | integer | Nein | - | Filter nach aktivem Modell |
| `tag` | string | Nein | - | `negativ`, `positiv` oder `alert` |
| `status` | string | Nein | - | `aktiv` oder `inaktiv` |
| `coin_id` | string | Nein | - | Filter nach Coin-ID |
| `limit` | integer | Nein | 100 | Max. Anzahl Ergebnisse |
| `offset` | integer | Nein | 0 | Offset fuer Pagination |

---

#### `delete_model_predictions`
Loescht ALLE Model-Predictions fuer ein Modell (aktiv UND inaktiv). **Nicht rueckgaengig machbar!**

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `reset_model_statistics`
Setzt die Statistiken eines Modells zurueck (loescht alle Predictions). **Nicht rueckgaengig machbar!**

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `get_coin_details`
Holt detaillierte Coin-Informationen fuer ein Modell (Preishistorie, Predictions, Evaluierungen).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `coin_id` | string | Ja | Coin-ID (Mint-Adresse) |
| `start_timestamp` | string | Nein | Start-Zeitstempel ISO-Format (default: 24h zurueck) |
| `end_timestamp` | string | Nein | End-Zeitstempel ISO-Format (default: jetzt) |

---

### Konfiguration (7 Tools)

#### `update_alert_config`
Aktualisiert die Alert-Konfiguration eines Modells (Webhook, Threshold, Filter).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `n8n_webhook_url` | string | Nein | n8n Webhook URL (leer = deaktivieren) |
| `n8n_enabled` | boolean | Nein | Webhook aktivieren/deaktivieren |
| `n8n_send_mode` | string[] | Nein | `all`, `alerts_only`, `positive_only`, `negative_only` |
| `alert_threshold` | number | Nein | Alert-Schwellenwert 0.0-1.0 |
| `coin_filter_mode` | string | Nein | `all` oder `whitelist` |

---

#### `get_model_statistics`
Holt detaillierte Statistiken fuer ein Modell (Predictions, Alerts, Webhooks, Performance).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `get_n8n_status`
Prueft den n8n Webhook-Status fuer ein Modell (ok, error, unknown, no_url).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `get_ignore_settings`
Holt die Coin-Ignore-Einstellungen fuer ein Modell (Sekunden fuer bad/positive/alert Coins).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `update_ignore_settings`
Aktualisiert die Coin-Ignore-Einstellungen fuer ein Modell (0-86400 Sekunden).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `ignore_bad_seconds` | integer | Ja | Sekunden, die negative Coins ignoriert werden (0-86400) |
| `ignore_positive_seconds` | integer | Ja | Sekunden, die positive Coins ignoriert werden (0-86400) |
| `ignore_alert_seconds` | integer | Ja | Sekunden, die Alert-Coins ignoriert werden (0-86400) |

---

#### `get_max_log_entries`
Holt die Max-Log-Entries-Einstellungen fuer ein Modell (max. Eintraege pro Coin pro Typ).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `update_max_log_entries`
Aktualisiert die Max-Log-Entries-Einstellungen fuer ein Modell (0-1000, 0=unbegrenzt).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `max_log_entries_per_coin_negative` | integer | Ja | Max negative Eintraege pro Coin (0-1000) |
| `max_log_entries_per_coin_positive` | integer | Ja | Max positive Eintraege pro Coin (0-1000) |
| `max_log_entries_per_coin_alert` | integer | Ja | Max Alert-Eintraege pro Coin (0-1000) |

---

### Alerts (5 Tools)

#### `get_alerts`
Holt Alerts mit optionalen Filtern (Status, Modell, Coin, Datum). Unterstuetzt Pagination.

| Parameter | Typ | Required | Default | Beschreibung |
|-----------|-----|----------|---------|--------------|
| `status` | string | Nein | - | `pending`, `success`, `failed`, `expired` |
| `model_id` | integer | Nein | - | Filter nach active_model_id |
| `coin_id` | string | Nein | - | Filter nach Coin-ID |
| `prediction_type` | string | Nein | - | `time_based` oder `classic` |
| `date_from` | string | Nein | - | Ab Datum ISO-Format |
| `date_to` | string | Nein | - | Bis Datum ISO-Format |
| `unique_coins` | boolean | Nein | `true` | Nur aeltester Alert pro Coin |
| `include_non_alerts` | boolean | Nein | `false` | Auch Predictions unter Threshold zeigen |
| `limit` | integer | Nein | 100 | Max. Anzahl Ergebnisse |
| `offset` | integer | Nein | 0 | Offset fuer Pagination |

---

#### `get_alert_details`
Holt detaillierte Informationen zu einem bestimmten Alert (Metriken, Preishistorie, Evaluierung).

| Parameter | Typ | Required | Default | Beschreibung |
|-----------|-----|----------|---------|--------------|
| `alert_id` | integer | Ja | - | ID des Alerts |
| `chart_before_minutes` | integer | Nein | 10 | Minuten vor Alert fuer Chart-Daten |
| `chart_after_minutes` | integer | Nein | 10 | Minuten nach Evaluation fuer Chart-Daten |

---

#### `get_alert_statistics`
Holt Alert-Statistiken, optional gefiltert nach Modell und Zeitraum.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `model_id` | integer | Nein | Filter nach active_model_id |
| `date_from` | string | Nein | Ab Datum ISO-Format |
| `date_to` | string | Nein | Bis Datum ISO-Format |

---

#### `get_all_models_alert_statistics`
Holt Alert-Statistiken fuer alle oder ausgewaehlte aktive Modelle (optimierte Batch-Abfrage).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_ids` | integer[] | Nein | Liste von IDs (wenn leer: alle aktiven Modelle) |

---

#### `delete_model_alerts`
Loescht alle Alert-Evaluierungen fuer ein Modell. **Nicht rueckgaengig machbar!**

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

### System (10 Tools)

#### `health_check`
Prueft den Health-Status des Pump-Servers (DB-Verbindung, aktive Modelle, Uptime).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| - | - | - | Keine Parameter |

---

#### `get_stats`
Holt umfassende Service-Statistiken (Predictions, Modelle, Webhooks, Alerts).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| - | - | - | Keine Parameter |

---

#### `get_system_config`
Holt die aktuelle persistente Konfiguration (DB-URL, Training-Service-URL, n8n-URL etc.).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| - | - | - | Keine Parameter |

---

#### `update_configuration`
Speichert die persistente Konfiguration.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `config` | object | Ja | Dict mit Keys: `database_url`, `training_service_url`, `n8n_webhook_url`, `api_port`, `streamlit_port` |

---

#### `get_logs`
Holt die letzten Log-Zeilen des Services.

| Parameter | Typ | Required | Default | Beschreibung |
|-----------|-----|----------|---------|--------------|
| `tail` | integer | Nein | 100 | Anzahl der Log-Zeilen |

---

#### `restart_system`
Initiiert einen Service-Neustart ueber SIGTERM. Supervisor startet automatisch neu.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| - | - | - | Keine Parameter |

---

#### `delete_old_logs`
Loescht ALLE alten Logs (alert_evaluations, predictions, model_predictions) fuer ein Modell. **Nicht rueckgaengig machbar!**

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

---

#### `migrate_performance_metrics`
Fuehrt die DB-Migration fuer Performance-Metriken aus (fuegt Spalten fuer Accuracy, F1 etc. hinzu).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| - | - | - | Keine Parameter |

---

#### `debug_active_models`
Debug: Zeigt alle aktiven Modelle mit vollstaendigen Details.

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| - | - | - | Keine Parameter |

---

#### `debug_coin_metrics`
Debug: Zeigt coin_metrics Statistiken (Gesamtanzahl, neuester/aeltester Eintrag, unique Coins).

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| - | - | - | Keine Parameter |

---

## Architektur

```
┌───────────────────────────────────────────────────────────────┐
│                      KI-Clients                                │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐  │
│  │ Claude Code │  │   Cursor    │  │  Eigene Anwendungen   │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬───────────┘  │
└─────────┼────────────────┼─────────────────────┼──────────────┘
          └────────────────┴─────────────────────┘
                           │
                    SSE / JSON-RPC
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│                  Frontend (Nginx :3003)                         │
│   /api/*  ─────┐                                               │
│   /mcp/*  ─────┼──────► backend:8000                          │
│   /*      ─────┘ (SPA)                                         │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI :8000)                        │
│                                                                │
│  ┌───────────────────┐   ┌──────────────────────────────────┐  │
│  │    REST API       │   │         MCP Server               │  │
│  │    /api/*         │   │  38 Tools in 5 Kategorien        │  │
│  └─────────┬─────────┘   └──────────────┬───────────────────┘  │
│            │                            │                      │
│            └────────────┬───────────────┘                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Service Layer                          │   │
│  └─────────────────────────┬───────────────────────────────┘   │
└────────────────────────────┼──────────────────────────────────┘
                             ▼
                   ┌─────────────────┐
                   │   PostgreSQL    │
                   └─────────────────┘
```

---

## Technische Details

### Dependencies

```
mcp>=1.0.0              # MCP Python SDK (offizielle Implementierung)
fastapi>=0.115.0        # Web Framework (braucht anyio>=4.5)
anyio>=4.5.0            # Async I/O (MCP Requirement)
```

### Dateien

| Datei | Beschreibung |
|-------|--------------|
| `backend/app/mcp/server.py` | MCP Server mit `mcp.server.Server`, Tool-Registry |
| `backend/app/mcp/routes.py` | SSE Transport (`SseServerTransport`), FastAPI-Endpoints |
| `backend/app/mcp/tools/models.py` | 9 Model-Management Tools |
| `backend/app/mcp/tools/predictions.py` | 7 Prediction Tools |
| `backend/app/mcp/tools/configuration.py` | 7 Configuration Tools |
| `backend/app/mcp/tools/alerts.py` | 5 Alert Tools |
| `backend/app/mcp/tools/system.py` | 10 System Tools |

---

## Fehlerbehandlung

Alle Tools geben ein einheitliches Response-Format zurueck:

```json
// Erfolg
{"success": true, "...": "..."}

// Fehler
{"success": false, "error": "Beschreibung des Fehlers"}
```

### Haeufige Fehler

| Fehler | Ursache | Loesung |
|--------|---------|--------|
| `"No active models found"` | Keine Modelle aktiviert | Modell importieren und aktivieren |
| `"Model not found"` | Ungueltige active_model_id | ID mit `list_active_models` pruefen |
| `"Database connection failed"` | DB nicht erreichbar | DB-Verbindung und DSN pruefen |
| `"Training Service unavailable"` | Training-Service offline | Service-Status pruefen |

---

## Troubleshooting

### MCP Server nicht erreichbar

```bash
# 1. Container-Status pruefen
docker-compose ps

# 2. Backend-Logs pruefen
docker-compose logs backend

# 3. Endpoint testen
curl http://localhost:3003/mcp/info

# 4. SSE-Verbindung testen
curl -N http://localhost:3003/mcp/sse
```

### SSE-Verbindung bricht ab

- `proxy_read_timeout` in Nginx erhoehen (empfohlen: `86400s`)
- `proxy_buffering off` sicherstellen
- Bei Firewalls/Load-Balancern SSE-Timeout erhoehen

### Tools werden nicht erkannt

- Client neu starten nach Konfigurationsaenderung
- `.mcp.json` auf JSON-Syntax pruefen
- URL auf Erreichbarkeit testen
