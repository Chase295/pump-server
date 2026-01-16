# 🚀 API-Dokumentation: `/models/create/advanced`

## Vollständige Anleitung zur Modell-Erstellung

**Version:** 1.0  
**Stand:** Januar 2026  
**Endpoint:** `POST /api/models/create/advanced`

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Alle Parameter](#alle-parameter)
3. [Feature-Liste](#feature-liste)
4. [Balance-Optionen](#balance-optionen)
5. [Beispiele](#beispiele)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Der `/models/create/advanced` Endpoint ist der **vollständigste und flexibelste** Endpoint zur Erstellung von ML-Modellen für Pump-Detection.

### Was kann dieser Endpoint?

| Funktion | Beschreibung |
|----------|--------------|
| ✅ **Zeitbasierte Vorhersage** | "Steigt der Preis um X% in Y Minuten?" |
| ✅ **Feature Engineering** | 66 zusätzliche berechnete Features |
| ✅ **SMOTE** | Synthetisches Oversampling für unbalancierte Daten |
| ✅ **scale_pos_weight** | XGBoost-interne Klassen-Gewichtung |
| ✅ **Flexible Zeithorizonte** | 1 Minute bis 60+ Minuten |
| ✅ **Pump & Rug Detection** | Steigende oder fallende Preise vorhersagen |
| ✅ **Zwei Modell-Typen** | XGBoost und Random Forest |

---

## 📊 Alle Parameter

### Pflicht-Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `name` | string | Eindeutiger Modell-Name | `"Pump_Detector_v1"` |
| `model_type` | string | `xgboost` oder `random_forest` | `"xgboost"` |
| `features` | string | Komma-separierte Feature-Liste | `"price_close,volume_sol"` |
| `train_start` | string | Trainings-Startzeit (UTC, ISO-Format) | `"2026-01-07T06:00:00Z"` |
| `train_end` | string | Trainings-Endzeit (UTC, ISO-Format) | `"2026-01-07T18:00:00Z"` |

### Optionale Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `target_var` | string | `"price_close"` | Ziel-Variable für Vorhersage |
| `use_time_based_prediction` | bool | `true` | Zeitbasierte Vorhersage aktivieren |
| `future_minutes` | int | `5` | Vorhersage-Horizont in Minuten |
| `min_percent_change` | float | `2.0` | Minimale Preisänderung in % |
| `direction` | string | `"up"` | `"up"` für Pump, `"down"` für Rug |
| `use_engineered_features` | bool | `false` | Feature Engineering aktivieren (siehe [Feature Engineering Optionen](#feature-engineering-optionen)) |
| `use_flag_features` | bool | `true` | **NEU!** Flag-Features aktivieren (siehe [Flag-Features](#flag-features)) |
| `use_smote` | bool | `false` | SMOTE aktivieren |
| `scale_pos_weight` | float | `null` | XGBoost Klassen-Gewichtung |
| `class_weight` | string | `null` | `"balanced"` für Random Forest |
| `phases` | string | `null` | **NEU!** Coin-Phasen Filter (z.B. `"1,2,3"`) |

---

## 🔄 Coin-Phasen Filter (NEU!)

Mit dem `phases` Parameter kannst du das Training auf **bestimmte Coin-Entwicklungsphasen** beschränken.

### Verfügbare Phasen

| Phase ID | Name | Beschreibung | Alter |
|----------|------|--------------|-------|
| **1** | Baby Zone | Frisch erstellte Coins | 0-10 Min |
| **2** | Survival Zone | Überlebende Coins | 10-120 Min |
| **3** | Mature Zone | Reife Coins | 2-4 Stunden |
| **99** | Finished | Abgeschlossene Coins | - |
| **100** | Graduated | Graduierte Coins | - |

### Beispiele

```bash
# Nur Baby & Survival Zone (Phase 1 + 2)
phases=1,2

# Nur Mature Zone (Phase 3)
phases=3

# Alle aktiven Phasen (1, 2, 3)
phases=1,2,3
```

### Warum Phasen filtern?

| Use Case | Empfohlene Phasen | Grund |
|----------|-------------------|-------|
| **Second Wave Detection** | `1,2` | Pumps passieren früh |
| **Langfristige Trends** | `2,3` | Stabile Datenmuster |
| **Rug-Pull Detection** | `1` | Rugs passieren in Phase 1 |
| **Allgemein** | `1,2,3` | Maximale Datenmenge |

---

## 📊 Feature-Liste

### 28 Basis-Features (immer verfügbar)

⚠️ **WICHTIG:** Bei zeitbasierter Vorhersage wird `price_close` automatisch aus den Trainings-Features entfernt (verhindert Data Leakage). In diesem Fall sind es **27 Basis-Features** im Training.

#### Preis-Features (4)
```
price_open      - Eröffnungspreis der Minute
price_high      - Höchster Preis der Minute
price_low       - Niedrigster Preis der Minute
price_close     - Schlusskurs der Minute
```

#### Volume-Features (4)
```
volume_sol          - Gesamtes Handelsvolumen in SOL
buy_volume_sol      - Kaufvolumen in SOL
sell_volume_sol     - Verkaufsvolumen in SOL
net_volume_sol      - Netto-Volumen (Buy - Sell)
```

#### Market-Features (4)
```
market_cap_close        - Marktkapitalisierung
bonding_curve_pct       - Position auf der Bonding Curve (%)
virtual_sol_reserves    - Virtuelle SOL-Reserven
is_koth                 - King of the Hill Status (0/1)
```

#### Trade-Statistiken (4)
```
num_buys            - Anzahl Buy-Trades
num_sells           - Anzahl Sell-Trades
unique_wallets      - Einzigartige Wallet-Adressen
num_micro_trades    - Anzahl Mikro-Trades
```

#### Max Trade Sizes (2)
```
max_single_buy_sol      - Größter einzelner Kauf
max_single_sell_sol     - Größter einzelner Verkauf
```

#### Whale-Features (4)
```
whale_buy_volume_sol    - Whale-Kaufvolumen
whale_sell_volume_sol   - Whale-Verkaufsvolumen
num_whale_buys          - Anzahl Whale-Käufe
num_whale_sells         - Anzahl Whale-Verkäufe
```

#### Qualitäts-Features (4)
```
dev_sold_amount     - Vom Developer verkaufte Menge
volatility_pct      - Preisvolatilität in %
avg_trade_size_sol  - Durchschnittliche Trade-Größe
buy_pressure_ratio  - Kaufdruck-Verhältnis (0-1)
```

#### Wallet-Analyse (2)
```
unique_signer_ratio     - Verhältnis einzigartiger Signaturen
phase_id_at_time        - Coin-Phase (1-6)
```

---

## 🚩 Flag-Features (NEU!)

Flag-Features sind **Datenverfügbarkeits-Indikatoren**, die dem Modell anzeigen, ob ein Engineering-Feature genug historische Daten hat, um zuverlässig berechnet zu werden.

### Was sind Flag-Features?

Jedes window-basierte Engineering-Feature (z.B. `buy_pressure_ma_5`) erhält ein entsprechendes Flag-Feature (z.B. `buy_pressure_ma_5_has_data`), das anzeigt:
- **`1`** = Genug Daten vorhanden (Feature ist zuverlässig)
- **`0`** = Nicht genug Daten (Feature könnte unzuverlässig sein)

### Warum Flag-Features?

| Problem | Lösung mit Flag-Features |
|---------|-------------------------|
| Neue Coins haben keine 15-Minuten-Historie | Modell lernt, dass `buy_pressure_ma_15_has_data=0` bedeutet: Feature ignorieren |
| NaN-Werte in Engineering-Features | Flag zeigt dem Modell, ob NaN = "keine Daten" oder "echter Wert" |
| Unzuverlässige Features bei jungen Coins | Modell kann Features basierend auf Datenverfügbarkeit gewichten |

### Aktivierung

Flag-Features werden automatisch aktiviert, wenn:
1. `use_engineered_features=true` **UND**
2. `use_flag_features=true` (Default: `true`)

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering + **57 Flag-Features = 150 Features total**

### Deaktivierung

Wenn du Flag-Features nicht möchtest:
```bash
use_flag_features=false
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering = 93 Features total (ohne Flags)

---

## 🚩 Alle 57 Flag-Features

### Dev-Sold Flag-Features (3)
```
dev_sold_spike_5_has_data      - Hat Coin genug Daten für Dev-Sold Spike (5 Min)?
dev_sold_spike_10_has_data     - Hat Coin genug Daten für Dev-Sold Spike (10 Min)?
dev_sold_spike_15_has_data     - Hat Coin genug Daten für Dev-Sold Spike (15 Min)?
```

### Buy Pressure Flag-Features (6)
```
buy_pressure_ma_5_has_data     - Hat Coin genug Daten für Buy Pressure MA (5 Min)?
buy_pressure_ma_10_has_data   - Hat Coin genug Daten für Buy Pressure MA (10 Min)?
buy_pressure_ma_15_has_data   - Hat Coin genug Daten für Buy Pressure MA (15 Min)?
buy_pressure_trend_5_has_data  - Hat Coin genug Daten für Buy Pressure Trend (5 Min)?
buy_pressure_trend_10_has_data - Hat Coin genug Daten für Buy Pressure Trend (10 Min)?
buy_pressure_trend_15_has_data - Hat Coin genug Daten für Buy Pressure Trend (15 Min)?
```

### Whale Activity Flag-Features (3)
```
whale_activity_5_has_data      - Hat Coin genug Daten für Whale Activity (5 Min)?
whale_activity_10_has_data    - Hat Coin genug Daten für Whale Activity (10 Min)?
whale_activity_15_has_data    - Hat Coin genug Daten für Whale Activity (15 Min)?
```

### Volatility Flag-Features (6)
```
volatility_ma_5_has_data      - Hat Coin genug Daten für Volatility MA (5 Min)?
volatility_ma_10_has_data    - Hat Coin genug Daten für Volatility MA (10 Min)?
volatility_ma_15_has_data    - Hat Coin genug Daten für Volatility MA (15 Min)?
volatility_spike_5_has_data   - Hat Coin genug Daten für Volatility Spike (5 Min)?
volatility_spike_10_has_data - Hat Coin genug Daten für Volatility Spike (10 Min)?
volatility_spike_15_has_data - Hat Coin genug Daten für Volatility Spike (15 Min)?
```

### Wash Trading Flag-Features (3)
```
wash_trading_flag_5_has_data  - Hat Coin genug Daten für Wash Trading Detection (5 Min)?
wash_trading_flag_10_has_data - Hat Coin genug Daten für Wash Trading Detection (10 Min)?
wash_trading_flag_15_has_data - Hat Coin genug Daten für Wash Trading Detection (15 Min)?
```

### Volume Pattern Flag-Features (6)
```
net_volume_ma_5_has_data      - Hat Coin genug Daten für Net Volume MA (5 Min)?
net_volume_ma_10_has_data    - Hat Coin genug Daten für Net Volume MA (10 Min)?
net_volume_ma_15_has_data    - Hat Coin genug Daten für Net Volume MA (15 Min)?
volume_flip_5_has_data       - Hat Coin genug Daten für Volume Flip (5 Min)?
volume_flip_10_has_data      - Hat Coin genug Daten für Volume Flip (10 Min)?
volume_flip_15_has_data      - Hat Coin genug Daten für Volume Flip (15 Min)?
```

### Price Momentum Flag-Features (6)
```
price_change_5_has_data      - Hat Coin genug Daten für Price Change (5 Min)?
price_change_10_has_data    - Hat Coin genug Daten für Price Change (10 Min)?
price_change_15_has_data    - Hat Coin genug Daten für Price Change (15 Min)?
price_roc_5_has_data         - Hat Coin genug Daten für Price ROC (5 Min)?
price_roc_10_has_data        - Hat Coin genug Daten für Price ROC (10 Min)?
price_roc_15_has_data        - Hat Coin genug Daten für Price ROC (15 Min)?
```

### Price Acceleration Flag-Features (3)
```
price_acceleration_5_has_data  - Hat Coin genug Daten für Price Acceleration (5 Min)?
price_acceleration_10_has_data - Hat Coin genug Daten für Price Acceleration (10 Min)?
price_acceleration_15_has_data - Hat Coin genug Daten für Price Acceleration (15 Min)?
```

### Market Cap Velocity Flag-Features (3)
```
mcap_velocity_5_has_data      - Hat Coin genug Daten für Market Cap Velocity (5 Min)?
mcap_velocity_10_has_data    - Hat Coin genug Daten für Market Cap Velocity (10 Min)?
mcap_velocity_15_has_data    - Hat Coin genug Daten für Market Cap Velocity (15 Min)?
```

### ATH Flag-Features (15)
```
ath_distance_trend_5_has_data         - Hat Coin genug Daten für ATH Distance Trend (5 Min)?
ath_distance_trend_10_has_data        - Hat Coin genug Daten für ATH Distance Trend (10 Min)?
ath_distance_trend_15_has_data       - Hat Coin genug Daten für ATH Distance Trend (15 Min)?
ath_approach_5_has_data              - Hat Coin genug Daten für ATH Approach (5 Min)?
ath_approach_10_has_data             - Hat Coin genug Daten für ATH Approach (10 Min)?
ath_approach_15_has_data             - Hat Coin genug Daten für ATH Approach (15 Min)?
ath_breakout_count_5_has_data         - Hat Coin genug Daten für ATH Breakout Count (5 Min)?
ath_breakout_count_10_has_data       - Hat Coin genug Daten für ATH Breakout Count (10 Min)?
ath_breakout_count_15_has_data       - Hat Coin genug Daten für ATH Breakout Count (15 Min)?
ath_breakout_volume_ma_5_has_data     - Hat Coin genug Daten für ATH Breakout Volume MA (5 Min)?
ath_breakout_volume_ma_10_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (10 Min)?
ath_breakout_volume_ma_15_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (15 Min)?
ath_age_trend_5_has_data             - Hat Coin genug Daten für ATH Age Trend (5 Min)?
ath_age_trend_10_has_data            - Hat Coin genug Daten für ATH Age Trend (10 Min)?
ath_age_trend_15_has_data            - Hat Coin genug Daten für ATH Age Trend (15 Min)?
```

### Volume Spike Flag-Features (3)
```
volume_spike_5_has_data      - Hat Coin genug Daten für Volume Spike (5 Min)?
volume_spike_10_has_data    - Hat Coin genug Daten für Volume Spike (10 Min)?
volume_spike_15_has_data    - Hat Coin genug Daten für Volume Spike (15 Min)?
```

### Zusammenfassung Flag-Features

| Kategorie | Anzahl | Window-Größen |
|-----------|--------|---------------|
| Dev-Sold | 3 | 5, 10, 15 Min |
| Buy Pressure | 6 | 5, 10, 15 Min (MA + Trend) |
| Whale Activity | 3 | 5, 10, 15 Min |
| Volatility | 6 | 5, 10, 15 Min (MA + Spike) |
| Wash Trading | 3 | 5, 10, 15 Min |
| Volume Pattern | 6 | 5, 10, 15 Min (Net Volume MA + Volume Flip) |
| Price Momentum | 6 | 5, 10, 15 Min (Change + ROC) |
| Price Acceleration | 3 | 5, 10, 15 Min |
| Market Cap Velocity | 3 | 5, 10, 15 Min |
| ATH Features | 15 | 5, 10, 15 Min (5 verschiedene ATH-Features) |
| Volume Spike | 3 | 5, 10, 15 Min |
| **GESAMT** | **57** | - |

---

### ⚠️ WICHTIG: Selektive Flag-Feature-Filterung (NEU!)

**Wenn du nur einen Teil der Engineering-Features auswählst, werden automatisch nur die entsprechenden Flag-Features verwendet!**

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,price_change_5,price_change_10,volume_spike_5&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 
- 2 Basis-Features (`price_close`, `volume_sol` - `price_close` wird bei zeitbasierter Vorhersage entfernt)
- 3 Engineering-Features (`price_change_5`, `price_change_10`, `volume_spike_5`)
- **Nur 3 Flag-Features** (`price_change_5_has_data`, `price_change_10_has_data`, `volume_spike_5_has_data`)
- **NICHT alle 57 Flag-Features!**

**Warum?**
Das System filtert automatisch die Flag-Features, sodass nur die Flag-Features verwendet werden, die zu den ausgewählten Engineering-Features gehören. Dies verhindert:
- Overfitting durch zu viele Features
- Unnötige Komplexität
- Längere Trainingszeiten

**Vergleich:**

| Szenario | Engineering-Features | Flag-Features | Gesamt |
|----------|---------------------|--------------|--------|
| **Alle Engineering-Features** | 66 | 57 | 123 |
| **Nur 3 Engineering-Features** | 3 | **3** (nur die relevanten!) | 6 |
| **Nur 10 Engineering-Features** | 10 | **10** (nur die relevanten!) | 20 |

## 🔧 Feature Engineering Optionen

Der `use_engineered_features` Parameter bietet **3 verschiedene Modi**:

### Option 1: Keine Engineering-Features (Default)

**Verhalten:** Nur die Basis-Features werden verwendet, die du in der `features` Liste angibst.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&
  use_engineered_features=false
  # oder einfach weglassen (Default ist false)
```

**Ergebnis:** 4 Features total (nur Basis-Features)

---

### Option 2: Spezifische Engineering-Features auswählen

**Verhalten:** Du gibst explizit Engineering-Features in der `features` Liste an. Das Backend erstellt nur diese.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume&
  use_engineered_features=true
```

**Ergebnis:** 5 Features total (2 Basis + 3 Engineering)

**Vorteil:** Du hast volle Kontrolle über welche Engineering-Features verwendet werden.

---

### Option 3: Alle Engineering-Features (66 Stück)

**Verhalten:** Wenn `use_engineered_features=true` ist, aber **keine** Engineering-Features in der `features` Liste stehen, werden automatisch **alle 66 Engineering-Features** erstellt.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true
```

**Ergebnis:** 68 Features total (2 Basis + 66 Engineering)

**Vorteil:** Maximale Feature-Abdeckung ohne manuelle Auswahl.

---

### Zusammenfassung

| Modus | `use_engineered_features` | Engineering-Features in `features` | Ergebnis |
|-------|---------------------------|-----------------------------------|----------|
| **Keine** | `false` oder weglassen | - | Nur Basis-Features |
| **Spezifische** | `true` | ✅ Ja (z.B. `dev_sold_spike_5`) | Nur die angegebenen Engineering-Features |
| **Alle** | `true` | ❌ Nein | Alle 66 Engineering-Features |

---

### 66 Engineering-Features (mit `use_engineered_features=true`)

#### Dev-Sold Features (6)
```
dev_sold_flag           - Hat der Dev verkauft? (0/1)
dev_sold_cumsum         - Kumulative Dev-Verkäufe
dev_sold_spike_5        - Dev-Verkauf-Spike (5 Min)
dev_sold_spike_10       - Dev-Verkauf-Spike (10 Min)
dev_sold_spike_15       - Dev-Verkauf-Spike (15 Min)
```

#### Buy Pressure Features (6)
```
buy_pressure_ma_5       - Moving Average (5 Min)
buy_pressure_trend_5    - Trend (5 Min)
buy_pressure_ma_10      - Moving Average (10 Min)
buy_pressure_trend_10   - Trend (10 Min)
buy_pressure_ma_15      - Moving Average (15 Min)
buy_pressure_trend_15   - Trend (15 Min)
```

#### Whale Activity Features (4)
```
whale_net_volume        - Netto Whale-Volume
whale_activity_5        - Whale-Aktivität (5 Min)
whale_activity_10       - Whale-Aktivität (10 Min)
whale_activity_15       - Whale-Aktivität (15 Min)
```

#### Volatility Features (6)
```
volatility_ma_5         - Volatilität MA (5 Min)
volatility_spike_5      - Volatilität-Spike (5 Min)
volatility_ma_10        - Volatilität MA (10 Min)
volatility_spike_10     - Volatilität-Spike (10 Min)
volatility_ma_15        - Volatilität MA (15 Min)
volatility_spike_15     - Volatilität-Spike (15 Min)
```

#### Wash Trading Detection (3)
```
wash_trading_flag_5     - Wash Trading erkannt? (5 Min)
wash_trading_flag_10    - Wash Trading erkannt? (10 Min)
wash_trading_flag_15    - Wash Trading erkannt? (15 Min)
```

#### Volume Pattern Features (6)
```
net_volume_ma_5         - Netto-Volume MA (5 Min)
volume_flip_5           - Volume Flip (5 Min)
net_volume_ma_10        - Netto-Volume MA (10 Min)
volume_flip_10          - Volume Flip (10 Min)
net_volume_ma_15        - Netto-Volume MA (15 Min)
volume_flip_15          - Volume Flip (15 Min)
```

#### Price Momentum Features (6)
```
price_change_5          - Preisänderung (5 Min)
price_roc_5             - Rate of Change (5 Min)
price_change_10         - Preisänderung (10 Min)
price_roc_10            - Rate of Change (10 Min)
price_change_15         - Preisänderung (15 Min)
price_roc_15            - Rate of Change (15 Min)
```

#### Market Cap Velocity (3)
```
mcap_velocity_5         - MarketCap Änderungsrate (5 Min)
mcap_velocity_10        - MarketCap Änderungsrate (10 Min)
mcap_velocity_15        - MarketCap Änderungsrate (15 Min)
```

#### ATH Features (19)
```
rolling_ath             - Rolling All-Time-High
price_vs_ath_pct        - Distanz zum ATH in %
ath_breakout            - ATH durchbrochen? (0/1)
minutes_since_ath       - Minuten seit letztem ATH
ath_distance_trend_5    - ATH-Distanz Trend (5 Min)
ath_approach_5          - Nähert sich ATH? (5 Min)
ath_breakout_count_5    - ATH-Durchbrüche (5 Min)
ath_breakout_volume_ma_5 - Volume bei ATH-Breaks (5 Min)
ath_age_trend_5         - ATH-Alter Trend (5 Min)
... (analog für 10 und 15 Minuten)
```

#### Power Features (8)
```
buy_sell_ratio          - Buy/Sell Verhältnis
whale_dominance         - Whale-Anteil am Volume
price_acceleration_5    - Preis-Beschleunigung (5 Min)
price_acceleration_10   - Preis-Beschleunigung (10 Min)
price_acceleration_15   - Preis-Beschleunigung (15 Min)
volume_spike_5          - Volume-Spike (5 Min)
volume_spike_10         - Volume-Spike (10 Min)
volume_spike_15         - Volume-Spike (15 Min)
```

---

## ⚖️ Balance-Optionen

### Das Problem: Unbalancierte Daten

Bei Pump-Detection sind positive Labels (Pumps) sehr selten (oft nur 1-5% der Daten). Das führt dazu, dass Modelle einfach "Nein" für alles vorhersagen.

### Lösung 1: `scale_pos_weight` (✅ EMPFOHLEN)

XGBoost-intern, gewichtet die positive Klasse höher.

| Positive Labels | scale_pos_weight | Effekt |
|-----------------|------------------|--------|
| 0.5% | `200` | Sehr aggressiv |
| 1% | `100` | Standard |
| 2% | `50` | Moderat |
| 5% | `20` | Konservativ |

**Beispiel:**
```bash
scale_pos_weight=100
```

**Vorteile:**
- Keine synthetischen Daten
- Schneller als SMOTE
- Besser generalisierbar

### Lösung 2: `use_smote` (⚠️ Mit Vorsicht)

Synthetisches Oversampling - erstellt künstliche positive Samples.

**Beispiel:**
```bash
use_smote=true
```

**Nachteile:**
- Kann zu Overfitting führen
- Modell lernt synthetische statt echte Muster

### Lösung 3: `class_weight` (für Random Forest)

```bash
class_weight=balanced
```

---

## 📝 Beispiele

### Beispiel 1: Einfaches Pump-Modell

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio&\
future_minutes=5&\
min_percent_change=2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 2: Mit ALLEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 2c: Mit ALLEN Engineering-Features OHNE Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_No_Flags_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=false&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 70 Features (4 Basis + 66 Engineering, keine Flag-Features)

### Beispiel 2b: Mit SPEZIFISCHEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Selective_Engineering_v1&\
model_type=xgboost&\
features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume,volatility_spike_15&\
use_engineered_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 8 Features (2 Basis + 4 Engineering + **4 Flag-Features** - nur die für die ausgewählten Engineering-Features!)

**Wichtig:** Das System verwendet automatisch nur die Flag-Features, die zu den ausgewählten Engineering-Features gehören:
- `dev_sold_spike_5_has_data` (für `dev_sold_spike_5`)
- `buy_pressure_ma_10_has_data` (für `buy_pressure_ma_10`)
- `volatility_spike_15_has_data` (für `volatility_spike_15`)
- `whale_net_volume` hat kein Flag-Feature (ist kein window-basiertes Feature)

### Beispiel 3: OHNE Engineering-Features (nur Basis)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol&\
use_engineered_features=false&\
scale_pos_weight=100&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 5 Features (nur Basis-Features, keine Engineering)

### Beispiel 4: Mit scale_pos_weight (EMPFOHLEN)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Balanced_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 5: ULTIMATIV (Alle Features + Engineering + Flag-Features + Balance)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Ultimate_Pump_Detector&\
model_type=xgboost&\
features=price_open,price_high,price_low,price_close,volume_sol,buy_volume_sol,sell_volume_sol,net_volume_sol,market_cap_close,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct,unique_signer_ratio&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=15&\
direction=up&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 137 Features (14 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 5: Rug-Pull Detection

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Rug_Pull_Detector&\
model_type=xgboost&\
features=price_close,dev_sold_amount,buy_pressure_ratio,whale_sell_volume_sol&\
direction=down&\
min_percent_change=20&\
future_minutes=15&\
scale_pos_weight=50&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 6: Random Forest

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=RF_Pump_Detector&\
model_type=random_forest&\
features=price_close,volume_sol,buy_pressure_ratio&\
class_weight=balanced&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 7: Second Wave Detection (mit Flag-Features)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Second_Wave_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
future_minutes=15&\
min_percent_change=10&\
phases=1,2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 129 Features (6 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 8: Nur Baby Zone (Phase 1)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Baby_Zone_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
phases=1&\
scale_pos_weight=150&\
future_minutes=5&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 9: Survival + Mature Zone (Phase 2+3) mit Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Mature_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
phases=2,3&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=80&\
future_minutes=15&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

---

## 💡 Best Practices

### 1. Feature-Auswahl

| Empfehlung | Beschreibung |
|------------|--------------|
| ✅ Start mit Basis-Features | Beginne mit 5-10 wichtigen Features |
| ✅ Wichtigste Features zuerst | `price_close`, `volume_sol`, `buy_pressure_ratio` |
| ✅ Flag-Features aktivieren | Verbessert Modell-Performance bei neuen Coins |
| ⚠️ Nicht zu viele Features | Mehr als 30 Basis-Features kann zu Overfitting führen |
| ⚠️ Mit Engineering + Flags | Bis zu 150 Features möglich (27 Base + 66 Eng + 57 Flags bei zeitbasierter Vorhersage) oder 151 Features (28 Base + 66 Eng + 57 Flags ohne zeitbasierte Vorhersage) |
| ❌ Keine redundanten Features | z.B. nicht `price_open` UND `price_close` UND `price_high` UND `price_low` |

### 2. Zeithorizont-Wahl

| Zeithorizont | Empfohlene Schwelle | Use Case |
|--------------|---------------------|----------|
| 2-5 Min | 1-3% | Schnelle Scalping-Signale |
| 5-10 Min | 3-10% | Standard Pump Detection |
| 10-15 Min | 5-15% | Second Wave Detection |
| 15-30 Min | 10-25% | Langfristige Trends |

### 3. Balance-Strategie

| Situation | Empfehlung |
|-----------|------------|
| 1% positive Labels | `scale_pos_weight=100` |
| Sehr seltene Events | `scale_pos_weight=200` |
| Mehr Pumps erkennen | Höherer `scale_pos_weight` (mehr Fehlalarme) |
| Weniger Fehlalarme | Niedrigerer `scale_pos_weight` (weniger erkannte Pumps) |

### 4. Trainings-Zeitraum

| Zeitraum | Empfehlung |
|----------|------------|
| **Minimum** | 2 Stunden |
| **Optimal** | 8-12 Stunden |
| **Maximum** | 24+ Stunden (längere Wartezeit) |

---

## 🔧 Troubleshooting

### Problem: F1-Score = 0

**Ursache:** Zu wenig positive Labels oder keine Balance-Strategie.

**Lösung:**
1. Aktiviere `scale_pos_weight=100`
2. ODER senke `min_percent_change`
3. ODER erhöhe `future_minutes`

### Problem: Zu viele Fehlalarme

**Ursache:** `scale_pos_weight` zu hoch.

**Lösung:**
1. Senke `scale_pos_weight` (z.B. von 200 auf 100)
2. ODER erhöhe `min_percent_change`

### Problem: Keine Pumps erkannt

**Ursache:** `scale_pos_weight` zu niedrig oder Feature-Auswahl schlecht.

**Lösung:**
1. Erhöhe `scale_pos_weight` (z.B. auf 200)
2. Füge relevante Features hinzu: `buy_pressure_ratio`, `whale_buy_volume_sol`

### Problem: Training dauert zu lange

**Ursache:** Zu viele Features oder zu großer Zeitraum.

**Lösung:**
1. Reduziere Features auf 10-15
2. Reduziere Trainings-Zeitraum
3. Deaktiviere `use_engineered_features`

### Problem: "Keine Trainingsdaten gefunden"

**Ursache:** Der angegebene Zeitraum enthält keine Daten.

**Lösung:**
1. Prüfe ob der Zeitraum korrekt ist (UTC!)
2. Verwende einen Zeitraum mit bekannten Daten

---

## 📊 Response-Format

### Erfolgreiche Erstellung

```json
{
  "job_id": 424,
  "message": "Job erstellt. Modell 'MyModel' wird trainiert.",
  "status": "PENDING"
}
```

### Job-Status prüfen

```bash
GET /api/queue/{job_id}
```

```json
{
  "id": 424,
  "status": "COMPLETED",
  "result_model_id": 130,
  "progress": 100,
  "progress_msg": "Training abgeschlossen"
}
```

### Modell-Details abrufen

```bash
GET /api/models/{model_id}
```

---

## 🌐 Web UI

Die Web UI bietet dieselben Funktionen mit grafischer Oberfläche:

**URL:** https://test.local.chase295.de/training

Im Schritt 5 "Erweiterte Einstellungen" findest du:
- ⚖️ Klassen-Gewichtung (scale_pos_weight)
- Cross-Validation Einstellungen
- SMOTE Option
- Trainings-Zeitraum

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe die Job-Logs: `GET /api/queue/{job_id}`
2. Prüfe die Modell-Details: `GET /api/models/{model_id}`
3. Sieh dir die Confusion Matrix an für Einblicke in die Performance

---

**Dokumentation erstellt:** Januar 2026  
**Getestet:** 10/10 Tests bestanden ✅


## Vollständige Anleitung zur Modell-Erstellung

**Version:** 1.0  
**Stand:** Januar 2026  
**Endpoint:** `POST /api/models/create/advanced`

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Alle Parameter](#alle-parameter)
3. [Feature-Liste](#feature-liste)
4. [Balance-Optionen](#balance-optionen)
5. [Beispiele](#beispiele)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Der `/models/create/advanced` Endpoint ist der **vollständigste und flexibelste** Endpoint zur Erstellung von ML-Modellen für Pump-Detection.

### Was kann dieser Endpoint?

| Funktion | Beschreibung |
|----------|--------------|
| ✅ **Zeitbasierte Vorhersage** | "Steigt der Preis um X% in Y Minuten?" |
| ✅ **Feature Engineering** | 66 zusätzliche berechnete Features |
| ✅ **SMOTE** | Synthetisches Oversampling für unbalancierte Daten |
| ✅ **scale_pos_weight** | XGBoost-interne Klassen-Gewichtung |
| ✅ **Flexible Zeithorizonte** | 1 Minute bis 60+ Minuten |
| ✅ **Pump & Rug Detection** | Steigende oder fallende Preise vorhersagen |
| ✅ **Zwei Modell-Typen** | XGBoost und Random Forest |

---

## 📊 Alle Parameter

### Pflicht-Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `name` | string | Eindeutiger Modell-Name | `"Pump_Detector_v1"` |
| `model_type` | string | `xgboost` oder `random_forest` | `"xgboost"` |
| `features` | string | Komma-separierte Feature-Liste | `"price_close,volume_sol"` |
| `train_start` | string | Trainings-Startzeit (UTC, ISO-Format) | `"2026-01-07T06:00:00Z"` |
| `train_end` | string | Trainings-Endzeit (UTC, ISO-Format) | `"2026-01-07T18:00:00Z"` |

### Optionale Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `target_var` | string | `"price_close"` | Ziel-Variable für Vorhersage |
| `use_time_based_prediction` | bool | `true` | Zeitbasierte Vorhersage aktivieren |
| `future_minutes` | int | `5` | Vorhersage-Horizont in Minuten |
| `min_percent_change` | float | `2.0` | Minimale Preisänderung in % |
| `direction` | string | `"up"` | `"up"` für Pump, `"down"` für Rug |
| `use_engineered_features` | bool | `false` | Feature Engineering aktivieren (siehe [Feature Engineering Optionen](#feature-engineering-optionen)) |
| `use_flag_features` | bool | `true` | **NEU!** Flag-Features aktivieren (siehe [Flag-Features](#flag-features)) |
| `use_smote` | bool | `false` | SMOTE aktivieren |
| `scale_pos_weight` | float | `null` | XGBoost Klassen-Gewichtung |
| `class_weight` | string | `null` | `"balanced"` für Random Forest |
| `phases` | string | `null` | **NEU!** Coin-Phasen Filter (z.B. `"1,2,3"`) |

---

## 🔄 Coin-Phasen Filter (NEU!)

Mit dem `phases` Parameter kannst du das Training auf **bestimmte Coin-Entwicklungsphasen** beschränken.

### Verfügbare Phasen

| Phase ID | Name | Beschreibung | Alter |
|----------|------|--------------|-------|
| **1** | Baby Zone | Frisch erstellte Coins | 0-10 Min |
| **2** | Survival Zone | Überlebende Coins | 10-120 Min |
| **3** | Mature Zone | Reife Coins | 2-4 Stunden |
| **99** | Finished | Abgeschlossene Coins | - |
| **100** | Graduated | Graduierte Coins | - |

### Beispiele

```bash
# Nur Baby & Survival Zone (Phase 1 + 2)
phases=1,2

# Nur Mature Zone (Phase 3)
phases=3

# Alle aktiven Phasen (1, 2, 3)
phases=1,2,3
```

### Warum Phasen filtern?

| Use Case | Empfohlene Phasen | Grund |
|----------|-------------------|-------|
| **Second Wave Detection** | `1,2` | Pumps passieren früh |
| **Langfristige Trends** | `2,3` | Stabile Datenmuster |
| **Rug-Pull Detection** | `1` | Rugs passieren in Phase 1 |
| **Allgemein** | `1,2,3` | Maximale Datenmenge |

---

## 📊 Feature-Liste

### 28 Basis-Features (immer verfügbar)

⚠️ **WICHTIG:** Bei zeitbasierter Vorhersage wird `price_close` automatisch aus den Trainings-Features entfernt (verhindert Data Leakage). In diesem Fall sind es **27 Basis-Features** im Training.

#### Preis-Features (4)
```
price_open      - Eröffnungspreis der Minute
price_high      - Höchster Preis der Minute
price_low       - Niedrigster Preis der Minute
price_close     - Schlusskurs der Minute
```

#### Volume-Features (4)
```
volume_sol          - Gesamtes Handelsvolumen in SOL
buy_volume_sol      - Kaufvolumen in SOL
sell_volume_sol     - Verkaufsvolumen in SOL
net_volume_sol      - Netto-Volumen (Buy - Sell)
```

#### Market-Features (4)
```
market_cap_close        - Marktkapitalisierung
bonding_curve_pct       - Position auf der Bonding Curve (%)
virtual_sol_reserves    - Virtuelle SOL-Reserven
is_koth                 - King of the Hill Status (0/1)
```

#### Trade-Statistiken (4)
```
num_buys            - Anzahl Buy-Trades
num_sells           - Anzahl Sell-Trades
unique_wallets      - Einzigartige Wallet-Adressen
num_micro_trades    - Anzahl Mikro-Trades
```

#### Max Trade Sizes (2)
```
max_single_buy_sol      - Größter einzelner Kauf
max_single_sell_sol     - Größter einzelner Verkauf
```

#### Whale-Features (4)
```
whale_buy_volume_sol    - Whale-Kaufvolumen
whale_sell_volume_sol   - Whale-Verkaufsvolumen
num_whale_buys          - Anzahl Whale-Käufe
num_whale_sells         - Anzahl Whale-Verkäufe
```

#### Qualitäts-Features (4)
```
dev_sold_amount     - Vom Developer verkaufte Menge
volatility_pct      - Preisvolatilität in %
avg_trade_size_sol  - Durchschnittliche Trade-Größe
buy_pressure_ratio  - Kaufdruck-Verhältnis (0-1)
```

#### Wallet-Analyse (2)
```
unique_signer_ratio     - Verhältnis einzigartiger Signaturen
phase_id_at_time        - Coin-Phase (1-6)
```

---

## 🚩 Flag-Features (NEU!)

Flag-Features sind **Datenverfügbarkeits-Indikatoren**, die dem Modell anzeigen, ob ein Engineering-Feature genug historische Daten hat, um zuverlässig berechnet zu werden.

### Was sind Flag-Features?

Jedes window-basierte Engineering-Feature (z.B. `buy_pressure_ma_5`) erhält ein entsprechendes Flag-Feature (z.B. `buy_pressure_ma_5_has_data`), das anzeigt:
- **`1`** = Genug Daten vorhanden (Feature ist zuverlässig)
- **`0`** = Nicht genug Daten (Feature könnte unzuverlässig sein)

### Warum Flag-Features?

| Problem | Lösung mit Flag-Features |
|---------|-------------------------|
| Neue Coins haben keine 15-Minuten-Historie | Modell lernt, dass `buy_pressure_ma_15_has_data=0` bedeutet: Feature ignorieren |
| NaN-Werte in Engineering-Features | Flag zeigt dem Modell, ob NaN = "keine Daten" oder "echter Wert" |
| Unzuverlässige Features bei jungen Coins | Modell kann Features basierend auf Datenverfügbarkeit gewichten |

### Aktivierung

Flag-Features werden automatisch aktiviert, wenn:
1. `use_engineered_features=true` **UND**
2. `use_flag_features=true` (Default: `true`)

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering + **57 Flag-Features = 150 Features total**

### Deaktivierung

Wenn du Flag-Features nicht möchtest:
```bash
use_flag_features=false
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering = 93 Features total (ohne Flags)

---

## 🚩 Alle 57 Flag-Features

### Dev-Sold Flag-Features (3)
```
dev_sold_spike_5_has_data      - Hat Coin genug Daten für Dev-Sold Spike (5 Min)?
dev_sold_spike_10_has_data     - Hat Coin genug Daten für Dev-Sold Spike (10 Min)?
dev_sold_spike_15_has_data     - Hat Coin genug Daten für Dev-Sold Spike (15 Min)?
```

### Buy Pressure Flag-Features (6)
```
buy_pressure_ma_5_has_data     - Hat Coin genug Daten für Buy Pressure MA (5 Min)?
buy_pressure_ma_10_has_data   - Hat Coin genug Daten für Buy Pressure MA (10 Min)?
buy_pressure_ma_15_has_data   - Hat Coin genug Daten für Buy Pressure MA (15 Min)?
buy_pressure_trend_5_has_data  - Hat Coin genug Daten für Buy Pressure Trend (5 Min)?
buy_pressure_trend_10_has_data - Hat Coin genug Daten für Buy Pressure Trend (10 Min)?
buy_pressure_trend_15_has_data - Hat Coin genug Daten für Buy Pressure Trend (15 Min)?
```

### Whale Activity Flag-Features (3)
```
whale_activity_5_has_data      - Hat Coin genug Daten für Whale Activity (5 Min)?
whale_activity_10_has_data    - Hat Coin genug Daten für Whale Activity (10 Min)?
whale_activity_15_has_data    - Hat Coin genug Daten für Whale Activity (15 Min)?
```

### Volatility Flag-Features (6)
```
volatility_ma_5_has_data      - Hat Coin genug Daten für Volatility MA (5 Min)?
volatility_ma_10_has_data    - Hat Coin genug Daten für Volatility MA (10 Min)?
volatility_ma_15_has_data    - Hat Coin genug Daten für Volatility MA (15 Min)?
volatility_spike_5_has_data   - Hat Coin genug Daten für Volatility Spike (5 Min)?
volatility_spike_10_has_data - Hat Coin genug Daten für Volatility Spike (10 Min)?
volatility_spike_15_has_data - Hat Coin genug Daten für Volatility Spike (15 Min)?
```

### Wash Trading Flag-Features (3)
```
wash_trading_flag_5_has_data  - Hat Coin genug Daten für Wash Trading Detection (5 Min)?
wash_trading_flag_10_has_data - Hat Coin genug Daten für Wash Trading Detection (10 Min)?
wash_trading_flag_15_has_data - Hat Coin genug Daten für Wash Trading Detection (15 Min)?
```

### Volume Pattern Flag-Features (6)
```
net_volume_ma_5_has_data      - Hat Coin genug Daten für Net Volume MA (5 Min)?
net_volume_ma_10_has_data    - Hat Coin genug Daten für Net Volume MA (10 Min)?
net_volume_ma_15_has_data    - Hat Coin genug Daten für Net Volume MA (15 Min)?
volume_flip_5_has_data       - Hat Coin genug Daten für Volume Flip (5 Min)?
volume_flip_10_has_data      - Hat Coin genug Daten für Volume Flip (10 Min)?
volume_flip_15_has_data      - Hat Coin genug Daten für Volume Flip (15 Min)?
```

### Price Momentum Flag-Features (6)
```
price_change_5_has_data      - Hat Coin genug Daten für Price Change (5 Min)?
price_change_10_has_data    - Hat Coin genug Daten für Price Change (10 Min)?
price_change_15_has_data    - Hat Coin genug Daten für Price Change (15 Min)?
price_roc_5_has_data         - Hat Coin genug Daten für Price ROC (5 Min)?
price_roc_10_has_data        - Hat Coin genug Daten für Price ROC (10 Min)?
price_roc_15_has_data        - Hat Coin genug Daten für Price ROC (15 Min)?
```

### Price Acceleration Flag-Features (3)
```
price_acceleration_5_has_data  - Hat Coin genug Daten für Price Acceleration (5 Min)?
price_acceleration_10_has_data - Hat Coin genug Daten für Price Acceleration (10 Min)?
price_acceleration_15_has_data - Hat Coin genug Daten für Price Acceleration (15 Min)?
```

### Market Cap Velocity Flag-Features (3)
```
mcap_velocity_5_has_data      - Hat Coin genug Daten für Market Cap Velocity (5 Min)?
mcap_velocity_10_has_data    - Hat Coin genug Daten für Market Cap Velocity (10 Min)?
mcap_velocity_15_has_data    - Hat Coin genug Daten für Market Cap Velocity (15 Min)?
```

### ATH Flag-Features (15)
```
ath_distance_trend_5_has_data         - Hat Coin genug Daten für ATH Distance Trend (5 Min)?
ath_distance_trend_10_has_data        - Hat Coin genug Daten für ATH Distance Trend (10 Min)?
ath_distance_trend_15_has_data       - Hat Coin genug Daten für ATH Distance Trend (15 Min)?
ath_approach_5_has_data              - Hat Coin genug Daten für ATH Approach (5 Min)?
ath_approach_10_has_data             - Hat Coin genug Daten für ATH Approach (10 Min)?
ath_approach_15_has_data             - Hat Coin genug Daten für ATH Approach (15 Min)?
ath_breakout_count_5_has_data         - Hat Coin genug Daten für ATH Breakout Count (5 Min)?
ath_breakout_count_10_has_data       - Hat Coin genug Daten für ATH Breakout Count (10 Min)?
ath_breakout_count_15_has_data       - Hat Coin genug Daten für ATH Breakout Count (15 Min)?
ath_breakout_volume_ma_5_has_data     - Hat Coin genug Daten für ATH Breakout Volume MA (5 Min)?
ath_breakout_volume_ma_10_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (10 Min)?
ath_breakout_volume_ma_15_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (15 Min)?
ath_age_trend_5_has_data             - Hat Coin genug Daten für ATH Age Trend (5 Min)?
ath_age_trend_10_has_data            - Hat Coin genug Daten für ATH Age Trend (10 Min)?
ath_age_trend_15_has_data            - Hat Coin genug Daten für ATH Age Trend (15 Min)?
```

### Volume Spike Flag-Features (3)
```
volume_spike_5_has_data      - Hat Coin genug Daten für Volume Spike (5 Min)?
volume_spike_10_has_data    - Hat Coin genug Daten für Volume Spike (10 Min)?
volume_spike_15_has_data    - Hat Coin genug Daten für Volume Spike (15 Min)?
```

### Zusammenfassung Flag-Features

| Kategorie | Anzahl | Window-Größen |
|-----------|--------|---------------|
| Dev-Sold | 3 | 5, 10, 15 Min |
| Buy Pressure | 6 | 5, 10, 15 Min (MA + Trend) |
| Whale Activity | 3 | 5, 10, 15 Min |
| Volatility | 6 | 5, 10, 15 Min (MA + Spike) |
| Wash Trading | 3 | 5, 10, 15 Min |
| Volume Pattern | 6 | 5, 10, 15 Min (Net Volume MA + Volume Flip) |
| Price Momentum | 6 | 5, 10, 15 Min (Change + ROC) |
| Price Acceleration | 3 | 5, 10, 15 Min |
| Market Cap Velocity | 3 | 5, 10, 15 Min |
| ATH Features | 15 | 5, 10, 15 Min (5 verschiedene ATH-Features) |
| Volume Spike | 3 | 5, 10, 15 Min |
| **GESAMT** | **57** | - |

---

## 🔧 Feature Engineering Optionen

Der `use_engineered_features` Parameter bietet **3 verschiedene Modi**:

### Option 1: Keine Engineering-Features (Default)

**Verhalten:** Nur die Basis-Features werden verwendet, die du in der `features` Liste angibst.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&
  use_engineered_features=false
  # oder einfach weglassen (Default ist false)
```

**Ergebnis:** 4 Features total (nur Basis-Features)

---

### Option 2: Spezifische Engineering-Features auswählen

**Verhalten:** Du gibst explizit Engineering-Features in der `features` Liste an. Das Backend erstellt nur diese.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume&
  use_engineered_features=true
```

**Ergebnis:** 5 Features total (2 Basis + 3 Engineering)

**Vorteil:** Du hast volle Kontrolle über welche Engineering-Features verwendet werden.

---

### Option 3: Alle Engineering-Features (66 Stück)

**Verhalten:** Wenn `use_engineered_features=true` ist, aber **keine** Engineering-Features in der `features` Liste stehen, werden automatisch **alle 66 Engineering-Features** erstellt.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true
```

**Ergebnis:** 68 Features total (2 Basis + 66 Engineering)

**Vorteil:** Maximale Feature-Abdeckung ohne manuelle Auswahl.

---

### Zusammenfassung

| Modus | `use_engineered_features` | Engineering-Features in `features` | Ergebnis |
|-------|---------------------------|-----------------------------------|----------|
| **Keine** | `false` oder weglassen | - | Nur Basis-Features |
| **Spezifische** | `true` | ✅ Ja (z.B. `dev_sold_spike_5`) | Nur die angegebenen Engineering-Features |
| **Alle** | `true` | ❌ Nein | Alle 66 Engineering-Features |

---

### 66 Engineering-Features (mit `use_engineered_features=true`)

#### Dev-Sold Features (6)
```
dev_sold_flag           - Hat der Dev verkauft? (0/1)
dev_sold_cumsum         - Kumulative Dev-Verkäufe
dev_sold_spike_5        - Dev-Verkauf-Spike (5 Min)
dev_sold_spike_10       - Dev-Verkauf-Spike (10 Min)
dev_sold_spike_15       - Dev-Verkauf-Spike (15 Min)
```

#### Buy Pressure Features (6)
```
buy_pressure_ma_5       - Moving Average (5 Min)
buy_pressure_trend_5    - Trend (5 Min)
buy_pressure_ma_10      - Moving Average (10 Min)
buy_pressure_trend_10   - Trend (10 Min)
buy_pressure_ma_15      - Moving Average (15 Min)
buy_pressure_trend_15   - Trend (15 Min)
```

#### Whale Activity Features (4)
```
whale_net_volume        - Netto Whale-Volume
whale_activity_5        - Whale-Aktivität (5 Min)
whale_activity_10       - Whale-Aktivität (10 Min)
whale_activity_15       - Whale-Aktivität (15 Min)
```

#### Volatility Features (6)
```
volatility_ma_5         - Volatilität MA (5 Min)
volatility_spike_5      - Volatilität-Spike (5 Min)
volatility_ma_10        - Volatilität MA (10 Min)
volatility_spike_10     - Volatilität-Spike (10 Min)
volatility_ma_15        - Volatilität MA (15 Min)
volatility_spike_15     - Volatilität-Spike (15 Min)
```

#### Wash Trading Detection (3)
```
wash_trading_flag_5     - Wash Trading erkannt? (5 Min)
wash_trading_flag_10    - Wash Trading erkannt? (10 Min)
wash_trading_flag_15    - Wash Trading erkannt? (15 Min)
```

#### Volume Pattern Features (6)
```
net_volume_ma_5         - Netto-Volume MA (5 Min)
volume_flip_5           - Volume Flip (5 Min)
net_volume_ma_10        - Netto-Volume MA (10 Min)
volume_flip_10          - Volume Flip (10 Min)
net_volume_ma_15        - Netto-Volume MA (15 Min)
volume_flip_15          - Volume Flip (15 Min)
```

#### Price Momentum Features (6)
```
price_change_5          - Preisänderung (5 Min)
price_roc_5             - Rate of Change (5 Min)
price_change_10         - Preisänderung (10 Min)
price_roc_10            - Rate of Change (10 Min)
price_change_15         - Preisänderung (15 Min)
price_roc_15            - Rate of Change (15 Min)
```

#### Market Cap Velocity (3)
```
mcap_velocity_5         - MarketCap Änderungsrate (5 Min)
mcap_velocity_10        - MarketCap Änderungsrate (10 Min)
mcap_velocity_15        - MarketCap Änderungsrate (15 Min)
```

#### ATH Features (19)
```
rolling_ath             - Rolling All-Time-High
price_vs_ath_pct        - Distanz zum ATH in %
ath_breakout            - ATH durchbrochen? (0/1)
minutes_since_ath       - Minuten seit letztem ATH
ath_distance_trend_5    - ATH-Distanz Trend (5 Min)
ath_approach_5          - Nähert sich ATH? (5 Min)
ath_breakout_count_5    - ATH-Durchbrüche (5 Min)
ath_breakout_volume_ma_5 - Volume bei ATH-Breaks (5 Min)
ath_age_trend_5         - ATH-Alter Trend (5 Min)
... (analog für 10 und 15 Minuten)
```

#### Power Features (8)
```
buy_sell_ratio          - Buy/Sell Verhältnis
whale_dominance         - Whale-Anteil am Volume
price_acceleration_5    - Preis-Beschleunigung (5 Min)
price_acceleration_10   - Preis-Beschleunigung (10 Min)
price_acceleration_15   - Preis-Beschleunigung (15 Min)
volume_spike_5          - Volume-Spike (5 Min)
volume_spike_10         - Volume-Spike (10 Min)
volume_spike_15         - Volume-Spike (15 Min)
```

---

## ⚖️ Balance-Optionen

### Das Problem: Unbalancierte Daten

Bei Pump-Detection sind positive Labels (Pumps) sehr selten (oft nur 1-5% der Daten). Das führt dazu, dass Modelle einfach "Nein" für alles vorhersagen.

### Lösung 1: `scale_pos_weight` (✅ EMPFOHLEN)

XGBoost-intern, gewichtet die positive Klasse höher.

| Positive Labels | scale_pos_weight | Effekt |
|-----------------|------------------|--------|
| 0.5% | `200` | Sehr aggressiv |
| 1% | `100` | Standard |
| 2% | `50` | Moderat |
| 5% | `20` | Konservativ |

**Beispiel:**
```bash
scale_pos_weight=100
```

**Vorteile:**
- Keine synthetischen Daten
- Schneller als SMOTE
- Besser generalisierbar

### Lösung 2: `use_smote` (⚠️ Mit Vorsicht)

Synthetisches Oversampling - erstellt künstliche positive Samples.

**Beispiel:**
```bash
use_smote=true
```

**Nachteile:**
- Kann zu Overfitting führen
- Modell lernt synthetische statt echte Muster

### Lösung 3: `class_weight` (für Random Forest)

```bash
class_weight=balanced
```

---

## 📝 Beispiele

### Beispiel 1: Einfaches Pump-Modell

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio&\
future_minutes=5&\
min_percent_change=2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 2: Mit ALLEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 2c: Mit ALLEN Engineering-Features OHNE Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_No_Flags_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=false&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 70 Features (4 Basis + 66 Engineering, keine Flag-Features)

### Beispiel 2b: Mit SPEZIFISCHEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Selective_Engineering_v1&\
model_type=xgboost&\
features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume,volatility_spike_15&\
use_engineered_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 8 Features (2 Basis + 4 Engineering + **4 Flag-Features** - nur die für die ausgewählten Engineering-Features!)

**Wichtig:** Das System verwendet automatisch nur die Flag-Features, die zu den ausgewählten Engineering-Features gehören:
- `dev_sold_spike_5_has_data` (für `dev_sold_spike_5`)
- `buy_pressure_ma_10_has_data` (für `buy_pressure_ma_10`)
- `volatility_spike_15_has_data` (für `volatility_spike_15`)
- `whale_net_volume` hat kein Flag-Feature (ist kein window-basiertes Feature)

### Beispiel 3: OHNE Engineering-Features (nur Basis)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol&\
use_engineered_features=false&\
scale_pos_weight=100&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 5 Features (nur Basis-Features, keine Engineering)

### Beispiel 4: Mit scale_pos_weight (EMPFOHLEN)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Balanced_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 5: ULTIMATIV (Alle Features + Engineering + Flag-Features + Balance)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Ultimate_Pump_Detector&\
model_type=xgboost&\
features=price_open,price_high,price_low,price_close,volume_sol,buy_volume_sol,sell_volume_sol,net_volume_sol,market_cap_close,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct,unique_signer_ratio&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=15&\
direction=up&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 137 Features (14 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 5: Rug-Pull Detection

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Rug_Pull_Detector&\
model_type=xgboost&\
features=price_close,dev_sold_amount,buy_pressure_ratio,whale_sell_volume_sol&\
direction=down&\
min_percent_change=20&\
future_minutes=15&\
scale_pos_weight=50&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 6: Random Forest

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=RF_Pump_Detector&\
model_type=random_forest&\
features=price_close,volume_sol,buy_pressure_ratio&\
class_weight=balanced&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 7: Second Wave Detection (mit Flag-Features)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Second_Wave_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
future_minutes=15&\
min_percent_change=10&\
phases=1,2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 129 Features (6 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 8: Nur Baby Zone (Phase 1)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Baby_Zone_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
phases=1&\
scale_pos_weight=150&\
future_minutes=5&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 9: Survival + Mature Zone (Phase 2+3) mit Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Mature_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
phases=2,3&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=80&\
future_minutes=15&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

---

## 💡 Best Practices

### 1. Feature-Auswahl

| Empfehlung | Beschreibung |
|------------|--------------|
| ✅ Start mit Basis-Features | Beginne mit 5-10 wichtigen Features |
| ✅ Wichtigste Features zuerst | `price_close`, `volume_sol`, `buy_pressure_ratio` |
| ✅ Flag-Features aktivieren | Verbessert Modell-Performance bei neuen Coins |
| ⚠️ Nicht zu viele Features | Mehr als 30 Basis-Features kann zu Overfitting führen |
| ⚠️ Mit Engineering + Flags | Bis zu 150 Features möglich (27 Base + 66 Eng + 57 Flags bei zeitbasierter Vorhersage) oder 151 Features (28 Base + 66 Eng + 57 Flags ohne zeitbasierte Vorhersage) |
| ❌ Keine redundanten Features | z.B. nicht `price_open` UND `price_close` UND `price_high` UND `price_low` |

### 2. Zeithorizont-Wahl

| Zeithorizont | Empfohlene Schwelle | Use Case |
|--------------|---------------------|----------|
| 2-5 Min | 1-3% | Schnelle Scalping-Signale |
| 5-10 Min | 3-10% | Standard Pump Detection |
| 10-15 Min | 5-15% | Second Wave Detection |
| 15-30 Min | 10-25% | Langfristige Trends |

### 3. Balance-Strategie

| Situation | Empfehlung |
|-----------|------------|
| 1% positive Labels | `scale_pos_weight=100` |
| Sehr seltene Events | `scale_pos_weight=200` |
| Mehr Pumps erkennen | Höherer `scale_pos_weight` (mehr Fehlalarme) |
| Weniger Fehlalarme | Niedrigerer `scale_pos_weight` (weniger erkannte Pumps) |

### 4. Trainings-Zeitraum

| Zeitraum | Empfehlung |
|----------|------------|
| **Minimum** | 2 Stunden |
| **Optimal** | 8-12 Stunden |
| **Maximum** | 24+ Stunden (längere Wartezeit) |

---

## 🔧 Troubleshooting

### Problem: F1-Score = 0

**Ursache:** Zu wenig positive Labels oder keine Balance-Strategie.

**Lösung:**
1. Aktiviere `scale_pos_weight=100`
2. ODER senke `min_percent_change`
3. ODER erhöhe `future_minutes`

### Problem: Zu viele Fehlalarme

**Ursache:** `scale_pos_weight` zu hoch.

**Lösung:**
1. Senke `scale_pos_weight` (z.B. von 200 auf 100)
2. ODER erhöhe `min_percent_change`

### Problem: Keine Pumps erkannt

**Ursache:** `scale_pos_weight` zu niedrig oder Feature-Auswahl schlecht.

**Lösung:**
1. Erhöhe `scale_pos_weight` (z.B. auf 200)
2. Füge relevante Features hinzu: `buy_pressure_ratio`, `whale_buy_volume_sol`

### Problem: Training dauert zu lange

**Ursache:** Zu viele Features oder zu großer Zeitraum.

**Lösung:**
1. Reduziere Features auf 10-15
2. Reduziere Trainings-Zeitraum
3. Deaktiviere `use_engineered_features`

### Problem: "Keine Trainingsdaten gefunden"

**Ursache:** Der angegebene Zeitraum enthält keine Daten.

**Lösung:**
1. Prüfe ob der Zeitraum korrekt ist (UTC!)
2. Verwende einen Zeitraum mit bekannten Daten

---

## 📊 Response-Format

### Erfolgreiche Erstellung

```json
{
  "job_id": 424,
  "message": "Job erstellt. Modell 'MyModel' wird trainiert.",
  "status": "PENDING"
}
```

### Job-Status prüfen

```bash
GET /api/queue/{job_id}
```

```json
{
  "id": 424,
  "status": "COMPLETED",
  "result_model_id": 130,
  "progress": 100,
  "progress_msg": "Training abgeschlossen"
}
```

### Modell-Details abrufen

```bash
GET /api/models/{model_id}
```

---

## 🌐 Web UI

Die Web UI bietet dieselben Funktionen mit grafischer Oberfläche:

**URL:** https://test.local.chase295.de/training

Im Schritt 5 "Erweiterte Einstellungen" findest du:
- ⚖️ Klassen-Gewichtung (scale_pos_weight)
- Cross-Validation Einstellungen
- SMOTE Option
- Trainings-Zeitraum

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe die Job-Logs: `GET /api/queue/{job_id}`
2. Prüfe die Modell-Details: `GET /api/models/{model_id}`
3. Sieh dir die Confusion Matrix an für Einblicke in die Performance

---

**Dokumentation erstellt:** Januar 2026  
**Getestet:** 10/10 Tests bestanden ✅


## Vollständige Anleitung zur Modell-Erstellung

**Version:** 1.0  
**Stand:** Januar 2026  
**Endpoint:** `POST /api/models/create/advanced`

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Alle Parameter](#alle-parameter)
3. [Feature-Liste](#feature-liste)
4. [Balance-Optionen](#balance-optionen)
5. [Beispiele](#beispiele)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Der `/models/create/advanced` Endpoint ist der **vollständigste und flexibelste** Endpoint zur Erstellung von ML-Modellen für Pump-Detection.

### Was kann dieser Endpoint?

| Funktion | Beschreibung |
|----------|--------------|
| ✅ **Zeitbasierte Vorhersage** | "Steigt der Preis um X% in Y Minuten?" |
| ✅ **Feature Engineering** | 66 zusätzliche berechnete Features |
| ✅ **SMOTE** | Synthetisches Oversampling für unbalancierte Daten |
| ✅ **scale_pos_weight** | XGBoost-interne Klassen-Gewichtung |
| ✅ **Flexible Zeithorizonte** | 1 Minute bis 60+ Minuten |
| ✅ **Pump & Rug Detection** | Steigende oder fallende Preise vorhersagen |
| ✅ **Zwei Modell-Typen** | XGBoost und Random Forest |

---

## 📊 Alle Parameter

### Pflicht-Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `name` | string | Eindeutiger Modell-Name | `"Pump_Detector_v1"` |
| `model_type` | string | `xgboost` oder `random_forest` | `"xgboost"` |
| `features` | string | Komma-separierte Feature-Liste | `"price_close,volume_sol"` |
| `train_start` | string | Trainings-Startzeit (UTC, ISO-Format) | `"2026-01-07T06:00:00Z"` |
| `train_end` | string | Trainings-Endzeit (UTC, ISO-Format) | `"2026-01-07T18:00:00Z"` |

### Optionale Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `target_var` | string | `"price_close"` | Ziel-Variable für Vorhersage |
| `use_time_based_prediction` | bool | `true` | Zeitbasierte Vorhersage aktivieren |
| `future_minutes` | int | `5` | Vorhersage-Horizont in Minuten |
| `min_percent_change` | float | `2.0` | Minimale Preisänderung in % |
| `direction` | string | `"up"` | `"up"` für Pump, `"down"` für Rug |
| `use_engineered_features` | bool | `false` | Feature Engineering aktivieren (siehe [Feature Engineering Optionen](#feature-engineering-optionen)) |
| `use_flag_features` | bool | `true` | **NEU!** Flag-Features aktivieren (siehe [Flag-Features](#flag-features)) |
| `use_smote` | bool | `false` | SMOTE aktivieren |
| `scale_pos_weight` | float | `null` | XGBoost Klassen-Gewichtung |
| `class_weight` | string | `null` | `"balanced"` für Random Forest |
| `phases` | string | `null` | **NEU!** Coin-Phasen Filter (z.B. `"1,2,3"`) |

---

## 🔄 Coin-Phasen Filter (NEU!)

Mit dem `phases` Parameter kannst du das Training auf **bestimmte Coin-Entwicklungsphasen** beschränken.

### Verfügbare Phasen

| Phase ID | Name | Beschreibung | Alter |
|----------|------|--------------|-------|
| **1** | Baby Zone | Frisch erstellte Coins | 0-10 Min |
| **2** | Survival Zone | Überlebende Coins | 10-120 Min |
| **3** | Mature Zone | Reife Coins | 2-4 Stunden |
| **99** | Finished | Abgeschlossene Coins | - |
| **100** | Graduated | Graduierte Coins | - |

### Beispiele

```bash
# Nur Baby & Survival Zone (Phase 1 + 2)
phases=1,2

# Nur Mature Zone (Phase 3)
phases=3

# Alle aktiven Phasen (1, 2, 3)
phases=1,2,3
```

### Warum Phasen filtern?

| Use Case | Empfohlene Phasen | Grund |
|----------|-------------------|-------|
| **Second Wave Detection** | `1,2` | Pumps passieren früh |
| **Langfristige Trends** | `2,3` | Stabile Datenmuster |
| **Rug-Pull Detection** | `1` | Rugs passieren in Phase 1 |
| **Allgemein** | `1,2,3` | Maximale Datenmenge |

---

## 📊 Feature-Liste

### 28 Basis-Features (immer verfügbar)

⚠️ **WICHTIG:** Bei zeitbasierter Vorhersage wird `price_close` automatisch aus den Trainings-Features entfernt (verhindert Data Leakage). In diesem Fall sind es **27 Basis-Features** im Training.

#### Preis-Features (4)
```
price_open      - Eröffnungspreis der Minute
price_high      - Höchster Preis der Minute
price_low       - Niedrigster Preis der Minute
price_close     - Schlusskurs der Minute
```

#### Volume-Features (4)
```
volume_sol          - Gesamtes Handelsvolumen in SOL
buy_volume_sol      - Kaufvolumen in SOL
sell_volume_sol     - Verkaufsvolumen in SOL
net_volume_sol      - Netto-Volumen (Buy - Sell)
```

#### Market-Features (4)
```
market_cap_close        - Marktkapitalisierung
bonding_curve_pct       - Position auf der Bonding Curve (%)
virtual_sol_reserves    - Virtuelle SOL-Reserven
is_koth                 - King of the Hill Status (0/1)
```

#### Trade-Statistiken (4)
```
num_buys            - Anzahl Buy-Trades
num_sells           - Anzahl Sell-Trades
unique_wallets      - Einzigartige Wallet-Adressen
num_micro_trades    - Anzahl Mikro-Trades
```

#### Max Trade Sizes (2)
```
max_single_buy_sol      - Größter einzelner Kauf
max_single_sell_sol     - Größter einzelner Verkauf
```

#### Whale-Features (4)
```
whale_buy_volume_sol    - Whale-Kaufvolumen
whale_sell_volume_sol   - Whale-Verkaufsvolumen
num_whale_buys          - Anzahl Whale-Käufe
num_whale_sells         - Anzahl Whale-Verkäufe
```

#### Qualitäts-Features (4)
```
dev_sold_amount     - Vom Developer verkaufte Menge
volatility_pct      - Preisvolatilität in %
avg_trade_size_sol  - Durchschnittliche Trade-Größe
buy_pressure_ratio  - Kaufdruck-Verhältnis (0-1)
```

#### Wallet-Analyse (2)
```
unique_signer_ratio     - Verhältnis einzigartiger Signaturen
phase_id_at_time        - Coin-Phase (1-6)
```

---

## 🚩 Flag-Features (NEU!)

Flag-Features sind **Datenverfügbarkeits-Indikatoren**, die dem Modell anzeigen, ob ein Engineering-Feature genug historische Daten hat, um zuverlässig berechnet zu werden.

### Was sind Flag-Features?

Jedes window-basierte Engineering-Feature (z.B. `buy_pressure_ma_5`) erhält ein entsprechendes Flag-Feature (z.B. `buy_pressure_ma_5_has_data`), das anzeigt:
- **`1`** = Genug Daten vorhanden (Feature ist zuverlässig)
- **`0`** = Nicht genug Daten (Feature könnte unzuverlässig sein)

### Warum Flag-Features?

| Problem | Lösung mit Flag-Features |
|---------|-------------------------|
| Neue Coins haben keine 15-Minuten-Historie | Modell lernt, dass `buy_pressure_ma_15_has_data=0` bedeutet: Feature ignorieren |
| NaN-Werte in Engineering-Features | Flag zeigt dem Modell, ob NaN = "keine Daten" oder "echter Wert" |
| Unzuverlässige Features bei jungen Coins | Modell kann Features basierend auf Datenverfügbarkeit gewichten |

### Aktivierung

Flag-Features werden automatisch aktiviert, wenn:
1. `use_engineered_features=true` **UND**
2. `use_flag_features=true` (Default: `true`)

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering + **57 Flag-Features = 150 Features total**

### Deaktivierung

Wenn du Flag-Features nicht möchtest:
```bash
use_flag_features=false
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering = 93 Features total (ohne Flags)

---

## 🚩 Alle 57 Flag-Features

### Dev-Sold Flag-Features (3)
```
dev_sold_spike_5_has_data      - Hat Coin genug Daten für Dev-Sold Spike (5 Min)?
dev_sold_spike_10_has_data     - Hat Coin genug Daten für Dev-Sold Spike (10 Min)?
dev_sold_spike_15_has_data     - Hat Coin genug Daten für Dev-Sold Spike (15 Min)?
```

### Buy Pressure Flag-Features (6)
```
buy_pressure_ma_5_has_data     - Hat Coin genug Daten für Buy Pressure MA (5 Min)?
buy_pressure_ma_10_has_data   - Hat Coin genug Daten für Buy Pressure MA (10 Min)?
buy_pressure_ma_15_has_data   - Hat Coin genug Daten für Buy Pressure MA (15 Min)?
buy_pressure_trend_5_has_data  - Hat Coin genug Daten für Buy Pressure Trend (5 Min)?
buy_pressure_trend_10_has_data - Hat Coin genug Daten für Buy Pressure Trend (10 Min)?
buy_pressure_trend_15_has_data - Hat Coin genug Daten für Buy Pressure Trend (15 Min)?
```

### Whale Activity Flag-Features (3)
```
whale_activity_5_has_data      - Hat Coin genug Daten für Whale Activity (5 Min)?
whale_activity_10_has_data    - Hat Coin genug Daten für Whale Activity (10 Min)?
whale_activity_15_has_data    - Hat Coin genug Daten für Whale Activity (15 Min)?
```

### Volatility Flag-Features (6)
```
volatility_ma_5_has_data      - Hat Coin genug Daten für Volatility MA (5 Min)?
volatility_ma_10_has_data    - Hat Coin genug Daten für Volatility MA (10 Min)?
volatility_ma_15_has_data    - Hat Coin genug Daten für Volatility MA (15 Min)?
volatility_spike_5_has_data   - Hat Coin genug Daten für Volatility Spike (5 Min)?
volatility_spike_10_has_data - Hat Coin genug Daten für Volatility Spike (10 Min)?
volatility_spike_15_has_data - Hat Coin genug Daten für Volatility Spike (15 Min)?
```

### Wash Trading Flag-Features (3)
```
wash_trading_flag_5_has_data  - Hat Coin genug Daten für Wash Trading Detection (5 Min)?
wash_trading_flag_10_has_data - Hat Coin genug Daten für Wash Trading Detection (10 Min)?
wash_trading_flag_15_has_data - Hat Coin genug Daten für Wash Trading Detection (15 Min)?
```

### Volume Pattern Flag-Features (6)
```
net_volume_ma_5_has_data      - Hat Coin genug Daten für Net Volume MA (5 Min)?
net_volume_ma_10_has_data    - Hat Coin genug Daten für Net Volume MA (10 Min)?
net_volume_ma_15_has_data    - Hat Coin genug Daten für Net Volume MA (15 Min)?
volume_flip_5_has_data       - Hat Coin genug Daten für Volume Flip (5 Min)?
volume_flip_10_has_data      - Hat Coin genug Daten für Volume Flip (10 Min)?
volume_flip_15_has_data      - Hat Coin genug Daten für Volume Flip (15 Min)?
```

### Price Momentum Flag-Features (6)
```
price_change_5_has_data      - Hat Coin genug Daten für Price Change (5 Min)?
price_change_10_has_data    - Hat Coin genug Daten für Price Change (10 Min)?
price_change_15_has_data    - Hat Coin genug Daten für Price Change (15 Min)?
price_roc_5_has_data         - Hat Coin genug Daten für Price ROC (5 Min)?
price_roc_10_has_data        - Hat Coin genug Daten für Price ROC (10 Min)?
price_roc_15_has_data        - Hat Coin genug Daten für Price ROC (15 Min)?
```

### Price Acceleration Flag-Features (3)
```
price_acceleration_5_has_data  - Hat Coin genug Daten für Price Acceleration (5 Min)?
price_acceleration_10_has_data - Hat Coin genug Daten für Price Acceleration (10 Min)?
price_acceleration_15_has_data - Hat Coin genug Daten für Price Acceleration (15 Min)?
```

### Market Cap Velocity Flag-Features (3)
```
mcap_velocity_5_has_data      - Hat Coin genug Daten für Market Cap Velocity (5 Min)?
mcap_velocity_10_has_data    - Hat Coin genug Daten für Market Cap Velocity (10 Min)?
mcap_velocity_15_has_data    - Hat Coin genug Daten für Market Cap Velocity (15 Min)?
```

### ATH Flag-Features (15)
```
ath_distance_trend_5_has_data         - Hat Coin genug Daten für ATH Distance Trend (5 Min)?
ath_distance_trend_10_has_data        - Hat Coin genug Daten für ATH Distance Trend (10 Min)?
ath_distance_trend_15_has_data       - Hat Coin genug Daten für ATH Distance Trend (15 Min)?
ath_approach_5_has_data              - Hat Coin genug Daten für ATH Approach (5 Min)?
ath_approach_10_has_data             - Hat Coin genug Daten für ATH Approach (10 Min)?
ath_approach_15_has_data             - Hat Coin genug Daten für ATH Approach (15 Min)?
ath_breakout_count_5_has_data         - Hat Coin genug Daten für ATH Breakout Count (5 Min)?
ath_breakout_count_10_has_data       - Hat Coin genug Daten für ATH Breakout Count (10 Min)?
ath_breakout_count_15_has_data       - Hat Coin genug Daten für ATH Breakout Count (15 Min)?
ath_breakout_volume_ma_5_has_data     - Hat Coin genug Daten für ATH Breakout Volume MA (5 Min)?
ath_breakout_volume_ma_10_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (10 Min)?
ath_breakout_volume_ma_15_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (15 Min)?
ath_age_trend_5_has_data             - Hat Coin genug Daten für ATH Age Trend (5 Min)?
ath_age_trend_10_has_data            - Hat Coin genug Daten für ATH Age Trend (10 Min)?
ath_age_trend_15_has_data            - Hat Coin genug Daten für ATH Age Trend (15 Min)?
```

### Volume Spike Flag-Features (3)
```
volume_spike_5_has_data      - Hat Coin genug Daten für Volume Spike (5 Min)?
volume_spike_10_has_data    - Hat Coin genug Daten für Volume Spike (10 Min)?
volume_spike_15_has_data    - Hat Coin genug Daten für Volume Spike (15 Min)?
```

### Zusammenfassung Flag-Features

| Kategorie | Anzahl | Window-Größen |
|-----------|--------|---------------|
| Dev-Sold | 3 | 5, 10, 15 Min |
| Buy Pressure | 6 | 5, 10, 15 Min (MA + Trend) |
| Whale Activity | 3 | 5, 10, 15 Min |
| Volatility | 6 | 5, 10, 15 Min (MA + Spike) |
| Wash Trading | 3 | 5, 10, 15 Min |
| Volume Pattern | 6 | 5, 10, 15 Min (Net Volume MA + Volume Flip) |
| Price Momentum | 6 | 5, 10, 15 Min (Change + ROC) |
| Price Acceleration | 3 | 5, 10, 15 Min |
| Market Cap Velocity | 3 | 5, 10, 15 Min |
| ATH Features | 15 | 5, 10, 15 Min (5 verschiedene ATH-Features) |
| Volume Spike | 3 | 5, 10, 15 Min |
| **GESAMT** | **57** | - |

---

## 🔧 Feature Engineering Optionen

Der `use_engineered_features` Parameter bietet **3 verschiedene Modi**:

### Option 1: Keine Engineering-Features (Default)

**Verhalten:** Nur die Basis-Features werden verwendet, die du in der `features` Liste angibst.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&
  use_engineered_features=false
  # oder einfach weglassen (Default ist false)
```

**Ergebnis:** 4 Features total (nur Basis-Features)

---

### Option 2: Spezifische Engineering-Features auswählen

**Verhalten:** Du gibst explizit Engineering-Features in der `features` Liste an. Das Backend erstellt nur diese.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume&
  use_engineered_features=true
```

**Ergebnis:** 5 Features total (2 Basis + 3 Engineering)

**Vorteil:** Du hast volle Kontrolle über welche Engineering-Features verwendet werden.

---

### Option 3: Alle Engineering-Features (66 Stück)

**Verhalten:** Wenn `use_engineered_features=true` ist, aber **keine** Engineering-Features in der `features` Liste stehen, werden automatisch **alle 66 Engineering-Features** erstellt.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true
```

**Ergebnis:** 68 Features total (2 Basis + 66 Engineering)

**Vorteil:** Maximale Feature-Abdeckung ohne manuelle Auswahl.

---

### Zusammenfassung

| Modus | `use_engineered_features` | Engineering-Features in `features` | Ergebnis |
|-------|---------------------------|-----------------------------------|----------|
| **Keine** | `false` oder weglassen | - | Nur Basis-Features |
| **Spezifische** | `true` | ✅ Ja (z.B. `dev_sold_spike_5`) | Nur die angegebenen Engineering-Features |
| **Alle** | `true` | ❌ Nein | Alle 66 Engineering-Features |

---

### 66 Engineering-Features (mit `use_engineered_features=true`)

#### Dev-Sold Features (6)
```
dev_sold_flag           - Hat der Dev verkauft? (0/1)
dev_sold_cumsum         - Kumulative Dev-Verkäufe
dev_sold_spike_5        - Dev-Verkauf-Spike (5 Min)
dev_sold_spike_10       - Dev-Verkauf-Spike (10 Min)
dev_sold_spike_15       - Dev-Verkauf-Spike (15 Min)
```

#### Buy Pressure Features (6)
```
buy_pressure_ma_5       - Moving Average (5 Min)
buy_pressure_trend_5    - Trend (5 Min)
buy_pressure_ma_10      - Moving Average (10 Min)
buy_pressure_trend_10   - Trend (10 Min)
buy_pressure_ma_15      - Moving Average (15 Min)
buy_pressure_trend_15   - Trend (15 Min)
```

#### Whale Activity Features (4)
```
whale_net_volume        - Netto Whale-Volume
whale_activity_5        - Whale-Aktivität (5 Min)
whale_activity_10       - Whale-Aktivität (10 Min)
whale_activity_15       - Whale-Aktivität (15 Min)
```

#### Volatility Features (6)
```
volatility_ma_5         - Volatilität MA (5 Min)
volatility_spike_5      - Volatilität-Spike (5 Min)
volatility_ma_10        - Volatilität MA (10 Min)
volatility_spike_10     - Volatilität-Spike (10 Min)
volatility_ma_15        - Volatilität MA (15 Min)
volatility_spike_15     - Volatilität-Spike (15 Min)
```

#### Wash Trading Detection (3)
```
wash_trading_flag_5     - Wash Trading erkannt? (5 Min)
wash_trading_flag_10    - Wash Trading erkannt? (10 Min)
wash_trading_flag_15    - Wash Trading erkannt? (15 Min)
```

#### Volume Pattern Features (6)
```
net_volume_ma_5         - Netto-Volume MA (5 Min)
volume_flip_5           - Volume Flip (5 Min)
net_volume_ma_10        - Netto-Volume MA (10 Min)
volume_flip_10          - Volume Flip (10 Min)
net_volume_ma_15        - Netto-Volume MA (15 Min)
volume_flip_15          - Volume Flip (15 Min)
```

#### Price Momentum Features (6)
```
price_change_5          - Preisänderung (5 Min)
price_roc_5             - Rate of Change (5 Min)
price_change_10         - Preisänderung (10 Min)
price_roc_10            - Rate of Change (10 Min)
price_change_15         - Preisänderung (15 Min)
price_roc_15            - Rate of Change (15 Min)
```

#### Market Cap Velocity (3)
```
mcap_velocity_5         - MarketCap Änderungsrate (5 Min)
mcap_velocity_10        - MarketCap Änderungsrate (10 Min)
mcap_velocity_15        - MarketCap Änderungsrate (15 Min)
```

#### ATH Features (19)
```
rolling_ath             - Rolling All-Time-High
price_vs_ath_pct        - Distanz zum ATH in %
ath_breakout            - ATH durchbrochen? (0/1)
minutes_since_ath       - Minuten seit letztem ATH
ath_distance_trend_5    - ATH-Distanz Trend (5 Min)
ath_approach_5          - Nähert sich ATH? (5 Min)
ath_breakout_count_5    - ATH-Durchbrüche (5 Min)
ath_breakout_volume_ma_5 - Volume bei ATH-Breaks (5 Min)
ath_age_trend_5         - ATH-Alter Trend (5 Min)
... (analog für 10 und 15 Minuten)
```

#### Power Features (8)
```
buy_sell_ratio          - Buy/Sell Verhältnis
whale_dominance         - Whale-Anteil am Volume
price_acceleration_5    - Preis-Beschleunigung (5 Min)
price_acceleration_10   - Preis-Beschleunigung (10 Min)
price_acceleration_15   - Preis-Beschleunigung (15 Min)
volume_spike_5          - Volume-Spike (5 Min)
volume_spike_10         - Volume-Spike (10 Min)
volume_spike_15         - Volume-Spike (15 Min)
```

---

## ⚖️ Balance-Optionen

### Das Problem: Unbalancierte Daten

Bei Pump-Detection sind positive Labels (Pumps) sehr selten (oft nur 1-5% der Daten). Das führt dazu, dass Modelle einfach "Nein" für alles vorhersagen.

### Lösung 1: `scale_pos_weight` (✅ EMPFOHLEN)

XGBoost-intern, gewichtet die positive Klasse höher.

| Positive Labels | scale_pos_weight | Effekt |
|-----------------|------------------|--------|
| 0.5% | `200` | Sehr aggressiv |
| 1% | `100` | Standard |
| 2% | `50` | Moderat |
| 5% | `20` | Konservativ |

**Beispiel:**
```bash
scale_pos_weight=100
```

**Vorteile:**
- Keine synthetischen Daten
- Schneller als SMOTE
- Besser generalisierbar

### Lösung 2: `use_smote` (⚠️ Mit Vorsicht)

Synthetisches Oversampling - erstellt künstliche positive Samples.

**Beispiel:**
```bash
use_smote=true
```

**Nachteile:**
- Kann zu Overfitting führen
- Modell lernt synthetische statt echte Muster

### Lösung 3: `class_weight` (für Random Forest)

```bash
class_weight=balanced
```

---

## 📝 Beispiele

### Beispiel 1: Einfaches Pump-Modell

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio&\
future_minutes=5&\
min_percent_change=2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 2: Mit ALLEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 2c: Mit ALLEN Engineering-Features OHNE Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_No_Flags_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=false&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 70 Features (4 Basis + 66 Engineering, keine Flag-Features)

### Beispiel 2b: Mit SPEZIFISCHEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Selective_Engineering_v1&\
model_type=xgboost&\
features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume,volatility_spike_15&\
use_engineered_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 8 Features (2 Basis + 4 Engineering + **4 Flag-Features** - nur die für die ausgewählten Engineering-Features!)

**Wichtig:** Das System verwendet automatisch nur die Flag-Features, die zu den ausgewählten Engineering-Features gehören:
- `dev_sold_spike_5_has_data` (für `dev_sold_spike_5`)
- `buy_pressure_ma_10_has_data` (für `buy_pressure_ma_10`)
- `volatility_spike_15_has_data` (für `volatility_spike_15`)
- `whale_net_volume` hat kein Flag-Feature (ist kein window-basiertes Feature)

### Beispiel 3: OHNE Engineering-Features (nur Basis)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol&\
use_engineered_features=false&\
scale_pos_weight=100&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 5 Features (nur Basis-Features, keine Engineering)

### Beispiel 4: Mit scale_pos_weight (EMPFOHLEN)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Balanced_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 5: ULTIMATIV (Alle Features + Engineering + Flag-Features + Balance)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Ultimate_Pump_Detector&\
model_type=xgboost&\
features=price_open,price_high,price_low,price_close,volume_sol,buy_volume_sol,sell_volume_sol,net_volume_sol,market_cap_close,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct,unique_signer_ratio&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=15&\
direction=up&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 137 Features (14 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 5: Rug-Pull Detection

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Rug_Pull_Detector&\
model_type=xgboost&\
features=price_close,dev_sold_amount,buy_pressure_ratio,whale_sell_volume_sol&\
direction=down&\
min_percent_change=20&\
future_minutes=15&\
scale_pos_weight=50&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 6: Random Forest

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=RF_Pump_Detector&\
model_type=random_forest&\
features=price_close,volume_sol,buy_pressure_ratio&\
class_weight=balanced&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 7: Second Wave Detection (mit Flag-Features)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Second_Wave_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
future_minutes=15&\
min_percent_change=10&\
phases=1,2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 129 Features (6 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 8: Nur Baby Zone (Phase 1)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Baby_Zone_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
phases=1&\
scale_pos_weight=150&\
future_minutes=5&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 9: Survival + Mature Zone (Phase 2+3) mit Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Mature_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
phases=2,3&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=80&\
future_minutes=15&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

---

## 💡 Best Practices

### 1. Feature-Auswahl

| Empfehlung | Beschreibung |
|------------|--------------|
| ✅ Start mit Basis-Features | Beginne mit 5-10 wichtigen Features |
| ✅ Wichtigste Features zuerst | `price_close`, `volume_sol`, `buy_pressure_ratio` |
| ✅ Flag-Features aktivieren | Verbessert Modell-Performance bei neuen Coins |
| ⚠️ Nicht zu viele Features | Mehr als 30 Basis-Features kann zu Overfitting führen |
| ⚠️ Mit Engineering + Flags | Bis zu 150 Features möglich (27 Base + 66 Eng + 57 Flags bei zeitbasierter Vorhersage) oder 151 Features (28 Base + 66 Eng + 57 Flags ohne zeitbasierte Vorhersage) |
| ❌ Keine redundanten Features | z.B. nicht `price_open` UND `price_close` UND `price_high` UND `price_low` |

### 2. Zeithorizont-Wahl

| Zeithorizont | Empfohlene Schwelle | Use Case |
|--------------|---------------------|----------|
| 2-5 Min | 1-3% | Schnelle Scalping-Signale |
| 5-10 Min | 3-10% | Standard Pump Detection |
| 10-15 Min | 5-15% | Second Wave Detection |
| 15-30 Min | 10-25% | Langfristige Trends |

### 3. Balance-Strategie

| Situation | Empfehlung |
|-----------|------------|
| 1% positive Labels | `scale_pos_weight=100` |
| Sehr seltene Events | `scale_pos_weight=200` |
| Mehr Pumps erkennen | Höherer `scale_pos_weight` (mehr Fehlalarme) |
| Weniger Fehlalarme | Niedrigerer `scale_pos_weight` (weniger erkannte Pumps) |

### 4. Trainings-Zeitraum

| Zeitraum | Empfehlung |
|----------|------------|
| **Minimum** | 2 Stunden |
| **Optimal** | 8-12 Stunden |
| **Maximum** | 24+ Stunden (längere Wartezeit) |

---

## 🔧 Troubleshooting

### Problem: F1-Score = 0

**Ursache:** Zu wenig positive Labels oder keine Balance-Strategie.

**Lösung:**
1. Aktiviere `scale_pos_weight=100`
2. ODER senke `min_percent_change`
3. ODER erhöhe `future_minutes`

### Problem: Zu viele Fehlalarme

**Ursache:** `scale_pos_weight` zu hoch.

**Lösung:**
1. Senke `scale_pos_weight` (z.B. von 200 auf 100)
2. ODER erhöhe `min_percent_change`

### Problem: Keine Pumps erkannt

**Ursache:** `scale_pos_weight` zu niedrig oder Feature-Auswahl schlecht.

**Lösung:**
1. Erhöhe `scale_pos_weight` (z.B. auf 200)
2. Füge relevante Features hinzu: `buy_pressure_ratio`, `whale_buy_volume_sol`

### Problem: Training dauert zu lange

**Ursache:** Zu viele Features oder zu großer Zeitraum.

**Lösung:**
1. Reduziere Features auf 10-15
2. Reduziere Trainings-Zeitraum
3. Deaktiviere `use_engineered_features`

### Problem: "Keine Trainingsdaten gefunden"

**Ursache:** Der angegebene Zeitraum enthält keine Daten.

**Lösung:**
1. Prüfe ob der Zeitraum korrekt ist (UTC!)
2. Verwende einen Zeitraum mit bekannten Daten

---

## 📊 Response-Format

### Erfolgreiche Erstellung

```json
{
  "job_id": 424,
  "message": "Job erstellt. Modell 'MyModel' wird trainiert.",
  "status": "PENDING"
}
```

### Job-Status prüfen

```bash
GET /api/queue/{job_id}
```

```json
{
  "id": 424,
  "status": "COMPLETED",
  "result_model_id": 130,
  "progress": 100,
  "progress_msg": "Training abgeschlossen"
}
```

### Modell-Details abrufen

```bash
GET /api/models/{model_id}
```

---

## 🌐 Web UI

Die Web UI bietet dieselben Funktionen mit grafischer Oberfläche:

**URL:** https://test.local.chase295.de/training

Im Schritt 5 "Erweiterte Einstellungen" findest du:
- ⚖️ Klassen-Gewichtung (scale_pos_weight)
- Cross-Validation Einstellungen
- SMOTE Option
- Trainings-Zeitraum

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe die Job-Logs: `GET /api/queue/{job_id}`
2. Prüfe die Modell-Details: `GET /api/models/{model_id}`
3. Sieh dir die Confusion Matrix an für Einblicke in die Performance

---

**Dokumentation erstellt:** Januar 2026  
**Getestet:** 10/10 Tests bestanden ✅


## Vollständige Anleitung zur Modell-Erstellung

**Version:** 1.0  
**Stand:** Januar 2026  
**Endpoint:** `POST /api/models/create/advanced`

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Alle Parameter](#alle-parameter)
3. [Feature-Liste](#feature-liste)
4. [Balance-Optionen](#balance-optionen)
5. [Beispiele](#beispiele)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Der `/models/create/advanced` Endpoint ist der **vollständigste und flexibelste** Endpoint zur Erstellung von ML-Modellen für Pump-Detection.

### Was kann dieser Endpoint?

| Funktion | Beschreibung |
|----------|--------------|
| ✅ **Zeitbasierte Vorhersage** | "Steigt der Preis um X% in Y Minuten?" |
| ✅ **Feature Engineering** | 66 zusätzliche berechnete Features |
| ✅ **SMOTE** | Synthetisches Oversampling für unbalancierte Daten |
| ✅ **scale_pos_weight** | XGBoost-interne Klassen-Gewichtung |
| ✅ **Flexible Zeithorizonte** | 1 Minute bis 60+ Minuten |
| ✅ **Pump & Rug Detection** | Steigende oder fallende Preise vorhersagen |
| ✅ **Zwei Modell-Typen** | XGBoost und Random Forest |

---

## 📊 Alle Parameter

### Pflicht-Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `name` | string | Eindeutiger Modell-Name | `"Pump_Detector_v1"` |
| `model_type` | string | `xgboost` oder `random_forest` | `"xgboost"` |
| `features` | string | Komma-separierte Feature-Liste | `"price_close,volume_sol"` |
| `train_start` | string | Trainings-Startzeit (UTC, ISO-Format) | `"2026-01-07T06:00:00Z"` |
| `train_end` | string | Trainings-Endzeit (UTC, ISO-Format) | `"2026-01-07T18:00:00Z"` |

### Optionale Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `target_var` | string | `"price_close"` | Ziel-Variable für Vorhersage |
| `use_time_based_prediction` | bool | `true` | Zeitbasierte Vorhersage aktivieren |
| `future_minutes` | int | `5` | Vorhersage-Horizont in Minuten |
| `min_percent_change` | float | `2.0` | Minimale Preisänderung in % |
| `direction` | string | `"up"` | `"up"` für Pump, `"down"` für Rug |
| `use_engineered_features` | bool | `false` | Feature Engineering aktivieren (siehe [Feature Engineering Optionen](#feature-engineering-optionen)) |
| `use_flag_features` | bool | `true` | **NEU!** Flag-Features aktivieren (siehe [Flag-Features](#flag-features)) |
| `use_smote` | bool | `false` | SMOTE aktivieren |
| `scale_pos_weight` | float | `null` | XGBoost Klassen-Gewichtung |
| `class_weight` | string | `null` | `"balanced"` für Random Forest |
| `phases` | string | `null` | **NEU!** Coin-Phasen Filter (z.B. `"1,2,3"`) |

---

## 🔄 Coin-Phasen Filter (NEU!)

Mit dem `phases` Parameter kannst du das Training auf **bestimmte Coin-Entwicklungsphasen** beschränken.

### Verfügbare Phasen

| Phase ID | Name | Beschreibung | Alter |
|----------|------|--------------|-------|
| **1** | Baby Zone | Frisch erstellte Coins | 0-10 Min |
| **2** | Survival Zone | Überlebende Coins | 10-120 Min |
| **3** | Mature Zone | Reife Coins | 2-4 Stunden |
| **99** | Finished | Abgeschlossene Coins | - |
| **100** | Graduated | Graduierte Coins | - |

### Beispiele

```bash
# Nur Baby & Survival Zone (Phase 1 + 2)
phases=1,2

# Nur Mature Zone (Phase 3)
phases=3

# Alle aktiven Phasen (1, 2, 3)
phases=1,2,3
```

### Warum Phasen filtern?

| Use Case | Empfohlene Phasen | Grund |
|----------|-------------------|-------|
| **Second Wave Detection** | `1,2` | Pumps passieren früh |
| **Langfristige Trends** | `2,3` | Stabile Datenmuster |
| **Rug-Pull Detection** | `1` | Rugs passieren in Phase 1 |
| **Allgemein** | `1,2,3` | Maximale Datenmenge |

---

## 📊 Feature-Liste

### 28 Basis-Features (immer verfügbar)

⚠️ **WICHTIG:** Bei zeitbasierter Vorhersage wird `price_close` automatisch aus den Trainings-Features entfernt (verhindert Data Leakage). In diesem Fall sind es **27 Basis-Features** im Training.

#### Preis-Features (4)
```
price_open      - Eröffnungspreis der Minute
price_high      - Höchster Preis der Minute
price_low       - Niedrigster Preis der Minute
price_close     - Schlusskurs der Minute
```

#### Volume-Features (4)
```
volume_sol          - Gesamtes Handelsvolumen in SOL
buy_volume_sol      - Kaufvolumen in SOL
sell_volume_sol     - Verkaufsvolumen in SOL
net_volume_sol      - Netto-Volumen (Buy - Sell)
```

#### Market-Features (4)
```
market_cap_close        - Marktkapitalisierung
bonding_curve_pct       - Position auf der Bonding Curve (%)
virtual_sol_reserves    - Virtuelle SOL-Reserven
is_koth                 - King of the Hill Status (0/1)
```

#### Trade-Statistiken (4)
```
num_buys            - Anzahl Buy-Trades
num_sells           - Anzahl Sell-Trades
unique_wallets      - Einzigartige Wallet-Adressen
num_micro_trades    - Anzahl Mikro-Trades
```

#### Max Trade Sizes (2)
```
max_single_buy_sol      - Größter einzelner Kauf
max_single_sell_sol     - Größter einzelner Verkauf
```

#### Whale-Features (4)
```
whale_buy_volume_sol    - Whale-Kaufvolumen
whale_sell_volume_sol   - Whale-Verkaufsvolumen
num_whale_buys          - Anzahl Whale-Käufe
num_whale_sells         - Anzahl Whale-Verkäufe
```

#### Qualitäts-Features (4)
```
dev_sold_amount     - Vom Developer verkaufte Menge
volatility_pct      - Preisvolatilität in %
avg_trade_size_sol  - Durchschnittliche Trade-Größe
buy_pressure_ratio  - Kaufdruck-Verhältnis (0-1)
```

#### Wallet-Analyse (2)
```
unique_signer_ratio     - Verhältnis einzigartiger Signaturen
phase_id_at_time        - Coin-Phase (1-6)
```

---

## 🚩 Flag-Features (NEU!)

Flag-Features sind **Datenverfügbarkeits-Indikatoren**, die dem Modell anzeigen, ob ein Engineering-Feature genug historische Daten hat, um zuverlässig berechnet zu werden.

### Was sind Flag-Features?

Jedes window-basierte Engineering-Feature (z.B. `buy_pressure_ma_5`) erhält ein entsprechendes Flag-Feature (z.B. `buy_pressure_ma_5_has_data`), das anzeigt:
- **`1`** = Genug Daten vorhanden (Feature ist zuverlässig)
- **`0`** = Nicht genug Daten (Feature könnte unzuverlässig sein)

### Warum Flag-Features?

| Problem | Lösung mit Flag-Features |
|---------|-------------------------|
| Neue Coins haben keine 15-Minuten-Historie | Modell lernt, dass `buy_pressure_ma_15_has_data=0` bedeutet: Feature ignorieren |
| NaN-Werte in Engineering-Features | Flag zeigt dem Modell, ob NaN = "keine Daten" oder "echter Wert" |
| Unzuverlässige Features bei jungen Coins | Modell kann Features basierend auf Datenverfügbarkeit gewichten |

### Aktivierung

Flag-Features werden automatisch aktiviert, wenn:
1. `use_engineered_features=true` **UND**
2. `use_flag_features=true` (Default: `true`)

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering + **57 Flag-Features = 150 Features total**

### Deaktivierung

Wenn du Flag-Features nicht möchtest:
```bash
use_flag_features=false
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering = 93 Features total (ohne Flags)

---

## 🚩 Alle 57 Flag-Features

### Dev-Sold Flag-Features (3)
```
dev_sold_spike_5_has_data      - Hat Coin genug Daten für Dev-Sold Spike (5 Min)?
dev_sold_spike_10_has_data     - Hat Coin genug Daten für Dev-Sold Spike (10 Min)?
dev_sold_spike_15_has_data     - Hat Coin genug Daten für Dev-Sold Spike (15 Min)?
```

### Buy Pressure Flag-Features (6)
```
buy_pressure_ma_5_has_data     - Hat Coin genug Daten für Buy Pressure MA (5 Min)?
buy_pressure_ma_10_has_data   - Hat Coin genug Daten für Buy Pressure MA (10 Min)?
buy_pressure_ma_15_has_data   - Hat Coin genug Daten für Buy Pressure MA (15 Min)?
buy_pressure_trend_5_has_data  - Hat Coin genug Daten für Buy Pressure Trend (5 Min)?
buy_pressure_trend_10_has_data - Hat Coin genug Daten für Buy Pressure Trend (10 Min)?
buy_pressure_trend_15_has_data - Hat Coin genug Daten für Buy Pressure Trend (15 Min)?
```

### Whale Activity Flag-Features (3)
```
whale_activity_5_has_data      - Hat Coin genug Daten für Whale Activity (5 Min)?
whale_activity_10_has_data    - Hat Coin genug Daten für Whale Activity (10 Min)?
whale_activity_15_has_data    - Hat Coin genug Daten für Whale Activity (15 Min)?
```

### Volatility Flag-Features (6)
```
volatility_ma_5_has_data      - Hat Coin genug Daten für Volatility MA (5 Min)?
volatility_ma_10_has_data    - Hat Coin genug Daten für Volatility MA (10 Min)?
volatility_ma_15_has_data    - Hat Coin genug Daten für Volatility MA (15 Min)?
volatility_spike_5_has_data   - Hat Coin genug Daten für Volatility Spike (5 Min)?
volatility_spike_10_has_data - Hat Coin genug Daten für Volatility Spike (10 Min)?
volatility_spike_15_has_data - Hat Coin genug Daten für Volatility Spike (15 Min)?
```

### Wash Trading Flag-Features (3)
```
wash_trading_flag_5_has_data  - Hat Coin genug Daten für Wash Trading Detection (5 Min)?
wash_trading_flag_10_has_data - Hat Coin genug Daten für Wash Trading Detection (10 Min)?
wash_trading_flag_15_has_data - Hat Coin genug Daten für Wash Trading Detection (15 Min)?
```

### Volume Pattern Flag-Features (6)
```
net_volume_ma_5_has_data      - Hat Coin genug Daten für Net Volume MA (5 Min)?
net_volume_ma_10_has_data    - Hat Coin genug Daten für Net Volume MA (10 Min)?
net_volume_ma_15_has_data    - Hat Coin genug Daten für Net Volume MA (15 Min)?
volume_flip_5_has_data       - Hat Coin genug Daten für Volume Flip (5 Min)?
volume_flip_10_has_data      - Hat Coin genug Daten für Volume Flip (10 Min)?
volume_flip_15_has_data      - Hat Coin genug Daten für Volume Flip (15 Min)?
```

### Price Momentum Flag-Features (6)
```
price_change_5_has_data      - Hat Coin genug Daten für Price Change (5 Min)?
price_change_10_has_data    - Hat Coin genug Daten für Price Change (10 Min)?
price_change_15_has_data    - Hat Coin genug Daten für Price Change (15 Min)?
price_roc_5_has_data         - Hat Coin genug Daten für Price ROC (5 Min)?
price_roc_10_has_data        - Hat Coin genug Daten für Price ROC (10 Min)?
price_roc_15_has_data        - Hat Coin genug Daten für Price ROC (15 Min)?
```

### Price Acceleration Flag-Features (3)
```
price_acceleration_5_has_data  - Hat Coin genug Daten für Price Acceleration (5 Min)?
price_acceleration_10_has_data - Hat Coin genug Daten für Price Acceleration (10 Min)?
price_acceleration_15_has_data - Hat Coin genug Daten für Price Acceleration (15 Min)?
```

### Market Cap Velocity Flag-Features (3)
```
mcap_velocity_5_has_data      - Hat Coin genug Daten für Market Cap Velocity (5 Min)?
mcap_velocity_10_has_data    - Hat Coin genug Daten für Market Cap Velocity (10 Min)?
mcap_velocity_15_has_data    - Hat Coin genug Daten für Market Cap Velocity (15 Min)?
```

### ATH Flag-Features (15)
```
ath_distance_trend_5_has_data         - Hat Coin genug Daten für ATH Distance Trend (5 Min)?
ath_distance_trend_10_has_data        - Hat Coin genug Daten für ATH Distance Trend (10 Min)?
ath_distance_trend_15_has_data       - Hat Coin genug Daten für ATH Distance Trend (15 Min)?
ath_approach_5_has_data              - Hat Coin genug Daten für ATH Approach (5 Min)?
ath_approach_10_has_data             - Hat Coin genug Daten für ATH Approach (10 Min)?
ath_approach_15_has_data             - Hat Coin genug Daten für ATH Approach (15 Min)?
ath_breakout_count_5_has_data         - Hat Coin genug Daten für ATH Breakout Count (5 Min)?
ath_breakout_count_10_has_data       - Hat Coin genug Daten für ATH Breakout Count (10 Min)?
ath_breakout_count_15_has_data       - Hat Coin genug Daten für ATH Breakout Count (15 Min)?
ath_breakout_volume_ma_5_has_data     - Hat Coin genug Daten für ATH Breakout Volume MA (5 Min)?
ath_breakout_volume_ma_10_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (10 Min)?
ath_breakout_volume_ma_15_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (15 Min)?
ath_age_trend_5_has_data             - Hat Coin genug Daten für ATH Age Trend (5 Min)?
ath_age_trend_10_has_data            - Hat Coin genug Daten für ATH Age Trend (10 Min)?
ath_age_trend_15_has_data            - Hat Coin genug Daten für ATH Age Trend (15 Min)?
```

### Volume Spike Flag-Features (3)
```
volume_spike_5_has_data      - Hat Coin genug Daten für Volume Spike (5 Min)?
volume_spike_10_has_data    - Hat Coin genug Daten für Volume Spike (10 Min)?
volume_spike_15_has_data    - Hat Coin genug Daten für Volume Spike (15 Min)?
```

### Zusammenfassung Flag-Features

| Kategorie | Anzahl | Window-Größen |
|-----------|--------|---------------|
| Dev-Sold | 3 | 5, 10, 15 Min |
| Buy Pressure | 6 | 5, 10, 15 Min (MA + Trend) |
| Whale Activity | 3 | 5, 10, 15 Min |
| Volatility | 6 | 5, 10, 15 Min (MA + Spike) |
| Wash Trading | 3 | 5, 10, 15 Min |
| Volume Pattern | 6 | 5, 10, 15 Min (Net Volume MA + Volume Flip) |
| Price Momentum | 6 | 5, 10, 15 Min (Change + ROC) |
| Price Acceleration | 3 | 5, 10, 15 Min |
| Market Cap Velocity | 3 | 5, 10, 15 Min |
| ATH Features | 15 | 5, 10, 15 Min (5 verschiedene ATH-Features) |
| Volume Spike | 3 | 5, 10, 15 Min |
| **GESAMT** | **57** | - |

---

## 🔧 Feature Engineering Optionen

Der `use_engineered_features` Parameter bietet **3 verschiedene Modi**:

### Option 1: Keine Engineering-Features (Default)

**Verhalten:** Nur die Basis-Features werden verwendet, die du in der `features` Liste angibst.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&
  use_engineered_features=false
  # oder einfach weglassen (Default ist false)
```

**Ergebnis:** 4 Features total (nur Basis-Features)

---

### Option 2: Spezifische Engineering-Features auswählen

**Verhalten:** Du gibst explizit Engineering-Features in der `features` Liste an. Das Backend erstellt nur diese.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume&
  use_engineered_features=true
```

**Ergebnis:** 5 Features total (2 Basis + 3 Engineering)

**Vorteil:** Du hast volle Kontrolle über welche Engineering-Features verwendet werden.

---

### Option 3: Alle Engineering-Features (66 Stück)

**Verhalten:** Wenn `use_engineered_features=true` ist, aber **keine** Engineering-Features in der `features` Liste stehen, werden automatisch **alle 66 Engineering-Features** erstellt.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true
```

**Ergebnis:** 68 Features total (2 Basis + 66 Engineering)

**Vorteil:** Maximale Feature-Abdeckung ohne manuelle Auswahl.

---

### Zusammenfassung

| Modus | `use_engineered_features` | Engineering-Features in `features` | Ergebnis |
|-------|---------------------------|-----------------------------------|----------|
| **Keine** | `false` oder weglassen | - | Nur Basis-Features |
| **Spezifische** | `true` | ✅ Ja (z.B. `dev_sold_spike_5`) | Nur die angegebenen Engineering-Features |
| **Alle** | `true` | ❌ Nein | Alle 66 Engineering-Features |

---

### 66 Engineering-Features (mit `use_engineered_features=true`)

#### Dev-Sold Features (6)
```
dev_sold_flag           - Hat der Dev verkauft? (0/1)
dev_sold_cumsum         - Kumulative Dev-Verkäufe
dev_sold_spike_5        - Dev-Verkauf-Spike (5 Min)
dev_sold_spike_10       - Dev-Verkauf-Spike (10 Min)
dev_sold_spike_15       - Dev-Verkauf-Spike (15 Min)
```

#### Buy Pressure Features (6)
```
buy_pressure_ma_5       - Moving Average (5 Min)
buy_pressure_trend_5    - Trend (5 Min)
buy_pressure_ma_10      - Moving Average (10 Min)
buy_pressure_trend_10   - Trend (10 Min)
buy_pressure_ma_15      - Moving Average (15 Min)
buy_pressure_trend_15   - Trend (15 Min)
```

#### Whale Activity Features (4)
```
whale_net_volume        - Netto Whale-Volume
whale_activity_5        - Whale-Aktivität (5 Min)
whale_activity_10       - Whale-Aktivität (10 Min)
whale_activity_15       - Whale-Aktivität (15 Min)
```

#### Volatility Features (6)
```
volatility_ma_5         - Volatilität MA (5 Min)
volatility_spike_5      - Volatilität-Spike (5 Min)
volatility_ma_10        - Volatilität MA (10 Min)
volatility_spike_10     - Volatilität-Spike (10 Min)
volatility_ma_15        - Volatilität MA (15 Min)
volatility_spike_15     - Volatilität-Spike (15 Min)
```

#### Wash Trading Detection (3)
```
wash_trading_flag_5     - Wash Trading erkannt? (5 Min)
wash_trading_flag_10    - Wash Trading erkannt? (10 Min)
wash_trading_flag_15    - Wash Trading erkannt? (15 Min)
```

#### Volume Pattern Features (6)
```
net_volume_ma_5         - Netto-Volume MA (5 Min)
volume_flip_5           - Volume Flip (5 Min)
net_volume_ma_10        - Netto-Volume MA (10 Min)
volume_flip_10          - Volume Flip (10 Min)
net_volume_ma_15        - Netto-Volume MA (15 Min)
volume_flip_15          - Volume Flip (15 Min)
```

#### Price Momentum Features (6)
```
price_change_5          - Preisänderung (5 Min)
price_roc_5             - Rate of Change (5 Min)
price_change_10         - Preisänderung (10 Min)
price_roc_10            - Rate of Change (10 Min)
price_change_15         - Preisänderung (15 Min)
price_roc_15            - Rate of Change (15 Min)
```

#### Market Cap Velocity (3)
```
mcap_velocity_5         - MarketCap Änderungsrate (5 Min)
mcap_velocity_10        - MarketCap Änderungsrate (10 Min)
mcap_velocity_15        - MarketCap Änderungsrate (15 Min)
```

#### ATH Features (19)
```
rolling_ath             - Rolling All-Time-High
price_vs_ath_pct        - Distanz zum ATH in %
ath_breakout            - ATH durchbrochen? (0/1)
minutes_since_ath       - Minuten seit letztem ATH
ath_distance_trend_5    - ATH-Distanz Trend (5 Min)
ath_approach_5          - Nähert sich ATH? (5 Min)
ath_breakout_count_5    - ATH-Durchbrüche (5 Min)
ath_breakout_volume_ma_5 - Volume bei ATH-Breaks (5 Min)
ath_age_trend_5         - ATH-Alter Trend (5 Min)
... (analog für 10 und 15 Minuten)
```

#### Power Features (8)
```
buy_sell_ratio          - Buy/Sell Verhältnis
whale_dominance         - Whale-Anteil am Volume
price_acceleration_5    - Preis-Beschleunigung (5 Min)
price_acceleration_10   - Preis-Beschleunigung (10 Min)
price_acceleration_15   - Preis-Beschleunigung (15 Min)
volume_spike_5          - Volume-Spike (5 Min)
volume_spike_10         - Volume-Spike (10 Min)
volume_spike_15         - Volume-Spike (15 Min)
```

---

## ⚖️ Balance-Optionen

### Das Problem: Unbalancierte Daten

Bei Pump-Detection sind positive Labels (Pumps) sehr selten (oft nur 1-5% der Daten). Das führt dazu, dass Modelle einfach "Nein" für alles vorhersagen.

### Lösung 1: `scale_pos_weight` (✅ EMPFOHLEN)

XGBoost-intern, gewichtet die positive Klasse höher.

| Positive Labels | scale_pos_weight | Effekt |
|-----------------|------------------|--------|
| 0.5% | `200` | Sehr aggressiv |
| 1% | `100` | Standard |
| 2% | `50` | Moderat |
| 5% | `20` | Konservativ |

**Beispiel:**
```bash
scale_pos_weight=100
```

**Vorteile:**
- Keine synthetischen Daten
- Schneller als SMOTE
- Besser generalisierbar

### Lösung 2: `use_smote` (⚠️ Mit Vorsicht)

Synthetisches Oversampling - erstellt künstliche positive Samples.

**Beispiel:**
```bash
use_smote=true
```

**Nachteile:**
- Kann zu Overfitting führen
- Modell lernt synthetische statt echte Muster

### Lösung 3: `class_weight` (für Random Forest)

```bash
class_weight=balanced
```

---

## 📝 Beispiele

### Beispiel 1: Einfaches Pump-Modell

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio&\
future_minutes=5&\
min_percent_change=2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 2: Mit ALLEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 2c: Mit ALLEN Engineering-Features OHNE Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_No_Flags_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=false&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 70 Features (4 Basis + 66 Engineering, keine Flag-Features)

### Beispiel 2b: Mit SPEZIFISCHEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Selective_Engineering_v1&\
model_type=xgboost&\
features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume,volatility_spike_15&\
use_engineered_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 8 Features (2 Basis + 4 Engineering + **4 Flag-Features** - nur die für die ausgewählten Engineering-Features!)

**Wichtig:** Das System verwendet automatisch nur die Flag-Features, die zu den ausgewählten Engineering-Features gehören:
- `dev_sold_spike_5_has_data` (für `dev_sold_spike_5`)
- `buy_pressure_ma_10_has_data` (für `buy_pressure_ma_10`)
- `volatility_spike_15_has_data` (für `volatility_spike_15`)
- `whale_net_volume` hat kein Flag-Feature (ist kein window-basiertes Feature)

### Beispiel 3: OHNE Engineering-Features (nur Basis)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol&\
use_engineered_features=false&\
scale_pos_weight=100&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 5 Features (nur Basis-Features, keine Engineering)

### Beispiel 4: Mit scale_pos_weight (EMPFOHLEN)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Balanced_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 5: ULTIMATIV (Alle Features + Engineering + Flag-Features + Balance)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Ultimate_Pump_Detector&\
model_type=xgboost&\
features=price_open,price_high,price_low,price_close,volume_sol,buy_volume_sol,sell_volume_sol,net_volume_sol,market_cap_close,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct,unique_signer_ratio&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=15&\
direction=up&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 137 Features (14 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 5: Rug-Pull Detection

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Rug_Pull_Detector&\
model_type=xgboost&\
features=price_close,dev_sold_amount,buy_pressure_ratio,whale_sell_volume_sol&\
direction=down&\
min_percent_change=20&\
future_minutes=15&\
scale_pos_weight=50&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 6: Random Forest

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=RF_Pump_Detector&\
model_type=random_forest&\
features=price_close,volume_sol,buy_pressure_ratio&\
class_weight=balanced&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 7: Second Wave Detection (mit Flag-Features)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Second_Wave_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
future_minutes=15&\
min_percent_change=10&\
phases=1,2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 129 Features (6 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 8: Nur Baby Zone (Phase 1)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Baby_Zone_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
phases=1&\
scale_pos_weight=150&\
future_minutes=5&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 9: Survival + Mature Zone (Phase 2+3) mit Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Mature_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
phases=2,3&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=80&\
future_minutes=15&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

---

## 💡 Best Practices

### 1. Feature-Auswahl

| Empfehlung | Beschreibung |
|------------|--------------|
| ✅ Start mit Basis-Features | Beginne mit 5-10 wichtigen Features |
| ✅ Wichtigste Features zuerst | `price_close`, `volume_sol`, `buy_pressure_ratio` |
| ✅ Flag-Features aktivieren | Verbessert Modell-Performance bei neuen Coins |
| ⚠️ Nicht zu viele Features | Mehr als 30 Basis-Features kann zu Overfitting führen |
| ⚠️ Mit Engineering + Flags | Bis zu 150 Features möglich (27 Base + 66 Eng + 57 Flags bei zeitbasierter Vorhersage) oder 151 Features (28 Base + 66 Eng + 57 Flags ohne zeitbasierte Vorhersage) |
| ❌ Keine redundanten Features | z.B. nicht `price_open` UND `price_close` UND `price_high` UND `price_low` |

### 2. Zeithorizont-Wahl

| Zeithorizont | Empfohlene Schwelle | Use Case |
|--------------|---------------------|----------|
| 2-5 Min | 1-3% | Schnelle Scalping-Signale |
| 5-10 Min | 3-10% | Standard Pump Detection |
| 10-15 Min | 5-15% | Second Wave Detection |
| 15-30 Min | 10-25% | Langfristige Trends |

### 3. Balance-Strategie

| Situation | Empfehlung |
|-----------|------------|
| 1% positive Labels | `scale_pos_weight=100` |
| Sehr seltene Events | `scale_pos_weight=200` |
| Mehr Pumps erkennen | Höherer `scale_pos_weight` (mehr Fehlalarme) |
| Weniger Fehlalarme | Niedrigerer `scale_pos_weight` (weniger erkannte Pumps) |

### 4. Trainings-Zeitraum

| Zeitraum | Empfehlung |
|----------|------------|
| **Minimum** | 2 Stunden |
| **Optimal** | 8-12 Stunden |
| **Maximum** | 24+ Stunden (längere Wartezeit) |

---

## 🔧 Troubleshooting

### Problem: F1-Score = 0

**Ursache:** Zu wenig positive Labels oder keine Balance-Strategie.

**Lösung:**
1. Aktiviere `scale_pos_weight=100`
2. ODER senke `min_percent_change`
3. ODER erhöhe `future_minutes`

### Problem: Zu viele Fehlalarme

**Ursache:** `scale_pos_weight` zu hoch.

**Lösung:**
1. Senke `scale_pos_weight` (z.B. von 200 auf 100)
2. ODER erhöhe `min_percent_change`

### Problem: Keine Pumps erkannt

**Ursache:** `scale_pos_weight` zu niedrig oder Feature-Auswahl schlecht.

**Lösung:**
1. Erhöhe `scale_pos_weight` (z.B. auf 200)
2. Füge relevante Features hinzu: `buy_pressure_ratio`, `whale_buy_volume_sol`

### Problem: Training dauert zu lange

**Ursache:** Zu viele Features oder zu großer Zeitraum.

**Lösung:**
1. Reduziere Features auf 10-15
2. Reduziere Trainings-Zeitraum
3. Deaktiviere `use_engineered_features`

### Problem: "Keine Trainingsdaten gefunden"

**Ursache:** Der angegebene Zeitraum enthält keine Daten.

**Lösung:**
1. Prüfe ob der Zeitraum korrekt ist (UTC!)
2. Verwende einen Zeitraum mit bekannten Daten

---

## 📊 Response-Format

### Erfolgreiche Erstellung

```json
{
  "job_id": 424,
  "message": "Job erstellt. Modell 'MyModel' wird trainiert.",
  "status": "PENDING"
}
```

### Job-Status prüfen

```bash
GET /api/queue/{job_id}
```

```json
{
  "id": 424,
  "status": "COMPLETED",
  "result_model_id": 130,
  "progress": 100,
  "progress_msg": "Training abgeschlossen"
}
```

### Modell-Details abrufen

```bash
GET /api/models/{model_id}
```

---

## 🌐 Web UI

Die Web UI bietet dieselben Funktionen mit grafischer Oberfläche:

**URL:** https://test.local.chase295.de/training

Im Schritt 5 "Erweiterte Einstellungen" findest du:
- ⚖️ Klassen-Gewichtung (scale_pos_weight)
- Cross-Validation Einstellungen
- SMOTE Option
- Trainings-Zeitraum

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe die Job-Logs: `GET /api/queue/{job_id}`
2. Prüfe die Modell-Details: `GET /api/models/{model_id}`
3. Sieh dir die Confusion Matrix an für Einblicke in die Performance

---

**Dokumentation erstellt:** Januar 2026  
**Getestet:** 10/10 Tests bestanden ✅



**Version:** 1.0  
**Stand:** Januar 2026  
**Endpoint:** `POST /api/models/create/advanced`

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Alle Parameter](#alle-parameter)
3. [Feature-Liste](#feature-liste)
4. [Balance-Optionen](#balance-optionen)
5. [Beispiele](#beispiele)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Der `/models/create/advanced` Endpoint ist der **vollständigste und flexibelste** Endpoint zur Erstellung von ML-Modellen für Pump-Detection.

### Was kann dieser Endpoint?

| Funktion | Beschreibung |
|----------|--------------|
| ✅ **Zeitbasierte Vorhersage** | "Steigt der Preis um X% in Y Minuten?" |
| ✅ **Feature Engineering** | 66 zusätzliche berechnete Features |
| ✅ **SMOTE** | Synthetisches Oversampling für unbalancierte Daten |
| ✅ **scale_pos_weight** | XGBoost-interne Klassen-Gewichtung |
| ✅ **Flexible Zeithorizonte** | 1 Minute bis 60+ Minuten |
| ✅ **Pump & Rug Detection** | Steigende oder fallende Preise vorhersagen |
| ✅ **Zwei Modell-Typen** | XGBoost und Random Forest |

---

## 📊 Alle Parameter

### Pflicht-Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `name` | string | Eindeutiger Modell-Name | `"Pump_Detector_v1"` |
| `model_type` | string | `xgboost` oder `random_forest` | `"xgboost"` |
| `features` | string | Komma-separierte Feature-Liste | `"price_close,volume_sol"` |
| `train_start` | string | Trainings-Startzeit (UTC, ISO-Format) | `"2026-01-07T06:00:00Z"` |
| `train_end` | string | Trainings-Endzeit (UTC, ISO-Format) | `"2026-01-07T18:00:00Z"` |

### Optionale Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `target_var` | string | `"price_close"` | Ziel-Variable für Vorhersage |
| `use_time_based_prediction` | bool | `true` | Zeitbasierte Vorhersage aktivieren |
| `future_minutes` | int | `5` | Vorhersage-Horizont in Minuten |
| `min_percent_change` | float | `2.0` | Minimale Preisänderung in % |
| `direction` | string | `"up"` | `"up"` für Pump, `"down"` für Rug |
| `use_engineered_features` | bool | `false` | Feature Engineering aktivieren (siehe [Feature Engineering Optionen](#feature-engineering-optionen)) |
| `use_flag_features` | bool | `true` | **NEU!** Flag-Features aktivieren (siehe [Flag-Features](#flag-features)) |
| `use_smote` | bool | `false` | SMOTE aktivieren |
| `scale_pos_weight` | float | `null` | XGBoost Klassen-Gewichtung |
| `class_weight` | string | `null` | `"balanced"` für Random Forest |
| `phases` | string | `null` | **NEU!** Coin-Phasen Filter (z.B. `"1,2,3"`) |

---

## 🔄 Coin-Phasen Filter (NEU!)

Mit dem `phases` Parameter kannst du das Training auf **bestimmte Coin-Entwicklungsphasen** beschränken.

### Verfügbare Phasen

| Phase ID | Name | Beschreibung | Alter |
|----------|------|--------------|-------|
| **1** | Baby Zone | Frisch erstellte Coins | 0-10 Min |
| **2** | Survival Zone | Überlebende Coins | 10-120 Min |
| **3** | Mature Zone | Reife Coins | 2-4 Stunden |
| **99** | Finished | Abgeschlossene Coins | - |
| **100** | Graduated | Graduierte Coins | - |

### Beispiele

```bash
# Nur Baby & Survival Zone (Phase 1 + 2)
phases=1,2

# Nur Mature Zone (Phase 3)
phases=3

# Alle aktiven Phasen (1, 2, 3)
phases=1,2,3
```

### Warum Phasen filtern?

| Use Case | Empfohlene Phasen | Grund |
|----------|-------------------|-------|
| **Second Wave Detection** | `1,2` | Pumps passieren früh |
| **Langfristige Trends** | `2,3` | Stabile Datenmuster |
| **Rug-Pull Detection** | `1` | Rugs passieren in Phase 1 |
| **Allgemein** | `1,2,3` | Maximale Datenmenge |

---

## 📊 Feature-Liste

### 28 Basis-Features (immer verfügbar)

⚠️ **WICHTIG:** Bei zeitbasierter Vorhersage wird `price_close` automatisch aus den Trainings-Features entfernt (verhindert Data Leakage). In diesem Fall sind es **27 Basis-Features** im Training.

#### Preis-Features (4)
```
price_open      - Eröffnungspreis der Minute
price_high      - Höchster Preis der Minute
price_low       - Niedrigster Preis der Minute
price_close     - Schlusskurs der Minute
```

#### Volume-Features (4)
```
volume_sol          - Gesamtes Handelsvolumen in SOL
buy_volume_sol      - Kaufvolumen in SOL
sell_volume_sol     - Verkaufsvolumen in SOL
net_volume_sol      - Netto-Volumen (Buy - Sell)
```

#### Market-Features (4)
```
market_cap_close        - Marktkapitalisierung
bonding_curve_pct       - Position auf der Bonding Curve (%)
virtual_sol_reserves    - Virtuelle SOL-Reserven
is_koth                 - King of the Hill Status (0/1)
```

#### Trade-Statistiken (4)
```
num_buys            - Anzahl Buy-Trades
num_sells           - Anzahl Sell-Trades
unique_wallets      - Einzigartige Wallet-Adressen
num_micro_trades    - Anzahl Mikro-Trades
```

#### Max Trade Sizes (2)
```
max_single_buy_sol      - Größter einzelner Kauf
max_single_sell_sol     - Größter einzelner Verkauf
```

#### Whale-Features (4)
```
whale_buy_volume_sol    - Whale-Kaufvolumen
whale_sell_volume_sol   - Whale-Verkaufsvolumen
num_whale_buys          - Anzahl Whale-Käufe
num_whale_sells         - Anzahl Whale-Verkäufe
```

#### Qualitäts-Features (4)
```
dev_sold_amount     - Vom Developer verkaufte Menge
volatility_pct      - Preisvolatilität in %
avg_trade_size_sol  - Durchschnittliche Trade-Größe
buy_pressure_ratio  - Kaufdruck-Verhältnis (0-1)
```

#### Wallet-Analyse (2)
```
unique_signer_ratio     - Verhältnis einzigartiger Signaturen
phase_id_at_time        - Coin-Phase (1-6)
```

---

## 🚩 Flag-Features (NEU!)

Flag-Features sind **Datenverfügbarkeits-Indikatoren**, die dem Modell anzeigen, ob ein Engineering-Feature genug historische Daten hat, um zuverlässig berechnet zu werden.

### Was sind Flag-Features?

Jedes window-basierte Engineering-Feature (z.B. `buy_pressure_ma_5`) erhält ein entsprechendes Flag-Feature (z.B. `buy_pressure_ma_5_has_data`), das anzeigt:
- **`1`** = Genug Daten vorhanden (Feature ist zuverlässig)
- **`0`** = Nicht genug Daten (Feature könnte unzuverlässig sein)

### Warum Flag-Features?

| Problem | Lösung mit Flag-Features |
|---------|-------------------------|
| Neue Coins haben keine 15-Minuten-Historie | Modell lernt, dass `buy_pressure_ma_15_has_data=0` bedeutet: Feature ignorieren |
| NaN-Werte in Engineering-Features | Flag zeigt dem Modell, ob NaN = "keine Daten" oder "echter Wert" |
| Unzuverlässige Features bei jungen Coins | Modell kann Features basierend auf Datenverfügbarkeit gewichten |

### Aktivierung

Flag-Features werden automatisch aktiviert, wenn:
1. `use_engineered_features=true` **UND**
2. `use_flag_features=true` (Default: `true`)

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering + **57 Flag-Features = 150 Features total**

### Deaktivierung

Wenn du Flag-Features nicht möchtest:
```bash
use_flag_features=false
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering = 93 Features total (ohne Flags)

---

## 🚩 Alle 57 Flag-Features

### Dev-Sold Flag-Features (3)
```
dev_sold_spike_5_has_data      - Hat Coin genug Daten für Dev-Sold Spike (5 Min)?
dev_sold_spike_10_has_data     - Hat Coin genug Daten für Dev-Sold Spike (10 Min)?
dev_sold_spike_15_has_data     - Hat Coin genug Daten für Dev-Sold Spike (15 Min)?
```

### Buy Pressure Flag-Features (6)
```
buy_pressure_ma_5_has_data     - Hat Coin genug Daten für Buy Pressure MA (5 Min)?
buy_pressure_ma_10_has_data   - Hat Coin genug Daten für Buy Pressure MA (10 Min)?
buy_pressure_ma_15_has_data   - Hat Coin genug Daten für Buy Pressure MA (15 Min)?
buy_pressure_trend_5_has_data  - Hat Coin genug Daten für Buy Pressure Trend (5 Min)?
buy_pressure_trend_10_has_data - Hat Coin genug Daten für Buy Pressure Trend (10 Min)?
buy_pressure_trend_15_has_data - Hat Coin genug Daten für Buy Pressure Trend (15 Min)?
```

### Whale Activity Flag-Features (3)
```
whale_activity_5_has_data      - Hat Coin genug Daten für Whale Activity (5 Min)?
whale_activity_10_has_data    - Hat Coin genug Daten für Whale Activity (10 Min)?
whale_activity_15_has_data    - Hat Coin genug Daten für Whale Activity (15 Min)?
```

### Volatility Flag-Features (6)
```
volatility_ma_5_has_data      - Hat Coin genug Daten für Volatility MA (5 Min)?
volatility_ma_10_has_data    - Hat Coin genug Daten für Volatility MA (10 Min)?
volatility_ma_15_has_data    - Hat Coin genug Daten für Volatility MA (15 Min)?
volatility_spike_5_has_data   - Hat Coin genug Daten für Volatility Spike (5 Min)?
volatility_spike_10_has_data - Hat Coin genug Daten für Volatility Spike (10 Min)?
volatility_spike_15_has_data - Hat Coin genug Daten für Volatility Spike (15 Min)?
```

### Wash Trading Flag-Features (3)
```
wash_trading_flag_5_has_data  - Hat Coin genug Daten für Wash Trading Detection (5 Min)?
wash_trading_flag_10_has_data - Hat Coin genug Daten für Wash Trading Detection (10 Min)?
wash_trading_flag_15_has_data - Hat Coin genug Daten für Wash Trading Detection (15 Min)?
```

### Volume Pattern Flag-Features (6)
```
net_volume_ma_5_has_data      - Hat Coin genug Daten für Net Volume MA (5 Min)?
net_volume_ma_10_has_data    - Hat Coin genug Daten für Net Volume MA (10 Min)?
net_volume_ma_15_has_data    - Hat Coin genug Daten für Net Volume MA (15 Min)?
volume_flip_5_has_data       - Hat Coin genug Daten für Volume Flip (5 Min)?
volume_flip_10_has_data      - Hat Coin genug Daten für Volume Flip (10 Min)?
volume_flip_15_has_data      - Hat Coin genug Daten für Volume Flip (15 Min)?
```

### Price Momentum Flag-Features (6)
```
price_change_5_has_data      - Hat Coin genug Daten für Price Change (5 Min)?
price_change_10_has_data    - Hat Coin genug Daten für Price Change (10 Min)?
price_change_15_has_data    - Hat Coin genug Daten für Price Change (15 Min)?
price_roc_5_has_data         - Hat Coin genug Daten für Price ROC (5 Min)?
price_roc_10_has_data        - Hat Coin genug Daten für Price ROC (10 Min)?
price_roc_15_has_data        - Hat Coin genug Daten für Price ROC (15 Min)?
```

### Price Acceleration Flag-Features (3)
```
price_acceleration_5_has_data  - Hat Coin genug Daten für Price Acceleration (5 Min)?
price_acceleration_10_has_data - Hat Coin genug Daten für Price Acceleration (10 Min)?
price_acceleration_15_has_data - Hat Coin genug Daten für Price Acceleration (15 Min)?
```

### Market Cap Velocity Flag-Features (3)
```
mcap_velocity_5_has_data      - Hat Coin genug Daten für Market Cap Velocity (5 Min)?
mcap_velocity_10_has_data    - Hat Coin genug Daten für Market Cap Velocity (10 Min)?
mcap_velocity_15_has_data    - Hat Coin genug Daten für Market Cap Velocity (15 Min)?
```

### ATH Flag-Features (15)
```
ath_distance_trend_5_has_data         - Hat Coin genug Daten für ATH Distance Trend (5 Min)?
ath_distance_trend_10_has_data        - Hat Coin genug Daten für ATH Distance Trend (10 Min)?
ath_distance_trend_15_has_data       - Hat Coin genug Daten für ATH Distance Trend (15 Min)?
ath_approach_5_has_data              - Hat Coin genug Daten für ATH Approach (5 Min)?
ath_approach_10_has_data             - Hat Coin genug Daten für ATH Approach (10 Min)?
ath_approach_15_has_data             - Hat Coin genug Daten für ATH Approach (15 Min)?
ath_breakout_count_5_has_data         - Hat Coin genug Daten für ATH Breakout Count (5 Min)?
ath_breakout_count_10_has_data       - Hat Coin genug Daten für ATH Breakout Count (10 Min)?
ath_breakout_count_15_has_data       - Hat Coin genug Daten für ATH Breakout Count (15 Min)?
ath_breakout_volume_ma_5_has_data     - Hat Coin genug Daten für ATH Breakout Volume MA (5 Min)?
ath_breakout_volume_ma_10_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (10 Min)?
ath_breakout_volume_ma_15_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (15 Min)?
ath_age_trend_5_has_data             - Hat Coin genug Daten für ATH Age Trend (5 Min)?
ath_age_trend_10_has_data            - Hat Coin genug Daten für ATH Age Trend (10 Min)?
ath_age_trend_15_has_data            - Hat Coin genug Daten für ATH Age Trend (15 Min)?
```

### Volume Spike Flag-Features (3)
```
volume_spike_5_has_data      - Hat Coin genug Daten für Volume Spike (5 Min)?
volume_spike_10_has_data    - Hat Coin genug Daten für Volume Spike (10 Min)?
volume_spike_15_has_data    - Hat Coin genug Daten für Volume Spike (15 Min)?
```

### Zusammenfassung Flag-Features

| Kategorie | Anzahl | Window-Größen |
|-----------|--------|---------------|
| Dev-Sold | 3 | 5, 10, 15 Min |
| Buy Pressure | 6 | 5, 10, 15 Min (MA + Trend) |
| Whale Activity | 3 | 5, 10, 15 Min |
| Volatility | 6 | 5, 10, 15 Min (MA + Spike) |
| Wash Trading | 3 | 5, 10, 15 Min |
| Volume Pattern | 6 | 5, 10, 15 Min (Net Volume MA + Volume Flip) |
| Price Momentum | 6 | 5, 10, 15 Min (Change + ROC) |
| Price Acceleration | 3 | 5, 10, 15 Min |
| Market Cap Velocity | 3 | 5, 10, 15 Min |
| ATH Features | 15 | 5, 10, 15 Min (5 verschiedene ATH-Features) |
| Volume Spike | 3 | 5, 10, 15 Min |
| **GESAMT** | **57** | - |

---

## 🔧 Feature Engineering Optionen

Der `use_engineered_features` Parameter bietet **3 verschiedene Modi**:

### Option 1: Keine Engineering-Features (Default)

**Verhalten:** Nur die Basis-Features werden verwendet, die du in der `features` Liste angibst.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&
  use_engineered_features=false
  # oder einfach weglassen (Default ist false)
```

**Ergebnis:** 4 Features total (nur Basis-Features)

---

### Option 2: Spezifische Engineering-Features auswählen

**Verhalten:** Du gibst explizit Engineering-Features in der `features` Liste an. Das Backend erstellt nur diese.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume&
  use_engineered_features=true
```

**Ergebnis:** 5 Features total (2 Basis + 3 Engineering)

**Vorteil:** Du hast volle Kontrolle über welche Engineering-Features verwendet werden.

---

### Option 3: Alle Engineering-Features (66 Stück)

**Verhalten:** Wenn `use_engineered_features=true` ist, aber **keine** Engineering-Features in der `features` Liste stehen, werden automatisch **alle 66 Engineering-Features** erstellt.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true
```

**Ergebnis:** 68 Features total (2 Basis + 66 Engineering)

**Vorteil:** Maximale Feature-Abdeckung ohne manuelle Auswahl.

---

### Zusammenfassung

| Modus | `use_engineered_features` | Engineering-Features in `features` | Ergebnis |
|-------|---------------------------|-----------------------------------|----------|
| **Keine** | `false` oder weglassen | - | Nur Basis-Features |
| **Spezifische** | `true` | ✅ Ja (z.B. `dev_sold_spike_5`) | Nur die angegebenen Engineering-Features |
| **Alle** | `true` | ❌ Nein | Alle 66 Engineering-Features |

---

### 66 Engineering-Features (mit `use_engineered_features=true`)

#### Dev-Sold Features (6)
```
dev_sold_flag           - Hat der Dev verkauft? (0/1)
dev_sold_cumsum         - Kumulative Dev-Verkäufe
dev_sold_spike_5        - Dev-Verkauf-Spike (5 Min)
dev_sold_spike_10       - Dev-Verkauf-Spike (10 Min)
dev_sold_spike_15       - Dev-Verkauf-Spike (15 Min)
```

#### Buy Pressure Features (6)
```
buy_pressure_ma_5       - Moving Average (5 Min)
buy_pressure_trend_5    - Trend (5 Min)
buy_pressure_ma_10      - Moving Average (10 Min)
buy_pressure_trend_10   - Trend (10 Min)
buy_pressure_ma_15      - Moving Average (15 Min)
buy_pressure_trend_15   - Trend (15 Min)
```

#### Whale Activity Features (4)
```
whale_net_volume        - Netto Whale-Volume
whale_activity_5        - Whale-Aktivität (5 Min)
whale_activity_10       - Whale-Aktivität (10 Min)
whale_activity_15       - Whale-Aktivität (15 Min)
```

#### Volatility Features (6)
```
volatility_ma_5         - Volatilität MA (5 Min)
volatility_spike_5      - Volatilität-Spike (5 Min)
volatility_ma_10        - Volatilität MA (10 Min)
volatility_spike_10     - Volatilität-Spike (10 Min)
volatility_ma_15        - Volatilität MA (15 Min)
volatility_spike_15     - Volatilität-Spike (15 Min)
```

#### Wash Trading Detection (3)
```
wash_trading_flag_5     - Wash Trading erkannt? (5 Min)
wash_trading_flag_10    - Wash Trading erkannt? (10 Min)
wash_trading_flag_15    - Wash Trading erkannt? (15 Min)
```

#### Volume Pattern Features (6)
```
net_volume_ma_5         - Netto-Volume MA (5 Min)
volume_flip_5           - Volume Flip (5 Min)
net_volume_ma_10        - Netto-Volume MA (10 Min)
volume_flip_10          - Volume Flip (10 Min)
net_volume_ma_15        - Netto-Volume MA (15 Min)
volume_flip_15          - Volume Flip (15 Min)
```

#### Price Momentum Features (6)
```
price_change_5          - Preisänderung (5 Min)
price_roc_5             - Rate of Change (5 Min)
price_change_10         - Preisänderung (10 Min)
price_roc_10            - Rate of Change (10 Min)
price_change_15         - Preisänderung (15 Min)
price_roc_15            - Rate of Change (15 Min)
```

#### Market Cap Velocity (3)
```
mcap_velocity_5         - MarketCap Änderungsrate (5 Min)
mcap_velocity_10        - MarketCap Änderungsrate (10 Min)
mcap_velocity_15        - MarketCap Änderungsrate (15 Min)
```

#### ATH Features (19)
```
rolling_ath             - Rolling All-Time-High
price_vs_ath_pct        - Distanz zum ATH in %
ath_breakout            - ATH durchbrochen? (0/1)
minutes_since_ath       - Minuten seit letztem ATH
ath_distance_trend_5    - ATH-Distanz Trend (5 Min)
ath_approach_5          - Nähert sich ATH? (5 Min)
ath_breakout_count_5    - ATH-Durchbrüche (5 Min)
ath_breakout_volume_ma_5 - Volume bei ATH-Breaks (5 Min)
ath_age_trend_5         - ATH-Alter Trend (5 Min)
... (analog für 10 und 15 Minuten)
```

#### Power Features (8)
```
buy_sell_ratio          - Buy/Sell Verhältnis
whale_dominance         - Whale-Anteil am Volume
price_acceleration_5    - Preis-Beschleunigung (5 Min)
price_acceleration_10   - Preis-Beschleunigung (10 Min)
price_acceleration_15   - Preis-Beschleunigung (15 Min)
volume_spike_5          - Volume-Spike (5 Min)
volume_spike_10         - Volume-Spike (10 Min)
volume_spike_15         - Volume-Spike (15 Min)
```

---

## ⚖️ Balance-Optionen

### Das Problem: Unbalancierte Daten

Bei Pump-Detection sind positive Labels (Pumps) sehr selten (oft nur 1-5% der Daten). Das führt dazu, dass Modelle einfach "Nein" für alles vorhersagen.

### Lösung 1: `scale_pos_weight` (✅ EMPFOHLEN)

XGBoost-intern, gewichtet die positive Klasse höher.

| Positive Labels | scale_pos_weight | Effekt |
|-----------------|------------------|--------|
| 0.5% | `200` | Sehr aggressiv |
| 1% | `100` | Standard |
| 2% | `50` | Moderat |
| 5% | `20` | Konservativ |

**Beispiel:**
```bash
scale_pos_weight=100
```

**Vorteile:**
- Keine synthetischen Daten
- Schneller als SMOTE
- Besser generalisierbar

### Lösung 2: `use_smote` (⚠️ Mit Vorsicht)

Synthetisches Oversampling - erstellt künstliche positive Samples.

**Beispiel:**
```bash
use_smote=true
```

**Nachteile:**
- Kann zu Overfitting führen
- Modell lernt synthetische statt echte Muster

### Lösung 3: `class_weight` (für Random Forest)

```bash
class_weight=balanced
```

---

## 📝 Beispiele

### Beispiel 1: Einfaches Pump-Modell

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio&\
future_minutes=5&\
min_percent_change=2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 2: Mit ALLEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 2c: Mit ALLEN Engineering-Features OHNE Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_No_Flags_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=false&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 70 Features (4 Basis + 66 Engineering, keine Flag-Features)

### Beispiel 2b: Mit SPEZIFISCHEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Selective_Engineering_v1&\
model_type=xgboost&\
features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume,volatility_spike_15&\
use_engineered_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 8 Features (2 Basis + 4 Engineering + **4 Flag-Features** - nur die für die ausgewählten Engineering-Features!)

**Wichtig:** Das System verwendet automatisch nur die Flag-Features, die zu den ausgewählten Engineering-Features gehören:
- `dev_sold_spike_5_has_data` (für `dev_sold_spike_5`)
- `buy_pressure_ma_10_has_data` (für `buy_pressure_ma_10`)
- `volatility_spike_15_has_data` (für `volatility_spike_15`)
- `whale_net_volume` hat kein Flag-Feature (ist kein window-basiertes Feature)

### Beispiel 3: OHNE Engineering-Features (nur Basis)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol&\
use_engineered_features=false&\
scale_pos_weight=100&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 5 Features (nur Basis-Features, keine Engineering)

### Beispiel 4: Mit scale_pos_weight (EMPFOHLEN)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Balanced_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 5: ULTIMATIV (Alle Features + Engineering + Flag-Features + Balance)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Ultimate_Pump_Detector&\
model_type=xgboost&\
features=price_open,price_high,price_low,price_close,volume_sol,buy_volume_sol,sell_volume_sol,net_volume_sol,market_cap_close,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct,unique_signer_ratio&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=15&\
direction=up&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 137 Features (14 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 5: Rug-Pull Detection

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Rug_Pull_Detector&\
model_type=xgboost&\
features=price_close,dev_sold_amount,buy_pressure_ratio,whale_sell_volume_sol&\
direction=down&\
min_percent_change=20&\
future_minutes=15&\
scale_pos_weight=50&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 6: Random Forest

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=RF_Pump_Detector&\
model_type=random_forest&\
features=price_close,volume_sol,buy_pressure_ratio&\
class_weight=balanced&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 7: Second Wave Detection (mit Flag-Features)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Second_Wave_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
future_minutes=15&\
min_percent_change=10&\
phases=1,2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 129 Features (6 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 8: Nur Baby Zone (Phase 1)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Baby_Zone_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
phases=1&\
scale_pos_weight=150&\
future_minutes=5&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 9: Survival + Mature Zone (Phase 2+3) mit Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Mature_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
phases=2,3&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=80&\
future_minutes=15&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

---

## 💡 Best Practices

### 1. Feature-Auswahl

| Empfehlung | Beschreibung |
|------------|--------------|
| ✅ Start mit Basis-Features | Beginne mit 5-10 wichtigen Features |
| ✅ Wichtigste Features zuerst | `price_close`, `volume_sol`, `buy_pressure_ratio` |
| ✅ Flag-Features aktivieren | Verbessert Modell-Performance bei neuen Coins |
| ⚠️ Nicht zu viele Features | Mehr als 30 Basis-Features kann zu Overfitting führen |
| ⚠️ Mit Engineering + Flags | Bis zu 150 Features möglich (27 Base + 66 Eng + 57 Flags bei zeitbasierter Vorhersage) oder 151 Features (28 Base + 66 Eng + 57 Flags ohne zeitbasierte Vorhersage) |
| ❌ Keine redundanten Features | z.B. nicht `price_open` UND `price_close` UND `price_high` UND `price_low` |

### 2. Zeithorizont-Wahl

| Zeithorizont | Empfohlene Schwelle | Use Case |
|--------------|---------------------|----------|
| 2-5 Min | 1-3% | Schnelle Scalping-Signale |
| 5-10 Min | 3-10% | Standard Pump Detection |
| 10-15 Min | 5-15% | Second Wave Detection |
| 15-30 Min | 10-25% | Langfristige Trends |

### 3. Balance-Strategie

| Situation | Empfehlung |
|-----------|------------|
| 1% positive Labels | `scale_pos_weight=100` |
| Sehr seltene Events | `scale_pos_weight=200` |
| Mehr Pumps erkennen | Höherer `scale_pos_weight` (mehr Fehlalarme) |
| Weniger Fehlalarme | Niedrigerer `scale_pos_weight` (weniger erkannte Pumps) |

### 4. Trainings-Zeitraum

| Zeitraum | Empfehlung |
|----------|------------|
| **Minimum** | 2 Stunden |
| **Optimal** | 8-12 Stunden |
| **Maximum** | 24+ Stunden (längere Wartezeit) |

---

## 🔧 Troubleshooting

### Problem: F1-Score = 0

**Ursache:** Zu wenig positive Labels oder keine Balance-Strategie.

**Lösung:**
1. Aktiviere `scale_pos_weight=100`
2. ODER senke `min_percent_change`
3. ODER erhöhe `future_minutes`

### Problem: Zu viele Fehlalarme

**Ursache:** `scale_pos_weight` zu hoch.

**Lösung:**
1. Senke `scale_pos_weight` (z.B. von 200 auf 100)
2. ODER erhöhe `min_percent_change`

### Problem: Keine Pumps erkannt

**Ursache:** `scale_pos_weight` zu niedrig oder Feature-Auswahl schlecht.

**Lösung:**
1. Erhöhe `scale_pos_weight` (z.B. auf 200)
2. Füge relevante Features hinzu: `buy_pressure_ratio`, `whale_buy_volume_sol`

### Problem: Training dauert zu lange

**Ursache:** Zu viele Features oder zu großer Zeitraum.

**Lösung:**
1. Reduziere Features auf 10-15
2. Reduziere Trainings-Zeitraum
3. Deaktiviere `use_engineered_features`

### Problem: "Keine Trainingsdaten gefunden"

**Ursache:** Der angegebene Zeitraum enthält keine Daten.

**Lösung:**
1. Prüfe ob der Zeitraum korrekt ist (UTC!)
2. Verwende einen Zeitraum mit bekannten Daten

---

## 📊 Response-Format

### Erfolgreiche Erstellung

```json
{
  "job_id": 424,
  "message": "Job erstellt. Modell 'MyModel' wird trainiert.",
  "status": "PENDING"
}
```

### Job-Status prüfen

```bash
GET /api/queue/{job_id}
```

```json
{
  "id": 424,
  "status": "COMPLETED",
  "result_model_id": 130,
  "progress": 100,
  "progress_msg": "Training abgeschlossen"
}
```

### Modell-Details abrufen

```bash
GET /api/models/{model_id}
```

---

## 🌐 Web UI

Die Web UI bietet dieselben Funktionen mit grafischer Oberfläche:

**URL:** https://test.local.chase295.de/training

Im Schritt 5 "Erweiterte Einstellungen" findest du:
- ⚖️ Klassen-Gewichtung (scale_pos_weight)
- Cross-Validation Einstellungen
- SMOTE Option
- Trainings-Zeitraum

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe die Job-Logs: `GET /api/queue/{job_id}`
2. Prüfe die Modell-Details: `GET /api/models/{model_id}`
3. Sieh dir die Confusion Matrix an für Einblicke in die Performance

---

**Dokumentation erstellt:** Januar 2026  
**Getestet:** 10/10 Tests bestanden ✅


## Vollständige Anleitung zur Modell-Erstellung

**Version:** 1.0  
**Stand:** Januar 2026  
**Endpoint:** `POST /api/models/create/advanced`

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Alle Parameter](#alle-parameter)
3. [Feature-Liste](#feature-liste)
4. [Balance-Optionen](#balance-optionen)
5. [Beispiele](#beispiele)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Der `/models/create/advanced` Endpoint ist der **vollständigste und flexibelste** Endpoint zur Erstellung von ML-Modellen für Pump-Detection.

### Was kann dieser Endpoint?

| Funktion | Beschreibung |
|----------|--------------|
| ✅ **Zeitbasierte Vorhersage** | "Steigt der Preis um X% in Y Minuten?" |
| ✅ **Feature Engineering** | 66 zusätzliche berechnete Features |
| ✅ **SMOTE** | Synthetisches Oversampling für unbalancierte Daten |
| ✅ **scale_pos_weight** | XGBoost-interne Klassen-Gewichtung |
| ✅ **Flexible Zeithorizonte** | 1 Minute bis 60+ Minuten |
| ✅ **Pump & Rug Detection** | Steigende oder fallende Preise vorhersagen |
| ✅ **Zwei Modell-Typen** | XGBoost und Random Forest |

---

## 📊 Alle Parameter

### Pflicht-Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `name` | string | Eindeutiger Modell-Name | `"Pump_Detector_v1"` |
| `model_type` | string | `xgboost` oder `random_forest` | `"xgboost"` |
| `features` | string | Komma-separierte Feature-Liste | `"price_close,volume_sol"` |
| `train_start` | string | Trainings-Startzeit (UTC, ISO-Format) | `"2026-01-07T06:00:00Z"` |
| `train_end` | string | Trainings-Endzeit (UTC, ISO-Format) | `"2026-01-07T18:00:00Z"` |

### Optionale Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `target_var` | string | `"price_close"` | Ziel-Variable für Vorhersage |
| `use_time_based_prediction` | bool | `true` | Zeitbasierte Vorhersage aktivieren |
| `future_minutes` | int | `5` | Vorhersage-Horizont in Minuten |
| `min_percent_change` | float | `2.0` | Minimale Preisänderung in % |
| `direction` | string | `"up"` | `"up"` für Pump, `"down"` für Rug |
| `use_engineered_features` | bool | `false` | Feature Engineering aktivieren (siehe [Feature Engineering Optionen](#feature-engineering-optionen)) |
| `use_flag_features` | bool | `true` | **NEU!** Flag-Features aktivieren (siehe [Flag-Features](#flag-features)) |
| `use_smote` | bool | `false` | SMOTE aktivieren |
| `scale_pos_weight` | float | `null` | XGBoost Klassen-Gewichtung |
| `class_weight` | string | `null` | `"balanced"` für Random Forest |
| `phases` | string | `null` | **NEU!** Coin-Phasen Filter (z.B. `"1,2,3"`) |

---

## 🔄 Coin-Phasen Filter (NEU!)

Mit dem `phases` Parameter kannst du das Training auf **bestimmte Coin-Entwicklungsphasen** beschränken.

### Verfügbare Phasen

| Phase ID | Name | Beschreibung | Alter |
|----------|------|--------------|-------|
| **1** | Baby Zone | Frisch erstellte Coins | 0-10 Min |
| **2** | Survival Zone | Überlebende Coins | 10-120 Min |
| **3** | Mature Zone | Reife Coins | 2-4 Stunden |
| **99** | Finished | Abgeschlossene Coins | - |
| **100** | Graduated | Graduierte Coins | - |

### Beispiele

```bash
# Nur Baby & Survival Zone (Phase 1 + 2)
phases=1,2

# Nur Mature Zone (Phase 3)
phases=3

# Alle aktiven Phasen (1, 2, 3)
phases=1,2,3
```

### Warum Phasen filtern?

| Use Case | Empfohlene Phasen | Grund |
|----------|-------------------|-------|
| **Second Wave Detection** | `1,2` | Pumps passieren früh |
| **Langfristige Trends** | `2,3` | Stabile Datenmuster |
| **Rug-Pull Detection** | `1` | Rugs passieren in Phase 1 |
| **Allgemein** | `1,2,3` | Maximale Datenmenge |

---

## 📊 Feature-Liste

### 28 Basis-Features (immer verfügbar)

⚠️ **WICHTIG:** Bei zeitbasierter Vorhersage wird `price_close` automatisch aus den Trainings-Features entfernt (verhindert Data Leakage). In diesem Fall sind es **27 Basis-Features** im Training.

#### Preis-Features (4)
```
price_open      - Eröffnungspreis der Minute
price_high      - Höchster Preis der Minute
price_low       - Niedrigster Preis der Minute
price_close     - Schlusskurs der Minute
```

#### Volume-Features (4)
```
volume_sol          - Gesamtes Handelsvolumen in SOL
buy_volume_sol      - Kaufvolumen in SOL
sell_volume_sol     - Verkaufsvolumen in SOL
net_volume_sol      - Netto-Volumen (Buy - Sell)
```

#### Market-Features (4)
```
market_cap_close        - Marktkapitalisierung
bonding_curve_pct       - Position auf der Bonding Curve (%)
virtual_sol_reserves    - Virtuelle SOL-Reserven
is_koth                 - King of the Hill Status (0/1)
```

#### Trade-Statistiken (4)
```
num_buys            - Anzahl Buy-Trades
num_sells           - Anzahl Sell-Trades
unique_wallets      - Einzigartige Wallet-Adressen
num_micro_trades    - Anzahl Mikro-Trades
```

#### Max Trade Sizes (2)
```
max_single_buy_sol      - Größter einzelner Kauf
max_single_sell_sol     - Größter einzelner Verkauf
```

#### Whale-Features (4)
```
whale_buy_volume_sol    - Whale-Kaufvolumen
whale_sell_volume_sol   - Whale-Verkaufsvolumen
num_whale_buys          - Anzahl Whale-Käufe
num_whale_sells         - Anzahl Whale-Verkäufe
```

#### Qualitäts-Features (4)
```
dev_sold_amount     - Vom Developer verkaufte Menge
volatility_pct      - Preisvolatilität in %
avg_trade_size_sol  - Durchschnittliche Trade-Größe
buy_pressure_ratio  - Kaufdruck-Verhältnis (0-1)
```

#### Wallet-Analyse (2)
```
unique_signer_ratio     - Verhältnis einzigartiger Signaturen
phase_id_at_time        - Coin-Phase (1-6)
```

---

## 🚩 Flag-Features (NEU!)

Flag-Features sind **Datenverfügbarkeits-Indikatoren**, die dem Modell anzeigen, ob ein Engineering-Feature genug historische Daten hat, um zuverlässig berechnet zu werden.

### Was sind Flag-Features?

Jedes window-basierte Engineering-Feature (z.B. `buy_pressure_ma_5`) erhält ein entsprechendes Flag-Feature (z.B. `buy_pressure_ma_5_has_data`), das anzeigt:
- **`1`** = Genug Daten vorhanden (Feature ist zuverlässig)
- **`0`** = Nicht genug Daten (Feature könnte unzuverlässig sein)

### Warum Flag-Features?

| Problem | Lösung mit Flag-Features |
|---------|-------------------------|
| Neue Coins haben keine 15-Minuten-Historie | Modell lernt, dass `buy_pressure_ma_15_has_data=0` bedeutet: Feature ignorieren |
| NaN-Werte in Engineering-Features | Flag zeigt dem Modell, ob NaN = "keine Daten" oder "echter Wert" |
| Unzuverlässige Features bei jungen Coins | Modell kann Features basierend auf Datenverfügbarkeit gewichten |

### Aktivierung

Flag-Features werden automatisch aktiviert, wenn:
1. `use_engineered_features=true` **UND**
2. `use_flag_features=true` (Default: `true`)

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering + **57 Flag-Features = 150 Features total**

### Deaktivierung

Wenn du Flag-Features nicht möchtest:
```bash
use_flag_features=false
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering = 93 Features total (ohne Flags)

---

## 🚩 Alle 57 Flag-Features

### Dev-Sold Flag-Features (3)
```
dev_sold_spike_5_has_data      - Hat Coin genug Daten für Dev-Sold Spike (5 Min)?
dev_sold_spike_10_has_data     - Hat Coin genug Daten für Dev-Sold Spike (10 Min)?
dev_sold_spike_15_has_data     - Hat Coin genug Daten für Dev-Sold Spike (15 Min)?
```

### Buy Pressure Flag-Features (6)
```
buy_pressure_ma_5_has_data     - Hat Coin genug Daten für Buy Pressure MA (5 Min)?
buy_pressure_ma_10_has_data   - Hat Coin genug Daten für Buy Pressure MA (10 Min)?
buy_pressure_ma_15_has_data   - Hat Coin genug Daten für Buy Pressure MA (15 Min)?
buy_pressure_trend_5_has_data  - Hat Coin genug Daten für Buy Pressure Trend (5 Min)?
buy_pressure_trend_10_has_data - Hat Coin genug Daten für Buy Pressure Trend (10 Min)?
buy_pressure_trend_15_has_data - Hat Coin genug Daten für Buy Pressure Trend (15 Min)?
```

### Whale Activity Flag-Features (3)
```
whale_activity_5_has_data      - Hat Coin genug Daten für Whale Activity (5 Min)?
whale_activity_10_has_data    - Hat Coin genug Daten für Whale Activity (10 Min)?
whale_activity_15_has_data    - Hat Coin genug Daten für Whale Activity (15 Min)?
```

### Volatility Flag-Features (6)
```
volatility_ma_5_has_data      - Hat Coin genug Daten für Volatility MA (5 Min)?
volatility_ma_10_has_data    - Hat Coin genug Daten für Volatility MA (10 Min)?
volatility_ma_15_has_data    - Hat Coin genug Daten für Volatility MA (15 Min)?
volatility_spike_5_has_data   - Hat Coin genug Daten für Volatility Spike (5 Min)?
volatility_spike_10_has_data - Hat Coin genug Daten für Volatility Spike (10 Min)?
volatility_spike_15_has_data - Hat Coin genug Daten für Volatility Spike (15 Min)?
```

### Wash Trading Flag-Features (3)
```
wash_trading_flag_5_has_data  - Hat Coin genug Daten für Wash Trading Detection (5 Min)?
wash_trading_flag_10_has_data - Hat Coin genug Daten für Wash Trading Detection (10 Min)?
wash_trading_flag_15_has_data - Hat Coin genug Daten für Wash Trading Detection (15 Min)?
```

### Volume Pattern Flag-Features (6)
```
net_volume_ma_5_has_data      - Hat Coin genug Daten für Net Volume MA (5 Min)?
net_volume_ma_10_has_data    - Hat Coin genug Daten für Net Volume MA (10 Min)?
net_volume_ma_15_has_data    - Hat Coin genug Daten für Net Volume MA (15 Min)?
volume_flip_5_has_data       - Hat Coin genug Daten für Volume Flip (5 Min)?
volume_flip_10_has_data      - Hat Coin genug Daten für Volume Flip (10 Min)?
volume_flip_15_has_data      - Hat Coin genug Daten für Volume Flip (15 Min)?
```

### Price Momentum Flag-Features (6)
```
price_change_5_has_data      - Hat Coin genug Daten für Price Change (5 Min)?
price_change_10_has_data    - Hat Coin genug Daten für Price Change (10 Min)?
price_change_15_has_data    - Hat Coin genug Daten für Price Change (15 Min)?
price_roc_5_has_data         - Hat Coin genug Daten für Price ROC (5 Min)?
price_roc_10_has_data        - Hat Coin genug Daten für Price ROC (10 Min)?
price_roc_15_has_data        - Hat Coin genug Daten für Price ROC (15 Min)?
```

### Price Acceleration Flag-Features (3)
```
price_acceleration_5_has_data  - Hat Coin genug Daten für Price Acceleration (5 Min)?
price_acceleration_10_has_data - Hat Coin genug Daten für Price Acceleration (10 Min)?
price_acceleration_15_has_data - Hat Coin genug Daten für Price Acceleration (15 Min)?
```

### Market Cap Velocity Flag-Features (3)
```
mcap_velocity_5_has_data      - Hat Coin genug Daten für Market Cap Velocity (5 Min)?
mcap_velocity_10_has_data    - Hat Coin genug Daten für Market Cap Velocity (10 Min)?
mcap_velocity_15_has_data    - Hat Coin genug Daten für Market Cap Velocity (15 Min)?
```

### ATH Flag-Features (15)
```
ath_distance_trend_5_has_data         - Hat Coin genug Daten für ATH Distance Trend (5 Min)?
ath_distance_trend_10_has_data        - Hat Coin genug Daten für ATH Distance Trend (10 Min)?
ath_distance_trend_15_has_data       - Hat Coin genug Daten für ATH Distance Trend (15 Min)?
ath_approach_5_has_data              - Hat Coin genug Daten für ATH Approach (5 Min)?
ath_approach_10_has_data             - Hat Coin genug Daten für ATH Approach (10 Min)?
ath_approach_15_has_data             - Hat Coin genug Daten für ATH Approach (15 Min)?
ath_breakout_count_5_has_data         - Hat Coin genug Daten für ATH Breakout Count (5 Min)?
ath_breakout_count_10_has_data       - Hat Coin genug Daten für ATH Breakout Count (10 Min)?
ath_breakout_count_15_has_data       - Hat Coin genug Daten für ATH Breakout Count (15 Min)?
ath_breakout_volume_ma_5_has_data     - Hat Coin genug Daten für ATH Breakout Volume MA (5 Min)?
ath_breakout_volume_ma_10_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (10 Min)?
ath_breakout_volume_ma_15_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (15 Min)?
ath_age_trend_5_has_data             - Hat Coin genug Daten für ATH Age Trend (5 Min)?
ath_age_trend_10_has_data            - Hat Coin genug Daten für ATH Age Trend (10 Min)?
ath_age_trend_15_has_data            - Hat Coin genug Daten für ATH Age Trend (15 Min)?
```

### Volume Spike Flag-Features (3)
```
volume_spike_5_has_data      - Hat Coin genug Daten für Volume Spike (5 Min)?
volume_spike_10_has_data    - Hat Coin genug Daten für Volume Spike (10 Min)?
volume_spike_15_has_data    - Hat Coin genug Daten für Volume Spike (15 Min)?
```

### Zusammenfassung Flag-Features

| Kategorie | Anzahl | Window-Größen |
|-----------|--------|---------------|
| Dev-Sold | 3 | 5, 10, 15 Min |
| Buy Pressure | 6 | 5, 10, 15 Min (MA + Trend) |
| Whale Activity | 3 | 5, 10, 15 Min |
| Volatility | 6 | 5, 10, 15 Min (MA + Spike) |
| Wash Trading | 3 | 5, 10, 15 Min |
| Volume Pattern | 6 | 5, 10, 15 Min (Net Volume MA + Volume Flip) |
| Price Momentum | 6 | 5, 10, 15 Min (Change + ROC) |
| Price Acceleration | 3 | 5, 10, 15 Min |
| Market Cap Velocity | 3 | 5, 10, 15 Min |
| ATH Features | 15 | 5, 10, 15 Min (5 verschiedene ATH-Features) |
| Volume Spike | 3 | 5, 10, 15 Min |
| **GESAMT** | **57** | - |

---

## 🔧 Feature Engineering Optionen

Der `use_engineered_features` Parameter bietet **3 verschiedene Modi**:

### Option 1: Keine Engineering-Features (Default)

**Verhalten:** Nur die Basis-Features werden verwendet, die du in der `features` Liste angibst.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&
  use_engineered_features=false
  # oder einfach weglassen (Default ist false)
```

**Ergebnis:** 4 Features total (nur Basis-Features)

---

### Option 2: Spezifische Engineering-Features auswählen

**Verhalten:** Du gibst explizit Engineering-Features in der `features` Liste an. Das Backend erstellt nur diese.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume&
  use_engineered_features=true
```

**Ergebnis:** 5 Features total (2 Basis + 3 Engineering)

**Vorteil:** Du hast volle Kontrolle über welche Engineering-Features verwendet werden.

---

### Option 3: Alle Engineering-Features (66 Stück)

**Verhalten:** Wenn `use_engineered_features=true` ist, aber **keine** Engineering-Features in der `features` Liste stehen, werden automatisch **alle 66 Engineering-Features** erstellt.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true
```

**Ergebnis:** 68 Features total (2 Basis + 66 Engineering)

**Vorteil:** Maximale Feature-Abdeckung ohne manuelle Auswahl.

---

### Zusammenfassung

| Modus | `use_engineered_features` | Engineering-Features in `features` | Ergebnis |
|-------|---------------------------|-----------------------------------|----------|
| **Keine** | `false` oder weglassen | - | Nur Basis-Features |
| **Spezifische** | `true` | ✅ Ja (z.B. `dev_sold_spike_5`) | Nur die angegebenen Engineering-Features |
| **Alle** | `true` | ❌ Nein | Alle 66 Engineering-Features |

---

### 66 Engineering-Features (mit `use_engineered_features=true`)

#### Dev-Sold Features (6)
```
dev_sold_flag           - Hat der Dev verkauft? (0/1)
dev_sold_cumsum         - Kumulative Dev-Verkäufe
dev_sold_spike_5        - Dev-Verkauf-Spike (5 Min)
dev_sold_spike_10       - Dev-Verkauf-Spike (10 Min)
dev_sold_spike_15       - Dev-Verkauf-Spike (15 Min)
```

#### Buy Pressure Features (6)
```
buy_pressure_ma_5       - Moving Average (5 Min)
buy_pressure_trend_5    - Trend (5 Min)
buy_pressure_ma_10      - Moving Average (10 Min)
buy_pressure_trend_10   - Trend (10 Min)
buy_pressure_ma_15      - Moving Average (15 Min)
buy_pressure_trend_15   - Trend (15 Min)
```

#### Whale Activity Features (4)
```
whale_net_volume        - Netto Whale-Volume
whale_activity_5        - Whale-Aktivität (5 Min)
whale_activity_10       - Whale-Aktivität (10 Min)
whale_activity_15       - Whale-Aktivität (15 Min)
```

#### Volatility Features (6)
```
volatility_ma_5         - Volatilität MA (5 Min)
volatility_spike_5      - Volatilität-Spike (5 Min)
volatility_ma_10        - Volatilität MA (10 Min)
volatility_spike_10     - Volatilität-Spike (10 Min)
volatility_ma_15        - Volatilität MA (15 Min)
volatility_spike_15     - Volatilität-Spike (15 Min)
```

#### Wash Trading Detection (3)
```
wash_trading_flag_5     - Wash Trading erkannt? (5 Min)
wash_trading_flag_10    - Wash Trading erkannt? (10 Min)
wash_trading_flag_15    - Wash Trading erkannt? (15 Min)
```

#### Volume Pattern Features (6)
```
net_volume_ma_5         - Netto-Volume MA (5 Min)
volume_flip_5           - Volume Flip (5 Min)
net_volume_ma_10        - Netto-Volume MA (10 Min)
volume_flip_10          - Volume Flip (10 Min)
net_volume_ma_15        - Netto-Volume MA (15 Min)
volume_flip_15          - Volume Flip (15 Min)
```

#### Price Momentum Features (6)
```
price_change_5          - Preisänderung (5 Min)
price_roc_5             - Rate of Change (5 Min)
price_change_10         - Preisänderung (10 Min)
price_roc_10            - Rate of Change (10 Min)
price_change_15         - Preisänderung (15 Min)
price_roc_15            - Rate of Change (15 Min)
```

#### Market Cap Velocity (3)
```
mcap_velocity_5         - MarketCap Änderungsrate (5 Min)
mcap_velocity_10        - MarketCap Änderungsrate (10 Min)
mcap_velocity_15        - MarketCap Änderungsrate (15 Min)
```

#### ATH Features (19)
```
rolling_ath             - Rolling All-Time-High
price_vs_ath_pct        - Distanz zum ATH in %
ath_breakout            - ATH durchbrochen? (0/1)
minutes_since_ath       - Minuten seit letztem ATH
ath_distance_trend_5    - ATH-Distanz Trend (5 Min)
ath_approach_5          - Nähert sich ATH? (5 Min)
ath_breakout_count_5    - ATH-Durchbrüche (5 Min)
ath_breakout_volume_ma_5 - Volume bei ATH-Breaks (5 Min)
ath_age_trend_5         - ATH-Alter Trend (5 Min)
... (analog für 10 und 15 Minuten)
```

#### Power Features (8)
```
buy_sell_ratio          - Buy/Sell Verhältnis
whale_dominance         - Whale-Anteil am Volume
price_acceleration_5    - Preis-Beschleunigung (5 Min)
price_acceleration_10   - Preis-Beschleunigung (10 Min)
price_acceleration_15   - Preis-Beschleunigung (15 Min)
volume_spike_5          - Volume-Spike (5 Min)
volume_spike_10         - Volume-Spike (10 Min)
volume_spike_15         - Volume-Spike (15 Min)
```

---

## ⚖️ Balance-Optionen

### Das Problem: Unbalancierte Daten

Bei Pump-Detection sind positive Labels (Pumps) sehr selten (oft nur 1-5% der Daten). Das führt dazu, dass Modelle einfach "Nein" für alles vorhersagen.

### Lösung 1: `scale_pos_weight` (✅ EMPFOHLEN)

XGBoost-intern, gewichtet die positive Klasse höher.

| Positive Labels | scale_pos_weight | Effekt |
|-----------------|------------------|--------|
| 0.5% | `200` | Sehr aggressiv |
| 1% | `100` | Standard |
| 2% | `50` | Moderat |
| 5% | `20` | Konservativ |

**Beispiel:**
```bash
scale_pos_weight=100
```

**Vorteile:**
- Keine synthetischen Daten
- Schneller als SMOTE
- Besser generalisierbar

### Lösung 2: `use_smote` (⚠️ Mit Vorsicht)

Synthetisches Oversampling - erstellt künstliche positive Samples.

**Beispiel:**
```bash
use_smote=true
```

**Nachteile:**
- Kann zu Overfitting führen
- Modell lernt synthetische statt echte Muster

### Lösung 3: `class_weight` (für Random Forest)

```bash
class_weight=balanced
```

---

## 📝 Beispiele

### Beispiel 1: Einfaches Pump-Modell

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio&\
future_minutes=5&\
min_percent_change=2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 2: Mit ALLEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 2c: Mit ALLEN Engineering-Features OHNE Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_No_Flags_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=false&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 70 Features (4 Basis + 66 Engineering, keine Flag-Features)

### Beispiel 2b: Mit SPEZIFISCHEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Selective_Engineering_v1&\
model_type=xgboost&\
features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume,volatility_spike_15&\
use_engineered_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 8 Features (2 Basis + 4 Engineering + **4 Flag-Features** - nur die für die ausgewählten Engineering-Features!)

**Wichtig:** Das System verwendet automatisch nur die Flag-Features, die zu den ausgewählten Engineering-Features gehören:
- `dev_sold_spike_5_has_data` (für `dev_sold_spike_5`)
- `buy_pressure_ma_10_has_data` (für `buy_pressure_ma_10`)
- `volatility_spike_15_has_data` (für `volatility_spike_15`)
- `whale_net_volume` hat kein Flag-Feature (ist kein window-basiertes Feature)

### Beispiel 3: OHNE Engineering-Features (nur Basis)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol&\
use_engineered_features=false&\
scale_pos_weight=100&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 5 Features (nur Basis-Features, keine Engineering)

### Beispiel 4: Mit scale_pos_weight (EMPFOHLEN)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Balanced_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 5: ULTIMATIV (Alle Features + Engineering + Flag-Features + Balance)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Ultimate_Pump_Detector&\
model_type=xgboost&\
features=price_open,price_high,price_low,price_close,volume_sol,buy_volume_sol,sell_volume_sol,net_volume_sol,market_cap_close,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct,unique_signer_ratio&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=15&\
direction=up&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 137 Features (14 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 5: Rug-Pull Detection

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Rug_Pull_Detector&\
model_type=xgboost&\
features=price_close,dev_sold_amount,buy_pressure_ratio,whale_sell_volume_sol&\
direction=down&\
min_percent_change=20&\
future_minutes=15&\
scale_pos_weight=50&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 6: Random Forest

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=RF_Pump_Detector&\
model_type=random_forest&\
features=price_close,volume_sol,buy_pressure_ratio&\
class_weight=balanced&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 7: Second Wave Detection (mit Flag-Features)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Second_Wave_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
future_minutes=15&\
min_percent_change=10&\
phases=1,2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 129 Features (6 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 8: Nur Baby Zone (Phase 1)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Baby_Zone_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
phases=1&\
scale_pos_weight=150&\
future_minutes=5&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 9: Survival + Mature Zone (Phase 2+3) mit Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Mature_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
phases=2,3&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=80&\
future_minutes=15&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

---

## 💡 Best Practices

### 1. Feature-Auswahl

| Empfehlung | Beschreibung |
|------------|--------------|
| ✅ Start mit Basis-Features | Beginne mit 5-10 wichtigen Features |
| ✅ Wichtigste Features zuerst | `price_close`, `volume_sol`, `buy_pressure_ratio` |
| ✅ Flag-Features aktivieren | Verbessert Modell-Performance bei neuen Coins |
| ⚠️ Nicht zu viele Features | Mehr als 30 Basis-Features kann zu Overfitting führen |
| ⚠️ Mit Engineering + Flags | Bis zu 150 Features möglich (27 Base + 66 Eng + 57 Flags bei zeitbasierter Vorhersage) oder 151 Features (28 Base + 66 Eng + 57 Flags ohne zeitbasierte Vorhersage) |
| ❌ Keine redundanten Features | z.B. nicht `price_open` UND `price_close` UND `price_high` UND `price_low` |

### 2. Zeithorizont-Wahl

| Zeithorizont | Empfohlene Schwelle | Use Case |
|--------------|---------------------|----------|
| 2-5 Min | 1-3% | Schnelle Scalping-Signale |
| 5-10 Min | 3-10% | Standard Pump Detection |
| 10-15 Min | 5-15% | Second Wave Detection |
| 15-30 Min | 10-25% | Langfristige Trends |

### 3. Balance-Strategie

| Situation | Empfehlung |
|-----------|------------|
| 1% positive Labels | `scale_pos_weight=100` |
| Sehr seltene Events | `scale_pos_weight=200` |
| Mehr Pumps erkennen | Höherer `scale_pos_weight` (mehr Fehlalarme) |
| Weniger Fehlalarme | Niedrigerer `scale_pos_weight` (weniger erkannte Pumps) |

### 4. Trainings-Zeitraum

| Zeitraum | Empfehlung |
|----------|------------|
| **Minimum** | 2 Stunden |
| **Optimal** | 8-12 Stunden |
| **Maximum** | 24+ Stunden (längere Wartezeit) |

---

## 🔧 Troubleshooting

### Problem: F1-Score = 0

**Ursache:** Zu wenig positive Labels oder keine Balance-Strategie.

**Lösung:**
1. Aktiviere `scale_pos_weight=100`
2. ODER senke `min_percent_change`
3. ODER erhöhe `future_minutes`

### Problem: Zu viele Fehlalarme

**Ursache:** `scale_pos_weight` zu hoch.

**Lösung:**
1. Senke `scale_pos_weight` (z.B. von 200 auf 100)
2. ODER erhöhe `min_percent_change`

### Problem: Keine Pumps erkannt

**Ursache:** `scale_pos_weight` zu niedrig oder Feature-Auswahl schlecht.

**Lösung:**
1. Erhöhe `scale_pos_weight` (z.B. auf 200)
2. Füge relevante Features hinzu: `buy_pressure_ratio`, `whale_buy_volume_sol`

### Problem: Training dauert zu lange

**Ursache:** Zu viele Features oder zu großer Zeitraum.

**Lösung:**
1. Reduziere Features auf 10-15
2. Reduziere Trainings-Zeitraum
3. Deaktiviere `use_engineered_features`

### Problem: "Keine Trainingsdaten gefunden"

**Ursache:** Der angegebene Zeitraum enthält keine Daten.

**Lösung:**
1. Prüfe ob der Zeitraum korrekt ist (UTC!)
2. Verwende einen Zeitraum mit bekannten Daten

---

## 📊 Response-Format

### Erfolgreiche Erstellung

```json
{
  "job_id": 424,
  "message": "Job erstellt. Modell 'MyModel' wird trainiert.",
  "status": "PENDING"
}
```

### Job-Status prüfen

```bash
GET /api/queue/{job_id}
```

```json
{
  "id": 424,
  "status": "COMPLETED",
  "result_model_id": 130,
  "progress": 100,
  "progress_msg": "Training abgeschlossen"
}
```

### Modell-Details abrufen

```bash
GET /api/models/{model_id}
```

---

## 🌐 Web UI

Die Web UI bietet dieselben Funktionen mit grafischer Oberfläche:

**URL:** https://test.local.chase295.de/training

Im Schritt 5 "Erweiterte Einstellungen" findest du:
- ⚖️ Klassen-Gewichtung (scale_pos_weight)
- Cross-Validation Einstellungen
- SMOTE Option
- Trainings-Zeitraum

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe die Job-Logs: `GET /api/queue/{job_id}`
2. Prüfe die Modell-Details: `GET /api/models/{model_id}`
3. Sieh dir die Confusion Matrix an für Einblicke in die Performance

---

**Dokumentation erstellt:** Januar 2026  
**Getestet:** 10/10 Tests bestanden ✅


## Vollständige Anleitung zur Modell-Erstellung

**Version:** 1.0  
**Stand:** Januar 2026  
**Endpoint:** `POST /api/models/create/advanced`

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Alle Parameter](#alle-parameter)
3. [Feature-Liste](#feature-liste)
4. [Balance-Optionen](#balance-optionen)
5. [Beispiele](#beispiele)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Der `/models/create/advanced` Endpoint ist der **vollständigste und flexibelste** Endpoint zur Erstellung von ML-Modellen für Pump-Detection.

### Was kann dieser Endpoint?

| Funktion | Beschreibung |
|----------|--------------|
| ✅ **Zeitbasierte Vorhersage** | "Steigt der Preis um X% in Y Minuten?" |
| ✅ **Feature Engineering** | 66 zusätzliche berechnete Features |
| ✅ **SMOTE** | Synthetisches Oversampling für unbalancierte Daten |
| ✅ **scale_pos_weight** | XGBoost-interne Klassen-Gewichtung |
| ✅ **Flexible Zeithorizonte** | 1 Minute bis 60+ Minuten |
| ✅ **Pump & Rug Detection** | Steigende oder fallende Preise vorhersagen |
| ✅ **Zwei Modell-Typen** | XGBoost und Random Forest |

---

## 📊 Alle Parameter

### Pflicht-Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `name` | string | Eindeutiger Modell-Name | `"Pump_Detector_v1"` |
| `model_type` | string | `xgboost` oder `random_forest` | `"xgboost"` |
| `features` | string | Komma-separierte Feature-Liste | `"price_close,volume_sol"` |
| `train_start` | string | Trainings-Startzeit (UTC, ISO-Format) | `"2026-01-07T06:00:00Z"` |
| `train_end` | string | Trainings-Endzeit (UTC, ISO-Format) | `"2026-01-07T18:00:00Z"` |

### Optionale Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `target_var` | string | `"price_close"` | Ziel-Variable für Vorhersage |
| `use_time_based_prediction` | bool | `true` | Zeitbasierte Vorhersage aktivieren |
| `future_minutes` | int | `5` | Vorhersage-Horizont in Minuten |
| `min_percent_change` | float | `2.0` | Minimale Preisänderung in % |
| `direction` | string | `"up"` | `"up"` für Pump, `"down"` für Rug |
| `use_engineered_features` | bool | `false` | Feature Engineering aktivieren (siehe [Feature Engineering Optionen](#feature-engineering-optionen)) |
| `use_flag_features` | bool | `true` | **NEU!** Flag-Features aktivieren (siehe [Flag-Features](#flag-features)) |
| `use_smote` | bool | `false` | SMOTE aktivieren |
| `scale_pos_weight` | float | `null` | XGBoost Klassen-Gewichtung |
| `class_weight` | string | `null` | `"balanced"` für Random Forest |
| `phases` | string | `null` | **NEU!** Coin-Phasen Filter (z.B. `"1,2,3"`) |

---

## 🔄 Coin-Phasen Filter (NEU!)

Mit dem `phases` Parameter kannst du das Training auf **bestimmte Coin-Entwicklungsphasen** beschränken.

### Verfügbare Phasen

| Phase ID | Name | Beschreibung | Alter |
|----------|------|--------------|-------|
| **1** | Baby Zone | Frisch erstellte Coins | 0-10 Min |
| **2** | Survival Zone | Überlebende Coins | 10-120 Min |
| **3** | Mature Zone | Reife Coins | 2-4 Stunden |
| **99** | Finished | Abgeschlossene Coins | - |
| **100** | Graduated | Graduierte Coins | - |

### Beispiele

```bash
# Nur Baby & Survival Zone (Phase 1 + 2)
phases=1,2

# Nur Mature Zone (Phase 3)
phases=3

# Alle aktiven Phasen (1, 2, 3)
phases=1,2,3
```

### Warum Phasen filtern?

| Use Case | Empfohlene Phasen | Grund |
|----------|-------------------|-------|
| **Second Wave Detection** | `1,2` | Pumps passieren früh |
| **Langfristige Trends** | `2,3` | Stabile Datenmuster |
| **Rug-Pull Detection** | `1` | Rugs passieren in Phase 1 |
| **Allgemein** | `1,2,3` | Maximale Datenmenge |

---

## 📊 Feature-Liste

### 28 Basis-Features (immer verfügbar)

⚠️ **WICHTIG:** Bei zeitbasierter Vorhersage wird `price_close` automatisch aus den Trainings-Features entfernt (verhindert Data Leakage). In diesem Fall sind es **27 Basis-Features** im Training.

#### Preis-Features (4)
```
price_open      - Eröffnungspreis der Minute
price_high      - Höchster Preis der Minute
price_low       - Niedrigster Preis der Minute
price_close     - Schlusskurs der Minute
```

#### Volume-Features (4)
```
volume_sol          - Gesamtes Handelsvolumen in SOL
buy_volume_sol      - Kaufvolumen in SOL
sell_volume_sol     - Verkaufsvolumen in SOL
net_volume_sol      - Netto-Volumen (Buy - Sell)
```

#### Market-Features (4)
```
market_cap_close        - Marktkapitalisierung
bonding_curve_pct       - Position auf der Bonding Curve (%)
virtual_sol_reserves    - Virtuelle SOL-Reserven
is_koth                 - King of the Hill Status (0/1)
```

#### Trade-Statistiken (4)
```
num_buys            - Anzahl Buy-Trades
num_sells           - Anzahl Sell-Trades
unique_wallets      - Einzigartige Wallet-Adressen
num_micro_trades    - Anzahl Mikro-Trades
```

#### Max Trade Sizes (2)
```
max_single_buy_sol      - Größter einzelner Kauf
max_single_sell_sol     - Größter einzelner Verkauf
```

#### Whale-Features (4)
```
whale_buy_volume_sol    - Whale-Kaufvolumen
whale_sell_volume_sol   - Whale-Verkaufsvolumen
num_whale_buys          - Anzahl Whale-Käufe
num_whale_sells         - Anzahl Whale-Verkäufe
```

#### Qualitäts-Features (4)
```
dev_sold_amount     - Vom Developer verkaufte Menge
volatility_pct      - Preisvolatilität in %
avg_trade_size_sol  - Durchschnittliche Trade-Größe
buy_pressure_ratio  - Kaufdruck-Verhältnis (0-1)
```

#### Wallet-Analyse (2)
```
unique_signer_ratio     - Verhältnis einzigartiger Signaturen
phase_id_at_time        - Coin-Phase (1-6)
```

---

## 🚩 Flag-Features (NEU!)

Flag-Features sind **Datenverfügbarkeits-Indikatoren**, die dem Modell anzeigen, ob ein Engineering-Feature genug historische Daten hat, um zuverlässig berechnet zu werden.

### Was sind Flag-Features?

Jedes window-basierte Engineering-Feature (z.B. `buy_pressure_ma_5`) erhält ein entsprechendes Flag-Feature (z.B. `buy_pressure_ma_5_has_data`), das anzeigt:
- **`1`** = Genug Daten vorhanden (Feature ist zuverlässig)
- **`0`** = Nicht genug Daten (Feature könnte unzuverlässig sein)

### Warum Flag-Features?

| Problem | Lösung mit Flag-Features |
|---------|-------------------------|
| Neue Coins haben keine 15-Minuten-Historie | Modell lernt, dass `buy_pressure_ma_15_has_data=0` bedeutet: Feature ignorieren |
| NaN-Werte in Engineering-Features | Flag zeigt dem Modell, ob NaN = "keine Daten" oder "echter Wert" |
| Unzuverlässige Features bei jungen Coins | Modell kann Features basierend auf Datenverfügbarkeit gewichten |

### Aktivierung

Flag-Features werden automatisch aktiviert, wenn:
1. `use_engineered_features=true` **UND**
2. `use_flag_features=true` (Default: `true`)

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering + **57 Flag-Features = 150 Features total**

### Deaktivierung

Wenn du Flag-Features nicht möchtest:
```bash
use_flag_features=false
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering = 93 Features total (ohne Flags)

---

## 🚩 Alle 57 Flag-Features

### Dev-Sold Flag-Features (3)
```
dev_sold_spike_5_has_data      - Hat Coin genug Daten für Dev-Sold Spike (5 Min)?
dev_sold_spike_10_has_data     - Hat Coin genug Daten für Dev-Sold Spike (10 Min)?
dev_sold_spike_15_has_data     - Hat Coin genug Daten für Dev-Sold Spike (15 Min)?
```

### Buy Pressure Flag-Features (6)
```
buy_pressure_ma_5_has_data     - Hat Coin genug Daten für Buy Pressure MA (5 Min)?
buy_pressure_ma_10_has_data   - Hat Coin genug Daten für Buy Pressure MA (10 Min)?
buy_pressure_ma_15_has_data   - Hat Coin genug Daten für Buy Pressure MA (15 Min)?
buy_pressure_trend_5_has_data  - Hat Coin genug Daten für Buy Pressure Trend (5 Min)?
buy_pressure_trend_10_has_data - Hat Coin genug Daten für Buy Pressure Trend (10 Min)?
buy_pressure_trend_15_has_data - Hat Coin genug Daten für Buy Pressure Trend (15 Min)?
```

### Whale Activity Flag-Features (3)
```
whale_activity_5_has_data      - Hat Coin genug Daten für Whale Activity (5 Min)?
whale_activity_10_has_data    - Hat Coin genug Daten für Whale Activity (10 Min)?
whale_activity_15_has_data    - Hat Coin genug Daten für Whale Activity (15 Min)?
```

### Volatility Flag-Features (6)
```
volatility_ma_5_has_data      - Hat Coin genug Daten für Volatility MA (5 Min)?
volatility_ma_10_has_data    - Hat Coin genug Daten für Volatility MA (10 Min)?
volatility_ma_15_has_data    - Hat Coin genug Daten für Volatility MA (15 Min)?
volatility_spike_5_has_data   - Hat Coin genug Daten für Volatility Spike (5 Min)?
volatility_spike_10_has_data - Hat Coin genug Daten für Volatility Spike (10 Min)?
volatility_spike_15_has_data - Hat Coin genug Daten für Volatility Spike (15 Min)?
```

### Wash Trading Flag-Features (3)
```
wash_trading_flag_5_has_data  - Hat Coin genug Daten für Wash Trading Detection (5 Min)?
wash_trading_flag_10_has_data - Hat Coin genug Daten für Wash Trading Detection (10 Min)?
wash_trading_flag_15_has_data - Hat Coin genug Daten für Wash Trading Detection (15 Min)?
```

### Volume Pattern Flag-Features (6)
```
net_volume_ma_5_has_data      - Hat Coin genug Daten für Net Volume MA (5 Min)?
net_volume_ma_10_has_data    - Hat Coin genug Daten für Net Volume MA (10 Min)?
net_volume_ma_15_has_data    - Hat Coin genug Daten für Net Volume MA (15 Min)?
volume_flip_5_has_data       - Hat Coin genug Daten für Volume Flip (5 Min)?
volume_flip_10_has_data      - Hat Coin genug Daten für Volume Flip (10 Min)?
volume_flip_15_has_data      - Hat Coin genug Daten für Volume Flip (15 Min)?
```

### Price Momentum Flag-Features (6)
```
price_change_5_has_data      - Hat Coin genug Daten für Price Change (5 Min)?
price_change_10_has_data    - Hat Coin genug Daten für Price Change (10 Min)?
price_change_15_has_data    - Hat Coin genug Daten für Price Change (15 Min)?
price_roc_5_has_data         - Hat Coin genug Daten für Price ROC (5 Min)?
price_roc_10_has_data        - Hat Coin genug Daten für Price ROC (10 Min)?
price_roc_15_has_data        - Hat Coin genug Daten für Price ROC (15 Min)?
```

### Price Acceleration Flag-Features (3)
```
price_acceleration_5_has_data  - Hat Coin genug Daten für Price Acceleration (5 Min)?
price_acceleration_10_has_data - Hat Coin genug Daten für Price Acceleration (10 Min)?
price_acceleration_15_has_data - Hat Coin genug Daten für Price Acceleration (15 Min)?
```

### Market Cap Velocity Flag-Features (3)
```
mcap_velocity_5_has_data      - Hat Coin genug Daten für Market Cap Velocity (5 Min)?
mcap_velocity_10_has_data    - Hat Coin genug Daten für Market Cap Velocity (10 Min)?
mcap_velocity_15_has_data    - Hat Coin genug Daten für Market Cap Velocity (15 Min)?
```

### ATH Flag-Features (15)
```
ath_distance_trend_5_has_data         - Hat Coin genug Daten für ATH Distance Trend (5 Min)?
ath_distance_trend_10_has_data        - Hat Coin genug Daten für ATH Distance Trend (10 Min)?
ath_distance_trend_15_has_data       - Hat Coin genug Daten für ATH Distance Trend (15 Min)?
ath_approach_5_has_data              - Hat Coin genug Daten für ATH Approach (5 Min)?
ath_approach_10_has_data             - Hat Coin genug Daten für ATH Approach (10 Min)?
ath_approach_15_has_data             - Hat Coin genug Daten für ATH Approach (15 Min)?
ath_breakout_count_5_has_data         - Hat Coin genug Daten für ATH Breakout Count (5 Min)?
ath_breakout_count_10_has_data       - Hat Coin genug Daten für ATH Breakout Count (10 Min)?
ath_breakout_count_15_has_data       - Hat Coin genug Daten für ATH Breakout Count (15 Min)?
ath_breakout_volume_ma_5_has_data     - Hat Coin genug Daten für ATH Breakout Volume MA (5 Min)?
ath_breakout_volume_ma_10_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (10 Min)?
ath_breakout_volume_ma_15_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (15 Min)?
ath_age_trend_5_has_data             - Hat Coin genug Daten für ATH Age Trend (5 Min)?
ath_age_trend_10_has_data            - Hat Coin genug Daten für ATH Age Trend (10 Min)?
ath_age_trend_15_has_data            - Hat Coin genug Daten für ATH Age Trend (15 Min)?
```

### Volume Spike Flag-Features (3)
```
volume_spike_5_has_data      - Hat Coin genug Daten für Volume Spike (5 Min)?
volume_spike_10_has_data    - Hat Coin genug Daten für Volume Spike (10 Min)?
volume_spike_15_has_data    - Hat Coin genug Daten für Volume Spike (15 Min)?
```

### Zusammenfassung Flag-Features

| Kategorie | Anzahl | Window-Größen |
|-----------|--------|---------------|
| Dev-Sold | 3 | 5, 10, 15 Min |
| Buy Pressure | 6 | 5, 10, 15 Min (MA + Trend) |
| Whale Activity | 3 | 5, 10, 15 Min |
| Volatility | 6 | 5, 10, 15 Min (MA + Spike) |
| Wash Trading | 3 | 5, 10, 15 Min |
| Volume Pattern | 6 | 5, 10, 15 Min (Net Volume MA + Volume Flip) |
| Price Momentum | 6 | 5, 10, 15 Min (Change + ROC) |
| Price Acceleration | 3 | 5, 10, 15 Min |
| Market Cap Velocity | 3 | 5, 10, 15 Min |
| ATH Features | 15 | 5, 10, 15 Min (5 verschiedene ATH-Features) |
| Volume Spike | 3 | 5, 10, 15 Min |
| **GESAMT** | **57** | - |

---

## 🔧 Feature Engineering Optionen

Der `use_engineered_features` Parameter bietet **3 verschiedene Modi**:

### Option 1: Keine Engineering-Features (Default)

**Verhalten:** Nur die Basis-Features werden verwendet, die du in der `features` Liste angibst.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&
  use_engineered_features=false
  # oder einfach weglassen (Default ist false)
```

**Ergebnis:** 4 Features total (nur Basis-Features)

---

### Option 2: Spezifische Engineering-Features auswählen

**Verhalten:** Du gibst explizit Engineering-Features in der `features` Liste an. Das Backend erstellt nur diese.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume&
  use_engineered_features=true
```

**Ergebnis:** 5 Features total (2 Basis + 3 Engineering)

**Vorteil:** Du hast volle Kontrolle über welche Engineering-Features verwendet werden.

---

### Option 3: Alle Engineering-Features (66 Stück)

**Verhalten:** Wenn `use_engineered_features=true` ist, aber **keine** Engineering-Features in der `features` Liste stehen, werden automatisch **alle 66 Engineering-Features** erstellt.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true
```

**Ergebnis:** 68 Features total (2 Basis + 66 Engineering)

**Vorteil:** Maximale Feature-Abdeckung ohne manuelle Auswahl.

---

### Zusammenfassung

| Modus | `use_engineered_features` | Engineering-Features in `features` | Ergebnis |
|-------|---------------------------|-----------------------------------|----------|
| **Keine** | `false` oder weglassen | - | Nur Basis-Features |
| **Spezifische** | `true` | ✅ Ja (z.B. `dev_sold_spike_5`) | Nur die angegebenen Engineering-Features |
| **Alle** | `true` | ❌ Nein | Alle 66 Engineering-Features |

---

### 66 Engineering-Features (mit `use_engineered_features=true`)

#### Dev-Sold Features (6)
```
dev_sold_flag           - Hat der Dev verkauft? (0/1)
dev_sold_cumsum         - Kumulative Dev-Verkäufe
dev_sold_spike_5        - Dev-Verkauf-Spike (5 Min)
dev_sold_spike_10       - Dev-Verkauf-Spike (10 Min)
dev_sold_spike_15       - Dev-Verkauf-Spike (15 Min)
```

#### Buy Pressure Features (6)
```
buy_pressure_ma_5       - Moving Average (5 Min)
buy_pressure_trend_5    - Trend (5 Min)
buy_pressure_ma_10      - Moving Average (10 Min)
buy_pressure_trend_10   - Trend (10 Min)
buy_pressure_ma_15      - Moving Average (15 Min)
buy_pressure_trend_15   - Trend (15 Min)
```

#### Whale Activity Features (4)
```
whale_net_volume        - Netto Whale-Volume
whale_activity_5        - Whale-Aktivität (5 Min)
whale_activity_10       - Whale-Aktivität (10 Min)
whale_activity_15       - Whale-Aktivität (15 Min)
```

#### Volatility Features (6)
```
volatility_ma_5         - Volatilität MA (5 Min)
volatility_spike_5      - Volatilität-Spike (5 Min)
volatility_ma_10        - Volatilität MA (10 Min)
volatility_spike_10     - Volatilität-Spike (10 Min)
volatility_ma_15        - Volatilität MA (15 Min)
volatility_spike_15     - Volatilität-Spike (15 Min)
```

#### Wash Trading Detection (3)
```
wash_trading_flag_5     - Wash Trading erkannt? (5 Min)
wash_trading_flag_10    - Wash Trading erkannt? (10 Min)
wash_trading_flag_15    - Wash Trading erkannt? (15 Min)
```

#### Volume Pattern Features (6)
```
net_volume_ma_5         - Netto-Volume MA (5 Min)
volume_flip_5           - Volume Flip (5 Min)
net_volume_ma_10        - Netto-Volume MA (10 Min)
volume_flip_10          - Volume Flip (10 Min)
net_volume_ma_15        - Netto-Volume MA (15 Min)
volume_flip_15          - Volume Flip (15 Min)
```

#### Price Momentum Features (6)
```
price_change_5          - Preisänderung (5 Min)
price_roc_5             - Rate of Change (5 Min)
price_change_10         - Preisänderung (10 Min)
price_roc_10            - Rate of Change (10 Min)
price_change_15         - Preisänderung (15 Min)
price_roc_15            - Rate of Change (15 Min)
```

#### Market Cap Velocity (3)
```
mcap_velocity_5         - MarketCap Änderungsrate (5 Min)
mcap_velocity_10        - MarketCap Änderungsrate (10 Min)
mcap_velocity_15        - MarketCap Änderungsrate (15 Min)
```

#### ATH Features (19)
```
rolling_ath             - Rolling All-Time-High
price_vs_ath_pct        - Distanz zum ATH in %
ath_breakout            - ATH durchbrochen? (0/1)
minutes_since_ath       - Minuten seit letztem ATH
ath_distance_trend_5    - ATH-Distanz Trend (5 Min)
ath_approach_5          - Nähert sich ATH? (5 Min)
ath_breakout_count_5    - ATH-Durchbrüche (5 Min)
ath_breakout_volume_ma_5 - Volume bei ATH-Breaks (5 Min)
ath_age_trend_5         - ATH-Alter Trend (5 Min)
... (analog für 10 und 15 Minuten)
```

#### Power Features (8)
```
buy_sell_ratio          - Buy/Sell Verhältnis
whale_dominance         - Whale-Anteil am Volume
price_acceleration_5    - Preis-Beschleunigung (5 Min)
price_acceleration_10   - Preis-Beschleunigung (10 Min)
price_acceleration_15   - Preis-Beschleunigung (15 Min)
volume_spike_5          - Volume-Spike (5 Min)
volume_spike_10         - Volume-Spike (10 Min)
volume_spike_15         - Volume-Spike (15 Min)
```

---

## ⚖️ Balance-Optionen

### Das Problem: Unbalancierte Daten

Bei Pump-Detection sind positive Labels (Pumps) sehr selten (oft nur 1-5% der Daten). Das führt dazu, dass Modelle einfach "Nein" für alles vorhersagen.

### Lösung 1: `scale_pos_weight` (✅ EMPFOHLEN)

XGBoost-intern, gewichtet die positive Klasse höher.

| Positive Labels | scale_pos_weight | Effekt |
|-----------------|------------------|--------|
| 0.5% | `200` | Sehr aggressiv |
| 1% | `100` | Standard |
| 2% | `50` | Moderat |
| 5% | `20` | Konservativ |

**Beispiel:**
```bash
scale_pos_weight=100
```

**Vorteile:**
- Keine synthetischen Daten
- Schneller als SMOTE
- Besser generalisierbar

### Lösung 2: `use_smote` (⚠️ Mit Vorsicht)

Synthetisches Oversampling - erstellt künstliche positive Samples.

**Beispiel:**
```bash
use_smote=true
```

**Nachteile:**
- Kann zu Overfitting führen
- Modell lernt synthetische statt echte Muster

### Lösung 3: `class_weight` (für Random Forest)

```bash
class_weight=balanced
```

---

## 📝 Beispiele

### Beispiel 1: Einfaches Pump-Modell

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio&\
future_minutes=5&\
min_percent_change=2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 2: Mit ALLEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 2c: Mit ALLEN Engineering-Features OHNE Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_No_Flags_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=false&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 70 Features (4 Basis + 66 Engineering, keine Flag-Features)

### Beispiel 2b: Mit SPEZIFISCHEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Selective_Engineering_v1&\
model_type=xgboost&\
features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume,volatility_spike_15&\
use_engineered_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 8 Features (2 Basis + 4 Engineering + **4 Flag-Features** - nur die für die ausgewählten Engineering-Features!)

**Wichtig:** Das System verwendet automatisch nur die Flag-Features, die zu den ausgewählten Engineering-Features gehören:
- `dev_sold_spike_5_has_data` (für `dev_sold_spike_5`)
- `buy_pressure_ma_10_has_data` (für `buy_pressure_ma_10`)
- `volatility_spike_15_has_data` (für `volatility_spike_15`)
- `whale_net_volume` hat kein Flag-Feature (ist kein window-basiertes Feature)

### Beispiel 3: OHNE Engineering-Features (nur Basis)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol&\
use_engineered_features=false&\
scale_pos_weight=100&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 5 Features (nur Basis-Features, keine Engineering)

### Beispiel 4: Mit scale_pos_weight (EMPFOHLEN)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Balanced_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 5: ULTIMATIV (Alle Features + Engineering + Flag-Features + Balance)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Ultimate_Pump_Detector&\
model_type=xgboost&\
features=price_open,price_high,price_low,price_close,volume_sol,buy_volume_sol,sell_volume_sol,net_volume_sol,market_cap_close,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct,unique_signer_ratio&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=15&\
direction=up&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 137 Features (14 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 5: Rug-Pull Detection

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Rug_Pull_Detector&\
model_type=xgboost&\
features=price_close,dev_sold_amount,buy_pressure_ratio,whale_sell_volume_sol&\
direction=down&\
min_percent_change=20&\
future_minutes=15&\
scale_pos_weight=50&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 6: Random Forest

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=RF_Pump_Detector&\
model_type=random_forest&\
features=price_close,volume_sol,buy_pressure_ratio&\
class_weight=balanced&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 7: Second Wave Detection (mit Flag-Features)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Second_Wave_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
future_minutes=15&\
min_percent_change=10&\
phases=1,2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 129 Features (6 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 8: Nur Baby Zone (Phase 1)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Baby_Zone_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
phases=1&\
scale_pos_weight=150&\
future_minutes=5&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 9: Survival + Mature Zone (Phase 2+3) mit Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Mature_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
phases=2,3&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=80&\
future_minutes=15&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

---

## 💡 Best Practices

### 1. Feature-Auswahl

| Empfehlung | Beschreibung |
|------------|--------------|
| ✅ Start mit Basis-Features | Beginne mit 5-10 wichtigen Features |
| ✅ Wichtigste Features zuerst | `price_close`, `volume_sol`, `buy_pressure_ratio` |
| ✅ Flag-Features aktivieren | Verbessert Modell-Performance bei neuen Coins |
| ⚠️ Nicht zu viele Features | Mehr als 30 Basis-Features kann zu Overfitting führen |
| ⚠️ Mit Engineering + Flags | Bis zu 150 Features möglich (27 Base + 66 Eng + 57 Flags bei zeitbasierter Vorhersage) oder 151 Features (28 Base + 66 Eng + 57 Flags ohne zeitbasierte Vorhersage) |
| ❌ Keine redundanten Features | z.B. nicht `price_open` UND `price_close` UND `price_high` UND `price_low` |

### 2. Zeithorizont-Wahl

| Zeithorizont | Empfohlene Schwelle | Use Case |
|--------------|---------------------|----------|
| 2-5 Min | 1-3% | Schnelle Scalping-Signale |
| 5-10 Min | 3-10% | Standard Pump Detection |
| 10-15 Min | 5-15% | Second Wave Detection |
| 15-30 Min | 10-25% | Langfristige Trends |

### 3. Balance-Strategie

| Situation | Empfehlung |
|-----------|------------|
| 1% positive Labels | `scale_pos_weight=100` |
| Sehr seltene Events | `scale_pos_weight=200` |
| Mehr Pumps erkennen | Höherer `scale_pos_weight` (mehr Fehlalarme) |
| Weniger Fehlalarme | Niedrigerer `scale_pos_weight` (weniger erkannte Pumps) |

### 4. Trainings-Zeitraum

| Zeitraum | Empfehlung |
|----------|------------|
| **Minimum** | 2 Stunden |
| **Optimal** | 8-12 Stunden |
| **Maximum** | 24+ Stunden (längere Wartezeit) |

---

## 🔧 Troubleshooting

### Problem: F1-Score = 0

**Ursache:** Zu wenig positive Labels oder keine Balance-Strategie.

**Lösung:**
1. Aktiviere `scale_pos_weight=100`
2. ODER senke `min_percent_change`
3. ODER erhöhe `future_minutes`

### Problem: Zu viele Fehlalarme

**Ursache:** `scale_pos_weight` zu hoch.

**Lösung:**
1. Senke `scale_pos_weight` (z.B. von 200 auf 100)
2. ODER erhöhe `min_percent_change`

### Problem: Keine Pumps erkannt

**Ursache:** `scale_pos_weight` zu niedrig oder Feature-Auswahl schlecht.

**Lösung:**
1. Erhöhe `scale_pos_weight` (z.B. auf 200)
2. Füge relevante Features hinzu: `buy_pressure_ratio`, `whale_buy_volume_sol`

### Problem: Training dauert zu lange

**Ursache:** Zu viele Features oder zu großer Zeitraum.

**Lösung:**
1. Reduziere Features auf 10-15
2. Reduziere Trainings-Zeitraum
3. Deaktiviere `use_engineered_features`

### Problem: "Keine Trainingsdaten gefunden"

**Ursache:** Der angegebene Zeitraum enthält keine Daten.

**Lösung:**
1. Prüfe ob der Zeitraum korrekt ist (UTC!)
2. Verwende einen Zeitraum mit bekannten Daten

---

## 📊 Response-Format

### Erfolgreiche Erstellung

```json
{
  "job_id": 424,
  "message": "Job erstellt. Modell 'MyModel' wird trainiert.",
  "status": "PENDING"
}
```

### Job-Status prüfen

```bash
GET /api/queue/{job_id}
```

```json
{
  "id": 424,
  "status": "COMPLETED",
  "result_model_id": 130,
  "progress": 100,
  "progress_msg": "Training abgeschlossen"
}
```

### Modell-Details abrufen

```bash
GET /api/models/{model_id}
```

---

## 🌐 Web UI

Die Web UI bietet dieselben Funktionen mit grafischer Oberfläche:

**URL:** https://test.local.chase295.de/training

Im Schritt 5 "Erweiterte Einstellungen" findest du:
- ⚖️ Klassen-Gewichtung (scale_pos_weight)
- Cross-Validation Einstellungen
- SMOTE Option
- Trainings-Zeitraum

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe die Job-Logs: `GET /api/queue/{job_id}`
2. Prüfe die Modell-Details: `GET /api/models/{model_id}`
3. Sieh dir die Confusion Matrix an für Einblicke in die Performance

---

**Dokumentation erstellt:** Januar 2026  
**Getestet:** 10/10 Tests bestanden ✅


## Vollständige Anleitung zur Modell-Erstellung

**Version:** 1.0  
**Stand:** Januar 2026  
**Endpoint:** `POST /api/models/create/advanced`

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Alle Parameter](#alle-parameter)
3. [Feature-Liste](#feature-liste)
4. [Balance-Optionen](#balance-optionen)
5. [Beispiele](#beispiele)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Der `/models/create/advanced` Endpoint ist der **vollständigste und flexibelste** Endpoint zur Erstellung von ML-Modellen für Pump-Detection.

### Was kann dieser Endpoint?

| Funktion | Beschreibung |
|----------|--------------|
| ✅ **Zeitbasierte Vorhersage** | "Steigt der Preis um X% in Y Minuten?" |
| ✅ **Feature Engineering** | 66 zusätzliche berechnete Features |
| ✅ **SMOTE** | Synthetisches Oversampling für unbalancierte Daten |
| ✅ **scale_pos_weight** | XGBoost-interne Klassen-Gewichtung |
| ✅ **Flexible Zeithorizonte** | 1 Minute bis 60+ Minuten |
| ✅ **Pump & Rug Detection** | Steigende oder fallende Preise vorhersagen |
| ✅ **Zwei Modell-Typen** | XGBoost und Random Forest |

---

## 📊 Alle Parameter

### Pflicht-Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `name` | string | Eindeutiger Modell-Name | `"Pump_Detector_v1"` |
| `model_type` | string | `xgboost` oder `random_forest` | `"xgboost"` |
| `features` | string | Komma-separierte Feature-Liste | `"price_close,volume_sol"` |
| `train_start` | string | Trainings-Startzeit (UTC, ISO-Format) | `"2026-01-07T06:00:00Z"` |
| `train_end` | string | Trainings-Endzeit (UTC, ISO-Format) | `"2026-01-07T18:00:00Z"` |

### Optionale Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `target_var` | string | `"price_close"` | Ziel-Variable für Vorhersage |
| `use_time_based_prediction` | bool | `true` | Zeitbasierte Vorhersage aktivieren |
| `future_minutes` | int | `5` | Vorhersage-Horizont in Minuten |
| `min_percent_change` | float | `2.0` | Minimale Preisänderung in % |
| `direction` | string | `"up"` | `"up"` für Pump, `"down"` für Rug |
| `use_engineered_features` | bool | `false` | Feature Engineering aktivieren (siehe [Feature Engineering Optionen](#feature-engineering-optionen)) |
| `use_flag_features` | bool | `true` | **NEU!** Flag-Features aktivieren (siehe [Flag-Features](#flag-features)) |
| `use_smote` | bool | `false` | SMOTE aktivieren |
| `scale_pos_weight` | float | `null` | XGBoost Klassen-Gewichtung |
| `class_weight` | string | `null` | `"balanced"` für Random Forest |
| `phases` | string | `null` | **NEU!** Coin-Phasen Filter (z.B. `"1,2,3"`) |

---

## 🔄 Coin-Phasen Filter (NEU!)

Mit dem `phases` Parameter kannst du das Training auf **bestimmte Coin-Entwicklungsphasen** beschränken.

### Verfügbare Phasen

| Phase ID | Name | Beschreibung | Alter |
|----------|------|--------------|-------|
| **1** | Baby Zone | Frisch erstellte Coins | 0-10 Min |
| **2** | Survival Zone | Überlebende Coins | 10-120 Min |
| **3** | Mature Zone | Reife Coins | 2-4 Stunden |
| **99** | Finished | Abgeschlossene Coins | - |
| **100** | Graduated | Graduierte Coins | - |

### Beispiele

```bash
# Nur Baby & Survival Zone (Phase 1 + 2)
phases=1,2

# Nur Mature Zone (Phase 3)
phases=3

# Alle aktiven Phasen (1, 2, 3)
phases=1,2,3
```

### Warum Phasen filtern?

| Use Case | Empfohlene Phasen | Grund |
|----------|-------------------|-------|
| **Second Wave Detection** | `1,2` | Pumps passieren früh |
| **Langfristige Trends** | `2,3` | Stabile Datenmuster |
| **Rug-Pull Detection** | `1` | Rugs passieren in Phase 1 |
| **Allgemein** | `1,2,3` | Maximale Datenmenge |

---

## 📊 Feature-Liste

### 28 Basis-Features (immer verfügbar)

⚠️ **WICHTIG:** Bei zeitbasierter Vorhersage wird `price_close` automatisch aus den Trainings-Features entfernt (verhindert Data Leakage). In diesem Fall sind es **27 Basis-Features** im Training.

#### Preis-Features (4)
```
price_open      - Eröffnungspreis der Minute
price_high      - Höchster Preis der Minute
price_low       - Niedrigster Preis der Minute
price_close     - Schlusskurs der Minute
```

#### Volume-Features (4)
```
volume_sol          - Gesamtes Handelsvolumen in SOL
buy_volume_sol      - Kaufvolumen in SOL
sell_volume_sol     - Verkaufsvolumen in SOL
net_volume_sol      - Netto-Volumen (Buy - Sell)
```

#### Market-Features (4)
```
market_cap_close        - Marktkapitalisierung
bonding_curve_pct       - Position auf der Bonding Curve (%)
virtual_sol_reserves    - Virtuelle SOL-Reserven
is_koth                 - King of the Hill Status (0/1)
```

#### Trade-Statistiken (4)
```
num_buys            - Anzahl Buy-Trades
num_sells           - Anzahl Sell-Trades
unique_wallets      - Einzigartige Wallet-Adressen
num_micro_trades    - Anzahl Mikro-Trades
```

#### Max Trade Sizes (2)
```
max_single_buy_sol      - Größter einzelner Kauf
max_single_sell_sol     - Größter einzelner Verkauf
```

#### Whale-Features (4)
```
whale_buy_volume_sol    - Whale-Kaufvolumen
whale_sell_volume_sol   - Whale-Verkaufsvolumen
num_whale_buys          - Anzahl Whale-Käufe
num_whale_sells         - Anzahl Whale-Verkäufe
```

#### Qualitäts-Features (4)
```
dev_sold_amount     - Vom Developer verkaufte Menge
volatility_pct      - Preisvolatilität in %
avg_trade_size_sol  - Durchschnittliche Trade-Größe
buy_pressure_ratio  - Kaufdruck-Verhältnis (0-1)
```

#### Wallet-Analyse (2)
```
unique_signer_ratio     - Verhältnis einzigartiger Signaturen
phase_id_at_time        - Coin-Phase (1-6)
```

---

## 🚩 Flag-Features (NEU!)

Flag-Features sind **Datenverfügbarkeits-Indikatoren**, die dem Modell anzeigen, ob ein Engineering-Feature genug historische Daten hat, um zuverlässig berechnet zu werden.

### Was sind Flag-Features?

Jedes window-basierte Engineering-Feature (z.B. `buy_pressure_ma_5`) erhält ein entsprechendes Flag-Feature (z.B. `buy_pressure_ma_5_has_data`), das anzeigt:
- **`1`** = Genug Daten vorhanden (Feature ist zuverlässig)
- **`0`** = Nicht genug Daten (Feature könnte unzuverlässig sein)

### Warum Flag-Features?

| Problem | Lösung mit Flag-Features |
|---------|-------------------------|
| Neue Coins haben keine 15-Minuten-Historie | Modell lernt, dass `buy_pressure_ma_15_has_data=0` bedeutet: Feature ignorieren |
| NaN-Werte in Engineering-Features | Flag zeigt dem Modell, ob NaN = "keine Daten" oder "echter Wert" |
| Unzuverlässige Features bei jungen Coins | Modell kann Features basierend auf Datenverfügbarkeit gewichten |

### Aktivierung

Flag-Features werden automatisch aktiviert, wenn:
1. `use_engineered_features=true` **UND**
2. `use_flag_features=true` (Default: `true`)

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true&
  use_flag_features=true
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering + **57 Flag-Features = 150 Features total**

### Deaktivierung

Wenn du Flag-Features nicht möchtest:
```bash
use_flag_features=false
```

**Ergebnis:** 27 Base (ohne price_close bei zeitbasierter Vorhersage) + 66 Engineering = 93 Features total (ohne Flags)

---

## 🚩 Alle 57 Flag-Features

### Dev-Sold Flag-Features (3)
```
dev_sold_spike_5_has_data      - Hat Coin genug Daten für Dev-Sold Spike (5 Min)?
dev_sold_spike_10_has_data     - Hat Coin genug Daten für Dev-Sold Spike (10 Min)?
dev_sold_spike_15_has_data     - Hat Coin genug Daten für Dev-Sold Spike (15 Min)?
```

### Buy Pressure Flag-Features (6)
```
buy_pressure_ma_5_has_data     - Hat Coin genug Daten für Buy Pressure MA (5 Min)?
buy_pressure_ma_10_has_data   - Hat Coin genug Daten für Buy Pressure MA (10 Min)?
buy_pressure_ma_15_has_data   - Hat Coin genug Daten für Buy Pressure MA (15 Min)?
buy_pressure_trend_5_has_data  - Hat Coin genug Daten für Buy Pressure Trend (5 Min)?
buy_pressure_trend_10_has_data - Hat Coin genug Daten für Buy Pressure Trend (10 Min)?
buy_pressure_trend_15_has_data - Hat Coin genug Daten für Buy Pressure Trend (15 Min)?
```

### Whale Activity Flag-Features (3)
```
whale_activity_5_has_data      - Hat Coin genug Daten für Whale Activity (5 Min)?
whale_activity_10_has_data    - Hat Coin genug Daten für Whale Activity (10 Min)?
whale_activity_15_has_data    - Hat Coin genug Daten für Whale Activity (15 Min)?
```

### Volatility Flag-Features (6)
```
volatility_ma_5_has_data      - Hat Coin genug Daten für Volatility MA (5 Min)?
volatility_ma_10_has_data    - Hat Coin genug Daten für Volatility MA (10 Min)?
volatility_ma_15_has_data    - Hat Coin genug Daten für Volatility MA (15 Min)?
volatility_spike_5_has_data   - Hat Coin genug Daten für Volatility Spike (5 Min)?
volatility_spike_10_has_data - Hat Coin genug Daten für Volatility Spike (10 Min)?
volatility_spike_15_has_data - Hat Coin genug Daten für Volatility Spike (15 Min)?
```

### Wash Trading Flag-Features (3)
```
wash_trading_flag_5_has_data  - Hat Coin genug Daten für Wash Trading Detection (5 Min)?
wash_trading_flag_10_has_data - Hat Coin genug Daten für Wash Trading Detection (10 Min)?
wash_trading_flag_15_has_data - Hat Coin genug Daten für Wash Trading Detection (15 Min)?
```

### Volume Pattern Flag-Features (6)
```
net_volume_ma_5_has_data      - Hat Coin genug Daten für Net Volume MA (5 Min)?
net_volume_ma_10_has_data    - Hat Coin genug Daten für Net Volume MA (10 Min)?
net_volume_ma_15_has_data    - Hat Coin genug Daten für Net Volume MA (15 Min)?
volume_flip_5_has_data       - Hat Coin genug Daten für Volume Flip (5 Min)?
volume_flip_10_has_data      - Hat Coin genug Daten für Volume Flip (10 Min)?
volume_flip_15_has_data      - Hat Coin genug Daten für Volume Flip (15 Min)?
```

### Price Momentum Flag-Features (6)
```
price_change_5_has_data      - Hat Coin genug Daten für Price Change (5 Min)?
price_change_10_has_data    - Hat Coin genug Daten für Price Change (10 Min)?
price_change_15_has_data    - Hat Coin genug Daten für Price Change (15 Min)?
price_roc_5_has_data         - Hat Coin genug Daten für Price ROC (5 Min)?
price_roc_10_has_data        - Hat Coin genug Daten für Price ROC (10 Min)?
price_roc_15_has_data        - Hat Coin genug Daten für Price ROC (15 Min)?
```

### Price Acceleration Flag-Features (3)
```
price_acceleration_5_has_data  - Hat Coin genug Daten für Price Acceleration (5 Min)?
price_acceleration_10_has_data - Hat Coin genug Daten für Price Acceleration (10 Min)?
price_acceleration_15_has_data - Hat Coin genug Daten für Price Acceleration (15 Min)?
```

### Market Cap Velocity Flag-Features (3)
```
mcap_velocity_5_has_data      - Hat Coin genug Daten für Market Cap Velocity (5 Min)?
mcap_velocity_10_has_data    - Hat Coin genug Daten für Market Cap Velocity (10 Min)?
mcap_velocity_15_has_data    - Hat Coin genug Daten für Market Cap Velocity (15 Min)?
```

### ATH Flag-Features (15)
```
ath_distance_trend_5_has_data         - Hat Coin genug Daten für ATH Distance Trend (5 Min)?
ath_distance_trend_10_has_data        - Hat Coin genug Daten für ATH Distance Trend (10 Min)?
ath_distance_trend_15_has_data       - Hat Coin genug Daten für ATH Distance Trend (15 Min)?
ath_approach_5_has_data              - Hat Coin genug Daten für ATH Approach (5 Min)?
ath_approach_10_has_data             - Hat Coin genug Daten für ATH Approach (10 Min)?
ath_approach_15_has_data             - Hat Coin genug Daten für ATH Approach (15 Min)?
ath_breakout_count_5_has_data         - Hat Coin genug Daten für ATH Breakout Count (5 Min)?
ath_breakout_count_10_has_data       - Hat Coin genug Daten für ATH Breakout Count (10 Min)?
ath_breakout_count_15_has_data       - Hat Coin genug Daten für ATH Breakout Count (15 Min)?
ath_breakout_volume_ma_5_has_data     - Hat Coin genug Daten für ATH Breakout Volume MA (5 Min)?
ath_breakout_volume_ma_10_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (10 Min)?
ath_breakout_volume_ma_15_has_data    - Hat Coin genug Daten für ATH Breakout Volume MA (15 Min)?
ath_age_trend_5_has_data             - Hat Coin genug Daten für ATH Age Trend (5 Min)?
ath_age_trend_10_has_data            - Hat Coin genug Daten für ATH Age Trend (10 Min)?
ath_age_trend_15_has_data            - Hat Coin genug Daten für ATH Age Trend (15 Min)?
```

### Volume Spike Flag-Features (3)
```
volume_spike_5_has_data      - Hat Coin genug Daten für Volume Spike (5 Min)?
volume_spike_10_has_data    - Hat Coin genug Daten für Volume Spike (10 Min)?
volume_spike_15_has_data    - Hat Coin genug Daten für Volume Spike (15 Min)?
```

### Zusammenfassung Flag-Features

| Kategorie | Anzahl | Window-Größen |
|-----------|--------|---------------|
| Dev-Sold | 3 | 5, 10, 15 Min |
| Buy Pressure | 6 | 5, 10, 15 Min (MA + Trend) |
| Whale Activity | 3 | 5, 10, 15 Min |
| Volatility | 6 | 5, 10, 15 Min (MA + Spike) |
| Wash Trading | 3 | 5, 10, 15 Min |
| Volume Pattern | 6 | 5, 10, 15 Min (Net Volume MA + Volume Flip) |
| Price Momentum | 6 | 5, 10, 15 Min (Change + ROC) |
| Price Acceleration | 3 | 5, 10, 15 Min |
| Market Cap Velocity | 3 | 5, 10, 15 Min |
| ATH Features | 15 | 5, 10, 15 Min (5 verschiedene ATH-Features) |
| Volume Spike | 3 | 5, 10, 15 Min |
| **GESAMT** | **57** | - |

---

## 🔧 Feature Engineering Optionen

Der `use_engineered_features` Parameter bietet **3 verschiedene Modi**:

### Option 1: Keine Engineering-Features (Default)

**Verhalten:** Nur die Basis-Features werden verwendet, die du in der `features` Liste angibst.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&
  use_engineered_features=false
  # oder einfach weglassen (Default ist false)
```

**Ergebnis:** 4 Features total (nur Basis-Features)

---

### Option 2: Spezifische Engineering-Features auswählen

**Verhalten:** Du gibst explizit Engineering-Features in der `features` Liste an. Das Backend erstellt nur diese.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume&
  use_engineered_features=true
```

**Ergebnis:** 5 Features total (2 Basis + 3 Engineering)

**Vorteil:** Du hast volle Kontrolle über welche Engineering-Features verwendet werden.

---

### Option 3: Alle Engineering-Features (66 Stück)

**Verhalten:** Wenn `use_engineered_features=true` ist, aber **keine** Engineering-Features in der `features` Liste stehen, werden automatisch **alle 66 Engineering-Features** erstellt.

**Beispiel:**
```bash
POST /api/models/create/advanced?
  features=price_close,volume_sol&
  use_engineered_features=true
```

**Ergebnis:** 68 Features total (2 Basis + 66 Engineering)

**Vorteil:** Maximale Feature-Abdeckung ohne manuelle Auswahl.

---

### Zusammenfassung

| Modus | `use_engineered_features` | Engineering-Features in `features` | Ergebnis |
|-------|---------------------------|-----------------------------------|----------|
| **Keine** | `false` oder weglassen | - | Nur Basis-Features |
| **Spezifische** | `true` | ✅ Ja (z.B. `dev_sold_spike_5`) | Nur die angegebenen Engineering-Features |
| **Alle** | `true` | ❌ Nein | Alle 66 Engineering-Features |

---

### 66 Engineering-Features (mit `use_engineered_features=true`)

#### Dev-Sold Features (6)
```
dev_sold_flag           - Hat der Dev verkauft? (0/1)
dev_sold_cumsum         - Kumulative Dev-Verkäufe
dev_sold_spike_5        - Dev-Verkauf-Spike (5 Min)
dev_sold_spike_10       - Dev-Verkauf-Spike (10 Min)
dev_sold_spike_15       - Dev-Verkauf-Spike (15 Min)
```

#### Buy Pressure Features (6)
```
buy_pressure_ma_5       - Moving Average (5 Min)
buy_pressure_trend_5    - Trend (5 Min)
buy_pressure_ma_10      - Moving Average (10 Min)
buy_pressure_trend_10   - Trend (10 Min)
buy_pressure_ma_15      - Moving Average (15 Min)
buy_pressure_trend_15   - Trend (15 Min)
```

#### Whale Activity Features (4)
```
whale_net_volume        - Netto Whale-Volume
whale_activity_5        - Whale-Aktivität (5 Min)
whale_activity_10       - Whale-Aktivität (10 Min)
whale_activity_15       - Whale-Aktivität (15 Min)
```

#### Volatility Features (6)
```
volatility_ma_5         - Volatilität MA (5 Min)
volatility_spike_5      - Volatilität-Spike (5 Min)
volatility_ma_10        - Volatilität MA (10 Min)
volatility_spike_10     - Volatilität-Spike (10 Min)
volatility_ma_15        - Volatilität MA (15 Min)
volatility_spike_15     - Volatilität-Spike (15 Min)
```

#### Wash Trading Detection (3)
```
wash_trading_flag_5     - Wash Trading erkannt? (5 Min)
wash_trading_flag_10    - Wash Trading erkannt? (10 Min)
wash_trading_flag_15    - Wash Trading erkannt? (15 Min)
```

#### Volume Pattern Features (6)
```
net_volume_ma_5         - Netto-Volume MA (5 Min)
volume_flip_5           - Volume Flip (5 Min)
net_volume_ma_10        - Netto-Volume MA (10 Min)
volume_flip_10          - Volume Flip (10 Min)
net_volume_ma_15        - Netto-Volume MA (15 Min)
volume_flip_15          - Volume Flip (15 Min)
```

#### Price Momentum Features (6)
```
price_change_5          - Preisänderung (5 Min)
price_roc_5             - Rate of Change (5 Min)
price_change_10         - Preisänderung (10 Min)
price_roc_10            - Rate of Change (10 Min)
price_change_15         - Preisänderung (15 Min)
price_roc_15            - Rate of Change (15 Min)
```

#### Market Cap Velocity (3)
```
mcap_velocity_5         - MarketCap Änderungsrate (5 Min)
mcap_velocity_10        - MarketCap Änderungsrate (10 Min)
mcap_velocity_15        - MarketCap Änderungsrate (15 Min)
```

#### ATH Features (19)
```
rolling_ath             - Rolling All-Time-High
price_vs_ath_pct        - Distanz zum ATH in %
ath_breakout            - ATH durchbrochen? (0/1)
minutes_since_ath       - Minuten seit letztem ATH
ath_distance_trend_5    - ATH-Distanz Trend (5 Min)
ath_approach_5          - Nähert sich ATH? (5 Min)
ath_breakout_count_5    - ATH-Durchbrüche (5 Min)
ath_breakout_volume_ma_5 - Volume bei ATH-Breaks (5 Min)
ath_age_trend_5         - ATH-Alter Trend (5 Min)
... (analog für 10 und 15 Minuten)
```

#### Power Features (8)
```
buy_sell_ratio          - Buy/Sell Verhältnis
whale_dominance         - Whale-Anteil am Volume
price_acceleration_5    - Preis-Beschleunigung (5 Min)
price_acceleration_10   - Preis-Beschleunigung (10 Min)
price_acceleration_15   - Preis-Beschleunigung (15 Min)
volume_spike_5          - Volume-Spike (5 Min)
volume_spike_10         - Volume-Spike (10 Min)
volume_spike_15         - Volume-Spike (15 Min)
```

---

## ⚖️ Balance-Optionen

### Das Problem: Unbalancierte Daten

Bei Pump-Detection sind positive Labels (Pumps) sehr selten (oft nur 1-5% der Daten). Das führt dazu, dass Modelle einfach "Nein" für alles vorhersagen.

### Lösung 1: `scale_pos_weight` (✅ EMPFOHLEN)

XGBoost-intern, gewichtet die positive Klasse höher.

| Positive Labels | scale_pos_weight | Effekt |
|-----------------|------------------|--------|
| 0.5% | `200` | Sehr aggressiv |
| 1% | `100` | Standard |
| 2% | `50` | Moderat |
| 5% | `20` | Konservativ |

**Beispiel:**
```bash
scale_pos_weight=100
```

**Vorteile:**
- Keine synthetischen Daten
- Schneller als SMOTE
- Besser generalisierbar

### Lösung 2: `use_smote` (⚠️ Mit Vorsicht)

Synthetisches Oversampling - erstellt künstliche positive Samples.

**Beispiel:**
```bash
use_smote=true
```

**Nachteile:**
- Kann zu Overfitting führen
- Modell lernt synthetische statt echte Muster

### Lösung 3: `class_weight` (für Random Forest)

```bash
class_weight=balanced
```

---

## 📝 Beispiele

### Beispiel 1: Einfaches Pump-Modell

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio&\
future_minutes=5&\
min_percent_change=2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 2: Mit ALLEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 2c: Mit ALLEN Engineering-Features OHNE Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Engineering_No_Flags_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=false&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 70 Features (4 Basis + 66 Engineering, keine Flag-Features)

### Beispiel 2b: Mit SPEZIFISCHEN Engineering-Features + Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Selective_Engineering_v1&\
model_type=xgboost&\
features=price_close,volume_sol,dev_sold_spike_5,buy_pressure_ma_10,whale_net_volume,volatility_spike_15&\
use_engineered_features=true&\
use_flag_features=true&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 8 Features (2 Basis + 4 Engineering + **4 Flag-Features** - nur die für die ausgewählten Engineering-Features!)

**Wichtig:** Das System verwendet automatisch nur die Flag-Features, die zu den ausgewählten Engineering-Features gehören:
- `dev_sold_spike_5_has_data` (für `dev_sold_spike_5`)
- `buy_pressure_ma_10_has_data` (für `buy_pressure_ma_10`)
- `volatility_spike_15_has_data` (für `volatility_spike_15`)
- `whale_net_volume` hat kein Flag-Feature (ist kein window-basiertes Feature)

### Beispiel 3: OHNE Engineering-Features (nur Basis)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Simple_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol&\
use_engineered_features=false&\
scale_pos_weight=100&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 5 Features (nur Basis-Features, keine Engineering)

### Beispiel 4: Mit scale_pos_weight (EMPFOHLEN)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Balanced_Pump_v1&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 5: ULTIMATIV (Alle Features + Engineering + Flag-Features + Balance)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Ultimate_Pump_Detector&\
model_type=xgboost&\
features=price_open,price_high,price_low,price_close,volume_sol,buy_volume_sol,sell_volume_sol,net_volume_sol,market_cap_close,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct,unique_signer_ratio&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
use_smote=false&\
future_minutes=10&\
min_percent_change=15&\
direction=up&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 137 Features (14 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 5: Rug-Pull Detection

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Rug_Pull_Detector&\
model_type=xgboost&\
features=price_close,dev_sold_amount,buy_pressure_ratio,whale_sell_volume_sol&\
direction=down&\
min_percent_change=20&\
future_minutes=15&\
scale_pos_weight=50&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 6: Random Forest

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=RF_Pump_Detector&\
model_type=random_forest&\
features=price_close,volume_sol,buy_pressure_ratio&\
class_weight=balanced&\
future_minutes=10&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 7: Second Wave Detection (mit Flag-Features)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Second_Wave_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount,whale_buy_volume_sol,volatility_pct&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=100&\
future_minutes=15&\
min_percent_change=10&\
phases=1,2&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 129 Features (6 Basis + 66 Engineering + 57 Flag-Features)

### Beispiel 8: Nur Baby Zone (Phase 1)

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Baby_Zone_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,dev_sold_amount&\
phases=1&\
scale_pos_weight=150&\
future_minutes=5&\
min_percent_change=5&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```

### Beispiel 9: Survival + Mature Zone (Phase 2+3) mit Flag-Features

```bash
curl -X POST "https://test.local.chase295.de/api/models/create/advanced?\
name=Mature_Pump_Detector&\
model_type=xgboost&\
features=price_close,volume_sol,buy_pressure_ratio,whale_buy_volume_sol&\
phases=2,3&\
use_engineered_features=true&\
use_flag_features=true&\
use_flag_features=true&\
scale_pos_weight=80&\
future_minutes=15&\
min_percent_change=10&\
train_start=2026-01-07T06:00:00Z&\
train_end=2026-01-07T18:00:00Z"
```
**Ergebnis:** 127 Features (4 Basis + 66 Engineering + 57 Flag-Features)

---

## 💡 Best Practices

### 1. Feature-Auswahl

| Empfehlung | Beschreibung |
|------------|--------------|
| ✅ Start mit Basis-Features | Beginne mit 5-10 wichtigen Features |
| ✅ Wichtigste Features zuerst | `price_close`, `volume_sol`, `buy_pressure_ratio` |
| ✅ Flag-Features aktivieren | Verbessert Modell-Performance bei neuen Coins |
| ⚠️ Nicht zu viele Features | Mehr als 30 Basis-Features kann zu Overfitting führen |
| ⚠️ Mit Engineering + Flags | Bis zu 150 Features möglich (27 Base + 66 Eng + 57 Flags bei zeitbasierter Vorhersage) oder 151 Features (28 Base + 66 Eng + 57 Flags ohne zeitbasierte Vorhersage) |
| ❌ Keine redundanten Features | z.B. nicht `price_open` UND `price_close` UND `price_high` UND `price_low` |

### 2. Zeithorizont-Wahl

| Zeithorizont | Empfohlene Schwelle | Use Case |
|--------------|---------------------|----------|
| 2-5 Min | 1-3% | Schnelle Scalping-Signale |
| 5-10 Min | 3-10% | Standard Pump Detection |
| 10-15 Min | 5-15% | Second Wave Detection |
| 15-30 Min | 10-25% | Langfristige Trends |

### 3. Balance-Strategie

| Situation | Empfehlung |
|-----------|------------|
| 1% positive Labels | `scale_pos_weight=100` |
| Sehr seltene Events | `scale_pos_weight=200` |
| Mehr Pumps erkennen | Höherer `scale_pos_weight` (mehr Fehlalarme) |
| Weniger Fehlalarme | Niedrigerer `scale_pos_weight` (weniger erkannte Pumps) |

### 4. Trainings-Zeitraum

| Zeitraum | Empfehlung |
|----------|------------|
| **Minimum** | 2 Stunden |
| **Optimal** | 8-12 Stunden |
| **Maximum** | 24+ Stunden (längere Wartezeit) |

---

## 🔧 Troubleshooting

### Problem: F1-Score = 0

**Ursache:** Zu wenig positive Labels oder keine Balance-Strategie.

**Lösung:**
1. Aktiviere `scale_pos_weight=100`
2. ODER senke `min_percent_change`
3. ODER erhöhe `future_minutes`

### Problem: Zu viele Fehlalarme

**Ursache:** `scale_pos_weight` zu hoch.

**Lösung:**
1. Senke `scale_pos_weight` (z.B. von 200 auf 100)
2. ODER erhöhe `min_percent_change`

### Problem: Keine Pumps erkannt

**Ursache:** `scale_pos_weight` zu niedrig oder Feature-Auswahl schlecht.

**Lösung:**
1. Erhöhe `scale_pos_weight` (z.B. auf 200)
2. Füge relevante Features hinzu: `buy_pressure_ratio`, `whale_buy_volume_sol`

### Problem: Training dauert zu lange

**Ursache:** Zu viele Features oder zu großer Zeitraum.

**Lösung:**
1. Reduziere Features auf 10-15
2. Reduziere Trainings-Zeitraum
3. Deaktiviere `use_engineered_features`

### Problem: "Keine Trainingsdaten gefunden"

**Ursache:** Der angegebene Zeitraum enthält keine Daten.

**Lösung:**
1. Prüfe ob der Zeitraum korrekt ist (UTC!)
2. Verwende einen Zeitraum mit bekannten Daten

---

## 📊 Response-Format

### Erfolgreiche Erstellung

```json
{
  "job_id": 424,
  "message": "Job erstellt. Modell 'MyModel' wird trainiert.",
  "status": "PENDING"
}
```

### Job-Status prüfen

```bash
GET /api/queue/{job_id}
```

```json
{
  "id": 424,
  "status": "COMPLETED",
  "result_model_id": 130,
  "progress": 100,
  "progress_msg": "Training abgeschlossen"
}
```

### Modell-Details abrufen

```bash
GET /api/models/{model_id}
```

---

## 🌐 Web UI

Die Web UI bietet dieselben Funktionen mit grafischer Oberfläche:

**URL:** https://test.local.chase295.de/training

Im Schritt 5 "Erweiterte Einstellungen" findest du:
- ⚖️ Klassen-Gewichtung (scale_pos_weight)
- Cross-Validation Einstellungen
- SMOTE Option
- Trainings-Zeitraum

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe die Job-Logs: `GET /api/queue/{job_id}`
2. Prüfe die Modell-Details: `GET /api/models/{model_id}`
3. Sieh dir die Confusion Matrix an für Einblicke in die Performance

---

**Dokumentation erstellt:** Januar 2026  
**Getestet:** 10/10 Tests bestanden ✅

