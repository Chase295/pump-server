"""
Feature-Processing für Pump Server
GLEICHE Logik wie Training Service für konsistente Features!
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import asyncpg
from app.database.connection import get_pool
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

FEATURE_HISTORY_SIZE = 1000

async def prepare_features(
    coin_id: str,
    model_config: Dict[str, Any],
    pool: Optional[asyncpg.Pool] = None
) -> pd.DataFrame:
    """
    Bereitet Features für einen Coin auf.
    FLEXIBEL: Liest die tatsächliche Feature-Anzahl vom Modell selbst!
    """
    if pool is None:
        pool = await get_pool()

    # KRITISCH: Erst die tatsächliche Feature-Anzahl und -Namen vom Modell lesen!
    model_feature_names = None
    try:
        from app.prediction.model_manager import load_model
        model_file_path = model_config['local_model_path']
        model = load_model(model_file_path)

        # Feature-Namen direkt vom Modell lesen (wenn vorhanden)
        if hasattr(model, 'feature_names_in_'):
            model_feature_names = list(model.feature_names_in_)
            logger.info(f"Feature-Namen vom Modell gelesen: {len(model_feature_names)} Features")

        # XGBoost/RandomForest haben n_features_in_
        if hasattr(model, 'n_features_in_'):
            expected_features = model.n_features_in_
        elif hasattr(model, 'n_features_'):
            expected_features = model.n_features_
        else:
            # Fallback: Verwende Datenbank-Features
            expected_features = len(model_config['features'])
            logger.warning(f"Modell hat kein n_features_in_ Attribut, verwende DB-Features: {expected_features}")

        logger.debug(f"Modell {model_config['id']} erwartet {expected_features} Features (DB hat {len(model_config['features'])})")

    except Exception as e:
        logger.error(f"Fehler beim Laden des Modells {model_config['id']}: {e}")
        # Fallback: Verwende Datenbank-Features
        expected_features = len(model_config['features'])
        logger.warning(f"Verwende Fallback: {expected_features} Features aus DB")

    # Hole ALLE verfügbaren Basis-Daten
    history = await get_coin_history_for_prediction(
        coin_id=coin_id,
        limit=FEATURE_HISTORY_SIZE,
        phases=model_config.get('phases'),
        pool=pool
    )

    if len(history) == 0:
        raise ValueError(f"Keine Daten für Coin {coin_id} gefunden")

    # Feature-Engineering und Feature-Auswahl
    params = model_config.get('params') or {}

    if model_feature_names:
        # ===== NEUER PFAD: Exakte Feature-Namen vom Modell verwenden =====
        required_features = model_feature_names

        # Pruefe ob Feature-Engineering noetig ist
        has_engineered = any(f for f in required_features if f not in history.columns and not f.endswith('_has_data'))
        has_flags = any(f.endswith('_has_data') for f in required_features)

        if has_engineered or has_flags:
            window_sizes = params.get('feature_engineering_windows', [5, 10, 15])
            history = create_pump_detection_features(history, window_sizes=window_sizes, include_flags=has_flags)

        logger.info(f"Verwende exakte Feature-Namen vom Modell: {len(required_features)} Features")
    else:
        # ===== FALLBACK: Alter Pfad fuer Modelle ohne feature_names_in_ =====
        use_engineered_features = params.get('use_engineered_features', False)

        if use_engineered_features:
            window_sizes = params.get('feature_engineering_windows', [5, 10, 15])
            history = create_pump_detection_features(history, window_sizes=window_sizes)

        # Features auswaehlen: Die ersten N Features aus der Datenbank-Liste
        db_features = model_config['features'].copy()
        original_db_features_count = len(db_features)

        target_variable = model_config.get('target_variable')

        if expected_features == original_db_features_count:
            logger.info(f"BEHALTE target_variable '{target_variable}' als Feature (Modell wurde mit {expected_features} Features trainiert, DB hat {original_db_features_count})")
        elif (model_config.get('target_operator') is None and
              target_variable and
              target_variable in db_features and
              expected_features < original_db_features_count):
            db_features = [f for f in db_features if f != target_variable]
            logger.info(f"ENTFERNE target_variable '{target_variable}' aus Features (Modell erwartet {expected_features}, DB hat {original_db_features_count})")
        else:
            logger.info(f"Keine Aenderung an target_variable '{target_variable}' (expected={expected_features}, db_count={original_db_features_count}, operator={model_config.get('target_operator')})")

        # Nimm nur die ersten expected_features Features
        if len(db_features) >= expected_features:
            required_features = db_features[:expected_features]
        else:
            if not use_engineered_features:
                logger.warning(
                    f"DB hat nur {len(db_features)} Features, Modell braucht {expected_features}. "
                    f"Fuehre Feature-Engineering durch um fehlende Features zu generieren."
                )
                window_sizes = params.get('feature_engineering_windows', [5, 10, 15])
                history = create_pump_detection_features(history, window_sizes=window_sizes)

            available_cols = [c for c in history.columns if c not in ['mint', 'timestamp']]
            required_features = [f for f in db_features if f in available_cols]

            for col in available_cols:
                if len(required_features) >= expected_features:
                    break
                if col not in required_features:
                    required_features.append(col)

            if len(required_features) < expected_features:
                raise ValueError(
                    f"Kann nicht genug Features generieren: {len(required_features)}/{expected_features}. "
                    f"DB-Features: {db_features}, Verfuegbar: {len(available_cols)}"
                )

            logger.warning(
                f"Feature-Ergaenzung: DB hatte {len(db_features)}, Modell braucht {expected_features}. "
                f"Ergaenzt auf {len(required_features)} Features. "
                f"ACHTUNG: Feature-Reihenfolge ist geschaetzt - Vorhersagequalitaet unklar!"
            )

    # Validierung: Prüfe ob alle erforderlichen Features vorhanden sind
    missing = [f for f in required_features if f not in history.columns]
    if missing:
        logger.warning(f"⚠️ Features fehlen: {missing} - versuche zu berechnen...")
        history = calculate_missing_features(history, missing)

        # Prüfe erneut
        still_missing = [f for f in required_features if f not in history.columns]
        if still_missing:
            raise ValueError(
                f"Features können nicht berechnet werden: {still_missing}\n"
                f"Benötigt ({len(required_features)}): {required_features}\n"
                f"Verfügbar ({len(list(history.columns))}): {sorted(list(history.columns))}"
            )

    # Features in der korrekten Reihenfolge zurückgeben
    latest_data = history.iloc[-1:][required_features]
    latest_data = latest_data.fillna(0.0)  # NaN-Werte behandeln
    latest_data = latest_data[required_features]  # Sicherstellen der Reihenfolge

    logger.debug(f"✅ Features vorbereitet für Modell: {len(required_features)}/{expected_features} Features, Shape: {latest_data.shape}")
    return latest_data


async def get_coin_history_for_prediction(
    coin_id: str,
    limit: int,
    phases: Optional[List[int]] = None,
    pool: Optional[asyncpg.Pool] = None
) -> pd.DataFrame:
    """
    Holt Historie für einen Coin (angepasst für Prediction).
    Lädt ALLE verfügbaren Spalten aus coin_metrics für maximale Flexibilität.
    
    WICHTIG: Wenn phases angegeben ist, werden nur Einträge aus diesen Phasen geladen.
    Dies stellt sicher, dass Modelle nur mit Daten aus den Phasen arbeiten, auf die sie trainiert wurden.
    """
    if pool is None:
        pool = await get_pool()

    # PHASEN-FILTER: Wenn Modell auf spezifische Phasen trainiert wurde, filtere danach
    if phases and len(phases) > 0:
        # Modell ist nur für bestimmte Phasen trainiert - lade nur Daten aus diesen Phasen
        query = """
            SELECT * FROM coin_metrics
            WHERE mint = $1
              AND phase_id_at_time = ANY($2::int[])
            ORDER BY timestamp DESC
            LIMIT $3
        """
        rows = await pool.fetch(query, coin_id, phases, limit)
        logger.debug(f"📊 Lade Historie für Coin {coin_id[:8]}... mit Phasen-Filter: {phases} -> {len(rows)} Einträge")
    else:
        # Modell ist für alle Phasen - lade alle Daten
        query = """
            SELECT * FROM coin_metrics
            WHERE mint = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """
        rows = await pool.fetch(query, coin_id, limit)
        logger.debug(f"📊 Lade Historie für Coin {coin_id[:8]}... ohne Phasen-Filter -> {len(rows)} Einträge")

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([dict(row) for row in rows])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()

    # Konvertiere alle numerischen Spalten zu float
    for col in df.columns:
        if col not in ['mint', 'timestamp']:  # Nicht konvertieren
            try:
                # Konvertiere zu numeric, ignoriere Fehler bei Strings
                df[col] = pd.to_numeric(df[col], errors='ignore', downcast='float')
            except:
                pass

    logger.debug(f"📊 Geladene Spalten für {coin_id}: {len(df.columns)} Spalten, {len(df)} Zeilen")
    return df


def add_ath_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fügt ATH-Features hinzu (Data Leakage-frei).
    GLEICHE Logik wie Training Service!
    """
    if 'price_high' not in df.columns or 'price_close' not in df.columns:
        logger.warning("⚠️ ATH-Features: price_high oder price_close fehlen - überspringe")
        return df

    # Rolling ATH: Historisches Maximum bis zu jedem Zeitpunkt
    df['rolling_ath'] = df['price_high'].cummax()

    # ATH-Distance: Wie weit entfernt vom historischen ATH?
    df['ath_distance_pct'] = ((df['rolling_ath'] - df['price_close']) / df['rolling_ath']) * 100

    # ATH-Breakout: Neue ATH-Breaks
    df['prev_rolling_ath'] = df['rolling_ath'].shift(1)
    df['ath_breakout'] = (df['price_high'] > df['prev_rolling_ath']).astype(int)

    # Zeit seit letztem ATH
    # Für Prediction: Vereinfacht - verwende Index als Proxy für Zeit
    ath_timestamps = df.index[df['ath_breakout'] == 1]
    if len(ath_timestamps) > 0:
        # Letzter ATH-Timestamp
        last_ath_idx = ath_timestamps[-1]
        df['minutes_since_ath'] = (df.index - last_ath_idx).total_seconds() / 60
        # Für Daten vor dem ersten ATH
        mask_before_first = df.index < ath_timestamps[0]
        df.loc[mask_before_first, 'minutes_since_ath'] = (df.loc[mask_before_first].index - df.index[0]).total_seconds() / 60
    else:
        # Kein ATH gefunden - verwende Zeit seit Anfang
        df['minutes_since_ath'] = (df.index - df.index[0]).total_seconds() / 60

    # ATH-Zeit-Features
    df['ath_age_hours'] = df['minutes_since_ath'] / 60.0
    df['ath_is_recent'] = (df['minutes_since_ath'] < 60).astype(int)  # Innerhalb 1 Stunde
    df['ath_is_old'] = (df['minutes_since_ath'] > 1440).astype(int)   # Älter als 24 Stunden

    # NaN-Werte behandeln
    df['ath_distance_pct'] = df['ath_distance_pct'].fillna(100.0)
    df['minutes_since_ath'] = df['minutes_since_ath'].fillna(0.0)
    df['ath_age_hours'] = df['ath_age_hours'].fillna(0.0)

    logger.info(f"✅ ATH-Features hinzugefügt: rolling_ath, ath_distance_pct, ath_breakout, minutes_since_ath, ath_age_hours, ath_is_recent, ath_is_old")
    return df


