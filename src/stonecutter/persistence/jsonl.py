# BEGIN stonecutter extension: JSONL logging
import json
import os
from typing import Dict, Any
from ..settings import settings

def append_jsonl(path: str, obj: Dict[str, Any]):
    """Append object as JSON line to file."""
    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Append compact JSON line
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '\n')
            
    except Exception as e:
        # Silent fail - continue without JSONL logging if unavailable
        print(f"Warning: Could not write to JSONL: {e}")
# END stonecutter extension