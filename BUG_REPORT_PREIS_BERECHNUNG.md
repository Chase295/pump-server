# 🐛 KRITISCHER BUG-REPORT: Preis-Berechnung

## 📋 Zusammenfassung

**Problem:** Die Preis-Änderung wird in der CoinDetails-Seite falsch berechnet, was zu abweichenden Werten führt (z.B. 19.51% statt 75%).

**Betroffene Bereiche:**
- ✅ Log-Seite: Korrekt (zeigt `actual_price_change_pct`)
- ❌ CoinDetails-Seite: Falsch (verwendet `priceHistory[0]` bis `priceHistory[last]`)

**Schweregrad:** 🔴 KRITISCH

---

## 🔍 Detaillierte Analyse

### 1. Problem-Beschreibung

**Beispiel-Coin:** `8opbUAy4YZTM5krXd3FNneCoYrom7HobcHhiGZWKpump`
**Prediction ID:** 817214

**Tatsächliche Werte:**
- Start-Preis (prediction_timestamp): `2.800000000000e-08`
- End-Preis (evaluation_timestamp): `4.900000000000e-08`
- **Korrekte Berechnung:** `((4.9e-08 - 2.8e-08) / 2.8e-08) * 100 = 75.00%`
- **Gespeichert in DB:** `actual_price_change_pct = 75.00%` ✅

**Was angezeigt wird:**
- **Log-Seite:** 75.00% ✅ (korrekt, verwendet `actual_price_change_pct`)
- **CoinDetails-Seite:** 19.51% ❌ (falsch!)

### 2. Ursache

**In `CoinDetails.tsx` (Zeile 224-226):**
```typescript
const startPrice = priceHistory[0]?.price_close || 0;
const endPrice = priceHistory[priceHistory.length - 1]?.price_close || 0;
const priceChange = startPrice > 0 ? ((endPrice - startPrice) / startPrice) * 100 : 0;
```

**Problem:**
- `priceHistory` enthält Daten von **10 Minuten vor `prediction_timestamp`** bis **10 Minuten nach `evaluation_timestamp`**
- `priceHistory[0]` ist **NICHT** der Preis zum `prediction_timestamp`, sondern 10 Minuten davor!
- `priceHistory[last]` ist **NICHT** der Preis zum `evaluation_timestamp`, sondern 10 Minuten danach!

**Beispiel:**
- `priceHistory[0]`: `4.100000000000e-08` (10min vor prediction)
- `priceHistory[last]`: `4.900000000000e-08` (10min nach evaluation)
- Berechnung: `((4.9e-08 - 4.1e-08) / 4.1e-08) * 100 = 19.51%` ❌

**Korrekt sollte sein:**
- Start-Preis: `2.800000000000e-08` (zum prediction_timestamp)
- End-Preis: `4.900000000000e-08` (zum evaluation_timestamp)
- Berechnung: `((4.9e-08 - 2.8e-08) / 2.8e-08) * 100 = 75.00%` ✅

### 3. Betroffene Bereiche

#### ✅ Log-Seite (`ModelLogs.tsx`)
- **Status:** ✅ KORREKT
- **Verwendet:** `actual_price_change_pct` aus der Datenbank
- **Anzeige:** Korrekte Werte

#### ❌ CoinDetails-Seite (`CoinDetails.tsx`)
- **Status:** ❌ FEHLERHAFT
- **Verwendet:** `priceHistory[0]` bis `priceHistory[last]`
- **Anzeige:** Falsche Werte (z.B. 19.51% statt 75%)

#### ✅ Datenbank (`model_predictions`)
- **Status:** ✅ KORREKT
- **Berechnung:** `actual_price_change_pct` wird korrekt berechnet und gespeichert
- **Formel:** `((price_close_at_evaluation - price_close_at_prediction) / price_close_at_prediction) * 100`

### 4. Prüfung: Negative Alerts

**Frage:** Werden negative Alerts auch falsch berechnet?

