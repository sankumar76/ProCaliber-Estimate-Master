"""About page: application name, purpose, version and developer."""

import tkinter as tk
from tkinter import ttk

from core import app_info
from gui import theme
from gui.widgets import Card, ScrollableFrame


class AboutPage(ttk.Frame):
    title = "About"

    def __init__(self, parent, app):
        super().__init__(parent)
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.body

        # Hero: logo mark, name, version line
        hero = tk.Frame(body, bg=theme.SIDEBAR_BG, padx=28, pady=26)
        hero.pack(fill="x", pady=(0, 14))
        tk.Label(hero, text="PC", bg=theme.ACCENT, fg="white", width=3,
                 font=(theme.FONT, 22, "bold"), pady=6).pack(side="left", padx=(0, 20))
        text = tk.Frame(hero, bg=theme.SIDEBAR_BG)
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=app_info.APP_NAME, bg=theme.SIDEBAR_BG, fg="white",
                 font=(theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(text, text=app_info.SUMMARY, bg=theme.SIDEBAR_BG, fg=theme.SIDEBAR_TEXT,
                 font=theme.F_BASE, justify="left", wraplength=700).pack(anchor="w", pady=(2, 8))
        tk.Label(text, text=f"Version {app_info.VERSION}   ·   Released {app_info.RELEASE_DATE}",
                 bg=theme.SIDEBAR_BG, fg=theme.ACCENT, font=theme.F_BOLD).pack(anchor="w")
        credit = tk.Frame(text, bg=theme.SIDEBAR_BG)
        credit.pack(anchor="w", pady=(6, 0))
        tk.Label(credit, text="Designed & developed by ", bg=theme.SIDEBAR_BG,
                 fg=theme.SIDEBAR_TEXT, font=theme.F_BASE).pack(side="left")
        tk.Label(credit, text=app_info.DEVELOPER, bg=theme.SIDEBAR_BG, fg="white",
                 font=theme.F_BOLD).pack(side="left")
        tk.Label(credit, text="  ·  ", bg=theme.SIDEBAR_BG, fg=theme.SIDEBAR_MUTED,
                 font=theme.F_BASE).pack(side="left")
        tk.Label(credit, text=app_info.COMPANY, bg=theme.SIDEBAR_BG, fg="white",
                 font=theme.F_BOLD).pack(side="left")

        about = Card(body, "About this application")
        about.pack(fill="x", pady=(0, 14))
        desc = ttk.Label(about.content, text=app_info.DESCRIPTION, style="Card.TLabel",
                         justify="left", wraplength=800)
        desc.pack(anchor="w", fill="x")
        about.content.bind("<Configure>",
                           lambda e: desc.configure(wraplength=max(e.width - 4, 300)))

        features = Card(body, "What it does")
        features.pack(fill="x", pady=(0, 14))
        for i, (name, detail) in enumerate(app_info.FEATURES):
            ttk.Label(features.content, text=name, style="Card.TLabel",
                      font=theme.F_BOLD).grid(row=i, column=0, sticky="nw", padx=(0, 24), pady=5)
            ttk.Label(features.content, text=detail, style="Muted.TLabel", font=theme.F_BASE,
                      wraplength=640, justify="left").grid(row=i, column=1, sticky="w", pady=5)
        features.content.columnconfigure(1, weight=1)

        details = Card(body, "Application details")
        details.pack(fill="x")
        rows = [
            ("Application", app_info.APP_NAME),
            ("Version", app_info.VERSION),
            ("Release date", app_info.RELEASE_DATE),
            ("Designed & developed by", app_info.DEVELOPER),
            ("Company", app_info.COMPANY),
        ]
        for i, (label, value) in enumerate(rows):
            ttk.Label(details.content, text=label, style="Muted.TLabel", font=theme.F_BASE
                      ).grid(row=i, column=0, sticky="w", padx=(0, 32), pady=4)
            ttk.Label(details.content, text=value, style="Card.TLabel", font=theme.F_BOLD
                      ).grid(row=i, column=1, sticky="w", pady=4)
