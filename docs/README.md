# Pump Server - Entwicklerdokumentation

ML Prediction Service für Kryptowährungs-Vorhersagen mit trainiereten Machine Learning Modellen.

## Quick Start

```bash
# 1. Environment konfigurieren
cp .env.example .env
# .env anpassen (DB_DSN, TRAINING_SERVICE_API_URL)

# 2. Services starten
docker-compose up -d

# 3. Frontend öffnen
open http://localhost:3003
```

## Dokumentationsübersicht

### Architecture
| Datei | Beschreibung |
|-------|--------------|
| [overview.md](architecture/overview.md) | System-Architektur, Tech-Stack, Diagramme |
| [backend.md](architecture/backend.md) | FastAPI Backend, Module, Supervisor |
| [frontend.md](architecture/frontend.md) | React UI, Components, State Management |
| [data-flow.md](architecture/data-flow.md) | Datenfluss-Diagramme, Event Processing |

### API
| Datei | Beschreibung |
|-------|--------------|
| [endpoints.md](api/endpoints.md) | Alle 40+ REST API Endpoints |
| [schemas.md](api/schemas.md) | Pydantic & TypeScript Schemas |
| [mcp-server.md](api/mcp-server.md) | MCP Server für Claude Code Integration |

### Algorithms
| Datei | Beschreibung |
|-------|--------------|
| [prediction-engine.md](algorithms/prediction-engine.md) | ML Prediction Pipeline |
| [feature-processing.md](algorithms/feature-processing.md) | Feature Engineering |
| [alert-evaluation.md](algorithms/alert-evaluation.md) | Alert Evaluator Service |
| [event-handler.md](algorithms/event-handler.md) | Event-Driven Processing |

### Database
| Datei | Beschreibung |
|-------|--------------|
| [schema.md](database/schema.md) | Tabellen, ER-Diagramm, Indexes |
| [migrations.md](database/migrations.md) | Migration History & Patterns |
| [queries.md](database/queries.md) | Wichtige SQL Queries |

### Deployment
| Datei | Beschreibung |
|-------|--------------|
| [docker.md](deployment/docker.md) | Docker Compose, Dockerfiles |
| [environment.md](deployment/environment.md) | Umgebungsvariablen |
| [monitoring.md](deployment/monitoring.md) | Health Checks, Prometheus |

### Reference
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
│   │   ├── mcp/            # MCP Server für KI-Integration
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
├── sql/                    # SQL Migrations
├── docker-compose.yml
├── .env.example
└── CLAUDE.md               # AI Assistant Guide
```

## Tech Stack

| Komponente | Technologie |
|------------|-------------|
| Backend | Python 3.11, FastAPI, asyncpg |
| ML | scikit-learn, XGBoost |
| Frontend | React 18, TypeScript, MUI v7 |
| Database | PostgreSQL (extern) |
| Deployment | Docker, Nginx, Supervisor |
| Monitoring | Prometheus Metrics |

## Services

| Service | Port | Beschreibung |
|---------|------|--------------|
| pump-server-backend | 8000 (intern) | FastAPI + Event Handler + Streamlit |
| pump-server-frontend | 3003 | React UI mit Nginx Proxy |

## Weiterführende Links

- [CLAUDE.md](../CLAUDE.md) - AI Assistant Konfiguration
- [.env.example](../.env.example) - Beispiel Environment
- [docker-compose.yml](../docker-compose.yml) - Docker Setup
