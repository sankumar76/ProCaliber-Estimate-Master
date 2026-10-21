"""Main window: sidebar navigation hosting both modules."""

import datetime
import os
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from core import app_info
from core.estimate_workbook import app_data_dir, resource_path
from gui import theme
from gui.about_page import AboutPage
from gui.cost_estimator_pages import CostEstimatorPage
from gui.weight_calculator_pages import (SHAPE_PAGES, SECTION_PAGES,
                                         SpecificGravityPage, UnitConverterPage)
from gui.widgets import MaterialState, disable_combobox_wheel

APP_NAME = app_info.APP_NAME

# The two main modules: (number, title, subtitle, colour, [(group, [(label, page)])])
MODULES = [
    ("1", "Weight Calculator", "Shapes & IS sections", theme.WEIGHT_COLOR, [
        ("Shapes", SHAPE_PAGES),
        ("IS sections", SECTION_PAGES),
        ("Tools", [("Specific Gravity", SpecificGravityPage),
                   ("Unit Converter", UnitConverterPage)]),
    ]),
    ("2", "Cost Estimator", "Excel cost estimates", theme.COST_COLOR, [
        (None, [("Cost Estimate", CostEstimatorPage)]),
    ]),
]


class NavItem(tk.Frame):
    """Sidebar link with a coloured marker when active."""

    def __init__(self, parent, text, command, color, bg, indent=18):
        super().__init__(parent, bg=bg, cursor="hand2")
        self.color, self.bg = color, bg
        self.bar = tk.Frame(self, width=3, bg=bg)
        self.bar.pack(side="left", fill="y")
        self.label = tk.Label(self, text=text, anchor="w", padx=indent, pady=6,
                              bg=bg, fg=theme.SIDEBAR_TEXT, font=theme.F_NAV)
        self.label.pack(side="left", fill="x", expand=True)
        self.active = False
        for w in (self, self.label, self.bar):
            w.bind("<Button-1>", lambda _e: command())
            w.bind("<Enter>", lambda _e: self._paint(hover=True))
            w.bind("<Leave>", lambda _e: self._paint())

    def set_active(self, active):
        self.active = active
        self._paint()

    def _paint(self, hover=False):
        if self.active:
            bg, fg, font, bar = theme.SIDEBAR_HOVER, "white", (theme.FONT, 10, "bold"), self.color
        elif hover:
            bg, fg, font, bar = theme.SIDEBAR_HOVER, "white", theme.F_NAV, theme.SIDEBAR_HOVER
        else:
            bg, fg, font, bar = self.bg, theme.SIDEBAR_TEXT, theme.F_NAV, self.bg
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg, font=font)
        self.bar.configure(bg=bar)


