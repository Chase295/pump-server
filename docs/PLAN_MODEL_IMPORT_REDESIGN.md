# Plan: Model-Import Seite Redesign

## Ziel
Die Model-Import Seite (`ModelImport.tsx`) soll von der aktuellen Tabellenansicht auf eine **Kachel-Ansicht (Card-Grid)** umgestellt werden, ähnlich der Übersichtsseite (`Overview.tsx`), jedoch nur mit den relevanten Modell-Informationen (ohne Statistiken/Performance-Daten).

## Aktueller Stand

### Overview.tsx (Aktive Modelle)
- Grid-Layout mit `ModelCard` Komponenten
- Responsive: 1 Spalte (xs), 2 Spalten (sm), 3 Spalten (lg)
- Jede Kachel zeigt:
  - Modell-Name, ID, Typ-Badge
  - Status (Aktiv/Inaktiv)
  - Basis-Statistiken (Vorhersagen, Wahrscheinlichkeit, Alerts)
  - Alert-Performance
  - Action-Buttons (Details, Alert, Logs, Aktivieren/Deaktivieren, Löschen)

### ModelImport.tsx (Verfügbare Modelle)
- Tabellen-Layout mit `<Table>` Komponente
- Zeigt: Name, Typ, Accuracy, F1, Features, Ziel, Aktionen
- Nicht responsive (Tabelle scrollt auf Mobile)
- Action-Buttons: Details, Importieren

## Geplante Änderungen

### 1. Neue Komponente: `AvailableModelCard.tsx`

**Pfad:** `frontend/src/components/models/AvailableModelCard.tsx`

**Inhalt der Kachel:**
```
┌────────────────────────────────────────────────────┐
│ [Icon] Model Name                    [Status-Chip] │
│         Typ-Badge  ID: 123                         │
├────────────────────────────────────────────────────┤
│ 📊 Training-Metriken                               │
│ ┌──────────────┐  ┌──────────────┐                │
│ │  [Icon]      │  │  [Icon]      │                │
│ │  87.5%       │  │  82.3%       │                │
│ │  Accuracy    │  │  F1-Score    │                │
│ └──────────────┘  └──────────────┘                │
│                                                    │
│ ┌──────────────┐  ┌──────────────┐                │
│ │  [Icon]      │  │  [Icon]      │                │
│ │  78.2%       │  │  74.1%       │                │
│ │  Precision   │  │  Recall      │                │
│ └──────────────┘  └──────────────┘                │
├────────────────────────────────────────────────────┤
│ 🎯 Ziel-Konfiguration                              │
│ ┌──────────────┐  ┌──────────────┐                │
│ │  UP 5%       │  │  15 min      │                │
│ │  Richtung    │  │  Zeitfenster │                │
│ └──────────────┘  └──────────────┘                │
├────────────────────────────────────────────────────┤
│ 📋 Features: 25 Features                           │
│ Phasen: Phase 1, 2, 3                             │
├────────────────────────────────────────────────────┤
│ [Details]                    [✅ Importieren]     │
│                      oder    [⚠️ Bereits importiert] │
└────────────────────────────────────────────────────┘
```

**Props:**
```typescript
interface AvailableModelCardProps {
  model: AvailableModel;
  onDetailsClick: (modelId: number) => void;
  onImportClick: (model: AvailableModel) => void;
  isAlreadyImported: boolean;
  isImporting: boolean;
}
```

### 2. Anpassung ModelImport.tsx

**Änderungen:**
1. Import von `AvailableModelCard` statt Table-Komponenten
2. Grid-Layout wie in Overview.tsx
3. Statistik-Chips im Header (Gesamt, Bereit, Bereits importiert)
4. Responsive Spalten

**Neues Layout:**
```tsx
<Box
  sx={{
    display: 'grid',
    gridTemplateColumns: {
      xs: '1fr',           // Mobile: 1 Spalte
      sm: 'repeat(2, 1fr)', // Tablet: 2 Spalten
      lg: 'repeat(3, 1fr)'  // Desktop: 3 Spalten
    },
    gap: 3
  }}
>
  {readyModels.map((model) => (
    <AvailableModelCard
      key={model.id}
      model={model}
      onDetailsClick={handleDetailsClick}
      onImportClick={handleImportClick}
      isAlreadyImported={isAlreadyImported(model.id)}
      isImporting={importMutation.isPending && selectedModel?.id === model.id}
    />
  ))}
</Box>
```

### 3. Styling (konsistent mit ModelCard)

- Gleiche Card-Höhe und Padding
- Gleiche Hover-Effekte (translateY, boxShadow)
- Gleiche Farbgebung (cyan Akzente)
- Gleiche Icon-Boxen (32x32px, borderRadius 1.5)
- Gleiche Typografie-Stile

### 4. Mobile-Optimierungen

