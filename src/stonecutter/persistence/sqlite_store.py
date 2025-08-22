# BEGIN stonecutter extension: sqlite harden
import sqlite3
import json
import time
import uuid
import os
from typing import Dict, Any, List, Optional
from ..settings import settings
from ..logging_conf import logger

_CONN = None

def init_db():
    """Initialize SQLite database with required tables."""
    global _CONN
    if _CONN:
        return _CONN
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
        
        _CONN = sqlite3.connect(settings.db_path, isolation_level=None, check_same_thread=False)
        cur = _CONN.cursor()
        
        # Create tables if not exist
        cur.execute("""CREATE TABLE IF NOT EXISTS runs(
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
        )""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS scores(
            run_id TEXT, 
            key TEXT, 
            value INTEGER
        )""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS providers(
            run_id TEXT, 
            name TEXT, 
            model TEXT, 
            latency_ms INTEGER, 
            is_mock INTEGER
        )""")
        
        logger.info(f"Database initialized at {settings.db_path}")
        return _CONN
        
    except Exception as e:
        logger.error(f"[persistence] Database initialization failed: {e}")
        return None

def save_run(rec: Dict[str, Any]):
    """Save run record to database with robust error handling."""
    if not settings.persistence_enabled:
        return
    
    try:
        conn = init_db()
        if not conn:
            logger.error("[persistence] No database connection available")
            return
            
        cur = conn.cursor()
        
        # Extract and validate required fields
        run_id = rec.get("id", str(uuid.uuid4()))
        ts = rec.get("ts", rec.get("timestamp", int(time.time() * 1000)))
        mode = rec.get("mode", "")
        brand = rec.get("brand", "")
        category = rec.get("category", "")
        audience = rec.get("audience", "")
        channels = rec.get("channels", "")
        
        # Extract signal scores safely
        meta = rec.get("meta", {})
        signal_scores = meta.get("signal_scores", {})
        confidence = int(signal_scores.get("confidence", 0))
        consensus = int(signal_scores.get("consensus", 0))
        diversity = int(signal_scores.get("diversity", 0))
        story = (rec.get("story") or "")[:280]
        
        # Insert/replace run record
        cur.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
            run_id, ts, mode, brand, category, audience, channels, 
            confidence, consensus, diversity, story
        ))
        
        # Clear existing related records
        cur.execute("DELETE FROM scores WHERE run_id = ?", (run_id,))
        cur.execute("DELETE FROM providers WHERE run_id = ?", (run_id,))
        
        # Insert scores
        for k, v in rec.get("scores", {}).items():
            cur.execute("INSERT INTO scores(run_id,key,value) VALUES(?,?,?)", 
                       (run_id, k, int(v) if isinstance(v, (int, float)) else 0))
        
        # Insert providers
        for p in rec.get("providers", []):
            provider_name = p.get("provider", "")
            model = p.get("model", "")
            latency_ms = p.get("latency_ms", 0)
            is_mock = 1 if (model == "mock" or model is None) else 0
            
            cur.execute("INSERT INTO providers(run_id,name,model,latency_ms,is_mock) VALUES(?,?,?,?,?)", (
                run_id, provider_name, model, latency_ms, is_mock
            ))
        
        logger.info(f"[persistence] Successfully saved run {run_id}")
        
    except Exception as e:
        logger.error(f"[persistence] save_run failed: {e}")

def last_runs(limit: int = 50) -> List[Dict[str, Any]]:
    """Get last N runs with basic info."""
    if not settings.persistence_enabled:
        return []
    
    try:
        conn = init_db()
        if not conn:
            return []
            
        cur = conn.cursor()
        cur.execute("SELECT id, ts, brand, category, audience, channels, confidence, consensus, diversity FROM runs ORDER BY ts DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        
        results = [
            {
                "id": r[0], 
                "timestamp": r[1], 
                "brand": r[2], 
                "category": r[3], 
                "audience": r[4], 
                "channels": r[5],
                "confidence": r[6], 
                "consensus": r[7], 
                "diversity": r[8]
            }
            for r in rows
        ]
        
        logger.info(f"[persistence] Retrieved {len(results)} runs from database")
        return results
        
    except Exception as e:
        logger.error(f"[persistence] last_runs failed: {e}")
        return []

def get_run_details(run_id: str) -> Optional[Dict[str, Any]]:
    """Get full run details including scores and providers."""
    if not settings.persistence_enabled:
        return None
    
    try:
        conn = init_db()
        if not conn:
            return None
            
        cur = conn.cursor()
        
        # Get main run data
        cur.execute('''
            SELECT id, ts, mode, brand, category, audience, channels,
                   confidence, consensus, diversity, story
            FROM runs WHERE id = ?
        ''', (run_id,))
        
        run_row = cur.fetchone()
        if not run_row:
            return None
        
        # Get scores
        cur.execute('SELECT key, value FROM scores WHERE run_id = ?', (run_id,))
        scores_rows = cur.fetchall()
        scores = {row[0]: row[1] for row in scores_rows}
        
        # Get providers
        cur.execute('SELECT name, model, latency_ms, is_mock FROM providers WHERE run_id = ?', (run_id,))
        providers_rows = cur.fetchall()
        providers = [
            {
                'provider': row[0],
                'model': row[1],
                'latency_ms': row[2],
                'is_mock': bool(row[3])
            }
            for row in providers_rows
        ]
        
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
        logger.error(f"[persistence] get_run_details failed: {e}")
        return None
# END stonecutter extension: sqlite harden