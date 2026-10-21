"""Module B - Cost Estimator page (spec sections 5-8).

Workflow: the user picks (or creates) an estimate spreadsheet once; every
"Add Part" then writes the part straight into that spreadsheet. If the file
is open in Excel, the app closes it first (offering to save the user's Excel
edits), reloads it from disk so those edits are kept, adds the part, and can
re-open it in Excel afterwards.
"""

import datetime
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import excel_link, settings
from core.estimate_workbook import (DEFAULT_CNC_RATE, DEFAULT_CUTTING_COST,
                                    DEFAULT_VMC_RATE, Dimensions, EstimateError,
                                    EstimateWorkbook, FileLockedError, PartInput,
                                    app_data_dir, compute_costs, is_file_locked)
from gui import theme
from gui.widgets import (Banner, Card, Field, InputError, MaterialPicker,
                         NumberField, ScrollableFrame, StatusLabel, TabBar,
                         collect, fmt, fmt_money, page_header)

DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d-%m-%y", "%d/%m/%y")
DIM_FIELDS = (  # (key, column header, Dimensions attribute)
    ("o", "Length", "length"), ("p", "Width", "width"), ("q", "Thickness", "thickness"),
    ("r", "Outer dia", "outer_dia"), ("s", "Inner dia", "inner_dia"),
    ("t", "Length", "round_length"),
)
SECTIONS = (("details", "Part details"), ("material", "Material"),
            ("size", "Size"), ("costs", "Machining & costs"))
XLSX_TYPES = [("Excel workbook", "*.xlsx")]
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
IMAGE_TYPES = [("Pictures", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp"),
               ("All files", "*.*")]
THUMB_W, THUMB_H = 120, 84      # part-view preview size (px)
PASTED_TO_KEEP = 200            # pasted pictures kept in the app-data folder
EXCEL_GREEN = "#107C41"


def _prune(folder, keep):
    """Delete all but the newest ``keep`` files in ``folder`` (best effort)."""
    try:
        files = sorted((os.path.join(folder, f) for f in os.listdir(folder)),
                       key=os.path.getmtime)
        for stale in files[:-keep]:
            os.remove(stale)
    except OSError:
        pass


def default_folder():
    """Default place for estimate spreadsheets: Documents\\Cost_Calculations
    (created on first use). The user can pick any other folder in the dialog."""
    docs = None
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0:  # My Documents
            docs = buf.value
    except (AttributeError, OSError):
        pass
    folder = os.path.join(docs or os.path.join(os.path.expanduser("~"), "Documents"),
                          "Cost_Calculations")
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        return docs or os.path.expanduser("~")
    return folder


def parse_date(text):
    text = text.strip()
    for f in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text, f).date()
        except ValueError:
            pass
    raise InputError("Use DD-MM-YYYY")


