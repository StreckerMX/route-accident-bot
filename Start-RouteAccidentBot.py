#!/usr/bin/env python3
"""Punto de entrada del monitor de trafico Route Accident Bot."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from route_accident_bot.monitor_service import RouteMonitor, load_config

SETTINGS_FILE = "RouteAccidentBot.Settings.yaml"
ENV_EXAMPLE_FILE = "RouteAccidentBot.env.example"


def main() -> int:
    base_dir = Path(__file__).parent
    load_dotenv(base_dir / ".env", encoding="utf-8-sig")

    config_path = base_dir / SETTINGS_FILE
    if not config_path.exists():
        print(f"Error: no se encontro {config_path}")
        return 1

    try:
        monitor = RouteMonitor(base_dir=base_dir, config=load_config(config_path))
    except ValueError as exc:
        print(f"Error: {exc}")
        if "GOOGLE" in str(exc):
            print(f"Copia {base_dir / ENV_EXAMPLE_FILE} a {base_dir / '.env'} y agrega tus claves.")
        return 1

    monitor.run_blocking()
    return 0


if __name__ == "__main__":
    sys.exit(main())