**Antwort:** 
- ✅ **Datenbank:** Negative Alerts werden korrekt berechnet (z.B. -10% wird als -10% gespeichert)
- ❌ **CoinDetails-Seite:** Negative Alerts werden auch falsch angezeigt (verwendet falsche Start/End-Preise)

**Beispiel für negativen Alert:**
- Start-Preis: `1.000000000000e-08`
- End-Preis: `0.900000000000e-08`
- **Korrekt:** `((0.9e-08 - 1.0e-08) / 1.0e-08) * 100 = -10.00%`
- **Falsch (CoinDetails):** Verwendet `priceHistory[0]` bis `priceHistory[last]`, was zu falschen Werten führt

---

## 🔧 Lösung

### Option 1: Verwende `actual_price_change_pct` direkt (EMPFOHLEN)

**Vorteil:** Einfach, schnell, verwendet bereits korrekte DB-Werte

```typescript
// In CoinDetails.tsx, stats useMemo
const stats = React.useMemo(() => {
  if (!coinDetails) return null;

  const priceHistory = coinDetails.price_history;
  if (priceHistory.length === 0) return null;

  // NEU: Verwende actual_price_change_pct aus der ersten Prediction
  const firstPrediction = coinDetails.predictions?.[0];
  const actualChangePct = firstPrediction?.actual_price_change_pct;
  
  // Fallback: Berechne aus price_close_at_prediction und price_close_at_evaluation
  let priceChange = 0;
  let startPrice = 0;
  let endPrice = 0;
  
  if (actualChangePct !== null && actualChangePct !== undefined) {
    // Verwende direkt den gespeicherten Wert
    priceChange = actualChangePct;
    
    // Finde Start- und End-Preis für Anzeige
    const predictionTimestamp = new Date(coinDetails.prediction_timestamp).getTime();
    const evaluationTimestamp = firstPrediction?.evaluation_timestamp 
      ? new Date(firstPrediction.evaluation_timestamp).getTime() 
      : null;
    
    // Finde Preis zum prediction_timestamp
    const predPricePoint = priceHistory.find(p => {
      const pointTime = new Date(p.timestamp).getTime();
      return Math.abs(pointTime - predictionTimestamp) < 60000; // ±1 Minute
    });
    
    if (predPricePoint) {
      startPrice = predPricePoint.price_close || predPricePoint.price_high || predPricePoint.price_low || 0;
    }
    
    // Finde Preis zum evaluation_timestamp
    if (evaluationTimestamp) {
      const evalPricePoint = priceHistory.find(p => {
        const pointTime = new Date(p.timestamp).getTime();
        return Math.abs(pointTime - evaluationTimestamp) < 60000; // ±1 Minute
      });
      
      if (evalPricePoint) {
        endPrice = evalPricePoint.price_close || evalPricePoint.price_high || evalPricePoint.price_low || 0;
      }
    }
    
    // Wenn keine Preise gefunden, berechne rückwärts aus actualChangePct
    if (startPrice > 0 && endPrice === 0) {
      endPrice = startPrice * (1 + actualChangePct / 100);
    } else if (endPrice > 0 && startPrice === 0) {
      startPrice = endPrice / (1 + actualChangePct / 100);
    }
  } else {
    // Fallback: Alte Logik (aber mit korrekten Timestamps)
    const predictionTimestamp = new Date(coinDetails.prediction_timestamp).getTime();
    const firstPrediction = coinDetails.predictions?.[0];
    const evaluationTimestamp = firstPrediction?.evaluation_timestamp 
      ? new Date(firstPrediction.evaluation_timestamp).getTime() 
      : null;
    
    // Finde Preis zum prediction_timestamp
    const predPricePoint = priceHistory.find(p => {
      const pointTime = new Date(p.timestamp).getTime();
      return Math.abs(pointTime - predictionTimestamp) < 60000;
    });
    
    if (predPricePoint) {
      startPrice = predPricePoint.price_close || predPricePoint.price_high || predPricePoint.price_low || 0;
    }
    
    // Finde Preis zum evaluation_timestamp
    if (evaluationTimestamp) {
      const evalPricePoint = priceHistory.find(p => {
        const pointTime = new Date(p.timestamp).getTime();
        return Math.abs(pointTime - evaluationTimestamp) < 60000;
      });
      
      if (evalPricePoint) {
        endPrice = evalPricePoint.price_close || evalPricePoint.price_high || evalPricePoint.price_low || 0;
      }
    }
    
    if (startPrice > 0 && endPrice > 0) {
      priceChange = ((endPrice - startPrice) / startPrice) * 100;
    }
  }

  const predictions = coinDetails.predictions;
  const evaluations = coinDetails.evaluations;

  return {
    startPrice,
    endPrice,
    priceChange,
    totalPredictions: predictions.length,
    totalAlerts: predictions.filter(p => p.is_alert).length,
    totalEvaluations: evaluations.length,
    successEvaluations: evaluations.filter(e => e.status === 'success').length,
    failedEvaluations: evaluations.filter(e => e.status === 'failed').length,
    pendingEvaluations: evaluations.filter(e => e.status === 'pending').length
  };
}, [coinDetails]);
```

