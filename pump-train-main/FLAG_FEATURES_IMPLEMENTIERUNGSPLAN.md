# 🚩 Flag-Features Implementierungsplan - Schritt für Schritt

**Ziel:** Komplette Integration von Flag-Features in das ML-Training-System  
**Status:** Detaillierter Plan für 100% funktionierende Implementierung  
**Datum:** 2026-01-08

---

## 📋 Übersicht

Dieser Plan führt dich durch die komplette Implementierung von Flag-Features, sodass:
- ✅ Backend Flag-Features korrekt generiert
- ✅ API alle Features (inkl. Flags) zurückgibt
- ✅ UI Flag-Features anzeigt
- ✅ Modelle mit Flag-Features trainiert werden können
- ✅ Bestehende Funktionalität bleibt erhalten

---

## 🎯 Phase 1: Backend - Feature Engineering erweitern

### Schritt 1.1: Feature Engineering Funktion erweitern

**Datei:** `app/training/feature_engineering.py`  
**Funktion:** `add_pump_detection_features()`

**Änderungen:**

```python
def add_pump_detection_features(
    data: pd.DataFrame, 
    window_sizes: List[int] = [5, 10, 15],
    include_flags: bool = True  # NEU: Flag-Features aktivieren/deaktivieren
) -> pd.DataFrame:
    """
    Fügt alle Engineering-Features für Pump-Detection hinzu.
    
    NEU: Wenn include_flags=True, werden zusätzliche Flag-Features erstellt,
    die anzeigen, ob ein Feature genug Daten hat.
    """
    if len(data) == 0:
        return data
    
    df = data.copy()
    
    # Berechne Coin-Age (wird für Flags benötigt)
    if 'mint' in df.columns and 'timestamp' in df.columns:
        df = df.sort_values(['mint', 'timestamp']).reset_index(drop=True)
        df['coin_age_minutes'] = df.groupby('mint')['timestamp'].transform(
            lambda x: (x - x.min()).dt.total_seconds() / 60
        )
    else:
        # Fallback: Verwende Zeilen-Index als Proxy
        df['coin_age_minutes'] = df.groupby(df.index).cumcount()
        logger.warning("⚠️ Keine 'mint' oder 'timestamp' Spalte - verwende Index als Coin-Age")
    
    logger.info(f"🔧 Generiere Engineering Features für {len(df)} Zeilen...")
    
    # ============================================
    # 1. DEV-SOLD FEATURES
    # ============================================
    if 'dev_sold_amount' in df.columns:
        df['dev_sold_flag'] = (df['dev_sold_amount'] > 0).astype(int)
        df['dev_sold_cumsum'] = df['dev_sold_amount'].cumsum()
        
        for window in window_sizes:
            df[f'dev_sold_spike_{window}'] = (
                df['dev_sold_amount'] > df['dev_sold_amount'].rolling(window).mean() * 2
            ).astype(int).fillna(0)
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'dev_sold_spike_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
    
    # ============================================
    # 2. BUY PRESSURE FEATURES
    # ============================================
    if 'buy_pressure_ratio' in df.columns:
        for window in window_sizes:
            # Feature berechnen
            df[f'buy_pressure_ma_{window}'] = df['buy_pressure_ratio'].rolling(window).mean()
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
            
            # Fülle NaN nur wenn genug Daten vorhanden (für Random Forest)
            # XGBoost kann NaN, also lassen wir sie für XGBoost
            # Später im Training wird entschieden, ob gefüllt werden soll
    
    # ============================================
    # 3. WHALE ACTIVITY FEATURES
    # ============================================
    if 'whale_buy_volume_sol' in df.columns and 'whale_sell_volume_sol' in df.columns:
        df['whale_net_volume'] = df['whale_buy_volume_sol'] - df['whale_sell_volume_sol']
        
        for window in window_sizes:
            df[f'whale_activity_{window}'] = (
                df['whale_buy_volume_sol'].rolling(window).sum() +
                df['whale_sell_volume_sol'].rolling(window).sum()
            )
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'whale_activity_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
    
    # ============================================
    # 4. VOLATILITY FEATURES
    # ============================================
    if 'volatility_pct' in df.columns:
        for window in window_sizes:
            df[f'volatility_ma_{window}'] = df['volatility_pct'].rolling(window).mean()
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
    
    # ============================================
    # 5. WASH TRADING DETECTION
    # ============================================
    if 'unique_signer_ratio' in df.columns:
        for window in window_sizes:
            df[f'wash_trading_flag_{window}'] = (
                df['unique_signer_ratio'].rolling(window).mean() < 0.3
            ).astype(int)
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'wash_trading_flag_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
    
    # ============================================
    # 6. VOLUME PATTERN FEATURES
    # ============================================
    if 'net_volume_sol' in df.columns:
        for window in window_sizes:
            df[f'net_volume_ma_{window}'] = df['net_volume_sol'].rolling(window).mean()
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
    
    # ============================================
    # 7. PRICE MOMENTUM FEATURES
    # ============================================
    if 'price_close' in df.columns:
        for window in window_sizes:
            df[f'price_change_{window}'] = df['price_close'].diff(window)
            df[f'price_roc_{window}'] = (
                (df['price_close'] - df['price_close'].shift(window)) / 
                df['price_close'].shift(window) * 100
            )
            df[f'price_acceleration_{window}'] = (
                df['price_close'].diff(window).diff(window)
            )
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'price_change_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
                df[f'price_roc_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
                df[f'price_acceleration_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window
                ).astype(int)
    
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
    
    # ============================================
    # 9. ATH FEATURES
    # ============================================
    # ATH-Features haben bereits eine Art "Flag" (ath_breakout), 
    # aber wir können auch has_data Flags hinzufügen
    if 'price_close' in df.columns:
        for window in window_sizes:
            # ATH-Distanz Trend
            df[f'ath_distance_trend_{window}'] = df['price_vs_ath_pct'].diff(window)
            df[f'ath_approach_{window}'] = (df[f'ath_distance_trend_{window}'] > 0).astype(int)
            df[f'ath_breakout_count_{window}'] = df['ath_breakout'].rolling(window).sum()
            
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
    
    # ============================================
    # 10. VOLUME SPIKE
    # ============================================
    if 'volume_sol' in df.columns:
        for window in window_sizes:
            vol_ma = df['volume_sol'].rolling(window * 2).mean()
            df[f'volume_spike_{window}'] = (df['volume_sol'] > vol_ma * 2).astype(int)
            
            # NEU: Flag-Feature
            if include_flags:
                df[f'volume_spike_{window}_has_data'] = (
                    df['coin_age_minutes'] >= window * 2
                ).astype(int)
    
    # Entferne temporäre Spalten
    df = df.drop(columns=['coin_age_minutes'], errors='ignore')
    
    logger.info(f"✅ Engineering Features generiert: {len(df.columns)} Spalten total")
    if include_flags:
        flag_count = sum(1 for col in df.columns if col.endswith('_has_data'))
        logger.info(f"🚩 Flag-Features erstellt: {flag_count} Flags")
    
    return df
```