def create_pump_detection_features(
    data: pd.DataFrame,
    window_sizes: list = [5, 10, 15],
    include_flags: bool = False
) -> pd.DataFrame:
    """
    Erstellt zusätzliche Features für Pump-Detection.
    GLEICHE Logik wie Training Service!

    Args:
        include_flags: Wenn True, werden _has_data Flag-Features erzeugt
                       (zeigen an ob genug Daten fuer ein Window vorhanden sind)
    """
    df = data.copy()

    if not df.index.is_monotonic_increasing:
        df = df.sort_index()

    # Coin-Age berechnen (wird fuer Flag-Features benoetigt)
    if include_flags:
        if hasattr(df.index, 'dtype') and pd.api.types.is_datetime64_any_dtype(df.index):
            time_diff = (df.index - df.index[0]).total_seconds() / 60
            df['coin_age_minutes'] = time_diff
        else:
            df['coin_age_minutes'] = range(len(df))
            logger.warning("Kein Datetime-Index - verwende Zeilen-Index als Coin-Age Proxy")

    # Zuerst ATH-Features hinzufügen (falls nicht schon vorhanden)
    if 'rolling_ath' not in df.columns:
        df = add_ath_features(df)

    # Dev-Tracking Features (KRITISCH!)
    if 'dev_sold_amount' in df.columns:
        df['dev_sold_flag'] = (df['dev_sold_amount'].fillna(0) > 0).astype(int)
        df['dev_sold_cumsum'] = df['dev_sold_amount'].fillna(0).cumsum()
        for window in window_sizes:
            df[f'dev_sold_spike_{window}'] = (
                df['dev_sold_amount'].fillna(0) > df['dev_sold_amount'].fillna(0).rolling(window, min_periods=1).mean() * 2
            ).astype(int)
            if include_flags:
                df[f'dev_sold_spike_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # Ratio-Features (Buy-Pressure)
    if 'buy_pressure_ratio' in df.columns:
        for window in window_sizes:
            df[f'buy_pressure_ma_{window}'] = (
                df['buy_pressure_ratio'].fillna(0).rolling(window, min_periods=1).mean()
            )
            df[f'buy_pressure_trend_{window}'] = (
                df['buy_pressure_ratio'] - df[f'buy_pressure_ma_{window}']
            )
            if include_flags:
                df[f'buy_pressure_ma_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                df[f'buy_pressure_trend_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # Whale-Aktivität Features
    if 'whale_buy_volume_sol' in df.columns and 'whale_sell_volume_sol' in df.columns:
        df['whale_net_volume'] = (
            df['whale_buy_volume_sol'].fillna(0) -
            df['whale_sell_volume_sol'].fillna(0)
        )
        for window in window_sizes:
            df[f'whale_activity_{window}'] = (
                df['whale_buy_volume_sol'].fillna(0).rolling(window, min_periods=1).sum() +
                df['whale_sell_volume_sol'].fillna(0).rolling(window, min_periods=1).sum()
            )
            if include_flags:
                df[f'whale_activity_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
        
        # Whale Dominanz (KRITISCH: Muss berechnet werden!)
        if 'volume_sol' in df.columns and 'whale_dominance' not in df.columns:
            df['whale_dominance'] = (
                (df['whale_buy_volume_sol'].fillna(0) + df['whale_sell_volume_sol'].fillna(0)) /
                (df['volume_sol'] + 0.001)
            ).fillna(0)
            logger.debug("✅ Berechnet: whale_dominance in create_pump_detection_features")

    # Buy/Sell Ratio (wichtig für Sentiment)
    if 'num_buys' in df.columns and 'num_sells' in df.columns:
        df['buy_sell_ratio'] = (df['num_buys'] / (df['num_sells'] + 1)).fillna(1)

    # Volatilitäts-Features
    if 'volatility_pct' in df.columns:
        for window in window_sizes:
            df[f'volatility_ma_{window}'] = (
                df['volatility_pct'].rolling(window, min_periods=1).mean()
            )
            df[f'volatility_spike_{window}'] = (
                df['volatility_pct'] >
                df[f'volatility_ma_{window}'] * 1.5
            ).astype(int)
            if include_flags:
                df[f'volatility_ma_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                df[f'volatility_spike_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # Wash-Trading Detection
    if 'unique_signer_ratio' in df.columns:
        for window in window_sizes:
            df[f'wash_trading_flag_{window}'] = (
                df['unique_signer_ratio'].rolling(window, min_periods=1).mean() < 0.3
            ).astype(int)
            if include_flags:
                df[f'wash_trading_flag_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # Volume-Patterns (erweitert)
    if 'net_volume_sol' in df.columns:
        for window in window_sizes:
            df[f'net_volume_ma_{window}'] = df['net_volume_sol'].rolling(window, min_periods=1).mean()
            df[f'volume_flip_{window}'] = (
                np.sign(df['net_volume_sol']) != np.sign(df['net_volume_sol'].shift(window))
            ).astype(int)
            if include_flags:
                df[f'net_volume_ma_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                df[f'volume_flip_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # Price Momentum (erweitert)
    if 'price_close' in df.columns:
        for window in window_sizes:
            df[f'price_change_{window}'] = df['price_close'].diff(window)
            df[f'price_roc_{window}'] = (
                (df['price_close'] - df['price_close'].shift(window)) /
                df['price_close'].shift(window).replace(0, np.nan)
            ) * 100
            # Price Acceleration (Beschleunigung der Preisaenderung)
            price_change_raw = df['price_close'].diff(window)
            df[f'price_acceleration_{window}'] = price_change_raw.diff(window)
            if include_flags:
                df[f'price_change_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                df[f'price_roc_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                df[f'price_acceleration_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # Volume Patterns (erweitert)
    if 'volume_sol' in df.columns:
        for window in window_sizes:
            rolling_avg = df['volume_sol'].rolling(window=window, min_periods=1).mean()
            df[f'volume_ratio_{window}'] = df['volume_sol'] / rolling_avg.replace(0, np.nan)
            vol_ma = df['volume_sol'].rolling(window * 2, min_periods=1).mean()
            df[f'volume_spike_{window}'] = (df['volume_sol'] > vol_ma * 2).astype(int)
            if include_flags:
                df[f'volume_ratio_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                df[f'volume_spike_{window}_has_data'] = (df['coin_age_minutes'] >= window * 2).astype(int)

    # Market Cap Velocity
    if 'market_cap_close' in df.columns:
        for window in window_sizes:
            df[f'mcap_velocity_{window}'] = df['market_cap_close'].diff(window)
            if include_flags:
                df[f'mcap_velocity_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # ATH-basierte Rolling-Window Features
    if 'ath_distance_pct' in df.columns and 'ath_breakout' in df.columns:
        for window in window_sizes:
            # ATH-Trend (nähert sich Preis dem ATH?)
            df[f'ath_distance_trend_{window}'] = (
                df['ath_distance_pct'].rolling(window, min_periods=1).mean()
            )
            df[f'ath_approach_{window}'] = (
                df[f'ath_distance_trend_{window}'].diff() < 0
            ).astype(int)

            # ATH-Breakout-Häufigkeit
            df[f'ath_breakout_count_{window}'] = (
                df['ath_breakout'].rolling(window, min_periods=1).sum()
            )

            # ATH-Breakout-Volumen
            if 'volume_sol' in df.columns:
                ath_breakout_volume = df['ath_breakout'] * df['volume_sol']
                df[f'ath_breakout_volume_ma_{window}'] = (
                    ath_breakout_volume.rolling(window, min_periods=1).mean()
                )

            if include_flags:
                df[f'ath_distance_trend_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                df[f'ath_approach_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                df[f'ath_breakout_count_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)
                if 'volume_sol' in df.columns:
                    df[f'ath_breakout_volume_ma_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # ATH-Zeit-Features
    if 'minutes_since_ath' in df.columns:
        for window in window_sizes:
            df[f'ath_age_trend_{window}'] = (
                df['minutes_since_ath'].rolling(window, min_periods=1).mean()
            )
            if include_flags:
                df[f'ath_age_trend_{window}_has_data'] = (df['coin_age_minutes'] >= window).astype(int)

    # Cleanup temporaere Spalten
    if include_flags and 'coin_age_minutes' in df.columns:
        # Nur entfernen wenn coin_age_minutes nicht in den benoetigten Features ist
        # (wird spaeter ggf. nochmal benoetigt, aber normalerweise kein Modell-Feature)
        pass  # Behalten - wird spaeter durch Feature-Selektion gefiltert

    # NaN-Werte behandeln (wie im Training Service)
    df.fillna(0, inplace=True)
    df.replace([np.inf, -np.inf], 0, inplace=True)

    return df


async def enrich_with_market_context(data: pd.DataFrame, pool: Optional[asyncpg.Pool] = None) -> pd.DataFrame:
    """
    Fügt SOL-Preis-Kontext hinzu (GLEICHE Logik wie Training Service!)
    """
    if pool is None:
        pool = await get_pool()

    df = data.copy()

    # SOL-Preis-Daten aus exchange_rates laden
    # Annahme: Die Daten sind bereits in einem Zeitbereich
    try:
        # Hier würden wir eigentlich die SOL-Daten aus der DB laden
        # Für jetzt: Placeholder - in Produktion würden wir das implementieren
        logger.info("ℹ️ Marktstimmung: SOL-Preis-Kontext wird hinzugefügt (Placeholder)")

        # Placeholder-Werte (würden aus DB geladen werden)
        if 'sol_price_usd' not in df.columns:
            df['sol_price_usd'] = 150.0  # Placeholder
            df['sol_price_change_pct'] = 0.0
            df['sol_price_ma_5'] = 150.0
            df['sol_price_volatility'] = 0.02

    except Exception as e:
        logger.warning(f"⚠️ Marktstimmung konnte nicht geladen werden: {e}")
        # Fallback-Werte
        df['sol_price_usd'] = 150.0
        df['sol_price_change_pct'] = 0.0
        df['sol_price_ma_5'] = 150.0
        df['sol_price_volatility'] = 0.02

    return df


def calculate_missing_base_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet fehlende Basis-Features aus verfügbaren Daten.
    GLEICHE Logik wie Training Service!
    """
    df = df.copy()

    # net_volume_sol berechnen falls fehlend
    if 'net_volume_sol' not in df.columns:
        if 'buy_volume_sol' in df.columns and 'sell_volume_sol' in df.columns:
            df['net_volume_sol'] = df['buy_volume_sol'] - df['sell_volume_sol']
            logger.debug("✅ Berechnet: net_volume_sol")

    # buy_pressure_ratio berechnen falls fehlend
    if 'buy_pressure_ratio' not in df.columns:
        if 'buy_volume_sol' in df.columns and 'sell_volume_sol' in df.columns:
            total_volume = df['buy_volume_sol'] + df['sell_volume_sol']
            df['buy_pressure_ratio'] = df['buy_volume_sol'] / total_volume.replace(0, np.nan)
            df['buy_pressure_ratio'] = df['buy_pressure_ratio'].fillna(0.5)
            logger.debug("✅ Berechnet: buy_pressure_ratio")

    # dev_sold_amount falls fehlend (kann nicht berechnet werden)
    if 'dev_sold_amount' not in df.columns:
        df['dev_sold_amount'] = 0.0
        logger.warning("⚠️ dev_sold_amount nicht verfügbar - setze auf 0.0")

    # whale_buy_volume_sol und whale_sell_volume_sol falls fehlend
    if 'whale_buy_volume_sol' not in df.columns:
        df['whale_buy_volume_sol'] = 0.0
        logger.warning("⚠️ whale_buy_volume_sol nicht verfügbar - setze auf 0.0")

    if 'whale_sell_volume_sol' not in df.columns:
        df['whale_sell_volume_sol'] = 0.0
        logger.warning("⚠️ whale_sell_volume_sol nicht verfügbar - setze auf 0.0")

    # unique_signer_ratio falls fehlend
    if 'unique_signer_ratio' not in df.columns:
        df['unique_signer_ratio'] = 0.5  # Neutraler Wert
        logger.warning("⚠️ unique_signer_ratio nicht verfügbar - setze auf 0.5")

    # volatility_pct falls fehlend
    if 'volatility_pct' not in df.columns:
        df['volatility_pct'] = 0.0
        logger.warning("⚠️ volatility_pct nicht verfügbar - setze auf 0.0")

    # market_cap_close falls fehlend
    if 'market_cap_close' not in df.columns:
        df['market_cap_close'] = 0.0
        logger.warning("⚠️ market_cap_close nicht verfügbar - setze auf 0.0")

    return df


def calculate_missing_features(df: pd.DataFrame, missing_features: List[str]) -> pd.DataFrame:
    """
    Berechnet fehlende Features aus verfügbaren Daten.
    VEREINFACHT: Fokussiert auf funktionierende Fallbacks.
    """
    df = df.copy()

    # Erst Basis-Features berechnen
    df = calculate_missing_base_features(df)

    calculated_features = []

    # Spezielle Feature-Berechnungen (BEVOR Fallback auf 0.0)
    for feature in missing_features:
        if feature in df.columns:
            continue

        try:
            # Whale Dominanz (KRITISCH: Muss berechnet werden, nicht auf 0.0 setzen!)
            if feature == 'whale_dominance':
                if 'whale_buy_volume_sol' in df.columns and 'whale_sell_volume_sol' in df.columns and 'volume_sol' in df.columns:
                    df['whale_dominance'] = (
                        (df['whale_buy_volume_sol'].fillna(0) + df['whale_sell_volume_sol'].fillna(0)) / 
                        (df['volume_sol'] + 0.001)
                    ).fillna(0)
                    calculated_features.append(feature)
                    logger.debug(f"✅ Berechnet: {feature}")
                else:
                    logger.warning(f"⚠️ Kann {feature} nicht berechnen - fehlende Basis-Features")
                    df[feature] = 0.0
                    calculated_features.append(feature)
                continue

            # Marktstimmung Features (Placeholder)
            if feature in ['sol_price_usd', 'sol_price_ma_5']:
                df[feature] = 150.0
                calculated_features.append(feature)

            elif feature in ['sol_price_change_pct', 'sol_price_volatility']:
                df[feature] = 0.0
                calculated_features.append(feature)

            # Alle anderen Features: 0.0
            else:
                df[feature] = 0.0
                calculated_features.append(feature)

        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Setzen von {feature}: {e}")
            df[feature] = 0.0

    if calculated_features:
        logger.info(f"✅ Fallback-Features gesetzt: {len(calculated_features)} Features")

    # NaN-Werte behandeln
    df.fillna(0, inplace=True)
    df.replace([np.inf, -np.inf], 0, inplace=True)

    return df
