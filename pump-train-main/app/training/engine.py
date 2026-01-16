"""
Training Engine für ML Training Service
Trainiert Random Forest und XGBoost Modelle
"""
import joblib
import pandas as pd
import numpy as np
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from app.training.feature_engineering import create_time_based_labels

logger = logging.getLogger(__name__)

# Default-Features (wird verwendet wenn keine Features übergeben werden)
DEFAULT_FEATURES = [
    # Basis OHLC
    "price_open", "price_high", "price_low", "price_close",
    
    # Volumen
    "volume_sol", "buy_volume_sol", "sell_volume_sol", "net_volume_sol",
    
    # Market Cap & Phase
    "market_cap_close", "phase_id_at_time",
    
    # ⚠️ KRITISCH für Rug-Detection
    "dev_sold_amount",  # Wichtigster Indikator!
    
    # Ratio-Metriken (Bot-Spam vs. echtes Interesse)
    "buy_pressure_ratio",
    "unique_signer_ratio",
    
    # Whale-Aktivität
    "whale_buy_volume_sol",
    "whale_sell_volume_sol",
    
    # Volatilität
    "volatility_pct",
    "avg_trade_size_sol",
    
    # 🆕 ATH-Tracking (Breakout-Erkennung)
    "ath_price_sol",
    "price_vs_ath_pct",      # Wie weit vom ATH entfernt?
    "minutes_since_ath"      # Wie lange ist es her?
]

# XGBoost optional (für lokales Testing ohne libomp)

# Inline-Funktion um Import-Fehler zu vermeiden
def get_engineered_feature_names(window_sizes=[5, 10, 15]):
    features = []
    # Dev-Tracking Features
    features.extend(['dev_sold_flag', 'dev_sold_cumsum'])
    for w in window_sizes:
        features.append(f'dev_sold_spike_{w}')
    # Ratio-Features
    for w in window_sizes:
        features.extend([f'buy_pressure_ma_{w}', f'buy_pressure_trend_{w}'])
    # Whale-Aktivität Features
    features.append('whale_net_volume')
    for w in window_sizes:
        features.append(f'whale_activity_{w}')
    # Volatilitäts-Features
    for w in window_sizes:
        features.extend([f'volatility_ma_{w}', f'volatility_spike_{w}'])
    # Wash-Trading Detection
    for w in window_sizes:
        features.append(f'wash_trading_flag_{w}')
    # Net-Volume Features
    for w in window_sizes:
        features.extend([f'net_volume_ma_{w}', f'volume_flip_{w}'])
    # Price Momentum
    for w in window_sizes:
        features.extend([f'price_change_{w}', f'price_roc_{w}'])
    # Market Cap Velocity
    for w in window_sizes:
        features.append(f'mcap_velocity_{w}')
    # ATH-basierte Features
    for w in window_sizes:
        features.extend([
            f'ath_distance_trend_{w}', f'ath_approach_{w}', f'ath_breakout_count_{w}',
            f'ath_breakout_volume_ma_{w}', f'ath_age_trend_{w}'
        ])
    return features
XGBOOST_AVAILABLE = False
XGBClassifier = None
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except Exception as e:
    # Fängt ImportError, XGBoostError, OSError, etc.
    XGBOOST_AVAILABLE = False
    logger.warning(f"⚠️ XGBoost nicht verfügbar: {type(e).__name__}. In Docker wird es funktionieren.")

from app.database.models import get_model_type_defaults
from app.training.feature_engineering import (
    load_training_data, 
    create_labels,
    validate_ath_data_availability
)

def create_model(model_type: str, params: Dict[str, Any]) -> Any:
    """
    Erstellt Modell-Instanz basierend auf Typ.
    
    ⚠️ WICHTIG: Nur Random Forest und XGBoost werden unterstützt!
    
    Args:
        model_type: Modell-Typ ("random_forest" oder "xgboost")
        params: Dictionary mit Hyperparametern. JSONB liefert bereits richtige Python-Typen.
                Unterstützte Parameter:
                - Random Forest: n_estimators, max_depth, min_samples_split, random_state
                - XGBoost: n_estimators, max_depth, learning_rate, random_state
    
    Returns:
        Modell-Instanz (RandomForestClassifier oder XGBClassifier)
        
    Raises:
        ValueError: Wenn model_type nicht unterstützt wird oder XGBoost nicht verfügbar ist
        
    Example:
        ```python
        params = {"n_estimators": 100, "max_depth": 10}
        model = create_model("random_forest", params)
        ```
    """
    # JSONB liefert bereits richtige Python-Typen (int, float, etc.)
    # Keine String-Konvertierung nötig!
    
    # ⚠️ WICHTIG: Entferne interne Parameter die nicht für Modell-Erstellung verwendet werden
    excluded_params = ['n_estimators', 'max_depth', 'min_samples_split', 'random_state', 
                       '_time_based', 'use_engineered_features', 'feature_engineering_windows',
                       'use_smote', 'use_timeseries_split', 'cv_splits',
                       'use_market_context', 'exclude_features', 'use_flag_features']  # Phase 2: Neue Parameter + Flag-Features
    # ⚠️ WICHTIG: use_flag_features wird für Modell-Speicherung benötigt, aber NICHT an RandomForestClassifier/XGBClassifier übergeben!
    
    if model_type == "random_forest":
        # ⚠️ WICHTIG: Verwende die gleiche excluded_params Liste für Random Forest
        return RandomForestClassifier(
            n_estimators=params.get('n_estimators', 100),
            max_depth=params.get('max_depth', 10),
            min_samples_split=params.get('min_samples_split', 2),
            random_state=params.get('random_state', 42),
            **{k: v for k, v in params.items() 
               if k not in excluded_params}
        )
    
    elif model_type == "xgboost":
        if not XGBOOST_AVAILABLE:
            raise ValueError("XGBoost ist nicht verfügbar. In Docker wird es funktionieren.")
        # ⚠️ WICHTIG: Entferne interne Parameter die nicht für Modell-Erstellung verwendet werden
        excluded_params = ['n_estimators', 'max_depth', 'learning_rate', 'random_state',
                           '_time_based', 'use_engineered_features', 'feature_engineering_windows',
                           'use_smote', 'use_timeseries_split', 'cv_splits',
                           'use_market_context', 'exclude_features', 'use_flag_features']  # Phase 2: Neue Parameter + Flag-Features
        return XGBClassifier(
            n_estimators=params.get('n_estimators', 100),
            max_depth=params.get('max_depth', 6),
            learning_rate=params.get('learning_rate', 0.1),
            random_state=params.get('random_state', 42),
            eval_metric='logloss',  # Für binäre Klassifikation
            **{k: v for k, v in params.items() 
               if k not in excluded_params}
        )
    
    else:
        raise ValueError(f"Unbekannter Modell-Typ: {model_type}. Nur 'random_forest' und 'xgboost' sind unterstützt!")

def prepare_features_for_training(
    features: List[str],
    target_var: Optional[str],
    use_time_based: bool
) -> tuple[List[str], List[str]]:
    """
    Bereitet Features für Training vor.
    
    ⚠️ KRITISCH: Bei zeitbasierter Vorhersage wird target_var NUR für Labels verwendet,
    NICHT für Training! Dies verhindert Data Leakage.
    
    Args:
        features: Liste der ursprünglichen Features
        target_var: Ziel-Variable (z.B. "price_close")
        use_time_based: True wenn zeitbasierte Vorhersage aktiviert
    
    Returns:
        Tuple von (features_for_loading, features_for_training)
        - features_for_loading: Enthält target_var (für Daten-Laden und Labels)
        - features_for_training: Enthält target_var NICHT bei zeitbasierter Vorhersage
    """
    # Für Daten-Laden: target_var wird benötigt (für Labels)
    features_for_loading = list(features)  # Kopie erstellen
    if target_var and target_var not in features_for_loading:
        features_for_loading.append(target_var)
        logger.info(f"➕ target_var '{target_var}' zu Features für Daten-Laden hinzugefügt")
    
    # Für Training: target_var wird ENTFERNT bei zeitbasierter Vorhersage
    features_for_training = list(features)  # Kopie erstellen
    if use_time_based and target_var and target_var in features_for_training:
        features_for_training.remove(target_var)
        logger.warning(f"⚠️ target_var '{target_var}' aus Features entfernt (zeitbasierte Vorhersage - verhindert Data Leakage)")
    
    return features_for_loading, features_for_training