**Wichtig:**
- `include_flags` Parameter hinzufügen (Standard: `True`)
- `coin_age_minutes` berechnen
- Für jedes Window-Feature ein `_has_data` Flag erstellen
- NaN-Werte NICHT sofort füllen (wird später im Training gemacht)

---

### Schritt 1.2: Training Engine anpassen

**Datei:** `app/training/engine.py`  
**Funktion:** `train_model_sync()`

**Änderungen:**

```python
def train_model_sync(
    data: pd.DataFrame,
    model_type: str,  # 'xgboost' oder 'random_forest'
    features: List[str],
    # ... andere Parameter ...
    use_flag_features: bool = True,  # NEU: Flag-Features verwenden?
) -> Dict[str, Any]:
    """
    Trainiert ein ML-Modell.
    
    NEU: Wenn use_flag_features=True, werden Flag-Features automatisch
    zu den Features hinzugefügt und NaN-Werte entsprechend behandelt.
    """
    
    # ... bestehender Code ...
    
    # Feature-Engineering
    if use_engineered_features:
        from app.training.feature_engineering import add_pump_detection_features
        
        # NEU: Flag-Features aktivieren
        data = add_pump_detection_features(
            data, 
            window_sizes=feature_engineering_windows,
            include_flags=use_flag_features  # NEU
        )
        
        # NEU: Flag-Features automatisch zu Features hinzufügen
        if use_flag_features:
            flag_features = [col for col in data.columns if col.endswith('_has_data')]
            # Füge Flag-Features zu features-Liste hinzu, wenn das entsprechende Feature auch drin ist
            for feature in features.copy():
                for window in feature_engineering_windows:
                    # Prüfe ob Feature ein Window-Feature ist
                    if f'_{window}' in feature or feature.endswith(f'_{window}'):
                        flag_name = f'{feature}_has_data'
                        if flag_name in flag_features and flag_name not in features:
                            features.append(flag_name)
                            logger.info(f"➕ Flag-Feature hinzugefügt: {flag_name}")
    
    # ... bestehender Code ...
    
    # NEU: NaN-Handling basierend auf Modell-Typ und Flag-Features
    if use_flag_features:
        # Für XGBoost: NaN bleibt NaN (wird ignoriert)
        # Für Random Forest: Fülle NaN mit 0, aber nur wenn has_data = 0
        if model_type == 'random_forest':
            # Fülle NaN nur wenn has_data Flag = 0 (nicht genug Daten)
            for col in data.columns:
                if col.endswith('_has_data'):
                    continue  # Überspringe Flag-Features selbst
                
                flag_col = f'{col}_has_data'
                if flag_col in data.columns:
                    # Wenn has_data = 0, dann fülle NaN mit 0
                    mask_no_data = data[flag_col] == 0
                    if mask_no_data.any():
                        data.loc[mask_no_data, col] = data.loc[mask_no_data, col].fillna(0)
                        logger.debug(f"🔧 NaN gefüllt für {col} wo has_data=0")
                else:
                    # Kein Flag vorhanden, fülle alle NaN mit 0 (Fallback)
                    data[col] = data[col].fillna(0)
        # Für XGBoost: NaN bleibt NaN (wird automatisch ignoriert)
    else:
        # Altes Verhalten: Alle NaN mit 0 füllen
        data = data.fillna(0)
    
    # ... Rest des Trainings ...
```

