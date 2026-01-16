# 📊 Coin-Details Feature - Vollständiger Implementierungsplan

## 🎯 Ziel
Erweiterung der ModelLogs-Seite um eine Coin-Details-Seite, die beim Klick auf einen Coin geöffnet wird und folgende Features bietet:
- **Preis-Kurve** ab dem DB-Eintrag (Zeitpunkt der Vorhersage)
- **KI-Auswertungen** als Marker/Annotations in der Grafik
- **Zeitfenster-Einstellung** für die Anzeige
- **Responsive Design** mit Material-UI

---

## 📋 Schritt-für-Schritt Plan

### **Phase 1: Backend - API-Endpunkte** 🔧

#### **Schritt 1.1: Coin-Daten Endpunkt**
**Datei:** `ml-prediction-service/app/api/routes.py`

**Neuer Endpunkt:**
```python
GET /api/models/{model_id}/coins/{coin_id}/details
```

**Query-Parameter:**
- `start_timestamp` (optional): Start-Zeitpunkt für Preis-Historie
- `end_timestamp` (optional): End-Zeitpunkt für Preis-Historie
- `time_window_minutes` (optional): Zeitfenster in Minuten (default: 60)

**Response:**
```json
{
  "coin_id": "ABC123...",
  "model_id": 18,
  "prediction_timestamp": "2025-01-11T10:30:00Z",
  "price_history": [
    {
      "timestamp": "2025-01-11T10:30:00Z",
      "price_open": 0.001,
      "price_high": 0.0015,
      "price_low": 0.0009,
      "price_close": 0.0012,
      "volume_sol": 100.5,
      "market_cap_close": 50000
    }
  ],
  "predictions": [
    {
      "id": 123,
      "timestamp": "2025-01-11T10:30:00Z",
      "prediction": 1,
      "probability": 0.85,
      "alert_threshold": 0.7,
      "is_alert": true
    }
  ],
  "evaluations": [
    {
      "id": 456,
      "evaluation_timestamp": "2025-01-11T10:40:00Z",
      "status": "success",
      "actual_price_change": 0.15,
      "expected_change": 0.10
    }
  ]
}
```

**Implementierung:**
1. Neue Funktion in `app/database/models.py`: `get_coin_price_history()`
2. Neue Funktion in `app/database/models.py`: `get_coin_predictions_for_model()`
3. Neue Funktion in `app/database/alert_models.py`: `get_coin_evaluations_for_model()`
4. Route-Handler in `app/api/routes.py`

---

#### **Schritt 1.2: Datenbank-Funktionen**

**1.2.1: Preis-Historie abrufen**
```python
async def get_coin_price_history(
    coin_id: str,
    start_timestamp: datetime,
    end_timestamp: Optional[datetime] = None,
    pool: Optional[asyncpg.Pool] = None
) -> List[Dict[str, Any]]:
    """
    Holt Preis-Historie für einen Coin ab einem bestimmten Zeitpunkt.
    
    Args:
        coin_id: Coin-Mint-Adresse
        start_timestamp: Start-Zeitpunkt (normalerweise prediction_timestamp)
        end_timestamp: Optional: End-Zeitpunkt (falls nicht gesetzt: jetzt)
        pool: Optional: DB-Pool
    
    Returns:
        Liste von Dicts mit Preis-Daten, sortiert nach timestamp ASC
    """
```

**SQL-Query:**
```sql
SELECT 
    timestamp,
    price_open,
    price_high,
    price_low,
    price_close,
    volume_sol,
    market_cap_close
FROM coin_metrics
WHERE mint = $1
  AND timestamp >= $2
  AND ($3 IS NULL OR timestamp <= $3)
ORDER BY timestamp ASC
```

**1.2.2: Vorhersagen für Coin abrufen**
```python
async def get_coin_predictions_for_model(
    coin_id: str,
    model_id: int,
    start_timestamp: datetime,
    end_timestamp: Optional[datetime] = None,
    pool: Optional[asyncpg.Pool] = None
) -> List[Dict[str, Any]]:
    """
    Holt alle Vorhersagen für einen Coin und ein Modell.
    
    Returns:
        Liste von Dicts mit prediction_id, timestamp, prediction, probability, alert_threshold
    """
```

