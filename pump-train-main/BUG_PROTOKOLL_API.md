# 🚨 BUG-PROTOKOLL: ML Training Service API

**Stand:** Januar 2026
**Status:** 58 von 69 Jobs FAILED (84% Fehlerquote)

---

## 📊 **ZUSAMMENFASSUNG DER PROBLEME**

### **Fehler-Statistik:**
- **10 Jobs:** `cannot access local variable 'get_engineered_feature_names'` (Code-Bug)
- **9 Jobs:** `Keine Trainingsdaten gefunden!` (Datenverfügbarkeit)
- **6 Jobs:** Missing required fields für zeitbasierte Vorhersage
- **4 Jobs:** `column "price_change_pct" does not exist` (Feature Engineering)
- **4 Jobs:** `column "auto" does not exist` (Invalid Feature)
- **13 Jobs:** Unausgewogene Labels (Datenproblem)
- **1 Job:** Modell-Datei nicht gefunden (Test-Problem)

### **Root Cause Analyse:**
1. **Code-Bugs** (können behoben werden)
2. **Datenabhängige Probleme** (konfigurationabhängig)
3. **Feature Engineering Issues** (Performance + Kompatibilität)

---

## 🐛 **DETAILLIERTE BUG-ANALYSE**

### **BUG #1: CRITICAL - Import Scoping Error**
**Fehlermeldung:** `cannot access local variable 'get_engineered_feature_names' where it is not associated with a value`

**Betroffene Jobs:** 10 (IDs: 68, 69, + ältere)

**Root Cause:**
- Funktionen werden innerhalb von try/catch Blöcken importiert
- Python Variable Scoping: `local variable` Fehler wenn außerhalb des Blocks verwendet
- Mehrere Stellen in `engine.py` betroffen

**Affected Code Locations:**
1. `engine.py:284` - Feature Engineering Imports
2. `engine.py:352` - `validate_critical_features` Import
3. `engine.py:203` - `create_time_based_labels` Import
4. `engine.py:248` - `get_available_ath_features` Import
5. `engine.py:792` - `validate_ath_data_availability` Import
6. `engine.py:821` - `enrich_with_market_context` Import

**Reproduktion:**
```python
# ❌ PROBLEMATIC CODE PATTERN
def train_model_sync(...):
    if some_condition:
        from module import function  # Import inside if-block
    # ...
    function()  # ❌ "cannot access local variable" when condition=False
```

**Fix Required:**
```python
# ✅ CORRECTED CODE PATTERN
def train_model_sync(...):
    from module import function  # Import at function level
    if some_condition:
        # use function
    # function is available everywhere in function scope
```

**Status:** ❌ **NICHT BEHOBEN** - Fixes wurden versucht aber sind unvollständig

---

### **BUG #2: HIGH - Unausgewogene Labels**
**Fehlermeldung:** `Labels sind nicht ausgewogen: X positive, Y negative`

**Betroffene Jobs:** 13

**Root Cause:**
- Label-Bedingungen sind zu streng/weich für die verfügbaren Daten
- Zeitbasierte Preisänderungen kommen nicht vor
- Beispiel: `price_close > 0.05` ergibt 0 positive Labels

**Beispiele:**
- `0 positive, 906 negative` - Bedingung zu streng
- `743 positive, 0 negative` - Bedingung zu schwach
- `11354 positive, 0 negative` - Extrem unausgewogen

**Affected Features:**
- Zeitbasierte Vorhersage Labels
- Regelbasierte Bedingungen
- SMOTE kann nicht kompensieren wenn 0 Labels vorhanden

**Status:** ⚠️ **DATENABHÄNGIG** - Nicht wirklich ein Bug, aber API muss robuste Defaults haben

---

### **BUG #3: HIGH - Missing Training Data**
**Fehlermeldung:** `Keine Trainingsdaten gefunden!`

**Betroffene Jobs:** 9

**Root Cause:**
- Zeitbereiche ohne Daten in der Datenbank
- Ungültige Zeitstempel (z.B. 10:00-10:05 enthält keine Daten)
- Datenbank-Abfrage gibt leeres ResultSet zurück

**Reproduktion:**
```bash
# Datenverfügbarkeit prüfen
curl https://test.local.chase295.de/api/data-availability
# Returns: 2025-12-31T00:00:02Z bis 2026-01-03T19:57:18Z

# Aber dieser Bereich hat keine Daten:
"train_start": "2025-12-31T10:00:00Z",
"train_end": "2025-12-31T10:05:00Z"
```

**Status:** ⚠️ **KONFIGURATIONS-PROBLEM** - API muss validieren dass Daten verfügbar sind

---

### **BUG #4: MEDIUM - Feature Engineering Column Errors**
**Fehlermeldung:** `column "price_change_pct" does not exist`

**Betroffene Jobs:** 4

**Root Cause:**
- Feature Engineering erwartet Spalten die nicht in den Rohdaten vorhanden sind
- `create_pump_detection_features()` scheitert bei fehlenden Basis-Spalten
- Fallback-Mechanismus funktioniert nicht richtig

**Affected Columns:**
- `price_change_pct` - Sollte von Feature Engineering erstellt werden
- `rsi_14` - Technischer Indikator
- `price_change_1h` - Zeitbasierte Änderung
- `auto` - Invalid Feature-Name

**Status:** ❌ **FEATURE ENGINEERING BUG** - Erstellte Features stimmen nicht mit erwarteten überein

---

### **BUG #5: MEDIUM - Invalid Configuration**
**Fehlermeldung:** `target_var, target_operator und target_value müssen gesetzt sein wenn zeitbasierte Vorhersage nicht aktiviert ist`

