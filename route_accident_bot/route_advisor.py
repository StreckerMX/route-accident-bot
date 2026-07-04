"""Compara rutas y genera recomendación de cambio."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from .traffic_analyzer import RouteAnalysis


@dataclass
class RouteComparison:
    label: str
    duration_minutes: int
    delay_minutes: int
    distance_km: float
    has_severe_jam: bool
    is_primary: bool


@dataclass
class Recommendation:
    action: str
    reason: str
    best_route_label: str
    minutes_saved: int
    maps_url: str


def build_maps_url(origin: str, destination: str) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={quote(origin)}"
        f"&destination={quote(destination)}"
        "&travelmode=driving"
    )


def build_maps_point_url(lat: float, lng: float, zoom: int = 17) -> str:
    return (
        "https://www.google.com/maps/search/?api=1"
        f"&query={lat:.6f},{lng:.6f}"
        f"&zoom={zoom}"
    )


def compare_routes(analyses: list[RouteAnalysis]) -> list[RouteComparison]:
    comparisons = []
    for analysis in analyses:
        comparisons.append(
            RouteComparison(
                label=analysis.route_label,
                duration_minutes=analysis.duration_minutes,
                delay_minutes=analysis.delay_minutes,
                distance_km=analysis.distance_km,
                has_severe_jam=analysis.has_severe_jam,
                is_primary=analysis.route_index == 0,
            )
        )
    return comparisons


def recommend(
    analyses: list[RouteAnalysis],
    origin: str,
    destination: str,
    switch_threshold_minutes: int,
) -> Recommendation:
    if not analyses:
        return Recommendation(
            action="MANTENER_RUTA",
            reason="No se obtuvieron rutas de la API.",
            best_route_label="N/A",
            minutes_saved=0,
            maps_url=build_maps_url(origin, destination),
        )

    primary = analyses[0]
    best = min(analyses, key=lambda a: a.duration_minutes)
    minutes_saved = primary.duration_minutes - best.duration_minutes

    if (
        primary.has_severe_jam
        and best.route_index != 0
        and minutes_saved >= switch_threshold_minutes
        and not best.has_severe_jam
    ):
        return Recommendation(
            action="CAMBIAR_RUTA",
            reason=(
                f"La ruta alternativa '{best.route_label}' ahorra ~{minutes_saved} min "
                f"y no muestra atascos severos."
            ),
            best_route_label=best.route_label,
            minutes_saved=minutes_saved,
            maps_url=build_maps_url(origin, destination),
        )

    if primary.has_severe_jam and minutes_saved >= switch_threshold_minutes // 2:
        return Recommendation(
            action="CONSIDERAR_ALTERNATIVA",
            reason=(
                f"Hay congestión en la ruta principal. '{best.route_label}' podría ahorrar "
                f"~{minutes_saved} min, pero conviene validar condiciones actuales."
            ),
            best_route_label=best.route_label,
            minutes_saved=minutes_saved,
            maps_url=build_maps_url(origin, destination),
        )

    if primary.has_severe_jam:
        return Recommendation(
            action="CONSIDERAR_ALTERNATIVA",
            reason="Hay congestión significativa, pero las alternativas no ofrecen mejora clara.",
            best_route_label=primary.route_label,
            minutes_saved=0,
            maps_url=build_maps_url(origin, destination),
        )

    return Recommendation(
        action="MANTENER_RUTA",
        reason="La ruta principal está dentro de parámetros aceptables.",
        best_route_label=primary.route_label,
        minutes_saved=0,
        maps_url=build_maps_url(origin, destination),
    )