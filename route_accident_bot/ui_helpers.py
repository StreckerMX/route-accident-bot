"""Utilidades compartidas para la interfaz grafica."""

from __future__ import annotations

import tkinter as tk
import webbrowser

import customtkinter as ctk


def add_labeled_entry_with_paste(
    parent: ctk.CTkBaseClass,
    label: str,
    show: str | None = None,
    placeholder: str = "",
) -> ctk.CTkEntry:
    ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=8, pady=(8, 0))
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=8, pady=4)
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


def open_url(url: str) -> None:
    if url:
        webbrowser.open(url)