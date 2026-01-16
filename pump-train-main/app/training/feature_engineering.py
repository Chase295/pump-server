"""
Feature Engineering für ML Training Service
============================================

Lädt Daten aus coin_metrics und erstellt Labels für ML-Training.
Generiert Engineering-Features für Pump-Detection.

Autor: ML Training Service Team
Version: 2.0.0 (Vollständig repariert)
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.database.connection import get_pool

logger = logging.getLogger(__name__)

# ⚠️ RAM-Management: Max Anzahl Zeilen
MAX_TRAINING_ROWS = 100000  # 100k Zeilen für stabiles Training

# ============================================================================
# VERFÜGBARE BASIS-FEATURES (29 Spalten in coin_metrics)
# ============================================================================
BASE_FEATURES = [
    'price_open', 'price_high', 'price_low', 'price_close',
    'market_cap_close', 'bonding_curve_pct', 'virtual_sol_reserves', 'is_koth',
    'volume_sol', 'buy_volume_sol', 'sell_volume_sol', 'net_volume_sol',
    'num_buys', 'num_sells', 'unique_wallets', 'num_micro_trades',
    'max_single_buy_sol', 'max_single_sell_sol',
    'whale_buy_volume_sol', 'whale_sell_volume_sol', 'num_whale_buys', 'num_whale_sells',
    'dev_sold_amount', 'volatility_pct', 'avg_trade_size_sol',
    'buy_pressure_ratio', 'unique_signer_ratio', 'phase_id_at_time'
]

# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def _ensure_utc(dt: str | datetime) -> datetime:
    """Konvertiert datetime zu UTC (tz-aware)."""
    if isinstance(dt, str):
        dt = dt.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    return dt


# ============================================================================
# HAUPTFUNKTION: DATEN LADEN
# ============================================================================

async def load_training_data(
    train_start: str | datetime,
    train_end: str | datetime,
    features: List[str],
    phases: Optional[List[int]] = None,
    include_ath: bool = True,
    include_flags: bool = True  # NEU: Flag-Features aktivieren/deaktivieren
) -> pd.DataFrame:
    """
    Lädt Trainingsdaten aus coin_metrics mit ALLEN angeforderten Features.
    
    Args:
        train_start: Start-Zeitpunkt (ISO-String oder datetime)
        train_end: End-Zeitpunkt (ISO-String oder datetime)
        features: Liste der gewünschten Features
        phases: Optional - Nur bestimmte Coin-Phasen laden
        include_ath: Engineering-Features generieren (default: True)
                    ⚠️ WICHTIG: Dieser Parameter steuert auch die Generierung von Engineering-Features!
                    Wenn use_engineered_features=True ist, muss include_ath=True sein!
    
    Returns:
        DataFrame mit allen angeforderten Features
    """
    pool = await get_pool()
    
    # Parameter zu datetime konvertieren
    if isinstance(train_start, str):
        train_start = datetime.fromisoformat(train_start.replace('Z', '+00:00'))
    if isinstance(train_end, str):
        train_end = datetime.fromisoformat(train_end.replace('Z', '+00:00'))
    
    logger.info(f"📊 Lade Daten: {train_start} bis {train_end}")
    logger.info(f"📊 Angeforderte Features: {features}")
    
    # ============================================
    # DYNAMISCHE SPALTEN-SELEKTION
    # ============================================
    # Immer benötigte Spalten
    required_columns = {'timestamp', 'mint'}
    
    # Füge alle angeforderten Features hinzu (wenn sie in DB existieren)
    requested_columns = set()
    for feature in features:
        if feature in BASE_FEATURES:
            requested_columns.add(feature)
        elif feature == 'timestamp':
            continue  # Bereits in required
        else:
            logger.warning(f"⚠️ Feature '{feature}' nicht in Basis-Features, wird übersprungen")
    

    # ⚠️ WICHTIG: Wenn Engineering-Features aktiviert sind, lade ALLE benötigten Basis-Spalten!
    # Engineering-Features benötigen viele Basis-Spalten, die möglicherweise nicht in der Anfrage stehen
    if include_ath:
        # Liste aller Basis-Spalten, die für Engineering-Features benötigt werden
        required_for_engineering = {
            'price_close', 'volume_sol',  # Immer benötigt
            'dev_sold_amount',  # Für dev_sold_spike
            'unique_signer_ratio',  # Für wash_trading_flag
            'whale_buy_volume_sol', 'whale_sell_volume_sol',  # Für whale_activity
            'volatility_pct',  # Für volatility_spike/ma
            'net_volume_sol',  # Für net_volume_ma, volume_flip
            'market_cap_close',  # Für mcap_velocity
            'buy_pressure_ratio',  # Für buy_pressure Features
            'num_buys', 'num_sells',  # Für buy_sell_ratio
        }
        logger.info(f"🔧 Engineering aktiviert - lade zusätzliche Basis-Spalten: {required_for_engineering}")
        requested_columns.update(required_for_engineering)

    # Kombiniere alle Spalten
    all_columns = required_columns | requested_columns
    
    # Stelle sicher, dass mindestens price_close und volume_sol dabei sind
    all_columns.add('price_close')
    all_columns.add('volume_sol')
    
    # Baue SELECT-Klausel
    columns_list = sorted(list(all_columns))
    columns_str = ', '.join([f'cm.{col}' for col in columns_list])
    
    logger.info(f"📊 Lade Spalten: {columns_list}")
    
    # ============================================
    # QUERY BAUEN
    # ============================================
    if phases:
        query = f"""
        SELECT {columns_str}
            FROM coin_metrics cm
        WHERE cm.timestamp >= $1 
          AND cm.timestamp <= $2
          AND cm.phase_id_at_time = ANY($3)
            ORDER BY cm.timestamp
        LIMIT {MAX_TRAINING_ROWS}
        """
        params = [train_start, train_end, phases]
    else:
        query = f"""
        SELECT {columns_str}
            FROM coin_metrics cm
        WHERE cm.timestamp >= $1 
          AND cm.timestamp <= $2
            ORDER BY cm.timestamp
        LIMIT {MAX_TRAINING_ROWS}
        """
        params = [train_start, train_end]
    
    # ============================================
    # DATEN LADEN
    # ============================================
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        if not rows:
            logger.warning("⚠️ Keine Daten im angegebenen Zeitraum gefunden!")
            return pd.DataFrame()
        
        data = pd.DataFrame([dict(row) for row in rows])
        logger.info(f"✅ {len(data)} Zeilen geladen, {len(data.columns)} Spalten")
        
        # ✅ FIX: Konvertiere Decimal zu float (verhindert Typfehler in Berechnungen)
        from decimal import Decimal
        for col in data.columns:
            if data[col].dtype == object:
                # Prüfe ob erste Nicht-Null-Wert ein Decimal ist
                first_val = data[col].dropna().iloc[0] if len(data[col].dropna()) > 0 else None
                if isinstance(first_val, Decimal):
                    data[col] = data[col].astype(float)
        
        # Timestamp als datetime
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        # ============================================
        # ENGINEERING FEATURES GENERIEREN
        # ============================================
        # ⚠️ WICHTIG: include_ath steuert nicht nur ATH-Daten, sondern auch Engineering-Features!
        # Wenn use_engineered_features=True ist, muss include_ath=True sein!
        if include_ath and len(data) > 0:
            logger.info("🔧 Generiere Engineering Features...")
            data = add_pump_detection_features(data, include_flags=include_flags)
            logger.info(f"✅ {len(data.columns)} Spalten nach Engineering")
        
        return data
        
    except Exception as e:
        logger.error(f"❌ Fehler in load_training_data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


# ============================================================================
# LABEL-ERSTELLUNG
# ============================================================================

def create_time_based_labels(
    data: pd.DataFrame,
    target_var: str, 
    future_minutes: int,
    min_percent_change: float,
    direction: str,
    phase_intervals: Optional[List[Dict]] = None
) -> pd.Series:
    """
    Erstellt zeitbasierte Labels für Klassifikation.
    
    Logik: Prüft ob der Preis innerhalb von X Minuten um Y% steigt/fällt.
    
    Args:
        data: DataFrame mit Preis-Daten
        target_var: Ziel-Variable (z.B. 'price_close')
        future_minutes: Vorhersage-Horizont in Minuten
        min_percent_change: Minimum Preisänderung in %
        direction: 'up' für Pump-Detection, 'down' für Rug-Detection
        phase_intervals: Optional - Phasen-Intervalle für zeitbasierte Vorhersage
    
    Returns:
        Series mit Labels (1 = Ereignis tritt ein, 0 = nicht)
    """
    if target_var not in data.columns:
        logger.warning(f"⚠️ target_var '{target_var}' nicht in Daten, verwende price_close")
        target_var = 'price_close'
    
    if target_var not in data.columns:
        logger.error(f"❌ Weder '{target_var}' noch 'price_close' in Daten!")
        return pd.Series([0] * len(data), index=data.index)
    
    # ✅ KRITISCH: Sortiere nach Coin und Timestamp für korrekte Berechnung
    if 'mint' in data.columns and 'timestamp' in data.columns:
        # Sortiere nach Coin und Zeit
        data_sorted = data.sort_values(['mint', 'timestamp']).copy()
        original_index = data.index
        
        # Berechne zukünftigen Preis PRO COIN (groupby shift)
        future_price = data_sorted.groupby('mint')[target_var].shift(-future_minutes)
        current_price = data_sorted[target_var]
        
        logger.info(f"✅ Label-Berechnung: Gruppiert nach {data_sorted['mint'].nunique()} Coins")
    else:
        # Fallback: Keine Gruppierung (einzelner Coin oder keine mint-Spalte)
        data_sorted = data.copy()
        original_index = data.index
        future_price = data_sorted[target_var].shift(-future_minutes)
        current_price = data_sorted[target_var]
        logger.warning("⚠️ Keine 'mint' Spalte - Labels ohne Coin-Gruppierung berechnet")
    
    # Berechne prozentuale Änderung
    percent_change = ((future_price - current_price) / current_price) * 100
    
    # Erstelle Labels basierend auf Richtung
    if direction == 'up':
        labels = (percent_change >= min_percent_change).astype(int)
    else:
        labels = (percent_change <= -min_percent_change).astype(int)
    
    # Ersetze NaN (durch shift entstanden) mit 0
    labels = labels.fillna(0).astype(int)
    
    # ✅ Stelle ursprüngliche Reihenfolge wieder her
    if 'mint' in data.columns:
        labels = labels.reindex(original_index)
    
    positive_count = labels.sum()
    negative_count = len(labels) - positive_count
    
    logger.info(f"📊 Labels erstellt: {positive_count} positive, {negative_count} negative")
    logger.info(f"   Ratio: {positive_count / len(labels) * 100:.2f}% positive")
    
    return labels


def create_rule_based_labels(
    data: pd.DataFrame,
    target_var: str,
    operator: str,
    target_value: float
) -> pd.Series:
    """
    Erstellt regelbasierte Labels.

    Args:
        data: DataFrame
        target_var: Ziel-Variable
        operator: Vergleichsoperator ('>', '<', '>=', '<=', '=')
        target_value: Schwellwert

    Returns:
        Series mit Labels
    """
    if target_var not in data.columns:
        logger.error(f"❌ target_var '{target_var}' nicht in Daten!")
        return pd.Series([0] * len(data), index=data.index)
    
    col = data[target_var]
    
    if operator == '>':
        labels = (col > target_value).astype(int)
    elif operator == '<':
        labels = (col < target_value).astype(int)
    elif operator == '>=':
        labels = (col >= target_value).astype(int)
    elif operator == '<=':
        labels = (col <= target_value).astype(int)
    elif operator == '=':
        labels = (col == target_value).astype(int)
    else:
        logger.error(f"❌ Ungültiger Operator: {operator}")
        labels = pd.Series([0] * len(data), index=data.index)
    
    return labels


# Alias für Kompatibilität
create_labels = create_time_based_labels


# ============================================================================
# ENGINEERING FEATURES
# ============================================================================

def add_pump_detection_features(
    data: pd.DataFrame,
    window_sizes: List[int] = [5, 10, 15],
    include_flags: bool = True  # NEU: Flag-Features aktivieren/deaktivieren
) -> pd.DataFrame:
    """
    Fügt alle Engineering-Features für Pump-Detection hinzu.
    
    Generiert Features basierend auf:
    - Dev-Sold Analyse
    - Buy Pressure Trends
    - Whale Activity
    - Volatilität
    - Volume Patterns
    - Price Momentum
    - Market Cap Velocity
    
    NEU: Wenn include_flags=True, werden zusätzliche Flag-Features erstellt,
    die anzeigen, ob ein Feature genug Daten hat.
    
    Args:
        data: DataFrame mit Basis-Features
        window_sizes: Liste der Fenstergrößen (Default: [5, 10, 15])
        include_flags: Flag-Features aktivieren? (Default: True)
    
    Returns:
        DataFrame mit zusätzlichen Engineering-Features (und optional Flag-Features)
    """
    if len(data) == 0:
        return data
    
    df = data.copy()
    
    logger.info(f"🔧 Generiere Engineering Features für {len(df)} Zeilen...")
    
    # NEU: Berechne Coin-Age (wird für Flags benötigt)
    if 'mint' in df.columns and 'timestamp' in df.columns:
        df = df.sort_values(['mint', 'timestamp']).reset_index(drop=True)
        df['coin_age_minutes'] = df.groupby('mint')['timestamp'].transform(
            lambda x: (x - x.min()).dt.total_seconds() / 60
        )
    elif 'timestamp' in df.columns:
        # Fallback: Verwende Zeilen-Index als Proxy (wenn kein mint vorhanden)
        df = df.sort_values('timestamp').reset_index(drop=True)
        df['coin_age_minutes'] = df.groupby(df.index).cumcount()
        logger.warning("⚠️ Keine 'mint' Spalte - verwende Index als Coin-Age Proxy")
    else:
        # Fallback: Verwende Zeilen-Index
        df['coin_age_minutes'] = df.groupby(df.index).cumcount()
        logger.warning("⚠️ Keine 'mint' oder 'timestamp' Spalte - verwende Index als Coin-Age Proxy")
    
    # ============================================
    # 1. DEV-SOLD FEATURES
    # ============================================
    if 'dev_sold_amount' in df.columns:
        # Flag: Hat Dev verkauft?
        df['dev_sold_flag'] = (df['dev_sold_amount'] > 0).astype(int)
        
        # Kumulierte Dev-Verkäufe
        df['dev_sold_cumsum'] = df['dev_sold_amount'].cumsum()
        
        # Dev-Sold Spikes (plötzliche Verkäufe)
        for window in window_sizes:
            df[f'dev_sold_spike_{window}'] = (
                df['dev_sold_amount'] > df['dev_sold_amount'].rolling(window).mean() * 2
            ).astype(int)
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'dev_sold_spike_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN nur wenn nicht genug Daten (wird später im Training behandelt)
            # Für jetzt: Fülle mit 0 für Rückwärtskompatibilität
            df[f'dev_sold_spike_{window}'] = df[f'dev_sold_spike_{window}'].fillna(0)
    
    # ============================================
    # 2. BUY PRESSURE FEATURES
    # ============================================
    if 'buy_pressure_ratio' in df.columns:
        for window in window_sizes:
            # Moving Average (NICHT sofort füllen - wird später behandelt)
            df[f'buy_pressure_ma_{window}'] = df['buy_pressure_ratio'].rolling(window).mean()
            
            # Trend (Differenz zum MA)
            df[f'buy_pressure_trend_{window}'] = (
                df['buy_pressure_ratio'] - df[f'buy_pressure_ma_{window}']
            )
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'buy_pressure_ma_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
                df[f'buy_pressure_trend_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität (wird später im Training überschrieben)
            df[f'buy_pressure_ma_{window}'] = df[f'buy_pressure_ma_{window}'].fillna(0)
            df[f'buy_pressure_trend_{window}'] = df[f'buy_pressure_trend_{window}'].fillna(0)
    
    # ============================================
    # 3. WHALE ACTIVITY FEATURES
    # ============================================
    if 'whale_buy_volume_sol' in df.columns and 'whale_sell_volume_sol' in df.columns:
        # Netto Whale Volumen
        df['whale_net_volume'] = df['whale_buy_volume_sol'] - df['whale_sell_volume_sol']
        
        for window in window_sizes:
            # Whale Aktivität (absolutes Volumen)
            df[f'whale_activity_{window}'] = (
                df['whale_buy_volume_sol'].rolling(window).sum() +
                df['whale_sell_volume_sol'].rolling(window).sum()
            )
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'whale_activity_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'whale_activity_{window}'] = df[f'whale_activity_{window}'].fillna(0)
    
    # ============================================
    # 4. VOLATILITY FEATURES
    # ============================================
    if 'volatility_pct' in df.columns:
        for window in window_sizes:
            # Moving Average Volatilität
            df[f'volatility_ma_{window}'] = df['volatility_pct'].rolling(window).mean()
            
            # Volatilitäts-Spike
            df[f'volatility_spike_{window}'] = (
                df['volatility_pct'] > df[f'volatility_ma_{window}'] * 1.5
            ).astype(int)
    
            # NEU: Flag-Feature
            if include_flags:
                df[f'volatility_ma_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
                df[f'volatility_spike_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'volatility_ma_{window}'] = df[f'volatility_ma_{window}'].fillna(0)
            df[f'volatility_spike_{window}'] = df[f'volatility_spike_{window}'].fillna(0)
    
    # ============================================
    # 5. WASH TRADING DETECTION
    # ============================================
    if 'unique_signer_ratio' in df.columns:
        for window in window_sizes:
            # Niedrige Unique Signer = mögliches Wash Trading
            df[f'wash_trading_flag_{window}'] = (
                df['unique_signer_ratio'].rolling(window).mean() < 0.3
            ).astype(int)
    
            # NEU: Flag-Feature
            if include_flags:
                df[f'wash_trading_flag_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'wash_trading_flag_{window}'] = df[f'wash_trading_flag_{window}'].fillna(0)
    
    # ============================================
    # 6. VOLUME PATTERN FEATURES
    # ============================================
    if 'net_volume_sol' in df.columns:
        for window in window_sizes:
            # Net Volume Moving Average
            df[f'net_volume_ma_{window}'] = df['net_volume_sol'].rolling(window).mean()
            
            # Volume Flip (Vorzeichenwechsel)
            df[f'volume_flip_{window}'] = (
                np.sign(df['net_volume_sol']) != np.sign(df['net_volume_sol'].shift(window))
            ).astype(int)
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'net_volume_ma_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
                df[f'volume_flip_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'net_volume_ma_{window}'] = df[f'net_volume_ma_{window}'].fillna(0)
            df[f'volume_flip_{window}'] = df[f'volume_flip_{window}'].fillna(0)
    
    # ============================================
    # 7. PRICE MOMENTUM FEATURES
    # ============================================
    if 'price_close' in df.columns:
        for window in window_sizes:
            # Absolute Preisänderung
            df[f'price_change_{window}'] = df['price_close'].diff(window)
            
            # Rate of Change (ROC)
            df[f'price_roc_{window}'] = (
                (df['price_close'] - df['price_close'].shift(window)) / 
                df['price_close'].shift(window) * 100
            )
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'price_change_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
                df[f'price_roc_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'price_change_{window}'] = df[f'price_change_{window}'].fillna(0)
            df[f'price_roc_{window}'] = df[f'price_roc_{window}'].fillna(0)
    
    # ============================================
    # 8. MARKET CAP VELOCITY
    # ============================================
    if 'market_cap_close' in df.columns:
        for window in window_sizes:
            df[f'mcap_velocity_{window}'] = df['market_cap_close'].diff(window)
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'mcap_velocity_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'mcap_velocity_{window}'] = df[f'mcap_velocity_{window}'].fillna(0)
    
    # ============================================
    # 9. ATH (ALL-TIME-HIGH) FEATURES ⭐ KRITISCH FÜR PUMP DETECTION
    # ============================================
    if 'price_close' in df.columns:
        # ✅ KRITISCH: ATH muss PRO COIN berechnet werden!
        if 'mint' in df.columns:
            # Sortiere nach Coin und Zeit für korrekte Berechnung
            df = df.sort_values(['mint', 'timestamp']).reset_index(drop=True)
            
            # Rolling ATH pro Coin (höchster Preis bis zu diesem Zeitpunkt)
            df['rolling_ath'] = df.groupby('mint')['price_close'].transform(
                lambda x: x.expanding().max()
            )
            
            logger.info(f"✅ ATH berechnet für {df['mint'].nunique()} Coins")
        else:
            # Fallback: Globale Berechnung
            df['rolling_ath'] = df['price_close'].expanding().max()
            logger.warning("⚠️ Keine 'mint' Spalte - ATH global berechnet")
        
        # Distanz zum ATH in Prozent
        df['price_vs_ath_pct'] = ((df['price_close'] - df['rolling_ath']) / df['rolling_ath'] * 100).fillna(0)
        
        # ATH-Breakout Flag (neues ATH erreicht)
        df['ath_breakout'] = (df['price_close'] >= df['rolling_ath'] * 0.999).astype(int)  # 0.1% Toleranz
        
        # Minuten seit letztem ATH (vereinfachte Berechnung)
        df['minutes_since_ath'] = 0
        if 'mint' in df.columns:
            for mint in df['mint'].unique():
                mask = df['mint'] == mint
                coin_data = df.loc[mask, 'price_close'].values
                rolling_ath = df.loc[mask, 'rolling_ath'].values
                
                minutes_since = []
                last_ath_idx = 0
                for i in range(len(coin_data)):
                    if coin_data[i] >= rolling_ath[i] * 0.999:  # Neues ATH
                        last_ath_idx = i
                    minutes_since.append(i - last_ath_idx)
                
                df.loc[mask, 'minutes_since_ath'] = minutes_since
        
        for window in window_sizes:
            # ATH-Distanz Trend (wird der Abstand zum ATH kleiner?)
            df[f'ath_distance_trend_{window}'] = df['price_vs_ath_pct'].diff(window)
            
            # ATH-Approach Flag (nähert sich dem ATH)
            df[f'ath_approach_{window}'] = (df[f'ath_distance_trend_{window}'] > 0).astype(int)
            
            # ATH-Breakout Count (wie oft wurde ATH in den letzten X Minuten durchbrochen)
            df[f'ath_breakout_count_{window}'] = df['ath_breakout'].rolling(window).sum()
            
            # Volumen bei ATH-Breakouts
            if 'volume_sol' in df.columns:
                breakout_volume = df['volume_sol'] * df['ath_breakout']
                df[f'ath_breakout_volume_ma_{window}'] = breakout_volume.rolling(window).mean()
            
            # ATH-Alter Trend (wird das ATH älter oder neuer?)
            df[f'ath_age_trend_{window}'] = df['minutes_since_ath'].diff(window)
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'ath_distance_trend_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
            ).astype(int)
                df[f'ath_approach_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
                df[f'ath_breakout_count_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
                if 'volume_sol' in df.columns:
                    df[f'ath_breakout_volume_ma_{window}_has_data'] = (
                        df['coin_age_minutes'] >= window
                    ).astype(int)
                df[f'ath_age_trend_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'ath_distance_trend_{window}'] = df[f'ath_distance_trend_{window}'].fillna(0)
            df[f'ath_breakout_count_{window}'] = df[f'ath_breakout_count_{window}'].fillna(0)
            if 'volume_sol' in df.columns:
                df[f'ath_breakout_volume_ma_{window}'] = df[f'ath_breakout_volume_ma_{window}'].fillna(0)
            df[f'ath_age_trend_{window}'] = df[f'ath_age_trend_{window}'].fillna(0)
        
        # Cleanup temporäre Spalten
        df = df.drop(columns=['ath_timestamp'], errors='ignore')
    
    # ============================================
    # 10. ZUSÄTZLICHE POWER-FEATURES
    # ============================================
    
    # Buy/Sell Ratio (wichtig für Sentiment)
    if 'num_buys' in df.columns and 'num_sells' in df.columns:
        df['buy_sell_ratio'] = (df['num_buys'] / (df['num_sells'] + 1)).fillna(1)
    
    # Whale Dominanz (Anteil Whale-Volume am Gesamtvolumen)
    if 'whale_buy_volume_sol' in df.columns and 'volume_sol' in df.columns:
        df['whale_dominance'] = ((df['whale_buy_volume_sol'] + df.get('whale_sell_volume_sol', 0)) / (df['volume_sol'] + 0.001)).fillna(0)
    
    # Price Acceleration (Beschleunigung der Preisänderung)
    if 'price_close' in df.columns:
        for window in window_sizes:
            price_change = df['price_close'].diff(window)
            df[f'price_acceleration_{window}'] = price_change.diff(window)
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'price_acceleration_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'price_acceleration_{window}'] = df[f'price_acceleration_{window}'].fillna(0)
    
    # Volume Spike Detection
    if 'volume_sol' in df.columns:
        for window in window_sizes:
            vol_ma = df['volume_sol'].rolling(window * 2).mean()
            df[f'volume_spike_{window}'] = (df['volume_sol'] > vol_ma * 2).astype(int)
            
            # NEU: Flag-Feature (Volume Spike braucht window*2 Daten)
            if include_flags:
                df[f'volume_spike_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window * 2
                ).astype(int)
            
            # Fülle NaN für Rückwärtskompatibilität
            df[f'volume_spike_{window}'] = df[f'volume_spike_{window}'].fillna(0)
    
    # Entferne temporäre Spalten
    df = df.drop(columns=['coin_age_minutes'], errors='ignore')
    
    logger.info(f"✅ Engineering Features generiert: {len(df.columns)} Spalten total")
    if include_flags:
        flag_count = sum(1 for col in df.columns if col.endswith('_has_data'))
        logger.info(f"🚩 Flag-Features erstellt: {flag_count} Flags")
    
    return df


def create_pump_detection_features(
    data: pd.DataFrame, 
    window_sizes: List[int] = [5, 10, 15],
    include_flags: bool = True  # NEU: Flag-Features aktivieren/deaktivieren
) -> pd.DataFrame:
    """
    Erstellt Pump-Detection Features mit konfigurierbaren Fenstergrößen.

    Args:
        data: DataFrame mit Basis-Features
        window_sizes: Liste der Fenstergrößen für Rolling-Berechnungen (Default: [5, 10, 15])

    Returns:
        DataFrame mit Engineering-Features
    """
    return add_pump_detection_features(data, window_sizes=window_sizes, include_flags=include_flags)


# ============================================================================
# VALIDIERUNGS-FUNKTIONEN
# ============================================================================

def validate_critical_features(features: list) -> dict:
    """
    Prüft ob kritische Features in der Feature-Liste vorhanden sind.
    
    Args:
        features: Liste der angeforderten Features
    
    Returns:
        Dictionary mit Feature-Name -> True/False (vorhanden/nicht vorhanden)
    """
    critical_features = [
        'dev_sold_amount',
        'buy_pressure_ratio',
        'unique_signer_ratio',
        'whale_buy_volume_sol',
        'whale_sell_volume_sol',
        'volatility_pct',
        'avg_trade_size_sol',
    ]
    
    result = {}
    for feature in critical_features:
        result[feature] = feature in features
    
    return result


async def validate_ath_data_availability(
    train_start: datetime | str,
    train_end: datetime | str
) -> Dict[str, Any]:
    """
    Prüft ob ATH-Daten für den Zeitraum verfügbar sind.
    
    Args:
        train_start: Start-Zeitpunkt
        train_end: Ende-Zeitpunkt
    
    Returns:
        Dict mit:
        - available: bool
        - coins_with_ath: int
        - coins_without_ath: int
        - coverage_pct: float
        - total_coins: int
    """
    pool = await get_pool()
    
    # Konvertiere zu UTC
    train_start_utc = _ensure_utc(train_start)
    train_end_utc = _ensure_utc(train_end)
    
    # Prüfe wie viele Coins ATH-Daten haben
    query = """
        SELECT 
            COUNT(DISTINCT cm.mint) as total_coins,
            COUNT(DISTINCT CASE WHEN COALESCE(cs.ath_price_sol, 0) > 0 THEN cm.mint END) as coins_with_ath,
            COUNT(DISTINCT CASE WHEN COALESCE(cs.ath_price_sol, 0) = 0 OR cs.ath_price_sol IS NULL THEN cm.mint END) as coins_without_ath
        FROM coin_metrics cm
        LEFT JOIN coin_streams cs ON cm.mint = cs.token_address
        WHERE cm.timestamp >= $1 AND cm.timestamp <= $2
    """
    
    try:
        row = await pool.fetchrow(query, train_start_utc, train_end_utc)
        
        total_coins = row['total_coins'] or 0
        coins_with_ath = row['coins_with_ath'] or 0
        coins_without_ath = row['coins_without_ath'] or 0
        
        coverage_pct = (coins_with_ath / total_coins * 100) if total_coins > 0 else 0.0
        
        return {
            "available": coins_with_ath > 0,
            "coins_with_ath": coins_with_ath,
            "coins_without_ath": coins_without_ath,
            "coverage_pct": coverage_pct,
            "total_coins": total_coins
        }
    except Exception as e:
        logger.warning(f"⚠️ Fehler bei ATH-Daten-Validierung: {e}")
        return {
            "available": False,
            "coins_with_ath": 0,
            "coins_without_ath": 0,
            "coverage_pct": 0.0,
            "total_coins": 0,
            "error": str(e)
        }


def check_overlap(
    train_start: datetime, 
    train_end: datetime, 
    test_start: datetime, 
    test_end: datetime
) -> dict:
    """
    Prüft ob Trainings- und Testzeiträume überlappen.
    
    Returns:
        Dict mit:
        - has_overlap: Boolean
        - overlap_days: Anzahl überlappender Tage (0 wenn kein Overlap)
        - overlap_note: Beschreibung des Overlaps (für DB-Speicherung)
    """
    has_overlap = not (train_end <= test_start or test_end <= train_start)
    
    overlap_days = 0.0
    overlap_note = "✅ Keine Überschneidung mit Trainingsdaten"
    
    if has_overlap:
        # Berechne Overlap
        overlap_start = max(train_start, test_start)
        overlap_end = min(train_end, test_end)
        overlap_duration = overlap_end - overlap_start
        overlap_days = overlap_duration.total_seconds() / 86400.0  # In Tagen
        
        # Berechne Overlap-Prozent (bezogen auf Test-Zeitraum)
        test_duration = test_end - test_start
        overlap_percent = (overlap_duration.total_seconds() / test_duration.total_seconds()) * 100 if test_duration.total_seconds() > 0 else 0
        
        overlap_note = f"⚠️ {overlap_percent:.1f}% Überschneidung mit Trainingsdaten - Ergebnisse können verfälscht sein"
    
    return {
        "has_overlap": has_overlap,
        "overlap_days": overlap_days,
        "overlap_note": overlap_note
    }


# ============================================================================
# MARKET CONTEXT (Stub für zukünftige Erweiterung)
# ============================================================================

async def enrich_with_market_context(data: pd.DataFrame) -> pd.DataFrame:
    """
    Reichert DataFrame mit Marktkontext an.
    
    Stub-Funktion für zukünftige Erweiterung:
    - SOL-Preis
    - BTC-Trend
    - Gesamt-Markt-Sentiment
    
    Args:
        data: DataFrame
    
    Returns:
        DataFrame (aktuell unverändert)
    """
    # TODO: Implementiere Markt-Kontext
    return data


# ============================================================================
# FEATURE NAMEN GENERATOR
# ============================================================================

def get_engineered_feature_names(window_sizes: List[int] = [5, 10, 15]) -> List[str]:
    """
    Generiert Liste aller Engineering-Feature-Namen.
    
    Args:
        window_sizes: Liste der Fenstergrößen
    
    Returns:
        Liste aller generierten Feature-Namen
    """
    features = []
    
    for window in window_sizes:
        # Dev-Sold Features
        features.append(f'dev_sold_spike_{window}')
        
        # Buy Pressure Features
        features.extend([
            f'buy_pressure_ma_{window}',
            f'buy_pressure_trend_{window}',
        ])
        
        # Whale Activity Features
        features.append(f'whale_activity_{window}')
        
        # Volatility Features
        features.extend([
            f'volatility_ma_{window}',
            f'volatility_spike_{window}',
        ])
        
        # Wash Trading Features
        features.append(f'wash_trading_flag_{window}')
        
        # Volume Pattern Features
        features.extend([
            f'net_volume_ma_{window}',
            f'volume_flip_{window}',
        ])
        
        # Price Momentum Features
        features.extend([
            f'price_change_{window}',
            f'price_roc_{window}',
        ])
        
        # Market Cap Velocity Features
        features.append(f'mcap_velocity_{window}')
    
    # Basis Engineering Features (ohne Window)
    features.extend([
        'dev_sold_flag',
        'dev_sold_cumsum',
        'whale_net_volume',
    ])
    
    # ATH Features (ohne Window)
    features.extend([
        'rolling_ath',
        'price_vs_ath_pct',
        'ath_breakout',
        'minutes_since_ath',
    ])
    
    # ATH Features (mit Window)
    for window in window_sizes:
        features.extend([
            f'ath_distance_trend_{window}',
            f'ath_approach_{window}',
            f'ath_breakout_count_{window}',
            f'ath_breakout_volume_ma_{window}',
            f'ath_age_trend_{window}',
        ])
    
    # Zusätzliche Power-Features
    features.extend([
        'buy_sell_ratio',
        'whale_dominance',
    ])
    
    # Power Features mit Window
    for window in window_sizes:
        features.extend([
            f'price_acceleration_{window}',
            f'volume_spike_{window}',
        ])
    
    return features


def get_flag_feature_names(engineered_features: List[str]) -> List[str]:
    """
    Generiert eine Liste von Flag-Feature-Namen basierend auf den gegebenen Engineering-Features.
    Flag-Features werden für alle Features erstellt, die auf Rolling-Windows basieren.
    
    Args:
        engineered_features: Liste der Engineering-Feature-Namen
    
    Returns:
        Liste der Flag-Feature-Namen (z.B. ['dev_sold_spike_5_has_data', ...])
    """
    flag_features = []
    for ef in engineered_features:
        # Erkennung von window-basierten Features
        # Pattern: _ma_5, _spike_10, _trend_15, _count_5, _volume_ma_5, _age_trend_5, etc.
        if any(suffix in ef for suffix in ['_ma_', '_spike_', '_trend_', '_count_', '_volume_ma_', '_age_trend_', 
                                            '_velocity_', '_roc_', '_change_', '_flip_', '_activity_', '_approach_', 
                                            '_breakout_count_', '_breakout_volume_ma_', '_distance_trend_']):
            flag_features.append(f'{ef}_has_data')
    return sorted(list(set(flag_features)))  # Entferne Duplikate und sortiere


def get_all_available_features() -> Dict[str, List[str]]:
    """
    Gibt alle verfügbaren Features zurück, kategorisiert.
    
    Returns:
        Dictionary mit Kategorien und deren Features
    """
    return {
        'base': BASE_FEATURES,
        'engineered': get_engineered_feature_names(),
        'total_count': len(BASE_FEATURES) + len(get_engineered_feature_names())
    }
