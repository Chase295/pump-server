# System-Architektur Übersicht

## Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │   Browser    │    │  PostgreSQL  │    │   Training Service API   │  │
│  │  (User UI)   │    │  (External)  │    │   (Model Downloads)      │  │
│  └──────┬───────┘    └──────┬───────┘    └────────────┬─────────────┘  │
└─────────┼───────────────────┼─────────────────────────┼─────────────────┘
          │ :3003             │ :5432                   │ HTTPS
          ▼                   ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOCKER NETWORK                                   │
│                      pump-server-network                                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   pump-server-frontend                           │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │                      NGINX                               │    │   │
│  │  │  ┌─────────────┐         ┌─────────────────────────┐    │    │   │
│  │  │  │  /api/*     │────────▶│  proxy_pass backend     │    │    │   │
│  │  │  │  Proxy      │         │  :8000                  │    │    │   │
│  │  │  └─────────────┘         └─────────────────────────┘    │    │   │
│  │  │  ┌─────────────┐         ┌─────────────────────────┐    │    │   │
│  │  │  │  /mcp/*     │────────▶│  proxy_pass backend     │    │    │   │
│  │  │  │  MCP Server │         │  :8000 (SSE)            │    │    │   │
│  │  │  └─────────────┘         └─────────────────────────┘    │    │   │
│  │  │  ┌─────────────┐                                        │    │   │
│  │  │  │  /*         │─────────▶ React SPA (index.html)       │    │   │
│  │  │  │  Static     │                                        │    │   │
│  │  │  └─────────────┘                                        │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   pump-server-backend                            │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │                    SUPERVISOR                            │    │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │   │
│  │  │  │   FastAPI    │  │Event Handler │  │  Streamlit   │  │    │   │
│  │  │  │   :8000      │  │  Background  │  │   :8501      │  │    │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │                                                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │  VOLUMES                                                  │   │   │
│  │  │  /app/models  /app/logs  /app/config  /tmp/models        │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend (Python 3.11)

| Komponente | Version | Verwendung |
|------------|---------|------------|
| FastAPI | >=0.115.0 | REST API Framework |
| uvicorn | >=0.30.0 | ASGI Server |
| asyncpg | 0.29.0 | Async PostgreSQL Driver |
| pydantic | >=2.5.0 | Data Validation |
| scikit-learn | 1.3.2 | ML Models (RandomForest) |
| XGBoost | 2.0.2 | ML Models (XGBoost) |
| pandas | 2.1.3 | Data Processing |
| numpy | 1.26.2 | Numerical Computing |
| joblib | 1.3.2 | Model Serialization |
| streamlit | 1.28.0 | Admin Web UI |
| prometheus-client | 0.19.0 | Metrics Export |
| aiohttp | >=3.9.1 | Async HTTP (n8n) |
| mcp | >=1.0.0 | MCP Protocol SDK |
| sse-starlette | >=1.6.5 | SSE für MCP Server |

### Frontend (Node 22)

| Komponente | Verwendung |
|------------|------------|
| React 18 | UI Framework |
| TypeScript | Type Safety |
| Vite | Build Tool |
| MUI v7 | Component Library |
| React Query | Data Fetching & Caching |
| Zustand | State Management |
| React Hook Form | Form Handling |
| Zod | Schema Validation |
| Axios | HTTP Client |
| Recharts | Charts |

### Infrastructure

| Komponente | Verwendung |
|------------|------------|
| Docker | Containerization |
| Nginx | Reverse Proxy |
| Supervisor | Process Management |
| PostgreSQL | Database (extern) |

## Docker Volumes

```
volumes:
  pump-server-models    → /app/models     # ML Model Files (.pkl)
  pump-server-logs      → /app/logs       # Application Logs
  pump-server-config    → /app/config     # Persistent UI Config
  pump-server-tmp       → /tmp/models     # Temporary Model Storage
```

## Service-Kommunikation

### Frontend → Backend
```
Browser → :3003 → Nginx → /api/* → proxy_pass → backend:8000
```

### Backend → Database
```
FastAPI/EventHandler → asyncpg pool → PostgreSQL:5432 (extern)
```

### Backend → Training Service
```
Model Import → httpx → TRAINING_SERVICE_API_URL/api/models
```

### Backend → n8n
```
Alert Trigger → aiohttp → N8N_WEBHOOK_URL (per Model konfigurierbar)
```

## Prozess-Architektur (Backend)

Der Backend-Container führt 3 Prozesse unter Supervisor aus:

```
supervisord
├── fastapi      # REST API (Port 8000)
│   └── uvicorn app.main:app
├── event-handler # Background Prediction Processing
│   └── python app/prediction/event_handler.py
└── streamlit    # Admin UI (Port 8501, intern)
    └── streamlit run app/streamlit_app.py
```

### Prozess-Verantwortlichkeiten

| Prozess | Verantwortlichkeit |
|---------|-------------------|
| FastAPI | REST API, Health Checks, Metrics |
| Event Handler | LISTEN/NOTIFY, Batch Predictions, n8n Webhooks |
| Streamlit | Admin UI für Modellverwaltung (intern) |

## Netzwerk-Ports

| Port | Service | Zugriff |
|------|---------|---------|
| 3003 | Frontend (Nginx) | Extern (Published) |
| 3000 | Frontend (intern) | Docker intern |
| 8000 | Backend API | Docker intern |
| 8501 | Streamlit | Docker intern |
| 5432 | PostgreSQL | Extern (Host Network) |

## Datenbank-Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL (extern)                          │
│                                                                      │
│  ┌──────────────────────┐    ┌──────────────────────┐              │
│  │ prediction_active_   │    │   model_predictions   │              │
│  │ models               │◄───│                       │              │
│  │ (Aktive Modelle)     │    │ (Vorhersagen)        │              │
│  └──────────────────────┘    └──────────────────────┘              │
│            │                           │                            │
│            │                           ▼                            │
│            │                 ┌──────────────────────┐              │
│            │                 │  alert_evaluations   │              │
│            │                 │  (Alert Auswertung)  │              │
│            │                 └──────────────────────┘              │
│            │                                                        │
│            ▼                                                        │
│  ┌──────────────────────┐                                          │
│  │   coin_scan_cache    │                                          │
│  │   (Scan Cache)       │                                          │
│  └──────────────────────┘                                          │
│                                                                      │
│  ┌──────────────────────┐    ┌──────────────────────┐              │
│  │    coin_metrics      │    │      ml_models       │              │
│  │  (Extern, Read-Only) │    │ (Training Service)   │              │
│  └──────────────────────┘    └──────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## Weiterführende Dokumentation

- [Backend Architektur](backend.md) - Detaillierte Backend-Dokumentation
- [Frontend Architektur](frontend.md) - React UI Dokumentation
- [Datenfluss](data-flow.md) - Detaillierte Flow-Diagramme