def train_model_sync(
    data: pd.DataFrame,
    model_type: str,
    features: List[str],
    target_var: Optional[str],  # Optional wenn zeitbasierte Vorhersage aktiviert
    target_operator: Optional[str],  # Optional wenn zeitbasierte Vorhersage aktiviert
    target_value: Optional[float],  # Optional wenn zeitbasierte Vorhersage aktiviert
    params: dict,
    model_storage_path: str = "/app/models",
    # NEU: Zeitbasierte Parameter
    use_time_based: bool = False,
    future_minutes: Optional[int] = None,
    min_percent_change: Optional[float] = None,
    direction: str = "up",
    phase_intervals: Optional[Dict[int, int]] = None,  # {phase_id: interval_seconds}
    # ⚠️ FIX: Ursprünglich angeforderten Features (vor Erweiterung)
    original_requested_features: Optional[List[str]] = None  # NEU: Ursprünglich angeforderten Features
) -> Dict[str, Any]:
    """
    Trainiert ein ML-Modell (SYNCHRON - wird in run_in_executor aufgerufen!)
    
    ⚠️ WICHTIG: Diese Funktion ist SYNCHRON, weil model.fit() CPU-bound ist.
    Sie wird vom Job Manager in run_in_executor aufgerufen, damit der Event Loop nicht blockiert.
    
    Args:
        data: Bereits geladene Trainingsdaten (DataFrame)
        model_type: "random_forest" oder "xgboost" (nur diese beiden!)
        features: Liste der Feature-Namen (z.B. ["price_open", "price_high"])
        target_var: Ziel-Variable (z.B. "market_cap_close")
        target_operator: Vergleichsoperator (">", "<", ">=", "<=", "=")
        target_value: Schwellwert
        params: Dict mit Hyperparametern (bereits gemergt mit Defaults)
        model_storage_path: Pfad zum Models-Verzeichnis
    
    Returns:
        Dict mit Metriken, Modell-Pfad, Feature Importance
    """
    logger.info(f"🚀 Starte Training: {model_type} mit {len(data)} Zeilen")
    
    # ⚠️ WICHTIG: Speichere die ursprüngliche features-Liste VOR dem Feature-Engineering
    # (wird benötigt, um selected_engineered korrekt zu berechnen)
    # ⚠️ FIX: Verwende original_requested_features, falls verfügbar (enthält wirklich nur die ursprünglich angeforderten Features)
    # Falls nicht verfügbar, verwende features.copy() (könnte bereits erweitert sein)
    # Debug: Schreibe auch in Datei
    try:
        with open('/tmp/train_model_sync_debug.log', 'w') as f:
            f.write(f"TRAIN_MODEL_SYNC: original_requested_features empfangen\n")
            f.write(f"  original_requested_features={original_requested_features}\n")
            f.write(f"  type={type(original_requested_features)}\n")
            f.write(f"  len={len(original_requested_features) if original_requested_features else 0}\n")
            if original_requested_features:
                f.write(f"  content={original_requested_features[:10]}\n")
            f.write(f"  features len={len(features)}\n")
            f.write(f"  features content={features[:10]}\n")
    except:
        pass
    
    logger.info(f"🔍 DEBUG TRAIN_MODEL_SYNC: original_requested_features={original_requested_features}")
    logger.info(f"🔍 DEBUG TRAIN_MODEL_SYNC: original_requested_features type={type(original_requested_features)}")
    logger.info(f"🔍 DEBUG TRAIN_MODEL_SYNC: original_requested_features len={len(original_requested_features) if original_requested_features else 0}")
    if original_requested_features:
        logger.info(f"🔍 DEBUG TRAIN_MODEL_SYNC: original_requested_features content={original_requested_features[:10]}")
    logger.info(f"🔍 DEBUG TRAIN_MODEL_SYNC: features len={len(features)}")
    logger.info(f"🔍 DEBUG TRAIN_MODEL_SYNC: features content={features[:10]}")
    original_features_before_engineering = original_requested_features.copy() if original_requested_features else features.copy()
    
    # Debug: Schreibe auch in Datei
    try:
        with open('/tmp/train_model_sync_debug.log', 'a') as f:
            f.write(f"  original_features_before_engineering len={len(original_features_before_engineering)}\n")
            f.write(f"  original_features_before_engineering content={original_features_before_engineering[:10]}\n")
    except:
        pass
    
    logger.info(f"🔍 DEBUG: original_features_before_engineering gespeichert: {len(original_features_before_engineering)} Features: {original_features_before_engineering[:10]}...")
    
    # 1. Erstelle Labels
    if use_time_based:
        # Bei zeitbasierter Vorhersage muss target_var gesetzt sein (für welche Variable wird die Änderung berechnet)
        if not target_var:
            raise ValueError("target_var muss gesetzt sein für zeitbasierte Vorhersage (z.B. 'price_close')")
        logger.info(f"⏰ Zeitbasierte Vorhersage: {future_minutes} Minuten, {min_percent_change}%, Richtung: {direction}")
        
        # ⚠️ WICHTIG: create_time_based_labels gibt (labels, data) zurück wenn NaN entfernt wurden
        result = create_time_based_labels(
            data, 
            target_var, 
            future_minutes, 
            min_percent_change, 
            direction,
            phase_intervals  # NEU: Phase-Intervalle übergeben
        )
        
        # Prüfe ob Tuple zurückgegeben wurde (labels, data) oder nur labels
        if isinstance(result, tuple):
            labels, data = result  # Daten wurden gefiltert (NaN entfernt)
        else:
            labels = result  # Keine Filterung nötig
    else:
        # Normale Labels (aktuelles System)
        if not target_var or not target_operator or target_value is None:
            raise ValueError("target_var, target_operator und target_value müssen gesetzt sein wenn zeitbasierte Vorhersage nicht aktiviert ist")
        labels = create_labels(data, target_var, target_operator, target_value)
    
    positive_count = labels.sum()
    negative_count = len(labels) - positive_count
    
    # 🆕 NEU: Automatische Anpassung bei unausgewogenen Labels
    if positive_count == 0 or negative_count == 0:
        if use_time_based:
            # Bei zeitbasierter Vorhersage: Bedingungen automatisch anpassen
            logger.warning(f"⚠️ Zeitbasierte Labels extrem unausgewogen: {positive_count} positive, {negative_count} negative")

            # Versuche Bedingungen automatisch anzupassen
            if positive_count == 0:
                # Zu strenge Bedingung - reduziere min_percent_change
                original_change = params.get('min_percent_change', 5.0)
                new_change = max(0.1, original_change * 0.5)  # Halbieren, mindestens 0.1%
                logger.info(f"🔧 Passe min_percent_change automatisch an: {original_change}% -> {new_change}%")

                # Erstelle Labels neu mit angepasster Bedingung
                result = create_time_based_labels(
                    data,
                    target_var,
                    future_minutes,
                    new_change,  # Angepasste Bedingung
                    direction,
                    phase_intervals
                )

                # Prüfe ob Tuple zurückgegeben wurde (labels, data) oder nur labels
                if isinstance(result, tuple):
                    labels, data = result
                else:
                    labels = result

                positive_count = labels.sum()
                negative_count = len(labels) - positive_count
                logger.info(f"✅ Nach automatischer Anpassung: {positive_count} positive, {negative_count} negative")

            elif negative_count == 0:
                # Zu schwache Bedingung - erhöhe min_percent_change
                original_change = params.get('min_percent_change', 5.0)
                new_change = min(50.0, original_change * 2.0)  # Verdoppeln, maximal 50%
                logger.info(f"🔧 Passe min_percent_change automatisch an: {original_change}% -> {new_change}%")

                # Erstelle Labels neu mit angepasster Bedingung
                result = create_time_based_labels(
                    data,
                    target_var,
                    future_minutes,
                    new_change,  # Angepasste Bedingung
                    direction,
                    phase_intervals
                )

                # Prüfe ob Tuple zurückgegeben wurde (labels, data) oder nur labels
                if isinstance(result, tuple):
                    labels, data = result
                else:
                    labels = result

                positive_count = labels.sum()
                negative_count = len(labels) - positive_count
                logger.info(f"✅ Nach automatischer Anpassung: {positive_count} positive, {negative_count} negative")

        else:
            # Bei regelbasierter Vorhersage: Detaillierte Fehlermeldung
            if positive_count == 0:
                raise ValueError(
                    f"Labels sind nicht ausgewogen: {positive_count} positive, {negative_count} negative. "
                    f"Keine positiven Labels gefunden - die Bedingung '{target_var} {target_operator} {target_value}' "
                    f"wird nie erfüllt!\n"
                    f"Empfehlung: Verwende eine schwächere Bedingung (z.B. '{target_var} > {target_value * 0.1}') oder "
                    f"schalte auf zeitbasierte Vorhersage um."
                )
            elif negative_count == 0:
                raise ValueError(
                    f"Labels sind nicht ausgewogen: {positive_count} positive, {negative_count} negative. "
                    f"Keine negativen Labels gefunden - die Bedingung '{target_var} {target_operator} {target_value}' "
                    f"wird immer erfüllt!\n"
                    f"Empfehlung: Verwende eine strengere Bedingung (z.B. '{target_var} > {target_value * 10}') oder "
                    f"schalte auf zeitbasierte Vorhersage um."
                )
    
    # Warnung wenn immer noch sehr unausgewogen (aber nicht 0)
    balance_ratio = min(positive_count, negative_count) / max(positive_count, negative_count)
    if balance_ratio < 0.1:
        logger.warning(f"⚠️ Labels unausgewogen: {positive_count} positive, {negative_count} negative (Ratio: {balance_ratio:.2f}) - SMOTE wird angewendet")
        # Keine Exception mehr - SMOTE soll das Problem lösen
    
    # 1.4. ATH-Features zur Features-Liste hinzufügen (nach Daten-Laden)
    # ⚠️ TEMPORÄR AUSKOMMENTIERT: ATH-Features wegen Scoping-Problemen
    # include_ath = params.get('include_ath', True)
    # logger.info(f"🔍 ATH-Debug: include_ath={include_ath}, rolling_ath in data.columns={('rolling_ath' in data.columns)}")

    # TEMPORÄR: ATH-Features komplett deaktiviert wegen Scoping-Problems
    ath_features = []  # Leere Liste - keine ATH-Features
    # else:
    #     logger.info("ℹ️ ATH-Features deaktiviert (Standard)")

    # Importiere Feature-Engineering Funktionen am Anfang der Funktion (um Scoping-Fehler zu vermeiden)
    from app.training.feature_engineering import create_pump_detection_features
    from app.training.feature_engineering import validate_critical_features
    from app.training.feature_engineering import validate_ath_data_availability
    from app.training.feature_engineering import enrich_with_market_context
    from app.training.feature_engineering import get_engineered_feature_names

    # 1.5. Feature-Engineering: Erstelle zusätzliche Features im DataFrame (wenn aktiviert)
    # ⚠️ WICHTIG: Muss nach Label-Erstellung, aber vor Feature-Vorbereitung erfolgen!
    use_engineered_features = params.get('use_engineered_features', False)  # Default: False für Rückwärtskompatibilität
    # NEU: Flag-Features aktivieren/deaktivieren
    use_flag_features = params.get('use_flag_features', True)  # Default: True (empfohlen)
    if use_flag_features:
        logger.info("🚩 Flag-Features aktiviert (werden mit Engineering Features erstellt)")
    # get_engineered_feature_names ist jetzt als globale Funktion definiert

    # Definiere window_sizes außerhalb des if-Blocks (wird später benötigt)
    window_sizes = params.get('feature_engineering_windows', [5, 10, 15])  # Konfigurierbar

    # Initialisiere Variablen für späteren Gebrauch
    original_columns = set(data.columns)
    new_columns = set()
    engineered_features_created = []
    flag_features_created = []  # NEU: Liste für Flag-Features
    features_were_filtered_flag = False  # ⚠️ WICHTIG: Markiert ob features gefiltert wurde
    filtered_features_to_use = None  # ⚠️ WICHTIG: Speichert gefilterte Features-Liste für finalen Filter

    if use_engineered_features:
        logger.info("🔧 Erstelle Pump-Detection Features im DataFrame...")
        
        # Ursprüngliche Spalten wurden bereits oben gespeichert
        
        # ⚠️ WICHTIG: Prüfe welche Engineering-Features in der features-Liste stehen
        # Wenn spezifische Engineering-Features ausgewählt wurden, erstelle nur diese!
        # ⚠️ KRITISCH: Speichere selected_engineered VOR dem Feature-Engineering,
        # damit nur die ursprünglich ausgewählten Features erkannt werden!
        from app.training.feature_engineering import get_engineered_feature_names
        all_possible_engineered = get_engineered_feature_names(window_sizes)
        selected_engineered_original = [f for f in original_features_before_engineering if f in all_possible_engineered]  # Speichere ursprüngliche Auswahl
        logger.info(f"🔍 DEBUG: original_features_before_engineering={len(original_features_before_engineering)} Features: {original_features_before_engineering[:10]}...")
        logger.info(f"🔍 DEBUG: selected_engineered_original={len(selected_engineered_original)} Features: {selected_engineered_original[:10]}...")
        selected_engineered = selected_engineered_original.copy()  # Für späteren Gebrauch
        
        if selected_engineered:
            # Spezifische Engineering-Features wurden ausgewählt - erstelle nur diese!
            logger.info(f"🎯 {len(selected_engineered)} spezifische Engineering-Features ausgewählt - erstelle nur diese")
            logger.info(f"🎯 Ausgewählte Engineering-Features: {selected_engineered[:10]}... (erste 10)")
            
            # ⚠️ WICHTIG: Speichere die ursprüngliche selected_engineered-Liste für Flag-Features
            # (Flag-Features müssen für ALLE ausgewählten Engineering-Features erstellt werden, auch wenn sie bereits in features sind)
            original_selected_engineered = selected_engineered.copy()
            
            # Erstelle nur die ausgewählten Engineering-Features
            # Dafür müssen wir create_pump_detection_features anpassen oder manuell erstellen
            # Für jetzt: Erstelle alle, aber filtere später
            data = create_pump_detection_features(data, window_sizes=window_sizes, include_flags=use_flag_features)
            
            # Finde erstellte Features
            new_columns = set(data.columns) - original_columns
            all_new_features = list(new_columns)
            
            # Filtere: Nur die ausgewählten Engineering-Features verwenden, die NOCH NICHT in features sind
            # ⚠️ KRITISCH: Entferne Duplikate - nur Features hinzufügen, die noch nicht in der Liste sind
            engineered_features_created = [f for f in all_new_features 
                                           if f in original_selected_engineered 
                                           and not f.endswith('_has_data')
                                           and f not in features]  # ⚠️ WICHTIG: Nicht hinzufügen, wenn bereits vorhanden
            
            # Flag-Features: Nur für die ausgewählten Engineering-Features (verwende selected_engineered_original)
            flag_features_created = []
            if use_flag_features:
                for eng_feature in selected_engineered_original:  # Verwende selected_engineered_original für Flag-Features
                    flag_name = f'{eng_feature}_has_data'
                    if flag_name in all_new_features and flag_name not in features:  # ⚠️ WICHTIG: Nicht hinzufügen, wenn bereits vorhanden
                        flag_features_created.append(flag_name)
                logger.info(f"🚩 {len(flag_features_created)} Flag-Features für ausgewählte Engineering-Features erstellt")
        else:
            # Keine spezifischen Engineering-Features ausgewählt - erstelle ALLE
            logger.info("🔧 Keine spezifischen Engineering-Features ausgewählt - erstelle ALLE 66 Engineering-Features")
            data = create_pump_detection_features(data, window_sizes=window_sizes, include_flags=use_flag_features)
            
            # Finde tatsächlich erstellte Features (nur die, die im DataFrame vorhanden sind)
            new_columns = set(data.columns) - original_columns
            all_new_features = list(new_columns)
            
            # Trenne Engineering-Features und Flag-Features
            engineered_features_created = [f for f in all_new_features if not f.endswith('_has_data')]
            flag_features_created = [f for f in all_new_features if f.endswith('_has_data')]
        
        # ⚠️ KRITISCHER FIX: Wenn Flag-Features bereits in data.columns sind (z.B. von load_training_data),
        # aber nicht in all_new_features (weil sie schon vorher erstellt wurden), extrahiere sie direkt!
        if use_flag_features and len(flag_features_created) == 0:
            # Prüfe ob Flag-Features bereits in data.columns sind
            all_flag_features_in_data = [f for f in data.columns if f.endswith('_has_data')]
            if all_flag_features_in_data:
                # Filtere nur die, die zu den ausgewählten Engineering-Features gehören
                if selected_engineered:
                    flag_features_created = [f for f in all_flag_features_in_data 
                                            if f.replace('_has_data', '') in selected_engineered]
                else:
                    flag_features_created = [f for f in all_flag_features_in_data if f not in features]
                logger.info(f"🔍 Flag-Features bereits in Daten gefunden: {len(all_flag_features_in_data)} total, {len(flag_features_created)} passend")
        
        # Erweitere features-Liste um tatsächlich erstellte Engineering-Features
        # ⚠️ WICHTIG: Vermeide Duplikate - nur Features hinzufügen, die noch nicht in der Liste sind
        new_engineered = [f for f in engineered_features_created if f not in features]
        if new_engineered:
            features.extend(new_engineered)
            logger.info(f"✅ {len(new_engineered)} neue Engineering-Features hinzugefügt ({len(engineered_features_created) - len(new_engineered)} waren bereits vorhanden)")
        else:
            logger.info(f"ℹ️ Alle {len(engineered_features_created)} Engineering-Features waren bereits in der Features-Liste")
        
        # NEU: Füge Flag-Features hinzu, wenn aktiviert
        if use_flag_features and flag_features_created:
            # ⚠️ WICHTIG: Vermeide Duplikate - nur Flag-Features hinzufügen, die noch nicht in der Liste sind
            new_flags = [f for f in flag_features_created if f not in features]
            if new_flags:
                features.extend(new_flags)
                logger.info(f"🚩 {len(new_flags)} neue Flag-Features hinzugefügt ({len(flag_features_created) - len(new_flags)} waren bereits vorhanden)")
            else:
                logger.info(f"ℹ️ Alle {len(flag_features_created)} Flag-Features waren bereits in der Features-Liste")
        elif use_flag_features and not flag_features_created:
            logger.warning(f"⚠️ use_flag_features=True, aber keine Flag-Features erstellt! (Möglicherweise wurden sie nicht generiert)")

        # ⚠️ KRITISCH: Entferne Duplikate aus features-Liste BEVOR wir sie weiter verwenden
        features = list(dict.fromkeys(features))  # dict.fromkeys behält Reihenfolge und entfernt Duplikate
        logger.info(f"✅ {len(engineered_features_created)} Engineering-Features erstellt")
        logger.info(f"📊 Gesamt-Features: {len(features)} (inkl. {len(flag_features_created)} Flag-Features, Duplikate entfernt)")
        logger.info(f"📊 Features-Liste nach Engineering: {features[:10]}... (erste 10 von {len(features)})")

        # 🛠️ FIX: Stelle sicher, dass alle erwarteten engineered Features erstellt werden
        # Wenn nicht alle Features erstellt wurden, erstelle fehlende mit 0-Werten
        expected_engineered = get_engineered_feature_names(window_sizes)
        missing_engineered = [f for f in expected_engineered if f not in engineered_features_created]

        if missing_engineered:
            logger.warning(f"⚠️ {len(missing_engineered)} engineered Features fehlen - erstelle mit Fallback-Werten")
            for feature in missing_engineered:
                data[feature] = 0.0  # Fallback-Wert
            # Füge auch die fehlenden Features zur Liste hinzu
            features.extend(missing_engineered)
            logger.info(f"✅ Fallback-Features hinzugefügt: {len(missing_engineered)} Features")

        # 🐛 DEBUG: Detaillierte Analyse des Feature-Engineering-Bugs
        logger.info(f"🐛 DEBUG - Feature Engineering Analyse:")
        logger.info(f"🐛 DEBUG - Ursprüngliche Spalten: {len(original_columns)}")
        logger.info(f"🐛 DEBUG - Neue Spalten erstellt: {len(new_columns)} - {sorted(list(new_columns))}")

        # Erwartete Features von get_engineered_feature_names()
        # expected_engineered = get_engineered_feature_names(window_sizes)  # Deaktiviert wegen Import-Fehlern
        logger.info(f"🐛 DEBUG - Erwartete engineered Features: {len(expected_engineered)} - {sorted(expected_engineered)}")

        # Welche erwarteten Features wurden NICHT erstellt?
        missing_engineered = [f for f in expected_engineered if f not in new_columns]
        if missing_engineered:
            logger.error(f"🐛 BUG - FEHLENDE ENGINEERED FEATURES: {len(missing_engineered)} - {sorted(missing_engineered)}")

        # Welche Basis-Spalten fehlen? (Grund für nicht-erstellte Features)
        required_bases = ['dev_sold_amount', 'buy_pressure_ratio', 'unique_signer_ratio',
                         'whale_buy_volume_sol', 'whale_sell_volume_sol', 'volatility_pct',
                         'net_volume_sol', 'price_close', 'volume_sol', 'market_cap_close',
                         'ath_distance_pct', 'ath_breakout', 'minutes_since_ath']
        missing_bases = [col for col in required_bases if col not in data.columns]
        if missing_bases:
            logger.warning(f"🐛 WARN - FEHLENDE BASIS-SPALTE: {missing_bases} (Grund für fehlende engineered Features)")
    else:
        logger.info("ℹ️ Feature-Engineering deaktiviert (Standard-Modus)")
    
    # ✅ NEUE Validierung: Prüfe kritische Features (aber nicht blockierend)
    missing_critical = validate_critical_features(features)
    
    # Warnungen nur loggen, aber nicht blockieren
    if not missing_critical.get('dev_sold_amount'):
        logger.warning(
            "⚠️ KRITISCH: 'dev_sold_amount' fehlt in Features! "
            "Dies ist der wichtigste Rug-Pull-Indikator!"
        )
    
    if not missing_critical.get('buy_pressure_ratio'):
        logger.warning(
            "⚠️ WICHTIG: 'buy_pressure_ratio' fehlt - "
            "Bot-Spam vs. echtes Interesse kann nicht erkannt werden"
        )
    
    if not missing_critical.get('unique_signer_ratio'):
        logger.warning(
            "⚠️ WICHTIG: 'unique_signer_ratio' fehlt - "
            "Wash-Trading kann nicht erkannt werden"
        )
    
    # NEU: NaN-Handling für Flag-Features basierend auf Modell-Typ
    if use_flag_features and flag_features_created and model_type == "random_forest":
        from app.training.feature_engineering import get_flag_feature_names
        for flag_f in flag_features_created:
            if flag_f in data.columns:
                original_feature = flag_f.replace('_has_data', '')
                if original_feature in data.columns:
                    # Fülle NaN im Original-Feature mit 0, wenn das Flag 0 ist (keine Daten)
                    data.loc[data[flag_f] == 0, original_feature] = data.loc[data[flag_f] == 0, original_feature].fillna(0)
                    logger.debug(f"🔧 NaN in '{original_feature}' mit 0 gefüllt, wo '{flag_f}' 0 ist (Random Forest)")
    elif use_flag_features and flag_features_created and model_type == "xgboost":
        logger.info("ℹ️ XGBoost behandelt NaN-Werte intern, keine spezielle NaN-Füllung für Flag-Features nötig.")
    
    # 2. Prepare Features (X) und Labels (y)
    # ⚠️ WICHTIG: features enthält jetzt auch engineered und ATH features
    # ⚠️ KRITISCHER FIX: Wenn use_flag_features=True, füge ALLE Flag-Features aus data.columns hinzu!
    # use_flag_features ist bereits oben definiert (Zeile 381)
    use_flag_features_value = params.get('use_flag_features', True)  # Hole nochmal aus params für Sicherheit
    logger.info(f"🔍 DEBUG: use_flag_features={use_flag_features_value}, features vor Flag-Check: {len(features)}")
    
    # ⚠️ WICHTIG: Prüfe ZUERST ob spezifische Engineering-Features ausgewählt wurden
    # (bevor wir Flag-Features hinzufügen)
    selected_engineered = []
    if use_engineered_features:
        from app.training.feature_engineering import get_engineered_feature_names
        all_possible_engineered = get_engineered_feature_names(window_sizes)
        # ⚠️ FIX: selected_engineered muss aus original_features_before_engineering berechnet werden,
        # nicht aus features (das enthält bereits alle Engineering-Features, die in Zeile 399-600 erstellt wurden)!
        selected_engineered = [f for f in original_features_before_engineering if f in all_possible_engineered]
        logger.info(f"🔍 DEBUG STEP3: original_features_before_engineering={len(original_features_before_engineering)} Features: {original_features_before_engineering[:10]}...")
        logger.info(f"🔍 DEBUG STEP3: selected_engineered={len(selected_engineered)} Features: {selected_engineered[:10]}...")
    
    if use_flag_features_value:
        # ⚠️ WICHTIG: Wenn spezifische Engineering-Features ausgewählt wurden, 
        # füge nur die Flag-Features für diese hinzu!
        # ⚠️ FIX: Verwende selected_engineered_original (aus Zeile 411), nicht selected_engineered (aus Zeile 591)!
        # selected_engineered_original wurde bereits korrekt aus original_features_before_engineering berechnet
        # ABER: selected_engineered_original ist nur verfügbar, wenn use_engineered_features=True war
        # Wenn nicht, dann verwende selected_engineered (wurde gerade berechnet)
        selected_eng_for_flags = selected_engineered_original if selected_engineered_original else selected_engineered
        logger.info(f"🔍 DEBUG: selected_engineered_original={len(selected_engineered_original) if selected_engineered_original else 0}, selected_engineered={len(selected_engineered)}, verwende: {len(selected_eng_for_flags)}")
        
        if selected_eng_for_flags and len(selected_eng_for_flags) < 50:  # Nur wenn weniger als 50 (d.h. spezifische Auswahl)
            # Nur Flag-Features für ausgewählte Engineering-Features
            flag_features_to_add = []
            for eng_feature in selected_eng_for_flags:
                flag_name = f'{eng_feature}_has_data'
                if flag_name in data.columns and flag_name not in features:
                    flag_features_to_add.append(flag_name)
            if flag_features_to_add:
                features.extend(flag_features_to_add)
                logger.info(f"🚩 {len(flag_features_to_add)} Flag-Features für ausgewählte Engineering-Features hinzugefügt")
        else:
            # Keine spezifischen Engineering-Features ausgewählt - füge ALLE Flag-Features hinzu
            all_flag_features_in_data = [f for f in data.columns if f.endswith('_has_data') and f not in features]
            if all_flag_features_in_data:
                features.extend(all_flag_features_in_data)
                logger.info(f"🚩 {len(all_flag_features_in_data)} zusätzliche Flag-Features aus data.columns hinzugefügt")
                logger.info(f"🚩 Flag-Features: {all_flag_features_in_data[:5]}... (erste 5 von {len(all_flag_features_in_data)})")
            else:
                # Prüfe ob Flag-Features überhaupt in data.columns sind
                all_flags_in_data = [f for f in data.columns if f.endswith('_has_data')]
                logger.warning(f"⚠️ use_flag_features=True, aber keine neuen Flag-Features gefunden! (Total in data: {len(all_flags_in_data)})")
                if all_flags_in_data:
                    logger.warning(f"⚠️ Flag-Features in data.columns: {all_flags_in_data[:10]}...")
                    logger.warning(f"⚠️ Features-Liste aktuell: {len(features)} Features")
    
    # ⚠️ WICHTIG: Filtere nur die Features, die auch in der ursprünglichen features-Liste standen
    # (außer wenn use_engineered_features=true und keine spezifischen Engineering-Features ausgewählt wurden)
    # ⚠️ WICHTIG: selected_engineered_original muss außerhalb des if-Blocks verfügbar sein für späteren Gebrauch
    # ⚠️ KRITISCH: selected_engineered_original wurde bereits oben berechnet (Zeile 410)!
    # Verwende selected_engineered_original, nicht selected_engineered (das wird später überschrieben)
    if use_engineered_features:
        # Prüfe ob spezifische Engineering-Features ausgewählt wurden
        # ⚠️ WICHTIG: selected_engineered_original wurde bereits oben berechnet (Zeile 410)
        # Verwende es direkt, ohne es neu zu berechnen!
        if selected_engineered_original:
            # ⚠️ KRITISCH: Entferne Duplikate aus features BEVOR wir selected_engineered extrahieren
            features = list(dict.fromkeys(features))  # Entferne Duplikate zuerst
            
            # ⚠️ WICHTIG: Verwende selected_engineered_original (ursprüngliche Auswahl), nicht selected_engineered!
            # selected_engineered würde aus features berechnet werden, das enthält bereits alle Engineering-Features
            selected_engineered = selected_engineered_original.copy()  # Verwende ursprüngliche Auswahl für Kompatibilität
            
            # Nur die ursprünglich ausgewählten Features verwenden (Basis + ausgewählte Engineering + deren Flags)
            # ⚠️ WICHTIG: Entferne Duplikate durch Verwendung eines Sets
            original_base_features = [f for f in features if f not in all_possible_engineered and not f.endswith('_has_data')]
            original_selected_eng = list(set(selected_engineered_original))  # Verwende ursprüngliche Auswahl
            # ⚠️ KRITISCH: Filtere Flag-Features direkt aus data.columns, nicht aus features!
            # features enthält bereits alle Flag-Features, also müssen wir direkt aus data.columns filtern
            original_selected_flags = [f'{eng_feat}_has_data' for eng_feat in selected_engineered_original if f'{eng_feat}_has_data' in data.columns]  # Direkt aus data.columns filtern
            logger.info(f"🔍 DEBUG: selected_engineered_original={len(selected_engineered_original)} Features: {selected_engineered_original[:5]}...")
            logger.info(f"🔍 DEBUG: original_selected_flags={len(original_selected_flags)} Flags: {original_selected_flags[:5]}...")
            
            # Kombiniere: Basis + ausgewählte Engineering + deren Flags (ohne Duplikate)
            features_to_use = list(dict.fromkeys(original_base_features + original_selected_eng + original_selected_flags))  # dict.fromkeys behält Reihenfolge
            logger.info(f"🎯 Verwende nur ausgewählte Features: {len(original_base_features)} Basis + {len(original_selected_eng)} Engineering + {len(original_selected_flags)} Flags = {len(features_to_use)} total (Duplikate entfernt)")
            features = features_to_use
            # ⚠️ WICHTIG: Markiere dass features gefiltert wurde (für späteren Gebrauch in Zeile 673)
            features_were_filtered_flag = True
            # ⚠️ WICHTIG: Speichere features_to_use für späteren Gebrauch (für finalen Filter)
            filtered_features_to_use = features_to_use.copy()
            # ⚠️ WICHTIG: Speichere features_to_use für späteren Gebrauch (für finalen Filter)
            filtered_features_to_use = features_to_use.copy()
    
    # Verwende nur Features, die tatsächlich in den Daten vorhanden sind
    # ⚠️ WICHTIG: Entferne Duplikate aus features-Liste bevor wir available_features erstellen
    features = list(dict.fromkeys(features))  # dict.fromkeys behält Reihenfolge und entfernt Duplikate
    available_features = [f for f in features if f in data.columns]
    missing_features = [f for f in features if f not in data.columns]
    
    # ⚠️ HINWEIS: price_close wird NICHT zu available_features hinzugefügt, wenn es als target_var verwendet wird.
    # Dies verhindert Data Leakage bei zeitbasierter Vorhersage.
    # price_close wird trotzdem für Engineering-Features verwendet (z.B. price_change, price_roc, etc.).
    
    # ⚠️ KRITISCHER FIX: Stelle sicher, dass Flag-Features in available_features sind!
    # ⚠️ WICHTIG: Wenn spezifische Engineering-Features ausgewählt wurden, nur deren Flag-Features verwenden!
    # (Alle Flag-Features werden erstellt, aber nur die benötigten werden zum Training verwendet)
    if use_flag_features_value:
        # Prüfe ob spezifische Engineering-Features ausgewählt wurden
        # ⚠️ WICHTIG: Wenn features bereits gefiltert wurde (Zeile 644), dann enthält available_features bereits die richtigen Flag-Features!
        # Verwende features_were_filtered_flag (wurde in Zeile 646 gesetzt)
        
        if features_were_filtered_flag:
            # features wurde bereits gefiltert - available_features enthält bereits die richtigen Flag-Features
            # Prüfe nur, ob Flag-Features für ausgewählte Engineering-Features fehlen und füge sie hinzu
            logger.info(f"🔍 DEBUG: features_were_filtered_flag=True, selected_engineered_original={len(selected_engineered_original)} Features")
            flag_features_to_add = []
            for eng_feature in selected_engineered_original:
                flag_name = f'{eng_feature}_has_data'
                if flag_name in data.columns and flag_name not in available_features:
                    flag_features_to_add.append(flag_name)
            if flag_features_to_add:
                available_features.extend(flag_features_to_add)
                logger.info(f"🚩 {len(flag_features_to_add)} fehlende Flag-Features für ausgewählte Engineering-Features hinzugefügt")
            else:
                logger.info(f"✅ Features wurden bereits gefiltert - available_features enthält bereits {len([f for f in available_features if f.endswith('_has_data')])} Flag-Features für ausgewählte Engineering-Features")
        else:
            logger.info(f"🔍 DEBUG: features_were_filtered_flag=False, selected_engineered_original={len(selected_engineered_original) if selected_engineered_original else 0} Features")
            if use_engineered_features and selected_engineered_original:
                # features wurde NICHT gefiltert, aber spezifische Engineering-Features wurden ausgewählt
                # Füge nur Flag-Features für ausgewählte Engineering-Features hinzu
                flag_features_to_add = []
                for eng_feature in selected_engineered_original:
                    flag_name = f'{eng_feature}_has_data'
                    if flag_name in data.columns and flag_name not in available_features:
                        flag_features_to_add.append(flag_name)
                if flag_features_to_add:
                    available_features.extend(flag_features_to_add)
                    logger.info(f"🚩 {len(flag_features_to_add)} Flag-Features für ausgewählte Engineering-Features zu available_features hinzugefügt (nur diese werden verwendet)")
            else:
                # Keine spezifischen Engineering-Features ausgewählt - füge ALLE Flag-Features hinzu
                all_flag_features_available = [f for f in data.columns if f.endswith('_has_data') and f not in available_features]
                logger.info(f"🔍 DEBUG: Flag-Features in available_features: {len([f for f in available_features if f.endswith('_has_data')])}, fehlende: {len(all_flag_features_available)}")
                if all_flag_features_available:
                    available_features.extend(all_flag_features_available)
                    logger.info(f"🚩 {len(all_flag_features_available)} Flag-Features zu available_features hinzugefügt (alle werden verwendet)")
    
    # ⚠️ KRITISCH: Entferne Duplikate aus available_features BEVOR wir sie verwenden
    available_features = list(dict.fromkeys(available_features))  # dict.fromkeys behält Reihenfolge und entfernt Duplikate
    
    # ⚠️ BESTE LÖSUNG: Am Ende einen einfachen, stabilen Filter hinzufügen
    # Wenn spezifische Engineering-Features ausgewählt wurden, filtere Flag-Features entsprechend
    # ⚠️ WICHTIG: use_engineered_features könnte nicht verfügbar sein, hole es aus params
    use_engineered_features_for_filter = params.get('use_engineered_features', False) if params else False
    
    # ⚠️ KRITISCH: Debug-Logging, um zu sehen, was in params steht
    logger.info(f"🔍 FLAG-FILTER DEBUG: params keys={list(params.keys()) if params else []}")
    logger.info(f"🔍 FLAG-FILTER DEBUG: params.get('use_engineered_features')={params.get('use_engineered_features') if params else None}")
    logger.info(f"🔍 FLAG-FILTER CHECK: use_flag_features_value={use_flag_features_value}, use_engineered_features_for_filter={use_engineered_features_for_filter}")
    
    if use_flag_features_value and use_engineered_features_for_filter:
        from app.training.feature_engineering import get_engineered_feature_names
        all_possible_engineered = get_engineered_feature_names(window_sizes)
        
        # ⚠️ WICHTIG: Verwende original_requested_features DIREKT (kommt aus API-Anfrage, wurde nie modifiziert)
        # Falls nicht verfügbar, verwende original_features_before_engineering als Fallback
        source_features = original_requested_features if original_requested_features else original_features_before_engineering
        
        # Finde welche Engineering-Features in den ursprünglich angeforderten Features sind
        engineering_features_requested = [f for f in source_features if f in all_possible_engineered]
        
        # Debug-Logging (auch in Datei schreiben für Debugging)
        try:
            with open('/tmp/flag_filter_debug.log', 'w') as f:
                f.write(f"FLAG-FILTER DEBUG:\n")
                f.write(f"  use_flag_features_value={use_flag_features_value}\n")
                f.write(f"  use_engineered_features={use_engineered_features}\n")
                f.write(f"  original_requested_features={original_requested_features}\n")
                f.write(f"  original_requested_features len={len(original_requested_features) if original_requested_features else 0}\n")
                if original_requested_features:
                    f.write(f"  original_requested_features content={original_requested_features[:10]}\n")
                f.write(f"  original_features_before_engineering len={len(original_features_before_engineering)}\n")
                f.write(f"  original_features_before_engineering content={original_features_before_engineering[:10]}\n")
                f.write(f"  source_features len={len(source_features)}\n")
                f.write(f"  source_features content={source_features[:10]}\n")
                f.write(f"  engineering_features_requested len={len(engineering_features_requested)}\n")
                f.write(f"  engineering_features_requested content={engineering_features_requested[:10]}\n")
                f.write(f"  all_possible_engineered len={len(all_possible_engineered)}\n")
        except Exception as e:
            logger.error(f"❌ Fehler beim Schreiben des Debug-Logs: {e}")
        
        logger.info(f"🔍 FLAG-FILTER: original_requested_features={len(original_requested_features) if original_requested_features else 0}, source={len(source_features)}, engineering={len(engineering_features_requested)}")
        
        # Wenn weniger als alle Engineering-Features angefordert wurden (d.h. spezifische Auswahl)
        if len(engineering_features_requested) > 0 and len(engineering_features_requested) < len(all_possible_engineered):
            # Filtere Flag-Features: Nur die für die angeforderten Engineering-Features behalten
            expected_flag_names = [f'{eng_feat}_has_data' for eng_feat in engineering_features_requested]
            flag_features_in_available = [f for f in available_features if f.endswith('_has_data')]
            flag_features_to_keep = [f for f in flag_features_in_available if f in expected_flag_names]
            flag_features_to_remove = [f for f in flag_features_in_available if f not in expected_flag_names]
            
            logger.info(f"🔍 FLAG-FILTER: {len(flag_features_in_available)} Flag-Features in available_features, {len(expected_flag_names)} erwartet")
            
            if flag_features_to_remove:
                available_features = [f for f in available_features if f not in flag_features_to_remove]
                logger.info(f"✅ FLAG-FILTER: {len(flag_features_to_remove)} unerwünschte Flag-Features entfernt, {len(flag_features_to_keep)} behalten (für {len(engineering_features_requested)} angeforderte Engineering-Features)")
                try:
                    with open('/tmp/flag_filter_debug.log', 'a') as f:
                        f.write(f"  ✅ {len(flag_features_to_remove)} Flag-Features entfernt, {len(flag_features_to_keep)} behalten\n")
                        f.write(f"  Erwartete Flags: {expected_flag_names}\n")
                        f.write(f"  Behaltene Flags: {flag_features_to_keep}\n")
                        f.write(f"  Entfernte Flags (erste 10): {flag_features_to_remove[:10]}\n")
                except:
                    pass
            else:
                logger.info(f"ℹ️ FLAG-FILTER: Keine Flag-Features zu entfernen (alle sind bereits korrekt)")
        else:
            logger.info(f"ℹ️ FLAG-FILTER: Keine Filterung nötig ({len(engineering_features_requested)} von {len(all_possible_engineered)} Engineering-Features angefordert)")
            try:
                with open('/tmp/flag_filter_debug.log', 'a') as f:
                    f.write(f"  ℹ️ Keine Filterung nötig\n")
            except:
                pass
    # ⚠️ FINAL FIX: Wenn features gefiltert wurde, filtere Flag-Features in available_features!
    # Dies ist ein sicherer, direkter Fix, der garantiert funktioniert
    # Wir verwenden features_were_filtered_flag, das bereits gesetzt wurde, wenn features gefiltert wurde
    if use_flag_features_value and features_were_filtered_flag and filtered_features_to_use:
        # Wenn features gefiltert wurde, dann enthält features nur die ausgewählten Flag-Features
        # Filtere available_features, um nur die Flag-Features zu behalten, die in features sind
        flag_features_in_filtered = [f for f in filtered_features_to_use if f.endswith('_has_data')]
        flag_features_in_available = [f for f in available_features if f.endswith('_has_data')]
        flag_features_to_keep = [f for f in flag_features_in_available if f in flag_features_in_filtered]
        flag_features_to_remove = [f for f in flag_features_in_available if f not in flag_features_in_filtered]
        
        # Entferne unerwünschte Flag-Features
        if flag_features_to_remove:
            available_features = [f for f in available_features if f not in flag_features_to_remove]
            logger.info(f"✅ FINAL FIX: {len(flag_features_to_remove)} unerwünschte Flag-Features entfernt, {len(flag_features_to_keep)} behalten (aus features)")
    
    # ⚠️ KRITISCH: Direkter Filter VOR 'FINAL: available_features', damit er definitiv ausgeführt wird
    # Prüfe nochmal, ob use_engineered_features gesetzt ist und ob wir filtern müssen
    use_engineered_features_for_filter_final = params.get('use_engineered_features', False) if params else False
    use_flag_features_value_final = params.get('use_flag_features', False) if params else False
    
    # ⚠️ DEBUG: Logge die Werte für Debugging (kann später entfernt werden)
    logger.debug(f"🔍 FLAG-FILTER FINAL: use_flag_features_value_final={use_flag_features_value_final}, use_engineered_features_for_filter_final={use_engineered_features_for_filter_final}")
    logger.debug(f"🔍 FLAG-FILTER FINAL: original_requested_features={original_requested_features}")
    
    if use_flag_features_value_final and use_engineered_features_for_filter_final:
        from app.training.feature_engineering import get_engineered_feature_names
        all_possible_engineered_final = get_engineered_feature_names(window_sizes)
        
        # Verwende original_requested_features DIREKT
        source_features_final = original_requested_features if original_requested_features else original_features_before_engineering
        
        # Finde welche Engineering-Features in den ursprünglich angeforderten Features sind
        engineering_features_requested_final = [f for f in source_features_final if f in all_possible_engineered_final]
        
        # ⚠️ DEBUG: Logge die Werte
        logger.info(f"🔍 FLAG-FILTER FINAL DEBUG: source_features_final len={len(source_features_final)}, content={source_features_final[:10]}")
        logger.info(f"🔍 FLAG-FILTER FINAL DEBUG: engineering_features_requested_final len={len(engineering_features_requested_final)}, content={engineering_features_requested_final}")
        logger.info(f"🔍 FLAG-FILTER FINAL DEBUG: all_possible_engineered_final len={len(all_possible_engineered_final)}")
        
        # Wenn weniger als alle Engineering-Features angefordert wurden (d.h. spezifische Auswahl)
        if len(engineering_features_requested_final) > 0 and len(engineering_features_requested_final) < len(all_possible_engineered_final):
            # Filtere Flag-Features: Nur die für die angeforderten Engineering-Features behalten
            expected_flag_names_final = [f'{eng_feat}_has_data' for eng_feat in engineering_features_requested_final]
            flag_features_in_available_final = [f for f in available_features if f.endswith('_has_data')]
            flag_features_to_keep_final = [f for f in flag_features_in_available_final if f in expected_flag_names_final]
            flag_features_to_remove_final = [f for f in flag_features_in_available_final if f not in expected_flag_names_final]
            
            if flag_features_to_remove_final:
                available_features = [f for f in available_features if f not in flag_features_to_remove_final]
                logger.info(f"✅ FLAG-FILTER FINAL: {len(flag_features_to_remove_final)} unerwünschte Flag-Features entfernt, {len(flag_features_to_keep_final)} behalten (für {len(engineering_features_requested_final)} angeforderte Engineering-Features)")
                logger.info(f"🔍 FLAG-FILTER FINAL: Erwartete Flags: {expected_flag_names_final}")
    
    logger.info(f"📊 FINAL: available_features hat {len(available_features)} Features (davon {len([f for f in available_features if f.endswith('_has_data')])} Flag-Features, Duplikate entfernt)")

    if missing_features:
        logger.warning(f"⚠️ Einige Features nicht in Daten gefunden (werden übersprungen): {missing_features}")

    if not available_features:
        raise ValueError("Keine Features in Daten gefunden!")

    X = data[available_features].values
    y = labels.values
    logger.info(f"📊 Training mit {len(available_features)} Features ({available_features}), {len(data)} Samples")
    logger.info(f"⚠️ Übersprungene Features: {missing_features}")

    # 🐛 DEBUG: Finale Feature-Analyse
    logger.info(f"🐛 DEBUG - Finale Feature-Zusammenfassung:")
    logger.info(f"🐛 DEBUG - Ursprüngliche Features-Liste: {len(features)}")
    logger.info(f"🐛 DEBUG - Verfügbare Features: {len(available_features)}")
    logger.info(f"🐛 DEBUG - Fehlende Features: {len(missing_features)}")

    # Kategorisiere fehlende Features
    base_features = ['price_open', 'price_high', 'price_low', 'price_close', 'volume_sol',
                    'buy_volume_sol', 'sell_volume_sol', 'net_volume_sol', 'market_cap_close',
                    'phase_id_at_time', 'dev_sold_amount', 'buy_pressure_ratio', 'unique_signer_ratio',
                    'whale_buy_volume_sol', 'whale_sell_volume_sol', 'volatility_pct', 'avg_trade_size_sol',
                    'ath_price_sol', 'price_vs_ath_pct', 'minutes_since_ath']

    ath_features = ['rolling_ath', 'ath_distance_pct', 'ath_breakout', 'ath_age_hours',
                   'ath_is_recent', 'ath_is_old']

    # engineered_features = get_engineered_feature_names(window_sizes)  # Deaktiviert wegen Import-Fehlern
    engineered_features = []

    missing_base = [f for f in missing_features if f in base_features]
    missing_ath = [f for f in missing_features if f in ath_features]
    missing_engineered = [f for f in missing_features if f in engineered_features]

    logger.info(f"🐛 DEBUG - Fehlende Basis-Features: {len(missing_base)} - {missing_base}")
    logger.info(f"🐛 DEBUG - Fehlende ATH-Features: {len(missing_ath)} - {missing_ath}")
    logger.info(f"🐛 DEBUG - Fehlende Engineered-Features: {len(missing_engineered)} - {missing_engineered}")

    # Prüfe Daten-Verfügbarkeit für kritische Spalten
    critical_columns = ['dev_sold_amount', 'buy_pressure_ratio', 'unique_signer_ratio',
                       'ath_distance_pct', 'ath_breakout', 'minutes_since_ath']
    logger.info(f"🐛 DEBUG - Kritische Spalten in DataFrame:")
    for col in critical_columns:
        exists = col in data.columns
        if exists:
            nan_count = data[col].isna().sum()
            zero_count = (data[col] == 0).sum()
            logger.info(f"🐛 DEBUG -   {col}: ✅ vorhanden, NaN: {nan_count}, Zero: {zero_count}")
        else:
            logger.info(f"🐛 DEBUG -   {col}: ❌ FEHLT")
    
    # 3. TimeSeriesSplit für Cross-Validation (bei Zeitreihen wichtig!)
    use_timeseries_split = params.get('use_timeseries_split', True)  # Default: True
    
    cv_results = None
    if use_timeseries_split:
        from sklearn.model_selection import TimeSeriesSplit, cross_validate
        
        logger.info("🔀 Verwende TimeSeriesSplit für Cross-Validation...")
        
        # TimeSeriesSplit konfigurieren
        n_splits = params.get('cv_splits', 5)  # Anzahl Splits
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        # Cross-Validation durchführen
        logger.info(f"📊 Führe {n_splits}-Fold Cross-Validation durch...")
        
        # Erstelle temporäres Modell für CV
        temp_model = create_model(model_type, params)
        
        cv_results = cross_validate(
            estimator=temp_model,
            X=X,
            y=y,
            cv=tscv,
            scoring=['accuracy', 'f1', 'precision', 'recall'],
            return_train_score=True,
            n_jobs=-1  # Parallelisierung
        )
        
        # Ergebnisse loggen
        logger.info("📊 Cross-Validation Ergebnisse:")
        logger.info(f"   Train Accuracy: {cv_results['train_accuracy'].mean():.4f} ± {cv_results['train_accuracy'].std():.4f}")
        logger.info(f"   Test Accuracy:  {cv_results['test_accuracy'].mean():.4f} ± {cv_results['test_accuracy'].std():.4f}")
        logger.info(f"   Train F1:       {cv_results['train_f1'].mean():.4f} ± {cv_results['train_f1'].std():.4f}")
        logger.info(f"   Test F1:        {cv_results['test_f1'].mean():.4f} ± {cv_results['test_f1'].std():.4f}")
        
        # Overfitting-Check
        train_test_gap = cv_results['train_accuracy'].mean() - cv_results['test_accuracy'].mean()
        if train_test_gap > 0.1:
            logger.warning(f"⚠️ OVERFITTING erkannt! Train-Test Gap: {train_test_gap:.2%}")
            logger.warning("   → Modell generalisiert schlecht auf neue Daten")
        
        # Final Model Training auf allen Daten
        logger.info("🎯 Trainiere finales Modell auf allen Daten...")
        
        # Verwende letzten Split für finales Test-Set
        splits = list(tscv.split(X))
        last_train_idx, last_test_idx = splits[-1]
        
        X_final_train, X_final_test = X[last_train_idx], X[last_test_idx]
        y_final_train, y_final_test = y[last_train_idx], y[last_test_idx]
        
        logger.info(f"📊 Final Train-Set: {len(X_final_train)} Zeilen, Test-Set: {len(X_final_test)} Zeilen")
        
    else:
        # Fallback: Einfacher Train-Test-Split (für Rückwärtskompatibilität)
        logger.info("ℹ️ Verwende einfachen Train-Test-Split (nicht empfohlen für Zeitreihen)")
        X_final_train, X_final_test, y_final_train, y_final_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    
    # 3.5. Imbalanced Data Handling mit SMOTE (auf Train-Set)
    use_smote = params.get('use_smote', True)  # Default: True für bessere Performance
    
    if use_smote:
        # Label-Balance prüfen
        positive_ratio = y_final_train.sum() / len(y_final_train)
        negative_ratio = 1 - positive_ratio
        
        logger.info(f"📊 Label-Balance: {positive_ratio:.2%} positive, {negative_ratio:.2%} negative")
        
        # SMOTE anwenden wenn starkes Ungleichgewicht
        balance_threshold = 0.3  # Wenn < 30% oder > 70% → SMOTE
        if positive_ratio < balance_threshold or positive_ratio > (1 - balance_threshold):
            logger.info("⚖️ Starkes Label-Ungleichgewicht erkannt - Wende SMOTE an...")
            
            try:
                from imblearn.over_sampling import SMOTE
                from imblearn.under_sampling import RandomUnderSampler
                from imblearn.pipeline import Pipeline as ImbPipeline
                
                # SMOTE + Random Under-Sampling Kombination
                # SMOTE erhöht Minority-Klasse, Under-Sampling reduziert Majority-Klasse
                sampling_strategy_smote = 0.5  # Ziel: Minority-Klasse auf 50% der Majority-Klasse
                sampling_strategy_under = 0.8  # Dann: Majority auf 80% der neuen Minority
                
                # K-Neighbors für SMOTE (muss <= Anzahl positive Samples sein)
                k_neighbors = min(5, max(1, int(y_final_train.sum()) - 1))
                
                smote = SMOTE(
                    sampling_strategy=sampling_strategy_smote,
                    random_state=42,
                    k_neighbors=k_neighbors
                )
                under = RandomUnderSampler(
                    sampling_strategy=sampling_strategy_under,
                    random_state=42
                )
                
                # Pipeline erstellen
                pipeline = ImbPipeline([
                    ('smote', smote),
                    ('under', under)
                ])
                
                X_train_balanced, y_train_balanced = pipeline.fit_resample(X_final_train, y_final_train)
                
                logger.info(f"✅ SMOTE abgeschlossen:")
                logger.info(f"   Vorher: {len(X_final_train)} Samples ({y_final_train.sum()} positive, {len(y_final_train) - y_final_train.sum()} negative)")
                logger.info(f"   Nachher: {len(X_train_balanced)} Samples ({y_train_balanced.sum()} positive, {len(y_train_balanced) - y_train_balanced.sum()} negative)")
                logger.info(f"   Neue Balance: {y_train_balanced.sum() / len(y_train_balanced):.2%} positive")
                
                X_final_train = X_train_balanced
                y_final_train = y_train_balanced
                
            except Exception as e:
                logger.warning(f"⚠️ SMOTE fehlgeschlagen: {e} - Training ohne SMOTE fortsetzen")
                logger.warning("   Mögliche Ursachen: Zu wenig positive Samples für SMOTE")
        else:
            logger.info("✅ Label-Balance akzeptabel - Kein SMOTE nötig")
    else:
        logger.info("ℹ️ SMOTE deaktiviert (use_smote=False)")
    
    # 4. Erstelle und trainiere Modell (CPU-BOUND - blockiert!)
    model = create_model(model_type, params)
    logger.info(f"⚙️ Training läuft... (kann einige Minuten dauern)")
    model.fit(X_final_train, y_final_train)  # ⚠️ Blockiert Event Loop - deshalb run_in_executor!
    logger.info(f"✅ Training abgeschlossen")
    
    # 5. Berechne Metriken auf finalem Test-Set
    y_pred = model.predict(X_final_test)
    accuracy = accuracy_score(y_final_test, y_pred)
    f1 = f1_score(y_final_test, y_pred)
    precision = precision_score(y_final_test, y_pred)
    recall = recall_score(y_final_test, y_pred)
    
    logger.info(f"📈 Metriken: Accuracy={accuracy:.4f}, F1={f1:.4f}, Precision={precision:.4f}, Recall={recall:.4f}")
    
    # 5.5. Zusätzliche Metriken berechnen
    from sklearn.metrics import roc_auc_score, matthews_corrcoef, confusion_matrix
    
    # ROC-AUC (benötigt Wahrscheinlichkeiten)
    roc_auc = None
    if hasattr(model, 'predict_proba'):
        try:
            y_pred_proba = model.predict_proba(X_final_test)[:, 1]
            roc_auc = roc_auc_score(y_final_test, y_pred_proba)
            logger.info(f"📊 ROC-AUC: {roc_auc:.4f}")
        except Exception as e:
            logger.warning(f"⚠️ ROC-AUC konnte nicht berechnet werden: {e}")
    else:
        logger.info("ℹ️ Modell unterstützt keine Wahrscheinlichkeiten (predict_proba) - ROC-AUC nicht verfügbar")
    
    # Confusion Matrix Details
    cm = confusion_matrix(y_final_test, y_pred)
    if cm.size == 4:  # 2x2 Matrix
        tn, fp, fn, tp = cm.ravel()
    else:
        tn, fp, fn, tp = 0, 0, 0, 0
    
    # False Positive Rate (wichtig für Pump-Detection!)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    # False Negative Rate
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    # Matthews Correlation Coefficient (besser für imbalanced data)
    mcc = matthews_corrcoef(y_final_test, y_pred)
    
    # Profit-Simulation (vereinfacht)
    # Annahme: 1% Gewinn pro richtig erkanntem Pump, 0.5% Verlust pro False Positive
    profit_per_tp = 0.01  # 1%
    loss_per_fp = -0.005  # -0.5%
    simulated_profit = (tp * profit_per_tp) + (fp * loss_per_fp)
    simulated_profit_pct = simulated_profit / len(y_final_test) * 100 if len(y_final_test) > 0 else 0.0
    
    logger.info(f"💰 Simulierter Profit: {simulated_profit_pct:.2f}% (bei {tp} TP, {fp} FP)")
    roc_auc_str = f"{roc_auc:.4f}" if roc_auc is not None else "N/A"
    logger.info(f"📊 Zusätzliche Metriken: ROC-AUC={roc_auc_str}, MCC={mcc:.4f}, FPR={fpr:.4f}, FNR={fnr:.4f}")
    
    # 5.6. Rug-spezifische Metriken berechnen
    rug_metrics = {}
    try:
        y_pred_proba = None
        if hasattr(model, 'predict_proba'):
            y_pred_proba = model.predict_proba(X_final_test)[:, 1]
        
        rug_metrics = calculate_rug_detection_metrics(
            y_true=y_final_test,
            y_pred=y_pred,
            y_pred_proba=y_pred_proba,
            X_test=X_final_test,
            features=features
        )
        
        # Merge mit Standard-Metriken
        logger.info(f"📊 Rug-Detection-Metriken: {rug_metrics}")
    except Exception as e:
        logger.warning(f"⚠️ Fehler beim Berechnen der Rug-Detection-Metriken: {e}")
    
    # 6. Feature Importance extrahieren (wenn verfügbar)
    feature_importance = {}
    if hasattr(model, 'feature_importances_'):
        # Für Random Forest und XGBoost
        importances = model.feature_importances_
        feature_importance = dict(zip(features, importances.tolist()))
        logger.info(f"🎯 Feature Importance: {feature_importance}")
    
    # 7. Speichere Modell als .pkl (Datei) UND serialisiere für DB
    os.makedirs(model_storage_path, exist_ok=True)
    # ⚠️ WICHTIG: UTC-Zeitstempel verwenden!
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    model_filename = f"model_{model_type}_{timestamp}.pkl"
    model_path = os.path.join(model_storage_path, model_filename)

    # Serialisiere Modell für DB-Speicherung (BLOB)
    import io
    model_buffer = io.BytesIO()
    joblib.dump(model, model_buffer)
    model_data = model_buffer.getvalue()
    logger.info(f"📦 Modell serialisiert: {len(model_data)} Bytes")

    # Speichere auch als Datei (für Backward-Kompatibilität)
    joblib.dump(model, model_path)
    logger.info(f"💾 Modell gespeichert: {model_path}")
    
    # 8. Return Ergebnisse
    result = {
        "accuracy": float(accuracy),
        "f1": float(f1),
        "precision": float(precision),
        "recall": float(recall),
        "roc_auc": float(roc_auc) if roc_auc else None,  # NEU
        "mcc": float(mcc),  # NEU
        "fpr": float(fpr),  # NEU
        "fnr": float(fnr),  # NEU
        "confusion_matrix": {  # NEU
            "tp": int(tp),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn)
        },
        "simulated_profit_pct": float(simulated_profit_pct),  # NEU
        "rug_detection_metrics": rug_metrics,  # NEU: Rug-spezifische Metriken
        "model_path": model_path,
        "model_data": model_data,  # NEU: Serialisiertes Modell für DB
        "feature_importance": feature_importance,  # Als Dict (für JSONB)
        "num_samples": len(data),
        "num_features": len(available_features),  # ⚠️ WICHTIG: Anzahl der tatsächlich verwendeten Features
        "features": list(dict.fromkeys(available_features))  # ⚠️ WICHTIG: Erweiterte Features-Liste (inkl. engineered features UND Flag-Features) zurückgeben, Duplikate entfernt
    }
    
    # ⚠️ HINWEIS: price_close wird NICHT zu result['features'] hinzugefügt, wenn es als target_var verwendet wird.
    # Dies verhindert Data Leakage bei zeitbasierter Vorhersage.
    # 27 Base-Features (ohne price_close) + 66 Engineering + 57 Flags = 150 Features ist KORREKT!
    
    # NEU: CV-Ergebnisse hinzufügen (wenn verfügbar)
    if cv_results is not None:
        result["cv_scores"] = {
            "train_accuracy": cv_results['train_accuracy'].tolist(),
            "test_accuracy": cv_results['test_accuracy'].tolist(),
            "train_f1": cv_results['train_f1'].tolist(),
            "test_f1": cv_results['test_f1'].tolist(),
            "train_precision": cv_results['train_precision'].tolist(),
            "test_precision": cv_results['test_precision'].tolist(),
            "train_recall": cv_results['train_recall'].tolist(),
            "test_recall": cv_results['test_recall'].tolist()
        }
        result["cv_overfitting_gap"] = float(
            cv_results['train_accuracy'].mean() - cv_results['test_accuracy'].mean()
        )
    
    return result

