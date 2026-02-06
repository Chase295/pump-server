# Glossar

## A

### Active Model
Ein importiertes ML-Modell, das im Prediction Service aktiv ist und Vorhersagen macht. Gespeichert in `prediction_active_models`.

### Alert
Eine Vorhersage mit hoher Wahrscheinlichkeit (probability >= alert_threshold). Löst n8n Webhook aus.

### Alert Evaluator
Background-Service, der ausstehende Alerts auswertet und ihren Status aktualisiert (success/failed/expired).

### Alert Threshold
Schwellwert (0.0-1.0), ab dem eine Vorhersage als Alert gilt. Standard: 0.7 (70%).

### ATH (All-Time-High)
Höchster Preis eines Coins seit der Vorhersage. Wird für Erfolgs-Evaluierung verwendet.

### ATH-Tracking
Kontinuierliche Überwachung des höchsten/niedrigsten Preises seit einer Vorhersage.

## B

### Batch Processing
Verarbeitung mehrerer Events gleichzeitig. Standard: 50 Events pro Batch.

## C

### Coin
Kryptowährung, identifiziert durch Mint-Adresse (coin_id).

### Coin Metrics
Externe Tabelle mit Preis- und Volume-Daten für jeden Coin. Wird vom Collector befüllt.

### Coin Filter
Filtert Coins für ein Modell. Modi: `all` (alle) oder `whitelist` (nur bestimmte).

### Coin Scan Cache
Cache-Tabelle für Ignore-Logik. Verhindert zu häufige Scans desselben Coins.

## D

### Dev Sold
Entwickler-Verkauf - wenn der Token-Ersteller verkauft. Wichtiges Feature für Rug-Detection.

## E

### Event Handler
Komponente, die coin_metrics auf neue Einträge überwacht und Vorhersagen triggert.

### Evaluation
Auswertung einer Vorhersage nach Ablauf des Zeitfensters (future_minutes).

## F

### FastAPI
Python Web-Framework für das Backend. Läuft auf Port 8000.

### Feature
Eingabe-Variable für ML-Modell (z.B. price_close, volume_sol, buy_pressure_ratio).

### Feature Engineering
Berechnung zusätzlicher Features aus Basisdaten (z.B. Rolling-Averages, ATH-Distance).

### Feature Processor
Modul, das Features für Vorhersagen aufbereitet. Muss identisch zum Training Service arbeiten.

### Future Minutes
Vorhersage-Horizont in Minuten (z.B. 5 = Vorhersage für 5 Minuten in die Zukunft).

## H

### Health Check
Endpoint `/api/health` zur Prüfung des Service-Status.

## I

### Ignore Settings
Einstellungen, wie lange ein Coin nach einer Vorhersage ignoriert wird:
- `ignore_bad_seconds`: Nach negativer Vorhersage
- `ignore_positive_seconds`: Nach positiver Vorhersage
- `ignore_alert_seconds`: Nach Alert

## J

### JSONB
PostgreSQL-Datentyp für JSON mit Indexierung. Verwendet für Features, Params, etc.

## L

### LISTEN/NOTIFY
PostgreSQL-Mechanismus für Echtzeit-Benachrichtigungen bei Datenbankänderungen.

## M

### Max Log Entries
Maximale Anzahl Einträge pro Coin und Tag (negativ/positiv/alert). 0 = unbegrenzt.

### MCC (Matthews Correlation Coefficient)
Metrik für Klassifikations-Qualität, besonders für unbalancierte Daten.

### MCP (Model Context Protocol)
Protokoll von Anthropic für KI-Tool-Integration. Ermöglicht Claude Code und anderen KI-Clients den direkten Zugriff auf Service-Funktionen. Der pump-server bietet einen integrierten MCP Server unter `/mcp/sse`.

### MCP Server
Komponente, die 38 Tools in 5 Kategorien fuer KI-Clients bereitstellt:
- Model-Tools (9): `list_active_models`, `import_model`, `rename_model`, `delete_model`, etc.
- Prediction-Tools (7): `predict_coin`, `get_predictions`, `get_model_predictions`, etc.
- Config-Tools (7): `update_alert_config`, `get_ignore_settings`, `get_max_log_entries`, etc.
- Alert-Tools (5): `get_alerts`, `get_alert_details`, `get_alert_statistics`, etc.
- System-Tools (10): `health_check`, `get_stats`, `get_logs`, `restart_system`, etc.

