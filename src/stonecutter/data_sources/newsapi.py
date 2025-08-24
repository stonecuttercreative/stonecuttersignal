# BEGIN stonecutter live: newsapi
from typing import List, Dict
import httpx
from ..settings import settings
from .base import DataSource

NEWS_URL = "https://newsapi.org/v2/everything"

class NewsAPI(DataSource):
    name = "newsapi"
    async def fetch(self, query: str) -> List[Dict]:
        if not settings.enable_newsapi or not settings.newsapi_key:
            return []
        params = {"q": query, "sortBy": "relevancy", "pageSize": 10, "language": "en"}
        headers = {"X-Api-Key": settings.newsapi_key}
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_s) as client:
                r = await client.get(NEWS_URL, params=params, headers=headers)
                r.raise_for_status()
                arts = r.json().get("articles", [])
                out = []
                for a in arts:
                    out.append({
                        "title": a.get("title"),
                        "url": a.get("url"),
                        "snippet": (a.get("description") or "")[:280],
                        "source": (a.get("source") or {}).get("name"),
                        "provider": self.name,
                    })
                return out
        except Exception:
            return []
# END stonecutter live: newsapi