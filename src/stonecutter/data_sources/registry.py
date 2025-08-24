# BEGIN stonecutter live: data registry
from typing import List
from .newsapi import NewsAPI
from .gdelt import GDELT

def load_sources() -> List:
    src = []
    try: src.append(NewsAPI())
    except Exception: pass
    try: src.append(GDELT())
    except Exception: pass
    return src
# END stonecutter live: data registry