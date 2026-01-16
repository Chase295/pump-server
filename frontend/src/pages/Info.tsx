/**
 * Info-Seite - Vollständige Dokumentation des ML Prediction Service
 */
import React from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import PageContainer from '../components/layout/PageContainer';

const Info: React.FC = () => {
  return (
    <PageContainer>
      <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography variant="h3" sx={{ fontWeight: 700, mb: 2, color: '#00d4ff' }}>
            🤖 ML Prediction Service
          </Typography>
          <Typography variant="h5" sx={{ mb: 1, color: 'text.secondary' }}>
            🤖 ML Prediction Service Management
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            v1.0.0
          </Typography>
        </Box>

        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 3, color: '#00d4ff' }}>
              🤖 ML Prediction Service - Vollständige Dokumentation
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Alle Features, Parameter, Funktionen und API-Endpunkte im Detail erklärt
            </Typography>

            <Box sx={{ mb: 3, p: 2, bgcolor: 'rgba(0, 212, 255, 0.1)', borderRadius: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                Protokoll: HTTP/1.1 + RESTful API | Content-Type: application/json
              </Typography>
              <Typography variant="body2">
                Authentifizierung: Keine (internes Netzwerk) | Rate Limiting: Keins
              </Typography>
            </Box>
          </CardContent>
        </Card>

        {/* Was ist dieses System? */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              📖 WAS IST DIESES SYSTEM?
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Der ML Prediction Service ist ein Echtzeit-Vorhersage-System für Pump-Detection auf der Solana-Blockchain. 
              Er analysiert Kryptowährungs-Daten (Coins) in Echtzeit und sagt voraus, ob ein Coin in den nächsten X Minuten 
              um Y% steigen (Pump) oder fallen (Rug) wird.
            </Typography>
            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Das System kann:
            </Typography>
            <List>
              <ListItem>
                <ListItemText primary="• Modelle vom Training Service importieren und verwalten" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Automatisch Vorhersagen treffen, sobald neue Coin-Daten verfügbar sind (LISTEN/NOTIFY oder Polling)" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Zeitbasierte Vorhersagen treffen ('Steigt der Preis um 10% in 5 Minuten?')" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Alert-System mit konfigurierbaren Thresholds und n8n-Integration" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Coin-Filterung (Whitelist, alle Coins)" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Phasen-Filterung (Modelle können für spezifische Coin-Phasen konfiguriert werden: 1, 2, 3, 4, etc.)" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Coin-Ignore-System (verhindert zu häufige Scans basierend auf Vorhersage-Ergebnis - Alert/Positive/Bad)" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Manuelle Vorhersagen via API (mit vollständiger DB- und n8n-Integration)" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Alert-Auswertung mit ATH-Tracking (ATH Highest/Lowest während Auswertungsperiode)" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Detaillierte Statistiken und Performance-Metriken" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Coin-Details mit Preis-Kurven und Vorhersage-Historie" />
              </ListItem>
            </List>
            <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic', color: 'text.secondary' }}>
              Typischer Workflow: 1) Modell importieren → 2) Alert-Konfiguration einstellen → 3) Modell aktivieren → 
              4) Automatische Vorhersagen → 5) Alerts an n8n senden → 6) Auswertung und Statistiken analysieren
            </Typography>
          </CardContent>
        </Card>

        {/* Alle Features */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              📊 ALLE FEATURES IM DETAIL
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              1. Modell-Verwaltung
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Feature</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                    <TableCell><strong>API-Endpunkt</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Modell importieren</TableCell>
                    <TableCell>Lädt Modell vom Training Service herunter und speichert es lokal</TableCell>
                    <TableCell><code>POST /api/models/import</code></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell aktivieren/deaktivieren</TableCell>
                    <TableCell>Steuert, ob ein Modell für Vorhersagen verwendet wird</TableCell>
                    <TableCell><code>{`POST /api/models/{id}/activate`}</code><br /><code>{`POST /api/models/{id}/deactivate`}</code></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell umbenennen</TableCell>
                    <TableCell>Vergibt einen benutzerdefinierten Namen (nur lokal, ändert nicht Training Service)</TableCell>
                    <TableCell><code>{`PATCH /api/models/{id}/rename`}</code></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell löschen</TableCell>
                    <TableCell>Entfernt Modell aus Datenbank und löscht lokale Datei</TableCell>
                    <TableCell><code>{`DELETE /api/models/{id}`}</code></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell-Statistiken</TableCell>
                    <TableCell>Zeigt detaillierte Performance-Metriken (Accuracy, F1, etc.)</TableCell>
                    <TableCell><code>{`GET /api/models/{id}/statistics`}</code></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              2. Alert-System
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Feature</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                    <TableCell><strong>Einstellung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Alert-Threshold</TableCell>
                    <TableCell>Minimale Wahrscheinlichkeit (0-99%) für einen Alert. Standard: 70%</TableCell>
                    <TableCell>Konfigurierbar pro Modell (1-99%)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>n8n Webhook</TableCell>
                    <TableCell>URL für n8n-Integration. Alerts werden automatisch dorthin gesendet</TableCell>
                    <TableCell>Optional, pro Modell konfigurierbar</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Send-Modus</TableCell>
                    <TableCell>Welche Vorhersagen an n8n gesendet werden (mehrfach wählbar)</TableCell>
                    <TableCell>Optionen: all, alerts_only, positive_only, negative_only</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Coin-Filter</TableCell>
                    <TableCell>Welche Coins vom Modell verarbeitet werden</TableCell>
                    <TableCell>Optionen: all, whitelist, phases</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Coin-Ignore-System</TableCell>
                    <TableCell>Ignoriert Coins nach Vorhersage für konfigurierbare Zeit (basierend auf Ergebnis: negativ/positiv/alert)</TableCell>
                    <TableCell>Konfigurierbar pro Modell (ignore_bad/positive/alert_seconds)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Automatische Auswertung</TableCell>
                    <TableCell>Background-Job evaluiert Vorhersagen nach evaluation_timestamp (prüft ob Ziel erreicht wurde)</TableCell>
                    <TableCell>Status: aktiv (ausstehend), inaktiv (ausgewertet mit Ergebnis)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>ATH-Tracking</TableCell>
                    <TableCell>Verfolgt All-Time-High während der Auswertungsperiode</TableCell>
                    <TableCell>Automatisch für alle Alerts</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              3. Vorhersage-System
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Feature</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Automatische Vorhersagen</TableCell>
                    <TableCell>Event-Handler überwacht coin_metrics und macht automatisch Vorhersagen bei neuen Einträgen</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>LISTEN/NOTIFY</TableCell>
                    <TableCell>Echtzeit-Erkennung neuer Coin-Daten (&lt; 100ms Latency). Fallback: Polling alle 30s</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Batch-Verarbeitung</TableCell>
                    <TableCell>Sammelt mehrere Coins (max. 50) oder wartet 5 Sekunden für Batch-Verarbeitung</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Manuelle Vorhersagen</TableCell>
                    <TableCell>API-Endpunkt für manuelle Vorhersagen für einen spezifischen Coin. Speichert in DB, sendet an n8n (wenn konfiguriert), respektiert Phasen-Filterung</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Phasen-Filterung</TableCell>
                    <TableCell>Modelle können für spezifische Coin-Phasen (1, 2, 3, 4, etc.) konfiguriert werden. Nur Coins in den erlaubten Phasen werden verarbeitet</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Vorhersage-Status</TableCell>
                    <TableCell>Kategorisierung: Negativ (&lt;50%), Positiv (≥50%), Alert (≥Threshold)</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              4. Statistiken & Auswertungen
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Metrik</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Gesamt-Vorhersagen</TableCell>
                    <TableCell>Anzahl aller Vorhersagen des Modells</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alerts (≥Threshold)</TableCell>
                    <TableCell>Anzahl der Vorhersagen über dem Alert-Threshold</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Nicht-Alerts</TableCell>
                    <TableCell>Anzahl der Vorhersagen unter dem Alert-Threshold</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alerts: Success/Failed/Wait</TableCell>
                    <TableCell>Auswertungs-Status der Alerts (erfolgreich, fehlgeschlagen, ausstehend)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Nicht-Alerts: Success/Failed/Wait</TableCell>
                    <TableCell>Auswertungs-Status der Nicht-Alerts (invertierte Logik)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Success-Rates</TableCell>
                    <TableCell>Erfolgsquote für Alerts und Nicht-Alerts separat</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Performance-Summen</TableCell>
                    <TableCell>Gesamt-Performance, Gewinn-Summe, Verlust-Summe (in %)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Durchschnittliche Wahrscheinlichkeit</TableCell>
                    <TableCell>Mittlere Wahrscheinlichkeit aller Vorhersagen</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* API-Endpunkte */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              🔗 ALLE API-ENDPUNKTE
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              Modell-Verwaltung
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Aktion</strong></TableCell>
                    <TableCell><strong>Methode</strong></TableCell>
                    <TableCell><strong>Endpoint</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Verfügbare Modelle</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>/api/models/available</code></TableCell>
                    <TableCell>Liste aller verfügbaren Modelle vom Training Service (für Import)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell-Details (verfügbar)</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>{`/api/models/available/{model_id}`}</code></TableCell>
                    <TableCell>Details eines verfügbaren Modells vom Training Service</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell importieren</TableCell>
                    <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                    <TableCell><code>/api/models/import</code></TableCell>
                    <TableCell>Importiert Modell vom Training Service (Download + lokale Speicherung)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alle Modelle</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>/api/models</code></TableCell>
                    <TableCell>Liste aller importierten Modelle (aktiv + inaktiv)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Einzelnes Modell</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}`}</code></TableCell>
                    <TableCell>Details eines importierten Modells</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell aktivieren</TableCell>
                    <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/activate`}</code></TableCell>
                    <TableCell>Aktiviert Modell für Vorhersagen</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell deaktivieren</TableCell>
                    <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/deactivate`}</code></TableCell>
                    <TableCell>Deaktiviert Modell (keine Vorhersagen mehr)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell umbenennen</TableCell>
                    <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/rename`}</code></TableCell>
                    <TableCell>Vergibt benutzerdefinierten Namen (nur lokal)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell löschen</TableCell>
                    <TableCell><Chip label="DELETE" size="small" color="error" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}`}</code></TableCell>
                    <TableCell>Löscht Modell aus DB und lokale Datei</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell-Statistiken</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/statistics`}</code></TableCell>
                    <TableCell>Detaillierte Performance-Metriken eines Modells</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Alert-Konfiguration
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Aktion</strong></TableCell>
                    <TableCell><strong>Methode</strong></TableCell>
                    <TableCell><strong>Endpoint</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Alert-Konfiguration aktualisieren</TableCell>
                    <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/alert-config`}</code></TableCell>
                    <TableCell>Komplette Alert-Konfiguration (Threshold, n8n, Filter, etc.)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alert-Threshold aktualisieren</TableCell>
                    <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/alert-threshold`}</code></TableCell>
                    <TableCell>Nur Alert-Threshold ändern (1-99%)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>n8n-Einstellungen aktualisieren</TableCell>
                    <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/n8n-settings`}</code></TableCell>
                    <TableCell>Nur n8n-Einstellungen (Webhook, Send-Modus, Enabled)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Ignore-Einstellungen aktualisieren</TableCell>
                    <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/ignore-settings`}</code></TableCell>
                    <TableCell>Coin-Ignore-Zeiten (bad, positive, alert) in Sekunden</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Ignore-Einstellungen abrufen</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/ignore-settings`}</code></TableCell>
                    <TableCell>Holt aktuelle Ignore-Einstellungen</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>n8n-Status abrufen</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/n8n-status`}</code></TableCell>
                    <TableCell>Zeigt n8n-Konfigurations-Status</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Vorhersagen
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Aktion</strong></TableCell>
                    <TableCell><strong>Methode</strong></TableCell>
                    <TableCell><strong>Endpoint</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Manuelle Vorhersage</TableCell>
                    <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                    <TableCell><code>/api/predict</code></TableCell>
                    <TableCell>Macht Vorhersage für einen Coin mit allen aktiven Modellen. Speichert in DB, sendet an n8n (wenn konfiguriert), respektiert Phasen-Filterung</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alle Vorhersagen</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>/api/predictions</code></TableCell>
                    <TableCell>Liste aller Vorhersagen mit Filtern (coin_id, model_id, probability, etc.)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Neueste Vorhersage</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>{`/api/predictions/latest/{coin_id}`}</code></TableCell>
                    <TableCell>Neueste Vorhersage für einen Coin</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Alert-Logs & Auswertungen
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Aktion</strong></TableCell>
                    <TableCell><strong>Methode</strong></TableCell>
                    <TableCell><strong>Endpoint</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Modell-Vorhersagen abrufen</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>/api/model-predictions</code></TableCell>
                    <TableCell>Liste aller Modell-Vorhersagen mit Filtern (status, tag, coin_id, date_from, date_to, etc.)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Vorhersage-Details</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>{`/api/model-predictions/{prediction_id}`}</code></TableCell>
                    <TableCell>Details einer einzelnen Vorhersage mit Preis-Kurve</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Vorhersagen löschen</TableCell>
                    <TableCell><Chip label="DELETE" size="small" color="error" /></TableCell>
                    <TableCell><code>{`/api/model-predictions/model/{active_model_id}`}</code></TableCell>
                    <TableCell>Löscht alle Vorhersagen für ein Modell (Reset)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Auswertungs-Job starten</TableCell>
                    <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                    <TableCell><code>/api/admin/evaluate-predictions</code></TableCell>
                    <TableCell>Startet manuell den Background-Job zur Auswertung ausstehender Vorhersagen</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alte Logs löschen</TableCell>
                    <TableCell><Chip label="DELETE" size="small" color="error" /></TableCell>
                    <TableCell><code>{`/api/admin/delete-old-logs/{active_model_id}`}</code></TableCell>
                    <TableCell>Löscht alle alten Logs (alert_evaluations, predictions, model_predictions) für ein Modell</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Coin-Details
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Aktion</strong></TableCell>
                    <TableCell><strong>Methode</strong></TableCell>
                    <TableCell><strong>Endpoint</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Coin-Details</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>{`/api/models/{active_model_id}/coins/{coin_id}/details`}</code></TableCell>
                    <TableCell>Preis-Historie, Vorhersagen und Auswertungen für einen Coin mit Graph</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              System & Konfiguration
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Aktion</strong></TableCell>
                    <TableCell><strong>Methode</strong></TableCell>
                    <TableCell><strong>Endpoint</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Health Check</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>/api/health</code></TableCell>
                    <TableCell>System-Status, DB-Verbindung, Uptime, aktive Modelle</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Prometheus Metrics</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>/api/metrics</code></TableCell>
                    <TableCell>Prometheus-kompatible Metriken (Text-Format)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Service-Statistiken</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>/api/stats</code></TableCell>
                    <TableCell>Gesamt-Statistiken (Anzahl Vorhersagen, Modelle, etc.)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Konfiguration abrufen</TableCell>
                    <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                    <TableCell><code>/api/config</code></TableCell>
                    <TableCell>Persistente Konfiguration (DB_DSN, TRAINING_SERVICE_API_URL)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Konfiguration speichern</TableCell>
                    <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                    <TableCell><code>/api/config</code></TableCell>
                    <TableCell>Speichert persistente Konfiguration (überlebt Container-Neustarts)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Service neu starten</TableCell>
                    <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                    <TableCell><code>/api/system/restart</code></TableCell>
                    <TableCell>Startet Backend-Service neu (lädt neue Konfiguration)</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Alert-Konfiguration Details */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              ⚙️ ALERT-KONFIGURATION IM DETAIL
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              Alert-Threshold
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Der Alert-Threshold bestimmt, ab welcher Wahrscheinlichkeit eine Vorhersage als "Alert" gilt.
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Wert</strong></TableCell>
                    <TableCell><strong>Bedeutung</strong></TableCell>
                    <TableCell><strong>Beispiel</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>1-99%</TableCell>
                    <TableCell>Minimale Wahrscheinlichkeit für Alert</TableCell>
                    <TableCell>70% = Alle Vorhersagen ≥70% sind Alerts</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Standard</TableCell>
                    <TableCell>70% (0.7)</TableCell>
                    <TableCell>Kann pro Modell individuell eingestellt werden</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Send-Modus (n8n)
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Bestimmt, welche Vorhersagen an n8n gesendet werden. <strong>Mehrfachauswahl möglich!</strong>
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Modus</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell><code>all</code></TableCell>
                    <TableCell>Alle Vorhersagen werden gesendet (unabhängig von Wahrscheinlichkeit)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>alerts_only</code></TableCell>
                    <TableCell>Nur Vorhersagen über dem Alert-Threshold</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>positive_only</code></TableCell>
                    <TableCell>Nur Vorhersagen ≥50% Wahrscheinlichkeit</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>negative_only</code></TableCell>
                    <TableCell>Nur Vorhersagen &lt;50% Wahrscheinlichkeit</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
            <Typography variant="body2" sx={{ mb: 3, fontStyle: 'italic', color: 'text.secondary' }}>
              Beispiel: <code>["alerts_only", "positive_only"]</code> sendet sowohl Alerts als auch positive Vorhersagen.
            </Typography>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Coin-Filter
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Modus</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell><code>all</code></TableCell>
                    <TableCell>Alle Coins werden verarbeitet (Standard)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>whitelist</code></TableCell>
                    <TableCell>Nur Coins in der Whitelist werden verarbeitet</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Coin-Ignore-System
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Verhindert, dass derselbe Coin zu häufig gescannt wird, basierend auf dem Vorhersage-Ergebnis. <strong>Modell-spezifisch!</strong>
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Einstellung</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                    <TableCell><strong>Standard</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell><code>ignore_bad_seconds</code></TableCell>
                    <TableCell>Ignoriert Coin nach negativer Vorhersage (Wahrscheinlichkeit &lt; 50%)</TableCell>
                    <TableCell>0 (deaktiviert)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>ignore_positive_seconds</code></TableCell>
                    <TableCell>Ignoriert Coin nach positiver Vorhersage (Wahrscheinlichkeit ≥ 50% aber &lt; Threshold)</TableCell>
                    <TableCell>0 (deaktiviert)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>ignore_alert_seconds</code></TableCell>
                    <TableCell>Ignoriert Coin nach Alert-Vorhersage (Wahrscheinlichkeit ≥ Threshold)</TableCell>
                    <TableCell>0 (deaktiviert)</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
            <Typography variant="body2" sx={{ mb: 3, fontStyle: 'italic', color: 'text.secondary' }}>
              <strong>Wichtig:</strong> Wenn ein Coin ignoriert wird, wird er <strong>komplett übersprungen</strong> - keine Vorhersage, kein Eintrag, kein Log. 
              Dies verhindert, dass sehr aktive Coins alle 5 Sekunden getestet werden.
            </Typography>
          </CardContent>
        </Card>

        {/* Auswertungs-System */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              📊 AUSWERTUNGS-SYSTEM IM DETAIL
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              Vorhersage-Status (Vorhersage-Status Spalte)
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Kategorisiert Vorhersagen basierend auf Wahrscheinlichkeit:
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Status</strong></TableCell>
                    <TableCell><strong>Bedingung</strong></TableCell>
                    <TableCell><strong>Farbe</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell><Chip label="Negativ" size="small" color="error" /></TableCell>
                    <TableCell>Wahrscheinlichkeit &lt; 50%</TableCell>
                    <TableCell>Rot</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><Chip label="Positiv" size="small" color="success" /></TableCell>
                    <TableCell>Wahrscheinlichkeit ≥ 50% aber &lt; Alert-Threshold</TableCell>
                    <TableCell>Grün</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><Chip label="Alert" size="small" sx={{ bgcolor: '#ff9800', color: '#fff', fontWeight: 700 }} /></TableCell>
                    <TableCell>Wahrscheinlichkeit ≥ Alert-Threshold</TableCell>
                    <TableCell>Orange (hervorgehoben)</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Status-System (Neue Architektur)
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Vereinfachtes Status-System mit klaren Tags und Status:
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Feld</strong></TableCell>
                    <TableCell><strong>Werte</strong></TableCell>
                    <TableCell><strong>Bedeutung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Tag</strong></TableCell>
                    <TableCell><Chip label="negativ" size="small" color="error" />, <Chip label="positiv" size="small" color="success" />, <Chip label="alert" size="small" sx={{ bgcolor: '#ff9800', color: '#fff' }} /></TableCell>
                    <TableCell>Automatisch basierend auf Wahrscheinlichkeit: &lt;50% = negativ, ≥50%&lt;Threshold = positiv, ≥Threshold = alert</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Status</strong></TableCell>
                    <TableCell><Chip label="aktiv" size="small" color="default" />, <Chip label="inaktiv" size="small" color="success" /></TableCell>
                    <TableCell>aktiv = Auswertung ausstehend, inaktiv = bereits ausgewertet</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Evaluation Result</strong></TableCell>
                    <TableCell>success, failed, not_applicable</TableCell>
                    <TableCell>Ergebnis der Auswertung (nur bei inaktiv): success = Ziel erreicht, failed = Ziel nicht erreicht</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              ATH-Tracking (All-Time-High)
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Während der Auswertungsperiode wird der höchste Preis (ATH) kontinuierlich verfolgt:
            </Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="ATH Preis-Änderung" 
                  secondary="Höchste prozentuale Preisänderung während der Auswertungsperiode (kann höher sein als die finale Änderung)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="ATH Timestamp" 
                  secondary="Zeitpunkt, an dem das ATH erreicht wurde"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="ATH Preis" 
                  secondary="Höchster Preis während der Auswertungsperiode"
                />
              </ListItem>
            </List>
            <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic', color: 'text.secondary' }}>
              <strong>Wichtig:</strong> Die finale Auswertung (Success/Failed) basiert auf dem Preis zum evaluation_timestamp, 
              aber das ATH zeigt den maximalen Gewinn, der während der Periode möglich gewesen wäre.
            </Typography>
          </CardContent>
        </Card>

        {/* Statistiken-Details */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              📈 STATISTIKEN-DETAILS
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              Übersicht-Statistiken
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Metrik</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Gesamt</TableCell>
                    <TableCell>Alle Vorhersagen des Modells (unabhängig von Threshold)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alerts (≥Threshold)</TableCell>
                    <TableCell>Anzahl der Vorhersagen über dem Alert-Threshold</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Nicht-Alerts</TableCell>
                    <TableCell>Anzahl der Vorhersagen unter dem Alert-Threshold</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Alerts-Details (≥Threshold)
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Metrik</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Alerts: Success</TableCell>
                    <TableCell>Alerts, die erfolgreich waren (Ziel wurde erreicht)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alerts: Failed</TableCell>
                    <TableCell>Alerts, die fehlgeschlagen sind (Ziel wurde nicht erreicht)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alerts: Wait</TableCell>
                    <TableCell>Alerts, die noch ausstehen (evaluation_timestamp noch nicht erreicht)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Alerts Success-Rate</TableCell>
                    <TableCell>Erfolgsquote der ausgewerteten Alerts: Success / (Success + Failed) × 100%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Nicht-Alerts-Details (&lt;Threshold)
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Metrik</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Nicht-Alerts: Success</TableCell>
                    <TableCell>Richtig als "nicht Alert" erkannt (Ziel wurde nicht erreicht, Modell hatte Recht)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Nicht-Alerts: Failed</TableCell>
                    <TableCell>Übersehener Gewinn (Ziel wurde erreicht, Modell hätte Alert geben sollen)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Nicht-Alerts: Wait</TableCell>
                    <TableCell>Nicht-Alerts, die noch ausstehen (evaluation_timestamp noch nicht erreicht)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Nicht-Alerts Success-Rate</TableCell>
                    <TableCell>Erfolgsquote der Nicht-Alerts: Success / (Success + Failed) × 100%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Performance-Summen
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Metrik</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Gesamt-Performance</TableCell>
                    <TableCell>Summe aller tatsächlichen Änderungen (Gewinne + Verluste zusammen)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Gewinn-Summe</TableCell>
                    <TableCell>Summe aller tatsächlichen Änderungen für Success-Alerts (nur Gewinne)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Verlust-Summe</TableCell>
                    <TableCell>Summe aller tatsächlichen Änderungen für Failed-Alerts (nur Verluste)</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
            <Typography variant="body2" sx={{ mb: 3, fontStyle: 'italic', color: 'text.secondary' }}>
              <strong>Hinweis:</strong> Alle Performance-Werte sind in Prozent angegeben. Positive Werte = Gewinn, negative Werte = Verlust.
            </Typography>
          </CardContent>
        </Card>

        {/* Event-Handler */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              ⚡ EVENT-HANDLER SYSTEM
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              Automatische Vorhersagen
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Der Event-Handler überwacht kontinuierlich die <code>coin_metrics</code> Tabelle auf neue Einträge und macht automatisch Vorhersagen.
            </Typography>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              LISTEN/NOTIFY (Echtzeit)
            </Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="Funktionsweise" 
                  secondary="PostgreSQL LISTEN/NOTIFY für Echtzeit-Erkennung neuer Coin-Daten (< 100ms Latency)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Trigger" 
                  secondary="Automatischer Trigger in coin_metrics sendet NOTIFY bei jedem INSERT"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Fallback" 
                  secondary="Falls LISTEN/NOTIFY nicht verfügbar, wechselt automatisch zu Polling"
                />
              </ListItem>
            </List>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Polling-Fallback
            </Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="Intervall" 
                  secondary="Prüft alle 30 Sekunden auf neue Einträge (konfigurierbar via POLLING_INTERVAL_SECONDS)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Batch-Verarbeitung" 
                  secondary="Sammelt max. 50 Coins oder wartet 5 Sekunden für Batch-Verarbeitung"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Parallel-Verarbeitung" 
                  secondary="Mehrere Coins werden parallel verarbeitet (alle aktiven Modelle)"
                />
              </ListItem>
            </List>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Verarbeitungs-Flow
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 212, 255, 0.1)', borderRadius: 2, mb: 2 }}>
              <Typography variant="body2" component="div">
                1. Neuer Coin-Eintrag in coin_metrics<br />
                2. Event-Handler erkennt neuen Eintrag (LISTEN/NOTIFY oder Polling)<br />
                3. Prüft Coin-Filter (all/whitelist)<br />
                4. Prüft Phasen-Filter (wenn Modell für spezifische Phasen konfiguriert - z.B. [1, 2] oder [3, 4])<br />
                5. Prüft Coin-Ignore-Status (basierend auf ignore_bad/positive/alert_seconds, Priorität: Alert &gt; Positive &gt; Bad)<br />
                6. Wenn ignoriert: Überspringe komplett (kein Eintrag, kein Log)<br />
                7. Lädt Coin-Historie für Feature-Engineering (nur Daten aus erlaubten Phasen, wenn Phasen-Filter aktiv)<br />
                8. Macht Vorhersage mit allen aktiven Modellen (die den Coin nicht ignorieren)<br />
                9. Speichert Vorhersage in model_predictions Tabelle (mit Tag: negativ/positiv/alert, Status: aktiv)<br />
                10. Aktualisiert Coin-Ignore-Cache (für nächste Ignore-Prüfung)<br />
                11. Sendet an n8n (wenn konfiguriert, gefiltert nach n8n_send_mode: all/alerts_only/positive_only/negative_only)<br />
                12. Background-Job evaluiert automatisch (alle 60s) ausstehende Vorhersagen (Status: aktiv → inaktiv)<br />
                13. ATH-Tracking-Loop aktualisiert kontinuierlich (alle 30s) ATH Highest/Lowest für aktive Vorhersagen
              </Typography>
            </Box>
          </CardContent>
        </Card>

        {/* API-Beispiele */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              🚀 KOMPLETTER BEISPIEL-WORKFLOW
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              1️⃣ Verfügbare Modelle abrufen
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                curl "http://localhost:3003/api/models/available"
              </code>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              2️⃣ Modell importieren
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                {`curl -X POST "http://localhost:3003/api/models/import" \\
  -H "Content-Type: application/json" \\
  -d '{"model_id": 337}'`}
              </code>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              3️⃣ Alert-Konfiguration einstellen
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                {`curl -X PATCH "http://localhost:3003/api/models/18/alert-config" \\
  -H "Content-Type: application/json" \\
  -d '{
    "alert_threshold": 0.75,
    "n8n_webhook_url": "https://n8n.example.com/webhook/abc",
    "n8n_enabled": true,
    "n8n_send_mode": ["alerts_only", "positive_only"],
    "coin_filter_mode": "all",
    "coin_whitelist": []
  }'`}
              </code>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              4️⃣ Modell aktivieren
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                curl -X POST "http://localhost:3003/api/models/18/activate"
              </code>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              5️⃣ Manuelle Vorhersage (optional)
            </Typography>
            <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
              Der manuelle Predict-Endpunkt macht Vorhersagen, speichert sie in der Datenbank und sendet sie an n8n (wenn konfiguriert).
              Er respektiert alle Filter (Phasen, Whitelist, Ignore-Einstellungen) genau wie der automatische Event-Handler.
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                {`# Mit allen aktiven Modellen:
curl -X POST "http://localhost:3003/api/predict" \\
  -H "Content-Type: application/json" \\
  -d '{"coin_id": "ABC123..."}'

# Nur mit bestimmten Modellen:
curl -X POST "http://localhost:3003/api/predict" \\
  -H "Content-Type: application/json" \\
  -d '{"coin_id": "ABC123...", "model_ids": [18, 20]}'`}
              </code>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              6️⃣ Modell-Vorhersagen abrufen
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                curl "http://localhost:3003/api/model-predictions?active_model_id=18&limit=50&offset=0&status=aktiv&tag=alert"
              </code>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              7️⃣ Vorhersage-Details abrufen
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                curl "http://localhost:3003/api/model-predictions/123?chart_before_minutes=10&chart_after_minutes=10"
              </code>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              8️⃣ Auswertungs-Job starten (optional)
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                curl -X POST "http://localhost:3003/api/admin/evaluate-predictions"
              </code>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              9️⃣ Coin-Details mit Graph
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: '0.875rem' }}>
              <code>
                curl "http://localhost:3003/api/models/18/coins/ABC123.../details?time_window_minutes=60"
              </code>
            </Box>
          </CardContent>
        </Card>

        {/* Einstellungen */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              ⚙️ ALLE EINSTELLUNGEN
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              System-Einstellungen (Persistent)
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Einstellung</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                    <TableCell><strong>Standard</strong></TableCell>
                    <TableCell><strong>Änderbar über UI</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>DB_DSN</TableCell>
                    <TableCell>PostgreSQL Verbindungs-String (externe Datenbank)</TableCell>
                    <TableCell>-</TableCell>
                    <TableCell>✅ Ja (Einstellungen-Seite)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>TRAINING_SERVICE_API_URL</TableCell>
                    <TableCell>URL zum Training Service (für Modell-Download)</TableCell>
                    <TableCell>-</TableCell>
                    <TableCell>✅ Ja (Einstellungen-Seite)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>N8N_WEBHOOK_URL</TableCell>
                    <TableCell>Globale n8n Webhook-URL (optional)</TableCell>
                    <TableCell>-</TableCell>
                    <TableCell>✅ Ja (Einstellungen-Seite)</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Modell-spezifische Einstellungen
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Einstellung</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                    <TableCell><strong>Standard</strong></TableCell>
                    <TableCell><strong>Bereich</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>alert_threshold</TableCell>
                    <TableCell>Minimale Wahrscheinlichkeit für Alert</TableCell>
                    <TableCell>70% (0.7)</TableCell>
                    <TableCell>1-99%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>n8n_webhook_url</TableCell>
                    <TableCell>n8n Webhook-URL für dieses Modell</TableCell>
                    <TableCell>-</TableCell>
                    <TableCell>URL oder leer</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>n8n_enabled</TableCell>
                    <TableCell>n8n-Integration aktiviert</TableCell>
                    <TableCell>true</TableCell>
                    <TableCell>true/false</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>n8n_send_mode</TableCell>
                    <TableCell>Welche Vorhersagen gesendet werden</TableCell>
                    <TableCell>["all"]</TableCell>
                    <TableCell>Array: all, alerts_only, positive_only, negative_only</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>coin_filter_mode</TableCell>
                    <TableCell>Coin-Filter-Modus</TableCell>
                    <TableCell>"all"</TableCell>
                    <TableCell>all, whitelist</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>phases</TableCell>
                    <TableCell>Erlaubte Coin-Phasen (Array). Nur Coins in diesen Phasen werden verarbeitet. Unterstützt alle Phasen (1, 2, 3, 4, 5, 6, etc.) und beliebige Kombinationen. Wenn leer/None: alle Phasen erlaubt</TableCell>
                    <TableCell>null (alle Phasen)</TableCell>
                    <TableCell>Array von Integers, z.B. [1, 2] oder [3, 4]</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>coin_whitelist</TableCell>
                    <TableCell>Liste erlaubter Coin-IDs (nur bei whitelist-Modus)</TableCell>
                    <TableCell>[]</TableCell>
                    <TableCell>Array von Coin-IDs</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>phases</TableCell>
                    <TableCell>Erlaubte Coin-Phasen (Array). Nur Coins in diesen Phasen werden verarbeitet. Unterstützt alle Phasen (1, 2, 3, 4, 5, 6, etc.) und beliebige Kombinationen. Wenn leer/None: alle Phasen erlaubt</TableCell>
                    <TableCell>null (alle Phasen)</TableCell>
                    <TableCell>Array von Integers, z.B. [1, 2] oder [3, 4]</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>ignore_bad_seconds</TableCell>
                    <TableCell>Ignoriere Coin nach negativer Vorhersage (Sekunden)</TableCell>
                    <TableCell>0</TableCell>
                    <TableCell>0-86400</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>ignore_positive_seconds</TableCell>
                    <TableCell>Ignoriere Coin nach positiver Vorhersage (Sekunden)</TableCell>
                    <TableCell>0</TableCell>
                    <TableCell>0-86400</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>ignore_alert_seconds</TableCell>
                    <TableCell>Ignoriere Coin nach Alert (Sekunden)</TableCell>
                    <TableCell>0</TableCell>
                    <TableCell>0-86400</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Filter & Suche */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              🔍 FILTER & SUCHE
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              Alert-Logs Filter
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Filter</strong></TableCell>
                    <TableCell><strong>Parameter</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Auswertungs-Status</TableCell>
                    <TableCell><code>status</code></TableCell>
                    <TableCell>pending, success, failed, expired</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Vorhersage-Status</TableCell>
                    <TableCell><code>predictionStatus</code></TableCell>
                    <TableCell>negativ (&lt;50%), positiv (≥50%), alert (≥Threshold)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Coin-ID</TableCell>
                    <TableCell><code>coin_id</code></TableCell>
                    <TableCell>Filter nach spezifischer Coin-ID</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Vorhersage-Typ</TableCell>
                    <TableCell><code>prediction_type</code></TableCell>
                    <TableCell>time_based, classic</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Von Datum</TableCell>
                    <TableCell><code>date_from</code></TableCell>
                    <TableCell>ISO-Format: 2026-01-13T00:00:00Z</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Bis Datum</TableCell>
                    <TableCell><code>date_to</code></TableCell>
                    <TableCell>ISO-Format: 2026-01-13T23:59:59Z</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Nicht-Alerts anzeigen</TableCell>
                    <TableCell><code>include_non_alerts</code></TableCell>
                    <TableCell>true/false - Zeigt auch Vorhersagen unter Threshold</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Vorhersagen Filter
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Filter</strong></TableCell>
                    <TableCell><strong>Parameter</strong></TableCell>
                    <TableCell><strong>Beschreibung</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Coin-ID</TableCell>
                    <TableCell><code>coin_id</code></TableCell>
                    <TableCell>Filter nach spezifischer Coin-ID</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modell-ID</TableCell>
                    <TableCell><code>model_id</code> oder <code>active_model_id</code></TableCell>
                    <TableCell>Filter nach Modell</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Vorhersage</TableCell>
                    <TableCell><code>prediction</code></TableCell>
                    <TableCell>0 (kein Pump) oder 1 (Pump)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Min. Wahrscheinlichkeit</TableCell>
                    <TableCell><code>min_probability</code></TableCell>
                    <TableCell>0.0 - 1.0 (z.B. 0.7 für ≥70%)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Max. Wahrscheinlichkeit</TableCell>
                    <TableCell><code>max_probability</code></TableCell>
                    <TableCell>0.0 - 1.0</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Phase</TableCell>
                    <TableCell><code>phase_id</code></TableCell>
                    <TableCell>1-6 (Coin-Phase)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Von Datum</TableCell>
                    <TableCell><code>date_from</code></TableCell>
                    <TableCell>ISO-Format String</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Bis Datum</TableCell>
                    <TableCell><code>date_to</code></TableCell>
                    <TableCell>ISO-Format String</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Technische Details */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, color: '#00d4ff' }}>
              🔧 TECHNISCHE DETAILS
            </Typography>
            <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600 }}>
              Architektur
            </Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="Backend" 
                  secondary="FastAPI (Python 3.11) mit asyncpg für Datenbank-Zugriff"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Frontend" 
                  secondary="React + TypeScript + Material-UI mit React Router"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Datenbank" 
                  secondary="PostgreSQL (extern, geteilt mit Training Service)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Event-Handling" 
                  secondary="LISTEN/NOTIFY (Echtzeit) mit Polling-Fallback (30s)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="ML-Frameworks" 
                  secondary="Scikit-learn, XGBoost (gleiche wie Training Service)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Deployment" 
                  secondary="Docker Compose (Frontend + Backend, keine DB)"
                />
              </ListItem>
            </List>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Datenbank-Tabellen
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Tabelle</strong></TableCell>
                    <TableCell><strong>Zweck</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell><code>prediction_active_models</code></TableCell>
                    <TableCell>Importierte Modelle mit Konfiguration (Alert-Threshold, n8n, etc.)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>model_predictions</code></TableCell>
                    <TableCell>Alle Vorhersagen mit Tag (negativ/positiv/alert), Status (aktiv/inaktiv), Auswertungsergebnissen und ATH-Tracking</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>coin_scan_cache</code></TableCell>
                    <TableCell>Cache für Coin-Ignore-System (ignore_until, ignore_reason, modell-spezifisch)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>predictions</code></TableCell>
                    <TableCell>Alte Tabelle (deprecated, wird nicht mehr verwendet)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>alert_evaluations</code></TableCell>
                    <TableCell>Alte Tabelle (deprecated, wird nicht mehr verwendet)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><code>coin_metrics</code></TableCell>
                    <TableCell>Coin-Daten (extern, wird vom Training Service befüllt)</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              Ports & Zugriff
            </Typography>
            <TableContainer component={Paper} sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Service</strong></TableCell>
                    <TableCell><strong>Port</strong></TableCell>
                    <TableCell><strong>URL</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Frontend (Nginx)</TableCell>
                    <TableCell>3003</TableCell>
                    <TableCell>http://localhost:3003</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Backend (FastAPI)</TableCell>
                    <TableCell>8000</TableCell>
                    <TableCell>http://localhost:8000</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>API (via Frontend)</TableCell>
                    <TableCell>3003</TableCell>
                    <TableCell>http://localhost:3003/api/*</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {/* Footer */}
        <Box sx={{ mt: 4, p: 3, textAlign: 'center', color: 'text.secondary' }}>
          <Typography variant="body2">
            🔄 System läuft seit Start | Dokumentation Stand: Januar 2026
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            ⚠️ Wichtig: Alle Konfigurationen sind persistent und überleben Container-Neustarts
          </Typography>
        </Box>
      </Box>
    </PageContainer>
  );
};

export default Info;
