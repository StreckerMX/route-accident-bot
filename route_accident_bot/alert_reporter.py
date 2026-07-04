"""Genera reportes legibles en consola."""

from __future__ import annotations

from datetime import datetime

from .google_geocoder import LocationInfo
from .news_investigator import NewsItem
from .route_advisor import Recommendation, RouteComparison
from .traffic_analyzer import RouteAnalysis, TrafficEvent


def _speed_label(speed: str) -> str:
    return {
        "TRAFFIC_JAM": "atasco severo",
        "SLOW": "tráfico lento",
        "NORMAL": "normal",
    }.get(speed, speed)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_ok_check(timestamp: datetime, primary: RouteAnalysis) -> str:
    return (
        f"[{timestamp.strftime('%H:%M:%S')}] OK — "
        f"Ruta: {primary.duration_minutes} min "
        f"(+{primary.delay_minutes} min de retraso)"
    )


def format_alert(
    timestamp: datetime,
    primary: RouteAnalysis,
    main_event: TrafficEvent | None,
    location: LocationInfo,
    news: list[NewsItem],
    comparisons: list[RouteComparison],
    recommendation: Recommendation,
) -> str:
    lines = [
        "",
        "═" * 50,
        f"ALERTA DE TRÁFICO — {timestamp.strftime('%H:%M:%S')}",
        "═" * 50,
    ]

    if main_event:
        lines.append(f"Ubicación: {location.formatted_address}")
        if location.road:
            lines.append(f"Vía: {location.road}")
        lines.append(
            f"Condición: {_speed_label(main_event.speed)} (severidad {main_event.severity})"
        )
        if main_event.road_hint:
            lines.append(f"Instrucción: {main_event.road_hint}")
    else:
        lines.append(f"Ubicación: {location.formatted_address}")

    lines.append(
        f"Retraso estimado: +{primary.delay_minutes} min "
        f"(ruta total: {primary.duration_minutes} min)"
    )

    if primary.warnings:
        lines.append("")
        lines.append("Avisos de la API:")
        for warning in primary.warnings:
            lines.append(f"  • {warning}")

    lines.append("")
    lines.append("Investigación:")
    if news:
        for item in news:
            snippet = item.snippet[:160] + "..." if len(item.snippet) > 160 else item.snippet
            lines.append(f"  • [{item.source}] {item.title}")
            if snippet:
                lines.append(f"    {snippet}")
    else:
        lines.append(
            "  • No se encontraron reportes públicos recientes. El atasco puede deberse "
            "a accidente no reportado, obra vial o alto volumen vehicular."
        )

    lines.append("")
    lines.append("Rutas disponibles:")
    for comp in comparisons:
        status = "atasco severo" if comp.has_severe_jam else "sin atascos severos"
        marker = " (actual)" if comp.is_primary else ""
        lines.append(
            f"  • {comp.label}{marker}: {comp.duration_minutes} min "
            f"(+{comp.delay_minutes} min) — {status}"
        )

    lines.append("")
    lines.append(f"Recomendación: {recommendation.action}")
    lines.append(f"Motivo: {recommendation.reason}")
    if recommendation.minutes_saved > 0:
        lines.append(f"Ahorro potencial: ~{recommendation.minutes_saved} min")
    lines.append(f"Mapa: {recommendation.maps_url}")
    lines.append("═" * 50)
    lines.append("")

    return "\n".join(lines)


def format_alert_telegram(
    timestamp: datetime,
    primary: RouteAnalysis,
    main_event: TrafficEvent | None,
    location: LocationInfo,
    news: list[NewsItem],
    comparisons: list[RouteComparison],
    recommendation: Recommendation,
) -> str:
    lines = [
        f"<b>🚨 ALERTA DE TRÁFICO</b> — {timestamp.strftime('%H:%M:%S')}",
        "",
    ]

    if main_event:
        lines.append(f"<b>Ubicación:</b> {_escape_html(location.formatted_address)}")
        if location.road:
            lines.append(f"<b>Vía:</b> {_escape_html(location.road)}")
        lines.append(
            f"<b>Condición:</b> {_speed_label(main_event.speed)} "
            f"(severidad {main_event.severity})"
        )
    else:
        lines.append(f"<b>Ubicación:</b> {_escape_html(location.formatted_address)}")

    lines.append(
        f"<b>Retraso:</b> +{primary.delay_minutes} min "
        f"(total: {primary.duration_minutes} min)"
    )

    lines.append("")
    lines.append("<b>Investigación:</b>")
    if news:
        for item in news[:3]:
            snippet = item.snippet[:120] + "..." if len(item.snippet) > 120 else item.snippet
            lines.append(f"• [{_escape_html(item.source)}] {_escape_html(item.title)}")
            if snippet:
                lines.append(f"  <i>{_escape_html(snippet)}</i>")
    else:
        lines.append(
            "<i>Sin reportes públicos recientes. Posible accidente no reportado, "
            "obra vial o alto volumen vehicular.</i>"
        )

    lines.append("")
    lines.append("<b>Rutas:</b>")
    for comp in comparisons:
        status = "atasco" if comp.has_severe_jam else "sin atasco"
        marker = " (actual)" if comp.is_primary else ""
        lines.append(
            f"• {_escape_html(comp.label)}{marker}: {comp.duration_minutes} min "
            f"(+{comp.delay_minutes}) — {status}"
        )

    lines.append("")
    lines.append(f"<b>Recomendación:</b> {recommendation.action}")
    lines.append(f"{_escape_html(recommendation.reason)}")
    if recommendation.minutes_saved > 0:
        lines.append(f"Ahorro potencial: ~{recommendation.minutes_saved} min")
    lines.append(f'<a href="{recommendation.maps_url}">Ver en Google Maps</a>')

    return "\n".join(lines)