**SQL-Query:**
```sql
SELECT 
    p.id,
    p.data_timestamp as timestamp,
    p.prediction,
    p.probability,
    pam.alert_threshold
FROM predictions p
JOIN prediction_active_models pam ON p.active_model_id = pam.id
WHERE p.coin_id = $1
  AND p.active_model_id = $2
  AND p.data_timestamp >= $3
  AND ($4 IS NULL OR p.data_timestamp <= $4)
ORDER BY p.data_timestamp ASC
```

**1.2.3: Auswertungen für Coin abrufen**
```python
async def get_coin_evaluations_for_model(
    coin_id: str,
    model_id: int,
    start_timestamp: datetime,
    end_timestamp: Optional[datetime] = None,
    pool: Optional[asyncpg.Pool] = None
) -> List[Dict[str, Any]]:
    """
    Holt alle Alert-Auswertungen für einen Coin und ein Modell.
    
    Returns:
        Liste von Dicts mit evaluation_id, evaluation_timestamp, status, actual_price_change
    """
```

**SQL-Query:**
```sql
SELECT 
    ae.id,
    ae.evaluation_timestamp,
    ae.status,
    ae.actual_price_change,
    ae.expected_price_change,
    p.data_timestamp as prediction_timestamp,
    p.probability
FROM alert_evaluations ae
JOIN predictions p ON ae.prediction_id = p.id
WHERE p.coin_id = $1
  AND p.active_model_id = $2
  AND p.data_timestamp >= $3
  AND ($4 IS NULL OR p.data_timestamp <= $4)
ORDER BY ae.evaluation_timestamp ASC
```

---

#### **Schritt 1.3: Pydantic Schemas**

**Datei:** `ml-prediction-service/app/api/schemas.py`

**Neue Schemas:**
```python
class PriceDataPoint(BaseModel):
    timestamp: datetime
    price_open: float
    price_high: float
    price_low: float
    price_close: float
    volume_sol: Optional[float] = None
    market_cap_close: Optional[float] = None

class PredictionMarker(BaseModel):
    id: int
    timestamp: datetime
    prediction: int  # 0 oder 1
    probability: float
    alert_threshold: float
    is_alert: bool  # probability >= alert_threshold

class EvaluationMarker(BaseModel):
    id: int
    evaluation_timestamp: datetime
    prediction_timestamp: datetime
    status: str  # 'success', 'failed', 'pending', 'expired'
    actual_price_change: Optional[float] = None
    expected_price_change: Optional[float] = None
    probability: float

class CoinDetailsResponse(BaseModel):
    coin_id: str
    model_id: int
    prediction_timestamp: datetime
    price_history: List[PriceDataPoint]
    predictions: List[PredictionMarker]
    evaluations: List[EvaluationMarker]
```

---

### **Phase 2: Frontend - Routing & Navigation** 🧭

#### **Schritt 2.1: Route hinzufügen**

**Datei:** `ml-prediction-service/frontend/src/App.tsx`

**Neue Route:**
```typescript
<Route 
  path="/model/:modelId/coin/:coinId" 
  element={<CoinDetails />} 
/>
```

---

#### **Schritt 2.2: ModelLogs - Coins klickbar machen**

**Datei:** `ml-prediction-service/frontend/src/pages/ModelLogs.tsx`

**Änderungen:**
1. Coin-ID Spalte klickbar machen (Link/Button)
2. `useNavigate` verwenden, um zur Coin-Details-Seite zu navigieren
3. Coin-ID kürzen für Anzeige, aber vollständig übergeben

**Beispiel:**
```typescript
<TableCell>
  <Link
    component="button"
    variant="body2"
    onClick={() => navigate(`/model/${id}/coin/${alert.coin_id}`)}
    sx={{ 
      textDecoration: 'none',
      '&:hover': { textDecoration: 'underline' }
    }}
  >
    {alert.coin_id.slice(0, 8)}...
  </Link>
</TableCell>
```

---

### **Phase 3: Frontend - CoinDetails Komponente** 🎨

#### **Schritt 3.1: Grundstruktur**

**Neue Datei:** `ml-prediction-service/frontend/src/pages/CoinDetails.tsx`

