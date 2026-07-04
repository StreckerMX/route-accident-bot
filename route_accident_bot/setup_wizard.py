"""Asistente grafico de configuracion inicial."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from .config_state import SETTINGS_FILE, load_config, save_config, write_env_file
from .google_maps_link_parser import GoogleMapsLinkError, parse_google_maps_link
from .ui_helpers import (
    APP_COLORS,
    add_labeled_entry_with_paste,
    add_link_field_with_paste,
    build_page_header,
    build_road_selector,
    build_section_title,
)


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
        self.geometry("680x760")
        self.minsize(600, 680)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build_ui(self) -> None:
        build_page_header(
            self,
            title="Configuracion inicial",
            subtitle="Conecta Google Routes y define tu ruta habitual",
            badge="Google",
        )

        form = ctk.CTkScrollableFrame(self, border_width=1, border_color=APP_COLORS["card_border"])
        form.pack(fill="both", expand=True, padx=20, pady=8)

        build_section_title(form, "1. Claves de API")
        self.routes_key_entry = add_labeled_entry_with_paste(
            form,
            "Google Routes API",
            show="*",
            hint="Crea una clave en console.cloud.google.com",
        )
        self.geocoding_key_entry = add_labeled_entry_with_paste(
            form,
            "Google Geocoding API (opcional)",
            show="*",
            hint="Puedes usar la misma clave que Routes",
        )

        build_section_title(form, "2. Tu ruta")
        self.link_entry, self.link_hint = add_link_field_with_paste(form)

        ctk.CTkLabel(form, text="Tipo de carretera", anchor="w").pack(anchor="w", padx=14, pady=(8, 0))
        self.road_var = tk.StringVar(value="free")
        self.road_selector = build_road_selector(form, self.road_var)

        self.periodic_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Revisar automaticamente cada 45 min", variable=self.periodic_var).pack(
            anchor="w", padx=14, pady=(0, 8)
        )

        build_section_title(form, "3. Notificaciones (opcional)")
        self.telegram_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form,
            text="Activar alertas por Telegram",
            variable=self.telegram_var,
            command=self._toggle_telegram,
        ).pack(anchor="w", padx=14, pady=(0, 4))

        self.telegram_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.telegram_frame.pack(fill="x", padx=14, pady=(0, 12))
        self.telegram_token_entry = add_labeled_entry_with_paste(self.telegram_frame, "Token del bot", show="*")
        self.telegram_chat_entry = add_labeled_entry_with_paste(self.telegram_frame, "Chat ID")
        self._toggle_telegram()

        self.status_label = ctk.CTkLabel(self, text="", text_color=APP_COLORS["warning"], anchor="w")
        self.status_label.pack(fill="x", padx=20, pady=4)

        ctk.CTkButton(
            self,
            text="Guardar y continuar",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=APP_COLORS["success_bg"],
            hover_color=APP_COLORS["success"],
            command=self._save,
        ).pack(fill="x", padx=20, pady=(4, 18))

    def _toggle_telegram(self) -> None:
        state = "normal" if self.telegram_var.get() else "disabled"
        self.telegram_token_entry.configure(state=state)
        self.telegram_chat_entry.configure(state=state)

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