# BEGIN stonecutter live: data base
from typing import List, Dict

class DataSource:
    name: str = "base"
    async def fetch(self, query: str) -> List[Dict]: ...
# END stonecutter live: data base