**Komponenten-Struktur:**
```typescript
const CoinDetails: React.FC = () => {
  const { modelId, coinId } = useParams<{ modelId: string; coinId: string }>();
  const navigate = useNavigate();
  
  // State für Zeitfenster
  const [timeWindow, setTimeWindow] = React.useState<number>(60); // Minuten
  
  // API-Call für Coin-Daten
  const { data, isLoading, error } = useQuery({
    queryKey: ['coinDetails', modelId, coinId, timeWindow],
    queryFn: () => coinsApi.getDetails(Number(modelId), coinId, timeWindow)
  });
  
  return (
    <PageContainer>
      {/* Breadcrumbs */}
      {/* Zeitfenster-Einstellung */}
      {/* Grafik */}
      {/* Zusätzliche Info-Karten */}
    </PageContainer>
  );
};
```

---

#### **Schritt 3.2: API-Service erweitern**

**Datei:** `ml-prediction-service/frontend/src/services/api.ts`

**Neue API-Funktion:**
```typescript
export const coinsApi = {
  getDetails: async (
    modelId: number, 
    coinId: string, 
    timeWindowMinutes: number = 60
  ): Promise<CoinDetails> => {
    const response = await apiClient.get(
      `/models/${modelId}/coins/${coinId}/details`,
      {
        params: {
          time_window_minutes: timeWindowMinutes
        }
      }
    );
    return response.data;
  }
};
```

**Neue TypeScript-Types:**

**Datei:** `ml-prediction-service/frontend/src/types/model.ts`

```typescript
export interface PriceDataPoint {
  timestamp: string;
  price_open: number;
  price_high: number;
  price_low: number;
  price_close: number;
  volume_sol?: number;
  market_cap_close?: number;
}

export interface PredictionMarker {
  id: number;
  timestamp: string;
  prediction: number;
  probability: number;
  alert_threshold: number;
  is_alert: boolean;
}

export interface EvaluationMarker {
  id: number;
  evaluation_timestamp: string;
  prediction_timestamp: string;
  status: 'success' | 'failed' | 'pending' | 'expired';
  actual_price_change?: number;
  expected_price_change?: number;
  probability: number;
}

export interface CoinDetails {
  coin_id: string;
  model_id: number;
  prediction_timestamp: string;
  price_history: PriceDataPoint[];
  predictions: PredictionMarker[];
  evaluations: EvaluationMarker[];
}
```

---

#### **Schritt 3.3: Zeitfenster-Einstellung**

**Komponente:**
```typescript
<Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
  <Typography variant="body2" color="text.secondary">
    Zeitfenster:
  </Typography>
  <Select
    value={timeWindow}
    onChange={(e) => setTimeWindow(Number(e.target.value))}
    size="small"
    sx={{ minWidth: 120 }}
  >
    <MenuItem value={15}>15 Minuten</MenuItem>
    <MenuItem value={30}>30 Minuten</MenuItem>
    <MenuItem value={60}>1 Stunde</MenuItem>
    <MenuItem value={120}>2 Stunden</MenuItem>
    <MenuItem value={240}>4 Stunden</MenuItem>
    <MenuItem value={480}>8 Stunden</MenuItem>
    <MenuItem value={1440}>24 Stunden</MenuItem>
  </Select>
</Box>
```

---

### **Phase 4: Frontend - Grafik-Komponente** 📈

#### **Schritt 4.1: Plotly Integration**

**Installation (falls noch nicht vorhanden):**
```bash
npm install plotly.js react-plotly.js
```

**Datei:** `ml-prediction-service/frontend/src/components/charts/CoinPriceChart.tsx`

