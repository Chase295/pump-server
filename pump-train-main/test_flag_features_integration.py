#!/usr/bin/env python3
"""
Vollständiger Integrationstest für Flag-Features
Testet alle kritischen Punkte der Flag-Features Integration
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
import sys
import time

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"  # Externe API
DB_URL = "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta"

# Test-Ergebnisse
test_results = []

def log_test(name: str, passed: bool, message: str = ""):
    """Loggt ein Test-Ergebnis"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"      → {message}")
    test_results.append({"name": name, "passed": passed, "message": message})

def print_section(title: str):
    """Druckt eine Sektion-Überschrift"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============================================================
# TEST 1: API Features Endpoint
# ============================================================
def test_features_endpoint():
    print_section("TEST 1: API Features Endpoint")
    
    try:
        # Test 1.1: Mit Flag-Features (Standard)
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            base_count = data.get('base_count', 0)
            engineered_count = data.get('engineered_count', 0)
            flag_count = data.get('flag_count', 0)
            total = data.get('total', 0)
            
            log_test(
                "GET /api/features?include_flags=true",
                True,
                f"Base: {base_count}, Engineering: {engineered_count}, Flags: {flag_count}, Total: {total}"
            )
            
            # Prüfe ob Flag-Features vorhanden sind
            if flag_count > 0:
                log_test("Flag-Features in Response", True, f"{flag_count} Flag-Features gefunden")
            else:
                log_test("Flag-Features in Response", False, "Keine Flag-Features gefunden!")
        else:
            log_test("GET /api/features?include_flags=true", False, f"Status: {response.status_code}")
        
        # Test 1.2: Ohne Flag-Features
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=false", timeout=10)
        if response.status_code == 200:
            data = response.json()
            flag_count = data.get('flag_count', 0)
            
            if flag_count == 0:
                log_test("GET /api/features?include_flags=false", True, "Keine Flag-Features zurückgegeben")
            else:
                log_test("GET /api/features?include_flags=false", False, f"Flag-Features sollten 0 sein, aber: {flag_count}")
        else:
            log_test("GET /api/features?include_flags=false", False, f"Status: {response.status_code}")
            
    except Exception as e:
        log_test("Features Endpoint", False, f"Exception: {str(e)}")

# ============================================================
# TEST 2: Modell mit Flag-Features erstellen
# ============================================================
def test_create_model_with_flags():
    print_section("TEST 2: Modell mit Flag-Features erstellen")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_FLAG_FEATURES_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol,buy_pressure_ratio",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "true",
            "use_flag_features": "true",  # WICHTIG: Flag-Features aktivieren
            "scale_pos_weight": "100"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell mit Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)
# ============================================================
def test_create_model_without_flags():
    print_section("TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_NO_FLAGS_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "false",
            "use_flag_features": "false",  # WICHTIG: Flag-Features deaktivieren
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell ohne Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 4: Datenbank prüfen
# ============================================================
async def test_database_storage():
    print_section("TEST 4: Datenbank prüfen (use_flag_features gespeichert)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Test 4.1: Prüfe ob Spalte existiert
        column_exists = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists:
            log_test("ml_models.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_models.use_flag_features Spalte existiert", False, "Spalte fehlt!")
            await conn.close()
            return
        
        # Test 4.2: Prüfe neueste Modelle
        recent_models = await conn.fetch("""
            SELECT id, name, use_flag_features, params
            FROM ml_models
            WHERE name LIKE 'TEST_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_models:
            log_test("Neueste Test-Modelle gefunden", True, f"{len(recent_models)} Modelle")
            for model in recent_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                params = model['params']
                
                # Prüfe ob use_flag_features in params auch gespeichert ist
                params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
                flags_in_params = params_dict.get('use_flag_features', None)
                
                log_test(
                    f"Modell {model_id} ({model_name})",
                    use_flags is not None,
                    f"use_flag_features={use_flags}, in params={flags_in_params}"
                )
        else:
            log_test("Neueste Test-Modelle gefunden", False, "Keine Test-Modelle gefunden")
        
        # Test 4.3: Prüfe ml_jobs
        column_exists_jobs = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_jobs' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists_jobs:
            log_test("ml_jobs.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_jobs.use_flag_features Spalte existiert", False, "Spalte fehlt!")
        
        await conn.close()
        
    except Exception as e:
        log_test("Datenbank prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 5: Warte auf Job-Abschluss und prüfe Modell
# ============================================================
async def test_wait_for_job_and_check_model(job_id: int, expected_flags: bool):
    print_section(f"TEST 5: Warte auf Job {job_id} (erwartet Flag-Features: {expected_flags})")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        max_wait = 300  # 5 Minuten
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await conn.fetchrow("""
                SELECT id, status, result_model_id, use_flag_features
                FROM ml_jobs
                WHERE id = $1
            """, job_id)
            
            if not job:
                log_test(f"Job {job_id} gefunden", False, "Job nicht in Datenbank")
                await conn.close()
                return None
            
            status = job['status']
            
            if status == 'COMPLETED':
                model_id = job['result_model_id']
                job_use_flags = job['use_flag_features']
                
                log_test(
                    f"Job {job_id} abgeschlossen",
                    True,
                    f"Status: {status}, Model-ID: {model_id}, use_flag_features: {job_use_flags}"
                )
                
                # Prüfe ob use_flag_features korrekt gespeichert wurde
                if job_use_flags == expected_flags:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        True,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                else:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        False,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                
                await conn.close()
                return model_id
                
            elif status == 'FAILED':
                error_msg = await conn.fetchval("""
                    SELECT error_msg FROM ml_jobs WHERE id = $1
                """, job_id)
                log_test(
                    f"Job {job_id} Status",
                    False,
                    f"Job fehlgeschlagen: {error_msg}"
                )
                await conn.close()
                return None
            
            # Warte 5 Sekunden
            await asyncio.sleep(5)
            print(f"      ⏳ Warte auf Job-Abschluss... (Status: {status})")
        
        log_test(f"Job {job_id} Timeout", False, f"Job nicht innerhalb von {max_wait}s abgeschlossen")
        await conn.close()
        return None
        
    except Exception as e:
        log_test(f"Job {job_id} prüfen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 6: Prüfe Modell-Details
# ============================================================
async def test_model_details(model_id: int, expected_flags: bool):
    print_section(f"TEST 6: Prüfe Modell {model_id} Details")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        model = await conn.fetchrow("""
            SELECT id, name, use_flag_features, params, features
            FROM ml_models
            WHERE id = $1
        """, model_id)
        
        if not model:
            log_test(f"Modell {model_id} gefunden", False, "Modell nicht in Datenbank")
            await conn.close()
            return
        
        model_use_flags = model['use_flag_features']
        params = model['params']
        features = model['features']
        
        # Prüfe use_flag_features Spalte
        if model_use_flags == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        
        # Prüfe params
        params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
        flags_in_params = params_dict.get('use_flag_features', None)
        
        if flags_in_params == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        
        # Prüfe Features (Flag-Features sollten enthalten sein wenn aktiviert)
        if expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if flag_features:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    True,
                    f"{len(flag_features)} Flag-Features gefunden"
                )
            else:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    False,
                    "Keine Flag-Features in Features-Liste gefunden"
                )
        elif not expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if not flag_features:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    True,
                    "Keine Flag-Features gefunden (wie erwartet)"
                )
            else:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    False,
                    f"{len(flag_features)} Flag-Features gefunden (sollten nicht vorhanden sein)"
                )
        
        await conn.close()
        
    except Exception as e:
        log_test(f"Modell {model_id} Details prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)
# ============================================================
async def test_existing_models():
    print_section("TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Hole 5 zufällige bestehende Modelle
        existing_models = await conn.fetch("""
            SELECT id, name, use_flag_features, status
            FROM ml_models
            WHERE name NOT LIKE 'TEST_%'
            AND status = 'READY'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        if existing_models:
            log_test("Bestehende Modelle gefunden", True, f"{len(existing_models)} Modelle")
            
            for model in existing_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                
                # Prüfe ob use_flag_features gesetzt ist (sollte True sein nach Migration)
                if use_flags is not None:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        True,
                        f"use_flag_features={use_flags} (nach Migration sollte True sein)"
                    )
                else:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        False,
                        "use_flag_features ist NULL (sollte nach Migration True sein)"
                    )
        else:
            log_test("Bestehende Modelle gefunden", False, "Keine bestehenden Modelle gefunden")
        
        await conn.close()
        
    except Exception as e:
        log_test("Bestehende Modelle prüfen", False, f"Exception: {str(e)}")

# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "="*60)
    print("  🧪 VOLLSTÄNDIGER INTEGRATIONSTEST: Flag-Features")
    print("="*60 + "\n")
    
    # Test 1: API Features Endpoint
    test_features_endpoint()
    
    # Test 2: Modell mit Flag-Features erstellen
    job_id_with_flags = test_create_model_with_flags()
    
    # Test 3: Modell ohne Flag-Features erstellen
    job_id_without_flags = test_create_model_without_flags()
    
    # Test 4: Datenbank prüfen
    await test_database_storage()
    
    # Test 5: Warte auf Jobs und prüfe Modelle
    if job_id_with_flags:
        model_id_with_flags = await test_wait_for_job_and_check_model(job_id_with_flags, True)
        if model_id_with_flags:
            await test_model_details(model_id_with_flags, True)
    
    if job_id_without_flags:
        model_id_without_flags = await test_wait_for_job_and_check_model(job_id_without_flags, False)
        if model_id_without_flags:
            await test_model_details(model_id_without_flags, False)
    
    # Test 7: Bestehende Modelle prüfen
    await test_existing_models()
    
    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Gesamt: {total_tests} Tests")
    print(f"✅ Bestanden: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FEHLGESCHLAGENE TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
    
    print("\n" + "="*60)
    
    # Exit Code
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())


Vollständiger Integrationstest für Flag-Features
Testet alle kritischen Punkte der Flag-Features Integration
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
import sys
import time

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"  # Externe API
DB_URL = "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta"

# Test-Ergebnisse
test_results = []

def log_test(name: str, passed: bool, message: str = ""):
    """Loggt ein Test-Ergebnis"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"      → {message}")
    test_results.append({"name": name, "passed": passed, "message": message})

def print_section(title: str):
    """Druckt eine Sektion-Überschrift"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============================================================
# TEST 1: API Features Endpoint
# ============================================================
def test_features_endpoint():
    print_section("TEST 1: API Features Endpoint")
    
    try:
        # Test 1.1: Mit Flag-Features (Standard)
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            base_count = data.get('base_count', 0)
            engineered_count = data.get('engineered_count', 0)
            flag_count = data.get('flag_count', 0)
            total = data.get('total', 0)
            
            log_test(
                "GET /api/features?include_flags=true",
                True,
                f"Base: {base_count}, Engineering: {engineered_count}, Flags: {flag_count}, Total: {total}"
            )
            
            # Prüfe ob Flag-Features vorhanden sind
            if flag_count > 0:
                log_test("Flag-Features in Response", True, f"{flag_count} Flag-Features gefunden")
            else:
                log_test("Flag-Features in Response", False, "Keine Flag-Features gefunden!")
        else:
            log_test("GET /api/features?include_flags=true", False, f"Status: {response.status_code}")
        
        # Test 1.2: Ohne Flag-Features
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=false", timeout=10)
        if response.status_code == 200:
            data = response.json()
            flag_count = data.get('flag_count', 0)
            
            if flag_count == 0:
                log_test("GET /api/features?include_flags=false", True, "Keine Flag-Features zurückgegeben")
            else:
                log_test("GET /api/features?include_flags=false", False, f"Flag-Features sollten 0 sein, aber: {flag_count}")
        else:
            log_test("GET /api/features?include_flags=false", False, f"Status: {response.status_code}")
            
    except Exception as e:
        log_test("Features Endpoint", False, f"Exception: {str(e)}")

# ============================================================
# TEST 2: Modell mit Flag-Features erstellen
# ============================================================
def test_create_model_with_flags():
    print_section("TEST 2: Modell mit Flag-Features erstellen")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_FLAG_FEATURES_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol,buy_pressure_ratio",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "true",
            "use_flag_features": "true",  # WICHTIG: Flag-Features aktivieren
            "scale_pos_weight": "100"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell mit Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)
# ============================================================
def test_create_model_without_flags():
    print_section("TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_NO_FLAGS_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "false",
            "use_flag_features": "false",  # WICHTIG: Flag-Features deaktivieren
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell ohne Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 4: Datenbank prüfen
# ============================================================
async def test_database_storage():
    print_section("TEST 4: Datenbank prüfen (use_flag_features gespeichert)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Test 4.1: Prüfe ob Spalte existiert
        column_exists = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists:
            log_test("ml_models.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_models.use_flag_features Spalte existiert", False, "Spalte fehlt!")
            await conn.close()
            return
        
        # Test 4.2: Prüfe neueste Modelle
        recent_models = await conn.fetch("""
            SELECT id, name, use_flag_features, params
            FROM ml_models
            WHERE name LIKE 'TEST_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_models:
            log_test("Neueste Test-Modelle gefunden", True, f"{len(recent_models)} Modelle")
            for model in recent_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                params = model['params']
                
                # Prüfe ob use_flag_features in params auch gespeichert ist
                params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
                flags_in_params = params_dict.get('use_flag_features', None)
                
                log_test(
                    f"Modell {model_id} ({model_name})",
                    use_flags is not None,
                    f"use_flag_features={use_flags}, in params={flags_in_params}"
                )
        else:
            log_test("Neueste Test-Modelle gefunden", False, "Keine Test-Modelle gefunden")
        
        # Test 4.3: Prüfe ml_jobs
        column_exists_jobs = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_jobs' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists_jobs:
            log_test("ml_jobs.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_jobs.use_flag_features Spalte existiert", False, "Spalte fehlt!")
        
        await conn.close()
        
    except Exception as e:
        log_test("Datenbank prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 5: Warte auf Job-Abschluss und prüfe Modell
# ============================================================
async def test_wait_for_job_and_check_model(job_id: int, expected_flags: bool):
    print_section(f"TEST 5: Warte auf Job {job_id} (erwartet Flag-Features: {expected_flags})")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        max_wait = 300  # 5 Minuten
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await conn.fetchrow("""
                SELECT id, status, result_model_id, use_flag_features
                FROM ml_jobs
                WHERE id = $1
            """, job_id)
            
            if not job:
                log_test(f"Job {job_id} gefunden", False, "Job nicht in Datenbank")
                await conn.close()
                return None
            
            status = job['status']
            
            if status == 'COMPLETED':
                model_id = job['result_model_id']
                job_use_flags = job['use_flag_features']
                
                log_test(
                    f"Job {job_id} abgeschlossen",
                    True,
                    f"Status: {status}, Model-ID: {model_id}, use_flag_features: {job_use_flags}"
                )
                
                # Prüfe ob use_flag_features korrekt gespeichert wurde
                if job_use_flags == expected_flags:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        True,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                else:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        False,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                
                await conn.close()
                return model_id
                
            elif status == 'FAILED':
                error_msg = await conn.fetchval("""
                    SELECT error_msg FROM ml_jobs WHERE id = $1
                """, job_id)
                log_test(
                    f"Job {job_id} Status",
                    False,
                    f"Job fehlgeschlagen: {error_msg}"
                )
                await conn.close()
                return None
            
            # Warte 5 Sekunden
            await asyncio.sleep(5)
            print(f"      ⏳ Warte auf Job-Abschluss... (Status: {status})")
        
        log_test(f"Job {job_id} Timeout", False, f"Job nicht innerhalb von {max_wait}s abgeschlossen")
        await conn.close()
        return None
        
    except Exception as e:
        log_test(f"Job {job_id} prüfen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 6: Prüfe Modell-Details
# ============================================================
async def test_model_details(model_id: int, expected_flags: bool):
    print_section(f"TEST 6: Prüfe Modell {model_id} Details")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        model = await conn.fetchrow("""
            SELECT id, name, use_flag_features, params, features
            FROM ml_models
            WHERE id = $1
        """, model_id)
        
        if not model:
            log_test(f"Modell {model_id} gefunden", False, "Modell nicht in Datenbank")
            await conn.close()
            return
        
        model_use_flags = model['use_flag_features']
        params = model['params']
        features = model['features']
        
        # Prüfe use_flag_features Spalte
        if model_use_flags == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        
        # Prüfe params
        params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
        flags_in_params = params_dict.get('use_flag_features', None)
        
        if flags_in_params == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        
        # Prüfe Features (Flag-Features sollten enthalten sein wenn aktiviert)
        if expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if flag_features:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    True,
                    f"{len(flag_features)} Flag-Features gefunden"
                )
            else:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    False,
                    "Keine Flag-Features in Features-Liste gefunden"
                )
        elif not expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if not flag_features:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    True,
                    "Keine Flag-Features gefunden (wie erwartet)"
                )
            else:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    False,
                    f"{len(flag_features)} Flag-Features gefunden (sollten nicht vorhanden sein)"
                )
        
        await conn.close()
        
    except Exception as e:
        log_test(f"Modell {model_id} Details prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)
# ============================================================
async def test_existing_models():
    print_section("TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Hole 5 zufällige bestehende Modelle
        existing_models = await conn.fetch("""
            SELECT id, name, use_flag_features, status
            FROM ml_models
            WHERE name NOT LIKE 'TEST_%'
            AND status = 'READY'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        if existing_models:
            log_test("Bestehende Modelle gefunden", True, f"{len(existing_models)} Modelle")
            
            for model in existing_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                
                # Prüfe ob use_flag_features gesetzt ist (sollte True sein nach Migration)
                if use_flags is not None:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        True,
                        f"use_flag_features={use_flags} (nach Migration sollte True sein)"
                    )
                else:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        False,
                        "use_flag_features ist NULL (sollte nach Migration True sein)"
                    )
        else:
            log_test("Bestehende Modelle gefunden", False, "Keine bestehenden Modelle gefunden")
        
        await conn.close()
        
    except Exception as e:
        log_test("Bestehende Modelle prüfen", False, f"Exception: {str(e)}")

# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "="*60)
    print("  🧪 VOLLSTÄNDIGER INTEGRATIONSTEST: Flag-Features")
    print("="*60 + "\n")
    
    # Test 1: API Features Endpoint
    test_features_endpoint()
    
    # Test 2: Modell mit Flag-Features erstellen
    job_id_with_flags = test_create_model_with_flags()
    
    # Test 3: Modell ohne Flag-Features erstellen
    job_id_without_flags = test_create_model_without_flags()
    
    # Test 4: Datenbank prüfen
    await test_database_storage()
    
    # Test 5: Warte auf Jobs und prüfe Modelle
    if job_id_with_flags:
        model_id_with_flags = await test_wait_for_job_and_check_model(job_id_with_flags, True)
        if model_id_with_flags:
            await test_model_details(model_id_with_flags, True)
    
    if job_id_without_flags:
        model_id_without_flags = await test_wait_for_job_and_check_model(job_id_without_flags, False)
        if model_id_without_flags:
            await test_model_details(model_id_without_flags, False)
    
    # Test 7: Bestehende Modelle prüfen
    await test_existing_models()
    
    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Gesamt: {total_tests} Tests")
    print(f"✅ Bestanden: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FEHLGESCHLAGENE TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
    
    print("\n" + "="*60)
    
    # Exit Code
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())


Vollständiger Integrationstest für Flag-Features
Testet alle kritischen Punkte der Flag-Features Integration
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
import sys
import time

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"  # Externe API
DB_URL = "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta"

# Test-Ergebnisse
test_results = []

def log_test(name: str, passed: bool, message: str = ""):
    """Loggt ein Test-Ergebnis"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"      → {message}")
    test_results.append({"name": name, "passed": passed, "message": message})

def print_section(title: str):
    """Druckt eine Sektion-Überschrift"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============================================================
# TEST 1: API Features Endpoint
# ============================================================
def test_features_endpoint():
    print_section("TEST 1: API Features Endpoint")
    
    try:
        # Test 1.1: Mit Flag-Features (Standard)
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            base_count = data.get('base_count', 0)
            engineered_count = data.get('engineered_count', 0)
            flag_count = data.get('flag_count', 0)
            total = data.get('total', 0)
            
            log_test(
                "GET /api/features?include_flags=true",
                True,
                f"Base: {base_count}, Engineering: {engineered_count}, Flags: {flag_count}, Total: {total}"
            )
            
            # Prüfe ob Flag-Features vorhanden sind
            if flag_count > 0:
                log_test("Flag-Features in Response", True, f"{flag_count} Flag-Features gefunden")
            else:
                log_test("Flag-Features in Response", False, "Keine Flag-Features gefunden!")
        else:
            log_test("GET /api/features?include_flags=true", False, f"Status: {response.status_code}")
        
        # Test 1.2: Ohne Flag-Features
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=false", timeout=10)
        if response.status_code == 200:
            data = response.json()
            flag_count = data.get('flag_count', 0)
            
            if flag_count == 0:
                log_test("GET /api/features?include_flags=false", True, "Keine Flag-Features zurückgegeben")
            else:
                log_test("GET /api/features?include_flags=false", False, f"Flag-Features sollten 0 sein, aber: {flag_count}")
        else:
            log_test("GET /api/features?include_flags=false", False, f"Status: {response.status_code}")
            
    except Exception as e:
        log_test("Features Endpoint", False, f"Exception: {str(e)}")

# ============================================================
# TEST 2: Modell mit Flag-Features erstellen
# ============================================================
def test_create_model_with_flags():
    print_section("TEST 2: Modell mit Flag-Features erstellen")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_FLAG_FEATURES_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol,buy_pressure_ratio",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "true",
            "use_flag_features": "true",  # WICHTIG: Flag-Features aktivieren
            "scale_pos_weight": "100"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell mit Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)
# ============================================================
def test_create_model_without_flags():
    print_section("TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_NO_FLAGS_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "false",
            "use_flag_features": "false",  # WICHTIG: Flag-Features deaktivieren
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell ohne Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 4: Datenbank prüfen
# ============================================================
async def test_database_storage():
    print_section("TEST 4: Datenbank prüfen (use_flag_features gespeichert)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Test 4.1: Prüfe ob Spalte existiert
        column_exists = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists:
            log_test("ml_models.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_models.use_flag_features Spalte existiert", False, "Spalte fehlt!")
            await conn.close()
            return
        
        # Test 4.2: Prüfe neueste Modelle
        recent_models = await conn.fetch("""
            SELECT id, name, use_flag_features, params
            FROM ml_models
            WHERE name LIKE 'TEST_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_models:
            log_test("Neueste Test-Modelle gefunden", True, f"{len(recent_models)} Modelle")
            for model in recent_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                params = model['params']
                
                # Prüfe ob use_flag_features in params auch gespeichert ist
                params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
                flags_in_params = params_dict.get('use_flag_features', None)
                
                log_test(
                    f"Modell {model_id} ({model_name})",
                    use_flags is not None,
                    f"use_flag_features={use_flags}, in params={flags_in_params}"
                )
        else:
            log_test("Neueste Test-Modelle gefunden", False, "Keine Test-Modelle gefunden")
        
        # Test 4.3: Prüfe ml_jobs
        column_exists_jobs = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_jobs' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists_jobs:
            log_test("ml_jobs.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_jobs.use_flag_features Spalte existiert", False, "Spalte fehlt!")
        
        await conn.close()
        
    except Exception as e:
        log_test("Datenbank prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 5: Warte auf Job-Abschluss und prüfe Modell
# ============================================================
async def test_wait_for_job_and_check_model(job_id: int, expected_flags: bool):
    print_section(f"TEST 5: Warte auf Job {job_id} (erwartet Flag-Features: {expected_flags})")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        max_wait = 300  # 5 Minuten
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await conn.fetchrow("""
                SELECT id, status, result_model_id, use_flag_features
                FROM ml_jobs
                WHERE id = $1
            """, job_id)
            
            if not job:
                log_test(f"Job {job_id} gefunden", False, "Job nicht in Datenbank")
                await conn.close()
                return None
            
            status = job['status']
            
            if status == 'COMPLETED':
                model_id = job['result_model_id']
                job_use_flags = job['use_flag_features']
                
                log_test(
                    f"Job {job_id} abgeschlossen",
                    True,
                    f"Status: {status}, Model-ID: {model_id}, use_flag_features: {job_use_flags}"
                )
                
                # Prüfe ob use_flag_features korrekt gespeichert wurde
                if job_use_flags == expected_flags:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        True,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                else:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        False,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                
                await conn.close()
                return model_id
                
            elif status == 'FAILED':
                error_msg = await conn.fetchval("""
                    SELECT error_msg FROM ml_jobs WHERE id = $1
                """, job_id)
                log_test(
                    f"Job {job_id} Status",
                    False,
                    f"Job fehlgeschlagen: {error_msg}"
                )
                await conn.close()
                return None
            
            # Warte 5 Sekunden
            await asyncio.sleep(5)
            print(f"      ⏳ Warte auf Job-Abschluss... (Status: {status})")
        
        log_test(f"Job {job_id} Timeout", False, f"Job nicht innerhalb von {max_wait}s abgeschlossen")
        await conn.close()
        return None
        
    except Exception as e:
        log_test(f"Job {job_id} prüfen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 6: Prüfe Modell-Details
# ============================================================
async def test_model_details(model_id: int, expected_flags: bool):
    print_section(f"TEST 6: Prüfe Modell {model_id} Details")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        model = await conn.fetchrow("""
            SELECT id, name, use_flag_features, params, features
            FROM ml_models
            WHERE id = $1
        """, model_id)
        
        if not model:
            log_test(f"Modell {model_id} gefunden", False, "Modell nicht in Datenbank")
            await conn.close()
            return
        
        model_use_flags = model['use_flag_features']
        params = model['params']
        features = model['features']
        
        # Prüfe use_flag_features Spalte
        if model_use_flags == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        
        # Prüfe params
        params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
        flags_in_params = params_dict.get('use_flag_features', None)
        
        if flags_in_params == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        
        # Prüfe Features (Flag-Features sollten enthalten sein wenn aktiviert)
        if expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if flag_features:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    True,
                    f"{len(flag_features)} Flag-Features gefunden"
                )
            else:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    False,
                    "Keine Flag-Features in Features-Liste gefunden"
                )
        elif not expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if not flag_features:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    True,
                    "Keine Flag-Features gefunden (wie erwartet)"
                )
            else:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    False,
                    f"{len(flag_features)} Flag-Features gefunden (sollten nicht vorhanden sein)"
                )
        
        await conn.close()
        
    except Exception as e:
        log_test(f"Modell {model_id} Details prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)
# ============================================================
async def test_existing_models():
    print_section("TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Hole 5 zufällige bestehende Modelle
        existing_models = await conn.fetch("""
            SELECT id, name, use_flag_features, status
            FROM ml_models
            WHERE name NOT LIKE 'TEST_%'
            AND status = 'READY'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        if existing_models:
            log_test("Bestehende Modelle gefunden", True, f"{len(existing_models)} Modelle")
            
            for model in existing_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                
                # Prüfe ob use_flag_features gesetzt ist (sollte True sein nach Migration)
                if use_flags is not None:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        True,
                        f"use_flag_features={use_flags} (nach Migration sollte True sein)"
                    )
                else:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        False,
                        "use_flag_features ist NULL (sollte nach Migration True sein)"
                    )
        else:
            log_test("Bestehende Modelle gefunden", False, "Keine bestehenden Modelle gefunden")
        
        await conn.close()
        
    except Exception as e:
        log_test("Bestehende Modelle prüfen", False, f"Exception: {str(e)}")

# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "="*60)
    print("  🧪 VOLLSTÄNDIGER INTEGRATIONSTEST: Flag-Features")
    print("="*60 + "\n")
    
    # Test 1: API Features Endpoint
    test_features_endpoint()
    
    # Test 2: Modell mit Flag-Features erstellen
    job_id_with_flags = test_create_model_with_flags()
    
    # Test 3: Modell ohne Flag-Features erstellen
    job_id_without_flags = test_create_model_without_flags()
    
    # Test 4: Datenbank prüfen
    await test_database_storage()
    
    # Test 5: Warte auf Jobs und prüfe Modelle
    if job_id_with_flags:
        model_id_with_flags = await test_wait_for_job_and_check_model(job_id_with_flags, True)
        if model_id_with_flags:
            await test_model_details(model_id_with_flags, True)
    
    if job_id_without_flags:
        model_id_without_flags = await test_wait_for_job_and_check_model(job_id_without_flags, False)
        if model_id_without_flags:
            await test_model_details(model_id_without_flags, False)
    
    # Test 7: Bestehende Modelle prüfen
    await test_existing_models()
    
    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Gesamt: {total_tests} Tests")
    print(f"✅ Bestanden: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FEHLGESCHLAGENE TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
    
    print("\n" + "="*60)
    
    # Exit Code
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())


Vollständiger Integrationstest für Flag-Features
Testet alle kritischen Punkte der Flag-Features Integration
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
import sys
import time

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"  # Externe API
DB_URL = "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta"

# Test-Ergebnisse
test_results = []

def log_test(name: str, passed: bool, message: str = ""):
    """Loggt ein Test-Ergebnis"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"      → {message}")
    test_results.append({"name": name, "passed": passed, "message": message})

def print_section(title: str):
    """Druckt eine Sektion-Überschrift"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============================================================
# TEST 1: API Features Endpoint
# ============================================================
def test_features_endpoint():
    print_section("TEST 1: API Features Endpoint")
    
    try:
        # Test 1.1: Mit Flag-Features (Standard)
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            base_count = data.get('base_count', 0)
            engineered_count = data.get('engineered_count', 0)
            flag_count = data.get('flag_count', 0)
            total = data.get('total', 0)
            
            log_test(
                "GET /api/features?include_flags=true",
                True,
                f"Base: {base_count}, Engineering: {engineered_count}, Flags: {flag_count}, Total: {total}"
            )
            
            # Prüfe ob Flag-Features vorhanden sind
            if flag_count > 0:
                log_test("Flag-Features in Response", True, f"{flag_count} Flag-Features gefunden")
            else:
                log_test("Flag-Features in Response", False, "Keine Flag-Features gefunden!")
        else:
            log_test("GET /api/features?include_flags=true", False, f"Status: {response.status_code}")
        
        # Test 1.2: Ohne Flag-Features
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=false", timeout=10)
        if response.status_code == 200:
            data = response.json()
            flag_count = data.get('flag_count', 0)
            
            if flag_count == 0:
                log_test("GET /api/features?include_flags=false", True, "Keine Flag-Features zurückgegeben")
            else:
                log_test("GET /api/features?include_flags=false", False, f"Flag-Features sollten 0 sein, aber: {flag_count}")
        else:
            log_test("GET /api/features?include_flags=false", False, f"Status: {response.status_code}")
            
    except Exception as e:
        log_test("Features Endpoint", False, f"Exception: {str(e)}")

# ============================================================
# TEST 2: Modell mit Flag-Features erstellen
# ============================================================
def test_create_model_with_flags():
    print_section("TEST 2: Modell mit Flag-Features erstellen")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_FLAG_FEATURES_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol,buy_pressure_ratio",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "true",
            "use_flag_features": "true",  # WICHTIG: Flag-Features aktivieren
            "scale_pos_weight": "100"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell mit Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)
# ============================================================
def test_create_model_without_flags():
    print_section("TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_NO_FLAGS_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "false",
            "use_flag_features": "false",  # WICHTIG: Flag-Features deaktivieren
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell ohne Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 4: Datenbank prüfen
# ============================================================
async def test_database_storage():
    print_section("TEST 4: Datenbank prüfen (use_flag_features gespeichert)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Test 4.1: Prüfe ob Spalte existiert
        column_exists = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists:
            log_test("ml_models.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_models.use_flag_features Spalte existiert", False, "Spalte fehlt!")
            await conn.close()
            return
        
        # Test 4.2: Prüfe neueste Modelle
        recent_models = await conn.fetch("""
            SELECT id, name, use_flag_features, params
            FROM ml_models
            WHERE name LIKE 'TEST_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_models:
            log_test("Neueste Test-Modelle gefunden", True, f"{len(recent_models)} Modelle")
            for model in recent_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                params = model['params']
                
                # Prüfe ob use_flag_features in params auch gespeichert ist
                params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
                flags_in_params = params_dict.get('use_flag_features', None)
                
                log_test(
                    f"Modell {model_id} ({model_name})",
                    use_flags is not None,
                    f"use_flag_features={use_flags}, in params={flags_in_params}"
                )
        else:
            log_test("Neueste Test-Modelle gefunden", False, "Keine Test-Modelle gefunden")
        
        # Test 4.3: Prüfe ml_jobs
        column_exists_jobs = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_jobs' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists_jobs:
            log_test("ml_jobs.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_jobs.use_flag_features Spalte existiert", False, "Spalte fehlt!")
        
        await conn.close()
        
    except Exception as e:
        log_test("Datenbank prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 5: Warte auf Job-Abschluss und prüfe Modell
# ============================================================
async def test_wait_for_job_and_check_model(job_id: int, expected_flags: bool):
    print_section(f"TEST 5: Warte auf Job {job_id} (erwartet Flag-Features: {expected_flags})")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        max_wait = 300  # 5 Minuten
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await conn.fetchrow("""
                SELECT id, status, result_model_id, use_flag_features
                FROM ml_jobs
                WHERE id = $1
            """, job_id)
            
            if not job:
                log_test(f"Job {job_id} gefunden", False, "Job nicht in Datenbank")
                await conn.close()
                return None
            
            status = job['status']
            
            if status == 'COMPLETED':
                model_id = job['result_model_id']
                job_use_flags = job['use_flag_features']
                
                log_test(
                    f"Job {job_id} abgeschlossen",
                    True,
                    f"Status: {status}, Model-ID: {model_id}, use_flag_features: {job_use_flags}"
                )
                
                # Prüfe ob use_flag_features korrekt gespeichert wurde
                if job_use_flags == expected_flags:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        True,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                else:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        False,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                
                await conn.close()
                return model_id
                
            elif status == 'FAILED':
                error_msg = await conn.fetchval("""
                    SELECT error_msg FROM ml_jobs WHERE id = $1
                """, job_id)
                log_test(
                    f"Job {job_id} Status",
                    False,
                    f"Job fehlgeschlagen: {error_msg}"
                )
                await conn.close()
                return None
            
            # Warte 5 Sekunden
            await asyncio.sleep(5)
            print(f"      ⏳ Warte auf Job-Abschluss... (Status: {status})")
        
        log_test(f"Job {job_id} Timeout", False, f"Job nicht innerhalb von {max_wait}s abgeschlossen")
        await conn.close()
        return None
        
    except Exception as e:
        log_test(f"Job {job_id} prüfen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 6: Prüfe Modell-Details
# ============================================================
async def test_model_details(model_id: int, expected_flags: bool):
    print_section(f"TEST 6: Prüfe Modell {model_id} Details")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        model = await conn.fetchrow("""
            SELECT id, name, use_flag_features, params, features
            FROM ml_models
            WHERE id = $1
        """, model_id)
        
        if not model:
            log_test(f"Modell {model_id} gefunden", False, "Modell nicht in Datenbank")
            await conn.close()
            return
        
        model_use_flags = model['use_flag_features']
        params = model['params']
        features = model['features']
        
        # Prüfe use_flag_features Spalte
        if model_use_flags == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        
        # Prüfe params
        params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
        flags_in_params = params_dict.get('use_flag_features', None)
        
        if flags_in_params == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        
        # Prüfe Features (Flag-Features sollten enthalten sein wenn aktiviert)
        if expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if flag_features:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    True,
                    f"{len(flag_features)} Flag-Features gefunden"
                )
            else:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    False,
                    "Keine Flag-Features in Features-Liste gefunden"
                )
        elif not expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if not flag_features:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    True,
                    "Keine Flag-Features gefunden (wie erwartet)"
                )
            else:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    False,
                    f"{len(flag_features)} Flag-Features gefunden (sollten nicht vorhanden sein)"
                )
        
        await conn.close()
        
    except Exception as e:
        log_test(f"Modell {model_id} Details prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)
# ============================================================
async def test_existing_models():
    print_section("TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Hole 5 zufällige bestehende Modelle
        existing_models = await conn.fetch("""
            SELECT id, name, use_flag_features, status
            FROM ml_models
            WHERE name NOT LIKE 'TEST_%'
            AND status = 'READY'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        if existing_models:
            log_test("Bestehende Modelle gefunden", True, f"{len(existing_models)} Modelle")
            
            for model in existing_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                
                # Prüfe ob use_flag_features gesetzt ist (sollte True sein nach Migration)
                if use_flags is not None:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        True,
                        f"use_flag_features={use_flags} (nach Migration sollte True sein)"
                    )
                else:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        False,
                        "use_flag_features ist NULL (sollte nach Migration True sein)"
                    )
        else:
            log_test("Bestehende Modelle gefunden", False, "Keine bestehenden Modelle gefunden")
        
        await conn.close()
        
    except Exception as e:
        log_test("Bestehende Modelle prüfen", False, f"Exception: {str(e)}")

# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "="*60)
    print("  🧪 VOLLSTÄNDIGER INTEGRATIONSTEST: Flag-Features")
    print("="*60 + "\n")
    
    # Test 1: API Features Endpoint
    test_features_endpoint()
    
    # Test 2: Modell mit Flag-Features erstellen
    job_id_with_flags = test_create_model_with_flags()
    
    # Test 3: Modell ohne Flag-Features erstellen
    job_id_without_flags = test_create_model_without_flags()
    
    # Test 4: Datenbank prüfen
    await test_database_storage()
    
    # Test 5: Warte auf Jobs und prüfe Modelle
    if job_id_with_flags:
        model_id_with_flags = await test_wait_for_job_and_check_model(job_id_with_flags, True)
        if model_id_with_flags:
            await test_model_details(model_id_with_flags, True)
    
    if job_id_without_flags:
        model_id_without_flags = await test_wait_for_job_and_check_model(job_id_without_flags, False)
        if model_id_without_flags:
            await test_model_details(model_id_without_flags, False)
    
    # Test 7: Bestehende Modelle prüfen
    await test_existing_models()
    
    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Gesamt: {total_tests} Tests")
    print(f"✅ Bestanden: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FEHLGESCHLAGENE TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
    
    print("\n" + "="*60)
    
    # Exit Code
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())

Vollständiger Integrationstest für Flag-Features
Testet alle kritischen Punkte der Flag-Features Integration
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
import sys
import time

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"  # Externe API
DB_URL = "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta"

# Test-Ergebnisse
test_results = []

def log_test(name: str, passed: bool, message: str = ""):
    """Loggt ein Test-Ergebnis"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"      → {message}")
    test_results.append({"name": name, "passed": passed, "message": message})

def print_section(title: str):
    """Druckt eine Sektion-Überschrift"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============================================================
# TEST 1: API Features Endpoint
# ============================================================
def test_features_endpoint():
    print_section("TEST 1: API Features Endpoint")
    
    try:
        # Test 1.1: Mit Flag-Features (Standard)
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            base_count = data.get('base_count', 0)
            engineered_count = data.get('engineered_count', 0)
            flag_count = data.get('flag_count', 0)
            total = data.get('total', 0)
            
            log_test(
                "GET /api/features?include_flags=true",
                True,
                f"Base: {base_count}, Engineering: {engineered_count}, Flags: {flag_count}, Total: {total}"
            )
            
            # Prüfe ob Flag-Features vorhanden sind
            if flag_count > 0:
                log_test("Flag-Features in Response", True, f"{flag_count} Flag-Features gefunden")
            else:
                log_test("Flag-Features in Response", False, "Keine Flag-Features gefunden!")
        else:
            log_test("GET /api/features?include_flags=true", False, f"Status: {response.status_code}")
        
        # Test 1.2: Ohne Flag-Features
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=false", timeout=10)
        if response.status_code == 200:
            data = response.json()
            flag_count = data.get('flag_count', 0)
            
            if flag_count == 0:
                log_test("GET /api/features?include_flags=false", True, "Keine Flag-Features zurückgegeben")
            else:
                log_test("GET /api/features?include_flags=false", False, f"Flag-Features sollten 0 sein, aber: {flag_count}")
        else:
            log_test("GET /api/features?include_flags=false", False, f"Status: {response.status_code}")
            
    except Exception as e:
        log_test("Features Endpoint", False, f"Exception: {str(e)}")

# ============================================================
# TEST 2: Modell mit Flag-Features erstellen
# ============================================================
def test_create_model_with_flags():
    print_section("TEST 2: Modell mit Flag-Features erstellen")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_FLAG_FEATURES_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol,buy_pressure_ratio",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "true",
            "use_flag_features": "true",  # WICHTIG: Flag-Features aktivieren
            "scale_pos_weight": "100"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell mit Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)
# ============================================================
def test_create_model_without_flags():
    print_section("TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_NO_FLAGS_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "false",
            "use_flag_features": "false",  # WICHTIG: Flag-Features deaktivieren
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell ohne Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 4: Datenbank prüfen
# ============================================================
async def test_database_storage():
    print_section("TEST 4: Datenbank prüfen (use_flag_features gespeichert)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Test 4.1: Prüfe ob Spalte existiert
        column_exists = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists:
            log_test("ml_models.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_models.use_flag_features Spalte existiert", False, "Spalte fehlt!")
            await conn.close()
            return
        
        # Test 4.2: Prüfe neueste Modelle
        recent_models = await conn.fetch("""
            SELECT id, name, use_flag_features, params
            FROM ml_models
            WHERE name LIKE 'TEST_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_models:
            log_test("Neueste Test-Modelle gefunden", True, f"{len(recent_models)} Modelle")
            for model in recent_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                params = model['params']
                
                # Prüfe ob use_flag_features in params auch gespeichert ist
                params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
                flags_in_params = params_dict.get('use_flag_features', None)
                
                log_test(
                    f"Modell {model_id} ({model_name})",
                    use_flags is not None,
                    f"use_flag_features={use_flags}, in params={flags_in_params}"
                )
        else:
            log_test("Neueste Test-Modelle gefunden", False, "Keine Test-Modelle gefunden")
        
        # Test 4.3: Prüfe ml_jobs
        column_exists_jobs = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_jobs' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists_jobs:
            log_test("ml_jobs.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_jobs.use_flag_features Spalte existiert", False, "Spalte fehlt!")
        
        await conn.close()
        
    except Exception as e:
        log_test("Datenbank prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 5: Warte auf Job-Abschluss und prüfe Modell
# ============================================================
async def test_wait_for_job_and_check_model(job_id: int, expected_flags: bool):
    print_section(f"TEST 5: Warte auf Job {job_id} (erwartet Flag-Features: {expected_flags})")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        max_wait = 300  # 5 Minuten
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await conn.fetchrow("""
                SELECT id, status, result_model_id, use_flag_features
                FROM ml_jobs
                WHERE id = $1
            """, job_id)
            
            if not job:
                log_test(f"Job {job_id} gefunden", False, "Job nicht in Datenbank")
                await conn.close()
                return None
            
            status = job['status']
            
            if status == 'COMPLETED':
                model_id = job['result_model_id']
                job_use_flags = job['use_flag_features']
                
                log_test(
                    f"Job {job_id} abgeschlossen",
                    True,
                    f"Status: {status}, Model-ID: {model_id}, use_flag_features: {job_use_flags}"
                )
                
                # Prüfe ob use_flag_features korrekt gespeichert wurde
                if job_use_flags == expected_flags:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        True,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                else:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        False,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                
                await conn.close()
                return model_id
                
            elif status == 'FAILED':
                error_msg = await conn.fetchval("""
                    SELECT error_msg FROM ml_jobs WHERE id = $1
                """, job_id)
                log_test(
                    f"Job {job_id} Status",
                    False,
                    f"Job fehlgeschlagen: {error_msg}"
                )
                await conn.close()
                return None
            
            # Warte 5 Sekunden
            await asyncio.sleep(5)
            print(f"      ⏳ Warte auf Job-Abschluss... (Status: {status})")
        
        log_test(f"Job {job_id} Timeout", False, f"Job nicht innerhalb von {max_wait}s abgeschlossen")
        await conn.close()
        return None
        
    except Exception as e:
        log_test(f"Job {job_id} prüfen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 6: Prüfe Modell-Details
# ============================================================
async def test_model_details(model_id: int, expected_flags: bool):
    print_section(f"TEST 6: Prüfe Modell {model_id} Details")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        model = await conn.fetchrow("""
            SELECT id, name, use_flag_features, params, features
            FROM ml_models
            WHERE id = $1
        """, model_id)
        
        if not model:
            log_test(f"Modell {model_id} gefunden", False, "Modell nicht in Datenbank")
            await conn.close()
            return
        
        model_use_flags = model['use_flag_features']
        params = model['params']
        features = model['features']
        
        # Prüfe use_flag_features Spalte
        if model_use_flags == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        
        # Prüfe params
        params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
        flags_in_params = params_dict.get('use_flag_features', None)
        
        if flags_in_params == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        
        # Prüfe Features (Flag-Features sollten enthalten sein wenn aktiviert)
        if expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if flag_features:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    True,
                    f"{len(flag_features)} Flag-Features gefunden"
                )
            else:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    False,
                    "Keine Flag-Features in Features-Liste gefunden"
                )
        elif not expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if not flag_features:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    True,
                    "Keine Flag-Features gefunden (wie erwartet)"
                )
            else:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    False,
                    f"{len(flag_features)} Flag-Features gefunden (sollten nicht vorhanden sein)"
                )
        
        await conn.close()
        
    except Exception as e:
        log_test(f"Modell {model_id} Details prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)
# ============================================================
async def test_existing_models():
    print_section("TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Hole 5 zufällige bestehende Modelle
        existing_models = await conn.fetch("""
            SELECT id, name, use_flag_features, status
            FROM ml_models
            WHERE name NOT LIKE 'TEST_%'
            AND status = 'READY'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        if existing_models:
            log_test("Bestehende Modelle gefunden", True, f"{len(existing_models)} Modelle")
            
            for model in existing_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                
                # Prüfe ob use_flag_features gesetzt ist (sollte True sein nach Migration)
                if use_flags is not None:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        True,
                        f"use_flag_features={use_flags} (nach Migration sollte True sein)"
                    )
                else:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        False,
                        "use_flag_features ist NULL (sollte nach Migration True sein)"
                    )
        else:
            log_test("Bestehende Modelle gefunden", False, "Keine bestehenden Modelle gefunden")
        
        await conn.close()
        
    except Exception as e:
        log_test("Bestehende Modelle prüfen", False, f"Exception: {str(e)}")

# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "="*60)
    print("  🧪 VOLLSTÄNDIGER INTEGRATIONSTEST: Flag-Features")
    print("="*60 + "\n")
    
    # Test 1: API Features Endpoint
    test_features_endpoint()
    
    # Test 2: Modell mit Flag-Features erstellen
    job_id_with_flags = test_create_model_with_flags()
    
    # Test 3: Modell ohne Flag-Features erstellen
    job_id_without_flags = test_create_model_without_flags()
    
    # Test 4: Datenbank prüfen
    await test_database_storage()
    
    # Test 5: Warte auf Jobs und prüfe Modelle
    if job_id_with_flags:
        model_id_with_flags = await test_wait_for_job_and_check_model(job_id_with_flags, True)
        if model_id_with_flags:
            await test_model_details(model_id_with_flags, True)
    
    if job_id_without_flags:
        model_id_without_flags = await test_wait_for_job_and_check_model(job_id_without_flags, False)
        if model_id_without_flags:
            await test_model_details(model_id_without_flags, False)
    
    # Test 7: Bestehende Modelle prüfen
    await test_existing_models()
    
    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Gesamt: {total_tests} Tests")
    print(f"✅ Bestanden: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FEHLGESCHLAGENE TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
    
    print("\n" + "="*60)
    
    # Exit Code
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())


Vollständiger Integrationstest für Flag-Features
Testet alle kritischen Punkte der Flag-Features Integration
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
import sys
import time

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"  # Externe API
DB_URL = "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta"

# Test-Ergebnisse
test_results = []

def log_test(name: str, passed: bool, message: str = ""):
    """Loggt ein Test-Ergebnis"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"      → {message}")
    test_results.append({"name": name, "passed": passed, "message": message})

def print_section(title: str):
    """Druckt eine Sektion-Überschrift"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============================================================
# TEST 1: API Features Endpoint
# ============================================================
def test_features_endpoint():
    print_section("TEST 1: API Features Endpoint")
    
    try:
        # Test 1.1: Mit Flag-Features (Standard)
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            base_count = data.get('base_count', 0)
            engineered_count = data.get('engineered_count', 0)
            flag_count = data.get('flag_count', 0)
            total = data.get('total', 0)
            
            log_test(
                "GET /api/features?include_flags=true",
                True,
                f"Base: {base_count}, Engineering: {engineered_count}, Flags: {flag_count}, Total: {total}"
            )
            
            # Prüfe ob Flag-Features vorhanden sind
            if flag_count > 0:
                log_test("Flag-Features in Response", True, f"{flag_count} Flag-Features gefunden")
            else:
                log_test("Flag-Features in Response", False, "Keine Flag-Features gefunden!")
        else:
            log_test("GET /api/features?include_flags=true", False, f"Status: {response.status_code}")
        
        # Test 1.2: Ohne Flag-Features
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=false", timeout=10)
        if response.status_code == 200:
            data = response.json()
            flag_count = data.get('flag_count', 0)
            
            if flag_count == 0:
                log_test("GET /api/features?include_flags=false", True, "Keine Flag-Features zurückgegeben")
            else:
                log_test("GET /api/features?include_flags=false", False, f"Flag-Features sollten 0 sein, aber: {flag_count}")
        else:
            log_test("GET /api/features?include_flags=false", False, f"Status: {response.status_code}")
            
    except Exception as e:
        log_test("Features Endpoint", False, f"Exception: {str(e)}")

# ============================================================
# TEST 2: Modell mit Flag-Features erstellen
# ============================================================
def test_create_model_with_flags():
    print_section("TEST 2: Modell mit Flag-Features erstellen")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_FLAG_FEATURES_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol,buy_pressure_ratio",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "true",
            "use_flag_features": "true",  # WICHTIG: Flag-Features aktivieren
            "scale_pos_weight": "100"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell mit Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)
# ============================================================
def test_create_model_without_flags():
    print_section("TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_NO_FLAGS_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "false",
            "use_flag_features": "false",  # WICHTIG: Flag-Features deaktivieren
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell ohne Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 4: Datenbank prüfen
# ============================================================
async def test_database_storage():
    print_section("TEST 4: Datenbank prüfen (use_flag_features gespeichert)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Test 4.1: Prüfe ob Spalte existiert
        column_exists = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists:
            log_test("ml_models.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_models.use_flag_features Spalte existiert", False, "Spalte fehlt!")
            await conn.close()
            return
        
        # Test 4.2: Prüfe neueste Modelle
        recent_models = await conn.fetch("""
            SELECT id, name, use_flag_features, params
            FROM ml_models
            WHERE name LIKE 'TEST_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_models:
            log_test("Neueste Test-Modelle gefunden", True, f"{len(recent_models)} Modelle")
            for model in recent_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                params = model['params']
                
                # Prüfe ob use_flag_features in params auch gespeichert ist
                params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
                flags_in_params = params_dict.get('use_flag_features', None)
                
                log_test(
                    f"Modell {model_id} ({model_name})",
                    use_flags is not None,
                    f"use_flag_features={use_flags}, in params={flags_in_params}"
                )
        else:
            log_test("Neueste Test-Modelle gefunden", False, "Keine Test-Modelle gefunden")
        
        # Test 4.3: Prüfe ml_jobs
        column_exists_jobs = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_jobs' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists_jobs:
            log_test("ml_jobs.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_jobs.use_flag_features Spalte existiert", False, "Spalte fehlt!")
        
        await conn.close()
        
    except Exception as e:
        log_test("Datenbank prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 5: Warte auf Job-Abschluss und prüfe Modell
# ============================================================
async def test_wait_for_job_and_check_model(job_id: int, expected_flags: bool):
    print_section(f"TEST 5: Warte auf Job {job_id} (erwartet Flag-Features: {expected_flags})")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        max_wait = 300  # 5 Minuten
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await conn.fetchrow("""
                SELECT id, status, result_model_id, use_flag_features
                FROM ml_jobs
                WHERE id = $1
            """, job_id)
            
            if not job:
                log_test(f"Job {job_id} gefunden", False, "Job nicht in Datenbank")
                await conn.close()
                return None
            
            status = job['status']
            
            if status == 'COMPLETED':
                model_id = job['result_model_id']
                job_use_flags = job['use_flag_features']
                
                log_test(
                    f"Job {job_id} abgeschlossen",
                    True,
                    f"Status: {status}, Model-ID: {model_id}, use_flag_features: {job_use_flags}"
                )
                
                # Prüfe ob use_flag_features korrekt gespeichert wurde
                if job_use_flags == expected_flags:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        True,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                else:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        False,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                
                await conn.close()
                return model_id
                
            elif status == 'FAILED':
                error_msg = await conn.fetchval("""
                    SELECT error_msg FROM ml_jobs WHERE id = $1
                """, job_id)
                log_test(
                    f"Job {job_id} Status",
                    False,
                    f"Job fehlgeschlagen: {error_msg}"
                )
                await conn.close()
                return None
            
            # Warte 5 Sekunden
            await asyncio.sleep(5)
            print(f"      ⏳ Warte auf Job-Abschluss... (Status: {status})")
        
        log_test(f"Job {job_id} Timeout", False, f"Job nicht innerhalb von {max_wait}s abgeschlossen")
        await conn.close()
        return None
        
    except Exception as e:
        log_test(f"Job {job_id} prüfen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 6: Prüfe Modell-Details
# ============================================================
async def test_model_details(model_id: int, expected_flags: bool):
    print_section(f"TEST 6: Prüfe Modell {model_id} Details")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        model = await conn.fetchrow("""
            SELECT id, name, use_flag_features, params, features
            FROM ml_models
            WHERE id = $1
        """, model_id)
        
        if not model:
            log_test(f"Modell {model_id} gefunden", False, "Modell nicht in Datenbank")
            await conn.close()
            return
        
        model_use_flags = model['use_flag_features']
        params = model['params']
        features = model['features']
        
        # Prüfe use_flag_features Spalte
        if model_use_flags == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        
        # Prüfe params
        params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
        flags_in_params = params_dict.get('use_flag_features', None)
        
        if flags_in_params == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        
        # Prüfe Features (Flag-Features sollten enthalten sein wenn aktiviert)
        if expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if flag_features:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    True,
                    f"{len(flag_features)} Flag-Features gefunden"
                )
            else:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    False,
                    "Keine Flag-Features in Features-Liste gefunden"
                )
        elif not expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if not flag_features:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    True,
                    "Keine Flag-Features gefunden (wie erwartet)"
                )
            else:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    False,
                    f"{len(flag_features)} Flag-Features gefunden (sollten nicht vorhanden sein)"
                )
        
        await conn.close()
        
    except Exception as e:
        log_test(f"Modell {model_id} Details prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)
# ============================================================
async def test_existing_models():
    print_section("TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Hole 5 zufällige bestehende Modelle
        existing_models = await conn.fetch("""
            SELECT id, name, use_flag_features, status
            FROM ml_models
            WHERE name NOT LIKE 'TEST_%'
            AND status = 'READY'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        if existing_models:
            log_test("Bestehende Modelle gefunden", True, f"{len(existing_models)} Modelle")
            
            for model in existing_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                
                # Prüfe ob use_flag_features gesetzt ist (sollte True sein nach Migration)
                if use_flags is not None:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        True,
                        f"use_flag_features={use_flags} (nach Migration sollte True sein)"
                    )
                else:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        False,
                        "use_flag_features ist NULL (sollte nach Migration True sein)"
                    )
        else:
            log_test("Bestehende Modelle gefunden", False, "Keine bestehenden Modelle gefunden")
        
        await conn.close()
        
    except Exception as e:
        log_test("Bestehende Modelle prüfen", False, f"Exception: {str(e)}")

# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "="*60)
    print("  🧪 VOLLSTÄNDIGER INTEGRATIONSTEST: Flag-Features")
    print("="*60 + "\n")
    
    # Test 1: API Features Endpoint
    test_features_endpoint()
    
    # Test 2: Modell mit Flag-Features erstellen
    job_id_with_flags = test_create_model_with_flags()
    
    # Test 3: Modell ohne Flag-Features erstellen
    job_id_without_flags = test_create_model_without_flags()
    
    # Test 4: Datenbank prüfen
    await test_database_storage()
    
    # Test 5: Warte auf Jobs und prüfe Modelle
    if job_id_with_flags:
        model_id_with_flags = await test_wait_for_job_and_check_model(job_id_with_flags, True)
        if model_id_with_flags:
            await test_model_details(model_id_with_flags, True)
    
    if job_id_without_flags:
        model_id_without_flags = await test_wait_for_job_and_check_model(job_id_without_flags, False)
        if model_id_without_flags:
            await test_model_details(model_id_without_flags, False)
    
    # Test 7: Bestehende Modelle prüfen
    await test_existing_models()
    
    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Gesamt: {total_tests} Tests")
    print(f"✅ Bestanden: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FEHLGESCHLAGENE TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
    
    print("\n" + "="*60)
    
    # Exit Code
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())


Vollständiger Integrationstest für Flag-Features
Testet alle kritischen Punkte der Flag-Features Integration
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
import sys
import time

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"  # Externe API
DB_URL = "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta"

# Test-Ergebnisse
test_results = []

def log_test(name: str, passed: bool, message: str = ""):
    """Loggt ein Test-Ergebnis"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"      → {message}")
    test_results.append({"name": name, "passed": passed, "message": message})

def print_section(title: str):
    """Druckt eine Sektion-Überschrift"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============================================================
# TEST 1: API Features Endpoint
# ============================================================
def test_features_endpoint():
    print_section("TEST 1: API Features Endpoint")
    
    try:
        # Test 1.1: Mit Flag-Features (Standard)
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            base_count = data.get('base_count', 0)
            engineered_count = data.get('engineered_count', 0)
            flag_count = data.get('flag_count', 0)
            total = data.get('total', 0)
            
            log_test(
                "GET /api/features?include_flags=true",
                True,
                f"Base: {base_count}, Engineering: {engineered_count}, Flags: {flag_count}, Total: {total}"
            )
            
            # Prüfe ob Flag-Features vorhanden sind
            if flag_count > 0:
                log_test("Flag-Features in Response", True, f"{flag_count} Flag-Features gefunden")
            else:
                log_test("Flag-Features in Response", False, "Keine Flag-Features gefunden!")
        else:
            log_test("GET /api/features?include_flags=true", False, f"Status: {response.status_code}")
        
        # Test 1.2: Ohne Flag-Features
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=false", timeout=10)
        if response.status_code == 200:
            data = response.json()
            flag_count = data.get('flag_count', 0)
            
            if flag_count == 0:
                log_test("GET /api/features?include_flags=false", True, "Keine Flag-Features zurückgegeben")
            else:
                log_test("GET /api/features?include_flags=false", False, f"Flag-Features sollten 0 sein, aber: {flag_count}")
        else:
            log_test("GET /api/features?include_flags=false", False, f"Status: {response.status_code}")
            
    except Exception as e:
        log_test("Features Endpoint", False, f"Exception: {str(e)}")

# ============================================================
# TEST 2: Modell mit Flag-Features erstellen
# ============================================================
def test_create_model_with_flags():
    print_section("TEST 2: Modell mit Flag-Features erstellen")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_FLAG_FEATURES_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol,buy_pressure_ratio",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "true",
            "use_flag_features": "true",  # WICHTIG: Flag-Features aktivieren
            "scale_pos_weight": "100"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell mit Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)
# ============================================================
def test_create_model_without_flags():
    print_section("TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_NO_FLAGS_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "false",
            "use_flag_features": "false",  # WICHTIG: Flag-Features deaktivieren
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell ohne Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 4: Datenbank prüfen
# ============================================================
async def test_database_storage():
    print_section("TEST 4: Datenbank prüfen (use_flag_features gespeichert)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Test 4.1: Prüfe ob Spalte existiert
        column_exists = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists:
            log_test("ml_models.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_models.use_flag_features Spalte existiert", False, "Spalte fehlt!")
            await conn.close()
            return
        
        # Test 4.2: Prüfe neueste Modelle
        recent_models = await conn.fetch("""
            SELECT id, name, use_flag_features, params
            FROM ml_models
            WHERE name LIKE 'TEST_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_models:
            log_test("Neueste Test-Modelle gefunden", True, f"{len(recent_models)} Modelle")
            for model in recent_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                params = model['params']
                
                # Prüfe ob use_flag_features in params auch gespeichert ist
                params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
                flags_in_params = params_dict.get('use_flag_features', None)
                
                log_test(
                    f"Modell {model_id} ({model_name})",
                    use_flags is not None,
                    f"use_flag_features={use_flags}, in params={flags_in_params}"
                )
        else:
            log_test("Neueste Test-Modelle gefunden", False, "Keine Test-Modelle gefunden")
        
        # Test 4.3: Prüfe ml_jobs
        column_exists_jobs = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_jobs' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists_jobs:
            log_test("ml_jobs.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_jobs.use_flag_features Spalte existiert", False, "Spalte fehlt!")
        
        await conn.close()
        
    except Exception as e:
        log_test("Datenbank prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 5: Warte auf Job-Abschluss und prüfe Modell
# ============================================================
async def test_wait_for_job_and_check_model(job_id: int, expected_flags: bool):
    print_section(f"TEST 5: Warte auf Job {job_id} (erwartet Flag-Features: {expected_flags})")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        max_wait = 300  # 5 Minuten
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await conn.fetchrow("""
                SELECT id, status, result_model_id, use_flag_features
                FROM ml_jobs
                WHERE id = $1
            """, job_id)
            
            if not job:
                log_test(f"Job {job_id} gefunden", False, "Job nicht in Datenbank")
                await conn.close()
                return None
            
            status = job['status']
            
            if status == 'COMPLETED':
                model_id = job['result_model_id']
                job_use_flags = job['use_flag_features']
                
                log_test(
                    f"Job {job_id} abgeschlossen",
                    True,
                    f"Status: {status}, Model-ID: {model_id}, use_flag_features: {job_use_flags}"
                )
                
                # Prüfe ob use_flag_features korrekt gespeichert wurde
                if job_use_flags == expected_flags:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        True,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                else:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        False,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                
                await conn.close()
                return model_id
                
            elif status == 'FAILED':
                error_msg = await conn.fetchval("""
                    SELECT error_msg FROM ml_jobs WHERE id = $1
                """, job_id)
                log_test(
                    f"Job {job_id} Status",
                    False,
                    f"Job fehlgeschlagen: {error_msg}"
                )
                await conn.close()
                return None
            
            # Warte 5 Sekunden
            await asyncio.sleep(5)
            print(f"      ⏳ Warte auf Job-Abschluss... (Status: {status})")
        
        log_test(f"Job {job_id} Timeout", False, f"Job nicht innerhalb von {max_wait}s abgeschlossen")
        await conn.close()
        return None
        
    except Exception as e:
        log_test(f"Job {job_id} prüfen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 6: Prüfe Modell-Details
# ============================================================
async def test_model_details(model_id: int, expected_flags: bool):
    print_section(f"TEST 6: Prüfe Modell {model_id} Details")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        model = await conn.fetchrow("""
            SELECT id, name, use_flag_features, params, features
            FROM ml_models
            WHERE id = $1
        """, model_id)
        
        if not model:
            log_test(f"Modell {model_id} gefunden", False, "Modell nicht in Datenbank")
            await conn.close()
            return
        
        model_use_flags = model['use_flag_features']
        params = model['params']
        features = model['features']
        
        # Prüfe use_flag_features Spalte
        if model_use_flags == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        
        # Prüfe params
        params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
        flags_in_params = params_dict.get('use_flag_features', None)
        
        if flags_in_params == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        
        # Prüfe Features (Flag-Features sollten enthalten sein wenn aktiviert)
        if expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if flag_features:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    True,
                    f"{len(flag_features)} Flag-Features gefunden"
                )
            else:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    False,
                    "Keine Flag-Features in Features-Liste gefunden"
                )
        elif not expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if not flag_features:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    True,
                    "Keine Flag-Features gefunden (wie erwartet)"
                )
            else:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    False,
                    f"{len(flag_features)} Flag-Features gefunden (sollten nicht vorhanden sein)"
                )
        
        await conn.close()
        
    except Exception as e:
        log_test(f"Modell {model_id} Details prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)
# ============================================================
async def test_existing_models():
    print_section("TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Hole 5 zufällige bestehende Modelle
        existing_models = await conn.fetch("""
            SELECT id, name, use_flag_features, status
            FROM ml_models
            WHERE name NOT LIKE 'TEST_%'
            AND status = 'READY'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        if existing_models:
            log_test("Bestehende Modelle gefunden", True, f"{len(existing_models)} Modelle")
            
            for model in existing_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                
                # Prüfe ob use_flag_features gesetzt ist (sollte True sein nach Migration)
                if use_flags is not None:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        True,
                        f"use_flag_features={use_flags} (nach Migration sollte True sein)"
                    )
                else:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        False,
                        "use_flag_features ist NULL (sollte nach Migration True sein)"
                    )
        else:
            log_test("Bestehende Modelle gefunden", False, "Keine bestehenden Modelle gefunden")
        
        await conn.close()
        
    except Exception as e:
        log_test("Bestehende Modelle prüfen", False, f"Exception: {str(e)}")

# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "="*60)
    print("  🧪 VOLLSTÄNDIGER INTEGRATIONSTEST: Flag-Features")
    print("="*60 + "\n")
    
    # Test 1: API Features Endpoint
    test_features_endpoint()
    
    # Test 2: Modell mit Flag-Features erstellen
    job_id_with_flags = test_create_model_with_flags()
    
    # Test 3: Modell ohne Flag-Features erstellen
    job_id_without_flags = test_create_model_without_flags()
    
    # Test 4: Datenbank prüfen
    await test_database_storage()
    
    # Test 5: Warte auf Jobs und prüfe Modelle
    if job_id_with_flags:
        model_id_with_flags = await test_wait_for_job_and_check_model(job_id_with_flags, True)
        if model_id_with_flags:
            await test_model_details(model_id_with_flags, True)
    
    if job_id_without_flags:
        model_id_without_flags = await test_wait_for_job_and_check_model(job_id_without_flags, False)
        if model_id_without_flags:
            await test_model_details(model_id_without_flags, False)
    
    # Test 7: Bestehende Modelle prüfen
    await test_existing_models()
    
    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Gesamt: {total_tests} Tests")
    print(f"✅ Bestanden: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FEHLGESCHLAGENE TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
    
    print("\n" + "="*60)
    
    # Exit Code
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())


Vollständiger Integrationstest für Flag-Features
Testet alle kritischen Punkte der Flag-Features Integration
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
import sys
import time

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"  # Externe API
DB_URL = "postgresql://postgres:9HVxi6hN6j7xpmqUx84o@100.118.155.75:5432/beta"

# Test-Ergebnisse
test_results = []

def log_test(name: str, passed: bool, message: str = ""):
    """Loggt ein Test-Ergebnis"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"      → {message}")
    test_results.append({"name": name, "passed": passed, "message": message})

def print_section(title: str):
    """Druckt eine Sektion-Überschrift"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ============================================================
# TEST 1: API Features Endpoint
# ============================================================
def test_features_endpoint():
    print_section("TEST 1: API Features Endpoint")
    
    try:
        # Test 1.1: Mit Flag-Features (Standard)
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            base_count = data.get('base_count', 0)
            engineered_count = data.get('engineered_count', 0)
            flag_count = data.get('flag_count', 0)
            total = data.get('total', 0)
            
            log_test(
                "GET /api/features?include_flags=true",
                True,
                f"Base: {base_count}, Engineering: {engineered_count}, Flags: {flag_count}, Total: {total}"
            )
            
            # Prüfe ob Flag-Features vorhanden sind
            if flag_count > 0:
                log_test("Flag-Features in Response", True, f"{flag_count} Flag-Features gefunden")
            else:
                log_test("Flag-Features in Response", False, "Keine Flag-Features gefunden!")
        else:
            log_test("GET /api/features?include_flags=true", False, f"Status: {response.status_code}")
        
        # Test 1.2: Ohne Flag-Features
        response = requests.get(f"{API_BASE_URL}/api/features?include_flags=false", timeout=10)
        if response.status_code == 200:
            data = response.json()
            flag_count = data.get('flag_count', 0)
            
            if flag_count == 0:
                log_test("GET /api/features?include_flags=false", True, "Keine Flag-Features zurückgegeben")
            else:
                log_test("GET /api/features?include_flags=false", False, f"Flag-Features sollten 0 sein, aber: {flag_count}")
        else:
            log_test("GET /api/features?include_flags=false", False, f"Status: {response.status_code}")
            
    except Exception as e:
        log_test("Features Endpoint", False, f"Exception: {str(e)}")

# ============================================================
# TEST 2: Modell mit Flag-Features erstellen
# ============================================================
def test_create_model_with_flags():
    print_section("TEST 2: Modell mit Flag-Features erstellen")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_FLAG_FEATURES_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol,buy_pressure_ratio",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "true",
            "use_flag_features": "true",  # WICHTIG: Flag-Features aktivieren
            "scale_pos_weight": "100"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (mit Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell mit Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)
# ============================================================
def test_create_model_without_flags():
    print_section("TEST 3: Modell ohne Flag-Features erstellen (Rückwärtskompatibilität)")
    
    try:
        # Bereite Test-Daten vor
        now = datetime.now(timezone.utc)
        train_end = now - timedelta(hours=1)
        train_start = train_end - timedelta(hours=12)
        
        params = {
            "name": f"TEST_NO_FLAGS_{int(time.time())}",
            "model_type": "xgboost",
            "features": "price_close,volume_sol",
            "train_start": train_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_end": train_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "future_minutes": "10",
            "min_percent_change": "5",
            "direction": "up",
            "use_engineered_features": "false",
            "use_flag_features": "false",  # WICHTIG: Flag-Features deaktivieren
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/models/create/advanced",
            params=params,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get('job_id')
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                True,
                f"Job erstellt: {job_id}"
            )
            return job_id
        else:
            log_test(
                "POST /api/models/create/advanced (ohne Flag-Features)",
                False,
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test("Modell ohne Flag-Features erstellen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 4: Datenbank prüfen
# ============================================================
async def test_database_storage():
    print_section("TEST 4: Datenbank prüfen (use_flag_features gespeichert)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Test 4.1: Prüfe ob Spalte existiert
        column_exists = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists:
            log_test("ml_models.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_models.use_flag_features Spalte existiert", False, "Spalte fehlt!")
            await conn.close()
            return
        
        # Test 4.2: Prüfe neueste Modelle
        recent_models = await conn.fetch("""
            SELECT id, name, use_flag_features, params
            FROM ml_models
            WHERE name LIKE 'TEST_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_models:
            log_test("Neueste Test-Modelle gefunden", True, f"{len(recent_models)} Modelle")
            for model in recent_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                params = model['params']
                
                # Prüfe ob use_flag_features in params auch gespeichert ist
                params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
                flags_in_params = params_dict.get('use_flag_features', None)
                
                log_test(
                    f"Modell {model_id} ({model_name})",
                    use_flags is not None,
                    f"use_flag_features={use_flags}, in params={flags_in_params}"
                )
        else:
            log_test("Neueste Test-Modelle gefunden", False, "Keine Test-Modelle gefunden")
        
        # Test 4.3: Prüfe ml_jobs
        column_exists_jobs = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_jobs' 
            AND column_name = 'use_flag_features'
        """)
        
        if column_exists_jobs:
            log_test("ml_jobs.use_flag_features Spalte existiert", True)
        else:
            log_test("ml_jobs.use_flag_features Spalte existiert", False, "Spalte fehlt!")
        
        await conn.close()
        
    except Exception as e:
        log_test("Datenbank prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 5: Warte auf Job-Abschluss und prüfe Modell
# ============================================================
async def test_wait_for_job_and_check_model(job_id: int, expected_flags: bool):
    print_section(f"TEST 5: Warte auf Job {job_id} (erwartet Flag-Features: {expected_flags})")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        max_wait = 300  # 5 Minuten
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job = await conn.fetchrow("""
                SELECT id, status, result_model_id, use_flag_features
                FROM ml_jobs
                WHERE id = $1
            """, job_id)
            
            if not job:
                log_test(f"Job {job_id} gefunden", False, "Job nicht in Datenbank")
                await conn.close()
                return None
            
            status = job['status']
            
            if status == 'COMPLETED':
                model_id = job['result_model_id']
                job_use_flags = job['use_flag_features']
                
                log_test(
                    f"Job {job_id} abgeschlossen",
                    True,
                    f"Status: {status}, Model-ID: {model_id}, use_flag_features: {job_use_flags}"
                )
                
                # Prüfe ob use_flag_features korrekt gespeichert wurde
                if job_use_flags == expected_flags:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        True,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                else:
                    log_test(
                        f"Job {job_id} use_flag_features korrekt",
                        False,
                        f"Erwartet: {expected_flags}, Gefunden: {job_use_flags}"
                    )
                
                await conn.close()
                return model_id
                
            elif status == 'FAILED':
                error_msg = await conn.fetchval("""
                    SELECT error_msg FROM ml_jobs WHERE id = $1
                """, job_id)
                log_test(
                    f"Job {job_id} Status",
                    False,
                    f"Job fehlgeschlagen: {error_msg}"
                )
                await conn.close()
                return None
            
            # Warte 5 Sekunden
            await asyncio.sleep(5)
            print(f"      ⏳ Warte auf Job-Abschluss... (Status: {status})")
        
        log_test(f"Job {job_id} Timeout", False, f"Job nicht innerhalb von {max_wait}s abgeschlossen")
        await conn.close()
        return None
        
    except Exception as e:
        log_test(f"Job {job_id} prüfen", False, f"Exception: {str(e)}")
        return None

# ============================================================
# TEST 6: Prüfe Modell-Details
# ============================================================
async def test_model_details(model_id: int, expected_flags: bool):
    print_section(f"TEST 6: Prüfe Modell {model_id} Details")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        model = await conn.fetchrow("""
            SELECT id, name, use_flag_features, params, features
            FROM ml_models
            WHERE id = $1
        """, model_id)
        
        if not model:
            log_test(f"Modell {model_id} gefunden", False, "Modell nicht in Datenbank")
            await conn.close()
            return
        
        model_use_flags = model['use_flag_features']
        params = model['params']
        features = model['features']
        
        # Prüfe use_flag_features Spalte
        if model_use_flags == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features Spalte",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {model_use_flags}"
            )
        
        # Prüfe params
        params_dict = params if isinstance(params, dict) else json.loads(params) if params else {}
        flags_in_params = params_dict.get('use_flag_features', None)
        
        if flags_in_params == expected_flags:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                True,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        else:
            log_test(
                f"Modell {model_id} use_flag_features in params",
                False,
                f"Erwartet: {expected_flags}, Gefunden: {flags_in_params}"
            )
        
        # Prüfe Features (Flag-Features sollten enthalten sein wenn aktiviert)
        if expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if flag_features:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    True,
                    f"{len(flag_features)} Flag-Features gefunden"
                )
            else:
                log_test(
                    f"Modell {model_id} Flag-Features in Features-Liste",
                    False,
                    "Keine Flag-Features in Features-Liste gefunden"
                )
        elif not expected_flags and features:
            flag_features = [f for f in features if f.endswith('_has_data')]
            if not flag_features:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    True,
                    "Keine Flag-Features gefunden (wie erwartet)"
                )
            else:
                log_test(
                    f"Modell {model_id} Keine Flag-Features in Features-Liste",
                    False,
                    f"{len(flag_features)} Flag-Features gefunden (sollten nicht vorhanden sein)"
                )
        
        await conn.close()
        
    except Exception as e:
        log_test(f"Modell {model_id} Details prüfen", False, f"Exception: {str(e)}")

# ============================================================
# TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)
# ============================================================
async def test_existing_models():
    print_section("TEST 7: Bestehende Modelle prüfen (Rückwärtskompatibilität)")
    
    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Hole 5 zufällige bestehende Modelle
        existing_models = await conn.fetch("""
            SELECT id, name, use_flag_features, status
            FROM ml_models
            WHERE name NOT LIKE 'TEST_%'
            AND status = 'READY'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        if existing_models:
            log_test("Bestehende Modelle gefunden", True, f"{len(existing_models)} Modelle")
            
            for model in existing_models:
                model_id = model['id']
                model_name = model['name']
                use_flags = model['use_flag_features']
                
                # Prüfe ob use_flag_features gesetzt ist (sollte True sein nach Migration)
                if use_flags is not None:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        True,
                        f"use_flag_features={use_flags} (nach Migration sollte True sein)"
                    )
                else:
                    log_test(
                        f"Bestehendes Modell {model_id} ({model_name})",
                        False,
                        "use_flag_features ist NULL (sollte nach Migration True sein)"
                    )
        else:
            log_test("Bestehende Modelle gefunden", False, "Keine bestehenden Modelle gefunden")
        
        await conn.close()
        
    except Exception as e:
        log_test("Bestehende Modelle prüfen", False, f"Exception: {str(e)}")

# ============================================================
# MAIN
# ============================================================
async def main():
    print("\n" + "="*60)
    print("  🧪 VOLLSTÄNDIGER INTEGRATIONSTEST: Flag-Features")
    print("="*60 + "\n")
    
    # Test 1: API Features Endpoint
    test_features_endpoint()
    
    # Test 2: Modell mit Flag-Features erstellen
    job_id_with_flags = test_create_model_with_flags()
    
    # Test 3: Modell ohne Flag-Features erstellen
    job_id_without_flags = test_create_model_without_flags()
    
    # Test 4: Datenbank prüfen
    await test_database_storage()
    
    # Test 5: Warte auf Jobs und prüfe Modelle
    if job_id_with_flags:
        model_id_with_flags = await test_wait_for_job_and_check_model(job_id_with_flags, True)
        if model_id_with_flags:
            await test_model_details(model_id_with_flags, True)
    
    if job_id_without_flags:
        model_id_without_flags = await test_wait_for_job_and_check_model(job_id_without_flags, False)
        if model_id_without_flags:
            await test_model_details(model_id_without_flags, False)
    
    # Test 7: Bestehende Modelle prüfen
    await test_existing_models()
    
    # Zusammenfassung
    print_section("ZUSAMMENFASSUNG")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Gesamt: {total_tests} Tests")
    print(f"✅ Bestanden: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FEHLGESCHLAGENE TESTS:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
    
    print("\n" + "="*60)
    
    # Exit Code
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())
