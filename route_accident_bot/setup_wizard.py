"""Asistente grafico de configuracion inicial."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from .config_state import SETTINGS_FILE, load_config, save_config, write_env_file
from .google_maps_link_parser import GoogleMapsLinkError, parse_google_maps_link
from .ui_helpers import add_labeled_entry_with_paste


class SetupWizard(ctk.CTk):
    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = base_dir
        self.config_path = base_dir / SETTINGS_FILE
        self.env_path = base_dir / ".env"
        self.config = load_config(self.config_path)
        self.completed = False
        self.origin_coords: tuple[float, float] | None = None
        self.destination_coords: tuple[float, float] | None = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Configuracion - Route Accident Bot")
        self.geometry("640x720")
        self.minsize(560, 640)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build_ui(self) -> None:
        ctk.CTkLabel(self, text="Configuracion inicial", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(16, 4))
        ctk.CTkLabel(self, text="Completa los datos para analizar tu ruta", text_color="gray70").pack(pady=(0, 12))

        form = ctk.CTkScrollableFrame(self)
        form.pack(fill="both", expand=True, padx=16, pady=8)

        self.routes_key_entry = add_labeled_entry_with_paste(form, "API Key - Routes API", show="*")
        self.geocoding_key_entry = add_labeled_entry_with_paste(
            form, "API Key - Geocoding API (opcional, misma clave)", show="*"
        )

        ctk.CTkLabel(form, text="Enlace de Google Maps").pack(anchor="w", padx=8, pady=(12, 0))
        link_row = ctk.CTkFrame(form, fg_color="transparent")
        link_row.pack(fill="x", padx=8, pady=4)
        link_row.grid_columnconfigure(0, weight=1)
        self.link_entry = ctk.CTkEntry(link_row, placeholder_text="Pega el enlace de tu ruta")
        self.link_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(link_row, text="Pegar", width=80, command=self._paste_link).grid(row=0, column=1)

        ctk.CTkLabel(form, text="Tipo de carretera").pack(anchor="w", padx=8, pady=(12, 0))
        self.road_var = tk.StringVar(value="free")
        road_row = ctk.CTkFrame(form, fg_color="transparent")
        road_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkRadioButton(road_row, text="Libre (sin cuota)", variable=self.road_var, value="free").pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(road_row, text="Cuota", variable=self.road_var, value="toll").pack(side="left")

        self.periodic_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Revisar automaticamente cada 45 min", variable=self.periodic_var).pack(anchor="w", padx=8, pady=12)

        self.telegram_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Activar Telegram (opcional)", variable=self.telegram_var, command=self._toggle_telegram).pack(anchor="w", padx=8, pady=4)
        self.telegram_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.telegram_frame.pack(fill="x", padx=8, pady=4)
        self.telegram_token_entry = add_labeled_entry_with_paste(self.telegram_frame, "Token de Telegram", show="*")
        self.telegram_chat_entry = add_labeled_entry_with_paste(self.telegram_frame, "Chat ID de Telegram")
        self._toggle_telegram()

        self.status_label = ctk.CTkLabel(self, text="", text_color="orange")
        self.status_label.pack(fill="x", padx=16, pady=4)

        ctk.CTkButton(self, text="Guardar y continuar", command=self._save).pack(fill="x", padx=16, pady=12)

    def _toggle_telegram(self) -> None:
        state = "normal" if self.telegram_var.get() else "disabled"
        self.telegram_token_entry.configure(state=state)
        self.telegram_chat_entry.configure(state=state)

    def _paste_link(self) -> None:
        try:
            text = self.clipboard_get().strip()
        except tk.TclError:
            self.status_label.configure(text="No hay texto en el portapapeles.")
            return
        self.link_entry.delete(0, "end")
        self.link_entry.insert(0, text)

    def _save(self) -> None:
        routes_key = self.routes_key_entry.get().strip()
        geocoding_key = self.geocoding_key_entry.get().strip() or routes_key
        link = self.link_entry.get().strip()

        if not routes_key:
            self.status_label.configure(text="Indica la API Key de Routes.")
            return
        if not link:
            self.status_label.configure(text="Pega el enlace de Google Maps.")
            return

        try:
            parsed = parse_google_maps_link(link)
        except GoogleMapsLinkError as exc:
            self.status_label.configure(text=str(exc))
            return

        self.origin_coords = parsed.origin_coords
        self.destination_coords = parsed.destination_coords

        telegram_enabled = self.telegram_var.get()
        telegram_token = self.telegram_token_entry.get().strip() if telegram_enabled else ""
        telegram_chat = self.telegram_chat_entry.get().strip() if telegram_enabled else ""
        if telegram_enabled and (not telegram_token or not telegram_chat):
            self.status_label.configure(text="Completa token y chat ID de Telegram.")
            return

        write_env_file(self.env_path, routes_key, geocoding_key, telegram_token, telegram_chat)

        self.config.setdefault("route", {})
        self.config.setdefault("monitor", {})
        self.config.setdefault("telegram", {})
        self.config["route"]["maps_link"] = link
        self.config["route"]["origin"] = parsed.origin
        self.config["route"]["destination"] = parsed.destination
        self.config["route"]["road_preference"] = self.road_var.get()
        self.config["monitor"]["periodic_enabled"] = bool(self.periodic_var.get())
        self.config["monitor"]["interval_minutes"] = 45
        self.config["monitor"]["jam_delay_threshold_minutes"] = 13
        self.config["telegram"]["enabled"] = telegram_enabled
        save_config(self.config_path, self.config)

        self.completed = True
        self.destroy()

    def _cancel(self) -> None:
        self.completed = False
        self.destroy()


def run_setup_wizard(base_dir: Path) -> bool:
    wizard = SetupWizard(base_dir)
    wizard.mainloop()
    return wizard.completed