**Komponente:**
```typescript
import Plot from 'react-plotly.js';
import type { PriceDataPoint, PredictionMarker, EvaluationMarker } from '../../types/model';

interface CoinPriceChartProps {
  priceHistory: PriceDataPoint[];
  predictions: PredictionMarker[];
  evaluations: EvaluationMarker[];
  predictionTimestamp: string;
}

const CoinPriceChart: React.FC<CoinPriceChartProps> = ({
  priceHistory,
  predictions,
  evaluations,
  predictionTimestamp
}) => {
  // Candlestick-Daten vorbereiten
  const candlestickData = {
    x: priceHistory.map(p => p.timestamp),
    open: priceHistory.map(p => p.price_open),
    high: priceHistory.map(p => p.price_high),
    low: priceHistory.map(p => p.price_low),
    close: priceHistory.map(p => p.price_close),
    type: 'candlestick',
    name: 'Preis',
    increasing: { line: { color: '#26a69a' } },
    decreasing: { line: { color: '#ef5350' } }
  };
  
  // Prediction-Marker vorbereiten
  const predictionMarkers = predictions.map(p => ({
    x: p.timestamp,
    y: priceHistory.find(ph => 
      new Date(ph.timestamp).getTime() >= new Date(p.timestamp).getTime()
    )?.price_close || 0,
    text: `${(p.probability * 100).toFixed(1)}% ${p.prediction === 1 ? '↑' : '↓'}`,
    marker: {
      color: p.is_alert ? '#ff9800' : '#2196f3',
      size: 12,
      symbol: p.prediction === 1 ? 'triangle-up' : 'triangle-down'
    }
  }));
  
  // Evaluation-Marker vorbereiten
  const evaluationMarkers = evaluations.map(e => ({
    x: e.evaluation_timestamp,
    y: priceHistory.find(ph => 
      new Date(ph.timestamp).getTime() >= new Date(e.evaluation_timestamp).getTime()
    )?.price_close || 0,
    text: `${e.status === 'success' ? '✓' : e.status === 'failed' ? '✗' : '⏳'} ${e.actual_price_change ? (e.actual_price_change * 100).toFixed(1) + '%' : ''}`,
    marker: {
      color: e.status === 'success' ? '#4caf50' : e.status === 'failed' ? '#f44336' : '#ff9800',
      size: 10,
      symbol: 'circle'
    }
  }));
  
  const data = [
    candlestickData,
    {
      x: predictionMarkers.map(m => m.x),
      y: predictionMarkers.map(m => m.y),
      text: predictionMarkers.map(m => m.text),
      type: 'scatter',
      mode: 'markers+text',
      name: 'Vorhersagen',
      marker: {
        color: predictionMarkers.map(m => m.marker.color),
        size: predictionMarkers.map(m => m.marker.size),
        symbol: predictionMarkers.map(m => m.marker.symbol)
      },
      textposition: 'top center'
    },
    {
      x: evaluationMarkers.map(m => m.x),
      y: evaluationMarkers.map(m => m.y),
      text: evaluationMarkers.map(m => m.text),
      type: 'scatter',
      mode: 'markers+text',
      name: 'Auswertungen',
      marker: {
        color: evaluationMarkers.map(m => m.marker.color),
        size: evaluationMarkers.map(m => m.marker.size)
      },
      textposition: 'bottom center'
    }
  ];
  
  const layout = {
    title: 'Coin-Preis-Kurve mit KI-Auswertungen',
    xaxis: {
      title: 'Zeit',
      type: 'date'
    },
    yaxis: {
      title: 'Preis (SOL)',
      type: 'log' // Optional: Log-Skala für bessere Darstellung
    },
    hovermode: 'x unified',
    showlegend: true,
    height: 600
  };
  
  return (
    <Plot
      data={data}
      layout={layout}
      config={{ responsive: true }}
      style={{ width: '100%', height: '100%' }}
    />
  );
};
```

---

#### **Schritt 4.2: Alternative: Chart.js (falls Plotly zu schwer)**

**Installation:**
```bash
npm install chart.js react-chartjs-2
```

**Vorteile:**
- Leichter als Plotly
- Bessere Performance
- Einfacher zu stylen

**Nachteile:**
- Weniger Features
- Keine Candlestick-Charts out-of-the-box (muss selbst gebaut werden)

---

### **Phase 5: UI-Verbesserungen** 🎨

#### **Schritt 5.1: Zusätzliche Info-Karten**

