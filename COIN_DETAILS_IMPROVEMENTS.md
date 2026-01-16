# 💡 Coin-Details Feature - Fragen & Verbesserungen

## ✅ **Gute Nachrichten:**
- **Recharts ist bereits installiert!** (`recharts: ^3.6.0`) - Wir können es direkt verwenden
- Recharts wird bereits in `PredictionsTab.tsx` verwendet - Konsistenz gewährleistet
- Keine zusätzlichen Dependencies nötig

---

## ❓ **Wichtige Fragen:**

### **1. Grafik-Library Entscheidung**
**Status:** ✅ **Recharts** (bereits vorhanden)

**Vorteile:**
- ✅ Bereits installiert
- ✅ Konsistent mit bestehender App
- ✅ Leichtgewichtig
- ✅ Gute Performance

**Nachteil:**
- ⚠️ Keine Candlestick-Charts out-of-the-box (müssen wir selbst bauen oder Line-Chart verwenden)

**Empfehlung:** 
- **Line-Chart** für Preis-Kurve (einfacher, schneller)
- Oder **Custom Candlestick** mit Recharts (aufwendiger, aber professioneller)

**Frage:** Bevorzugst du Line-Chart oder Candlestick?

---

### **2. Marker-Interaktivität**
**Frage:** Sollen die Marker in der Grafik interaktiv sein?

**Optionen:**
- **A) Tooltips:** Beim Hover über Marker → Details anzeigen (Wahrscheinlichkeit, Status, etc.)
- **B) Klickbar:** Klick auf Marker → Scroll zu Details oder Modal öffnen
- **C) Beides:** Tooltip + Klickbar

**Empfehlung:** **Option A (Tooltips)** - Einfach, benutzerfreundlich, keine zusätzliche Komplexität

---

### **3. Daten-Limit & Performance**
**Frage:** Wie viele Datenpunkte erwarten wir maximal?

**Szenarien:**
- **15 Minuten:** ~15-30 Datenpunkte (wenn alle 30s ein Eintrag)
- **24 Stunden:** ~2880 Datenpunkte (wenn alle 30s ein Eintrag)

**Problem:** Bei 24h könnte die Grafik langsam werden

**Lösungsvorschläge:**
1. **Sampling:** Bei >1000 Datenpunkten → Jeden N-ten Punkt nehmen
2. **Pagination:** Preis-Historie in Chunks laden
3. **Aggregation:** Stundenweise/Durchschnittswerte für lange Zeitfenster

**Empfehlung:** **Sampling** - Automatisch bei >1000 Datenpunkten

---

### **4. Zeitfenster-Berechnung**
**Frage:** Ab welchem Zeitpunkt soll die Grafik starten?

**Optionen:**
- **A) Ab erster Vorhersage:** Start = `prediction_timestamp` der ersten Vorhersage
- **B) Ab Alert-Timestamp:** Start = `alert_timestamp` des ersten Alerts
- **C) Konfigurierbar:** User kann Start-Zeitpunkt wählen

**Empfehlung:** **Option A** - Ab erster Vorhersage (logisch, da das der "Startpunkt" ist)

**Zusätzlich:** 
- **Vorherige Daten:** Optional 5-10 Minuten VOR der ersten Vorhersage anzeigen (Kontext)

---

### **5. Marker-Größe & Styling**
**Frage:** Sollen Marker unterschiedliche Größen haben?

**Optionen:**
- **A) Feste Größe:** Alle Marker gleich groß
- **B) Wahrscheinlichkeits-basiert:** Größere Marker = höhere Wahrscheinlichkeit
- **C) Alert-basiert:** Alerts größer als normale Vorhersagen

**Empfehlung:** **Option C** - Alerts größer (visuell hervorgehoben)

**Farben:**
- **Vorhersagen (Alert):** Orange (`#ff9800`) - Größe: 10px
- **Vorhersagen (Normal):** Blau (`#2196f3`) - Größe: 8px
- **Auswertungen (Success):** Grün (`#4caf50`) - Größe: 8px
- **Auswertungen (Failed):** Rot (`#f44336`) - Größe: 8px
- **Auswertungen (Pending):** Gelb (`#ff9800`) - Größe: 6px (gestrichelt)

---

### **6. Zusätzliche Features (Optional)**
**Frage:** Welche Features sind wichtig?

#### **A) Export-Funktion**
- **PNG-Export:** Grafik als Bild speichern
- **CSV-Export:** Preis-Daten als CSV exportieren

**Aufwand:** Mittel (2-3 Stunden)

#### **B) Vergleichsfunktion**
- Mehrere Coins gleichzeitig in einer Grafik anzeigen
- Vergleich der Performance

**Aufwand:** Hoch (4-6 Stunden)

#### **C) Zoom & Pan**
- Interaktives Zoomen in der Grafik
- Pan (Verschieben) für lange Zeitfenster

**Aufwand:** Niedrig (Recharts unterstützt das out-of-the-box)

**Empfehlung:** **Zoom & Pan** - Einfach, sehr nützlich

#### **D) Live-Updates**
- Automatische Aktualisierung der Grafik alle X Sekunden
- Neue Datenpunkte werden automatisch hinzugefügt

**Aufwand:** Niedrig (React Query `refetchInterval`)

**Empfehlung:** **Live-Updates** - Sehr nützlich für aktive Coins

#### **E) Statistiken-Panel**
- Erweiterte Statistiken:
  - Min/Max Preis
  - Durchschnittspreis
  - Volatilität
  - Beste/Schlechteste Vorhersage

