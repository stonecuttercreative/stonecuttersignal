# BEGIN stonecutter live: gdelt
from typing import List, Dict
import httpx
from ..settings import settings
from .base import DataSource

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

class GDELT(DataSource):
    name = "gdelt"
    async def fetch(self, query: str) -> List[Dict]:
        if not settings.enable_gdelt:
            return []
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_s) as client:
                r = await client.get(GDELT_URL, params={"query": query, "mode":"ArtList","format":"JSON","maxrecords":20})
                r.raise_for_status()
                arts = r.json().get("articles", [])
                out=[]
                for a in arts[:12]:
                    out.append({
                        "title": a.get("title"),
                        "url": a.get("url"),
                        "snippet": (a.get("seendate") or "")[:120],
                        "source": a.get("domain"),
                        "provider": self.name,
                    })
                return out
        except Exception:
            return []
# END stonecutter live: gdelt