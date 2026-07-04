"""Ventanas emergentes para mostrar alertas y noticias."""

from __future__ import annotations

import customtkinter as ctk

from .alert_reporter import AlertResult, format_alert_popup_body
from .news_investigator import NewsItem
from .route_advisor import build_maps_point_url
from .ui_helpers import APP_COLORS, open_url


def show_traffic_alert_popup(parent: ctk.CTk, result: AlertResult) -> None:
    popup = ctk.CTkToplevel(parent)
    popup.title("Alerta de trafico")
    popup.geometry("560x560")
    popup.minsize(480, 460)
    popup.transient(parent)
    popup.grab_set()
    popup.focus_set()

    ctk.CTkLabel(
        popup,
        text="Alerta de trafico detectada",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=APP_COLORS["warning"],
    ).pack(pady=(16, 8))

    body = ctk.CTkTextbox(popup, wrap="word", font=ctk.CTkFont(size=13))
    body.pack(fill="both", expand=True, padx=16, pady=(0, 8))
    body.insert("1.0", format_alert_popup_body(result))
    body.configure(state="disabled")

    actions = ctk.CTkFrame(popup, fg_color="transparent")
    actions.pack(fill="x", padx=16, pady=(0, 8))

    if result.main_event:
        delay_url = build_maps_point_url(result.main_event.lat, result.main_event.lng)
        ctk.CTkButton(
            actions,
            text="Ver retraso en Maps",
            fg_color="#9a6700",
            hover_color="#7a5200",
            command=lambda url=delay_url: open_url(url),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

    if result.news:
        ctk.CTkButton(
            actions,
            text=f"Ver noticias ({len(result.news)})",
            fg_color=APP_COLORS["accent"],
            hover_color=APP_COLORS["accent_hover"],
            command=lambda: show_news_popup(popup, result.news),
        ).pack(side="left", fill="x", expand=True, padx=6)

    if result.maps_url:
        ctk.CTkButton(
            actions,
            text=result.maps_label,
            fg_color=APP_COLORS["success_bg"],
            hover_color=APP_COLORS["success"],
            command=lambda url=result.maps_url: open_url(url),
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

    ctk.CTkButton(
        popup,
        text="Cerrar",
        fg_color="transparent",
        border_width=1,
        command=popup.destroy,
    ).pack(fill="x", padx=16, pady=(0, 16))


def show_news_popup(parent: ctk.CTkBaseClass, news: list[NewsItem]) -> None:
    popup = ctk.CTkToplevel(parent)
    popup.title("Noticias encontradas")
    popup.geometry("620x560")
    popup.minsize(520, 440)
    popup.transient(parent.winfo_toplevel())
    popup.focus_set()

    ctk.CTkLabel(
        popup,
        text=f"{len(news)} noticia{'s' if len(news) != 1 else ''} recientes",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(pady=(14, 8))

    scroll = ctk.CTkScrollableFrame(popup)
    scroll.pack(fill="both", expand=True, padx=16, pady=(0, 8))

    for index, item in enumerate(news, start=1):
        card = ctk.CTkFrame(scroll, border_width=1, border_color=APP_COLORS["card_border"])
        card.pack(fill="x", pady=(0, 10))

        age = f" · {item.age_label}" if item.age_label else ""
        ctk.CTkLabel(
            card,
            text=f"{index}. {item.title}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=540,
        ).pack(fill="x", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            card,
            text=f"{item.source}{age}",
            text_color=APP_COLORS["muted"],
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).pack(fill="x", padx=12)

        if item.snippet:
            snippet = item.snippet[:280] + "..." if len(item.snippet) > 280 else item.snippet
            ctk.CTkLabel(
                card,
                text=snippet,
                anchor="w",
                justify="left",
                wraplength=540,
            ).pack(fill="x", padx=12, pady=(4, 8))

        if item.url:
            ctk.CTkButton(
                card,
                text="Abrir noticia",
                height=28,
                command=lambda url=item.url: open_url(url),
            ).pack(anchor="w", padx=12, pady=(0, 10))

    ctk.CTkButton(popup, text="Cerrar", command=popup.destroy).pack(fill="x", padx=16, pady=(0, 14))