#!/usr/bin/env python3
"""Punto de entrada del monitor de trafico Route Accident Bot."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

from route_accident_bot.alert_reporter import format_alert, format_alert_telegram, format_ok_check
from route_accident_bot.google_geocoder import Geocoder, LocationInfo
from route_accident_bot.google_routes_client import RoutesClient
from route_accident_bot.news_investigator import Investigator
from route_accident_bot.route_advisor import compare_routes, recommend
from route_accident_bot.telegram_notifier import TelegramNotifier
from route_accident_bot.traffic_analyzer import analyze_route

SETTINGS_FILE = "RouteAccidentBot.Settings.yaml"
ENV_EXAMPLE_FILE = "RouteAccidentBot.env.example"


def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    base_dir = Path(__file__).parent
    load_dotenv(base_dir / ".env", encoding="utf-8-sig")

    routes_api_key = os.getenv("GOOGLE_ROUTES_API_KEY", "").strip()
    geocoding_api_key = os.getenv("GOOGLE_GEOCODING_API_KEY", "").strip()

    if not routes_api_key:
        print("Error: define GOOGLE_ROUTES_API_KEY en el archivo .env")
        print(f"Copia {base_dir / ENV_EXAMPLE_FILE} a {base_dir / '.env'} y agrega tus claves.")
        return 1

    if not geocoding_api_key:
        print("Error: define GOOGLE_GEOCODING_API_KEY en el archivo .env")
        print(f"Copia {base_dir / ENV_EXAMPLE_FILE} a {base_dir / '.env'} y agrega tus claves.")
        return 1

    config_path = base_dir / SETTINGS_FILE
    if not config_path.exists():
        print(f"Error: no se encontro {config_path}")
        return 1

    config = load_config(config_path)
    route_cfg = config.get("route", {})
    monitor_cfg = config.get("monitor", {})
    investigation_cfg = config.get("investigation", {})
    advisor_cfg = config.get("advisor", {})
    telegram_cfg = config.get("telegram", {})

    origin = route_cfg.get("origin", "").strip()
    destination = route_cfg.get("destination", "").strip()
    if not origin or not destination:
        print(f"Error: configura origin y destination en {SETTINGS_FILE}")
        return 1

    interval = int(monitor_cfg.get("interval_minutes", 45))
    delay_threshold = int(monitor_cfg.get("jam_delay_threshold_minutes", 13))
    cooldown = int(monitor_cfg.get("cooldown_minutes", 15))
    switch_threshold = advisor_cfg.get("recommend_switch_if_saves_minutes", 10)
    compute_alternatives = advisor_cfg.get("compute_alternatives", True)
    language = investigation_cfg.get("language", "es")

    routes_client = RoutesClient(routes_api_key, language_code=f"{language}-MX")
    geocoder = Geocoder(geocoding_api_key, language=language)
    investigator = Investigator(
        search_queries=investigation_cfg.get("search_queries", []),
        max_results=investigation_cfg.get("max_news_results", 5),
    )

    telegram = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )
    telegram_enabled = telegram_cfg.get("enabled", False) and telegram.enabled
    notify_on_alert = telegram_cfg.get("notify_on_alert", True)
    notify_on_ok = telegram_cfg.get("notify_on_ok", False)

    if telegram_cfg.get("enabled", False) and not telegram.enabled:
        print("Aviso: telegram.enabled=true pero faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env")

    print("=" * 50)
    print("  Route Accident Bot - Monitoreo activo")
    print("=" * 50)
    print(f"  Origen:      {origin}")
    print(f"  Destino:     {destination}")
    print(f"  Intervalo:   cada {interval} min")
    print(f"  Umbral:      +{delay_threshold} min de retraso")
    print(f"  Telegram:    {'activo' if telegram_enabled else 'desactivado'}")
    print("  Ctrl+C para detener")
    print("=" * 50)
    print()

    last_alert_at = None

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
                                location = LocationInfo(
                                    formatted_address="Ubicacion no determinada",
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

                            alert_text = format_alert(
                                timestamp=now,
                                primary=primary,
                                main_event=main_event,
                                location=location,
                                news=news,
                                comparisons=comparisons,
                                recommendation=recommendation,
                            )
                            print(alert_text)

                            if telegram_enabled and notify_on_alert:
                                try:
                                    sent = telegram.send(
                                        format_alert_telegram(
                                            timestamp=now,
                                            primary=primary,
                                            main_event=main_event,
                                            location=location,
                                            news=news,
                                            comparisons=comparisons,
                                            recommendation=recommendation,
                                        )
                                    )
                                    if sent:
                                        print("  Alerta enviada a Telegram.")
                                    else:
                                        print("  No se pudo enviar la alerta a Telegram.")
                                except Exception as exc:
                                    print(f"  Error de Telegram: {exc}")

                            last_alert_at = time.time()
                    else:
                        ok_text = format_ok_check(now, primary)
                        print(ok_text)
                        if telegram_enabled and notify_on_ok:
                            try:
                                telegram.send(ok_text, parse_mode=None)
                            except Exception as exc:
                                print(f"  Error de Telegram: {exc}")

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
