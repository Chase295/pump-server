# Backend Architektur

## Übersicht

Das Backend ist eine FastAPI-Anwendung mit drei Hauptprozessen unter Supervisor:
- **FastAPI** (REST API + MCP Server auf Port 8000)
- **Event Handler** (Background Processing)
- **Streamlit** (Admin UI auf Port 8501)

## Verzeichnisstruktur

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI Entry Point
│   ├── streamlit_app.py        # Streamlit Admin UI
│   ├── streamlit_utils.py      # Streamlit Helpers
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # 40+ API Endpoints
│   │   ├── schemas.py          # Pydantic Models
│   │   └── schemas_ml_training.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py       # asyncpg Pool Management
│   │   ├── models.py           # DB CRUD Operations
│   │   ├── alert_models.py     # Alert Evaluation
│   │   ├── ath_tracker.py      # ATH Tracking
│   │   └── utils.py            # DB Utilities
│   │
│   ├── mcp/                    # MCP Server für KI-Integration
│   │   ├── __init__.py
│   │   ├── server.py           # MCP Server & Tool-Registry
│   │   ├── routes.py           # FastAPI SSE Endpoints
│   │   └── tools/              # 13 MCP Tools
│   │       ├── models.py       # Model-Management Tools
│   │       ├── predictions.py  # Prediction Tools
│   │       ├── configuration.py # Config Tools
│   │       └── system.py       # System Tools
│   │
│   ├── prediction/
│   │   ├── __init__.py
│   │   ├── engine.py           # Core Prediction Logic
│   │   ├── feature_processor.py # Feature Engineering
│   │   ├── model_manager.py    # Model Loading & Caching
│   │   ├── event_handler.py    # Event-Driven Processing
│   │   ├── alert_evaluator.py  # Background Alert Service
│   │   └── n8n_client.py       # n8n Webhook Integration
│   │
│   ├── streamlit_pages/
│   │   ├── __init__.py
│   │   ├── overview.py         # Dashboard
│   │   ├── details.py          # Model Details
│   │   ├── model_import.py     # Model Import
│   │   ├── alert_system.py     # Alert System
│   │   ├── alert_config.py     # Alert Configuration
│   │   └── tabs.py             # Tab Navigation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # Configuration Management
│       ├── logging_config.py   # Structured Logging
│       ├── metrics.py          # Prometheus Metrics
│       └── exceptions.py       # Custom Exceptions
│
├── Dockerfile
├── requirements.txt
└── .dockerignore
```

## Entry Points

### main.py - FastAPI Application

```python
# Wichtige Komponenten:

# 1. App-Initialisierung
app = FastAPI(title="Pump Server")

# 2. Middleware
app.add_middleware(RequestIDMiddleware)  # Request Tracing
app.add_middleware(CORSMiddleware)       # CORS für Frontend

# 3. Startup Event
@app.on_event("startup")
async def startup():
    # Alert Evaluator als Background Task starten
    asyncio.create_task(alert_evaluator.start())

# 4. Shutdown Event
@app.on_event("shutdown")
async def shutdown():
    await close_pool()

# 5. Router einbinden
app.include_router(router)  # Alle API Routes
```

**Wichtig**: Lazy Database Loading - DB-Pool wird erst bei erstem API-Aufruf erstellt.

### streamlit_app.py - Admin UI

Tab-basierte Oberfläche mit Lazy Loading:
- Dashboard (Übersicht)
- Model Import
- Alert System
- Settings
- Info

## Module im Detail

### api/routes.py

**40+ Endpoints** in Kategorien:

#### Model Management
| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/models/available` | GET | Verfügbare Modelle vom Training Service |
| `/api/models/import` | POST | Modell importieren |
| `/api/models` | GET | Alle importierten Modelle |
| `/api/models/{id}` | GET | Modell-Details |
| `/api/models/active` | GET | Nur aktive Modelle |
| `/api/models/{id}/activate` | POST | Modell aktivieren |
| `/api/models/{id}/deactivate` | POST | Modell deaktivieren |
| `/api/models/{id}` | DELETE | Modell löschen |
| `/api/models/{id}/rename` | PATCH | Modell umbenennen |

