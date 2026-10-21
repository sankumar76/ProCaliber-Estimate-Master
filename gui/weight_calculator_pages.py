"""Module A - Weight Calculator pages (spec section 4)."""

import tkinter as tk
from tkinter import ttk

from core import calculations as calc
from core import materials, sections
from core.estimate_workbook import Dimensions
from gui import diagrams, theme
from gui.widgets import (Card, InputError, MaterialPicker, NumberField,
                         ScrollableFrame, StatusLabel, collect, fmt, page_header)

STANDARD, CUSTOM = "standard", "custom"
MODULE = "Weight Calculator"
LIVE_DELAY_MS = 200


def _module_header(body, title, subtitle):
    page_header(body, title, subtitle, module=MODULE, color=theme.WEIGHT_DARK)


class ShapePage(ttk.Frame):
    """A calculator page: material + dimensions -> area and weight.

    Results update live as the user types. For shapes that map onto the
    estimate's material-size columns (round bar, pipe, plate), the size is
    also sent to the Cost Estimator as the RM (raw material) size.

    Subclasses set ``title``/``subtitle``/``fields``/``diagram`` and implement
    ``compute(values, sg)`` returning (area, weight, length_for_kg_per_m).
    """

    title = ""
    subtitle = ""
    fields = ()               # (key, label) pairs, all in mm
    diagram = None            # sketch name in gui.diagrams
    area_label = "Cross-section area"
    show_per_metre = True

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._live_job = None
        self._last_sent = None
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        _module_header(body, self.title, self.subtitle)

        cols = ttk.Frame(body)
        cols.pack(fill="x")
        cols.columnconfigure(0, weight=3, uniform="cols")
        cols.columnconfigure(1, weight=2, uniform="cols")
        left = ttk.Frame(cols)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        right = ttk.Frame(cols)
        right.grid(row=0, column=1, sticky="nsew")

        # ---- left: inputs
        self.build_section_card(left)

        mat = Card(left, "Material")
        mat.pack(fill="x", pady=(0, 14))
        self.picker = MaterialPicker(mat.content, app.material)
        self.picker.pack(fill="x")

        dims = Card(left, "Dimensions", "All dimensions in millimetres. "
                                        "Letters match the sketch.")
        dims.pack(fill="x", pady=(0, 14))
        self.inputs = {}
        grid = dims.content
        for i, (key, label) in enumerate(self.fields):
            f = NumberField(grid, label, minimum=0,
                            allow_equal=self.allow_zero(key))
            f.grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 14), pady=(0, 6))
            f.entry.bind("<Return>", lambda _e: self.calculate())
            f.var.trace_add("write", lambda *_: self._schedule_live())
            self.inputs[key] = f
        for c in range(3):
            grid.columnconfigure(c, weight=1, uniform="dims")

        actions = ttk.Frame(left)
        actions.pack(fill="x")
        ttk.Button(actions, text="Calculate", style="Accent.TButton",
                   command=self.calculate).pack(side="left")
        ttk.Button(actions, text="Clear", command=self.clear).pack(side="left", padx=(8, 0))
        ttk.Label(actions, text="Results update as you type.", foreground=theme.MUTED,
                  font=theme.F_SMALL).pack(side="left", padx=(14, 0))

        # ---- right: result, sketch, link to the estimator
        res = Card(right, "Result")
        res.pack(fill="x", pady=(0, 14))
        hero = tk.Frame(res.content, bg=theme.INFO_SOFT, padx=16, pady=12)
        hero.pack(fill="x")
        tk.Label(hero, text="WEIGHT", bg=theme.INFO_SOFT, fg=theme.MUTED,
                 font=theme.F_RESULT_LABEL).pack(anchor="w")
        line = tk.Frame(hero, bg=theme.INFO_SOFT)
        line.pack(anchor="w")
        self.weight_value = tk.Label(line, text="—", bg=theme.INFO_SOFT,
                                     fg=theme.WEIGHT_DARK, font=(theme.FONT, 26, "bold"))
        self.weight_value.pack(side="left")
        tk.Label(line, text=" kg", bg=theme.INFO_SOFT, fg=theme.MUTED,
                 font=theme.F_CARD_TITLE).pack(side="left", anchor="s", pady=(0, 8))
        rows = ttk.Frame(res.content, style="Card.TFrame")
        rows.pack(fill="x", pady=(10, 0))
        rows.columnconfigure(0, weight=1)
        self.area_value = self._result_row(rows, 0, self.area_label, "mm²")
        self.kgm_value = (self._result_row(rows, 1, "Weight per metre", "kg/m")
                          if self.show_per_metre else None)
        self.status = StatusLabel(res.content)
        self.status.pack(anchor="w", pady=(6, 0))

        if self.diagram:
            sketch = Card(right, "Cross-section")
            sketch.pack(fill="x", pady=(0, 14))
            diagrams.make(sketch.content, self.diagram).pack()

        if self.to_dimensions({}) is not None:
            link = Card(right, "Cost Estimator",
                        "The raw-material (RM) size is sent to the Cost Estimator "
                        "automatically as you calculate.")
            link.pack(fill="x")
            self.link_status = StatusLabel(link.content, wraplength=320, justify="left")
            self.link_status.pack(anchor="w")
            buttons = ttk.Frame(link.content, style="Card.TFrame")
            buttons.pack(anchor="w", pady=(8, 0))
            ttk.Button(buttons, text="Open Cost Estimator →", style="Small.TButton",
                       command=lambda: app.show("Cost Estimate")).pack(side="left")
            ttk.Button(buttons, text="Use as FS size instead", style="Link.TButton",
                       command=lambda: self.send("fs")).pack(side="left", padx=(8, 0))

        state = app.material
        for var in (state.material, state.sg, state.custom_name):
            var.trace_add("write", lambda *_: self._schedule_live())

    def _result_row(self, parent, row, label, unit):
        ttk.Label(parent, text=label, style="Muted.TLabel", font=theme.F_BASE
                  ).grid(row=row, column=0, sticky="w", pady=3)
        value = ttk.Label(parent, text="—", style="Card.TLabel", font=theme.F_BOLD)
        value.grid(row=row, column=1, sticky="e", pady=3)
        ttk.Label(parent, text=unit, style="Muted.TLabel").grid(row=row, column=2, sticky="w",
                                                                padx=(4, 0))
        return value

    # hooks ------------------------------------------------------------------

    def build_section_card(self, body):
        pass

    def allow_zero(self, key):
        return False

    def validate(self, values):
        """Extra cross-field checks; return {key: message} for problems."""
        return {}

    def compute(self, values, sg):
        raise NotImplementedError

    def to_dimensions(self, values):
        """Map to the estimate's material-size block, or None if unsupported."""
        return None

    # actions ----------------------------------------------------------------

    def read(self, quiet=False):
        """(values, sg), or (None, None) if anything is missing/invalid."""
        if not quiet:
            self.status.clear()
        errors = False
        try:
            _, sg = self.app.material.resolve() if quiet else self.picker.resolve()
        except InputError:
            errors = True
        try:
            values = collect(self.inputs, quiet=quiet)
        except InputError:
            values, errors = None, True
        if values is not None:
            for key, message in self.validate(values).items():
                if not quiet:
                    self.inputs[key].set_error(message)
                errors = True
        if errors:
            if not quiet:
                self.status.error("Please correct the highlighted fields.")
            return None, None
        return values, sg

    def _schedule_live(self):
        if self._live_job:
            self.after_cancel(self._live_job)
        self._live_job = self.after(LIVE_DELAY_MS, self._live)

    def _live(self):
        self._live_job = None
        values, sg = self.read(quiet=True)
        if values is None:
            self.clear_results()
            return
        self._show(values, sg)

    def calculate(self):
        values, sg = self.read()
        if values is None:
            self.clear_results()
            return None
        self._show(values, sg)
        return values

    def _show(self, values, sg):
        area, weight, length = self.compute(values, sg)
        self.area_value.configure(text=fmt(area, 2))
        self.weight_value.configure(text=fmt(weight, 3))
        if self.kgm_value is not None:
            self.kgm_value.configure(text=fmt(weight / length * 1000 if length else None, 3))
        self._auto_send(values)

    def _auto_send(self, values):
        """Send the RM size to the Cost Estimator when it changes (only from
        the page the user is working on)."""
        dims = self.to_dimensions(values)
        if dims is None or self.app.pages.get(self.app.current) is not self:
            return
        key = dims.values()
        if key == self._last_sent:
            return
        self._last_sent = key
        self.app.send_to_estimator("rm", dims, self.title, navigate=False)
        self.link_status.ok(f"✔ RM size sent: {dims.describe()}")

    def clear_results(self):
        for label in (self.area_value, self.weight_value, self.kgm_value):
            if label is not None:
                label.configure(text="—")

    def clear(self):
        for f in self.inputs.values():
            if str(f.entry.cget("state")) != "readonly":
                f.var.set("")
            f.clear_error()
        self.clear_results()
        self.status.clear()

    def send(self, which):
        values = self.calculate()
        if values is None:
            return
        self.app.send_to_estimator(which, self.to_dimensions(values), self.title)