### Option 2: Verwende Preise zum korrekten Timestamp

**Vorteil:** Berechnet aus price_history, aber mit korrekten Timestamps

```typescript
// Finde Preis zum prediction_timestamp
const predictionTimestamp = new Date(coinDetails.prediction_timestamp).getTime();
const predPricePoint = priceHistory.find(p => {
  const pointTime = new Date(p.timestamp).getTime();
  return Math.abs(pointTime - predictionTimestamp) < 60000; // ±1 Minute
});

// Finde Preis zum evaluation_timestamp
const firstPrediction = coinDetails.predictions?.[0];
const evaluationTimestamp = firstPrediction?.evaluation_timestamp 
  ? new Date(firstPrediction.evaluation_timestamp).getTime() 
  : null;

const evalPricePoint = evaluationTimestamp ? priceHistory.find(p => {
  const pointTime = new Date(p.timestamp).getTime();
  return Math.abs(pointTime - evaluationTimestamp) < 60000;
}) : null;

const startPrice = predPricePoint?.price_close || predPricePoint?.price_high || predPricePoint?.price_low || 0;
const endPrice = evalPricePoint?.price_close || evalPricePoint?.price_high || evalPricePoint?.price_low || 0;
const priceChange = startPrice > 0 && endPrice > 0 ? ((endPrice - startPrice) / startPrice) * 100 : 0;
```

---

## ✅ Empfohlene Lösung

**Option 1** ist empfohlen, da:
1. Sie verwendet bereits korrekte DB-Werte (`actual_price_change_pct`)
2. Sie ist einfacher zu implementieren
3. Sie ist konsistent mit der Log-Seite
4. Sie vermeidet Rundungsfehler durch doppelte Berechnung

---

## 🧪 Test-Plan

1. **Test mit positivem Alert:**
   - Coin: `8opbUAy4YZTM5krXd3FNneCoYrom7HobcHhiGZWKpump`
   - Erwartet: 75.00% (nicht 19.51%)

2. **Test mit negativem Alert:**
   - Suche einen negativen Alert
   - Erwartet: Korrekte negative Prozentzahl

3. **Test mit mehreren Predictions:**
   - Coin mit mehreren Predictions
   - Erwartet: Korrekte Werte für alle Predictions

---

## 📝 Zusammenfassung

**Problem:** CoinDetails-Seite verwendet `priceHistory[0]` bis `priceHistory[last]` statt Preise zum `prediction_timestamp` und `evaluation_timestamp`.

**Lösung:** Verwende `actual_price_change_pct` direkt aus der Prediction oder finde Preise zum korrekten Timestamp.

**Betroffene Dateien:**
- `frontend/src/pages/CoinDetails.tsx` (Zeile 217-242)

**Priorität:** 🔴 HOCH (kritischer Bug, betrifft alle CoinDetails-Anzeigen)
