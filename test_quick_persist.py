# BEGIN stonecutter extension: quick persistence test
"""
Quick test to verify persistence is working
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stonecutter.persistence.sqlite_store import save_run, last_runs, init_db
from stonecutter.settings import settings
import uuid
import time

print("=== Quick Persistence Test ===")
print(f"Database path: {settings.db_path}")

# Initialize
init_db()

# BEGIN stonecutter fix: ts-seconds
# Create test record
test_record = {
    'id': str(uuid.uuid4()),
    'ts': int(time.time()),  # store seconds since epoch
    'timestamp': int(time.time()),
# END stonecutter fix: ts-seconds
    'mode': 'test',
    'brand': 'TestBrand',
    'category': 'TestCategory',
    'audience': 'Test Audience',
    'channels': 'Test Channels',
    'scores': {'cultural_fit': 80, 'clarity': 90},
    'meta': {
        'signal_scores': {
            'confidence': 85,
            'consensus': 90,
            'diversity': 10
        }
    },
    'story': 'Test story for persistence',
    'providers': [{'provider': 'test', 'model': 'test-model', 'latency_ms': 100}]
}

print(f"Saving test record: {test_record['id'][:8]}")
save_run(test_record)

print("Retrieving records...")
runs = last_runs(5)
print(f"Found {len(runs)} runs")

for run in runs:
    print(f"  - {run['id'][:8]} | {run['brand']} | conf:{run['confidence']}")

print("✓ Persistence test complete")
# END stonecutter extension