"""Interfaz grafica para Route Accident Bot (Google)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from .alert_popup import show_traffic_alert_popup
from .alert_reporter import AlertResult
from .config_state import SETTINGS_FILE, is_config_complete, load_config, save_config
from .google_maps_link_parser import GoogleMapsLinkError, parse_google_maps_link, parse_location_label
from .monitor_service import RouteMonitor
from .setup_wizard import run_setup_wizard
from .ui_helpers import (
    APP_COLORS,
    StatusBadge,
    add_link_field_with_paste,
    build_page_header,
    build_road_selector,
    build_route_card,
    format_log_line,
    open_url,
    sync_road_selector,
    update_route_card,
)


class RouteAccidentBotApp(ctk.CTk):
    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = base_dir
        self.config_path = base_dir / SETTINGS_FILE
        self.config = load_config(self.config_path)
        self.monitor: RouteMonitor | None = None
        self.origin_coords: tuple[float, float] | None = None
        self.destination_coords: tuple[float, float] | None = None
        self._is_running = False

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Route Accident Bot")
        self.geometry("800x700")
        self.minsize(680, 580)

        self._build_ui()
        self._load_fields_from_config()
        self._append_log("Listo. Pega tu enlace de Google Maps y pulsa Analizar ruta.")

    def _build_ui(self) -> None:
        build_page_header(
            self,
            title="Route Accident Bot",
            subtitle="Analisis de trafico en tiempo real con Google Routes",
            badge="Google",
        )

        form = ctk.CTkFrame(self, border_width=1, border_color=APP_COLORS["card_border"])
        form.pack(fill="x", padx=20, pady=(0, 10))

        self.link_entry, self.link_hint = add_link_field_with_paste(form, on_change=self._on_link_changed)
        self.origin_label, self.destination_label = build_route_card(form)

        ctk.CTkLabel(form, text="Tipo de carretera", anchor="w").pack(anchor="w", padx=14, pady=(4, 0))
        self.road_var = tk.StringVar(value="free")
        self.road_selector = build_road_selector(form, self.road_var)

        self.periodic_var = tk.BooleanVar(value=False)
        self.periodic_checkbox = ctk.CTkCheckBox(
            form,
            text="Revisar automaticamente cada 45 min",
            variable=self.periodic_var,
        )
        self.periodic_checkbox.pack(anchor="w", padx=14, pady=(0, 14))

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=(0, 8))
        controls.grid_columnconfigure((0, 1), weight=1)

        self.analyze_btn = ctk.CTkButton(
            controls,
            text="Analizar ruta",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=APP_COLORS["accent"],
            hover_color=APP_COLORS["accent_hover"],
            command=self._analyze_route,
        )
        self.analyze_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            controls,
            text="Detener",
            height=40,
            fg_color=APP_COLORS["danger"],
            hover_color=APP_COLORS["danger_hover"],
            command=self._stop_analysis,
        )
        self.stop_btn.grid(row=0, column=1, sticky="ew")

        ctk.CTkButton(
            self,
            text="Reconfigurar APIs y ruta",
            fg_color="transparent",
            border_width=1,
            command=self._reconfigure,
        ).pack(fill="x", padx=20, pady=(0, 8))

        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.pack(fill="x", padx=20, pady=(0, 8))
        self.status_badge = StatusBadge(status_row)
        self.status_badge.pack(fill="x")

        self.links_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.links_frame.pack(fill="x", padx=20, pady=(0, 8))
        self._maps_link_button: ctk.CTkButton | None = None

        log_header = ctk.CTkFrame(self, fg_color="transparent")
        log_header.pack(fill="x", padx=20, pady=(4, 0))
        log_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_header, text="Resultados", anchor="w", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkButton(log_header, text="Limpiar", width=80, height=28, command=self._clear_log).grid(row=0, column=1)

        self.log_box = ctk.CTkTextbox(self, wrap="word", font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(4, 18))

    def _load_fields_from_config(self) -> None:
        route_cfg = self.config.get("route", {})
        monitor_cfg = self.config.get("monitor", {})
        self.link_entry.insert(0, route_cfg.get("maps_link", ""))
        self.road_var.set(route_cfg.get("road_preference", "free"))
        sync_road_selector(self.road_selector, self.road_var.get())
        self.periodic_var.set(bool(monitor_cfg.get("periodic_enabled", False)))
        update_route_card(
            self.origin_label,
            self.destination_label,
            route_cfg.get("origin", ""),
            route_cfg.get("destination", ""),
        )
        if route_cfg.get("maps_link"):
            self._on_link_changed(route_cfg.get("maps_link", ""))

    def _set_running_state(self, running: bool) -> None:
        self._is_running = running
        state = "disabled" if running else "normal"
        self.analyze_btn.configure(state=state)
        self.link_entry.configure(state=state)
        self.road_selector.configure(state=state)
        self.periodic_checkbox.configure(state=state)

    def _on_link_changed(self, raw: str, error: str | None = None) -> None:
        if error:
            self.link_hint.configure(text=error, text_color=APP_COLORS["warning"])
            update_route_card(self.origin_label, self.destination_label, "", "")
            return
        if not raw:
            self.link_hint.configure(text="Comparte la ruta desde Google Maps y pega el enlace aqui.", text_color=APP_COLORS["muted"])
            update_route_card(self.origin_label, self.destination_label, "", "")
            return
        try:
            parsed = parse_google_maps_link(raw)
        except GoogleMapsLinkError as exc:
            self.link_hint.configure(text=str(exc), text_color=APP_COLORS["warning"])
            update_route_card(self.origin_label, self.destination_label, "", "")
            return
        self.origin_coords = parsed.origin_coords
        self.destination_coords = parsed.destination_coords
        update_route_card(self.origin_label, self.destination_label, parsed.origin, parsed.destination)
        self.link_hint.configure(text="Enlace valido.", text_color=APP_COLORS["success"])

    def _append_log(self, message: str) -> None:
        self.log_box.insert("end", format_log_line(message) + "\n")
        self.log_box.see("end")

    def _clear_log(self) -> None:
        self.log_box.delete("1.0", "end")

    def _thread_safe_log(self, message: str) -> None:
        self.after(0, lambda: self._append_log(message))

    def _thread_safe_status(self, status: str) -> None:
        def _update() -> None:
            self.status_badge.set_status(status)
            if status == "Detenido":
                self._set_running_state(False)

        self.after(0, _update)

    def _thread_safe_maps_link(self, url: str, label: str) -> None:
        self.after(0, lambda: self._show_maps_button(url, label))

    def _thread_safe_alert(self, result: AlertResult) -> None:
        self.after(0, lambda: show_traffic_alert_popup(self, result))

    def _show_maps_button(self, url: str, label: str) -> None:
        if self._maps_link_button is not None:
            self._maps_link_button.destroy()
            self._maps_link_button = None
        self._maps_link_button = ctk.CTkButton(
            self.links_frame,
            text=label,
            fg_color=APP_COLORS["success_bg"],
            hover_color=APP_COLORS["success"],
            command=lambda u=url: open_url(u),
        )
        self._maps_link_button.pack(fill="x")

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
        update_route_card(self.origin_label, self.destination_label, parsed.origin, parsed.destination)
        self.link_hint.configure(text="Enlace valido.", text_color=APP_COLORS["success"])
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
                on_alert=self._thread_safe_alert,
                on_maps_link=self._thread_safe_maps_link,
                origin_coords=self.origin_coords,
                destination_coords=self.destination_coords,
            )
            self._set_running_state(True)
            self.monitor.print_banner()
            self.monitor.start_analysis(periodic=periodic)
            self._append_log("Analisis iniciado.")
        except Exception as exc:
            self._append_log(f"No se pudo analizar: {exc}")

    def _stop_analysis(self) -> None:
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        self._set_running_state(False)
        self.status_badge.set_status("Detenido")
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