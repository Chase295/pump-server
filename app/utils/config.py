"""
Zentrale Konfiguration für ML Prediction Service

Liest alle Environment Variables und stellt Default-Werte bereit.
Unterstützt persistente UI-Konfiguration über Shared Volume.
Wichtig für Docker-Deployment mit externer Datenbank.
"""
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Lade .env-Datei
load_dotenv()

# ============================================================
# Persistente Konfiguration (UI-änderbar)
# ============================================================
CONFIG_FILE = "/app/config/ui_config.json"

def load_persistent_config() -> Dict[str, Any]:
    """Lädt persistente Konfiguration aus Shared Volume"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der persistenten Konfiguration: {e}")

    # Default-Konfiguration (werden beim ersten Start verwendet)
    return {
        "database_url": "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta",
        "training_service_url": "https://pump-training.local.chase295.de/api",
        "n8n_webhook_url": "",
        "api_port": 8000,
        "streamlit_port": 8501
    }

def save_persistent_config(config: Dict[str, Any]) -> bool:
    """Speichert persistente Konfiguration in Shared Volume"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Fehler beim Speichern der persistenten Konfiguration: {e}")
        return False

def ensure_config_file_exists():
    """Erstellt Config-Datei mit Default-Werten, falls sie nicht existiert"""
    if not os.path.exists(CONFIG_FILE):
        # Erstelle Verzeichnis falls nicht vorhanden
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        # Default-Konfiguration (hardcoded, nicht aus load_persistent_config)
        default_config = {
            "database_url": "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta",
            "training_service_url": "https://pump-training.local.chase295.de/api",
            "n8n_webhook_url": "",
            "api_port": 8000,
            "streamlit_port": 8501
        }
        save_persistent_config(default_config)  # Speichert sie in die Datei
        print(f"✅ Config-Datei erstellt mit Default-Werten: {CONFIG_FILE}")

# Stelle sicher, dass Config-Datei existiert (mit Default-Werten)
# WICHTIG: Muss VOR load_persistent_config() aufgerufen werden!
ensure_config_file_exists()

# Lade persistente Konfiguration
_persistent_config = load_persistent_config()

# Exportiere Funktionen für API-Zugriff
__all__ = ['load_persistent_config', 'save_persistent_config', 'ensure_config_file_exists', '_persistent_config']

# ============================================================
# Datenbank (EXTERNE DB!)
# ============================================================
# Priorität: Persistente Config > Environment Variable > Default
# WICHTIG: Persistente Config hat Vorrang, damit UI-Änderungen wirksam werden
_persistent_db_url = _persistent_config.get("database_url")
if _persistent_db_url:
    DB_DSN = _persistent_db_url
else:
    # Fallback: Environment Variable oder Default
    DB_DSN = os.getenv("DB_DSN") or os.getenv("DATABASE_URL",
              "postgresql://user:password@db:5432/ml_predictions")

# ============================================================
# Ports
# ============================================================
API_PORT = int(os.getenv("API_PORT",
              str(_persistent_config.get("api_port", 8000))))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT",
                   str(_persistent_config.get("streamlit_port", 8501))))

# ============================================================
# Modell-Storage (lokal im Container)
# ============================================================
MODEL_STORAGE_PATH = os.getenv("MODEL_STORAGE_PATH", "/app/models")

# ============================================================
# Training Service API (für Modell-Download)
# ============================================================
# Priorität: Persistente Config > Environment Variable > Default
# WICHTIG: Persistente Config hat Vorrang, damit UI-Änderungen wirksam werden
_persistent_training_url = _persistent_config.get("training_service_url")
if _persistent_training_url:
    TRAINING_SERVICE_API_URL = _persistent_training_url
else:
    # Fallback: Environment Variable oder Default
    TRAINING_SERVICE_API_URL = os.getenv("TRAINING_SERVICE_API_URL",
                         "http://localhost:8001/api")

# ============================================================
# Event-Handling
# ============================================================
POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", "30"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
BATCH_TIMEOUT_SECONDS = int(os.getenv("BATCH_TIMEOUT_SECONDS", "5"))

# ============================================================
# Feature-Engineering
# ============================================================
FEATURE_HISTORY_SIZE = int(os.getenv("FEATURE_HISTORY_SIZE", "20"))

# ============================================================
# Performance
# ============================================================
MAX_CONCURRENT_PREDICTIONS = int(os.getenv("MAX_CONCURRENT_PREDICTIONS", "10"))
MODEL_CACHE_SIZE = int(os.getenv("MODEL_CACHE_SIZE", "10"))

# ============================================================
# n8n Integration
# ============================================================
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL") or \
                (_persistent_config.get("n8n_webhook_url") if _persistent_config.get("n8n_webhook_url") else None)  # Optional
N8N_WEBHOOK_TIMEOUT = int(os.getenv("N8N_WEBHOOK_TIMEOUT", "5"))  # Sekunden
DEFAULT_ALERT_THRESHOLD = float(os.getenv("DEFAULT_ALERT_THRESHOLD", "0.7"))  # 0.0 - 1.0

# ============================================================
# Logging
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # "text" oder "json"
LOG_JSON_INDENT = int(os.getenv("LOG_JSON_INDENT", "0"))  # 0 = kompakt, 2+ = formatiert

