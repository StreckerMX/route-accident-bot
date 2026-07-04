"""Analiza tráfico y detecta atascos severos en una ruta."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import polyline


@dataclass
class TrafficEvent:
    speed: str
    start_index: int
    end_index: int
    lat: float
    lng: float
    road_hint: str = ""
    severity: str = "BAJA"


@dataclass
class RouteAnalysis:
    route_index: int
    route_label: str
    duration_minutes: int
    delay_minutes: int
    distance_km: float
    warnings: list[str] = field(default_factory=list)
    events: list[TrafficEvent] = field(default_factory=list)
    has_severe_jam: bool = False


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _decode_polyline(encoded: str) -> list[tuple[float, float]]:
    if not encoded:
        return []
    return polyline.decode(encoded)


def _midpoint_coords(
    points: list[tuple[float, float]], start: int, end: int
) -> tuple[float, float]:
    if not points:
        return 0.0, 0.0
    start = max(0, min(start, len(points) - 1))
    end = max(start + 1, min(end, len(points)))
    segment = points[start:end]
    if not segment:
        return points[start]
    mid = len(segment) // 2
    return segment[mid]


def _segment_length_km(
    points: list[tuple[float, float]], start: int, end: int
) -> float:
    if len(points) < 2:
        return 0.0
    start = max(0, min(start, len(points) - 1))
    end = max(start + 1, min(end, len(points)))
    total = 0.0
    for i in range(start, end - 1):
        lat1, lng1 = points[i]
        lat2, lng2 = points[i + 1]
        total += _haversine_km(lat1, lng1, lat2, lng2)
    return total


def _road_hint_from_steps(route: dict[str, Any], lat: float, lng: float) -> str:
    best_hint = ""
    best_dist = float("inf")
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            loc = step.get("startLocation", {}).get("latLng", {})
            step_lat = loc.get("latitude")
            step_lng = loc.get("longitude")
            if step_lat is None or step_lng is None:
                continue
            dist = _haversine_km(lat, lng, step_lat, step_lng)
            if dist < best_dist:
                instruction = step.get("navigationInstruction", {})
                best_hint = instruction.get("instructions", "")
                best_dist = dist
    return best_hint


def _severity(speed: str, delay_minutes: int, segment_km: float) -> str:
    if speed == "TRAFFIC_JAM" and (delay_minutes >= 15 or segment_km >= 2):
        return "ALTA"
    if speed == "TRAFFIC_JAM" or (speed == "SLOW" and delay_minutes >= 10):
        return "MEDIA"
    return "BAJA"


def analyze_route(
    route: dict[str, Any],
    route_index: int,
    route_label: str,
    duration_minutes: int,
    delay_minutes: int,
    distance_km: float,
    delay_threshold_minutes: int,
) -> RouteAnalysis:
    encoded = route.get("polyline", {}).get("encodedPolyline", "")
    points = _decode_polyline(encoded)

    intervals = []
    advisory = route.get("travelAdvisory", {})
    intervals.extend(advisory.get("speedReadingIntervals", []))
    for leg in route.get("legs", []):
        leg_advisory = leg.get("travelAdvisory", {})
        intervals.extend(leg_advisory.get("speedReadingIntervals", []))

    events: list[TrafficEvent] = []
    seen = set()

    for interval in intervals:
        speed = interval.get("speed", "NORMAL")
        if speed not in ("SLOW", "TRAFFIC_JAM"):
            continue

        start = interval.get("startPolylinePointIndex", 0)
        end = interval.get("endPolylinePointIndex", start + 1)
        key = (speed, start, end)
        if key in seen:
            continue
        seen.add(key)

        segment_km = _segment_length_km(points, start, end)
        if speed == "SLOW" and segment_km < 0.3:
            continue

        lat, lng = _midpoint_coords(points, start, end)
        severity = _severity(speed, delay_minutes, segment_km)
        road_hint = _road_hint_from_steps(route, lat, lng)

        events.append(
            TrafficEvent(
                speed=speed,
                start_index=start,
                end_index=end,
                lat=lat,
                lng=lng,
                road_hint=road_hint,
                severity=severity,
            )
        )

    events.sort(
        key=lambda e: {"ALTA": 0, "MEDIA": 1, "BAJA": 2}.get(e.severity, 3)
    )

    has_severe = delay_minutes >= delay_threshold_minutes and any(
        e.speed == "TRAFFIC_JAM" or e.severity in ("ALTA", "MEDIA") for e in events
    )

    return RouteAnalysis(
        route_index=route_index,
        route_label=route_label,
        duration_minutes=duration_minutes,
        delay_minutes=delay_minutes,
        distance_km=distance_km,
        warnings=route.get("warnings", []),
        events=events,
        has_severe_jam=has_severe,
    )