# ---- simple shapes ------------------------------------------------------------

class RoundBarPage(ShapePage):
    title = "Solid Shaft / Round Bar"
    subtitle = "Weight of a solid round bar from its diameter and length."
    fields = (("d", "Diameter (D)"), ("length", "Length (L)"))
    diagram = "round_bar"

    def compute(self, v, sg):
        return (*calc.round_bar(v["d"], v["length"], sg), v["length"])

    def to_dimensions(self, v):
        return Dimensions(outer_dia=v.get("d"), round_length=v.get("length"))


class PipePage(ShapePage):
    title = "Hollow Shaft / Pipe"
    subtitle = "Weight of a tube or hollow shaft from its outer and inner diameters."
    fields = (("od", "External diameter (OD)"), ("id", "Internal diameter (ID)"),
              ("length", "Length (L)"))
    diagram = "pipe"

    def allow_zero(self, key):
        return key == "id"

    def validate(self, v):
        if v["id"] >= v["od"]:
            return {"id": "Must be smaller than the external diameter"}
        return {}

    def compute(self, v, sg):
        return (*calc.pipe(v["od"], v["id"], v["length"], sg), v["length"])

    def to_dimensions(self, v):
        return Dimensions(outer_dia=v.get("od"), inner_dia=v.get("id"),
                          round_length=v.get("length"))


