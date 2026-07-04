"""Parsea enlaces de Google Maps para extraer origen y destino."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

import requests

COORD_PATTERN = re.compile(r"^(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)$")
AT_COORD_PATTERN = re.compile(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


class GoogleMapsLinkError(Exception):
    """Error al interpretar un enlace de Google Maps."""


@dataclass
class ParsedRoute:
    origin: str
    destination: str
    origin_coords: tuple[float, float] | None = None
    destination_coords: tuple[float, float] | None = None


def _format_coords(lat: float, lng: float) -> str:
    return f"{lat:.5f}, {lng:.5f}"


def _parse_coord_string(value: str) -> tuple[float, float] | None:
    value = unquote(value).strip()
    match = COORD_PATTERN.match(value)
    if match:
        return float(match.group(1)), float(match.group(2))
    at_match = AT_COORD_PATTERN.search(value)
    if at_match:
        return float(at_match.group(1)), float(at_match.group(2))
    return None


def _label_from_value(value: str) -> tuple[str, tuple[float, float] | None]:
    coords = _parse_coord_string(value)
    if coords:
        return _format_coords(coords[0], coords[1]), coords
    return unquote(value.replace("+", " ")).strip(), None


def _resolve_short_url(url: str) -> str:
    if "goo.gl" not in url and "maps.app" not in url:
        return url
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=15,
            headers={"User-Agent": "RouteAccidentBot/1.0"},
        )
        return response.url
    except requests.RequestException as exc:
        raise GoogleMapsLinkError(f"No se pudo resolver el enlace corto: {exc}") from exc


def _extract_dir_segments(path: str) -> list[str]:
    if "/dir/" not in path:
        return []

    dir_part = path.split("/dir/", 1)[1]
    dir_part = dir_part.split("/@", 1)[0]

    segments: list[str] = []
    for segment in dir_part.split("/"):
        segment = segment.strip()
        if not segment or segment.startswith("data=") or segment.startswith("@"):
            break
        segments.append(unquote(segment.replace("+", " ")))
    return segments


def parse_location_label(value: str) -> tuple[str, tuple[float, float] | None]:
    """Interpreta un texto de ubicacion (nombre o coordenadas)."""
    return _label_from_value(value.strip())


def parse_google_maps_link(raw_url: str) -> ParsedRoute:
    url = raw_url.strip()
    if not url:
        raise GoogleMapsLinkError("El enlace esta vacio.")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    url = _resolve_short_url(url)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    origin_val: str | None = query.get("origin", [None])[0]
    dest_val: str | None = query.get("destination", [None])[0]

    if not origin_val:
        origin_val = query.get("saddr", [None])[0]
    if not dest_val:
        dest_val = query.get("daddr", [None])[0]

    if not origin_val or not dest_val:
        segments = _extract_dir_segments(parsed.path)
        if len(segments) >= 2:
            origin_val = origin_val or segments[0]
            dest_val = dest_val or segments[-1]

    if not origin_val or not dest_val:
        raise GoogleMapsLinkError(
            "No se pudo extraer origen y destino. "
            "Usa un enlace de ruta con al menos dos puntos (ej. /dir/Origen/Destino)."
        )

    origin_label, origin_coords = _label_from_value(origin_val)
    dest_label, dest_coords = _label_from_value(dest_val)

    if not origin_label or not dest_label:
        raise GoogleMapsLinkError("Origen o destino invalido en el enlace.")

    return ParsedRoute(
        origin=origin_label,
        destination=dest_label,
        origin_coords=origin_coords,
        destination_coords=dest_coords,
    )