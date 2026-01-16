# Schritt-für-Schritt Plan: Flag-Features Filterung Fix

## Problem
Wenn nur ein Teil der Engineering-Features ausgewählt wird (z.B. 3 von 66), werden trotzdem ALLE 57 Flag-Features verwendet statt nur die 3 benötigten.

## Root Cause Analyse
1. `original_features_before_engineering` wird in Zeile 247 gespeichert
2. `selected_engineered_original` wird aus `original_features_before_engineering` berechnet (Zeile 411)
3. ABER: Die Logs zeigen, dass `selected_engineered_original` 66 Features enthält, nicht 3
4. Das bedeutet: `original_features_before_engineering` enthält bereits alle Engineering-Features

**Das Problem:** Die `features` Liste wird irgendwo erweitert, BEVOR sie in `train_model_sync` ankommt, oder `original_features_before_engineering` wird falsch berechnet.

## Lösung: Schritt-für-Schritt Plan

### Phase 1: Backup & Vorbereitung
1. ✅ Git Commit mit aktuellen Änderungen
2. ✅ Backup der aktuellen `engine.py`
3. ✅ Test-Script erstellen, um vor/nach zu vergleichen

### Phase 2: Root Cause Identifikation
1. Debug-Logs hinzufügen, um zu sehen, was in `original_features_before_engineering` steht
2. Prüfen, ob `features` irgendwo erweitert wird, BEVOR es in `train_model_sync` ankommt
3. Prüfen, ob `selected_engineered_original` korrekt berechnet wird

### Phase 3: Fix Implementierung
1. **Fix 1:** Stelle sicher, dass `original_features_before_engineering` wirklich die ursprüngliche Liste enthält
2. **Fix 2:** Berechne `selected_engineered_original` korrekt aus der ursprünglichen Liste
3. **Fix 3:** Filtere `original_selected_flags` korrekt (nur für `selected_engineered_original`)
4. **Fix 4:** Stelle sicher, dass `features_to_use` nur die richtigen Flag-Features enthält
5. **Fix 5:** Filtere `available_features` am Ende, um sicherzustellen, dass nur die richtigen Flag-Features verwendet werden

### Phase 4: Testing
1. Test 1: Modell mit 3 ausgewählten Engineering-Features erstellen
2. Test 2: Prüfen, ob nur 3 Flag-Features verwendet werden
3. Test 3: Prüfen, ob Modell korrekt trainiert wird
4. Test 4: Prüfen, ob Modell mit ALLEN Engineering-Features noch funktioniert
5. Test 5: Prüfen, ob Modell OHNE Engineering-Features noch funktioniert

### Phase 5: Cleanup
1. Debug-Logs entfernen
2. Code aufräumen
3. Finale Tests
4. Git Commit

## Risiko-Minimierung
- Jeder Schritt wird einzeln getestet
- Nach jedem Schritt wird ein Test durchgeführt
- Bei Problemen: Sofortiger Rollback
- Backup vorhanden für jeden Schritt

