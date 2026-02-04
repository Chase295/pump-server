# MCP Server Integration

Der pump-server bietet einen integrierten MCP (Model Context Protocol) Server, der es KI-Clients wie Claude Code, Cursor, oder anderen MCP-kompatiblen Anwendungen ermöglicht, direkt mit dem ML Prediction Service zu interagieren.

---

## Übersicht

| Eigenschaft | Wert |
|-------------|------|
| **Protokoll** | MCP (Model Context Protocol) |
| **Transport** | SSE (Server-Sent Events) |
| **Base URL** | `http://localhost:3003/mcp` (via Frontend-Proxy) |
| **SSE Endpoint** | `http://localhost:3003/mcp/sse` |
| **Tools** | 13 verfügbare Tools |
| **Authentifizierung** | Keine (lokaler Zugriff) |

---

## Schnellstart

### 1. Server-Status prüfen

```bash
# Info-Endpoint aufrufen
curl http://localhost:3003/mcp/info

# Health-Check
curl http://localhost:3003/mcp/health
```

### 2. Claude Code konfigurieren

Erstelle oder erweitere die Datei `~/.claude/mcp_servers.json`:

```json
{
  "mcpServers": {
    "pump-server": {
      "transport": "sse",
      "url": "http://localhost:3003/mcp/sse",
      "name": "Pump Server ML Predictions",
      "description": "ML Prediction Service für Kryptowährungs-Vorhersagen"
    }
  }
}
```

### 3. Claude Code neu starten

Nach dem Speichern der Konfiguration Claude Code neu starten. Der MCP Server erscheint dann in der Tool-Liste.

---

## Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/mcp/info` | GET | Server-Informationen und komplette Tool-Liste |
| `/mcp/sse` | GET | SSE-Stream für bidirektionale MCP-Kommunikation |
| `/mcp/messages/` | POST | Empfängt JSON-RPC Messages vom Client (mit `session_id` Query-Parameter) |
| `/mcp/health` | GET | Health-Check mit DB-Status und Uptime |

### Beispiel: `/mcp/info` Response

```json
{
  "name": "pump-server-mcp",
  "version": "1.0.0",
  "description": "MCP Server for Pump-Server ML Prediction Service",
  "transport": "sse",
  "sse_endpoint": "/mcp/sse",
  "messages_endpoint": "/mcp/messages/",
  "tools": [
    {"name": "list_active_models", "description": "Liste aktiver ML-Modelle"},
    {"name": "predict_coin", "description": "Vorhersage für Coin"},
    ...
  ],
  "tools_count": 13
}
```

### Beispiel: `/mcp/health` Response

```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2026-02-04T20:28:25.063903",
  "checks": {
    "database": {
      "connected": true,
      "latency_ms": 36.33
    },
    "models": {
      "active_count": 1
    },
    "predictions": {
      "last_hour": 0
    }
  },
  "uptime_seconds": 3600,
  "uptime_human": "1h 0m 0s"
}
```

---

## Verfügbare Tools (13)

### Modell-Management (6 Tools)

#### `list_active_models`
Liste aller aktiven (und optional inaktiven) ML-Modelle.

**Parameter:**
| Name | Typ | Required | Default | Beschreibung |
|------|-----|----------|---------|--------------|
| `include_inactive` | boolean | Nein | `false` | Auch pausierte Modelle anzeigen |

**Beispiel Response:**
```json
{
  "success": true,
  "models": [
    {
      "id": 1,
      "model_id": 42,
      "name": "BTC-Pump-Detector-v2",
      "model_type": "xgboost",
      "is_active": true,
      "target_direction": "UP",
      "future_minutes": 5,
      "alert_threshold": 0.7,
      "total_predictions": 15420,
      "training_accuracy": 0.85,
      "training_f1": 0.72
    }
  ],
  "total": 1,
  "active_count": 1,
  "inactive_count": 0
}
```

---