**Wichtig:**
- `use_flag_features` Parameter hinzufügen
- Flag-Features automatisch zu Features-Liste hinzufügen
- NaN-Handling basierend auf Modell-Typ und Flag-Features

---

### Schritt 1.3: Model Loader anpassen

**Datei:** `app/training/model_loader.py`  
**Funktion:** `test_model()`

**Änderungen:**

```python
async def test_model(
    model_id: int,
    test_start: str,
    test_end: str,
    model_storage_path: str = "/app/models"
) -> Dict[str, Any]:
    """
    Testet ein trainiertes Modell auf Test-Daten.
    
    NEU: Unterstützt Flag-Features automatisch.
    """
    
    # ... bestehender Code zum Laden des Modells ...
    
    # Feature-Engineering für Test-Daten
    if use_engineered_features:
        from app.training.feature_engineering import add_pump_detection_features
        
        # NEU: Flag-Features aktivieren (wie beim Training)
        test_data = add_pump_detection_features(
            test_data,
            window_sizes=feature_engineering_windows,
            include_flags=True  # NEU: Immer aktivieren wenn Modell sie hat
        )
        
        # NEU: Prüfe ob Modell Flag-Features erwartet
        model_features = set(features)
        flag_features_in_model = [f for f in model_features if f.endswith('_has_data')]
        
        if flag_features_in_model:
            logger.info(f"🚩 Modell erwartet {len(flag_features_in_model)} Flag-Features")
            # Stelle sicher, dass alle Flag-Features vorhanden sind
            for flag_feature in flag_features_in_model:
                if flag_feature not in test_data.columns:
                    # Erstelle Flag-Feature wenn fehlt
                    base_feature = flag_feature.replace('_has_data', '')
                    if base_feature in test_data.columns:
                        # Berechne Flag basierend auf Coin-Age
                        if 'coin_age_minutes' not in test_data.columns:
                            # Berechne Coin-Age
                            test_data['coin_age_minutes'] = test_data.groupby('mint')['timestamp'].transform(
                                lambda x: (x - x.min()).dt.total_seconds() / 60
                            )
                        # Extrahiere Window aus Feature-Name
                        window = int(flag_feature.split('_')[-2]) if flag_feature.split('_')[-2].isdigit() else 5
                        test_data[flag_feature] = (test_data['coin_age_minutes'] >= window).astype(int)
                        logger.info(f"➕ Flag-Feature erstellt: {flag_feature}")
        
        # NEU: NaN-Handling wie beim Training
        if model_type == 'random_forest':
            # Fülle NaN mit 0 wo has_data = 0
            for col in test_data.columns:
                if col.endswith('_has_data'):
                    continue
                flag_col = f'{col}_has_data'
                if flag_col in test_data.columns:
                    mask_no_data = test_data[flag_col] == 0
                    if mask_no_data.any():
                        test_data.loc[mask_no_data, col] = test_data.loc[mask_no_data, col].fillna(0)
        # Für XGBoost: NaN bleibt NaN
    
    # ... Rest des Tests ...
```