### MCP Tool
Eine Funktion, die über das MCP-Protokoll aufgerufen werden kann. Tools haben definierte Input-Parameter und geben strukturierte JSON-Responses zurück.

### Model
Trainiertes ML-Modell (RandomForest oder XGBoost) für Vorhersagen.

### Model Manager
Modul für Laden und Caching von ML-Modellen.

### Model Predictions
Tabelle mit allen Vorhersagen inkl. Status, ATH-Tracking und Evaluation.

## N

### n8n
Workflow-Automation-Tool. Empfängt Alerts via Webhook.

### n8n Send Mode
Steuerung, welche Vorhersagen an n8n gesendet werden:
- `all`: Alle
- `alerts_only`: Nur Alerts (probability >= threshold)
- `positive_only`: Nur prediction = 1
- `negative_only`: Nur prediction = 0

## P

### Phase
Marktphase eines Coins (z.B. 1, 2, 3). Modelle können auf spezifische Phasen trainiert sein.

### Polling
Regelmäßige DB-Abfrage als Fallback für LISTEN/NOTIFY. Standard: alle 30 Sekunden.

### Prediction
Vorhersage eines ML-Modells:
- `prediction`: 0 (negativ) oder 1 (positiv)
- `probability`: Wahrscheinlichkeit (0.0-1.0)

### Prediction Engine
Kernmodul, das Features aufbereitet und Vorhersagen mit ML-Modellen macht.

### Price Change Percent
Ziel-Preisänderung in Prozent für zeitbasierte Vorhersagen.

### Prometheus
Monitoring-System. Metriken via `/api/metrics`.

### PWA (Progressive Web App)
Web-App, die wie eine native App funktioniert. Frontend ist PWA-fähig.

## R

### RandomForest
ML-Algorithmus (Ensemble von Entscheidungsbäumen).

### ROC-AUC
Metrik für Klassifikations-Qualität (Area Under the ROC Curve).

### Rolling Window
Gleitendes Zeitfenster für Feature-Berechnung (z.B. 5, 10, 15 Minuten).

### Rug Pull
Betrug, bei dem Entwickler Liquidität abziehen. Das System versucht diese zu erkennen.

## S

### Send Ignored to n8n
Option, ignorierte Coins (wegen Max-Log-Entries) trotzdem an n8n zu senden.

### Status (Prediction)
- `aktiv`: Warte auf Evaluation
- `success`: Vorhersage war korrekt
- `failed`: Vorhersage war falsch
- `expired`: Zeitfenster abgelaufen
- `not_applicable`: Nicht auswertbar

### SSE (Server-Sent Events)
HTTP-Protokoll für unidirektionale Server-zu-Client-Kommunikation. Wird vom MCP Server für die Echtzeit-Kommunikation mit KI-Clients verwendet.

### Streamlit
Web-UI für das Backend. Läuft auf Port 8501.

### Supervisor
Prozess-Manager im Docker-Container. Verwaltet FastAPI, Event Handler, Streamlit.

## T

### Tag (Prediction)
Kategorisierung einer Vorhersage:
- `negativ`: probability < 0.5
- `positiv`: 0.5 <= probability < alert_threshold
- `alert`: probability >= alert_threshold

### Target Direction
Vorhersage-Richtung: `up` (Preis steigt) oder `down` (Preis fällt).

### Target Variable
Zielvariable des ML-Modells (z.B. price_change_pct).

### Training Service
Separater Service zum Trainieren von ML-Modellen. Pump Server importiert Modelle von dort.

## V

### Volume
Handelsvolumen in SOL.

## W

### Watchdog
Background-Task, der den Event Handler überwacht und bei Problemen neu startet.

### Webhook
HTTP-Aufruf an externe Services (n8n) bei Events.

### Whale
Großer Trader/Investor. Whale-Aktivität ist ein wichtiges Feature.

### Whale Dominance
Anteil des Whale-Volumens am Gesamtvolumen.

### Whitelist
Liste erlaubter Coins für ein Modell (bei coin_filter_mode = "whitelist").

## X

### XGBoost
ML-Algorithmus (Gradient Boosting).

## Z

### Zod
Schema-Validierung für TypeScript (Frontend Forms).
