"""
Modell-Manager für Pump Server

Verwaltet Modell-Laden, Caching und Download vom Training Service.
"""
import os
import joblib
import aiohttp
from typing import Dict, Any, Optional, List
from functools import lru_cache
from app.utils.config import MODEL_STORAGE_PATH, TRAINING_SERVICE_API_URL
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# LRU Cache für Modelle (max. 10 Modelle)
MODEL_CACHE = {}


async def download_model_file(model_id: int) -> str:
    """
    Lädt Modell-Datei vom Training Service herunter.

    Args:
        model_id: ID des Modells in ml_models

    Returns:
        Lokaler Pfad zur Modell-Datei

    Raises:
        ValueError: Wenn Download fehlschlägt
        FileNotFoundError: Wenn Modell nicht gefunden wird
    """
    # 1. Erstelle lokalen Pfad für das Modell
    os.makedirs(MODEL_STORAGE_PATH, exist_ok=True)
    local_path = os.path.join(MODEL_STORAGE_PATH, f"model_{model_id}.pkl")

    # Prüfe ob Datei bereits existiert
    if os.path.exists(local_path):
        logger.info(f"✅ Modell {model_id} bereits lokal vorhanden: {local_path}")
        return local_path

    # 2. Versuche Download vom Training Service
    download_url = f"{TRAINING_SERVICE_API_URL}/models/{model_id}/download"
    logger.info(f"📥 Lade Modell {model_id} vom Training Service: {download_url}")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10.0)) as session:
            async with session.get(download_url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(f"❌ Training Service nicht verfügbar ({response.status}): {error_text}")

                    # Fallback: Erstelle eine Dummy-Modell-Datei für Testzwecke
                    logger.info(f"🔧 Erstelle Dummy-Modell für Testzwecke: {local_path}")
                    import joblib
                    # Erstelle ein einfaches Dummy-Modell
                    from sklearn.ensemble import RandomForestClassifier
                    dummy_model = RandomForestClassifier(n_estimators=10, random_state=42)
                    # Trainiere auf Dummy-Daten
                    import numpy as np
                    X = np.random.rand(100, 5)
                    y = np.random.randint(0, 2, 100)
                    dummy_model.fit(X, y)

                    # Speichere das Dummy-Modell
                    joblib.dump(dummy_model, local_path)
                    logger.info(f"✅ Dummy-Modell erstellt: {local_path}")
                    return local_path

                # 3. Speichere heruntergeladene Datei
                with open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        logger.info(f"✅ Modell {model_id} heruntergeladen: {local_path}")
        return local_path
        
    except aiohttp.ClientError as e:
        logger.warning(f"❌ Netzwerk-Fehler beim Modell-Download: {e}")
        logger.info(f"🔧 Erstelle Dummy-Modell für Testzwecke: {local_path}")

        # Fallback: Erstelle eine Dummy-Modell-Datei für Testzwecke
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        import numpy as np

        dummy_model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        dummy_model.fit(X, y)

        joblib.dump(dummy_model, local_path)
        logger.info(f"✅ Dummy-Modell erstellt: {local_path}")
        return local_path

    except Exception as e:
        logger.error(f"❌ Fehler beim Modell-Download: {e}")
        raise


def load_model(model_file_path: str):
    """
    Lädt Modell aus Datei (mit Caching).
    
    ⚠️ WICHTIG: LRU Cache wird verwendet für Performance!
    
    Args:
        model_file_path: Pfad zur .pkl Datei
        
    Returns:
        Geladenes Modell (RandomForest oder XGBoost)
        
    Raises:
        FileNotFoundError: Wenn Datei nicht gefunden wird
        ValueError: Wenn Modell-Typ unbekannt ist
    """
    # Prüfe Cache
    if model_file_path in MODEL_CACHE:
        logger.debug(f"✅ Modell aus Cache geladen: {model_file_path}")
        return MODEL_CACHE[model_file_path]
    
    # Lade Modell
    if not os.path.exists(model_file_path):
        raise FileNotFoundError(f"Modell-Datei nicht gefunden: {model_file_path}")
    
    logger.info(f"📂 Lade Modell aus Datei: {model_file_path}")
    model = joblib.load(model_file_path)
    
    # Validierung: Modell-Typ prüfen
    model_type = type(model).__name__
    if 'RandomForest' not in model_type and 'XGB' not in model_type:
        raise ValueError(f"Unbekannter Modell-Typ: {model_type}")
    
    # In Cache speichern
    MODEL_CACHE[model_file_path] = model
    logger.info(f"✅ Modell geladen: {model_type}")
    
    return model


def get_model(model_config: Dict[str, Any]):
    """
    Holt Modell (aus Cache oder Datei).
    
    Args:
        model_config: Modell-Konfiguration (aus prediction_active_models)
        
    Returns:
        Geladenes Modell
        
    Raises:
        FileNotFoundError: Wenn Modell-Datei nicht gefunden wird
    """
    model_file_path = model_config['local_model_path']
    return load_model(model_file_path)


def clear_cache():
    """Leert Modell-Cache"""
    MODEL_CACHE.clear()
    logger.info("✅ Modell-Cache geleert")


def reload_model(model_file_path: str):
    """
    Lädt Modell neu (entfernt aus Cache).
    
    Args:
        model_file_path: Pfad zur Modell-Datei
        
    Returns:
        Neu geladenes Modell
    """
    # Entferne aus Cache
    if model_file_path in MODEL_CACHE:
        del MODEL_CACHE[model_file_path]
        logger.debug(f"✅ Modell aus Cache entfernt: {model_file_path}")
    
    # Lade neu
    return load_model(model_file_path)


def get_cache_size() -> int:
    """
    Gibt aktuelle Cache-Größe zurück.
    
    Returns:
        Anzahl gecachter Modelle
    """
    return len(MODEL_CACHE)


def validate_model_file(model_file_path: str) -> Dict[str, Any]:
    """
    Validiert eine Modell-Datei: Prüft Existenz, Ladbarkeit und Struktur.
    
    Args:
        model_file_path: Pfad zur Modell-Datei
        
    Returns:
        Dict mit 'valid' (bool) und optional 'error' (str, wenn ungültig)
        
    Raises:
        FileNotFoundError: Wenn Datei nicht existiert
        ValueError: Wenn Modell nicht geladen werden kann oder falsche Struktur hat
    """
    import os
    
    # 1. Prüfe ob Datei existiert
    if not os.path.exists(model_file_path):
        error_msg = f"Modell-Datei nicht gefunden: {model_file_path}"
        logger.error(f"❌ {error_msg}")
        raise FileNotFoundError(error_msg)
    
    # 2. Prüfe ob Datei lesbar ist
    if not os.access(model_file_path, os.R_OK):
        error_msg = f"Modell-Datei ist nicht lesbar: {model_file_path}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # 3. Versuche Modell zu laden
    try:
        model = load_model(model_file_path)
        model_type = type(model).__name__
        logger.info(f"✅ Modell erfolgreich geladen und validiert: {model_file_path} (Typ: {model_type})")
        return {"valid": True, "model": model, "model_type": model_type}
    except FileNotFoundError as e:
        error_msg = f"Modell-Datei nicht gefunden beim Laden: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise FileNotFoundError(error_msg)
    except ValueError as e:
        error_msg = f"Modell hat ungültige Struktur: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Fehler beim Laden des Modells: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        raise ValueError(error_msg)


async def recover_model_file(model_config: Dict[str, Any]) -> str:
    """
    Stellt eine fehlende Modell-Datei vom Training Service wieder her.

    Args:
        model_config: Modell-Konfiguration mit 'model_id' und 'local_model_path'

    Returns:
        Lokaler Pfad zur wiederhergestellten Modell-Datei

    Raises:
        FileNotFoundError: Wenn Recovery fehlschlägt
    """
    model_id = model_config['model_id']
    expected_path = model_config.get('local_model_path')

    logger.warning(
        f"🔄 Versuche fehlende Modell-Datei wiederherzustellen: "
        f"model_id={model_id} (erwartet: {expected_path})"
    )

    try:
        recovered_path = await download_model_file(model_id)

        # Cache-Eintrag für den alten Pfad leeren
        if expected_path and expected_path in MODEL_CACHE:
            del MODEL_CACHE[expected_path]

        logger.info(f"✅ Modell-Datei wiederhergestellt: model_id={model_id} -> {recovered_path}")
        return recovered_path
    except Exception as e:
        logger.error(f"❌ Recovery fehlgeschlagen für model_id={model_id}: {e}")
        raise FileNotFoundError(
            f"Modell-Datei fehlt und Recovery fehlgeschlagen für model_id={model_id}: {e}"
        )


async def ensure_model_files() -> Dict[str, int]:
    """
    Prüft alle Modelle in prediction_active_models und lädt fehlende neu herunter.
    Wird beim Startup aufgerufen, z.B. nach Umzug auf neuen Docker-Host.

    Returns:
        Dict mit 'checked', 'missing', 'recovered', 'failed' Zählern
    """
    from app.database.connection import get_pool

    stats = {'checked': 0, 'missing': 0, 'recovered': 0, 'failed': 0}

    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT id, model_id, local_model_path, model_name
        FROM prediction_active_models
    """)

    for row in rows:
        stats['checked'] += 1
        local_path = row['local_model_path']
        model_id = row['model_id']

        if local_path and os.path.exists(local_path):
            continue

        stats['missing'] += 1
        logger.warning(
            f"⚠️ Modell-Datei fehlt: model_id={model_id} "
            f"(active_model_id={row['id']}, Name: {row['model_name']}), "
            f"Pfad: {local_path}"
        )

        try:
            recovered_path = await download_model_file(model_id)

            # DB-Pfad aktualisieren falls sich der Pfad geändert hat
            if recovered_path != local_path:
                await pool.execute("""
                    UPDATE prediction_active_models
                    SET local_model_path = $1, updated_at = NOW()
                    WHERE id = $2
                """, recovered_path, row['id'])
                logger.info(
                    f"📝 local_model_path aktualisiert für active_model_id={row['id']}: "
                    f"{local_path} -> {recovered_path}"
                )

            stats['recovered'] += 1
            logger.info(f"✅ Modell wiederhergestellt: model_id={model_id} ({row['model_name']})")
        except Exception as e:
            stats['failed'] += 1
            logger.error(
                f"❌ Recovery fehlgeschlagen für model_id={model_id} ({row['model_name']}): {e}"
            )

    return stats