- **Touch-friendly**: Buttons mindestens 44px hoch
- **Lesbarkeit**: Ausreichende Schriftgrößen (min 14px)
- **Spacing**: Genug Abstand zwischen Elementen
- **Overflow**: Text-Ellipsis für lange Namen
- **Breakpoints**:
  - `xs` (0-600px): 1 Spalte, kompaktere Kacheln
  - `sm` (600-900px): 2 Spalten
  - `md` (900-1200px): 2-3 Spalten
  - `lg` (1200px+): 3 Spalten

## Implementierungs-Schritte

### Phase 1: AvailableModelCard Komponente erstellen
1. Neue Datei `frontend/src/components/models/AvailableModelCard.tsx`
2. Basis-Struktur von ModelCard übernehmen
3. Anpassen für verfügbare Modelle (ohne Runtime-Stats)
4. Training-Metriken anzeigen (Accuracy, F1, Precision, Recall)
5. Ziel-Konfiguration anzeigen (Richtung, Zeitfenster)
6. Action-Buttons: Details + Importieren

### Phase 2: ModelImport.tsx umbauen
1. Table-Import entfernen
2. AvailableModelCard importieren
3. Grid-Layout implementieren
4. Event-Handler anpassen
5. Import-Dialog beibehalten

### Phase 3: Responsive Testing
1. Chrome DevTools - Mobile Ansicht testen
2. Breakpoints überprüfen
3. Touch-Interaktionen testen
4. Text-Overflow prüfen

### Phase 4: Feinschliff
1. Animationen hinzufügen (Einblenden der Kacheln)
2. Loading-States für einzelne Kacheln
3. Empty-State verbessern
4. Bereits importierte Modelle visuell markieren

## Dateien die geändert werden

| Datei | Aktion |
|-------|--------|
| `frontend/src/components/models/AvailableModelCard.tsx` | **NEU** |
| `frontend/src/components/models/index.ts` | Export hinzufügen |
| `frontend/src/pages/ModelImport.tsx` | Umbauen |

## Zeitschätzung

- Phase 1: ~30 min
- Phase 2: ~20 min
- Phase 3: ~15 min
- Phase 4: ~15 min
- **Gesamt: ~80 min**

## Vorschau der Kachel-Daten

Aus der API (`/api/models/available`) kommen diese Felder:
```typescript
interface AvailableModel {
  id: number;
  name: string;
  model_type: string;           // "random_forest", "xgboost"
  target_variable: string;
  target_operator?: string;
  target_value?: number;
  future_minutes: number;       // z.B. 15
  price_change_percent: number; // z.B. 5
  target_direction: string;     // "up", "down"
  features: string[];           // Array der Feature-Namen
  phases?: number[];            // z.B. [1, 2, 3]
  training_accuracy?: number;   // z.B. 0.875
  training_f1?: number;         // z.B. 0.823
  training_precision?: number;  // z.B. 0.782 (falls vorhanden)
  training_recall?: number;     // z.B. 0.741 (falls vorhanden)
  created_at: string;
}
```

## Visueller Vergleich

### Vorher (Tabelle):
```
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ Name     │ Typ      │ Accuracy │ F1       │ Features │ Ziel     │ Aktion   │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Model 1  │ XGBoost  │ 87.5%    │ 82.3%    │ 25       │ UP 5%    │ [Import] │
│ Model 2  │ RF       │ 85.2%    │ 80.1%    │ 30       │ DOWN 3%  │ [Import] │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### Nachher (Kacheln):
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ 🧠 Model 1      │  │ 🧠 Model 2      │  │ 🧠 Model 3      │
│ XGB  ID: 1      │  │ RF   ID: 2      │  │ XGB  ID: 3      │
│                 │  │                 │  │                 │
│ 📊 Training     │  │ 📊 Training     │  │ 📊 Training     │
│ 87.5% Acc       │  │ 85.2% Acc       │  │ 89.1% Acc       │
│ 82.3% F1        │  │ 80.1% F1        │  │ 84.5% F1        │
│                 │  │                 │  │                 │
│ 🎯 UP 5% 15min  │  │ 🎯 DOWN 3% 10m  │  │ 🎯 UP 10% 30m   │
│                 │  │                 │  │                 │
│ [Details]       │  │ [Details]       │  │ [Details]       │
│ [✅ Importieren]│  │ [⚠️ Importiert] │  │ [✅ Importieren]│
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Fragen zur Klärung

1. **Sollen bereits importierte Modelle ausgeblendet oder nur markiert werden?**
   - Aktuell: Werden angezeigt mit deaktiviertem Button
   - Option: Komplett ausblenden mit Filter-Toggle

2. **Soll die Detail-Seite (`/model-import/:id`) auch angepasst werden?**
   - Aktuell: Separate Detail-Ansicht
   - Option: Modal statt Navigation

3. **Farbschema für Import-Status:**
   - Bereit: Grün (success)
   - Bereits importiert: Grau (default)
   - Import läuft: Blau (info) mit Spinner