**Aufwand:** Niedrig (1-2 Stunden)

**Empfehlung:** **Statistiken-Panel** - Guter Überblick

---

### **7. Navigation & UX**
**Frage:** Wie soll die Navigation funktionieren?

**Aktuell geplant:**
- Klick auf Coin-ID in ModelLogs → Coin-Details-Seite

**Zusätzliche Features:**
- **Zurück-Button:** Zurück zu ModelLogs
- **Breadcrumbs:** Übersicht → Modell → Logs → Coin (bereits geplant)
- **Quick-Links:** Direkt zu anderen Coins springen (Dropdown)

**Empfehlung:** Alle drei Features implementieren

---

### **8. Mobile-Responsiveness**
**Frage:** Wie wichtig ist Mobile-Ansicht?

**Überlegungen:**
- Grafik auf Mobile: Kann schwierig sein (Touch-Zoom nötig)
- Zeitfenster-Auswahl: Dropdown statt Select (besser für Mobile)

**Empfehlung:** 
- **Desktop-first:** Optimiert für Desktop
- **Mobile:** Grundfunktionalität, aber Grafik kann eingeschränkt sein

---

### **9. Fehlerbehandlung**
**Fragen:**
- Was passiert, wenn keine Preis-Daten vorhanden sind?
- Was passiert, wenn keine Vorhersagen vorhanden sind?
- Was passiert, wenn Coin-ID nicht existiert?

**Empfehlung:**
- **Freundliche Fehlermeldungen** mit Alternativen
- **Fallback:** Zeige zumindest Vorhersagen/Auswertungen ohne Grafik

---

### **10. Performance-Optimierung**
**Fragen:**
- Soll die Grafik lazy-loaded sein?
- Soll die Preis-Historie paginiert werden?
- Soll es Debouncing für Zeitfenster-Änderung geben?

**Empfehlung:**
- ✅ **Lazy Loading:** Ja (Grafik-Komponente)
- ✅ **Debouncing:** Ja (300ms für Zeitfenster-Änderung)
- ⚠️ **Pagination:** Nur wenn Performance-Probleme auftreten

---

## 🎨 **Design-Verbesserungen:**

### **1. Grafik-Layout**
**Vorschlag:**
- **Haupt-Grafik:** Preis-Kurve (Line-Chart) mit Marker
- **Unter-Grafik (optional):** Volume-Chart (separat, kleiner)

### **2. Marker-Legende**
**Vorschlag:**
- Legende oben rechts in der Grafik
- Interaktiv: Klick auf Legende → Marker ein/ausblenden

### **3. Zeitfenster-Visualisierung**
**Vorschlag:**
- **Zeitfenster-Balken:** Unter der Grafik, zeigt aktuelles Zeitfenster
- **Zoom-Buttons:** "+" und "-" für schnelles Zoomen

### **4. Info-Karten Design**
**Vorschlag:**
- **Kompakte Karten:** 3 Spalten auf Desktop, 1 Spalte auf Mobile
- **Icons:** Visuelle Icons für bessere Erkennbarkeit
- **Hover-Effekte:** Leichte Animation beim Hover

---

## 🚀 **Empfohlene Implementierungs-Reihenfolge (Erweitert):**

### **MVP (Minimum Viable Product):**
1. ✅ Backend API
2. ✅ Frontend Routing
3. ✅ CoinDetails Grundstruktur
4. ✅ Line-Chart mit Marker (Recharts)
5. ✅ Zeitfenster-Einstellung
6. ✅ Info-Karten

### **Phase 2 (Quick Wins):**
7. ✅ Tooltips für Marker
8. ✅ Zoom & Pan (Recharts)
9. ✅ Live-Updates (30s Refresh)
10. ✅ Statistiken-Panel

### **Phase 3 (Nice-to-Have):**
11. ⚠️ Export-Funktion (PNG/CSV)
12. ⚠️ Marker-Legende (interaktiv)
13. ⚠️ Zeitfenster-Visualisierung
14. ⚠️ Quick-Links zu anderen Coins

### **Phase 4 (Future):**
15. ⚠️ Vergleichsfunktion (mehrere Coins)
16. ⚠️ Candlestick-Chart (Custom)
17. ⚠️ Volume-Chart (separat)

---

## 📝 **Konkrete Entscheidungen:**

### **Ich empfehle folgende Konfiguration:**

1. **Grafik:** Line-Chart (Recharts) - Einfach, schnell, konsistent
2. **Marker:** Tooltips + Feste Größe (Alerts größer)
3. **Daten-Limit:** Sampling bei >1000 Datenpunkten
4. **Zeitfenster:** Ab erster Vorhersage + 5 Min vorher (Kontext)
5. **Features MVP:** Basis-Funktionalität + Zoom & Pan + Live-Updates
6. **Export:** Später (Phase 3)
7. **Mobile:** Desktop-first, Mobile funktional

---

## ❓ **Deine Entscheidungen:**

Bitte beantworte folgende Fragen:

1. **Grafik-Typ:** Line-Chart oder Candlestick?
2. **Marker-Interaktivität:** Tooltips, Klickbar, oder beides?
3. **Zeitfenster-Start:** Ab erster Vorhersage oder konfigurierbar?
4. **Zusätzliche Features:** Welche sind wichtig? (Export, Vergleich, etc.)
5. **Mobile:** Wie wichtig ist Mobile-Optimierung?

**Oder:** Soll ich mit den empfohlenen Einstellungen starten? 🚀