**Wichtig:**
- Flag-Features auch für Test-Daten generieren
- Prüfen ob Modell Flag-Features erwartet
- NaN-Handling wie beim Training

---

## 🎯 Phase 2: API - Endpoints erweitern

### Schritt 2.1: Features Endpoint erweitern

**Datei:** `app/api/routes.py`  
**Endpoint:** `GET /api/features`

**Änderungen:**

```python
@router.get("/features", response_model=FeaturesResponse)
async def get_features(include_flags: bool = True):  # NEU: Parameter
    """
    Gibt alle verfügbaren Features zurück.
    
    NEU: Wenn include_flags=True, werden auch Flag-Features zurückgegeben.
    """
    base_features = BASE_FEATURES  # 28 Features
    engineered_features = get_engineered_feature_names()  # 66 Features
    
    # NEU: Flag-Features hinzufügen
    flag_features = []
    if include_flags:
        for feature in engineered_features:
            # Prüfe ob Feature ein Window-Feature ist
            for window in [5, 10, 15]:
                if f'_{window}' in feature or feature.endswith(f'_{window}'):
                    flag_name = f'{feature}_has_data'
                    flag_features.append({
                        'id': flag_name,
                        'name': f'🚩 {feature} (Daten verfügbar)',
                        'description': f'Flag: Hat {feature} genug Daten? (1=ja, 0=nein)',
                        'category': 'flag',
                        'importance': 'optional',
                        'base_feature': feature
                    })
                    break
    
    return FeaturesResponse(
        base_features=base_features,
        engineered_features=engineered_features,
        flag_features=flag_features,  # NEU
        total_count=len(base_features) + len(engineered_features) + len(flag_features)
    )
```

**Wichtig:**
- `include_flags` Parameter hinzufügen
- Flag-Features automatisch generieren
- Metadaten für Flag-Features zurückgeben

---

### Schritt 2.2: Model Creation Endpoint erweitern

**Datei:** `app/api/routes.py`  
**Endpoint:** `POST /api/models/create/advanced`

**Änderungen:**

```python
@router.post("/models/create/advanced", response_model=CreateJobResponse)
async def create_model_job_advanced_endpoint(
    # ... bestehende Parameter ...
    use_flag_features: bool = Query(True, description="Flag-Features aktivieren?")  # NEU
):
    """
    Erstellt einen Trainings-Job mit erweiterten Optionen.
    
    NEU: use_flag_features steuert, ob Flag-Features verwendet werden.
    """
    
    # ... bestehender Code ...
    
    # NEU: use_flag_features an create_job übergeben
    job_id = await create_job(
        # ... bestehende Parameter ...
        use_flag_features=use_flag_features  # NEU
    )
    
    # ... Rest ...
```

