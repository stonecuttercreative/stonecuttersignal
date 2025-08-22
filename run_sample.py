# BEGIN stonecutter extension: sample seeding
"""
Sample data seeding script for Stonecutter Signal Dashboard

This script runs several example campaign briefs through the full pipeline
to populate the dashboard with sample data for testing and demonstration.
"""

import asyncio
import json
import time
import logging
from pprint import pprint

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the main function from stonecutter module
try:
    from stonecutter import run_signal_engine
except ImportError as e:
    logger.error(f"Could not import run_signal_engine: {e}")
    raise SystemExit(1)

SAMPLES = [
    {
        "brand": "Acme Bank",
        "category": "Finance", 
        "concept": "Clarity-first crypto education campaign focused on real risks and safe on-ramps.",
        "mode": "realtime",
        "audience": "Adults 25-45 seeking stability",
        "channels": "YouTube, CTV, OOH"
    },
    {
        "brand": "Drift",
        "category": "Wellness",
        "concept": "Short social stories about finding calm during market noise.",
        "mode": "realtime", 
        "audience": "GenZ + Millennials who track markets",
        # no channels → distribution_fit omitted, note recorded
    },
    {
        "brand": "Volt EV",
        "category": "Automotive",
        "concept": "Sustainability hero film with social cutdowns featuring owners' real experiences.",
        "mode": "realtime",
        "audience": "Eco‑conscious professionals", 
        "channels": "Instagram, TikTok, YouTube"
    },
    {
        "brand": "Nimble",
        "category": "Productivity",
        "concept": "Launch narrative for an AI meeting assistant that prioritizes privacy and clarity over hype.",
        "mode": "realtime",
        "audience": "Tech professionals and remote workers",
        "channels": "LinkedIn, YouTube, Podcast"
    },
]

def _run_one(payload):
    """Run a single brief through the engine and return results."""
    t0 = time.time()
    
    try:
        # Use the payload directly as dict or string
        # run_signal_engine handles both formats
        out = run_signal_engine(payload, interactive_mode=False)
        
        dt = int((time.time() - t0) * 1000)
        meta = out.get("meta", {}) or {}
        sig = meta.get("signal_scores", {}) or {}
        brand = (payload["brand"] if isinstance(payload, dict) and "brand" in payload else "(legacy/plain)")
        
        print(f"\n=== {brand} | {dt} ms ===")
        print(f"confidence={sig.get('confidence')}  consensus={sig.get('consensus')}  diversity={sig.get('diversity')}")
        
        # Print a compact view of providers (if surfaced)
        provs = out.get("providers") or []
        if provs:
            print("providers:", ", ".join([p.get("provider") or "?" for p in provs]))
        
        # Print scores compactly
        scores_str = json.dumps(out.get("scores", {}), ensure_ascii=False)
        if len(scores_str) > 400:
            scores_str = scores_str[:400] + "..."
        print(f"scores: {scores_str}\n")
        
        return out
        
    except Exception as e:
        logger.error(f"Error running brief for {payload}: {e}")
        print(f"\n=== ERROR: {payload} ===")
        print(f"Error: {e}\n")
        return None

def main():
    """Main function to run all sample briefs."""
    print("🔍 Starting Stonecutter Signal sample seeding...")
    print("This will run several example briefs through the full pipeline.\n")
    
    # Also include a legacy/plain brief to check backward compatibility
    legacy_brief = "A plain string brief about a clarity-over-hype crypto PSA targeting millennials through social media."
    SAMPLES.append(legacy_brief)
    
    # Check if the engine function is available
    try:
        # Test import worked
        print("✓ Engine function available")
    except Exception as e:
        logger.error(f"Could not access engine: {e}")
        return 1
    
    # Run all samples
    outs = []
    successful = 0
    
    for i, sample in enumerate(SAMPLES, 1):
        print(f"\n--- Running sample {i}/{len(SAMPLES)} ---")
        try:
            result = _run_one(sample)
            if result:
                outs.append(result)
                successful += 1
        except Exception as e:
            logger.error(f"Sample {i} failed: {e}")
            continue
    
    print(f"\n🎉 Completed seeding!")
    print(f"✓ Successfully processed: {successful}/{len(SAMPLES)} briefs")
    print(f"✓ Results stored: {len(outs)} entries")
    
    if successful > 0:
        print("\n📊 Dashboard should now show populated data:")
        print("  • Open http://localhost:8000/ to view the dashboard")
        print("  • Check /runs JSON endpoint for API data") 
        print("  • SQLite database and JSONL logs should contain new entries")
        
        # Try to show a quick summary
        try:
            from src.stonecutter.persistence.sqlite_store import last_runs
            recent = last_runs(limit=10)
            print(f"  • Database contains {len(recent)} recent runs")
        except Exception:
            print("  • Could not check database status")
    else:
        print("\n⚠️  No successful runs - check logs for errors")
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
# END stonecutter extension: sample seeding