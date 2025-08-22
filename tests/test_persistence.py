# BEGIN stonecutter extension: persistence tests
import pytest
import os
import tempfile
import uuid
import time
from src.stonecutter.persistence.sqlite_store import save_run, last_runs, get_run_details, init_db
from src.stonecutter.persistence.jsonl import append_jsonl
from src.stonecutter.settings import settings

def test_save_and_retrieve_run():
    """Test saving a run record and retrieving it."""
    # Use temporary database for testing
    original_db_path = settings.db_path
    original_enabled = settings.persistence_enabled
    
    try:
        # Set up temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        settings.db_path = temp_db.name
        settings.persistence_enabled = True
        
        # Reset initialization flag
        import src.stonecutter.persistence.sqlite_store as store_module
        store_module._db_initialized = False
        
        # Create test run record
        run_id = str(uuid.uuid4())
        test_run = {
            'id': run_id,
            'timestamp': int(time.time()),
            'mode': 'test-mode',
            'brand': 'TestBrand',
            'category': 'TestCategory',
            'audience': 'Test Audience',
            'channels': 'Test Channels',
            'scores': {'cultural_fit': 75, 'clarity': 80},
            'meta': {
                'signal_scores': {
                    'confidence': 85,
                    'consensus': 90,
                    'diversity': 10
                }
            },
            'story': 'Test story for the campaign',
            'providers': [
                {
                    'provider': 'test_provider',
                    'model': 'test-model',
                    'latency_ms': 100,
                    'is_mock': False
                }
            ]
        }
        
        # Save run
        save_run(test_run)
        
        # Retrieve runs
        runs = last_runs(limit=10)
        assert len(runs) >= 1, "Should have at least one run"
        
        # Find our run
        saved_run = None
        for run in runs:
            if run['id'] == run_id:
                saved_run = run
                break
        
        assert saved_run is not None, f"Run {run_id} not found in results"
        assert saved_run['brand'] == 'TestBrand'
        assert saved_run['category'] == 'TestCategory'
        assert saved_run['confidence'] == 85
        
        # Get full details
        details = get_run_details(run_id)
        assert details is not None, "Should retrieve run details"
        assert details['scores']['cultural_fit'] == 75
        assert details['scores']['clarity'] == 80
        assert len(details['providers']) == 1
        assert details['providers'][0]['provider'] == 'test_provider'
        
    finally:
        # Cleanup
        settings.db_path = original_db_path
        settings.persistence_enabled = original_enabled
        try:
            os.unlink(temp_db.name)
        except:
            pass

def test_jsonl_append():
    """Test JSONL logging functionality."""
    temp_dir = tempfile.mkdtemp()
    jsonl_path = os.path.join(temp_dir, 'test_logs.jsonl')
    
    try:
        # Test data
        test_record = {
            'id': str(uuid.uuid4()),
            'timestamp': int(time.time()),
            'test_field': 'test_value'
        }
        
        # Append to JSONL
        append_jsonl(jsonl_path, test_record)
        
        # Verify file exists and contains data
        assert os.path.exists(jsonl_path), "JSONL file should exist"
        
        with open(jsonl_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1, "Should have one line"
        
        # Parse the JSON line
        import json
        parsed = json.loads(lines[0].strip())
        assert parsed['id'] == test_record['id']
        assert parsed['test_field'] == 'test_value'
        
    finally:
        # Cleanup
        try:
            os.unlink(jsonl_path)
            os.rmdir(temp_dir)
        except:
            pass

def test_persistence_disabled():
    """Test that operations succeed gracefully when persistence is disabled."""
    original_enabled = settings.persistence_enabled
    
    try:
        settings.persistence_enabled = False
        
        # These should all succeed without error
        save_run({'id': 'test', 'timestamp': int(time.time())})
        runs = last_runs()
        assert runs == [], "Should return empty list when disabled"
        
        details = get_run_details('nonexistent')
        assert details is None, "Should return None when disabled"
        
    finally:
        settings.persistence_enabled = original_enabled
# END stonecutter extension