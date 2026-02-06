# Pump Server - Entwicklerdokumentation

Pump Server fuer Kryptowaehrungs-Vorhersagen mit trainierten Machine Learning Modellen.

## Quick Start

```bash
# 1. Environment konfigurieren
cp .env.example .env
# .env anpassen (DB_DSN, TRAINING_SERVICE_API_URL)

# 2. Services starten
docker-compose up -d

# 3. Frontend oeffnen
open http://localhost:3003
```

## Dokumentationsuebersicht

### Architektur
| Datei | Beschreibung |
|-------|--------------|
| [overview.md](architecture/overview.md) | System-Architektur, Tech-Stack, Diagramme |
| [backend.md](architecture/backend.md) | FastAPI Backend, Module, 38 MCP Tools |

### API
| Datei | Beschreibung |
|-------|--------------|
| [mcp-server.md](api/mcp-server.md) | MCP Server - 38 Tools in 5 Kategorien |

### Anleitungen
| Datei | Beschreibung |
|-------|--------------|
| [MCP_INTEGRATION_ANLEITUNG.md](MCP_INTEGRATION_ANLEITUNG.md) | MCP Server in FastAPI integrieren (Vorlage fuer neue Projekte) |

### Planung
| Datei | Beschreibung |
|-------|--------------|
| [ALERT_SYSTEM_PLAN.md](ALERT_SYSTEM_PLAN.md) | Alert-System Planungsdokument |
| [PLAN_MODEL_IMPORT_REDESIGN.md](PLAN_MODEL_IMPORT_REDESIGN.md) | Model-Import Redesign Plan |

### Referenz
| Datei | Beschreibung |
|-------|--------------|
| [glossary.md](glossary.md) | Begriffe und Definitionen |

## Projektstruktur

```
pump-server/
├── backend/                 # Python FastAPI Backend
│   ├── app/
│   │   ├── api/            # REST API Routes & Schemas
│   │   ├── database/       # DB Models & Connection
│   │   ├── mcp/            # MCP Server (38 Tools)
│   │   ├── prediction/     # ML Engine & Processing
│   │   └── utils/          # Config, Logging, Metrics
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # React TypeScript Frontend
│   ├── src/
│   │   ├── components/     # Reusable Components
│   │   ├── pages/          # Page Components
│   │   ├── services/       # API Client
│   │   └── types/          # TypeScript Types
│   └── Dockerfile
├── docs/                   # Diese Dokumentation
├── sql/                    # SQL Migrations & Schema
├── docker-compose.yml
├── .env.example
├── .mcp.json               # MCP Client-Konfiguration
└── CLAUDE.md               # AI Assistant Guide
```

## Tech Stack

| Komponente | Technologie |
|------------|-------------|
| Backend | Python 3.11, FastAPI, asyncpg |
| ML | scikit-learn, XGBoost |
| Frontend | React 18, TypeScript, MUI v7, Zustand, React Query |
| Database | PostgreSQL (extern) |
| MCP Server | Offizielle MCP SDK, SSE Transport |
| Deployment | Docker, Nginx, Supervisor |

## Services

| Service | Port | Beschreibung |
|---------|------|--------------|
| backend | 8000 (intern) | FastAPI + Event Handler + Streamlit |
| frontend | 3003 | React UI mit Nginx Proxy |

## Weiterfuehrende Links

- [CLAUDE.md](../CLAUDE.md) - AI Assistant Konfiguration
- [.env.example](../.env.example) - Beispiel Environment
- [docker-compose.yml](../docker-compose.yml) - Docker Setup
- [sql/SCHEMA_DOKUMENTATION.md](../sql/SCHEMA_DOKUMENTATION.md) - Datenbank-Schema