#### `list_available_models`
Liste aller verfügbaren Modelle zum Import vom Training-Service.

**Parameter:** Keine

**Beispiel Response:**
```json
{
  "success": true,
  "models": [
    {
      "id": 123,
      "name": "SOL-Pump-5min",
      "model_type": "random_forest",
      "target_direction": "UP",
      "future_minutes": 5,
      "features_count": 45,
      "training_accuracy": 0.82,
      "training_f1": 0.68,
      "training_precision": 0.75,
      "training_recall": 0.62
    }
  ],
  "total": 5
}
```

---

#### `import_model`
Importiert ein Modell vom Training-Service in den Pump-Server.

**Parameter:**
| Name | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `model_id` | integer | Ja | ID des Modells im Training-Service |

**Beispiel Response:**
```json
{
  "success": true,
  "message": "Model 123 successfully imported",
  "active_model_id": 5,
  "local_path": "/app/models/model_123.pkl"
}
```

---

#### `get_model_details`
Holt detaillierte Informationen zu einem aktiven Modell.

**Parameter:**
| Name | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**Beispiel Response:**
```json
{
  "success": true,
  "model": {
    "id": 1,
    "model_id": 42,
    "name": "BTC-Pump-Detector-v2",
    "model_type": "xgboost",
    "is_active": true,
    "target_variable": "price_change_5min",
    "target_direction": "UP",
    "target_value": 0.02,
    "future_minutes": 5,
    "features": ["volume_1m", "price_change_1m", "rsi_14", ...],
    "features_count": 45,
    "alert_threshold": 0.7,
    "n8n_enabled": true,
    "n8n_webhook_url": "https://n8n.example.com/webhook/...",
    "n8n_send_mode": ["alerts_only"],
    "ignore_bad_seconds": 300,
    "ignore_positive_seconds": 600,
    "ignore_alert_seconds": 900,
    "total_predictions": 15420,
    "stats": {
      "positive_predictions": 3420,
      "negative_predictions": 12000,
      "avg_probability": 0.42
    },
    "training_accuracy": 0.85,
    "training_f1": 0.72,
    "training_precision": 0.78,
    "training_recall": 0.67,
    "created_at": "2026-01-15T10:30:00",
    "last_prediction_at": "2026-02-04T20:25:00"
  }
}
```

---

#### `activate_model`
Aktiviert ein pausiertes Modell.

**Parameter:**
| Name | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des zu aktivierenden Modells |

**Beispiel Response:**
```json
{
  "success": true,
  "message": "Model 1 activated successfully"
}
```

---

#### `deactivate_model`
Pausiert ein aktives Modell.

**Parameter:**
| Name | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des zu pausierenden Modells |

**Beispiel Response:**
```json
{
  "success": true,
  "message": "Model 1 deactivated successfully"
}
```

---

### Vorhersagen (3 Tools)

#### `predict_coin`
Macht eine ML-Vorhersage für einen Cryptocurrency-Coin.

**Parameter:**
| Name | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `coin_id` | string | Ja | Coin-ID (Mint-Adresse des Tokens) |
| `model_ids` | integer[] | Nein | Liste von active_model_ids (wenn leer: alle aktiven Modelle) |

**Beispiel Response:**
```json
{
  "success": true,
  "coin_id": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
  "timestamp": "2026-02-04T20:30:00.000000",
  "predictions": [
    {
      "model_id": 42,
      "active_model_id": 1,
      "model_name": "BTC-Pump-Detector-v2",
      "prediction": 1,
      "prediction_label": "POSITIVE (UP)",
      "probability": 0.7823
    }
  ],
  "total_models": 1,
  "successful_predictions": 1
}
```

---

#### `get_predictions`
Holt historische Vorhersagen mit Filtern.