**Wichtig:**
- `use_flag_features` Parameter hinzufügen
- An `create_job()` übergeben

---

### Schritt 2.3: Database Models erweitern

**Datei:** `app/database/models.py`  
**Funktion:** `create_job()` und `create_model()`

**Änderungen:**

```python
async def create_job(
    # ... bestehende Parameter ...
    use_flag_features: bool = True,  # NEU
) -> int:
    """
    Erstellt einen neuen Job.
    
    NEU: use_flag_features wird in der Datenbank gespeichert.
    """
    
    # Prüfe ob Spalte existiert, sonst erstelle sie
    # (Migration wird später gemacht)
    
    job_id = await pool.fetchval(
        """
        INSERT INTO ml_jobs (
            # ... bestehende Spalten ...
            use_flag_features  -- NEU: Falls Spalte existiert
        ) VALUES (
            # ... bestehende Werte ...
            $N  -- NEU: use_flag_features
        ) RETURNING id
        """,
        # ... bestehende Werte ...
        use_flag_features  # NEU
    )
    
    return job_id

async def create_model(
    # ... bestehende Parameter ...
    use_flag_features: bool = True,  # NEU
) -> int:
    """
    Erstellt ein neues Modell.
    
    NEU: use_flag_features wird gespeichert.
    """
    
    # Ähnlich wie create_job
    # ...
```

**Wichtig:**
- `use_flag_features` in Datenbank speichern
- Migration für neue Spalte erstellen

---

## 🎯 Phase 3: Datenbank - Migration

### Schritt 3.1: Migration erstellen

**Datei:** `sql/migration_add_flag_features.sql`

```sql
-- Migration: Flag-Features Support
-- Datum: 2026-01-08

-- 1. Füge use_flag_features Spalte zu ml_jobs hinzu
ALTER TABLE ml_jobs 
ADD COLUMN IF NOT EXISTS use_flag_features BOOLEAN DEFAULT TRUE;

-- 2. Füge use_flag_features Spalte zu ml_models hinzu
ALTER TABLE ml_models 
ADD COLUMN IF NOT EXISTS use_flag_features BOOLEAN DEFAULT TRUE;

-- 3. Kommentare hinzufügen
COMMENT ON COLUMN ml_jobs.use_flag_features IS 'Flag-Features aktiviert? (Standard: true)';
COMMENT ON COLUMN ml_models.use_flag_features IS 'Flag-Features aktiviert? (Standard: true)';

-- 4. Index für Performance (optional)
CREATE INDEX IF NOT EXISTS idx_ml_jobs_use_flag_features ON ml_jobs(use_flag_features);
CREATE INDEX IF NOT EXISTS idx_ml_models_use_flag_features ON ml_models(use_flag_features);
```

**Ausführen:**
```bash
docker-compose exec ml-service python3 -c "
import asyncio
from app.database.connection import get_pool

async def run_migration():
    pool = await get_pool()
    with open('sql/migration_add_flag_features.sql', 'r') as f:
        sql = f.read()
    await pool.execute(sql)
    print('✅ Migration erfolgreich')

asyncio.run(run_migration())
"
```

---

## 🎯 Phase 4: Frontend - UI erweitern

### Schritt 4.1: Features Liste erweitern

**Datei:** `ml-ui/src/pages/Training.tsx`

**Änderungen:**