async def train_model(
    model_type: str,
    features: List[str],
    target_var: Optional[str],  # Optional wenn zeitbasierte Vorhersage aktiviert
    target_operator: Optional[str],  # Optional wenn zeitbasierte Vorhersage aktiviert
    target_value: Optional[float],  # Optional wenn zeitbasierte Vorhersage aktiviert
    train_start: str | datetime,
    train_end: str | datetime,
    phases: Optional[List[int]] = None,
    params: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None,
    model_storage_path: str = "/app/models",
    # NEU: Zeitbasierte Parameter
    use_time_based: bool = False,
    future_minutes: Optional[int] = None,
    min_percent_change: Optional[float] = None,
    direction: str = "up",
    # ⚠️ FIX: Ursprünglich angeforderten Features direkt aus API-Anfrage
    original_requested_features: Optional[List[str]] = None  # NEU: Ursprünglich angeforderten Features (vor Erweiterung)
) -> Dict[str, Any]:
    """
    Async Wrapper für train_model_sync
    Lädt Daten async, ruft dann sync-Funktion in run_in_executor auf
    
    ⚠️ KRITISCH: CPU-bound Training läuft in run_in_executor!
    
    Args:
        model_type: "random_forest" oder "xgboost" (nur diese beiden!)
        features: Liste der Feature-Namen
        target_var: Ziel-Variable
        target_operator: Vergleichsoperator
        target_value: Schwellwert
        train_start: Start-Zeitpunkt (ISO-Format oder datetime)
        train_end: Ende-Zeitpunkt (ISO-Format oder datetime)
        phases: Liste der Coin-Phasen oder None
        params: Dict mit Hyperparametern (optional, überschreibt Defaults)
        model_name: Name des Modells (optional, wird nicht verwendet)
        model_storage_path: Pfad zum Models-Verzeichnis
    
    Returns:
        Dict mit Metriken, Modell-Pfad, Feature Importance
    """
    import asyncio
    
    logger.info(f"🎯 Starte Modell-Training: {model_type}")
    
    # ⚠️ KRITISCH: Verwende original_requested_features direkt aus API-Anfrage (wurde bereits übergeben)
    # Falls nicht verfügbar, verwende features.copy() als Fallback (könnte bereits erweitert sein)
    if original_requested_features is None:
        original_requested_features = features.copy() if features else []
        logger.warning(f"⚠️ original_requested_features nicht übergeben, verwende features.copy() (könnte bereits erweitert sein)")
    else:
        logger.info(f"✅ original_requested_features aus API-Anfrage erhalten: {len(original_requested_features)} Features")
    # Debug: Schreibe auch in Datei
    try:
        with open('/tmp/original_requested_features_debug.log', 'w') as f:
            f.write(f"TRAIN_MODEL: original_requested_features gespeichert\n")
            f.write(f"  Länge: {len(original_requested_features)}\n")
            f.write(f"  Features: {original_requested_features}\n")
            f.write(f"  Features (erste 10): {original_requested_features[:10]}\n")
    except Exception as e:
        logger.error(f"❌ Fehler beim Schreiben des Debug-Logs (TRAIN_MODEL): {e}")
    logger.info(f"🔍 DEBUG TRAIN_MODEL: original_requested_features gespeichert: {len(original_requested_features)} Features: {original_requested_features[:10]}...")
    
    # 0.5. Wenn keine Features übergeben wurden, verwende Defaults
    exclude_features = (params or {}).get('exclude_features', [])
    if not features:
        features = DEFAULT_FEATURES.copy()
        original_requested_features = features.copy()
        logger.info(f"📊 Verwende Default-Features: {len(features)} Features")
    
    # Entferne ausgeschlossene Features
    if exclude_features:
        features = [f for f in features if f not in exclude_features]
        original_requested_features = [f for f in original_requested_features if f not in exclude_features]
        logger.info(f"📊 Features nach Ausschluss: {len(features)} Features (ausgeschlossen: {exclude_features})")
    
    # 1. Lade Default-Parameter aus DB (async)
    default_params = await get_model_type_defaults(model_type)
    logger.info(f"📋 Default-Parameter: {default_params}")
    
    # 2. Merge mit übergebenen Parametern (übergebene überschreiben Defaults)
    final_params = {**default_params, **(params or {})}
    logger.info(f"⚙️ Finale Parameter: {final_params}")
    
    # 2.3. Prüfe ob Feature-Engineering aktiviert ist (für später in train_model_sync)
    use_engineered_features = final_params.get('use_engineered_features', False)
    if use_engineered_features:
        logger.info("🔧 Feature-Engineering aktiviert (wird nach Daten-Laden durchgeführt)")

    # 2.4. ATH-Features werden später nach Daten-Laden hinzugefügt
    # (nicht hier, da sie erst in Python berechnet werden)
    
    # 2.5. Filtere ATH-Features aus der Loading-Liste (werden später berechnet)
    # ⚠️ WICHTIG: ATH-Features existieren nicht in der Datenbank und werden erst in Python berechnet
    ath_features = ['rolling_ath', 'ath_distance_pct', 'ath_breakout', 'minutes_since_ath', 'ath_age_hours', 'ath_is_recent', 'ath_is_old']
    features_for_db = [f for f in features if f not in ath_features]

    # Bereite Features vor (verhindert Data Leakage bei zeitbasierter Vorhersage)
    features_for_loading, features_for_training = prepare_features_for_training(
        features=features_for_db,  # Basis-Features ohne ATH-Features (nicht in DB)
        target_var=target_var,
        use_time_based=use_time_based
    )
    logger.info(f"📊 Features für Laden: {len(features_for_loading)} - {features_for_loading}")
    logger.info(f"📊 Features für Training: {len(features_for_training)} - {features_for_training}")
    logger.info(f"🧠 ATH-Features werden nach Daten-Laden hinzugefügt: {len(ath_features)} Features - {ath_features}")
    logger.info(f"🧠 Original features: {features}")
    logger.info(f"🧠 features_for_db: {features_for_db}")

    # Aktualisiere die features Liste für weitere Verarbeitung
    features = features_for_training.copy()
    
    # 2.6. Prüfe ATH-Daten-Verfügbarkeit (wenn include_ath aktiviert)
    # Import bereits oben erfolgt
    # Prüfe automatisch, ob ATH-Features in der Features-Liste sind
    ath_feature_names = ['rolling_ath', 'ath_distance_pct', 'ath_breakout', 'minutes_since_ath', 'ath_age_hours', 'ath_is_recent', 'ath_is_old']
    has_ath_features = any(f in features for f in ath_feature_names)
    
    # ⚠️ KRITISCHER BUG-FIX: include_ath muss True sein, wenn use_engineered_features=True ist!
    # include_ath steuert nicht nur ATH-Daten, sondern auch die Generierung von Engineering-Features!
    include_ath = final_params.get('include_ath', has_ath_features or use_engineered_features)  # Auto-detect ATH-Features ODER wenn Engineering aktiviert
    
    if include_ath:
        ath_validation = await validate_ath_data_availability(train_start, train_end)
        if not ath_validation["available"]:
            logger.warning(f"⚠️ Keine ATH-Daten verfügbar! Coverage: {ath_validation.get('coverage_pct', 0):.1f}%")
        else:
            logger.info(f"✅ ATH-Daten verfügbar: {ath_validation['coins_with_ath']}/{ath_validation['total_coins']} Coins ({ath_validation['coverage_pct']:.1f}%)")
    
    # 3. Lade Trainingsdaten (async) - mit target_var für Labels
    data = await load_training_data(
        train_start=train_start,
        train_end=train_end,
        features=features_for_loading,  # Enthält target_var (für Labels benötigt)
        phases=phases,
        include_ath=include_ath  # 🆕 ATH-Daten optional laden (steuert auch Engineering-Features!)
    )
    
    if len(data) == 0:
        raise ValueError("Keine Trainingsdaten gefunden!")
    
    # 3.5. Lade Marktstimmung (SOL-Preis-Kontext) - OPTIONAL
    use_market_context = final_params.get('use_market_context', False)
    
    if use_market_context:
        # Import bereits oben erfolgt
        logger.info("🌍 Füge Marktstimmung (SOL-Preis-Kontext) hinzu...")
        data = await enrich_with_market_context(
            data, 
            train_start=train_start, 
            train_end=train_end
        )
        
        # Füge Context-Features zu Features-Liste hinzu
        context_features = [
            "sol_price_usd",
            # "sol_price_change_pct",  # Wird von enrich_with_market_context erstellt
            "sol_price_ma_5",
            "sol_price_volatility"
        ]
        # Nur hinzufügen wenn nicht bereits vorhanden
        for cf in context_features:
            if cf not in features and cf in data.columns:
                features.append(cf)
                logger.info(f"➕ Context-Feature '{cf}' hinzugefügt")
    else:
        logger.info("ℹ️ Marktstimmung deaktiviert (use_market_context=False)")
    
    # 3.6. Lade Phase-Intervalle (falls zeitbasierte Vorhersage aktiviert)
    phase_intervals = None
    if use_time_based:
        from app.database.models import get_phase_intervals
        phase_intervals = await get_phase_intervals()
        logger.info(f"📊 {len(phase_intervals)} Phase-Intervalle geladen für zeitbasierte Vorhersage")
    
    # ⚠️ HINWEIS: price_close wird NICHT zu features hinzugefügt, wenn es als target_var verwendet wird.
    # Dies verhindert Data Leakage bei zeitbasierter Vorhersage.
    
    # 4. Führe CPU-bound Training in Executor aus (blockiert Event Loop NICHT!)
    loop = asyncio.get_running_loop()
    logger.info(f"🔄 Starte Training in Executor (blockiert Event Loop nicht)...")
    result = await loop.run_in_executor(
        None,  # Nutzt default ThreadPoolExecutor
        train_model_sync,
        data,  # Bereits geladene Daten
        model_type,
        features,  # ✅ Enthält jetzt IMMER price_close!
        target_var,
        target_operator,
        target_value,
        final_params,  # Bereits gemergte Parameter
        model_storage_path,
        # NEU: Zeitbasierte Parameter
        use_time_based,
        future_minutes,
        min_percent_change,
        direction,
        phase_intervals,  # NEU: Phase-Intervalle übergeben
        original_requested_features  # ⚠️ FIX: Ursprünglich angeforderten Features übergeben
    )
    
    logger.info(f"✅ Training erfolgreich abgeschlossen!")
    return result

