/**
 * Info-Seite - Vollständige Dokumentation des Pump Server
 * Mit aufklappbaren Kapiteln für bessere Übersicht und Mobile-Optimierung
 */
import React, { useState, SyntheticEvent } from 'react';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PageContainer from '../components/layout/PageContainer';

// Kapitel-Komponente für einheitliches Styling
interface ChapterProps {
  id: string;
  title: string;
  icon: string;
  children: React.ReactNode;
  expanded: boolean;
  onChange: (event: SyntheticEvent, isExpanded: boolean) => void;
}

const Chapter: React.FC<ChapterProps> = ({ title, icon, children, expanded, onChange }) => (
  <Accordion
    expanded={expanded}
    onChange={onChange}
    sx={{
      mb: 2,
      '&:before': { display: 'none' },
      borderRadius: '12px !important',
      overflow: 'hidden',
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      border: '1px solid rgba(0, 212, 255, 0.2)',
      '&.Mui-expanded': {
        borderColor: 'rgba(0, 212, 255, 0.4)',
      }
    }}
  >
    <AccordionSummary
      expandIcon={<ExpandMoreIcon sx={{ color: '#00d4ff' }} />}
      sx={{
        backgroundColor: 'rgba(0, 212, 255, 0.08)',
        '&:hover': { backgroundColor: 'rgba(0, 212, 255, 0.12)' },
        minHeight: { xs: 56, sm: 64 },
        '& .MuiAccordionSummary-content': {
          my: { xs: 1, sm: 1.5 }
        }
      }}
    >
      <Typography
        variant="h6"
        sx={{
          fontWeight: 600,
          color: '#00d4ff',
          fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' }
        }}
      >
        {icon} {title}
      </Typography>
    </AccordionSummary>
    <AccordionDetails sx={{ pt: 3, px: { xs: 2, sm: 3 } }}>
      {children}
    </AccordionDetails>
  </Accordion>
);

// Responsive Tabelle-Wrapper
interface ResponsiveTableProps {
  children: React.ReactNode;
}

const ResponsiveTable: React.FC<ResponsiveTableProps> = ({ children }) => (
  <TableContainer
    component={Paper}
    sx={{
      mb: 3,
      overflowX: 'auto',
      '& .MuiTable-root': {
        minWidth: { xs: 400, sm: 500 }
      }
    }}
  >
    {children}
  </TableContainer>
);

