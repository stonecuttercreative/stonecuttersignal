# BEGIN stonecutter extension: sqlite persistence
import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from ..settings import settings

_db_initialized = False

def init_db():
    """Initialize SQLite database with required tables."""
    global _db_initialized
    if _db_initialized:
        return
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(settings.db_path) if os.path.dirname(settings.db_path) else '.', exist_ok=True)
        
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        
        # Create runs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                ts INTEGER,
                mode TEXT,
                brand TEXT,
                category TEXT,
                audience TEXT,
                channels TEXT,
                confidence INTEGER,
                consensus INTEGER,
                diversity INTEGER,
                story TEXT
            )
        ''')
        
        # Create scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                run_id TEXT,
                key TEXT,
                value INTEGER,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
        ''')
        
        # Create providers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS providers (
                run_id TEXT,
                name TEXT,
                model TEXT,
                latency_ms INTEGER,
                is_mock INTEGER,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        _db_initialized = True
        
    except Exception as e:
        # Silent fail - continue without persistence if DB unavailable
        print(f"Warning: Could not initialize database: {e}")

def save_run(run_dict: Dict[str, Any]):
    """Save run record to database with UPSERT behavior."""
    if not settings.persistence_enabled:
        return
    
    try:
        init_db()
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        
        # Extract main run data
        run_id = run_dict.get('id', '')
        ts = run_dict.get('timestamp', 0)
        mode = run_dict.get('mode', '')
        brand = run_dict.get('brand', '')
        category = run_dict.get('category', '')
        audience = run_dict.get('audience', '')
        channels = run_dict.get('channels', '')
        
        # Extract signal scores
        signal_scores = run_dict.get('meta', {}).get('signal_scores', {})
        confidence = signal_scores.get('confidence', 0)
        consensus = signal_scores.get('consensus', 0)
        diversity = signal_scores.get('diversity', 0)
        
        story = run_dict.get('story', '')[:280]  # Truncate to 280 chars
        
        # UPSERT run record
        cursor.execute('''
            INSERT OR REPLACE INTO runs 
            (id, ts, mode, brand, category, audience, channels, confidence, consensus, diversity, story)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, ts, mode, brand, category, audience, channels, confidence, consensus, diversity, story))
        
        # Clear existing scores and providers for this run
        cursor.execute('DELETE FROM scores WHERE run_id = ?', (run_id,))
        cursor.execute('DELETE FROM providers WHERE run_id = ?', (run_id,))
        
        # Insert scores
        scores = run_dict.get('scores', {})
        for key, value in scores.items():
            cursor.execute('INSERT INTO scores (run_id, key, value) VALUES (?, ?, ?)', 
                         (run_id, key, int(value) if isinstance(value, (int, float)) else 0))
        
        # Insert providers
        providers = run_dict.get('providers', [])
        for provider in providers:
            name = provider.get('provider', '')
            model = provider.get('model', '')
            latency_ms = provider.get('latency_ms', 0)
            is_mock = 1 if (model == 'mock' or not provider.get('latency_ms')) else 0
            
            cursor.execute('''
                INSERT INTO providers (run_id, name, model, latency_ms, is_mock)
                VALUES (?, ?, ?, ?, ?)
            ''', (run_id, name, model, latency_ms, is_mock))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        # Silent fail - continue without persistence if DB unavailable
        print(f"Warning: Could not save run to database: {e}")

def last_runs(limit: int = 50) -> List[Dict[str, Any]]:
    """Get last N runs with basic info."""
    if not settings.persistence_enabled:
        return []
    
    try:
        init_db()
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, ts, mode, brand, category, audience, channels, 
                   confidence, consensus, diversity, story
            FROM runs 
            ORDER BY ts DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'timestamp': row[1],
                'mode': row[2],
                'brand': row[3],
                'category': row[4],
                'audience': row[5],
                'channels': row[6],
                'confidence': row[7],
                'consensus': row[8],
                'diversity': row[9],
                'story': row[10]
            })
        
        return results
        
    except Exception as e:
        print(f"Warning: Could not fetch runs from database: {e}")
        return []

def get_run_details(run_id: str) -> Optional[Dict[str, Any]]:
    """Get full run details including scores and providers."""
    if not settings.persistence_enabled:
        return None
    
    try:
        init_db()
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        
        # Get main run data
        cursor.execute('''
            SELECT id, ts, mode, brand, category, audience, channels,
                   confidence, consensus, diversity, story
            FROM runs WHERE id = ?
        ''', (run_id,))
        
        run_row = cursor.fetchone()
        if not run_row:
            conn.close()
            return None
        
        # Get scores
        cursor.execute('SELECT key, value FROM scores WHERE run_id = ?', (run_id,))
        scores_rows = cursor.fetchall()
        scores = {row[0]: row[1] for row in scores_rows}
        
        # Get providers
        cursor.execute('SELECT name, model, latency_ms, is_mock FROM providers WHERE run_id = ?', (run_id,))
        providers_rows = cursor.fetchall()
        providers = [
            {
                'provider': row[0],
                'model': row[1],
                'latency_ms': row[2],
                'is_mock': bool(row[3])
            }
            for row in providers_rows
        ]
        
        conn.close()
        
        return {
            'id': run_row[0],
            'timestamp': run_row[1],
            'mode': run_row[2],
            'brand': run_row[3],
            'category': run_row[4],
            'audience': run_row[5],
            'channels': run_row[6],
            'signal_scores': {
                'confidence': run_row[7],
                'consensus': run_row[8],
                'diversity': run_row[9]
            },
            'story': run_row[10],
            'scores': scores,
            'providers': providers
        }
        
    except Exception as e:
        print(f"Warning: Could not fetch run details: {e}")
        return None
# END stonecutter extension