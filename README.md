# Pump Server

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-%23336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)

Machine Learning Prediction Service - Echtzeit-Vorhersagen fuer Kryptowaehrungen mit trainierten Modellen.

## Uebersicht

Dieser Service:
- Laedt ML-Modelle vom Training Service
- Ueberwacht `coin_metrics` fuer neue Eintraege (LISTEN/NOTIFY oder Polling)
- Macht automatisch Vorhersagen mit allen aktiven Modellen
- Sendet Alerts an n8n (optional)
- Bietet REST API + MCP Server (38 Tools) fuer KI-Clients
- React Frontend fuer Modell-Verwaltung und Alert-Monitoring

## Quick Start mit Docker

### Voraussetzungen
- Docker & Docker Compose
- Externe PostgreSQL-Datenbank (geteilt mit Training Service)
- Training Service API erreichbar (fuer Modell-Download)

### Starten

```bash
cd pump-server

# Container bauen und starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f

# Health Check testen
curl http://localhost:3003/api/health

# Container stoppen
docker-compose down
```

### Environment Variables

Wichtigste Variablen (siehe `.env.example`):
- `DB_DSN` - Externe Datenbank-Verbindung
- `TRAINING_SERVICE_API_URL` - URL zum Training Service
- `MODEL_STORAGE_PATH` - Pfad fuer Modell-Dateien
- `N8N_WEBHOOK_URL` - n8n Webhook (optional)

## Web UI

### React Frontend (Port 3003)
- Dashboard mit Modell-Uebersicht
- Modell importieren, aktivieren, konfigurieren
- Alert-System mit Statistiken und Evaluierungen
- Coin-Detail-Ansicht mit Preishistorie

### Streamlit Admin UI (Port 8502)
- Alternatives Admin-Interface
- Live-Logs vom Container

## API Endpoints

### Models
- `GET /api/models/available` - Verfuegbare Modelle (fuer Import)
- `POST /api/models/import` - Modell importieren
- `GET /api/models/active` - Aktive Modelle
- `POST /api/models/{id}/activate` - Modell aktivieren
- `POST /api/models/{id}/deactivate` - Modell deaktivieren
- `PATCH /api/models/{id}/rename` - Modell umbenennen
- `DELETE /api/models/{id}` - Modell loeschen

### Predictions
- `POST /api/predict` - Manuelle Vorhersage
- `GET /api/predictions` - Liste von Vorhersagen
- `GET /api/predictions/latest/{coin_id}` - Neueste Vorhersage

### Alerts
- `GET /api/alerts` - Alert-Liste
- `GET /api/alerts/statistics` - Alert-Statistiken
- `PATCH /api/models/{id}/alert-config` - Alert-Konfiguration

### System
- `GET /api/health` - Health Check
- `GET /api/metrics` - Prometheus Metrics
- `GET /api/stats` - Statistiken

## MCP Server

Der Pump Server bietet einen integrierten MCP (Model Context Protocol) Server mit **38 Tools in 5 Kategorien** fuer KI-Clients wie Claude Code oder Cursor.

### Schnellstart

```bash
# MCP Info
curl http://localhost:3003/mcp/info

# SSE-Verbindung testen
curl -N http://localhost:3003/mcp/sse
```

### Client-Konfiguration

`.mcp.json` im Projektroot:

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

### Tool-Kategorien

| Kategorie | Anzahl | Beispiele |
|-----------|--------|-----------|
| Model-Management | 9 | `list_active_models`, `import_model`, `delete_model` |
| Predictions | 7 | `predict_coin`, `get_predictions`, `get_model_predictions` |
| Konfiguration | 7 | `update_alert_config`, `get_ignore_settings` |
| Alerts | 5 | `get_alerts`, `get_alert_statistics` |
| System | 10 | `health_check`, `get_stats`, `get_logs` |

Vollstaendige Dokumentation: [docs/api/mcp-server.md](docs/api/mcp-server.md)

## Dokumentation

- [docs/](docs/) - Entwicklerdokumentation
- [docs/api/mcp-server.md](docs/api/mcp-server.md) - MCP Server API (38 Tools)
- [docs/MCP_INTEGRATION_ANLEITUNG.md](docs/MCP_INTEGRATION_ANLEITUNG.md) - MCP in FastAPI integrieren
- [sql/SCHEMA_DOKUMENTATION.md](sql/SCHEMA_DOKUMENTATION.md) - Datenbank-Schema
- Swagger UI: `http://localhost:3003/docs`

## Deployment

### Coolify

1. Repository in Coolify verbinden
2. Docker Compose Deployment waehlen
3. Environment Variables setzen
4. Deploy!

## Wichtige Hinweise

- **Externe Datenbank:** DB laeuft nicht im Container!
- **Modell-Dateien:** Werden automatisch vom Training Service heruntergeladen
- **LISTEN/NOTIFY:** Fuer Echtzeit (< 100ms), Fallback: Polling (30s)
- **Docker Services:** `backend` und `frontend` (in docker-compose.yml)
