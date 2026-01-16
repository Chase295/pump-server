# 🔄 n8n Integration - ML Training Service

## Vollständige Anleitung für Workflow-Automatisierung

**Stand:** Januar 2026  
**Basis-URL:** `https://test.local.chase295.de/api`

---

## 📋 Inhaltsverzeichnis

1. [Workflow-Übersicht](#workflow-übersicht)
2. [Schritt 1: Modell erstellen](#schritt-1-modell-erstellen)
3. [Schritt 2: Job-Status prüfen](#schritt-2-job-status-prüfen)
4. [Schritt 3: Modell-Details abrufen](#schritt-3-modell-details-abrufen)
5. [Vollständiger n8n Workflow](#vollständiger-n8n-workflow)
6. [Alle API-Endpoints](#alle-api-endpoints)
7. [Webhook für Benachrichtigungen](#webhook-für-benachrichtigungen)

---

## 🔄 Workflow-Übersicht

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Modell      │────▶│  2. Warten &    │────▶│  3. Modell-     │
│     erstellen   │     │     Status      │     │     Details     │
│                 │     │     prüfen      │     │     abrufen     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     POST                    GET                     GET
/models/create/advanced  /queue/{job_id}        /models/{model_id}
```

---

## 📤 Schritt 1: Modell erstellen

### HTTP Request Node

| Einstellung | Wert |
|-------------|------|
| **Method** | POST |
| **URL** | `https://test.local.chase295.de/api/models/create/advanced` |
| **Authentication** | None |
| **Send Query Parameters** | ✅ Ja |

### Query Parameters

```json
{
  "name": "n8n_Auto_Model_{{ $now.format('yyyyMMdd_HHmmss') }}",
  "model_type": "xgboost",
  "features": "price_close,volume_sol,buy_pressure_ratio,dev_sold_amount",
  "train_start": "{{ $now.minus(12, 'hours').toISO() }}",
  "train_end": "{{ $now.minus(1, 'hours').toISO() }}",
  "future_minutes": "10",
  "min_percent_change": "5",
  "direction": "up",
  "use_engineered_features": "true",
  "scale_pos_weight": "100"
}
```

### Response (Erfolg)

```json
{
  "job_id": 435,
  "message": "Job erstellt. Modell 'n8n_Auto_Model_20260107_213000' wird trainiert.",
  "status": "PENDING"
}
```

### n8n Expression für Job-ID

```javascript
{{ $json.job_id }}
```

---

## ⏳ Schritt 2: Job-Status prüfen (Polling)

Das Training dauert 1-5 Minuten. Du musst den Status regelmäßig prüfen.

### HTTP Request Node

| Einstellung | Wert |
|-------------|------|
| **Method** | GET |
| **URL** | `https://test.local.chase295.de/api/queue/{{ $json.job_id }}` |

### Response (während Training)

```json
{
  "id": 435,
  "status": "IN_PROGRESS",
  "progress": 45,
  "progress_msg": "Feature Engineering...",
  "result_model_id": null
}
```

### Response (abgeschlossen)

```json
{
  "id": 435,
  "status": "COMPLETED",
  "progress": 100,
  "progress_msg": "Training abgeschlossen",
  "result_model_id": 131,
  "completed_at": "2026-01-07T21:35:00+00:00"
}
```

### Response (fehlgeschlagen)

```json
{
  "id": 435,
  "status": "FAILED",
  "progress": 0,
  "progress_msg": "Fehler",
  "error_msg": "Keine Trainingsdaten gefunden!",
  "result_model_id": null
}
```

### Mögliche Status-Werte

| Status | Bedeutung | Nächster Schritt |
|--------|-----------|------------------|
| `PENDING` | Wartet auf Worker | Weiter warten |
| `IN_PROGRESS` | Training läuft | Weiter warten |
| `COMPLETED` | ✅ Erfolgreich | Modell-Details abrufen |
| `FAILED` | ❌ Fehlgeschlagen | Fehler loggen |
| `CANCELLED` | Abgebrochen | - |

### n8n Loop-Logik

```javascript
// IF-Node Bedingung:
{{ $json.status }} !== "COMPLETED" && {{ $json.status }} !== "FAILED"

// Wenn wahr → Wait-Node (30 Sekunden) → zurück zu Status-Check
// Wenn falsch → weiter zu Modell-Details
```

---

## 📊 Schritt 3: Modell-Details abrufen

### HTTP Request Node

| Einstellung | Wert |
|-------------|------|
| **Method** | GET |
| **URL** | `https://test.local.chase295.de/api/models/{{ $json.result_model_id }}` |

### Response (vollständige Modell-Info)

```json
{
  "id": 131,
  "name": "n8n_Auto_Model_20260107_213000",
  "model_type": "xgboost",
  "status": "TRAINED",
  "created_at": "2026-01-07T21:30:00+00:00",
  
  "features": [
    "price_close",
    "volume_sol",
    "buy_pressure_ratio",
    "dev_sold_amount",
    "dev_sold_flag",
    "buy_pressure_ma_5",
    "..."
  ],
  "feature_count": 69,
  
  "training_accuracy": 0.9803,
  "training_precision": 0.0456,
  "training_recall": 0.0312,
  "training_f1": 0.0174,
  "training_roc_auc": 0.6234,
  
  "params": {
    "_time_based": {
      "enabled": true,
      "direction": "up",
      "future_minutes": 10,
      "min_percent_change": 5
    },
    "scale_pos_weight": 100,
    "use_engineered_features": true
  },
  
  "train_start": "2026-01-07T09:30:00+00:00",
  "train_end": "2026-01-07T20:30:00+00:00",
  
  "confusion_matrix": {
    "true_positives": 13,
    "false_positives": 272,
    "true_negatives": 48521,
    "false_negatives": 194
  },
  
  "feature_importance": {
    "price_close": 0.15,
    "volume_sol": 0.12,
    "buy_pressure_ratio": 0.11,
    "..."
  },
  
  "model_path": "/models/model_131.joblib"
}
```

### Wichtigste Metriken erklärt

| Metrik | Wert | Bedeutung |
|--------|------|-----------|
| `training_accuracy` | 0.98 | 98% korrekt (irreführend bei unbalancierten Daten!) |
| `training_precision` | 0.05 | 5% der "Pump"-Vorhersagen waren richtig |
| `training_recall` | 0.06 | 6% aller echten Pumps wurden erkannt |
| `training_f1` | 0.02 | Harmonisches Mittel aus Precision/Recall |
| `training_roc_auc` | 0.62 | Ranking-Qualität (>0.5 = besser als Zufall) |

### n8n Expressions für Metriken

```javascript
// Accuracy
{{ $json.training_accuracy * 100 }}%

// F1-Score
{{ ($json.training_f1 * 100).toFixed(2) }}%

// Ist das Modell gut?
{{ $json.training_f1 > 0.01 ? "✅ Brauchbar" : "⚠️ Schwach" }}

// Feature-Anzahl
{{ $json.features.length }} Features
```

---

## 🔧 Vollständiger n8n Workflow

### Workflow-Struktur

```
[Trigger] → [Create Model] → [Wait 30s] → [Check Status] → [IF Complete?]
                                              ↑                    │
                                              │    ┌───────────────┘
                                              │    ↓ Nein
                                              └────[Wait 30s]
                                                   ↓ Ja
                                          [Get Model Details] → [Process Results]
```

### JSON für n8n Import

```json
{
  "name": "ML Model Training Workflow",
  "nodes": [
    {
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [0, 0]
    },
    {
      "name": "Create Model",
      "type": "n8n-nodes-base.httpRequest",
      "position": [200, 0],
      "parameters": {
        "method": "POST",
        "url": "https://test.local.chase295.de/api/models/create/advanced",
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {"name": "name", "value": "={{ 'n8n_Model_' + $now.format('yyyyMMdd_HHmm') }}"},
            {"name": "model_type", "value": "xgboost"},
            {"name": "features", "value": "price_close,volume_sol,buy_pressure_ratio"},
            {"name": "train_start", "value": "={{ $now.minus(6, 'hours').toISO() }}"},
            {"name": "train_end", "value": "={{ $now.minus(1, 'hours').toISO() }}"},
            {"name": "future_minutes", "value": "10"},
            {"name": "min_percent_change", "value": "5"},
            {"name": "scale_pos_weight", "value": "100"}
          ]
        }
      }
    },
    {
      "name": "Wait 30s",
      "type": "n8n-nodes-base.wait",
      "position": [400, 0],
      "parameters": {
        "amount": 30,
        "unit": "seconds"
      }
    },
    {
      "name": "Check Job Status",
      "type": "n8n-nodes-base.httpRequest",
      "position": [600, 0],
      "parameters": {
        "method": "GET",
        "url": "=https://test.local.chase295.de/api/queue/{{ $('Create Model').item.json.job_id }}"
      }
    },
    {
      "name": "Is Complete?",
      "type": "n8n-nodes-base.if",
      "position": [800, 0],
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.status }}",
              "operation": "equals",
              "value2": "COMPLETED"
            }
          ]
        }
      }
    },
    {
      "name": "Get Model Details",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1000, -100],
      "parameters": {
        "method": "GET",
        "url": "=https://test.local.chase295.de/api/models/{{ $json.result_model_id }}"
      }
    },
    {
      "name": "Wait More",
      "type": "n8n-nodes-base.wait",
      "position": [1000, 100],
      "parameters": {
        "amount": 30,
        "unit": "seconds"
      }
    }
  ],
  "connections": {
    "Manual Trigger": {"main": [[{"node": "Create Model", "type": "main", "index": 0}]]},
    "Create Model": {"main": [[{"node": "Wait 30s", "type": "main", "index": 0}]]},
    "Wait 30s": {"main": [[{"node": "Check Job Status", "type": "main", "index": 0}]]},
    "Check Job Status": {"main": [[{"node": "Is Complete?", "type": "main", "index": 0}]]},
    "Is Complete?": {
      "main": [
        [{"node": "Get Model Details", "type": "main", "index": 0}],
        [{"node": "Wait More", "type": "main", "index": 0}]
      ]
    },
    "Wait More": {"main": [[{"node": "Check Job Status", "type": "main", "index": 0}]]}
  }
}
```

---

## 📡 Alle API-Endpoints

### Modell-Erstellung

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/models/create/advanced` | POST | Vollständig flexibel (EMPFOHLEN) |
| `/models/create/simple` | POST | Minimal (wenige Parameter) |
| `/models/create/time-based` | POST | Zeitbasiert (JSON Body) |

### Job-Verwaltung

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/queue` | GET | Alle Jobs auflisten |
| `/queue/{job_id}` | GET | Job-Status abrufen |
| `/queue/{job_id}` | DELETE | Job abbrechen |

### Modell-Verwaltung

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/models` | GET | Alle Modelle auflisten |
| `/models/{model_id}` | GET | Modell-Details |
| `/models/{model_id}` | DELETE | Modell löschen |
| `/models/{model_id}/predict` | POST | Vorhersage machen |

### System

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/health` | GET | System-Status |
| `/features` | GET | Verfügbare Features |

---

## 🔔 Webhook für Benachrichtigungen

Anstatt zu pollen, kannst du auch einen Webhook registrieren:

### Beispiel: Discord-Benachrichtigung

```json
{
  "name": "Notify on Complete",
  "type": "n8n-nodes-base.discord",
  "parameters": {
    "webhookUri": "https://discord.com/api/webhooks/...",
    "content": "🎉 Modell {{ $json.name }} wurde erstellt!\n\nF1-Score: {{ ($json.training_f1 * 100).toFixed(2) }}%\nFeatures: {{ $json.features.length }}"
  }
}
```

### Beispiel: Telegram-Benachrichtigung

```json
{
  "name": "Notify Telegram",
  "type": "n8n-nodes-base.telegram",
  "parameters": {
    "chatId": "YOUR_CHAT_ID",
    "text": "🤖 *Neues ML-Modell*\n\nName: `{{ $json.name }}`\nAccuracy: {{ ($json.training_accuracy * 100).toFixed(1) }}%\nF1: {{ ($json.training_f1 * 100).toFixed(2) }}%"
  }
}
```

---

## 📊 Erweiterte Beispiele

### Beispiel 1: Tägliches Auto-Training

```javascript
// Cron: Jeden Tag um 03:00 UTC
// Train mit Daten der letzten 24 Stunden

{
  "name": "Daily_Model_{{ $now.format('yyyyMMdd') }}",
  "train_start": "{{ $now.minus(25, 'hours').toISO() }}",
  "train_end": "{{ $now.minus(1, 'hours').toISO() }}"
}
```

### Beispiel 2: A/B-Test verschiedener Modelle

```javascript
// Erstelle 3 Modelle mit verschiedenen Einstellungen

// Modell A: Wenig Features
{"features": "price_close,volume_sol", "scale_pos_weight": "100"}

// Modell B: Viele Features
{"features": "...", "use_engineered_features": "true", "scale_pos_weight": "100"}

// Modell C: SMOTE statt scale_pos_weight
{"features": "...", "use_smote": "true"}

// Vergleiche die F1-Scores
```

### Beispiel 3: Modell-Qualitätsprüfung

```javascript
// n8n IF-Node: Nur wenn F1 > 0.01

{{ $json.training_f1 > 0.01 }}

// Wenn ja → Modell ist brauchbar
// Wenn nein → Lösche Modell oder markiere als "low quality"
```

---

## 🚨 Fehlerbehandlung

### Häufige Fehler

| HTTP Code | Bedeutung | Lösung |
|-----------|-----------|--------|
| 201 | ✅ Job erstellt | - |
| 400 | Ungültige Parameter | Parameter prüfen |
| 404 | Job/Modell nicht gefunden | ID prüfen |
| 422 | Validierungsfehler | Pflichtfelder prüfen |
| 500 | Server-Fehler | Logs prüfen |
| 502 | Backend nicht erreichbar | Warten & retry |

### n8n Error Handling

```json
{
  "name": "On Error",
  "type": "n8n-nodes-base.errorTrigger",
  "parameters": {},
  "onError": "continueRegularOutput"
}
```

---

## 📋 Checkliste für n8n Integration

- [ ] API-URL korrekt? (`https://test.local.chase295.de/api`)
- [ ] Zeiten in UTC (mit `Z` am Ende)?
- [ ] Features als komma-separierter String?
- [ ] Polling-Loop für Job-Status?
- [ ] Fehlerbehandlung implementiert?
- [ ] Benachrichtigung bei Abschluss?

---

## 💡 Pro-Tipps

### 1. Dynamische Zeitbereiche

```javascript
// Letzte 12 Stunden für Training
"train_start": "={{ $now.minus(12, 'hours').toISO() }}"
"train_end": "={{ $now.toISO() }}"
```

### 2. Modell-Namen mit Datum

```javascript
"name": "={{ 'AutoModel_' + $now.format('yyyyMMdd_HHmmss') }}"
```

### 3. Bedingte Features

```javascript
// Mehr Features am Wochenende (mehr Zeit)
"features": "={{ $now.weekday > 5 ? 'VIELE_FEATURES' : 'WENIGE_FEATURES' }}"
```

### 4. Retry bei Timeout

```json
{
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 60000
}
```

---

**Dokumentation erstellt:** Januar 2026  
**Getestet mit:** n8n v1.x