```typescript
// NEU: Flag-Features zu ENGINEERING_FEATURES hinzufügen
const FLAG_FEATURES = [
  // Wird dynamisch generiert basierend auf ENGINEERING_FEATURES
  // Format: {baseFeature}_has_data
];

// Funktion zum Generieren von Flag-Features
const generateFlagFeatures = (engineeringFeatures: typeof ENGINEERING_FEATURES) => {
  const flags: typeof ENGINEERING_FEATURES = [];
  
  engineeringFeatures.forEach(feature => {
    // Prüfe ob Feature ein Window-Feature ist (5, 10, 15)
    const hasWindow = /_(5|10|15)$/.test(feature.id);
    
    if (hasWindow) {
      flags.push({
        id: `${feature.id}_has_data`,
        name: `🚩 ${feature.name} (Daten verfügbar)`,
        desc: `Flag: Hat ${feature.name} genug Daten?`,
        category: 'flag',
        importance: 'optional',
      });
    }
  });
  
  return flags;
};

// In der Komponente:
const [flagFeatures] = useState(() => generateFlagFeatures(ENGINEERING_FEATURES));

// UI: Flag-Features anzeigen (optional, da automatisch aktiviert)
// Oder: Checkbox "Flag-Features aktivieren" hinzufügen
```

**Wichtig:**
- Flag-Features automatisch generieren
- UI-Option zum Aktivieren/Deaktivieren

---

### Schritt 4.2: Model Creation Form erweitern

**Datei:** `ml-ui/src/pages/Training.tsx`

**Änderungen:**

```typescript
// NEU: State für Flag-Features
const [useFlagFeatures, setUseFlagFeatures] = useState(true);

// NEU: Checkbox in UI
<FormControlLabel
  control={
    <Checkbox
      checked={useFlagFeatures}
      onChange={(e) => setUseFlagFeatures(e.target.checked)}
    />
  }
  label="🚩 Flag-Features aktivieren (empfohlen)"
/>

// NEU: Beim API-Call übergeben
const requestBody = {
  // ... bestehende Felder ...
  use_flag_features: useFlagFeatures,  // NEU
};

const data = await mlApi.createAdvancedModel(requestBody);
```

**Wichtig:**
- Checkbox für Flag-Features
- Standard: aktiviert
- An API übergeben

---

### Schritt 4.3: Model Details erweitern

**Datei:** `ml-ui/src/pages/ModelDetails.tsx`

**Änderungen:**

```typescript
// NEU: Flag-Features in Feature-Liste anzeigen
const renderFeatures = (features: string[]) => {
  const baseFeatures = features.filter(f => BASE_FEATURES.some(bf => bf.id === f));
  const engineeredFeatures = features.filter(f => 
    ENGINEERING_FEATURES.some(ef => ef.id === f) && !f.endsWith('_has_data')
  );
  const flagFeatures = features.filter(f => f.endsWith('_has_data'));  // NEU
  
  return (
    <div>
      <Typography variant="h6">Basis-Features ({baseFeatures.length})</Typography>
      {/* ... */}
      
      <Typography variant="h6">Engineering-Features ({engineeredFeatures.length})</Typography>
      {/* ... */}
      
      {/* NEU: Flag-Features */}
      {flagFeatures.length > 0 && (
        <>
          <Typography variant="h6">🚩 Flag-Features ({flagFeatures.length})</Typography>
          <List>
            {flagFeatures.map(feature => (
              <ListItem key={feature}>
                <ListItemText 
                  primary={feature}
                  secondary="Datenverfügbarkeits-Flag"
                />
              </ListItem>
            ))}
          </List>
        </>
      )}
    </div>
  );
};
```

**Wichtig:**
- Flag-Features separat anzeigen
- Anzahl anzeigen
- Beschreibung hinzufügen

---

## 🎯 Phase 5: Tests

### Schritt 5.1: Unit Tests

**Datei:** `tests/test_flag_features.py` (NEU)

