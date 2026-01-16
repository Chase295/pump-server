#!/bin/bash
# Test-Script für Flag-Features Fix

echo "=== TEST: Flag-Features Filterung ==="
echo ""

TIMESTAMP=$(date +%s)
JOB_ID=$(curl -s -X POST "http://localhost:3002/api/models/create/advanced?name=FLAG_TEST_${TIMESTAMP}&model_type=xgboost&features=volume_sol,price_close,buy_pressure_ratio,price_change_5,price_change_10,volume_spike_5&train_start=2026-01-08T00:00:00Z&train_end=2026-01-08T12:00:00Z&future_minutes=10&min_percent_change=3&direction=up&use_engineered_features=true&use_flag_features=true&scale_pos_weight=50" 2>&1 | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null)

echo "Job ID: $JOB_ID"
echo "Warte auf Job-Abschluss..."

for i in {1..30}; do
    STATUS=$(curl -s http://localhost:3002/api/queue/$JOB_ID 2>&1 | python3 -c "import sys, json; j=json.load(sys.stdin); print(j.get('status'))" 2>/dev/null)
    if [ "$STATUS" = "COMPLETED" ] || [ "$STATUS" = "FAILED" ]; then
        echo "Status: $STATUS"
        break
    fi
    sleep 2
done

MODEL_ID=$(curl -s http://localhost:3002/api/queue/$JOB_ID 2>&1 | python3 -c "import sys, json; print(json.load(sys.stdin).get('result_model_id', 'N/A'))" 2>/dev/null)

if [ "$MODEL_ID" != "N/A" ] && [ "$MODEL_ID" != "None" ]; then
    curl -s http://localhost:3002/api/models/$MODEL_ID > /tmp/model_flag_test.json
    python3 << 'PYEOF'
import json
with open('/tmp/model_flag_test.json', 'r') as f:
    m = json.load(f)

features = m.get('features', [])
selected_engineered = ['price_change_5', 'price_change_10', 'volume_spike_5']
expected_flags = [f"{feat}_has_data" for feat in selected_engineered]

used_flags = [f for f in features if '_has_data' in f]
expected_used = [f for f in used_flags if f in expected_flags]
unexpected_used = [f for f in used_flags if f not in expected_flags]

print(f"\n=== ERGEBNIS ===")
print(f"Flag-Features verwendet: {len(used_flags)}")
print(f"  ✅ Erwartete: {len(expected_used)}")
print(f"  ⚠️ Unerwartete: {len(unexpected_used)}")
print()

if unexpected_used:
    print("❌ FEHLER: Unerwartete Flag-Features werden verwendet!")
    print(f"   Erwartet: {expected_flags}")
    print(f"   Gefunden: {sorted(unexpected_used)[:5]}...")
    exit(1)
else:
    print("✅ PERFEKT! Nur Flag-Features für ausgewählte Engineering-Features werden verwendet!")
    print(f"   {sorted(expected_used)}")
    exit(0)
PYEOF
    TEST_RESULT=$?
    exit $TEST_RESULT
else
    echo "⚠️ Modell noch nicht erstellt"
    exit 1
fi
