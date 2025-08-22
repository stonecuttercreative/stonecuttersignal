# BEGIN stonecutter extension: check_db
"""
Database diagnostic script for Stonecutter Signal
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from stonecutter.persistence.sqlite_store import last_runs, init_db
    from stonecutter.settings import settings
    
    print("=== Stonecutter Signal Database Check ===")
    print(f"Database path: {settings.db_path}")
    print(f"Persistence enabled: {settings.persistence_enabled}")
    
    # Initialize database
    conn = init_db()
    if not conn:
        print("❌ Failed to initialize database")
        sys.exit(1)
    
    # Get recent runs
    rows = last_runs(10)
    print(f"\n📊 Recent runs: {len(rows)}")
    
    if rows:
        print("\nID | Brand | Category | Confidence | Consensus | Diversity")
        print("-" * 70)
        for r in rows:
            brand = (r.get("brand") or "Unknown")[:15]
            category = (r.get("category") or "Unknown")[:10]
            conf = r.get("confidence", 0)
            cons = r.get("consensus", 0)
            div = r.get("diversity", 0)
            run_id = r.get("id", "")[:8]
            print(f"{run_id} | {brand:15} | {category:10} | {conf:>10} | {cons:>9} | {div:>9}")
    else:
        print("No runs found in database")
        print("\nTry running: python run_sample.py")
    
    print(f"\nDatabase file exists: {os.path.exists(settings.db_path)}")
    if os.path.exists(settings.db_path):
        size = os.path.getsize(settings.db_path)
        print(f"Database size: {size} bytes")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to run: pip install -e .")
except Exception as e:
    print(f"❌ Error: {e}")
# END stonecutter extension: check_db