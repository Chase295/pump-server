# CLAUDE.md - Project Guide for AI Assistants

## Project Overview

Pump Server - A real-time machine learning prediction service that monitors cryptocurrency metrics and makes predictions using trained models.

## Tech Stack

### Backend (Python)
- **Framework**: FastAPI (>=0.115.0)
- **Database**: PostgreSQL with asyncpg
- **ML Libraries**: scikit-learn (1.3.2), XGBoost (2.0.2), pandas, numpy
- **Web UI**: Streamlit (8502)
- **Process Management**: Supervisor (runs FastAPI, Streamlit, and Event Handler)
- **MCP Server**: Model Context Protocol for AI client integration

### Frontend (TypeScript/React)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: MUI (Material-UI v7)
- **State Management**: Zustand, React Query
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts

## Project Structure

```
pump-server/
├── backend/                      # Python FastAPI Backend
│   ├── app/                      # Application code
│   │   ├── api/                  # FastAPI routes and schemas
│   │   ├── database/             # DB models and connection
│   │   ├── mcp/                  # MCP Server for AI integration
│   │   ├── prediction/           # ML prediction engine
│   │   ├── streamlit_pages/      # Streamlit UI pages
│   │   ├── utils/                # Config, logging, metrics
│   │   ├── main.py               # FastAPI app entry point
│   │   └── streamlit_app.py      # Streamlit entry point
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                     # React TypeScript Frontend
│   ├── src/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
│
├── docs/                         # Documentation
├── sql/                          # SQL scripts and migrations
│
├── docker-compose.yml            # Docker orchestration
├── .env                          # Environment variables (git-ignored)
├── .env.example                  # Example environment config
├── CLAUDE.md
└── README.md
```

## Key Commands

### Docker
```bash
# Build and start all services
docker-compose up -d

# Build specific service
docker-compose build pump-server-backend
docker-compose build pump-server-frontend

# View logs
docker-compose logs -f
docker-compose logs -f pump-server-backend

# Stop services
docker-compose down
```

### Testing MCP Server
```bash
# Check MCP info
curl http://localhost:3003/mcp/info

# Check MCP health
curl http://localhost:3003/mcp/health

# Test SSE connection
curl -N http://localhost:3003/mcp/sse
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/models/available` - List available models for import
- `POST /api/models/import` - Import a model
- `GET /api/models/active` - List active models
- `POST /api/predict` - Make a prediction
- `GET /api/predictions` - List predictions
- `GET /api/stats` - Service statistics

## MCP Server

The pump-server includes an integrated MCP (Model Context Protocol) server for AI client integration (e.g., Claude Code).

### MCP Endpoints
- `GET /mcp/info` - Server information and tool list
- `GET /mcp/sse` - SSE stream for real-time communication
- `POST /mcp/messages/` - JSON-RPC messages (with session_id)
- `GET /mcp/health` - MCP server health status

### Available Tools (13)
- **Model Tools**: list_active_models, list_available_models, import_model, get_model_details, activate_model, deactivate_model
- **Prediction Tools**: predict_coin, get_predictions, get_latest_prediction
- **Config Tools**: update_alert_config, get_model_statistics
- **System Tools**: health_check, get_stats

## Environment Variables

- `DB_DSN` - PostgreSQL connection string
- `TRAINING_SERVICE_API_URL` - URL to training service API
- `N8N_WEBHOOK_URL` - n8n webhook for alerts (optional)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