const Info: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // State für expandierte Kapitel - erstes standardmäßig offen
  const [expandedChapters, setExpandedChapters] = useState<string[]>(['chapter-system']);

  const handleChapterChange = (chapter: string) => (_event: SyntheticEvent, isExpanded: boolean) => {
    setExpandedChapters(prev =>
      isExpanded
        ? [...prev, chapter]
        : prev.filter(c => c !== chapter)
    );
  };

  // Alle expandieren/kollabieren
  const allChapterIds = [
    'chapter-system', 'chapter-features', 'chapter-api', 'chapter-alerts',
    'chapter-evaluation', 'chapter-statistics', 'chapter-eventhandler',
    'chapter-workflow', 'chapter-settings', 'chapter-filters', 'chapter-technical',
    'chapter-mcp'
  ];

  const expandAll = () => setExpandedChapters(allChapterIds);
  const collapseAll = () => setExpandedChapters([]);

  return (
    <PageContainer>
      <Box sx={{ maxWidth: 1400, mx: 'auto', p: { xs: 1.5, sm: 2, md: 3 } }}>
        {/* Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              mb: 2,
              color: '#00d4ff',
              fontSize: { xs: '1.75rem', sm: '2.25rem', md: '3rem' }
            }}
          >
            Pump Server
          </Typography>
          <Typography
            variant="h5"
            sx={{
              mb: 1,
              color: 'text.secondary',
              fontSize: { xs: '1rem', sm: '1.25rem', md: '1.5rem' }
            }}
          >
            Management & Dokumentation
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            v1.0.0
          </Typography>
        </Box>

        {/* Quick Info Card */}
        <Card sx={{ mb: 4 }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 700,
                mb: 2,
                color: '#00d4ff',
                fontSize: { xs: '1.1rem', sm: '1.25rem', md: '1.5rem' }
              }}
            >
              Vollständige Dokumentation
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Alle Features, Parameter, Funktionen und API-Endpunkte im Detail erklärt
            </Typography>

            <Box sx={{ mb: 2, p: 2, bgcolor: 'rgba(0, 212, 255, 0.1)', borderRadius: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                Protokoll: HTTP/1.1 + RESTful API | Content-Type: application/json
              </Typography>
              <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                Authentifizierung: Keine (internes Netzwerk) | Rate Limiting: Keins
              </Typography>
            </Box>

            {/* Expand/Collapse Buttons */}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label="Alle aufklappen"
                onClick={expandAll}
                size={isMobile ? 'small' : 'medium'}
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'rgba(0, 212, 255, 0.2)' } }}
              />
              <Chip
                label="Alle zuklappen"
                onClick={collapseAll}
                size={isMobile ? 'small' : 'medium'}
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'rgba(0, 212, 255, 0.2)' } }}
              />
            </Box>
          </CardContent>
        </Card>

        {/* ===== KAPITEL 1: Was ist dieses System? ===== */}
        <Chapter
          id="chapter-system"
          title="Was ist dieses System?"
          icon="📖"
          expanded={expandedChapters.includes('chapter-system')}
          onChange={handleChapterChange('chapter-system')}
        >
          <Typography variant="body1" sx={{ mb: 2 }}>
            Der Pump Server ist ein Echtzeit-Vorhersage-System für Pump-Detection auf der Solana-Blockchain.
            Er analysiert Kryptowährungs-Daten (Coins) in Echtzeit und sagt voraus, ob ein Coin in den nächsten X Minuten
            um Y% steigen (Pump) oder fallen (Rug) wird.
          </Typography>
          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Das System kann:
          </Typography>
          <List dense={isMobile}>
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
              <ListItemText primary="• Coin-Ignore-System (verhindert zu häufige Scans basierend auf Vorhersage-Ergebnis)" />
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
        </Chapter>

        {/* ===== KAPITEL 2: Alle Features ===== */}
        <Chapter
          id="chapter-features"
          title="Alle Features im Detail"
          icon="⚡"
          expanded={expandedChapters.includes('chapter-features')}
          onChange={handleChapterChange('chapter-features')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            1. Modell-Verwaltung
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Feature</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}><strong>API-Endpunkt</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Modell importieren</TableCell>
                  <TableCell>Lädt Modell vom Training Service herunter und speichert es lokal</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}><code>POST /api/models/import</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Aktivieren/Deaktivieren</TableCell>
                  <TableCell>Steuert, ob ein Modell für Vorhersagen verwendet wird</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}><code>{`POST /api/models/{id}/activate`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Umbenennen</TableCell>
                  <TableCell>Vergibt benutzerdefinierten Namen (nur lokal)</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}><code>{`PATCH /api/models/{id}/rename`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Löschen</TableCell>
                  <TableCell>Entfernt Modell aus Datenbank und löscht lokale Datei</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}><code>{`DELETE /api/models/{id}`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Statistiken</TableCell>
                  <TableCell>Detaillierte Performance-Metriken (Accuracy, F1, etc.)</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}><code>{`GET /api/models/{id}/statistics`}</code></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            2. Alert-System
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Feature</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><strong>Einstellung</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Alert-Threshold</TableCell>
                  <TableCell>Minimale Wahrscheinlichkeit (0-99%) für einen Alert. Standard: 70%</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Konfigurierbar pro Modell</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>n8n Webhook</TableCell>
                  <TableCell>URL für n8n-Integration. Alerts werden automatisch dorthin gesendet</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Optional, pro Modell</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Send-Modus</TableCell>
                  <TableCell>Welche Vorhersagen an n8n gesendet werden (mehrfach wählbar)</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>all, alerts_only, positive_only, negative_only</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Coin-Filter</TableCell>
                  <TableCell>Welche Coins vom Modell verarbeitet werden</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>all, whitelist, phases</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Coin-Ignore-System</TableCell>
                  <TableCell>Ignoriert Coins nach Vorhersage für konfigurierbare Zeit</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>ignore_bad/positive/alert_seconds</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>ATH-Tracking</TableCell>
                  <TableCell>Verfolgt All-Time-High während der Auswertungsperiode</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Automatisch für alle Alerts</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            3. Vorhersage-System
          </Typography>
          <ResponsiveTable>
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
                  <TableCell>API-Endpunkt für manuelle Vorhersagen für einen spezifischen Coin</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Phasen-Filterung</TableCell>
                  <TableCell>Modelle können für spezifische Coin-Phasen (1, 2, 3, 4, etc.) konfiguriert werden</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Vorhersage-Status</TableCell>
                  <TableCell>Kategorisierung: Negativ (&lt;50%), Positiv (≥50%), Alert (≥Threshold)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            4. Statistiken & Auswertungen
          </Typography>
          <ResponsiveTable>
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
                  <TableCell>Success-Rates</TableCell>
                  <TableCell>Erfolgsquote für Alerts und Nicht-Alerts separat</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Performance-Summen</TableCell>
                  <TableCell>Gesamt-Performance, Gewinn-Summe, Verlust-Summe (in %)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>
        </Chapter>

        {/* ===== KAPITEL 3: API-Endpunkte ===== */}
        <Chapter
          id="chapter-api"
          title="Alle API-Endpunkte"
          icon="🔌"
          expanded={expandedChapters.includes('chapter-api')}
          onChange={handleChapterChange('chapter-api')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Modell-Verwaltung
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Aktion</strong></TableCell>
                  <TableCell><strong>Methode</strong></TableCell>
                  <TableCell><strong>Endpoint</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Verfügbare Modelle</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>/api/models/available</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Modell importieren</TableCell>
                  <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                  <TableCell><code>/api/models/import</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Alle Modelle</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>/api/models</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Modell aktivieren</TableCell>
                  <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                  <TableCell><code>{`/api/models/{id}/activate`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Modell deaktivieren</TableCell>
                  <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                  <TableCell><code>{`/api/models/{id}/deactivate`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Modell umbenennen</TableCell>
                  <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                  <TableCell><code>{`/api/models/{id}/rename`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Modell löschen</TableCell>
                  <TableCell><Chip label="DELETE" size="small" color="error" /></TableCell>
                  <TableCell><code>{`/api/models/{id}`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Statistiken</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>{`/api/models/{id}/statistics`}</code></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Alert-Konfiguration
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Aktion</strong></TableCell>
                  <TableCell><strong>Methode</strong></TableCell>
                  <TableCell><strong>Endpoint</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Alert-Config</TableCell>
                  <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                  <TableCell><code>{`/api/models/{id}/alert-config`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Alert-Threshold</TableCell>
                  <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                  <TableCell><code>{`/api/models/{id}/alert-threshold`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>n8n-Settings</TableCell>
                  <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                  <TableCell><code>{`/api/models/{id}/n8n-settings`}</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Ignore-Settings</TableCell>
                  <TableCell><Chip label="PATCH" size="small" color="warning" /></TableCell>
                  <TableCell><code>{`/api/models/{id}/ignore-settings`}</code></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Vorhersagen
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Aktion</strong></TableCell>
                  <TableCell><strong>Methode</strong></TableCell>
                  <TableCell><strong>Endpoint</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Manuelle Vorhersage</TableCell>
                  <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                  <TableCell><code>/api/predict</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Alle Vorhersagen</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>/api/predictions</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Model-Predictions</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>/api/model-predictions</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Neueste für Coin</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>{`/api/predictions/latest/{coin_id}`}</code></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            System & Config
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Aktion</strong></TableCell>
                  <TableCell><strong>Methode</strong></TableCell>
                  <TableCell><strong>Endpoint</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Health Check</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>/api/health</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Metrics</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>/api/metrics</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Stats</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>/api/stats</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Config laden</TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell><code>/api/config</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Config speichern</TableCell>
                  <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                  <TableCell><code>/api/config</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Service restart</TableCell>
                  <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                  <TableCell><code>/api/system/restart</code></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>
        </Chapter>

        {/* ===== KAPITEL 4: Alert-System ===== */}
        <Chapter
          id="chapter-alerts"
          title="Alert-System im Detail"
          icon="🔔"
          expanded={expandedChapters.includes('chapter-alerts')}
          onChange={handleChapterChange('chapter-alerts')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Alert-Threshold
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Der Alert-Threshold bestimmt, ab welcher Wahrscheinlichkeit eine Vorhersage als "Alert" gilt.
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Wert</strong></TableCell>
                  <TableCell><strong>Bedeutung</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><strong>Beispiel</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>1-99%</TableCell>
                  <TableCell>Minimale Wahrscheinlichkeit für Alert</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>70% = Alle Vorhersagen ≥70% sind Alerts</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Standard</TableCell>
                  <TableCell>70% (0.7)</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Kann pro Modell individuell eingestellt werden</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Send-Modus (n8n)
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Bestimmt, welche Vorhersagen an n8n gesendet werden. <strong>Mehrfachauswahl möglich!</strong>
          </Typography>
          <ResponsiveTable>
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
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Coin-Ignore-System
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Verhindert, dass derselbe Coin zu häufig gescannt wird, basierend auf dem Vorhersage-Ergebnis. <strong>Modell-spezifisch!</strong>
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Einstellung</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><strong>Standard</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>ignore_bad_seconds</code></TableCell>
                  <TableCell>Ignoriert Coin nach negativer Vorhersage (&lt; 50%)</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>0 (deaktiviert)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>ignore_positive_seconds</code></TableCell>
                  <TableCell>Ignoriert Coin nach positiver Vorhersage (≥ 50% aber &lt; Threshold)</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>0 (deaktiviert)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>ignore_alert_seconds</code></TableCell>
                  <TableCell>Ignoriert Coin nach Alert-Vorhersage (≥ Threshold)</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>0 (deaktiviert)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>
          <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic', color: 'text.secondary' }}>
            <strong>Wichtig:</strong> Wenn ein Coin ignoriert wird, wird er <strong>komplett übersprungen</strong> - keine Vorhersage, kein Eintrag, kein Log.
          </Typography>
        </Chapter>

        {/* ===== KAPITEL 5: Evaluation & ATH ===== */}
        <Chapter
          id="chapter-evaluation"
          title="Evaluation & ATH-Tracking"
          icon="📊"
          expanded={expandedChapters.includes('chapter-evaluation')}
          onChange={handleChapterChange('chapter-evaluation')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Vorhersage-Status (Tag)
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Kategorisiert Vorhersagen basierend auf Wahrscheinlichkeit:
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Bedingung</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><strong>Farbe</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><Chip label="Negativ" size="small" color="error" /></TableCell>
                  <TableCell>Wahrscheinlichkeit &lt; 50%</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Rot</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Chip label="Positiv" size="small" color="success" /></TableCell>
                  <TableCell>Wahrscheinlichkeit ≥ 50% aber &lt; Alert-Threshold</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Grün</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Chip label="Alert" size="small" sx={{ bgcolor: '#ff9800', color: '#fff', fontWeight: 700 }} /></TableCell>
                  <TableCell>Wahrscheinlichkeit ≥ Alert-Threshold</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Orange</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Status-System
          </Typography>
          <ResponsiveTable>
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
                  <TableCell>negativ, positiv, alert</TableCell>
                  <TableCell>Automatisch basierend auf Wahrscheinlichkeit</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell>aktiv, inaktiv</TableCell>
                  <TableCell>aktiv = Auswertung ausstehend, inaktiv = ausgewertet</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Evaluation Result</strong></TableCell>
                  <TableCell>success, failed, not_applicable</TableCell>
                  <TableCell>Ergebnis: success = Ziel erreicht, failed = nicht erreicht</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            ATH-Tracking (All-Time-High)
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Während der Auswertungsperiode wird der höchste Preis (ATH) kontinuierlich verfolgt:
          </Typography>
          <List dense={isMobile}>
            <ListItem>
              <ListItemText
                primary="ATH Preis-Änderung"
                secondary="Höchste prozentuale Preisänderung während der Auswertungsperiode"
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
            <strong>Wichtig:</strong> Die finale Auswertung basiert auf dem Preis zum evaluation_timestamp,
            aber das ATH zeigt den maximalen Gewinn, der während der Periode möglich gewesen wäre.
          </Typography>
        </Chapter>

        {/* ===== KAPITEL 6: Statistiken ===== */}
        <Chapter
          id="chapter-statistics"
          title="Statistiken-Details"
          icon="📈"
          expanded={expandedChapters.includes('chapter-statistics')}
          onChange={handleChapterChange('chapter-statistics')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Übersicht-Statistiken
          </Typography>
          <ResponsiveTable>
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
                  <TableCell>Alle Vorhersagen des Modells</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Alerts (≥Threshold)</TableCell>
                  <TableCell>Vorhersagen über dem Alert-Threshold</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Nicht-Alerts</TableCell>
                  <TableCell>Vorhersagen unter dem Alert-Threshold</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Alerts-Details (≥Threshold)
          </Typography>
          <ResponsiveTable>
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
                  <TableCell>Erfolgsquote: Success / (Success + Failed) × 100%</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Performance-Summen
          </Typography>
          <ResponsiveTable>
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
                  <TableCell>Summe aller tatsächlichen Änderungen (Gewinne + Verluste)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Gewinn-Summe</TableCell>
                  <TableCell>Summe aller tatsächlichen Änderungen für Success-Alerts</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Verlust-Summe</TableCell>
                  <TableCell>Summe aller tatsächlichen Änderungen für Failed-Alerts</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>
          <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic', color: 'text.secondary' }}>
            <strong>Hinweis:</strong> Alle Performance-Werte sind in Prozent angegeben. Positive Werte = Gewinn, negative Werte = Verlust.
          </Typography>
        </Chapter>

        {/* ===== KAPITEL 7: Event-Handler ===== */}
        <Chapter
          id="chapter-eventhandler"
          title="Event-Handler System"
          icon="⚡"
          expanded={expandedChapters.includes('chapter-eventhandler')}
          onChange={handleChapterChange('chapter-eventhandler')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Automatische Vorhersagen
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Der Event-Handler überwacht kontinuierlich die <code>coin_metrics</code> Tabelle auf neue Einträge und macht automatisch Vorhersagen.
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            LISTEN/NOTIFY (Echtzeit)
          </Typography>
          <List dense={isMobile}>
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

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Polling-Fallback
          </Typography>
          <List dense={isMobile}>
            <ListItem>
              <ListItemText
                primary="Intervall"
                secondary="Prüft alle 30 Sekunden auf neue Einträge"
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
                secondary="Mehrere Coins werden parallel verarbeitet"
              />
            </ListItem>
          </List>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Verarbeitungs-Flow
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'rgba(0, 212, 255, 0.1)', borderRadius: 2, mb: 2 }}>
            <Typography variant="body2" component="div" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              1. Neuer Coin-Eintrag in coin_metrics<br />
              2. Event-Handler erkennt neuen Eintrag<br />
              3. Prüft Coin-Filter (all/whitelist)<br />
              4. Prüft Phasen-Filter<br />
              5. Prüft Coin-Ignore-Status<br />
              6. Wenn ignoriert: Überspringe komplett<br />
              7. Lädt Coin-Historie für Feature-Engineering<br />
              8. Macht Vorhersage mit allen aktiven Modellen<br />
              9. Speichert Vorhersage in model_predictions<br />
              10. Aktualisiert Coin-Ignore-Cache<br />
              11. Sendet an n8n (wenn konfiguriert)<br />
              12. Background-Job evaluiert automatisch
            </Typography>
          </Box>
        </Chapter>

        {/* ===== KAPITEL 8: Beispiel-Workflow ===== */}
        <Chapter
          id="chapter-workflow"
          title="Beispiel-Workflow"
          icon="🚀"
          expanded={expandedChapters.includes('chapter-workflow')}
          onChange={handleChapterChange('chapter-workflow')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            1. Verfügbare Modelle abrufen
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: { xs: '0.7rem', sm: '0.875rem' }, overflowX: 'auto' }}>
            <code>
              curl "http://localhost:3003/api/models/available"
            </code>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            2. Modell importieren
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: { xs: '0.7rem', sm: '0.875rem' }, overflowX: 'auto' }}>
            <code>
              {`curl -X POST "http://localhost:3003/api/models/import" \\
  -H "Content-Type: application/json" \\
  -d '{"model_id": 337}'`}
            </code>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            3. Alert-Konfiguration einstellen
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: { xs: '0.7rem', sm: '0.875rem' }, overflowX: 'auto' }}>
            <code>
              {`curl -X PATCH "http://localhost:3003/api/models/18/alert-config" \\
  -H "Content-Type: application/json" \\
  -d '{"alert_threshold": 0.75, "n8n_enabled": true}'`}
            </code>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            4. Modell aktivieren
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: { xs: '0.7rem', sm: '0.875rem' }, overflowX: 'auto' }}>
            <code>
              curl -X POST "http://localhost:3003/api/models/18/activate"
            </code>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            5. Manuelle Vorhersage (optional)
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: { xs: '0.7rem', sm: '0.875rem' }, overflowX: 'auto' }}>
            <code>
              {`curl -X POST "http://localhost:3003/api/predict" \\
  -H "Content-Type: application/json" \\
  -d '{"coin_id": "ABC123..."}'`}
            </code>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            6. Modell-Vorhersagen abrufen
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: { xs: '0.7rem', sm: '0.875rem' }, overflowX: 'auto' }}>
            <code>
              curl "http://localhost:3003/api/model-predictions?active_model_id=18&limit=50"
            </code>
          </Box>
        </Chapter>

        {/* ===== KAPITEL 9: Einstellungen ===== */}
        <Chapter
          id="chapter-settings"
          title="Alle Einstellungen"
          icon="⚙️"
          expanded={expandedChapters.includes('chapter-settings')}
          onChange={handleChapterChange('chapter-settings')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            System-Einstellungen (Persistent)
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Einstellung</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}><strong>Änderbar</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>DB_DSN</TableCell>
                  <TableCell>PostgreSQL Verbindungs-String</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Ja (Einstellungen-Seite)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>TRAINING_SERVICE_API_URL</TableCell>
                  <TableCell>URL zum Training Service</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Ja (Einstellungen-Seite)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>N8N_WEBHOOK_URL</TableCell>
                  <TableCell>Globale n8n Webhook-URL</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Ja (Einstellungen-Seite)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Modell-spezifische Einstellungen
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Einstellung</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><strong>Standard</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>alert_threshold</TableCell>
                  <TableCell>Minimale Wahrscheinlichkeit für Alert</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>70% (0.7)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>n8n_webhook_url</TableCell>
                  <TableCell>n8n Webhook-URL für dieses Modell</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>-</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>n8n_enabled</TableCell>
                  <TableCell>n8n-Integration aktiviert</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>true</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>n8n_send_mode</TableCell>
                  <TableCell>Welche Vorhersagen gesendet werden</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>["all"]</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>coin_filter_mode</TableCell>
                  <TableCell>Coin-Filter-Modus</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>"all"</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>phases</TableCell>
                  <TableCell>Erlaubte Coin-Phasen (Array)</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>null (alle)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>ignore_bad_seconds</TableCell>
                  <TableCell>Ignoriere Coin nach negativer Vorhersage</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>0</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>ignore_positive_seconds</TableCell>
                  <TableCell>Ignoriere Coin nach positiver Vorhersage</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>0</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>ignore_alert_seconds</TableCell>
                  <TableCell>Ignoriere Coin nach Alert</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>0</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>
        </Chapter>

        {/* ===== KAPITEL 10: Filter & Suche ===== */}
        <Chapter
          id="chapter-filters"
          title="Filter & Suche"
          icon="🔍"
          expanded={expandedChapters.includes('chapter-filters')}
          onChange={handleChapterChange('chapter-filters')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Alert-Logs Filter
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Filter</strong></TableCell>
                  <TableCell><strong>Parameter</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><strong>Beschreibung</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell><code>status</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>pending, success, failed, expired</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Vorhersage-Status</TableCell>
                  <TableCell><code>predictionStatus</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>negativ, positiv, alert</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Coin-ID</TableCell>
                  <TableCell><code>coin_id</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Filter nach spezifischer Coin-ID</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Von Datum</TableCell>
                  <TableCell><code>date_from</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>ISO-Format: 2026-01-13T00:00:00Z</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Bis Datum</TableCell>
                  <TableCell><code>date_to</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>ISO-Format: 2026-01-13T23:59:59Z</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Vorhersagen Filter
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Filter</strong></TableCell>
                  <TableCell><strong>Parameter</strong></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><strong>Beschreibung</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Coin-ID</TableCell>
                  <TableCell><code>coin_id</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Filter nach Coin</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Modell-ID</TableCell>
                  <TableCell><code>model_id</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Filter nach Modell</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Min. Wahrscheinlichkeit</TableCell>
                  <TableCell><code>min_probability</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>0.0 - 1.0</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Max. Wahrscheinlichkeit</TableCell>
                  <TableCell><code>max_probability</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>0.0 - 1.0</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Phase</TableCell>
                  <TableCell><code>phase_id</code></TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>1-6 (Coin-Phase)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>
        </Chapter>

        {/* ===== KAPITEL 11: Technische Details ===== */}
        <Chapter
          id="chapter-technical"
          title="Technische Details"
          icon="🔧"
          expanded={expandedChapters.includes('chapter-technical')}
          onChange={handleChapterChange('chapter-technical')}
        >
          <Typography variant="h6" sx={{ mt: 2, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Architektur
          </Typography>
          <List dense={isMobile}>
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
                secondary="Scikit-learn, XGBoost"
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Deployment"
                secondary="Docker Compose (Frontend + Backend)"
              />
            </ListItem>
          </List>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Datenbank-Tabellen
          </Typography>
          <ResponsiveTable>
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
                  <TableCell>Importierte Modelle mit Konfiguration</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>model_predictions</code></TableCell>
                  <TableCell>Alle Vorhersagen mit Tag, Status, Auswertungsergebnissen</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>coin_scan_cache</code></TableCell>
                  <TableCell>Cache für Coin-Ignore-System</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>coin_metrics</code></TableCell>
                  <TableCell>Coin-Daten (extern, wird vom Training Service befüllt)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Ports & Zugriff
          </Typography>
          <ResponsiveTable>
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
          </ResponsiveTable>
        </Chapter>

        {/* ===== KAPITEL 12: MCP Server ===== */}
        <Chapter
          id="chapter-mcp"
          title="MCP Server (KI-Integration)"
          icon="🤖"
          expanded={expandedChapters.includes('chapter-mcp')}
          onChange={handleChapterChange('chapter-mcp')}
        >
          <Typography variant="body1" sx={{ mb: 2 }}>
            Der Pump Server bietet einen integrierten <strong>MCP Server</strong> (Model Context Protocol),
            der es KI-Clients wie Claude Code ermöglicht, direkt mit dem Service zu interagieren.
            MCP ist ein Protokoll von Anthropic für die standardisierte Tool-Integration in KI-Anwendungen.
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Verfügbare Endpoints
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Endpoint</strong></TableCell>
                  <TableCell><strong>Methode</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>/mcp/info</code></TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell>Server-Informationen und Tool-Liste</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>/mcp/sse</code></TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell>SSE-Stream für Echtzeit-Kommunikation</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>/mcp/messages/</code></TableCell>
                  <TableCell><Chip label="POST" size="small" color="success" /></TableCell>
                  <TableCell>JSON-RPC Messages an den Server (mit session_id Parameter)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>/mcp/health</code></TableCell>
                  <TableCell><Chip label="GET" size="small" color="primary" /></TableCell>
                  <TableCell>MCP Server Health-Status</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Verfügbare Tools (13 insgesamt)
          </Typography>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1, fontWeight: 600, color: '#00d4ff' }}>
            Model-Tools (6)
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Tool</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>list_active_models</code></TableCell>
                  <TableCell>Liste aller aktiven Modelle mit Konfiguration</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>list_available_models</code></TableCell>
                  <TableCell>Verfügbare Modelle vom Training Service</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>import_model</code></TableCell>
                  <TableCell>Modell vom Training Service importieren</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>get_model_details</code></TableCell>
                  <TableCell>Detaillierte Informationen zu einem Modell</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>activate_model</code></TableCell>
                  <TableCell>Pausiertes Modell aktivieren</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>deactivate_model</code></TableCell>
                  <TableCell>Aktives Modell deaktivieren</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1, fontWeight: 600, color: '#00d4ff' }}>
            Prediction-Tools (3)
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Tool</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>predict_coin</code></TableCell>
                  <TableCell>ML-Vorhersage für einen spezifischen Coin</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>get_predictions</code></TableCell>
                  <TableCell>Historische Vorhersagen mit Filtern abrufen</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>get_latest_prediction</code></TableCell>
                  <TableCell>Neueste Vorhersage für einen Coin</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1, fontWeight: 600, color: '#00d4ff' }}>
            Config-Tools (2)
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Tool</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>update_alert_config</code></TableCell>
                  <TableCell>Alert-Konfiguration eines Modells ändern</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>get_model_statistics</code></TableCell>
                  <TableCell>Performance-Statistiken eines Modells</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1, fontWeight: 600, color: '#00d4ff' }}>
            System-Tools (2)
          </Typography>
          <ResponsiveTable>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Tool</strong></TableCell>
                  <TableCell><strong>Beschreibung</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>health_check</code></TableCell>
                  <TableCell>Service Health-Status prüfen</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>get_stats</code></TableCell>
                  <TableCell>Umfassende Service-Statistiken</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </ResponsiveTable>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Claude Code Konfiguration
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Um den MCP Server mit Claude Code zu verwenden, füge folgende Konfiguration zur Datei{' '}
            <code>~/.claude/mcp_servers.json</code> hinzu:
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2, mb: 3, fontFamily: 'monospace', fontSize: { xs: '0.7rem', sm: '0.8rem' }, overflowX: 'auto' }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
{`{
  "mcpServers": {
    "pump-server": {
      "transport": "sse",
      "url": "http://localhost:3003/mcp/sse"
    }
  }
}`}
            </pre>
          </Box>

          <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem' } }}>
            Setup-Anleitung
          </Typography>
          <List dense={isMobile}>
            <ListItem>
              <ListItemText
                primary="1. Service starten"
                secondary="docker-compose up -d"
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="2. Verbindung testen"
                secondary="curl http://localhost:3003/mcp/info"
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="3. MCP-Config erstellen"
                secondary="Konfiguration oben nach ~/.claude/mcp_servers.json kopieren"
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="4. Claude Code neustarten"
                secondary="Damit die neue MCP-Konfiguration geladen wird"
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="5. Tools verwenden"
                secondary='Beispiel: "Liste alle aktiven Modelle" in Claude Code'
              />
            </ListItem>
          </List>

          <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(0, 212, 255, 0.1)', borderRadius: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
              Technische Details
            </Typography>
            <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              Transport: SSE (Server-Sent Events) | Protokoll: JSON-RPC 2.0 | Port: 3003 (via Nginx Proxy)
            </Typography>
          </Box>
        </Chapter>

        {/* Footer */}
        <Box sx={{ mt: 4, p: 3, textAlign: 'center', color: 'text.secondary' }}>
          <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
            System läuft seit Start | Dokumentation Stand: Januar 2026
          </Typography>
          <Typography variant="body2" sx={{ mt: 1, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
            Wichtig: Alle Konfigurationen sind persistent und überleben Container-Neustarts
          </Typography>
        </Box>
      </Box>
    </PageContainer>
  );
};

export default Info;