**Betroffene Jobs:** 6

**Root Cause:**
- API validiert Parameter nicht korrekt vor Job-Erstellung
- Jobs werden mit inkonsistenten Parametern erstellt
- Zeitbasierte vs regelbasierte Vorhersage Parameter werden gemischt

**Status:** ❌ **VALIDIERUNGS-LÜCKE** - API sollte Parameter vorab validieren

---

### **BUG #6: LOW - Model File Not Found**
**Fehlermeldung:** `[Errno 2] No such file or directory: '/app/models/model_xgboost_20251229_002320.pkl'`

**Betroffene Jobs:** 1 (Test Job)

**Root Cause:**
- Modell-Datei wurde nicht erstellt (weil Training failed)
- Test versucht nicht-existierendes Modell zu laden
- Cleanup-Mechanismus fehlt

**Status:** ⚠️ **ABHÄNGIGKEITS-PROBLEM** - Test sollte nur laufen wenn Training erfolgreich war

---

## 🔧 **ERFORDERLICHE FIXES**

### **Priorität 1 - CRITICAL (Code-Bugs)**

#### **Fix #1.1: Import Scoping**
**Datei:** `app/training/engine.py`
**Zeilen:** 284, 352, 203, 248, 792, 821

**Lösung:**
```python
# ALLE Imports an den Anfang der Funktion verschieben
def train_model_sync(...):
    # Imports hierhin verschieben
    from app.training.feature_engineering import (
        create_pump_detection_features, get_engineered_feature_names,
        validate_critical_features, create_time_based_labels,
        get_available_ath_features, validate_ath_data_availability,
        enrich_with_market_context
    )
    # ... rest of function
```

#### **Fix #1.2: Variable Initialization**
**Datei:** `app/training/engine.py`
**Zeilen:** ~290

**Lösung:**
```python
# Variablen außerhalb von if-Blocks initialisieren
original_columns = set(data.columns)
new_columns = set()
engineered_features_created = []
window_sizes = params.get('feature_engineering_windows', [5, 10, 15])
```

### **Priorität 2 - HIGH (Validierung)**

#### **Fix #2.1: Pre-Validation**
**Datei:** `app/api/routes.py` - `create_model_job()`

**Lösung:**
```python
# Parameter validieren BEVOR Job erstellt wird
def validate_model_params(request):
    if request.use_time_based_prediction:
        if not request.future_minutes or not request.min_percent_change:
            raise HTTPException(400, "future_minutes und min_percent_change erforderlich")
    else:
        if not request.target_var or not request.operator or request.target_value is None:
            raise HTTPException(400, "target_var, operator und target_value erforderlich")
```

#### **Fix #2.2: Data Availability Check**
**Datei:** `app/api/routes.py`

**Lösung:**
```python
# Prüfen ob Daten im Zeitbereich verfügbar sind
def check_data_availability(start, end):
    # Datenbank-Abfrage um zu prüfen ob Daten vorhanden
    # Raise HTTPException wenn keine Daten gefunden
```

### **Priorität 3 - MEDIUM (Robustheit)**

#### **Fix #3.1: Feature Engineering Fallback**
**Datei:** `app/training/feature_engineering.py`

**Lösung:**
```python
# Robuste Fehlerbehandlung in create_pump_detection_features()
try:
    # Feature erstellen
except KeyError as e:
    logger.warning(f"Skipping feature {feature_name}: {e}")
    # Mit 0-Wert fortfahren
```

#### **Fix #3.2: Label Balancing**
**Datei:** `app/training/engine.py`

**Lösung:**
```python
# Automatische Anpassung von Bedingungen wenn Labels unausgewogen
if balance_ratio < 0.1:
    # Bedingung automatisch anpassen oder warnen
    logger.warning(f"Labels sehr unausgewogen ({balance_ratio:.2f}), SMOTE wird angewendet")
```

---

## 🧪 **TEST-STRATEGIEN**

### **Test nach Fixes:**

#### **Test 1: Import Scoping**
```bash
# Sollte funktionieren ohne "cannot access local variable"
curl -X POST /api/models/create/time-based \
  -d '{"name":"Test","model_type":"xgboost",...}'
```

#### **Test 2: Parameter Validation**
```bash
# Sollte 400 Bad Request zurückgeben für invalide Parameter
curl -X POST /api/models/create \
  -d '{"name":"Test","use_time_based_prediction":true}' # missing required fields
```

#### **Test 3: Data Availability**
```bash
# Sollte funktionieren mit verfügbaren Daten
curl -X POST /api/models/create/simple \
  -d '{"name":"Test","target":"price_close > 0.01","train_start":"2025-12-31T00:00:00Z","train_end":"2025-12-31T01:00:00Z"}'
```

---

## 📈 **ERWARTETE VERBESSERUNG**

### **Nach Fixes:**
- **Import Errors:** 0 (von 10)
- **Validation Errors:** 0 (von 6)
- **Data Errors:** Reduziert (von 9)
- **Feature Errors:** Reduziert (von 4)
- **Label Errors:** Reduziert durch bessere Defaults

### **Ziel:** <20% Fehlerquote (von aktuell 84%)

---

## 🎯 **AKTUELLE STATUS**

- ✅ **API Endpunkte:** Funktionieren
- ✅ **Job Creation:** Funktioniert
- ✅ **Simple Models:** Funktioniert
- ❌ **Advanced Features:** Mehrere Bugs
- ❌ **Error Handling:** Unvollständig
- ❌ **Input Validation:** Fehlt

**Nächste Schritte:** Fixes in Prioritätsreihenfolge implementieren.

