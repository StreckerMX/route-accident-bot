"""Investiga noticias relacionadas con un atasco o posible accidente."""

from __future__ import annotations

from dataclasses import dataclass

from duckduckgo_search import DDGS

from .google_geocoder import LocationInfo


@dataclass
class NewsItem:
    title: str
    snippet: str
    url: str
    source: str


class Investigator:
    def __init__(
        self,
        search_queries: list[str],
        max_results: int = 5,
        region: str = "mx-es",
    ):
        self.search_queries = search_queries
        self.max_results = max_results
        self.region = region

    def search(self, location: LocationInfo) -> list[NewsItem]:
        road = location.road or location.formatted_address
        city = location.city or location.state or location.neighborhood

        if not road and not city:
            return []

        queries = []
        for template in self.search_queries:
            query = template.format(road=road, city=city).strip()
            if query and query not in queries:
                queries.append(query)

        items: list[NewsItem] = []
        seen_urls: set[str] = set()

        with DDGS() as ddgs:
            for query in queries:
                if len(items) >= self.max_results:
                    break
                try:
                    results = ddgs.news(query, region=self.region, max_results=self.max_results)
                except Exception:
                    try:
                        results = ddgs.text(query, region=self.region, max_results=self.max_results)
                    except Exception:
                        continue

                for result in results:
                    url = result.get("url", result.get("href", ""))
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    items.append(
                        NewsItem(
                            title=result.get("title", "Sin título"),
                            snippet=result.get("body", result.get("snippet", "")),
                            url=url,
                            source=result.get("source", "Web"),
                        )
                    )
                    if len(items) >= self.max_results:
                        break

        return items