#### Predictions
| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/predict` | POST | Manuelle Vorhersage |
| `/api/predictions` | GET | Vorhersage-Historie |
| `/api/predictions/latest/{coin_id}` | GET | Letzte Vorhersage für Coin |

#### Alerts
| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/models/{id}/alert-threshold` | PATCH | Alert-Schwellwert setzen |
| `/api/models/{id}/n8n-settings` | PATCH | n8n Webhook konfigurieren |
| `/api/models/{id}/alert-config` | PATCH | Alert-Konfiguration |
| `/api/alerts` | GET | Alert-Liste |
| `/api/alerts/statistics` | GET | Alert-Statistiken |

#### Monitoring
| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/health` | GET | Health Status |
| `/api/metrics` | GET | Prometheus Metrics |
| `/api/stats` | GET | Service-Statistiken |
| `/api/logs` | GET | Log-Tail |

### database/connection.py

**Connection Pool Management**:

```python
# Pool-Konfiguration
pool = await asyncpg.create_pool(
    dsn=DB_DSN,
    min_size=1,
    max_size=10,
    command_timeout=60
)

# SSL-Konfiguration
# - Localhost/Intern: SSL deaktiviert
# - Extern: SSL mit self-signed Cert Support

# Wichtige Funktionen
async def get_pool() -> asyncpg.Pool      # Pool abrufen/erstellen
async def close_pool() -> None            # Pool schließen
async def test_connection() -> bool       # Health Check
```

### database/models.py

**CRUD Operations für prediction_active_models**:

```python
# Modell-Management
async def get_available_models() -> List[Dict]
async def get_active_models() -> List[Dict]
async def import_model(model_id: int) -> Dict
async def activate_model(id: int) -> Dict
async def deactivate_model(id: int) -> Dict
async def delete_model(id: int) -> bool

# Predictions
async def save_prediction(coin_id, timestamp, predictions, n8n_data) -> int
async def get_predictions(limit, offset, coin_id, model_id) -> List[Dict]

# Konfiguration
async def update_alert_config(id: int, config: Dict) -> Dict
async def update_ignore_settings(id: int, settings: Dict) -> Dict
```

### prediction/engine.py

**Core Prediction Logic**:

```python
async def predict_coin(
    coin_id: str,
    timestamp: datetime,
    model_config: Dict[str, Any],
    pool: Optional[asyncpg.Pool] = None
) -> Dict[str, Any]:
    """
    Einzelne Vorhersage für ein Coin-Model-Paar.

    Returns:
        {"prediction": 0|1, "probability": float}
    """

async def predict_coin_all_models(
    coin_id: str,
    timestamp: datetime,
    active_models: List[Dict],
    pool: Optional[asyncpg.Pool] = None
) -> List[Dict]:
    """
    Parallele Vorhersagen für alle aktiven Modelle.

    - Verwendet asyncio.gather() für Parallelität
    - Ein fehlerhaftes Modell blockiert nicht die anderen
    - Gibt nur erfolgreiche Vorhersagen zurück
    """
```

### prediction/feature_processor.py

**Feature Engineering Pipeline**:

```python
async def prepare_features(
    coin_id: str,
    model_config: Dict[str, Any],
    pool: Optional[asyncpg.Pool] = None
) -> pd.DataFrame:
    """
    1. Dynamische Feature-Anzahl aus Modell-Metadata
    2. Historische Daten aus coin_metrics laden
    3. Optional: Phase Filtering
    4. Optional: Feature Engineering (Pump Detection)
    5. Target Variable Handling
    6. NaN → 0.0
    """
