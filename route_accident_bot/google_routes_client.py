"""Cliente para Google Routes API v2."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import requests

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

FIELD_MASK = ",".join([
    "routes.duration",
    "routes.staticDuration",
    "routes.distanceMeters",
    "routes.warnings",
    "routes.routeLabels",
    "routes.travelAdvisory.speedReadingIntervals",
    "routes.polyline.encodedPolyline",
    "routes.legs.steps.navigationInstruction",
    "routes.legs.steps.startLocation",
    "routes.legs.travelAdvisory.speedReadingIntervals",
    "routes.legs.polyline.encodedPolyline",
])


def _parse_duration_seconds(value: str | None) -> int:
    if not value:
        return 0
    match = re.fullmatch(r"(\d+)s", value.strip())
    return int(match.group(1)) if match else 0


class RoutesClient:
    def __init__(self, api_key: str, language_code: str = "es-MX"):
        self.api_key = api_key
        self.language_code = language_code

    def compute_routes(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "DRIVE",
        compute_alternatives: bool = True,
        avoid_tolls: bool = False,
    ) -> list[dict[str, Any]]:
        body = {
            "origin": {"address": origin},
            "destination": {"address": destination},
            "travelMode": travel_mode,
            "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
            "extraComputations": ["TRAFFIC_ON_POLYLINE"],
            "computeAlternativeRoutes": compute_alternatives,
            "routeModifiers": {
                "avoidTolls": avoid_tolls,
                "avoidFerries": False,
            },
            "departureTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "languageCode": self.language_code,
            "units": "METRIC",
        }

        response = requests.post(
            ROUTES_URL,
            json=body,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": FIELD_MASK,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("routes", [])

    @staticmethod
    def route_duration_minutes(route: dict[str, Any]) -> int:
        return _parse_duration_seconds(route.get("duration")) // 60

    @staticmethod
    def route_delay_minutes(route: dict[str, Any]) -> int:
        duration = _parse_duration_seconds(route.get("duration"))
        static_duration = _parse_duration_seconds(route.get("staticDuration"))
        return max(0, (duration - static_duration) // 60)

    @staticmethod
    def route_distance_km(route: dict[str, Any]) -> float:
        meters = route.get("distanceMeters", 0)
        return round(meters / 1000, 1)

    @staticmethod
    def route_label(route: dict[str, Any], index: int) -> str:
        labels = route.get("routeLabels", [])
        if "DEFAULT_ROUTE" in labels:
            return "Ruta principal"
        if "DEFAULT_ROUTE_ALTERNATE" in labels:
            return f"Alternativa {index}"
        return f"Ruta {index + 1}"