class BoxSectionPage(ShapePage):
    title = "Box Section"
    subtitle = "Rectangular hollow section (outer size, wall thickness, total length)."
    fields = (("sl", "Section length (L)"), ("sw", "Section width (W)"),
              ("t", "Wall thickness (t)"), ("length", "Total length"))
    diagram = "box_section"

    def compute(self, v, sg):
        return (*calc.box_section(v["sl"], v["sw"], v["t"], v["length"], sg), v["length"])


class PlatePage(ShapePage):
    title = "Plate"
    subtitle = "Weight of a flat plate or block."
    fields = (("length", "Length (L)"), ("width", "Width (W)"), ("t", "Thickness (T)"))
    diagram = "plate"
    area_label = "Face area (L × W)"
    show_per_metre = False

    def compute(self, v, sg):
        return (*calc.plate(v["length"], v["width"], v["t"], sg), None)

    def to_dimensions(self, v):
        return Dimensions(length=v.get("length"), width=v.get("width"),
                          thickness=v.get("t"))


# ---- standard IS sections ----------------------------------------------------

class SectionPage(ShapePage):
    """Shape with a Standard IS Section / Custom toggle."""

    table = {}
    dim_keys = ()            # keys filled from the table, in table order

    def series_of(self, designation):
        return designation.split()[0]

    def build_section_card(self, body):
        card = Card(body, "Section",
                    "Pick a standard IS designation to fill in the dimensions, "
                    "or switch to Custom to enter any size.")
        card.pack(fill="x", pady=(0, 14))
        c = card.content
        self.mode = tk.StringVar(value=STANDARD)
        modes = ttk.Frame(c, style="Card.TFrame")
        modes.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Radiobutton(modes, text="Standard IS Section", value=STANDARD,
                        variable=self.mode, command=self.on_mode).pack(side="left")
        ttk.Radiobutton(modes, text="Custom", value=CUSTOM,
                        variable=self.mode, command=self.on_mode).pack(side="left", padx=(18, 0))

        self.groups = {}
        for name in self.table:
            self.groups.setdefault(self.series_of(name), []).append(name)
        self.series = tk.StringVar(value=next(iter(self.groups)))
        self.designation = tk.StringVar()

        box = ttk.Frame(c, style="Card.TFrame")
        box.grid(row=1, column=0, sticky="ew", padx=(0, 14))
        ttk.Label(box, text="Series", style="Field.TLabel").pack(anchor="w")
        self.series_combo = ttk.Combobox(box, textvariable=self.series, state="readonly",
                                         values=list(self.groups))
        self.series_combo.pack(fill="x", pady=(3, 0))

        box2 = ttk.Frame(c, style="Card.TFrame")
        box2.grid(row=1, column=1, sticky="ew")
        ttk.Label(box2, text="Designation", style="Field.TLabel").pack(anchor="w")
        self.desig_combo = ttk.Combobox(box2, textvariable=self.designation, state="readonly")
        self.desig_combo.pack(fill="x", pady=(3, 0))
        c.columnconfigure(0, weight=1, uniform="sec")
        c.columnconfigure(1, weight=1, uniform="sec")

        self.steel_note = ttk.Label(c, text="", style="Muted.TLabel")
        self.steel_note.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.series.trace_add("write", lambda *_: self.on_series())
        self.designation.trace_add("write", lambda *_: self.fill_from_table())
        self.app.material.material.trace_add("write", lambda *_: self.update_note())

    def on_series(self):
        names = self.groups.get(self.series.get(), [])
        self.desig_combo.configure(values=names)
        if names:
            self.designation.set(names[0])

    def fill_from_table(self):
        dims = self.table.get(self.designation.get())
        if dims is None or self.mode.get() != STANDARD:
            return
        for key, value in zip(self.dim_keys, dims):
            f = self.inputs[key]
            f.entry.configure(state="normal")
            f.set(float(value))
            f.entry.configure(state="readonly")

    def on_mode(self):
        standard = self.mode.get() == STANDARD
        for key in self.dim_keys:
            self.inputs[key].set_readonly(standard)
        combo_state = "readonly" if standard else "disabled"
        self.series_combo.configure(state=combo_state)
        self.desig_combo.configure(state=combo_state)
        if standard:
            self.fill_from_table()
        self.update_note()

    def update_note(self):
        if self.mode.get() == STANDARD and not self.app.material.is_steel():
            self.steel_note.configure(
                text="Note: standard IS sections are rolled steel shapes. "
                     "Use Custom mode for other materials.",
                foreground=theme.ACCENT_HOVER)
        else:
            self.steel_note.configure(text="")

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.on_series()
        self.on_mode()