class ModulePanel(tk.Frame):
    """A clearly separated sidebar block for one main module."""

    def __init__(self, parent, number, title, subtitle, color, on_header):
        super().__init__(parent, bg=theme.SIDEBAR_GROUP)
        tk.Frame(self, bg=color, height=3).pack(fill="x")
        head = tk.Frame(self, bg=theme.SIDEBAR_GROUP, padx=12, pady=10, cursor="hand2")
        head.pack(fill="x")
        badge = tk.Label(head, text=number, bg=color, fg=theme.SIDEBAR_BG,
                         font=(theme.FONT, 11, "bold"), width=2)
        badge.pack(side="left", anchor="n", pady=(2, 0))
        text = tk.Frame(head, bg=theme.SIDEBAR_GROUP)
        text.pack(side="left", padx=(8, 0))
        name = tk.Label(text, text=title, bg=theme.SIDEBAR_GROUP, fg="white", font=theme.F_MODULE)
        name.pack(anchor="w")
        sub = tk.Label(text, text=subtitle, bg=theme.SIDEBAR_GROUP, fg=theme.SIDEBAR_MUTED,
                       font=theme.F_SMALL)
        sub.pack(anchor="w")
        for w in (head, badge, text, name, sub):
            w.bind("<Button-1>", lambda _e: on_header())
        self.color = color

    def group_label(self, text):
        tk.Label(self, text=text.upper(), bg=theme.SIDEBAR_GROUP, fg=theme.SIDEBAR_MUTED,
                 font=theme.F_NAV_HEADER, anchor="w", padx=21).pack(fill="x", pady=(6, 1))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        icon = resource_path("assets", "app.ico")
        if os.path.exists(icon):
            try:
                self.iconbitmap(default=icon)
            except tk.TclError:
                pass
        theme.apply(self)
        disable_combobox_wheel(self)
        self.material = MaterialState(self)

        width, height = 1400, 900
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        width, height = min(width, sw - 40), min(height, sh - 80)
        self.geometry(f"{width}x{height}+{max((sw - width) // 2, 0)}+{max((sh - height) // 3, 0)}")
        self.minsize(1080, 680)

        sidebar = tk.Frame(self, bg=theme.SIDEBAR_BG, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.content = ttk.Frame(self)
        self.content.pack(side="left", fill="both", expand=True)

        brand = tk.Frame(sidebar, bg=theme.SIDEBAR_BG)
        brand.pack(fill="x", padx=20, pady=(20, 14))
        tk.Label(brand, text="PC", bg=theme.ACCENT, fg="white", width=3,
                 font=(theme.FONT, 12, "bold"), pady=4).pack(side="left")
        names = tk.Frame(brand, bg=theme.SIDEBAR_BG)
        names.pack(side="left", padx=(10, 0))
        tk.Label(names, text="ProCaliber", bg=theme.SIDEBAR_BG, fg="white",
                 font=theme.F_BRAND).pack(anchor="w")
        tk.Label(names, text="Estimator", bg=theme.SIDEBAR_BG, fg=theme.COST_COLOR,
                 font=(theme.FONT, 9, "bold")).pack(anchor="w")

        self.pages, self.nav_items = {}, {}
        for number, title, subtitle, color, groups in MODULES:
            first = groups[0][1][0][0]
            panel = ModulePanel(sidebar, number, title, subtitle, color,
                                lambda f=first: self.show(f))
            panel.pack(fill="x", padx=12, pady=(0, 12))
            for group, items in groups:
                if group:
                    panel.group_label(group)
                for label, page_cls in items:
                    self.pages[label] = page_cls(self.content, self)
                    item = NavItem(panel, label, lambda l=label: self.show(l), color,
                                   theme.SIDEBAR_GROUP, indent=30 if group else 18)
                    item.pack(fill="x")
                    self.nav_items[label] = item
            tk.Frame(panel, bg=theme.SIDEBAR_GROUP, height=6).pack(fill="x")

        # About sits at the bottom of the sidebar, under a version line.
        tk.Label(sidebar, text=f"Version {app_info.VERSION}", bg=theme.SIDEBAR_BG,
                 fg=theme.SIDEBAR_MUTED, font=theme.F_SMALL, anchor="w", padx=24
                 ).pack(side="bottom", fill="x", pady=(0, 14))
        self.pages["About"] = AboutPage(self.content, self)
        self.nav_items["About"] = NavItem(sidebar, "About", lambda: self.show("About"),
                                          theme.ACCENT, theme.SIDEBAR_BG, indent=21)
        self.nav_items["About"].pack(side="bottom", fill="x")

        self.estimator = self.pages["Cost Estimate"]
        self.current = None
        self.show("Round Bar")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def report_callback_exception(self, exc_type, exc, tb):
        """Never fail silently: log unexpected errors and tell the user."""
        log_path = None
        try:
            log_path = os.path.join(app_data_dir("Logs"), "error.log")
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(f"\n=== {datetime.datetime.now():%Y-%m-%d %H:%M:%S} "
                         f"{APP_NAME} {app_info.VERSION} ===\n")
                fh.write("".join(traceback.format_exception(exc_type, exc, tb)))
        except OSError:
            pass
        detail = f"\n\nDetails were saved to:\n{log_path}" if log_path else ""
        messagebox.showerror(
            "Something went wrong",
            f"An unexpected error occurred:\n\n{exc}{detail}\n\n"
            "Spreadsheets already on disk are not affected.", parent=self)

    def show(self, label):
        if self.current:
            self.pages[self.current].pack_forget()
            self.nav_items[self.current].set_active(False)
        self.current = label
        self.pages[label].pack(fill="both", expand=True)
        self.nav_items[label].set_active(True)

    def send_to_estimator(self, which, dims, source, navigate=True):
        self.estimator.receive_dimensions(which, dims, source)
        if navigate:
            self.show("Cost Estimate")

    def set_title_suffix(self, name):
        self.title(f"{name} — {APP_NAME}" if name else APP_NAME)

    def on_close(self):
        if self.estimator.confirm_close():
            self.destroy()