**Komponente:**
```typescript
<Grid container spacing={2} sx={{ mt: 2 }}>
  <Grid item xs={12} md={4}>
    <Card>
      <CardContent>
        <Typography variant="h6">Vorhersage-Info</Typography>
        <Typography variant="body2">
          Erste Vorhersage: {formatDate(data.prediction_timestamp)}
        </Typography>
        <Typography variant="body2">
          Anzahl Vorhersagen: {data.predictions.length}
        </Typography>
        <Typography variant="body2">
          Anzahl Alerts: {data.predictions.filter(p => p.is_alert).length}
        </Typography>
      </CardContent>
    </Card>
  </Grid>
  
  <Grid item xs={12} md={4}>
    <Card>
      <CardContent>
        <Typography variant="h6">Auswertungen</Typography>
        <Typography variant="body2">
          Erfolgreich: {data.evaluations.filter(e => e.status === 'success').length}
        </Typography>
        <Typography variant="body2">
          Fehlgeschlagen: {data.evaluations.filter(e => e.status === 'failed').length}
        </Typography>
        <Typography variant="body2">
          Ausstehend: {data.evaluations.filter(e => e.status === 'pending').length}
        </Typography>
      </CardContent>
    </Card>
  </Grid>
  
  <Grid item xs={12} md={4}>
    <Card>
      <CardContent>
        <Typography variant="h6">Preis-Entwicklung</Typography>
        <Typography variant="body2">
          Start-Preis: {data.price_history[0]?.price_close.toFixed(6)} SOL
        </Typography>
        <Typography variant="body2">
          Aktueller Preis: {data.price_history[data.price_history.length - 1]?.price_close.toFixed(6)} SOL
        </Typography>
        <Typography variant="body2" color={priceChange >= 0 ? 'success.main' : 'error.main'}>
          Änderung: {((priceChange) * 100).toFixed(2)}%
        </Typography>
      </CardContent>
    </Card>
  </Grid>
</Grid>
```

---

#### **Schritt 5.2: Breadcrumbs & Navigation**

```typescript
<Breadcrumbs sx={{ mb: 3 }}>
  <MuiLink
    component={Link}
    to="/overview"
    color="inherit"
  >
    Übersicht
  </MuiLink>
  <MuiLink
    component={Link}
    to={`/model/${modelId}`}
    color="inherit"
  >
    Modell {modelId}
  </MuiLink>
  <MuiLink
    component={Link}
    to={`/model/${modelId}/logs`}
    color="inherit"
  >
    Logs
  </MuiLink>
  <Typography color="text.primary">
    Coin {coinId.slice(0, 8)}...
  </Typography>
</Breadcrumbs>
```

---

### **Phase 6: Performance & Optimierung** ⚡

#### **Schritt 6.1: Datenbank-Indizes**

**Prüfen ob Indizes existieren:**
```sql
-- Für coin_metrics
CREATE INDEX IF NOT EXISTS idx_coin_metrics_mint_timestamp 
ON coin_metrics(mint, timestamp ASC);

-- Für predictions (bereits vorhanden, prüfen)
-- idx_predictions_coin_timestamp sollte bereits existieren

-- Für alert_evaluations
CREATE INDEX IF NOT EXISTS idx_alert_evaluations_prediction_coin 
ON alert_evaluations(prediction_id) 
INCLUDE (evaluation_timestamp, status);
```

---

#### **Schritt 6.2: Caching**

**React Query Caching:**
- `staleTime`: 30 Sekunden (Preis-Daten ändern sich schnell)
- `cacheTime`: 5 Minuten
- `refetchOnWindowFocus`: false (optional)

---

#### **Schritt 6.3: Lazy Loading**

**Grafik-Komponente lazy laden:**
```typescript
const CoinPriceChart = React.lazy(() => import('../components/charts/CoinPriceChart'));

// In CoinDetails:
<Suspense fallback={<LoadingSpinner />}>
  <CoinPriceChart {...chartProps} />
</Suspense>
```

---

### **Phase 7: Testing & Validierung** ✅

#### **Schritt 7.1: Backend-Tests**

1. **API-Endpunkt testen:**
   ```bash
   curl "http://localhost:8000/api/models/18/coins/ABC123.../details?time_window_minutes=60"
   ```

2. **Edge Cases prüfen:**
   - Coin ohne Preis-Historie
   - Coin ohne Vorhersagen
   - Coin ohne Auswertungen
   - Sehr langes Zeitfenster (Performance)

---

#### **Schritt 7.2: Frontend-Tests**

1. **Navigation testen:**
   - Klick auf Coin-ID in ModelLogs
   - Breadcrumbs funktionieren
   - Zurück-Button funktioniert