class _FlangedSectionPage(SectionPage):
    fields = (("h", "Section height (H)"), ("b", "Section width (B)"),
              ("tw", "Web thickness (tw)"), ("tf", "Flange thickness (tf)"),
              ("length", "Length"))
    dim_keys = ("h", "b", "tw", "tf")

    def compute(self, v, sg):
        return (*calc.beam_or_channel(v["h"], v["b"], v["tw"], v["tf"],
                                      v["length"], sg), v["length"])


class BeamPage(_FlangedSectionPage):
    title = "Beam Section"
    subtitle = "I-beams to IS 808 (ISJB, ISLB, ISMB, ISWB, ISHB, parallel flange)."
    table = sections.BEAMS
    diagram = "beam"

    def series_of(self, designation):
        return "Parallel flange (P)" if "(P)" in designation else designation.split()[0]


class ChannelPage(_FlangedSectionPage):
    title = "Channel Section"
    subtitle = "Channels to IS 808 (ISJC, ISLC, ISMC, ISCG)."
    table = sections.CHANNELS
    diagram = "channel"


class AnglePage(SectionPage):
    title = "Angle Section"
    subtitle = "Equal and unequal angles to IS 1852."
    table = sections.ANGLES
    fields = (("a", "Leg A"), ("b", "Leg B"), ("t", "Thickness (t)"), ("length", "Length"))
    dim_keys = ("a", "b", "t")
    diagram = "angle"

    def series_of(self, designation):
        return "Equal angles" if designation in sections.EQUAL_ANGLES else "Unequal angles"

    def validate(self, v):
        if v["t"] >= min(v["a"], v["b"]):
            return {"t": "Must be smaller than both legs"}
        return {}

    def compute(self, v, sg):
        return (*calc.angle(v["a"], v["b"], v["t"], v["length"], sg), v["length"])


class TeePage(SectionPage):
    title = "Tee Section"
    subtitle = "Tee bars to IS 1173 (ISNT, ISDT, ISLT, ISMT)."
    table = sections.TEES
    fields = _FlangedSectionPage.fields
    dim_keys = ("h", "b", "tw", "tf")
    diagram = "tee"

    def compute(self, v, sg):
        return (*calc.tee(v["h"], v["b"], v["tw"], v["tf"], v["length"], sg), v["length"])


# ---- reference & utilities ---------------------------------------------------

