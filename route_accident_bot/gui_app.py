"""Interfaz grafica para Route Accident Bot (Google)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Any

import customtkinter as ctk

from .google_maps_link_parser import GoogleMapsLinkError, parse_google_maps_link, parse_location_label
from .monitor_service import RouteMonitor, load_config, save_config

SETTINGS_FILE = "RouteAccidentBot.Settings.yaml"


class RouteAccidentBotApp(ctk.CTk):
    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = base_dir
        self.config_path = base_dir / SETTINGS_FILE
        self.config = load_config(self.config_path) if self.config_path.exists() else {}
        self.monitor: RouteMonitor | None = None
        self.origin_coords: tuple[float, float] | None = None
        self.destination_coords: tuple[float, float] | None = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Route Accident Bot")
        self.geometry("760x640")
        self.minsize(640, 520)

        self._build_ui()
        self._load_fields_from_config()

    def _build_ui(self) -> None:
        header = ctk.CTkLabel(
            self,
            text="Route Accident Bot",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        header.pack(pady=(16, 8))

        subtitle = ctk.CTkLabel(
            self,
            text="Monitoreo de trafico con Google Routes API",
            text_color="gray70",
        )
        subtitle.pack(pady=(0, 12))

        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(form, text="Enlace de Google Maps").pack(anchor="w", padx=12, pady=(12, 4))

        link_row = ctk.CTkFrame(form, fg_color="transparent")
        link_row.pack(fill="x", padx=12, pady=(0, 8))
        link_row.grid_columnconfigure(0, weight=1)

        self.link_entry = ctk.CTkEntry(link_row, placeholder_text="Pega aqui el enlace de la ruta")
        self.link_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(link_row, text="Pegar", width=80, command=self._paste_link).grid(
            row=0, column=1
        )

        ctk.CTkButton(form, text="Analizar enlace", command=self._parse_link).pack(
            fill="x", padx=12, pady=(0, 12)
        )

        self.origin_entry = self._labeled_entry(form, "Origen")
        self.destination_entry = self._labeled_entry(form, "Destino")

        settings_row = ctk.CTkFrame(form, fg_color="transparent")
        settings_row.pack(fill="x", padx=12, pady=(4, 12))
        settings_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(settings_row, text="Intervalo (min)").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(settings_row, text="Umbral retraso (+min)").grid(row=0, column=1, sticky="w")

        self.interval_entry = ctk.CTkEntry(settings_row)
        self.interval_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 0))

        self.threshold_entry = ctk.CTkEntry(settings_row)
        self.threshold_entry.grid(row=1, column=1, sticky="ew", pady=(4, 0))

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=16, pady=8)
        controls.grid_columnconfigure((0, 1), weight=1)

        self.start_button = ctk.CTkButton(controls, text="Iniciar monitoreo", command=self._start_monitor)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.stop_button = ctk.CTkButton(
            controls, text="Detener", fg_color="#8b2e2e", hover_color="#6f2424", command=self._stop_monitor
        )
        self.stop_button.grid(row=0, column=1, sticky="ew")

        self.status_label = ctk.CTkLabel(self, text="Estado: Detenido", anchor="w")
        self.status_label.pack(fill="x", padx=16, pady=(4, 8))

        ctk.CTkLabel(self, text="Log de actividad", anchor="w").pack(fill="x", padx=16)
        self.log_box = ctk.CTkTextbox(self, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(4, 16))

    def _labeled_entry(self, parent: ctk.CTkFrame, label: str) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=12, pady=(4, 0))
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=12, pady=(4, 8))
        return entry

    def _load_fields_from_config(self) -> None:
        route_cfg = self.config.get("route", {})
        monitor_cfg = self.config.get("monitor", {})
        self.origin_entry.insert(0, route_cfg.get("origin", ""))
        self.destination_entry.insert(0, route_cfg.get("destination", ""))
        self.interval_entry.insert(0, str(monitor_cfg.get("interval_minutes", 45)))
        self.threshold_entry.insert(0, str(monitor_cfg.get("jam_delay_threshold_minutes", 13)))

    def _append_log(self, message: str) -> None:
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def _thread_safe_log(self, message: str) -> None:
        self.after(0, lambda: self._append_log(message))

    def _thread_safe_status(self, status: str) -> None:
        self.after(0, lambda: self.status_label.configure(text=f"Estado: {status}"))

    def _paste_link(self) -> None:
        try:
            text = self.clipboard_get().strip()
        except tk.TclError:
            self._append_log("No hay texto en el portapapeles.")
            return
        self.link_entry.delete(0, "end")
        self.link_entry.insert(0, text)

    def _parse_link(self) -> None:
        raw = self.link_entry.get().strip()
        if not raw:
            self._append_log("Pega un enlace de Google Maps primero.")
            return
        try:
            parsed = parse_google_maps_link(raw)
        except GoogleMapsLinkError as exc:
            self._append_log(f"Error al analizar enlace: {exc}")
            return

        self.origin_entry.delete(0, "end")
        self.origin_entry.insert(0, parsed.origin)
        self.destination_entry.delete(0, "end")
        self.destination_entry.insert(0, parsed.destination)
        self.origin_coords = parsed.origin_coords
        self.destination_coords = parsed.destination_coords
        self._append_log(f"Ruta detectada: {parsed.origin} -> {parsed.destination}")

    def _read_form(self) -> tuple[str, str, int, int]:
        origin = self.origin_entry.get().strip()
        destination = self.destination_entry.get().strip()
        if not origin or not destination:
            raise ValueError("Indica origen y destino.")

        try:
            interval = int(self.interval_entry.get().strip())
            threshold = int(self.threshold_entry.get().strip())
        except ValueError as exc:
            raise ValueError("Intervalo y umbral deben ser numeros enteros.") from exc

        if interval < 1 or threshold < 1:
            raise ValueError("Intervalo y umbral deben ser mayores a 0.")

        return origin, destination, interval, threshold

    def _save_config_from_form(self) -> None:
        origin, destination, interval, threshold = self._read_form()
        self.config.setdefault("route", {})
        self.config.setdefault("monitor", {})
        self.config["route"]["origin"] = origin
        self.config["route"]["destination"] = destination
        self.config["monitor"]["interval_minutes"] = interval
        self.config["monitor"]["jam_delay_threshold_minutes"] = threshold
        save_config(self.config_path, self.config)

    def _start_monitor(self) -> None:
        if self.monitor and self.monitor.is_running:
            self._append_log("El monitoreo ya esta activo.")
            return

        try:
            origin, destination, _, _ = self._read_form()
            _, self.origin_coords = parse_location_label(origin)
            _, self.destination_coords = parse_location_label(destination)
            self._save_config_from_form()
            self.monitor = RouteMonitor(
                base_dir=self.base_dir,
                config=self.config,
                on_log=self._thread_safe_log,
                on_status=self._thread_safe_status,
                origin_coords=self.origin_coords,
                destination_coords=self.destination_coords,
            )
            self.monitor.print_banner()
            self.monitor.start()
            self._append_log("Monitoreo iniciado.")
        except Exception as exc:
            self._append_log(f"No se pudo iniciar: {exc}")

    def _stop_monitor(self) -> None:
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        self._append_log("Monitoreo detenido.")

    def on_close(self) -> None:
        if self.monitor:
            self.monitor.stop()
        self.destroy()


def run_gui(base_dir: Path) -> None:
    app = RouteAccidentBotApp(base_dir)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()