```

### prediction/event_handler.py

**Event-Driven Prediction Processing**:

```python
class EventHandler:
    """
    Zwei Modi:
    1. LISTEN/NOTIFY (bevorzugt): Echtzeit-Events von PostgreSQL
    2. Polling Fallback: Alle 30 Sekunden DB abfragen

    Batch-Processing:
    - Max 50 Events pro Batch
    - Timeout: 5 Sekunden
    - Parallele Vorhersagen für alle aktiven Modelle
    """

    async def setup_listener()    # LISTEN/NOTIFY Setup
    async def add_to_batch()      # Event zum Batch hinzufügen
    async def process_batch()     # Batch verarbeiten
```

### prediction/alert_evaluator.py

**Background Alert Service**:

```python
class AlertEvaluator:
    """
    Läuft alle 30 Sekunden:
    1. ATH-Tracking aktualisieren
    2. Pending Alerts auswerten (100 pro Batch)
    3. Statistiken aktualisieren

    Alert-Status:
    - pending → success (Vorhersage korrekt)
    - pending → failed (Vorhersage falsch)
    - pending → expired (Timeout)
    """
```

### prediction/n8n_client.py

**n8n Webhook Integration**:

```python
async def send_to_n8n(
    coin_id: str,
    timestamp: datetime,
    predictions: List[Dict],
    active_models: List[Dict]
) -> bool:
    """
    - Jedes Modell kann eigene n8n URL haben
    - Send Modes: ["all", "alerts_only", "positive_only", "negative_only"]
    - Timeout: 5 Sekunden
    - Fehler werden geloggt, blockieren aber nicht
    """
```

### utils/config.py

**Configuration Management**:

```python
# Environment Variables mit Defaults
DB_DSN = os.getenv("DB_DSN", "postgresql://...")
TRAINING_SERVICE_API_URL = os.getenv("TRAINING_SERVICE_API_URL", "...")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Persistent Configuration
# Speicherort: /app/config/ui_config.json
def load_persistent_config() -> Dict
def save_persistent_config(config: Dict) -> None
```

### utils/metrics.py

**Prometheus Metrics**:

```python
# Counters
ml_predictions_total           # Gesamtanzahl Vorhersagen
ml_alerts_triggered_total      # Ausgelöste Alerts
ml_errors_total                # Fehler nach Typ

# Gauges
ml_active_models               # Aktive Modelle
ml_models_loaded               # Geladene Modelle im Cache
ml_db_connected                # DB-Verbindungsstatus

# Histograms
ml_prediction_duration_seconds # Vorhersage-Latenz
ml_feature_processing_seconds  # Feature-Processing Zeit
ml_model_load_seconds          # Model-Ladezeit
```

### utils/exceptions.py

**Custom Exceptions**:

```python
class MLTrainingError(Exception)        # Basis-Exception
class ModelNotFoundError(MLTrainingError)
class InvalidModelParametersError(MLTrainingError)
class DatabaseError(MLTrainingError)
class TrainingError(MLTrainingError)
class DataError(MLTrainingError)
class ValidationError(MLTrainingError)
```

## Wichtige Design-Entscheidungen

### 1. Lazy Database Loading
- DB-Pool wird erst bei erstem API-Aufruf erstellt
- Ermöglicht graceful Startup auch wenn DB nicht erreichbar

### 2. Parallel Model Predictions
- `asyncio.gather()` für gleichzeitige Vorhersagen
- Ein langsames/fehlerhaftes Modell blockiert nicht

### 3. Batch Processing mit Timeout
- Events werden gesammelt (max 50 oder 5 Sekunden)
- Verhindert Überlastung bei vielen Events

### 4. Per-Model n8n Configuration
- Jedes Modell kann eigene Webhook-URL haben
- Flexible Alert-Routing möglich

### 5. Feature Flexibility
- Feature-Anzahl dynamisch aus Modell-Metadata
- Automatische Target Variable Handling

## Weiterführende Dokumentation

- [API Endpoints](../api/endpoints.md) - Vollständige API-Dokumentation
- [Prediction Engine](../algorithms/prediction-engine.md) - ML Pipeline Details
- [Event Handler](../algorithms/event-handler.md) - Event Processing