**Parameter:**
| Name | Typ | Required | Default | Beschreibung |
|------|-----|----------|---------|--------------|
| `coin_id` | string | Nein | - | Filter nach Coin-ID |
| `active_model_id` | integer | Nein | - | Filter nach Modell |
| `prediction` | integer | Nein | - | Filter: 0=negativ, 1=positiv |
| `min_probability` | number | Nein | - | Minimale Wahrscheinlichkeit (0.0-1.0) |
| `limit` | integer | Nein | 50 | Max. Anzahl Ergebnisse |
| `offset` | integer | Nein | 0 | Offset für Pagination |

**Beispiel Response:**
```json
{
  "success": true,
  "predictions": [
    {
      "id": 12345,
      "coin_id": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
      "model_id": 42,
      "active_model_id": 1,
      "prediction": 1,
      "prediction_label": "POSITIVE",
      "probability": 0.7823,
      "data_timestamp": "2026-02-04T20:25:00",
      "created_at": "2026-02-04T20:25:01"
    }
  ],
  "count": 1,
  "limit": 50,
  "offset": 0,
  "filters": {
    "coin_id": null,
    "active_model_id": 1,
    "prediction": 1,
    "min_probability": 0.7
  }
}
```

---

#### `get_latest_prediction`
Holt die neueste Vorhersage für einen bestimmten Coin.

**Parameter:**
| Name | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `coin_id` | string | Ja | Coin-ID (Mint-Adresse) |
| `model_id` | integer | Nein | Filter nach Modell-ID |

**Beispiel Response:**
```json
{
  "success": true,
  "found": true,
  "prediction": {
    "id": 12345,
    "coin_id": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    "model_id": 42,
    "active_model_id": 1,
    "prediction": 1,
    "prediction_label": "POSITIVE",
    "probability": 0.7823,
    "data_timestamp": "2026-02-04T20:25:00",
    "created_at": "2026-02-04T20:25:01"
  }
}
```

---

### Konfiguration (2 Tools)

#### `update_alert_config`
Aktualisiert die Alert-Konfiguration eines Modells.

**Parameter:**
| Name | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |
| `n8n_webhook_url` | string | Nein | n8n Webhook URL (leer = deaktivieren) |
| `n8n_enabled` | boolean | Nein | Webhook aktivieren/deaktivieren |
| `n8n_send_mode` | string[] | Nein | `['all']`, `['alerts_only']`, `['positive_only']`, `['negative_only']` |
| `alert_threshold` | number | Nein | Alert-Schwellenwert 0.0-1.0 |
| `coin_filter_mode` | string | Nein | `'all'` oder `'whitelist'` |
| `coin_whitelist` | string[] | Nein | Liste erlaubter Coin-Adressen |
| `min_scan_interval_seconds` | integer | Nein | Minimaler Scan-Interval |

**Beispiel Response:**
```json
{
  "success": true,
  "message": "Alert config for model 1 updated successfully",
  "changes": {
    "alert_threshold": 0.75,
    "n8n_enabled": true,
    "n8n_send_mode": ["alerts_only"]
  }
}
```

---

#### `get_model_statistics`
Holt detaillierte Statistiken für ein Modell.

**Parameter:**
| Name | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `active_model_id` | integer | Ja | ID des aktiven Modells |

**Beispiel Response:**
```json
{
  "success": true,
  "active_model_id": 1,
  "statistics": {
    "total_predictions": 15420,
    "positive_predictions": 3420,
    "negative_predictions": 12000,
    "positive_rate_percent": 22.18,
    "negative_rate_percent": 77.82,
    "avg_probability": 0.4215,
    "avg_probability_positive": 0.7523,
    "avg_probability_negative": 0.3102,
    "min_probability": 0.0523,
    "max_probability": 0.9821,
    "avg_duration_ms": 45.23,
    "unique_coins": 1250,
    "alerts_count": 842,
    "first_prediction": "2026-01-15T10:35:00",
    "last_prediction": "2026-02-04T20:25:00",
    "webhook_stats": {
      "total": 842,
      "success": 835,
      "failed": 7,
      "success_rate": 99.17
    }
  }
}
```

