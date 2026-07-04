"""Geocodificación inversa con Google Geocoding API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


@dataclass
class LocationInfo:
    formatted_address: str
    road: str
    neighborhood: str
    city: str
    state: str


def _extract_component(components: list[dict[str, Any]], type_name: str) -> str:
    for comp in components:
        if type_name in comp.get("types", []):
            return comp.get("long_name", "")
    return ""


class Geocoder:
    def __init__(self, api_key: str, language: str = "es"):
        self.api_key = api_key
        self.language = language

    def reverse(self, lat: float, lng: float) -> LocationInfo:
        response = requests.get(
            GEOCODE_URL,
            params={
                "latlng": f"{lat},{lng}",
                "key": self.api_key,
                "language": self.language,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return LocationInfo(
                formatted_address=f"{lat:.5f}, {lng:.5f}",
                road="",
                neighborhood="",
                city="",
                state="",
            )

        result = data["results"][0]
        components = result.get("address_components", [])

        road = _extract_component(components, "route")
        if not road:
            road = _extract_component(components, "street_address")

        return LocationInfo(
            formatted_address=result.get("formatted_address", ""),
            road=road,
            neighborhood=_extract_component(components, "sublocality")
            or _extract_component(components, "neighborhood"),
            city=_extract_component(components, "locality")
            or _extract_component(components, "administrative_area_level_2"),
            state=_extract_component(components, "administrative_area_level_1"),
        )