2. **Grafik testen:**
   - Preis-Kurve wird angezeigt
   - Marker werden korrekt positioniert
   - Zeitfenster-Änderung funktioniert

3. **Responsive Design:**
   - Mobile Ansicht
   - Tablet Ansicht
   - Desktop Ansicht

---

## 📝 Implementierungs-Reihenfolge

### **Empfohlene Reihenfolge:**

1. ✅ **Phase 1: Backend API** (Schritte 1.1 - 1.3)
   - Datenbank-Funktionen
   - API-Endpunkt
   - Schemas

2. ✅ **Phase 2: Frontend Routing** (Schritt 2.1 - 2.2)
   - Route hinzufügen
   - ModelLogs klickbar machen

3. ✅ **Phase 3: CoinDetails Grundstruktur** (Schritt 3.1 - 3.3)
   - Komponente erstellen
   - API-Service erweitern
   - Zeitfenster-Einstellung

4. ✅ **Phase 4: Grafik** (Schritt 4.1)
   - Plotly/Chart.js Integration
   - Marker für Vorhersagen und Auswertungen

5. ✅ **Phase 5: UI-Verbesserungen** (Schritt 5.1 - 5.2)
   - Info-Karten
   - Breadcrumbs

6. ✅ **Phase 6: Performance** (Schritt 6.1 - 6.3)
   - Indizes
   - Caching
   - Lazy Loading

7. ✅ **Phase 7: Testing** (Schritt 7.1 - 7.2)
   - Backend-Tests
   - Frontend-Tests

---

## 🎨 Design-Überlegungen

### **Farben für Marker:**
- **Vorhersagen (Alert):** Orange (`#ff9800`)
- **Vorhersagen (Normal):** Blau (`#2196f3`)
- **Auswertungen (Success):** Grün (`#4caf50`)
- **Auswertungen (Failed):** Rot (`#f44336`)
- **Auswertungen (Pending):** Gelb (`#ff9800`)

### **Grafik-Typ:**
- **Candlestick-Chart** für Preis-Darstellung (professionell)
- **Line-Chart** als Alternative (einfacher)

### **Zeitfenster-Optionen:**
- 15 Minuten (kurzfristig)
- 30 Minuten
- 1 Stunde (Standard)
- 2 Stunden
- 4 Stunden
- 8 Stunden
- 24 Stunden (langfristig)

---

## 🔧 Technische Details

### **Dependencies:**
- `react-plotly.js` oder `react-chartjs-2` für Grafiken
- `@mui/material` für UI-Komponenten (bereits vorhanden)
- `@tanstack/react-query` für API-Calls (bereits vorhanden)

### **Performance:**
- Max. 1000 Datenpunkte für Preis-Historie (bei Bedarf paginieren)
- Debouncing für Zeitfenster-Änderung (300ms)
- Memoization für Grafik-Daten

---

## 📚 Zusätzliche Features (Optional)

### **Erweiterungen für später:**
1. **Export-Funktion:** CSV/PNG Export der Grafik
2. **Vergleich:** Mehrere Coins gleichzeitig anzeigen
3. **Zoom:** Interaktives Zoomen in der Grafik
4. **Tooltips:** Detaillierte Info beim Hover
5. **Statistiken:** Erweiterte Statistiken für den Coin
6. **Alert-Historie:** Vollständige Alert-Historie für den Coin

---

## ✅ Checkliste

- [ ] Backend API-Endpunkt implementiert
- [ ] Datenbank-Funktionen erstellt
- [ ] Pydantic Schemas definiert
- [ ] Frontend Route hinzugefügt
- [ ] ModelLogs Coins klickbar gemacht
- [ ] CoinDetails Komponente erstellt
- [ ] API-Service erweitert
- [ ] Zeitfenster-Einstellung implementiert
- [ ] Grafik-Komponente erstellt
- [ ] Marker für Vorhersagen und Auswertungen
- [ ] Info-Karten hinzugefügt
- [ ] Breadcrumbs implementiert
- [ ] Performance-Optimierungen
- [ ] Tests durchgeführt
- [ ] Dokumentation aktualisiert

---

**Viel Erfolg bei der Implementierung! 🚀**