---

### System (2 Tools)

#### `health_check`
Prüft den Health-Status des Services.

**Parameter:** Keine

**Beispiel Response:**
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2026-02-04T20:30:00.000000",
  "checks": {
    "database": {
      "connected": true,
      "latency_ms": 12.5
    },
    "models": {
      "active_count": 3
    },
    "predictions": {
      "last_hour": 1520
    }
  },
  "uptime_seconds": 86400,
  "uptime_human": "1d 0h 0m 0s"
}
```

---

#### `get_stats`
Holt umfassende Service-Statistiken.

**Parameter:** Keine

**Beispiel Response:**
```json
{
  "success": true,
  "timestamp": "2026-02-04T20:30:00.000000",
  "predictions": {
    "total": 150000,
    "last_hour": 1520,
    "last_24h": 35000,
    "last_7d": 150000,
    "positive": 33000,
    "negative": 117000,
    "positive_rate_percent": 22.0,
    "avg_probability": 0.42,
    "avg_duration_ms": 42.5,
    "unique_coins": 5200
  },
  "models": {
    "total": 5,
    "active": 3,
    "inactive": 2
  },
  "webhooks_24h": {
    "total": 2500,
    "success": 2480,
    "failed": 20
  },
  "alerts": {
    "total": 8500,
    "last_24h": 580
  },
  "uptime_seconds": 86400
}
```

---

## Integration mit anderen Tools

### Cursor IDE

Cursor unterstützt MCP nativ. Konfiguration in `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pump-server": {
      "transport": "sse",
      "url": "http://localhost:3003/mcp/sse"
    }
  }
}
```

### Eigene Anwendung

Für die Integration in eigene Anwendungen:

```python
# Python Beispiel mit httpx-sse
import httpx
from httpx_sse import connect_sse

async def connect_to_mcp():
    async with httpx.AsyncClient() as client:
        async with connect_sse(client, "GET", "http://localhost:3003/mcp/sse") as event_source:
            async for event in event_source.aiter_sse():
                print(f"Event: {event.event}, Data: {event.data}")
```

```javascript
// JavaScript Beispiel mit EventSource
const eventSource = new EventSource('http://localhost:3003/mcp/sse');