```python
import pytest
import pandas as pd
from app.training.feature_engineering import add_pump_detection_features

def test_flag_features_generation():
    """Test: Flag-Features werden korrekt generiert"""
    # Erstelle Test-Daten (Coin mit nur 5 Minuten Daten)
    data = pd.DataFrame({
        'mint': ['coin1'] * 5,
        'timestamp': pd.date_range('2026-01-01', periods=5, freq='1min'),
        'price_close': [1.0, 1.1, 1.2, 1.3, 1.4],
        'volatility_pct': [0.1, 0.2, 0.3, 0.4, 0.5],
    })
    
    # Generiere Features mit Flags
    result = add_pump_detection_features(data, include_flags=True)
    
    # Prüfe: Flag-Features vorhanden?
    assert 'volatility_ma_5_has_data' in result.columns
    assert 'volatility_ma_10_has_data' in result.columns
    assert 'volatility_ma_15_has_data' in result.columns
    
    # Prüfe: Flag-Werte korrekt?
    assert result['volatility_ma_5_has_data'].iloc[-1] == 1  # 5 Min alt → hat Daten
    assert result['volatility_ma_10_has_data'].iloc[-1] == 0  # 5 Min alt → keine Daten
    assert result['volatility_ma_15_has_data'].iloc[-1] == 0  # 5 Min alt → keine Daten

def test_flag_features_without_flags():
    """Test: Ohne Flags funktioniert alles wie vorher"""
    data = pd.DataFrame({
        'mint': ['coin1'] * 5,
        'timestamp': pd.date_range('2026-01-01', periods=5, freq='1min'),
        'price_close': [1.0, 1.1, 1.2, 1.3, 1.4],
        'volatility_pct': [0.1, 0.2, 0.3, 0.4, 0.5],
    })
    
    result = add_pump_detection_features(data, include_flags=False)
    
    # Prüfe: Keine Flag-Features
    flag_features = [col for col in result.columns if col.endswith('_has_data')]
    assert len(flag_features) == 0

def test_nan_handling_with_flags():
    """Test: NaN-Handling funktioniert mit Flags"""
    # ... Test-Code ...
```

**Ausführen:**
```bash
docker-compose exec ml-service pytest tests/test_flag_features.py -v
```

---

### Schritt 5.2: Integration Tests

**Datei:** `tests/test_flag_features_integration.py` (NEU)

```python
import pytest
from app.api.routes import create_model_job_advanced_endpoint
from app.training.engine import train_model_sync

def test_model_training_with_flags():
    """Test: Modell-Training mit Flag-Features"""
    # ... Test-Code ...
    
def test_model_testing_with_flags():
    """Test: Modell-Testing mit Flag-Features"""
    # ... Test-Code ...
```

---

## 🎯 Phase 6: Dokumentation

### Schritt 6.1: API-Dokumentation aktualisieren

**Datei:** `API_ADVANCED_ENDPOINT_ANLEITUNG.md`

**Änderungen:**

```markdown
## Flag-Features

**NEU:** Flag-Features sind zusätzliche binäre Features, die anzeigen, ob ein Engineering-Feature genug Daten hat.

### Parameter:
- `use_flag_features` (bool, optional, default: true): Flag-Features aktivieren?

### Beispiel:
```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\\
name=Model_With_Flags&\\
use_flag_features=true&\\
..."
```

### Flag-Features Format:
- Format: `{feature_name}_has_data`
- Werte: `1` = genug Daten, `0` = nicht genug Daten
- Beispiel: `volatility_ma_15_has_data`
```

---

### Schritt 6.2: Info-Seite aktualisieren

**Datei:** `ml-ui/src/pages/Info.tsx`

**Änderungen:**

```typescript
// NEU: Abschnitt über Flag-Features hinzufügen
<Typography variant="h5">
  🚩 Flag-Features (Datenverfügbarkeit)
</Typography>
<Typography variant="body1">
  Flag-Features sind zusätzliche binäre Features, die anzeigen, ob ein Engineering-Feature
  genug Daten hat. Sie helfen dem Modell zu unterscheiden zwischen:
  - "Feature = 0 weil wirklich 0" (zuverlässig)
  - "Feature = 0 weil keine Daten" (unzuverlässig)
</Typography>
```

---

## 🎯 Phase 7: Deployment

### Schritt 7.1: Migration ausführen

```bash
# 1. Code pullen
git pull origin main

# 2. Migration ausführen
docker-compose exec ml-service python3 -c "
import asyncio
from app.database.connection import get_pool

async def run_migration():
    pool = await get_pool()
    with open('sql/migration_add_flag_features.sql', 'r') as f:
        sql = f.read()
    await pool.execute(sql)
    print('✅ Migration erfolgreich')

asyncio.run(run_migration())
"

# 3. Container neu bauen
docker-compose build

# 4. Container neu starten
docker-compose up -d
```

