"""Interfaz grafica para Route Accident Bot (Google)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from .config_state import SETTINGS_FILE, is_config_complete, load_config, save_config
from .google_maps_link_parser import GoogleMapsLinkError, parse_google_maps_link, parse_location_label
from .monitor_service import RouteMonitor
from .setup_wizard import run_setup_wizard


class RouteAccidentBotApp(ctk.CTk):
    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = base_dir
        self.config_path = base_dir / SETTINGS_FILE
        self.config = load_config(self.config_path)
        self.monitor: RouteMonitor | None = None
        self.origin_coords: tuple[float, float] | None = None
        self.destination_coords: tuple[float, float] | None = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Route Accident Bot")
        self.geometry("760x620")
        self.minsize(640, 520)

        self._build_ui()
        self._load_fields_from_config()

    def _build_ui(self) -> None:
        ctk.CTkLabel(self, text="Route Accident Bot", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(16, 8))
        ctk.CTkLabel(self, text="Analisis de trafico en ruta", text_color="gray70").pack(pady=(0, 12))

        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(form, text="Enlace de Google Maps").pack(anchor="w", padx=12, pady=(12, 4))
        link_row = ctk.CTkFrame(form, fg_color="transparent")
        link_row.pack(fill="x", padx=12, pady=(0, 8))
        link_row.grid_columnconfigure(0, weight=1)
        self.link_entry = ctk.CTkEntry(link_row, placeholder_text="Pega aqui el enlace de la ruta")
        self.link_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(link_row, text="Pegar", width=80, command=self._paste_link).grid(row=0, column=1)

        route_info = ctk.CTkFrame(form, fg_color="transparent")
        route_info.pack(fill="x", padx=12, pady=(0, 8))
        self.route_summary = ctk.CTkLabel(route_info, text="Ruta: sin configurar", anchor="w", justify="left")
        self.route_summary.pack(fill="x")

        ctk.CTkLabel(form, text="Tipo de carretera").pack(anchor="w", padx=12, pady=(4, 0))
        self.road_var = tk.StringVar(value="free")
        road_row = ctk.CTkFrame(form, fg_color="transparent")
        road_row.pack(fill="x", padx=12, pady=(4, 12))
        ctk.CTkRadioButton(road_row, text="Libre (sin cuota)", variable=self.road_var, value="free").pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(road_row, text="Cuota", variable=self.road_var, value="toll").pack(side="left")

        self.periodic_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Revisar automaticamente cada 45 min", variable=self.periodic_var).pack(anchor="w", padx=12, pady=(0, 12))

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=16, pady=8)
        controls.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(controls, text="Analizar ruta", command=self._analyze_route).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(controls, text="Detener", fg_color="#8b2e2e", hover_color="#6f2424", command=self._stop_analysis).grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(self, text="Reconfigurar APIs y ruta", fg_color="transparent", border_width=1, command=self._reconfigure).pack(fill="x", padx=16, pady=(0, 8))

        self.status_label = ctk.CTkLabel(self, text="Estado: Detenido", anchor="w")
        self.status_label.pack(fill="x", padx=16, pady=(4, 8))

        ctk.CTkLabel(self, text="Resultados", anchor="w").pack(fill="x", padx=16)
        self.log_box = ctk.CTkTextbox(self, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(4, 16))

    def _load_fields_from_config(self) -> None:
        route_cfg = self.config.get("route", {})
        monitor_cfg = self.config.get("monitor", {})
        self.link_entry.insert(0, route_cfg.get("maps_link", ""))
        self.road_var.set(route_cfg.get("road_preference", "free"))
        self.periodic_var.set(bool(monitor_cfg.get("periodic_enabled", False)))
        self._update_route_summary(route_cfg.get("origin", ""), route_cfg.get("destination", ""))

    def _update_route_summary(self, origin: str, destination: str) -> None:
        if origin and destination:
            self.route_summary.configure(text=f"Ruta: {origin} -> {destination}")
        else:
            self.route_summary.configure(text="Ruta: pega un enlace de Google Maps")

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

    def _parse_and_validate_link(self) -> tuple[str, str, str]:
        raw = self.link_entry.get().strip()
        if not raw:
            raise ValueError("Pega un enlace de Google Maps.")
        try:
            parsed = parse_google_maps_link(raw)
        except GoogleMapsLinkError as exc:
            raise ValueError(str(exc)) from exc
        self.origin_coords = parsed.origin_coords
        self.destination_coords = parsed.destination_coords
        self._update_route_summary(parsed.origin, parsed.destination)
        return raw, parsed.origin, parsed.destination

    def _save_config_from_form(self, maps_link: str, origin: str, destination: str) -> None:
        self.config.setdefault("route", {})
        self.config.setdefault("monitor", {})
        self.config["route"]["maps_link"] = maps_link
        self.config["route"]["origin"] = origin
        self.config["route"]["destination"] = destination
        self.config["route"]["road_preference"] = self.road_var.get()
        self.config["monitor"]["periodic_enabled"] = bool(self.periodic_var.get())
        self.config["monitor"]["interval_minutes"] = 45
        self.config["monitor"]["jam_delay_threshold_minutes"] = 13
        save_config(self.config_path, self.config)

    def _analyze_route(self) -> None:
        if self.monitor and self.monitor.is_running:
            self._append_log("Ya hay un analisis en curso.")
            return
        try:
            maps_link, origin, destination = self._parse_and_validate_link()
            _, self.origin_coords = parse_location_label(origin)
            _, self.destination_coords = parse_location_label(destination)
            self._save_config_from_form(maps_link, origin, destination)
            periodic = bool(self.periodic_var.get())

            self.monitor = RouteMonitor(
                base_dir=self.base_dir,
                config=self.config,
                on_log=self._thread_safe_log,
                on_status=self._thread_safe_status,
                origin_coords=self.origin_coords,
                destination_coords=self.destination_coords,
            )
            self.monitor.print_banner()
            self.monitor.start_analysis(periodic=periodic)
            self._append_log("Analisis iniciado.")
        except Exception as exc:
            self._append_log(f"No se pudo analizar: {exc}")

    def _stop_analysis(self) -> None:
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        self._append_log("Analisis detenido.")

    def _reconfigure(self) -> None:
        self._stop_analysis()
        if run_setup_wizard(self.base_dir):
            self.config = load_config(self.config_path)
            self.link_entry.delete(0, "end")
            self._load_fields_from_config()

    def on_close(self) -> None:
        if self.monitor:
            self.monitor.stop()
        self.destroy()


def run_gui(base_dir: Path) -> None:
    if not is_config_complete(base_dir):
        if not run_setup_wizard(base_dir):
            return
    app = RouteAccidentBotApp(base_dir)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()