eventSource.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
};
```

---

## Architektur

```
┌────────────────────────────────────────────────────────────────┐
│                     KI-Clients                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Claude Code │  │   Cursor    │  │  Eigene Anwendungen     │ │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘ │
└─────────┼────────────────┼──────────────────────┼──────────────┘
          │                │                      │
          └────────────────┴──────────────────────┘
                           │
                    SSE / JSON-RPC
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                   Frontend (Nginx :3003)                        │
│                                                                 │
│   /api/*  ──────────────────┐                                   │
│   /mcp/*  ──────────────────┼──────► pump-server-backend:8000  │
└─────────────────────────────┼──────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI :8000)                       │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐│
│  │     REST API         │  │          MCP Server              ││
│  │     /api/*           │  │          /mcp/*                  ││
│  │                      │  │                                  ││
│  │  - Models            │  │  - list_active_models            ││
│  │  - Predictions       │  │  - predict_coin                  ││
│  │  - Alerts            │  │  - get_stats                     ││
│  │  - Stats             │  │  - ...                           ││
│  └──────────┬───────────┘  └────────────────┬─────────────────┘│
│             │                               │                   │
│             └───────────────┬───────────────┘                   │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Service Layer                          │  │
│  │                                                           │  │
│  │  database/models.py    - DB Operations                    │  │
│  │  prediction/engine.py  - ML Predictions                   │  │
│  │  utils/metrics.py      - Prometheus Metrics               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (External)    │
                    └─────────────────┘
```

---

## Technische Details

### Dependencies

```
mcp>=1.0.0              # MCP Python SDK
sse-starlette>=1.6.5    # SSE Support für FastAPI
anyio>=4.5.0            # Async I/O (MCP Requirement)
fastapi>=0.115.0        # Web Framework
```

### Dateien

| Datei | Beschreibung |
|-------|--------------|
| `backend/app/mcp/__init__.py` | Modul-Initialisierung und Exports |
| `backend/app/mcp/server.py` | MCP Server, Tool-Registry und Dispatcher |
| `backend/app/mcp/routes.py` | FastAPI-Endpunkte für SSE |
| `backend/app/mcp/tools/models.py` | 6 Model-Management Tools |
| `backend/app/mcp/tools/predictions.py` | 3 Prediction Tools |
| `backend/app/mcp/tools/configuration.py` | 2 Configuration Tools |
| `backend/app/mcp/tools/system.py` | 2 System Tools |

### Nginx-Konfiguration

Der MCP-Endpoint wird über Nginx proxied mit SSE-spezifischen Einstellungen:

```nginx
location /mcp/ {
    proxy_pass http://pump-server-backend:8000/mcp/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # SSE-spezifische Einstellungen
    proxy_set_header Connection "";
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;  # 24h für lange SSE-Verbindungen
}
```

---

## Fehlerbehandlung

Alle Tools geben ein einheitliches Response-Format zurück:

### Erfolg
```json
{
  "success": true,
  "...": "..."
}
```

### Fehler
```json
{
  "success": false,
  "error": "Beschreibung des Fehlers"
}
```

### Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `"No active models found"` | Keine Modelle aktiviert | Modell importieren und aktivieren |
| `"Model not found"` | Ungültige active_model_id | ID mit `list_active_models` prüfen |
| `"Database connection failed"` | DB nicht erreichbar | DB-Verbindung und DSN prüfen |
| `"Training Service unavailable"` | Training-Service offline | Service-Status prüfen |

---

## Verwendungsbeispiele

### Beispiel 1: Modell-Übersicht abrufen

```
Benutzer: "Zeige mir alle aktiven ML-Modelle"

Claude verwendet: list_active_models

Response: "Du hast aktuell 3 aktive Modelle:
1. BTC-Pump-5min (ID: 1) - Accuracy: 85%, 15.420 Predictions
2. SOL-Detector (ID: 2) - Accuracy: 82%, 8.230 Predictions
3. ETH-Trend (ID: 3) - Accuracy: 79%, 5.100 Predictions"
```

### Beispiel 2: Vorhersage für Coin

```
Benutzer: "Mache eine Vorhersage für den Coin mit Adresse 7xKXtg..."

Claude verwendet: predict_coin mit coin_id="7xKXtg..."

Response: "Vorhersage für Coin 7xKXtg...:
- Modell 'BTC-Pump-5min': POSITIV mit 78.2% Wahrscheinlichkeit
- Modell 'SOL-Detector': NEGATIV mit 35.1% Wahrscheinlichkeit"
```

### Beispiel 3: Alert-Konfiguration ändern

```
Benutzer: "Setze den Alert-Threshold für Modell 1 auf 80%"

Claude verwendet: update_alert_config mit active_model_id=1, alert_threshold=0.8

Response: "Alert-Threshold für Modell 1 wurde auf 80% gesetzt."
```

---

## Troubleshooting

### MCP Server nicht erreichbar

1. Container-Status prüfen:
   ```bash
   docker-compose ps
   ```

2. Backend-Logs prüfen:
   ```bash
   docker-compose logs pump-server-backend
   ```

3. Endpoint testen:
   ```bash
   curl http://localhost:3003/mcp/info
   ```

### SSE-Verbindung bricht ab

- Prüfen ob `proxy_read_timeout` in Nginx ausreichend hoch ist
- Bei Firewalls/Load-Balancern SSE-Timeout erhöhen

### Tools werden nicht erkannt

- Claude Code neu starten nach Konfigurationsänderung
- Konfigurationsdatei auf JSON-Syntax prüfen
- URL auf Erreichbarkeit testen