---

### Schritt 7.2: Verifikation

```bash
# 1. Prüfe API
curl "http://localhost:8000/api/features?include_flags=true" | jq

# 2. Prüfe Datenbank
docker-compose exec ml-service python3 -c "
import asyncio
from app.database.connection import get_pool

async def check():
    pool = await get_pool()
    result = await pool.fetchrow('SELECT column_name FROM information_schema.columns WHERE table_name = \\'ml_models\\' AND column_name = \\'use_flag_features\\'')
    print('✅ Spalte vorhanden' if result else '❌ Spalte fehlt')

asyncio.run(check())
"

# 3. Teste Modell-Erstellung
curl -X POST "http://localhost:8000/api/models/create/advanced?name=Test_Flags&use_flag_features=true&..."
```

---

## ✅ Checkliste

### Backend
- [ ] `add_pump_detection_features()` erweitert
- [ ] `train_model_sync()` angepasst
- [ ] `test_model()` angepasst
- [ ] `create_job()` erweitert
- [ ] `create_model()` erweitert
- [ ] `/api/features` Endpoint erweitert
- [ ] `/api/models/create/advanced` Endpoint erweitert

### Datenbank
- [ ] Migration erstellt
- [ ] Migration ausgeführt
- [ ] Spalten hinzugefügt
- [ ] Indizes erstellt

### Frontend
- [ ] Flag-Features in Features-Liste
- [ ] Checkbox in Training-Form
- [ ] Flag-Features in Model Details
- [ ] Info-Seite aktualisiert

### Tests
- [ ] Unit Tests geschrieben
- [ ] Integration Tests geschrieben
- [ ] Tests erfolgreich

### Dokumentation
- [ ] API-Dokumentation aktualisiert
- [ ] Info-Seite aktualisiert
- [ ] README aktualisiert

### Deployment
- [ ] Migration ausgeführt
- [ ] Container neu gebaut
- [ ] Verifikation erfolgreich

---

## 🚨 Wichtige Hinweise

### Rückwärtskompatibilität

**Wichtig:** Alte Modelle ohne Flag-Features müssen weiterhin funktionieren!

**Lösung:**
- Standard: `use_flag_features = True` (neue Modelle)
- Alte Modelle: `use_flag_features = False` oder nicht gesetzt
- Beim Testen: Prüfe ob Modell Flag-Features hat, sonst nicht verwenden

### Performance

**Flag-Features erhöhen die Feature-Anzahl:**
- Vorher: ~66 Engineering-Features
- Nachher: ~66 Engineering-Features + ~50 Flag-Features = ~116 Features

**Auswirkung:**
- Training dauert etwas länger
- Modell-Size wird größer
- Aber: Bessere Genauigkeit

### Migration von alten Modellen

**Option 1:** Alte Modelle bleiben unverändert
- Alte Modelle: `use_flag_features = False`
- Neue Modelle: `use_flag_features = True`

**Option 2:** Alte Modelle neu trainieren (empfohlen für Produktion)
- Alte Modelle neu trainieren mit Flag-Features
- Bessere Performance

---

## 📊 Erwartete Ergebnisse

### Vorher (ohne Flag-Features):
- Feature-Anzahl: ~94 (28 Base + 66 Engineering)
- Modell kann nicht unterscheiden zwischen "0 weil wirklich 0" und "0 weil keine Daten"
- False Positives bei jungen Coins

### Nachher (mit Flag-Features):
- Feature-Anzahl: ~144 (28 Base + 66 Engineering + ~50 Flags)
- Modell kann unterscheiden zwischen "0 weil wirklich 0" und "0 weil keine Daten"
- Weniger False Positives bei jungen Coins
- Bessere Genauigkeit

---

**Erstellt:** 2026-01-08  
**Status:** Detaillierter Implementierungsplan  
**Geschätzte Dauer:** 4-6 Stunden für komplette Implementierung