def calculate_rug_detection_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: Optional[np.ndarray],
    X_test: np.ndarray,
    features: List[str]
) -> Dict[str, Any]:
    """
    Berechnet Rug-Pull-spezifische Metriken.
    
    Args:
        y_true: Echte Labels
        y_pred: Vorhergesagte Labels
        y_pred_proba: Vorhergesagte Wahrscheinlichkeiten (optional)
        X_test: Test-Features
        features: Liste der Feature-Namen
    
    Returns:
        Dict mit Rug-Detection-Metriken
    """
    from sklearn.metrics import confusion_matrix
    
    metrics = {}
    
    # 1. Dev-Sold Detection Rate (wenn Feature vorhanden)
    if 'dev_sold_amount' in features:
        try:
            dev_sold_idx = features.index('dev_sold_amount')
            dev_sold_mask = X_test[:, dev_sold_idx] > 0
            
            if dev_sold_mask.sum() > 0:
                dev_sold_detected = (y_pred[dev_sold_mask] == 1).sum()
                metrics['dev_sold_detection_rate'] = float(dev_sold_detected / dev_sold_mask.sum())
                logger.info(f"📊 Dev-Sold Detection Rate: {metrics['dev_sold_detection_rate']:.2%}")
        except (ValueError, IndexError) as e:
            logger.warning(f"⚠️ Konnte Dev-Sold Detection Rate nicht berechnen: {e}")
    
    # 2. Wash-Trading Detection (wenn Ratio vorhanden)
    if 'unique_signer_ratio' in features:
        try:
            ratio_idx = features.index('unique_signer_ratio')
            wash_trading_mask = X_test[:, ratio_idx] < 0.15
            
            if wash_trading_mask.sum() > 0:
                wash_detected = (y_pred[wash_trading_mask] == 1).sum()
                metrics['wash_trading_detection_rate'] = float(wash_detected / wash_trading_mask.sum())
                logger.info(f"📊 Wash-Trading Detection Rate: {metrics['wash_trading_detection_rate']:.2%}")
        except (ValueError, IndexError) as e:
            logger.warning(f"⚠️ Konnte Wash-Trading Detection Rate nicht berechnen: {e}")
    
    # 3. False Negative Cost (bei Rug-Pull-Detection ist FN teurer als FP!)
    try:
        cm = confusion_matrix(y_true, y_pred)
        if cm.size == 4:  # 2x2 Matrix
            tn, fp, fn, tp = cm.ravel()
            
            # FN = Rug wurde nicht erkannt (sehr teuer!)
            # FP = False Alarm (weniger schlimm)
            fn_cost = fn * 10.0  # FN ist 10x teurer
            fp_cost = fp * 1.0
            metrics['weighted_cost'] = float(fn_cost + fp_cost)
            logger.info(f"💰 Weighted Cost: {metrics['weighted_cost']:.2f} (FN={fn}, FP={fp})")
    except Exception as e:
        logger.warning(f"⚠️ Konnte Weighted Cost nicht berechnen: {e}")
    
    # 4. Profit @ Top-K (wenn Wahrscheinlichkeiten vorhanden)
    if y_pred_proba is not None:
        try:
            for k in [10, 20, 50, 100]:
                if len(y_pred_proba) >= k:
                    top_k_idx = np.argsort(y_pred_proba)[-k:]
                    precision_at_k = y_true[top_k_idx].sum() / k
                    metrics[f'precision_at_{k}'] = float(precision_at_k)
                    logger.info(f"📊 Precision @ Top-{k}: {precision_at_k:.2%}")
        except Exception as e:
            logger.warning(f"⚠️ Konnte Precision @ Top-K nicht berechnen: {e}")
    
    return metrics
