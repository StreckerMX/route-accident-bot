"""Utilidades compartidas para la interfaz grafica."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from collections.abc import Callable
from datetime import datetime

import customtkinter as ctk

APP_COLORS = {
    "accent": "#3b8ed0",
    "accent_hover": "#36719f",
    "success": "#2d8a4e",
    "success_bg": "#1e5c36",
    "warning": "#e0a020",
    "danger": "#8b2e2e",
    "danger_hover": "#6f2424",
    "muted": "gray70",
    "card": "#212121",
    "card_border": "#333333",
}

STATUS_STYLES: dict[str, tuple[str, str, str]] = {
    "Detenido": ("Detenido", "gray75", "#3a3a3a"),
    "Analizando": ("Analizando", "white", "#1f6aa5"),
    "Esperando proxima revision": ("Monitoreo activo", "#b8f0c8", "#1e5c36"),
}


def truncate_text(text: str, max_len: int = 52) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def format_log_line(message: str) -> str:
    stamp = datetime.now().strftime("%H:%M:%S")
    return f"[{stamp}] {message}"


def open_url(url: str) -> None:
    if url:
        webbrowser.open(url)


class StatusBadge(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._dot = ctk.CTkLabel(self, text="●", font=ctk.CTkFont(size=14))
        self._dot.pack(side="left", padx=(0, 6))
        self._label = ctk.CTkLabel(self, text="Estado: Detenido", anchor="w")
        self._label.pack(side="left", fill="x", expand=True)
        self.set_status("Detenido")

    def set_status(self, status: str) -> None:
        label, dot_color, _bg = STATUS_STYLES.get(status, (status, "gray75", "#3a3a3a"))
        self._dot.configure(text_color=dot_color)
        self._label.configure(text=f"Estado: {label}")


def build_page_header(
    parent: ctk.CTkBaseClass,
    title: str,
    subtitle: str,
    badge: str | None = None,
) -> ctk.CTkFrame:
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", padx=20, pady=(18, 10))

    title_row = ctk.CTkFrame(header, fg_color="transparent")
    title_row.pack(fill="x")
    ctk.CTkLabel(title_row, text=title, font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
    if badge:
        ctk.CTkLabel(
            title_row,
            text=badge,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white",
            fg_color=APP_COLORS["accent"],
            corner_radius=6,
            width=72,
            height=24,
        ).pack(side="right", padx=(8, 0))

    ctk.CTkLabel(header, text=subtitle, text_color=APP_COLORS["muted"], anchor="w").pack(fill="x", pady=(4, 0))
    return header


def build_section_title(parent: ctk.CTkBaseClass, text: str) -> None:
    ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color="gray85",
        anchor="w",
    ).pack(anchor="w", padx=14, pady=(14, 6))


def build_route_card(parent: ctk.CTkBaseClass) -> tuple[ctk.CTkLabel, ctk.CTkLabel, ctk.CTkLabel]:
    card = ctk.CTkFrame(parent, fg_color=APP_COLORS["card"], border_width=1, border_color=APP_COLORS["card_border"])
    card.pack(fill="x", padx=14, pady=(0, 10))

    origin = ctk.CTkLabel(
        card,
        text="Origen: sin configurar",
        anchor="w",
        justify="left",
        text_color="gray80",
        wraplength=640,
    )
    origin.pack(fill="x", padx=12, pady=(10, 2))

    destination = ctk.CTkLabel(
        card,
        text="Destino: sin configurar",
        anchor="w",
        justify="left",
        text_color="gray80",
        wraplength=640,
    )
    destination.pack(fill="x", padx=12, pady=(2, 2))

    route_info = ctk.CTkLabel(
        card,
        text="",
        anchor="w",
        justify="left",
        text_color="gray65",
        font=ctk.CTkFont(size=12),
        wraplength=640,
    )
    route_info.pack(fill="x", padx=12, pady=(2, 10))
    return origin, destination, route_info


def update_route_card(
    origin_label: ctk.CTkLabel,
    destination_label: ctk.CTkLabel,
    origin: str,
    destination: str,
    route_info_label: ctk.CTkLabel | None = None,
    route_info: str = "",
) -> None:
    if origin and destination:
        origin_label.configure(text=f"Origen: {truncate_text(origin)}")
        destination_label.configure(text=f"Destino: {truncate_text(destination)}")
    else:
        origin_label.configure(text="Origen: pega un enlace de Google Maps")
        destination_label.configure(text="Destino: —")
    if route_info_label is not None:
        route_info_label.configure(text=route_info)


def build_road_selector(
    parent: ctk.CTkBaseClass,
    variable: tk.StringVar,
    on_change: Callable[..., None] | None = None,
) -> ctk.CTkSegmentedButton:
    def on_select(value: str) -> None:
        variable.set("free" if "Libre" in value else "toll")
        if on_change:
            on_change()

    selector = ctk.CTkSegmentedButton(
        parent,
        values=["Libre (sin cuota)", "Cuota"],
        command=on_select,
    )
    selector.pack(fill="x", padx=14, pady=(0, 12))
    sync_road_selector(selector, variable.get())
    return selector


def sync_road_selector(selector: ctk.CTkSegmentedButton, preference: str) -> None:
    selector.set("Libre (sin cuota)" if preference == "free" else "Cuota")


def add_labeled_entry_with_paste(
    parent: ctk.CTkBaseClass,
    label: str,
    show: str | None = None,
    placeholder: str = "",
    hint: str = "",
) -> ctk.CTkEntry:
    ctk.CTkLabel(parent, text=label, anchor="w").pack(anchor="w", padx=12, pady=(10, 0))
    if hint:
        ctk.CTkLabel(parent, text=hint, text_color=APP_COLORS["muted"], font=ctk.CTkFont(size=11), anchor="w").pack(
            anchor="w", padx=12, pady=(0, 4)
        )

    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=4)
    row.grid_columnconfigure(0, weight=1)

    entry = ctk.CTkEntry(row, show=show, placeholder_text=placeholder)
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    def _paste() -> None:
        try:
            text = parent.winfo_toplevel().clipboard_get().strip()
        except tk.TclError:
            return
        entry.delete(0, "end")
        entry.insert(0, text)

    ctk.CTkButton(row, text="Pegar", width=80, command=_paste).grid(row=0, column=1)
    return entry


def add_link_field_with_paste(
    parent: ctk.CTkBaseClass,
    on_change: Callable[..., None] | None = None,
) -> tuple[ctk.CTkEntry, ctk.CTkLabel]:
    ctk.CTkLabel(parent, text="Enlace de Google Maps", anchor="w").pack(anchor="w", padx=14, pady=(12, 4))

    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=(0, 4))
    row.grid_columnconfigure(0, weight=1)

    entry = ctk.CTkEntry(row, placeholder_text="Pega aqui el enlace de la ruta")
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    def _paste() -> None:
        try:
            text = parent.winfo_toplevel().clipboard_get().strip()
        except tk.TclError:
            if on_change:
                on_change("", error="No hay texto en el portapapeles.")
            return
        entry.delete(0, "end")
        entry.insert(0, text)
        if on_change:
            on_change(text)

    ctk.CTkButton(row, text="Pegar", width=80, command=_paste).grid(row=0, column=1)

    hint = ctk.CTkLabel(parent, text="", text_color=APP_COLORS["muted"], font=ctk.CTkFont(size=11), anchor="w")
    hint.pack(fill="x", padx=14, pady=(0, 6))

    if on_change:
        entry.bind("<KeyRelease>", lambda _event: on_change(entry.get().strip()))

    return entry, hint