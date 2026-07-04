#!/usr/bin/env python3
"""Bot de monitoreo de tráfico y accidentes en rutas de Google Maps."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

from src.geocoder import Geocoder
from src.investigator import Investigator
from src.reporter import format_alert, format_ok_check
from src.route_advisor import compare_routes, recommend
from src.routes_client import RoutesClient
from src.traffic_analyzer import analyze_route


def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    base_dir = Path(__file__).parent
    load_dotenv(base_dir / ".env")

    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        print("Error: define GOOGLE_MAPS_API_KEY en el archivo .env")
        print(f"Copia {base_dir / '.env.example'} a {base_dir / '.env'} y agrega tu clave.")
        return 1

    config_path = base_dir / "config.yaml"
    if not config_path.exists():
        print(f"Error: no se encontró {config_path}")
        return 1

    config = load_config(config_path)
    route_cfg = config.get("route", {})
    monitor_cfg = config.get("monitor", {})
    investigation_cfg = config.get("investigation", {})
    advisor_cfg = config.get("advisor", {})

    origin = route_cfg.get("origin", "").strip()
    destination = route_cfg.get("destination", "").strip()
    if not origin or not destination:
        print("Error: configura origin y destination en config.yaml")
        return 1

    interval = monitor_cfg.get("interval_minutes", 5)
    delay_threshold = monitor_cfg.get("jam_delay_threshold_minutes", 8)
    cooldown = monitor_cfg.get("cooldown_minutes", 15)
    switch_threshold = advisor_cfg.get("recommend_switch_if_saves_minutes", 10)
    compute_alternatives = advisor_cfg.get("compute_alternatives", True)
    language = investigation_cfg.get("language", "es")

    routes_client = RoutesClient(api_key, language_code=f"{language}-MX")
    geocoder = Geocoder(api_key, language=language)
    investigator = Investigator(
        search_queries=investigation_cfg.get("search_queries", []),
        max_results=investigation_cfg.get("max_news_results", 5),
    )

    print("═" * 50)
    print("  Route Accident Bot — Monitoreo activo")
    print("═" * 50)
    print(f"  Origen:      {origin}")
    print(f"  Destino:     {destination}")
    print(f"  Intervalo:   cada {interval} min")
    print(f"  Umbral:      +{delay_threshold} min de retraso")
    print("  Ctrl+C para detener")
    print("═" * 50)
    print()

    last_alert_at: float | None = None

    try:
        while True:
            now = datetime.now()
            try:
                routes = routes_client.compute_routes(
                    origin=origin,
                    destination=destination,
                    travel_mode=route_cfg.get("travel_mode", "DRIVE"),
                    compute_alternatives=compute_alternatives,
                )

                if not routes:
                    print(f"[{now.strftime('%H:%M:%S')}] Sin rutas disponibles.")
                else:
                    analyses = []
                    for i, route in enumerate(routes):
                        analyses.append(
                            analyze_route(
                                route=route,
                                route_index=i,
                                route_label=RoutesClient.route_label(route, i),
                                duration_minutes=RoutesClient.route_duration_minutes(route),
                                delay_minutes=RoutesClient.route_delay_minutes(route),
                                distance_km=RoutesClient.route_distance_km(route),
                                delay_threshold_minutes=delay_threshold,
                            )
                        )

                    primary = analyses[0]

                    if primary.has_severe_jam:
                        in_cooldown = (
                            last_alert_at is not None
                            and (time.time() - last_alert_at) < cooldown * 60
                        )

                        if in_cooldown:
                            print(
                                f"[{now.strftime('%H:%M:%S')}] Atasco detectado "
                                f"(alerta en cooldown, {cooldown} min)"
                            )
                        else:
                            main_event = next(
                                (e for e in primary.events if e.severity in ("ALTA", "MEDIA")),
                                primary.events[0] if primary.events else None,
                            )

                            if main_event:
                                location = geocoder.reverse(main_event.lat, main_event.lng)
                            else:
                                from src.geocoder import LocationInfo

                                location = LocationInfo(
                                    formatted_address="Ubicación no determinada",
                                    road="",
                                    neighborhood="",
                                    city="",
                                    state="",
                                )

                            news = investigator.search(location)
                            comparisons = compare_routes(analyses)
                            recommendation = recommend(
                                analyses, origin, destination, switch_threshold
                            )

                            print(
                                format_alert(
                                    timestamp=now,
                                    primary=primary,
                                    main_event=main_event,
                                    location=location,
                                    news=news,
                                    comparisons=comparisons,
                                    recommendation=recommendation,
                                )
                            )
                            last_alert_at = time.time()
                    else:
                        print(format_ok_check(now, primary))

            except requests.HTTPError as exc:
                print(f"[{now.strftime('%H:%M:%S')}] Error HTTP: {exc}")
                if exc.response is not None:
                    print(f"  Detalle: {exc.response.text[:300]}")
            except Exception as exc:
                print(f"[{now.strftime('%H:%M:%S')}] Error: {exc}")

            time.sleep(interval * 60)

    except KeyboardInterrupt:
        print("\nMonitoreo detenido.")
        return 0


if __name__ == "__main__":
    sys.exit(main())