class SpecificGravityPage(ttk.Frame):
    title = "Specific Gravity"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        _module_header(body, "Specific Gravity Reference",
                       "Materials shared by the Weight Calculator and the Cost Estimator.")
        card = Card(body, "Materials",
                    "Double-click a material (or select it and press the button) to "
                    "make it the current material everywhere in the app.")
        card.pack(fill="x")
        tree = ttk.Treeview(card.content, columns=("sg", "density"), show="tree headings",
                            height=len(materials.MATERIALS), selectmode="browse")
        tree.heading("#0", text="Material", anchor="w")
        tree.heading("sg", text="Specific gravity (g/cm³)", anchor="e")
        tree.heading("density", text="Density (kg/m³)", anchor="e")
        tree.column("#0", width=260)
        tree.column("sg", width=200, anchor="e")
        tree.column("density", width=180, anchor="e")
        for name, sg in materials.MATERIALS:
            tree.insert("", "end", iid=name, text="  " + name,
                        values=(f"{sg:.2f}", f"{sg * 1000:,.0f}"))
        tree.pack(fill="x")
        tree.bind("<Double-1>", lambda _e: self.use())
        self.tree = tree

        row = ttk.Frame(card.content, style="Card.TFrame")
        row.pack(fill="x", pady=(12, 0))
        ttk.Button(row, text="Use selected material", style="Accent.TButton",
                   command=self.use).pack(side="left")
        self.status = StatusLabel(row)
        self.status.pack(side="left", padx=12)
        ttk.Label(card.content, style="Muted.TLabel",
                  text="Not listed? Choose “Custom...” in any material "
                       "dropdown and type its specific gravity.").pack(anchor="w", pady=(10, 0))

    def use(self):
        sel = self.tree.selection()
        if not sel:
            self.status.error("Select a material first.")
            return
        self.app.material.select(sel[0])
        self.status.ok(f"{sel[0]} is now the current material.")


class UnitConverterPage(ttk.Frame):
    title = "Unit Converter"

    def __init__(self, parent, app):
        super().__init__(parent)
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        _module_header(body, "Unit Converter", "Quick length and weight conversions.")
        self._converter(body, "Length", calc.LENGTH_UNITS, "mm", "inch")
        self._converter(body, "Weight", calc.WEIGHT_UNITS, "kg", "lb")

        facts = Card(body, "Handy reference")
        facts.pack(fill="x")
        for text in ("1 cu.m = 1000 litres = 220 gallons",
                     "2.2046 Pounds = 1 Kg",
                     "304.8 mm = 1 foot",
                     "25.4 mm = 1 inch"):
            ttk.Label(facts.content, text="•  " + text,
                      style="Card.TLabel").pack(anchor="w", pady=2)

    def _converter(self, body, title, units, from_default, to_default):
        card = Card(body, title)
        card.pack(fill="x", pady=(0, 14))
        c = card.content
        value = tk.StringVar(value="1")
        src = tk.StringVar(value=from_default)
        dst = tk.StringVar(value=to_default)
        names = list(units)

        def column(col, label, widget_factory):
            box = ttk.Frame(c, style="Card.TFrame")
            box.grid(row=0, column=col, sticky="ew", padx=(0, 12))
            ttk.Label(box, text=label, style="Field.TLabel").pack(anchor="w")
            w = widget_factory(box)
            w.pack(fill="x", pady=(3, 0))
            return w

        column(0, "Value", lambda p: ttk.Entry(p, textvariable=value))
        column(1, "From", lambda p: ttk.Combobox(p, textvariable=src, values=names,
                                                 state="readonly", width=10))
        ttk.Button(c, text="Swap", style="Small.TButton",
                   command=lambda: (lambda a, b: (src.set(b), dst.set(a)))(src.get(), dst.get())
                   ).grid(row=0, column=2, sticky="s", padx=(0, 12))
        column(3, "To", lambda p: ttk.Combobox(p, textvariable=dst, values=names,
                                               state="readonly", width=10))
        result = tk.Label(c, text="", bg=theme.CARD, fg=theme.WEIGHT_DARK, font=theme.F_RESULT)
        result.grid(row=1, column=0, columnspan=5, sticky="w", pady=(14, 0))
        for col, weight in ((0, 2), (1, 1), (3, 1)):
            c.columnconfigure(col, weight=weight)

        def update(*_):
            text = value.get().strip().replace(",", "")
            try:
                v = float(text)
            except ValueError:
                result.configure(text="Enter a number" if text else "",
                                 fg=theme.ERROR, font=theme.F_BASE)
                return
            out = calc.convert(v, src.get(), dst.get(), units)
            result.configure(text=f"{v:,.6g} {src.get()} = {out:,.6g} {dst.get()}",
                             fg=theme.WEIGHT_DARK, font=theme.F_RESULT)

        for var in (value, src, dst):
            var.trace_add("write", update)
        update()


SHAPE_PAGES = [
    ("Round Bar", RoundBarPage),
    ("Pipe", PipePage),
    ("Box Section", BoxSectionPage),
    ("Plate", PlatePage),
]

SECTION_PAGES = [
    ("Beam", BeamPage),
    ("Channel", ChannelPage),
    ("Angle", AnglePage),
    ("Tee", TeePage),
]