class CostEstimatorPage(ttk.Frame):
    title = "Cost Estimate"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        prefs = settings.load()
        self.target = None              # spreadsheet that parts are added to
        self.file_parts = []
        self.file_rates = (DEFAULT_CNC_RATE, DEFAULT_VMC_RATE)
        self.image_path = None
        self._preview_job = None
        self._added_snapshot = None
        self._undo_size = None

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        page_header(body, "Cost Estimator",
                    "Fill in the tabs, check the preview, then add the part to "
                    "your estimate spreadsheet.",
                    module="Cost Estimator", color=theme.ACCENT)

        self._build_spreadsheet_card(body)

        columns = ttk.Frame(body)
        columns.pack(fill="x")
        columns.columnconfigure(0, weight=5, uniform="cols")
        columns.columnconfigure(1, weight=3, uniform="cols")
        left = ttk.Frame(columns)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        right = ttk.Frame(columns)
        right.grid(row=0, column=1, sticky="nsew")
        self._build_form(left)
        self._build_preview_card(right)
        self._build_parts_card(body)

        for var in self._all_vars():
            var.trace_add("write", lambda *_: self._schedule_preview())
        for f in (self.cnc_rate, self.vmc_rate):
            f.var.trace_add("write", lambda *_: self._refresh_rates_note())
        self.app.bind_all("<Control-v>", self._on_ctrl_v, add="+")
        self.app.bind_all("<Control-V>", self._on_ctrl_v, add="+")

        self.tabs.select("details")
        self._restore_target(prefs["target"])
        self._update_preview()

    # ================================================================ layout

    def _build_spreadsheet_card(self, body):
        card = Card(body, padding=16)
        card.pack(fill="x", pady=(0, 16))
        c = card.content
        c.columnconfigure(0, weight=1)

        left = ttk.Frame(c, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsew")
        head = tk.Frame(left, bg=theme.CARD)
        head.pack(fill="x")
        tk.Label(head, text="XLSX", bg=EXCEL_GREEN, fg="white", font=(theme.FONT, 9, "bold"),
                 width=5, pady=10).pack(side="left", anchor="n")
        info = tk.Frame(head, bg=theme.CARD)
        info.pack(side="left", fill="x", expand=True, padx=(12, 0))
        tk.Label(info, text="ESTIMATE SPREADSHEET  ·  each part you add is written "
                            "straight into it", bg=theme.CARD, fg=theme.MUTED,
                 font=theme.F_EYEBROW).pack(anchor="w")
        self.file_label = tk.Label(info, text="", bg=theme.CARD, fg=theme.TEXT,
                                   font=(theme.FONT, 13, "bold"), anchor="w")
        self.file_label.pack(anchor="w")
        self.file_detail = tk.Label(info, text="", bg=theme.CARD, fg=theme.MUTED,
                                    font=theme.F_SMALL, anchor="w", justify="left")
        self.file_detail.pack(anchor="w")

        buttons = ttk.Frame(left, style="Card.TFrame")
        buttons.pack(anchor="w", pady=(12, 0))
        ttk.Button(buttons, text="New spreadsheet…",
                   command=self.new_spreadsheet).pack(side="left")
        ttk.Button(buttons, text="Choose spreadsheet…",
                   command=self.choose_spreadsheet).pack(side="left", padx=(8, 0))
        tk.Frame(buttons, bg=theme.BORDER, width=1, height=26).pack(side="left", padx=12)
        self.open_excel_btn = ttk.Button(buttons, text="Open in Excel",
                                         command=self.open_in_excel)
        self.open_excel_btn.pack(side="left")
        self.undo_btn = ttk.Button(buttons, text="Undo last part", command=self.undo_last)
        self.undo_btn.pack(side="left", padx=(8, 0))

        self.file_status = StatusLabel(left, wraplength=640, justify="left")
        self.file_status.pack(anchor="w", pady=(8, 0))

        rates = tk.Frame(c, bg=theme.CARD, padx=14, pady=12,
                         highlightthickness=1, highlightbackground=theme.BORDER)
        rates.grid(row=0, column=1, sticky="ne", padx=(20, 0))
        tk.Label(rates, text="MACHINING RATES", bg=theme.CARD, fg=theme.MUTED,
                 font=theme.F_EYEBROW).grid(row=0, column=0, columnspan=2, sticky="w")
        self.cnc_rate = NumberField(rates, "CNC (₹ / hour)", minimum=0, width=9)
        self.vmc_rate = NumberField(rates, "VMC (₹ / hour)", minimum=0, width=9)
        self.cnc_rate.grid(row=1, column=0, padx=(0, 10), pady=(6, 0))
        self.vmc_rate.grid(row=1, column=1, pady=(6, 0))
        self.rates_note = tk.Label(rates, text="", bg=theme.CARD, fg=theme.MUTED,
                                   font=theme.F_SMALL, justify="left", wraplength=240)
        self.rates_note.grid(row=2, column=0, columnspan=2, sticky="w")
        self.apply_rates_btn = ttk.Button(rates, text="Apply to spreadsheet now",
                                          style="Small.TButton", command=self.apply_rates)
        self.cnc_rate.set(DEFAULT_CNC_RATE)
        self.vmc_rate.set(DEFAULT_VMC_RATE)

    def _grid_fields(self, parent, specs, columns=3):
        fields = {key: widget for key, widget, _ in specs}
        col = row = 0
        for key, widget, span in specs:
            if col + span > columns:
                row, col = row + 1, 0
            widget.grid(row=row, column=col, columnspan=span, sticky="ew",
                        padx=(0, 12), pady=(0, 4))
            col += span
        for c in range(columns):
            parent.columnconfigure(c, weight=1, uniform="f")
        return fields

    def _build_form(self, parent):
        card = Card(parent, padding=0)
        card.pack(fill="x")
        self.tab_frames = {}
        bar_holder = tk.Frame(card.body, bg=theme.CARD, padx=12, pady=4)
        bar_holder.pack(fill="x")
        self.tabs = TabBar(bar_holder, SECTIONS, self._show_tab)
        self.tabs.pack(anchor="w")
        tk.Frame(card.body, height=1, bg=theme.BORDER).pack(fill="x")
        holder = ttk.Frame(card.body, style="Card.TFrame", padding=(20, 16, 20, 18))
        holder.pack(fill="both", expand=True)
        self.tab_holder = holder
        for key, _ in SECTIONS:
            self.tab_frames[key] = ttk.Frame(holder, style="Card.TFrame")
        self._build_details_tab(self.tab_frames["details"])
        self._build_material_tab(self.tab_frames["material"])
        self._build_size_tab(self.tab_frames["size"])
        self._build_costs_tab(self.tab_frames["costs"])
        keys = [k for k, _ in SECTIONS]
        names = dict(SECTIONS)
        for i, key in enumerate(keys):
            nav = ttk.Frame(self.tab_frames[key], style="Card.TFrame")
            nav.pack(fill="x", side="bottom", pady=(14, 0))
            if i > 0:
                ttk.Button(nav, text=f"← {names[keys[i - 1]]}", style="Small.TButton",
                           command=lambda k=keys[i - 1]: self.tabs.select(k)).pack(side="left")
            if i < len(keys) - 1:
                ttk.Button(nav, text=f"Next: {names[keys[i + 1]]} →", style="Small.TButton",
                           command=lambda k=keys[i + 1]: self.tabs.select(k)).pack(side="right")
            else:
                ttk.Label(nav, text="All set? Check the preview, then click "
                                    "“Add Part to Spreadsheet”.",
                          style="Muted.TLabel").pack(side="right")

    def _show_tab(self, key):
        for frame in self.tab_frames.values():
            frame.pack_forget()
        self.tab_frames[key].pack(fill="both", expand=True)

    def _build_details_tab(self, c):
        g = ttk.Frame(c, style="Card.TFrame")
        g.pack(fill="x")
        self.text_fields = self._grid_fields(g, [
            ("date", Field(g, "Date", hint="DD-MM-YYYY"), 1),
            ("drawing", Field(g, "Drawing number"), 1),
            ("rev", Field(g, "Rev. No"), 1),
            ("description", Field(g, "Description"), 3),
            ("process", Field(g, "Process flow", hint="e.g. CUT + TURN"), 1),
            ("coating", Field(g, "Coating / painting"), 1),
            ("remarks", Field(g, "Remarks"), 1),
        ])
        self.text_fields["date"].var.set(datetime.date.today().strftime("%d-%m-%Y"))
        g2 = ttk.Frame(c, style="Card.TFrame")
        g2.pack(fill="x")
        self.qty_fields = self._grid_fields(g2, [
            ("qty_frame", NumberField(g2, "QTY / frame", minimum=0, allow_equal=False), 1),
            ("batch_qty", NumberField(g2, "Batch QTY", minimum=1, integer=True), 1),
        ])
        self.qty_fields["qty_frame"].var.set("1")
        self._build_picture(c)

    def _build_picture(self, c):
        """Part view picture: from a file, or pasted from the clipboard
        (Snipping Tool, Print Screen, "Copy image", a file copied in Explorer)."""
        ttk.Label(c, text="Part view picture", style="Field.TLabel").pack(anchor="w", pady=(4, 0))
        pic = ttk.Frame(c, style="Card.TFrame")
        pic.pack(fill="x", pady=(3, 0))
        box = tk.Frame(pic, bg=theme.READONLY_BG, width=THUMB_W + 8, height=THUMB_H + 8,
                       highlightthickness=1, highlightbackground=theme.BORDER)
        box.pack(side="left")
        box.pack_propagate(False)
        self.thumb = tk.Label(box, text="No picture", bg=theme.READONLY_BG,
                              fg=theme.MUTED, font=theme.F_SMALL)
        self.thumb.pack(expand=True)
        self._thumb_image = None
        side = ttk.Frame(pic, style="Card.TFrame")
        side.pack(side="left", fill="x", expand=True, padx=(14, 0))
        buttons = ttk.Frame(side, style="Card.TFrame")
        buttons.pack(anchor="w")
        ttk.Button(buttons, text="Choose file…", style="Small.TButton",
                   command=self.choose_image).pack(side="left")
        ttk.Button(buttons, text="Paste  (Ctrl+V)", style="Small.TButton",
                   command=self.paste_image).pack(side="left", padx=(8, 0))
        self.image_clear = ttk.Button(buttons, text="Remove", style="Link.TButton",
                                      command=lambda: self.set_image(None))
        self.image_label = ttk.Label(side, text="", style="Card.TLabel")
        self.image_label.pack(anchor="w", pady=(6, 0))
        self.image_hint = StatusLabel(side, wraplength=380, justify="left")
        self.image_hint.pack(anchor="w")
        self._show_image_tip()

    def _build_material_tab(self, c):
        ttk.Label(c, text="The material is shared with the Weight Calculator — "
                          "picking it on either side updates both.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 10))
        self.picker = MaterialPicker(c, self.app.material)
        self.picker.pack(fill="x")
        g = ttk.Frame(c, style="Card.TFrame")
        g.pack(fill="x", pady=(10, 0))
        self.rm_price = NumberField(g, "RM price / kg", unit="₹", minimum=0)
        self.rm_price.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        for col in range(3):
            g.columnconfigure(col, weight=1, uniform="m")

    def _build_size_tab(self, c):
        hint = ttk.Label(c, text="Rectangular stock: fill Length / Width / Thickness. Round "
                                 "stock: fill Outer dia / Inner dia / Length. Leave unused "
                                 "cells blank. FS (finished size) is optional.",
                         style="Muted.TLabel", wraplength=600, justify="left")
        hint.pack(anchor="w", pady=(0, 10))
        g = ttk.Frame(c, style="Card.TFrame")
        g.pack(fill="x")
        self.size_banner = Banner(c, before=g)
        ttk.Label(g, text="Rectangular (mm)", style="Field.TLabel", font=theme.F_BOLD
                  ).grid(row=0, column=1, columnspan=3, sticky="w")
        ttk.Label(g, text="Round (mm)", style="Field.TLabel", font=theme.F_BOLD
                  ).grid(row=0, column=4, columnspan=3, sticky="w")
        for i, (_, header, _) in enumerate(DIM_FIELDS):
            ttk.Label(g, text=header, style="Field.TLabel").grid(row=1, column=i + 1, sticky="w")
        self.dims = {}
        for r, (which, label) in enumerate((("rm", "RM\nRaw material"),
                                            ("fs", "FS\nFinished size"))):
            ttk.Label(g, text=label, style="Card.TLabel", font=theme.F_SMALL,
                      justify="left").grid(row=r + 2, column=0, sticky="nw", padx=(0, 10), pady=(4, 0))
            row = {}
            for i, (key, _, _) in enumerate(DIM_FIELDS):
                f = NumberField(g, None, required=False, minimum=0, width=7)
                f.grid(row=r + 2, column=i + 1, sticky="ew", padx=(0, 6))
                row[key] = f
            self.dims[which] = row
        for col in range(1, 7):
            g.columnconfigure(col, weight=1, uniform="d")
        tools = ttk.Frame(c, style="Card.TFrame")
        tools.pack(fill="x", pady=(6, 0))
        ttk.Button(tools, text="Copy RM → FS", style="Small.TButton",
                   command=self.copy_rm_to_fs).pack(side="left")
        ttk.Button(tools, text="Get size from Weight Calculator", style="Link.TButton",
                   command=lambda: self.app.show("Round Bar")).pack(side="left", padx=(8, 0))
        self.size_error = ttk.Label(c, text="", style="Error.TLabel", wraplength=600)
        self.size_error.pack(anchor="w", pady=(6, 0))

    def _build_costs_tab(self, c):
        ttk.Label(c, text="Cycle times per piece are in minutes (the template divides them "
                          "by 60); setting times are in hours.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 10))
        g = ttk.Frame(c, style="Card.TFrame")
        g.pack(fill="x")
        self.cost_fields = self._grid_fields(g, [
            ("vmc_min", NumberField(g, "VMC time / piece", unit="min", required=False), 1),
            ("vmc_set", NumberField(g, "VMC setting time", unit="hrs", required=False), 1),
            ("cutting", NumberField(g, "Cutting cost / piece", unit="₹"), 1),
            ("cnc_min", NumberField(g, "CNC time / piece", unit="min", required=False), 1),
            ("cnc_set", NumberField(g, "CNC setting time", unit="hrs", required=False), 1),
        ])
        ttk.Label(c, text="Add-ons (% of subtotal cost / piece)",
                  style="Card.TLabel", font=theme.F_BOLD).pack(anchor="w", pady=(10, 6))
        g2 = ttk.Frame(c, style="Card.TFrame")
        g2.pack(fill="x")
        self.cost_fields.update(self._grid_fields(g2, [
            ("inspection", NumberField(g2, "Inspection", unit="%", required=False), 1),
            ("transport", NumberField(g2, "Int/Ext transport", unit="%", required=False), 1),
            ("packing", NumberField(g2, "Special packing", unit="%", required=False), 1),
        ]))
        self.cost_fields["cutting"].var.set(f"{DEFAULT_CUTTING_COST:g}")
        for key in ("inspection", "transport", "packing"):
            self.cost_fields[key].var.set("0")

    def _build_preview_card(self, parent):
        card = Card(parent, "Cost preview",
                    "Live preview using the same formulas written to Excel.")
        card.pack(fill="x")
        c = card.content
        self.preview = {}
        rows = [
            ("rm_weight", "RM weight / piece", "kg"),
            ("finished_weight", "Finished weight", "kg"),
            ("rm_cost", "RM cost / piece", "₹"),
            ("machining", "Machining cost / piece", "₹"),
            ("subtotal", "Subtotal cost / piece", "₹"),
            ("scrap_return", "Scrap return", "₹"),
        ]
        key_prices = [
            ("develop_cost", "Develop part cost + 15% OHC", "₹"),
            ("prod_cost", "Prod cost only", "₹"),
            ("total_cost", "Total cost (all pieces)", "₹"),
        ]
        for i, (key, label, unit) in enumerate(rows):
            ttk.Label(c, text=label, style="Muted.TLabel", font=theme.F_BASE
                      ).grid(row=i, column=0, sticky="w", pady=2)
            v = ttk.Label(c, text="—", style="Card.TLabel", font=theme.F_BOLD)
            v.grid(row=i, column=1, sticky="e", pady=2)
            self.preview[key] = (v, unit)
        c.columnconfigure(0, weight=1)
        ttk.Separator(c).grid(row=len(rows), column=0, columnspan=2, sticky="ew", pady=10)

        keys = tk.Frame(c, bg=theme.CARD)
        keys.grid(row=len(rows) + 1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        for key, label, unit in key_prices:
            box = tk.Frame(keys, bg=theme.ACCENT_SOFT)
            box.pack(fill="x", pady=(0, 6))
            tk.Frame(box, bg=theme.ACCENT, width=4).pack(side="left", fill="y")
            tk.Label(box, text=label, bg=theme.ACCENT_SOFT, fg=theme.TEXT,
                     font=theme.F_BOLD, padx=10, pady=8).pack(side="left")
            v = tk.Label(box, text="—", bg=theme.ACCENT_SOFT, fg=theme.ACCENT,
                         font=theme.F_KEY_PRICE, padx=12)
            v.pack(side="right")
            self.preview[key] = (v, unit)

        hero = tk.Frame(c, bg=theme.ACCENT, padx=16, pady=12)
        hero.grid(row=len(rows) + 2, column=0, columnspan=2, sticky="ew")
        tk.Label(hero, text="COST / PIECE", bg=theme.ACCENT, fg="#FFEDD5",
                 font=theme.F_RESULT_LABEL).pack(anchor="w")
        self.hero = tk.Label(hero, text="—", bg=theme.ACCENT, fg="white",
                             font=(theme.FONT, 24, "bold"))
        self.hero.pack(anchor="w")

        actions = ttk.Frame(c, style="Card.TFrame")
        actions.grid(row=len(rows) + 3, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="Add Part to Spreadsheet", style="Accent.TButton",
                   command=self.add_part).pack(fill="x")
        self.dest_label = ttk.Label(actions, text="", style="Muted.TLabel")
        self.dest_label.pack(anchor="w", pady=(4, 0))
        ttk.Button(actions, text="Clear form", command=self.clear_form).pack(fill="x", pady=(8, 0))
        self.status = StatusLabel(c, wraplength=320, justify="left")
        self.status.grid(row=len(rows) + 4, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_parts_card(self, body):
        card = Card(body)
        card.pack(fill="x", pady=(16, 0))
        self.parts_title = ttk.Label(card.content, text="", style="Card.TLabel",
                                     font=theme.F_CARD_TITLE)
        self.parts_title.pack(anchor="w", pady=(0, 10))
        table = ttk.Frame(card.content, style="Card.TFrame")
        table.pack(fill="x")
        cols = ("sno", "drawing", "description", "material", "batch", "rows")
        tree = ttk.Treeview(table, columns=cols, show="headings", height=6)
        for col, text, width, anchor in (
                ("sno", "S.no", 60, "center"), ("drawing", "Drawing number", 180, "w"),
                ("description", "Description", 320, "w"), ("material", "Material", 150, "w"),
                ("batch", "Batch QTY", 90, "e"), ("rows", "Excel rows", 90, "center")):
            tree.heading(col, text=text, anchor=anchor)
            tree.column(col, width=width, anchor=anchor, stretch=col == "description")
        vbar = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vbar.set)
        tree.pack(side="left", fill="x", expand=True)
        vbar.pack(side="right", fill="y")
        self.tree = tree

    # ======================================================= spreadsheet state

    def _save_settings(self):
        settings.save({"target": self.target})

    def _restore_target(self, path):
        """Re-open the spreadsheet used last time, if it is still there."""
        if path and os.path.exists(path):
            try:
                self._set_target(path, EstimateWorkbook.open(path))
                self.file_status.ok(f"Continuing with {os.path.basename(path)}. "
                                    "New parts will be added to it.")
                return
            except EstimateError:
                pass
        self._set_target(None)
        if path:
            self.file_status.note("The spreadsheet used last time can't be found. "
                                  "Start a new one or choose an existing one.")

    def _set_target(self, path, book=None):
        self.target = path
        if book is not None:
            self._absorb(book)
        else:
            self.file_parts = []
            self.file_rates = (DEFAULT_CNC_RATE, DEFAULT_VMC_RATE)
            self._refresh_spreadsheet()
        self._save_settings()

    def _absorb(self, book):
        """Take the part list and rates from a freshly loaded/saved workbook."""
        self.file_parts = book.parts()
        self.file_rates = book.rates
        self.cnc_rate.set(self.file_rates[0])
        self.vmc_rate.set(self.file_rates[1])
        self._refresh_spreadsheet()

    def _refresh_spreadsheet(self):
        count = len(self.file_parts)
        parts = f"{count} part{'s' if count != 1 else ''}"
        if self.target:
            name = os.path.basename(self.target)
            self.file_label.configure(text=name, fg=theme.TEXT)
            self.file_detail.configure(text=f"{parts}  ·  {os.path.dirname(self.target)}")
            self.dest_label.configure(text=f"Goes to: {name}")
            self.parts_title.configure(text=f"Parts in {name}")
        else:
            self.file_label.configure(text="No spreadsheet chosen yet", fg=theme.MUTED)
            self.file_detail.configure(
                text="Start a new spreadsheet or choose an existing one. You'll also be "
                     "asked when you add your first part.")
            self.dest_label.configure(text="You'll choose a spreadsheet when adding")
            self.parts_title.configure(text="Parts in the spreadsheet")
        state = "normal" if self.target else "disabled"
        self.open_excel_btn.configure(state=state)
        self.undo_btn.configure(state="normal" if self.file_parts else "disabled")
        self.tree.delete(*self.tree.get_children())
        for p in self.file_parts:
            self.tree.insert("", "end", values=(
                p["sno"], p["drawing"] or "", p["description"] or "", p["material"] or "",
                p["batch_qty"] if p["batch_qty"] is not None else "",
                f"{p['row']}–{p['row'] + 1}"))
        if self.file_parts:
            self.tree.see(self.tree.get_children()[-1])
        self.app.set_title_suffix(os.path.basename(self.target) if self.target else None)
        self._refresh_rates_note()

    def _refresh_rates_note(self):
        try:
            rates = self._rates(quiet=True)
        except InputError:
            rates = None
        changed = self.target and rates and rates != self.file_rates
        if changed:
            self.rates_note.configure(
                text="Changed — applied with the next part, or now:", fg=theme.ACCENT_HOVER)
            self.apply_rates_btn.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        else:
            self.rates_note.configure(
                text="Stored in the spreadsheet; used by every part in it.", fg=theme.MUTED)
            self.apply_rates_btn.grid_remove()

    # ======================================================= spreadsheet actions

    def new_spreadsheet(self):
        """Create a new, empty estimate spreadsheet and make it the target."""
        try:
            rates = self._rates()
        except InputError:
            self.file_status.error("Enter valid CNC / VMC rates first.")
            return None
        path = filedialog.asksaveasfilename(
            title="Create a new estimate spreadsheet", defaultextension=".xlsx",
            filetypes=XLSX_TYPES, initialdir=default_folder(),
            initialfile=f"ProCaliber Estimate {datetime.date.today():%d-%m-%Y}.xlsx")
        if not path:
            return None
        path = os.path.abspath(path)
        if is_file_locked(path) and self._release_from_excel(path) is None:
            return None
        book = EstimateWorkbook.new()
        book.set_rates(*rates)
        try:
            book.save(path)
        except EstimateError as exc:
            messagebox.showerror("Couldn't create the spreadsheet", str(exc), parent=self)
            return None
        self._set_target(path, book)
        self.file_status.ok(f"✔ Created {os.path.basename(path)}. Parts you add will "
                            "be written to it.")
        return path

    def choose_spreadsheet(self):
        """Make an existing estimate spreadsheet the target."""
        start = os.path.dirname(self.target) if self.target else default_folder()
        path = filedialog.askopenfilename(title="Choose an estimate spreadsheet",
                                          filetypes=XLSX_TYPES, initialdir=start)
        if not path:
            return None
        path = os.path.abspath(path)
        try:
            book = EstimateWorkbook.open(path)
        except EstimateError as exc:
            messagebox.showerror("Can't use this spreadsheet", str(exc), parent=self)
            return None
        self._set_target(path, book)
        message = (f"✔ Now adding to {os.path.basename(path)} ({len(self.file_parts)} "
                   f"parts). The next part goes to row {book.next_part_row()}.")
        if is_file_locked(path):
            message += " It's open in Excel right now — it will be closed before updating."
        self.file_status.ok(message)
        return path

    def open_in_excel(self):
        if self.target:
            self._launch_excel(self.target)

    def _launch_excel(self, path):
        try:
            os.startfile(path)
        except OSError as exc:
            messagebox.showerror("Can't open the spreadsheet", str(exc), parent=self)

    def undo_last(self):
        if not self.file_parts:
            return
        last = self.file_parts[-1]
        what = last["drawing"] or last["description"] or "(no drawing number)"
        if not messagebox.askyesno(
                "Remove the last part?",
                f"Remove part {last['sno']} — {what} — from "
                f"“{os.path.basename(self.target)}”?\n\n"
                "A backup of the spreadsheet is kept before the change.",
                icon="warning", default="no", parent=self):
            return
        removed = self._update_file(lambda book: book.remove_last_part())
        if removed:
            self.file_status.ok(f"✔ Removed part {removed['sno']} from "
                                f"{os.path.basename(self.target)}.")

    def apply_rates(self):
        try:
            rates = self._rates()
        except InputError:
            return
        if self._update_file(lambda book: book.set_rates(*rates) or True):
            self.file_status.ok(f"✔ Machining rates updated in "
                                f"{os.path.basename(self.target)} — every part uses them.")

    def _update_file(self, change):
        """Apply ``change(book)`` to the target spreadsheet on disk and save.

        The file is re-read from disk first, so edits made in Excel are kept.
        If Excel has it open, it is closed first (see _release_from_excel).
        Returns change's result, or None if the update didn't happen.
        """
        path = self.target
        name = os.path.basename(path)
        if not os.path.exists(path):
            messagebox.showerror(
                "Spreadsheet not found",
                f"“{name}” can't be found at\n{path}\n\nIt may have been moved "
                "or deleted. Start a new spreadsheet or choose another one.", parent=self)
            self._set_target(None)
            return None
        reopen = False
        if is_file_locked(path):
            outcome = self._release_from_excel(path)
            if outcome is None:
                self.file_status.error(f"Not updated — {name} is still open.")
                return None
            reopen = outcome == "closed"
        try:
            book = EstimateWorkbook.open(path)
            result = change(book)
            book.save()
        except FileLockedError as exc:
            messagebox.showwarning("Spreadsheet is in use", str(exc), parent=self)
            return None
        except EstimateError as exc:
            messagebox.showerror("Couldn't update the spreadsheet", str(exc), parent=self)
            return None
        self._absorb(book)
        if reopen:
            self._launch_excel(path)
        return result

    def _release_from_excel(self, path):
        """Make sure ``path`` isn't open elsewhere before writing to it.

        Returns "closed" (we closed it in Excel), "free" (the user closed it)
        or None (still open / the user cancelled).
        """
        name = os.path.basename(path)
        while True:
            wb = excel_link.find_workbook(path)
            if wb is not None:
                save = False
                if excel_link.has_unsaved_changes(wb):
                    save = messagebox.askyesnocancel(
                        "Save your changes in Excel?",
                        f"“{name}” is open in Excel and has changes that "
                        "haven't been saved.\n\n"
                        "Yes — save those changes, then update the spreadsheet\n"
                        "No — discard the changes made in Excel\n"
                        "Cancel — don't update now", icon="warning", parent=self)
                    if save is None:
                        return None
                try:
                    excel_link.close_workbook(wb, save)
                except excel_link.ExcelBusyError as exc:
                    messagebox.showwarning("Excel is busy", str(exc), parent=self)
                    return None
                if self._wait_until_free(path):
                    return "closed"
            if not messagebox.askretrycancel(
                    "Close the spreadsheet first",
                    f"“{name}” is open in Excel or another program, so it "
                    "can't be updated.\n\nClose it there, then click Retry.", parent=self):
                return None
            if not is_file_locked(path):
                return "free"

    def _wait_until_free(self, path, seconds=6):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if not is_file_locked(path):
                return True
            self.update()
            time.sleep(0.15)
        return not is_file_locked(path)

    def _ask_destination(self):
        """No spreadsheet yet: ask whether to create one or use an existing one."""
        dialog = tk.Toplevel(self)
        dialog.title("Where should this part go?")
        dialog.configure(bg=theme.CARD)
        dialog.transient(self.winfo_toplevel())
        dialog.resizable(False, False)
        choice = {"value": None}
        frame = tk.Frame(dialog, bg=theme.CARD, padx=24, pady=20)
        frame.pack()
        tk.Label(frame, text="Choose the spreadsheet for this estimate",
                 bg=theme.CARD, fg=theme.TEXT, font=theme.F_CARD_TITLE).pack(anchor="w")
        tk.Label(frame, text="The parts you add next will keep going into the same "
                             "spreadsheet until you choose another one.",
                 bg=theme.CARD, fg=theme.MUTED, font=theme.F_BASE, wraplength=420,
                 justify="left").pack(anchor="w", pady=(4, 16))

        def pick(value):
            choice["value"] = value
            dialog.destroy()

        ttk.Button(frame, text="Create a new spreadsheet…", style="Accent.TButton",
                   command=lambda: pick("new")).pack(fill="x")
        ttk.Button(frame, text="Add to an existing spreadsheet…",
                   command=lambda: pick("existing")).pack(fill="x", pady=(8, 0))
        ttk.Button(frame, text="Cancel", style="Link.TButton",
                   command=dialog.destroy).pack(pady=(10, 0))
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        dialog.update_idletasks()
        top = self.winfo_toplevel()
        x = top.winfo_rootx() + (top.winfo_width() - dialog.winfo_width()) // 2
        y = top.winfo_rooty() + (top.winfo_height() - dialog.winfo_height()) // 3
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dialog.grab_set()
        self.wait_window(dialog)
        if choice["value"] == "new":
            return self.new_spreadsheet()
        if choice["value"] == "existing":
            return self.choose_spreadsheet()
        return None

    # ================================================================ the form

    def _all_vars(self):
        fields = [*self.text_fields.values(), *self.qty_fields.values(),
                  *self.cost_fields.values(), self.rm_price, self.cnc_rate, self.vmc_rate]
        for row in self.dims.values():
            fields.extend(row.values())
        state = self.app.material
        return [f.var for f in fields] + [state.material, state.sg, state.custom_name]

    def _rates(self, quiet=False):
        values = collect({"cnc": self.cnc_rate, "vmc": self.vmc_rate}, quiet=quiet)
        return values["cnc"], values["vmc"]

    def _read_details(self, quiet):
        failed = False
        try:
            qty = collect(self.qty_fields, quiet)
        except InputError:
            failed, qty = True, None
        date_field = self.text_fields["date"]
        try:
            date = parse_date(date_field.get())
        except InputError as exc:
            if not quiet:
                date_field.set_error(str(exc))
            failed, date = True, None
        if failed:
            raise InputError("Part details")
        return {"date": date, **qty}

    def _read_material(self, quiet):
        failed = False
        try:
            name, sg = self.app.material.resolve() if quiet else self.picker.resolve()
        except InputError:
            failed, name, sg = True, None, None
        try:
            price = self.rm_price.value(quiet)
        except InputError:
            failed, price = True, None
        if failed:
            raise InputError("Material")
        return {"name": name, "sg": sg, "price": price}

    def _read_dims(self, which, quiet):
        row = self.dims[which]
        values = collect(row, quiet=quiet)
        o, p, q, r, s, t = (values[k] for k, _, _ in DIM_FIELDS)
        label = "RM" if which == "rm" else "FS"
        rect = [o, p, q]
        if any(v is not None for v in rect) and not all(v is not None for v in rect):
            raise InputError(f"{label}: fill all of Length, Width and Thickness (or none).")
        if any(v is not None for v in (r, s, t)):
            if r is None or t is None:
                raise InputError(f"{label}: round stock needs Outer dia and Length.")
            if s is not None and s >= r:
                raise InputError(f"{label}: Inner dia must be smaller than Outer dia.")
        if all(v is None for v in (o, p, q, r, s, t)) and which == "rm":
            raise InputError("Enter the RM (raw material) size.")
        return Dimensions(**{attr: values[k] for k, _, attr in DIM_FIELDS})

    def _read_size(self, quiet):
        messages, dims = [], {}
        for which in ("rm", "fs"):
            try:
                dims[which] = self._read_dims(which, quiet)
            except InputError as exc:
                messages.append(str(exc))
        if not quiet:
            generic = "Please correct the highlighted fields."
            self.size_error.configure(text=" ".join(m for m in messages if m != generic)
                                      or (generic if messages else ""))
        if messages:
            raise InputError("Size")
        return dims

    def _read_costs(self, quiet):
        values = collect(self.cost_fields, quiet)
        return {k: (v or 0) for k, v in values.items()}

    def _read_sections(self, quiet):
        """({section: values}, [sections with missing/invalid fields])."""
        results, failed = {}, []
        for key, _ in SECTIONS:
            try:
                results[key] = getattr(self, f"_read_{key}")(quiet)
            except InputError:
                failed.append(key)
        return results, failed

    def _build_part(self, r):
        text = {k: f.get() for k, f in self.text_fields.items()}
        d, m, s, c = r["details"], r["material"], r["size"], r["costs"]
        return PartInput(
            material=m["name"], specific_gravity=m["sg"],
            batch_qty=d["batch_qty"], qty_per_frame=d["qty_frame"],
            rm_price_per_kg=m["price"], rm=s["rm"], fs=s["fs"], date=d["date"],
            drawing_number=text["drawing"], rev_no=text["rev"],
            description=text["description"], process_flow=text["process"],
            coating=text["coating"], remarks=text["remarks"],
            part_view_image=self.image_path, cutting_cost=c["cutting"],
            vmc_min_per_piece=c["vmc_min"], vmc_setting_hours=c["vmc_set"],
            cnc_min_per_piece=c["cnc_min"], cnc_setting_hours=c["cnc_set"],
            inspection_pct=c["inspection"], transport_pct=c["transport"],
            packing_pct=c["packing"])

    def read_part(self, quiet=False):
        results, failed = self._read_sections(quiet)
        if failed:
            raise InputError("Please correct the highlighted fields.")
        return self._build_part(results)

    # ================================================================ preview

    def _schedule_preview(self):
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(150, self._update_preview)

    def _update_preview(self):
        self._preview_job = None
        try:
            part = self.read_part(quiet=True)
            cnc, vmc = self._rates(quiet=True)
        except InputError:
            for label, _ in self.preview.values():
                label.configure(text="—")
            self.hero.configure(text="—")
            return
        c = compute_costs(part, cnc, vmc)
        c["machining"] = c["cnc_machining_cost"] + c["vmc_machining_cost"]
        for key, (label, unit) in self.preview.items():
            label.configure(text=f"{fmt(c[key], 3)} kg" if unit == "kg" else fmt_money(c[key]))
        self.hero.configure(text=fmt_money(c["cost_per_piece"]))

    # ================================================================ adding

    def add_part(self):
        self.status.clear()
        results, failed = self._read_sections(quiet=False)
        if failed:
            names = dict(SECTIONS)
            self.tabs.select(failed[0])
            self.status.error("Some required details are missing or invalid. Check the "
                              "highlighted fields on: "
                              + ", ".join(names[k] for k in failed) + ".")
            return False
        try:
            rates = self._rates()
        except InputError:
            self.status.error("Enter valid CNC / VMC machining rates at the top.")
            return False
        part = self._build_part(results)
        if not self.target and not self._ask_destination():
            self.status.note("Not added — choose a spreadsheet first.")
            return False

        def change(book):
            book.set_rates(*rates)
            return book.add_part(part)

        row = self._update_file(change)
        if row is None:
            return False
        name = os.path.basename(self.target)
        sno = next((p["sno"] for p in self.file_parts if p["row"] == row), "")
        message = f"✔ Part {sno} added to {name} (rows {row}–{row + 1})."
        self.status.ok(message)
        self.file_status.ok(f"{message} Last updated {datetime.datetime.now():%H:%M}.")
        for key in ("drawing", "rev", "description"):
            self.text_fields[key].var.set("")
        self.set_image(None)
        self._added_snapshot = self._form_snapshot()
        self.tabs.select("details")
        return True

    def _form_snapshot(self):
        rate_vars = {str(self.cnc_rate.var), str(self.vmc_rate.var)}
        return tuple(v.get() for v in self._all_vars()
                     if str(v) not in rate_vars) + (self.image_path,)

    def has_pending_part(self):
        """True if the form holds a valid part that hasn't been added yet."""
        if self._form_snapshot() == self._added_snapshot:
            return False
        try:
            self.read_part(quiet=True)
        except InputError:
            return False
        return True

    def confirm_close(self):
        if not self.has_pending_part():
            return True
        return messagebox.askyesno(
            "Part not added yet",
            "A part is filled in on the Cost Estimator but hasn't been added to the "
            "spreadsheet.\n\nClose the app anyway?", icon="warning", default="no",
            parent=self)

    # ================================================================ form helpers

    def copy_rm_to_fs(self):
        for key, _, _ in DIM_FIELDS:
            self.dims["fs"][key].var.set(self.dims["rm"][key].var.get())

    def receive_dimensions(self, which, dims, source):
        """Fill the RM or FS size row from a Weight Calculator page."""
        row = self.dims[which]
        previous = {key: f.var.get() for key, f in row.items()}
        for key, _, attr in DIM_FIELDS:
            value = getattr(dims, attr)
            row[key].set(value if value is not None else "")
        self._undo_size = (which, previous)
        label = "RM (raw material)" if which == "rm" else "FS (finished)"
        self.size_banner.show(
            f"{label} size from Weight Calculator ({source}): {dims.describe()}"
            f"  ·  {datetime.datetime.now():%H:%M}",
            kind="info", action_text="Undo", action=self._undo_received_size)

    def _undo_received_size(self):
        if self._undo_size:
            which, previous = self._undo_size
            for key, value in previous.items():
                self.dims[which][key].var.set(value)
            self._undo_size = None
        self.size_banner.hide()

    def clear_form(self):
        for key in ("drawing", "rev", "description", "remarks"):
            self.text_fields[key].var.set("")
        for row in self.dims.values():
            for f in row.values():
                f.var.set("")
        self.set_image(None)
        self.size_error.configure(text="")
        self.size_banner.hide()
        self.status.clear()
        self.tabs.select("details")

    # ================================================================ picture

    def choose_image(self):
        path = filedialog.askopenfilename(title="Choose part view picture",
                                          filetypes=IMAGE_TYPES)
        if path:
            self.set_image(path)

    def _show_image_tip(self):
        self.image_hint.configure(
            text="Tip: take a snip with Win+Shift+S (or copy any picture), "
                 "then press Ctrl+V here.", foreground=theme.MUTED)

    def _on_ctrl_v(self, event):
        """Ctrl+V on this page pastes a picture. Inside a text field it still
        pastes text as usual, unless the clipboard holds only a picture."""
        if self.app.current != "Cost Estimate":
            return
        if isinstance(event.widget, (tk.Entry, tk.Text)):
            try:
                if self.clipboard_get():
                    return  # normal text paste
            except tk.TclError:
                pass  # no text on the clipboard, so try a picture
        self.paste_image()

    def paste_image(self):
        try:
            from PIL import ImageGrab
            data = ImageGrab.grabclipboard()
        except Exception:
            data = None
        if isinstance(data, list):  # file(s) copied in File Explorer
            files = [p for p in data if os.path.splitext(p)[1].lower() in IMAGE_EXTS]
            if files:
                self.set_image(files[0])
                return
            data = None
        if data is None:
            self.image_hint.error(
                "No picture on the clipboard. Take a snip with Win+Shift+S or copy "
                "a picture first, then click Paste.")
            return
        try:
            folder = app_data_dir("Pictures")
            path = os.path.join(folder, f"Pasted {datetime.datetime.now():%Y-%m-%d %H%M%S}.png")
            (data if data.mode in ("RGB", "RGBA") else data.convert("RGBA")).save(path, "PNG")
            _prune(folder, PASTED_TO_KEEP)
        except Exception as exc:
            self.image_hint.error(f"Couldn't use the pasted picture: {exc}")
            return
        self.tabs.select("details")
        self.set_image(path, label=f"Pasted picture ({data.width} × {data.height})")

    def set_image(self, path, label=None):
        if path:
            try:
                from PIL import Image, ImageTk
                with Image.open(path) as src:
                    src.load()
                    thumb = src.convert("RGBA")
                thumb.thumbnail((THUMB_W, THUMB_H))
                self._thumb_image = ImageTk.PhotoImage(thumb)
            except Exception as exc:
                self.image_hint.error(f"Couldn't read that picture: {exc}")
                return
            self.thumb.configure(image=self._thumb_image, text="")
            name = label or os.path.basename(path)
            self.image_label.configure(text=name if len(name) <= 40 else name[:37] + "…")
            self.image_clear.pack(side="left", padx=(8, 0))
            self.image_hint.ok("✔ Attached — goes into the Part View column.")
        else:
            self._thumb_image = None
            self.thumb.configure(image="", text="No picture")
            self.image_label.configure(text="")
            self.image_clear.pack_forget()
            self._show_image_tip()
        self.image_path = path
