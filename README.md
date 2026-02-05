# 🚀 Pump Server

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-%23336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)

Machine Learning Prediction Service für Coin-Bot - Echtzeit-Vorhersagen mit trainierten Modellen.

## 📋 Übersicht

Dieser Service:
- ✅ Lädt Modelle vom Training Service
- ✅ Überwacht `coin_metrics` für neue Einträge (LISTEN/NOTIFY oder Polling)
- ✅ Macht automatisch Vorhersagen mit allen aktiven Modellen
- ✅ Sendet Vorhersagen an n8n (optional)
- ✅ Bietet REST API für manuelle Vorhersagen und Modell-Verwaltung

## 🐳 Quick Start mit Docker

### Voraussetzungen
- Docker & Docker Compose
- Externe PostgreSQL-Datenbank (geteilt mit Training Service)
- Training Service API erreichbar (für Modell-Download)

### Lokales Testing

```bash
cd pump-server

# Container bauen und starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f

# Health Check testen
curl http://localhost:8006/api/health

# Container stoppen
docker-compose down
```

### Environment Variables

Wichtigste Variablen (siehe `.env.example`):
- `DB_DSN` - Externe Datenbank-Verbindung
- `TRAINING_SERVICE_API_URL` - URL zum Training Service
- `MODEL_STORAGE_PATH` - Pfad für Modell-Dateien
- `N8N_WEBHOOK_URL` - n8n Webhook (optional)

## 🎨 Web UI

Die Streamlit UI ist verfügbar unter:
- **Streamlit UI:** http://localhost:8502
- **FastAPI API:** http://localhost:8006

**Funktionen:**
- 🏠 Übersicht: Alle aktiven Modelle anzeigen und verwalten
- 📥 Modell importieren: Modelle vom Training Service importieren
- 🔮 Vorhersage: Manuelle Vorhersagen für Coins
- 📋 Vorhersagen: Liste aller Vorhersagen mit Filtern
- 📊 Statistiken: Service-Statistiken und Health Status
- 📜 Logs: Live-Logs vom Container anzeigen

## 📡 API Endpoints

### Models
- `GET /api/models/available` - Verfügbare Modelle (für Import)
- `POST /api/models/import` - Modell importieren
- `GET /api/models/active` - Aktive Modelle
- `POST /api/models/{id}/activate` - Modell aktivieren
- `POST /api/models/{id}/deactivate` - Modell deaktivieren
- `PATCH /api/models/{id}/rename` - Modell umbenennen
- `DELETE /api/models/{id}` - Modell löschen

### Predictions
- `POST /api/predict` - Manuelle Vorhersage
- `GET /api/predictions` - Liste von Vorhersagen
- `GET /api/predictions/latest/{coin_id}` - Neueste Vorhersage

### System
- `GET /api/health` - Health Check
- `GET /api/metrics` - Prometheus Metrics
- `GET /api/stats` - Statistiken

## 🔧 Konfiguration

Alle Konfiguration über Environment Variables (siehe `app/utils/config.py`).

## 📚 Dokumentation

- `ML_PREDICTION_SERVICE_AUFBAU_ANLEITUNG.md` - Vollständige Aufbau-Anleitung
- `API_BEISPIELE.md` - Praktische API-Beispiele mit curl und Python
- `sql/SCHEMA_DOKUMENTATION.md` - Datenbank-Schema Dokumentation
- API-Dokumentation: `http://localhost:8006/docs` (Swagger UI)
- Tests: `tests/test_e2e.py` - End-to-End Test-Suite

## 🚀 Deployment

### Coolify

1. Repository in Coolify verbinden
2. Docker Compose Deployment wählen
3. `docker-compose.coolify.yml` verwenden
4. Environment Variables setzen
5. Deploy!

Siehe `ML_PREDICTION_SERVICE_AUFBAU_ANLEITUNG.md` für Details.

## ⚠️ Wichtige Hinweise

- **Externe Datenbank:** DB läuft nicht im Container!
- **Modell-Dateien:** Müssen verfügbar sein (Volume oder Shared Storage)
- **Training Service:** Muss erreichbar sein für Modell-Download
- **LISTEN/NOTIFY:** Für Echtzeit (< 100ms), Fallback: Polling (30s)

## 📊 Status

- ✅ Phase 1: Grundlagen & Datenbank
- ✅ Phase 2: Core-Komponenten
- ✅ Phase 3: Prediction Engine
- ✅ Phase 4: REST API
- ✅ Phase 5: Docker & Deployment
- ✅ Phase 6: Testing & Optimierung
- ✅ Phase 7: Streamlit UI
