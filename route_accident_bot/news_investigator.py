"""Investiga noticias recientes relacionadas con un atasco o posible accidente."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from duckduckgo_search import DDGS

from .google_geocoder import LocationInfo


@dataclass
class NewsItem:
    title: str
    snippet: str
    url: str
    source: str
    age_label: str = ""


def _parse_news_age_hours(date_str: str) -> float | None:
    if not date_str:
        return None

    relative = re.search(
        r"(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs|hora|horas|minuto|minutos)\s+ago",
        date_str,
        re.IGNORECASE,
    )
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2).lower()
        if unit.startswith("min"):
            return amount / 60
        return float(amount)

    try:
        normalized = date_str.replace("Z", "+00:00")
        published = datetime.fromisoformat(normalized)
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - published).total_seconds()
        if age_seconds < 0:
            return 0.0
        return age_seconds / 3600
    except ValueError:
        return None


def _format_age_label(date_str: str) -> str:
    hours = _parse_news_age_hours(date_str)
    if hours is None:
        return ""
    if hours < 1:
        return f"hace {int(hours * 60)} min"
    return f"hace {hours:.1f} h"


class Investigator:
    def __init__(
        self,
        search_queries: list[str],
        max_results: int = 5,
        region: str = "mx-es",
        max_age_hours: float = 2.0,
    ):
        self.search_queries = search_queries
        self.max_results = max_results
        self.region = region
        self.max_age_hours = max_age_hours

    def _is_recent(self, result: dict) -> bool:
        age_hours = _parse_news_age_hours(str(result.get("date", "")))
        if age_hours is None:
            return False
        return age_hours <= self.max_age_hours

    def search(self, location: LocationInfo) -> list[NewsItem]:
        road = location.road or location.formatted_address
        city = location.city or location.state or location.neighborhood

        if not road and not city:
            return []

        queries: list[str] = []
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
                    results = ddgs.news(
                        query,
                        region=self.region,
                        timelimit="d",
                        max_results=self.max_results * 3,
                    )
                except Exception:
                    results = []

                for result in results:
                    if not self._is_recent(result):
                        continue
                    url = result.get("url", result.get("href", ""))
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    date_str = str(result.get("date", ""))
                    items.append(
                        NewsItem(
                            title=result.get("title", "Sin titulo"),
                            snippet=result.get("body", result.get("snippet", "")),
                            url=url,
                            source=result.get("source", "Web"),
                            age_label=_format_age_label(date_str),
                        )
                    )
                    if len(items) >= self.max_results:
                        break

        return items