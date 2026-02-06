# Pump Server - Frontend

React TypeScript Frontend fuer den Pump Server ML Prediction Service.

## Tech Stack

| Technologie | Version | Verwendung |
|-------------|---------|-----------|
| React | 18 | UI Framework |
| TypeScript | ~5.9 | Type Safety |
| Vite | 7 | Build Tool & Dev Server |
| MUI (Material-UI) | v7 | UI-Komponenten |
| Zustand | 5 | State Management |
| React Query | 5 | Server State & Caching |
| React Hook Form + Zod | 7 / 4 | Formular-Validierung |
| Recharts | 3 | Diagramme |
| React Router | 7 | Routing |
| Axios | 1 | HTTP Client |

## Projektstruktur

```
frontend/
├── src/
│   ├── App.tsx             # Haupt-App mit Routing
│   ├── main.tsx            # React Entry Point
│   ├── components/         # Wiederverwendbare Komponenten
│   ├── pages/              # Seiten-Komponenten
│   ├── services/           # API-Client (Axios)
│   ├── types/              # TypeScript Type Definitions
│   └── assets/             # Statische Assets
├── public/                 # Oeffentliche Dateien
├── Dockerfile              # Multi-Stage Build (Node + Nginx)
├── package.json
├── vite.config.ts          # Vite + Code-Splitting Config
└── tsconfig.json
```

## Entwicklung

```bash
# Dependencies installieren
npm install

# Dev-Server starten (Port 5173)
npm run dev

# Build fuer Produktion
npm run build

# Lint
npm run lint
```

## Build & Deployment

Das Frontend wird als Multi-Stage Docker-Image gebaut:

1. **Builder:** Node 22 - Kompiliert React App mit Vite
2. **Production:** Nginx Alpine - Served statische Dateien

### Nginx Proxy

Nginx leitet Requests weiter:
- `/api/*` -> `backend:8000` (REST API)
- `/mcp/*` -> `backend:8000` (MCP Server, mit SSE-Support)
- `/*` -> React SPA (`index.html` via `try_files`)

### Build

```bash
# Frontend-Image bauen
docker-compose build frontend

# Oder standalone
docker build -t pump-server-frontend .
```

## Code-Splitting

Vite ist konfiguriert fuer optimiertes Chunk-Splitting:

| Chunk | Inhalt |
|-------|--------|
| `vendor` | react, react-dom |
| `mui` | @mui/material, @mui/icons-material, @emotion |
| `router` | react-router-dom |
| `query` | @tanstack/react-query |
| `charts` | recharts |
