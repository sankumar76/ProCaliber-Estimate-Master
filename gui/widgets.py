"""Reusable UI building blocks."""

import tkinter as tk
from tkinter import ttk

from core import materials
from gui import theme


class InputError(ValueError):
    """Raised by a field whose content is invalid; message is user-facing."""


def parse_number(text, *, required=True, minimum=0.0, allow_equal=True, integer=False):
    text = (text or "").strip().replace(",", "")
    if not text:
        if required:
            raise InputError("Required")
        return None
    try:
        value = float(text)
    except ValueError:
        raise InputError("Enter a number")
    if integer and value != int(value):
        raise InputError("Enter a whole number")
    if minimum is not None:
        if value < minimum or (not allow_equal and value == minimum):
            raise InputError(f"Must be {'at least' if allow_equal else 'more than'} {minimum:g}")
    return int(value) if integer else value


def fmt(value, decimals=3):
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}"


def fmt_money(value):
    return "—" if value is None else f"₹ {value:,.2f}"


# ---- layout ----------------------------------------------------------------

WHEEL_NOTCH_PX = 60  # page scroll distance for one mouse-wheel notch


def disable_combobox_wheel(root):
    """Stop the wheel/touchpad from silently changing dropdown values while
    the user scrolls the page past them."""
    for sequence in ("<MouseWheel>", "<TouchpadScroll>"):
        try:
            root.bind_class("TCombobox", sequence, lambda _e: None)
        except tk.TclError:
            pass


class ScrollableFrame(ttk.Frame):
    """A vertically scrolling container; put children in ``.body``."""

    def __init__(self, parent, padding=(28, 22)):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=theme.BG, highlightthickness=0, bd=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(self.canvas, padding=padding)
        self._win = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        self._pending_px = 0.0
        self.bind_all("<MouseWheel>", self._on_wheel, add="+")
        try:  # Tk 9 reports precision touchpads (laptops) as a separate event
            self.bind_all("<TouchpadScroll>", self._on_touchpad, add="+")
        except tk.TclError:
            pass

    def _on_body(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self._win, width=event.width)

    def _is_target(self, event):
        """True if the pointer is over this page and the page can scroll."""
        if not self.winfo_ismapped() or self.body.winfo_height() <= self.canvas.winfo_height():
            return False
        widget = getattr(event, "widget", None)
        if not isinstance(widget, tk.Misc):  # e.g. an open dropdown list
            return False
        while widget is not None and widget is not self:
            if isinstance(widget, ttk.Treeview) and widget.yview() != (0.0, 1.0):
                return False  # a list with its own scrollbar scrolls itself
            widget = widget.master
        return widget is self

    def _scroll_pixels(self, pixels):
        # Touchpads send many tiny deltas; keep the remainder so none are lost.
        self._pending_px += pixels
        whole = int(self._pending_px)
        self._pending_px -= whole
        if whole:
            top = self.canvas.canvasy(0)
            self.canvas.yview_moveto(max(top + whole, 0) / self.body.winfo_height())

    def _on_wheel(self, event):
        if self._is_target(event):
            self._scroll_pixels(-event.delta / 120 * WHEEL_NOTCH_PX)

    def _on_touchpad(self, event):
        if self._is_target(event):
            dy = event.delta & 0xFFFF  # %D packs dx (high 16 bits) and dy (low)
            if dy >= 0x8000:
                dy -= 0x10000
            self._scroll_pixels(-dy)


class Card(tk.Frame):
    """White panel with a hairline border; add children to ``.body``."""

    def __init__(self, parent, title=None, subtitle=None, padding=18):
        super().__init__(parent, bg=theme.CARD, highlightthickness=1,
                         highlightbackground=theme.BORDER, bd=0)
        self.body = ttk.Frame(self, style="Card.TFrame", padding=padding)
        self.body.pack(fill="both", expand=True)
        if title:
            head = ttk.Frame(self.body, style="Card.TFrame")
            head.pack(fill="x", pady=(0, 12))
            ttk.Label(head, text=title, style="Card.TLabel",
                      font=theme.F_CARD_TITLE).pack(anchor="w")
            if subtitle:
                sub = ttk.Label(head, text=subtitle, style="Muted.TLabel",
                                wraplength=640, justify="left")
                sub.pack(anchor="w", pady=(2, 0))
                head.bind("<Configure>",
                          lambda e: sub.configure(wraplength=max(e.width - 4, 200)))
        self.content = ttk.Frame(self.body, style="Card.TFrame")
        self.content.pack(fill="both", expand=True)


def page_header(parent, title, subtitle=None, module=None, color=None):
    """Page title; ``module`` adds a coloured label naming the module above it."""
    frame = ttk.Frame(parent)
    frame.pack(fill="x", pady=(0, 18))
    if module:
        tag = tk.Frame(frame, bg=theme.BG)
        tag.pack(anchor="w", pady=(0, 4))
        tk.Frame(tag, bg=color or theme.ACCENT, width=18, height=3).pack(side="left", pady=(1, 0))
        tk.Label(tag, text=module.upper(), bg=theme.BG, fg=color or theme.ACCENT,
                 font=theme.F_EYEBROW, padx=8).pack(side="left")
    ttk.Label(frame, text=title, font=theme.F_TITLE).pack(anchor="w")
    if subtitle:
        ttk.Label(frame, text=subtitle, foreground=theme.MUTED,
                  font=theme.F_SUBTITLE).pack(anchor="w", pady=(2, 0))
    return frame


class TabBar(tk.Frame):
    """Numbered step tabs with an underline under the active one."""

    def __init__(self, parent, tabs, on_select, bg=theme.CARD):
        super().__init__(parent, bg=bg)
        self.on_select = on_select
        self.items = {}
        self.current = None
        for i, (key, label) in enumerate(tabs, start=1):
            item = tk.Frame(self, bg=bg, cursor="hand2")
            item.pack(side="left", padx=(0, 6))
            row = tk.Frame(item, bg=bg, padx=10, pady=8)
            row.pack()
            badge = tk.Label(row, text=str(i), width=2, font=theme.F_BADGE,
                             bg=theme.BUTTON, fg=theme.MUTED)
            badge.pack(side="left")
            text = tk.Label(row, text=label, bg=bg, fg=theme.MUTED, font=theme.F_TAB, padx=6)
            text.pack(side="left")
            line = tk.Frame(item, height=3, bg=bg)
            line.pack(fill="x")
            for w in (item, row, badge, text):
                w.bind("<Button-1>", lambda _e, k=key: self.select(k))
            self.items[key] = (badge, text, line)

    def select(self, key):
        self.current = key
        self._paint()
        self.on_select(key)

    def _paint(self):
        for key, (badge, text, line) in self.items.items():
            active = key == self.current
            badge.configure(bg=theme.ACCENT if active else theme.BUTTON,
                            fg="white" if active else theme.MUTED)
            text.configure(fg=theme.TEXT if active else theme.MUTED,
                           font=theme.F_TAB_ACTIVE if active else theme.F_TAB)
            line.configure(bg=theme.ACCENT if active else self["bg"])


class Banner(tk.Frame):
    """Slim coloured message strip with an optional action link."""

    KINDS = {"info": (theme.INFO_SOFT, theme.INFO),
             "ok": (theme.SUCCESS_SOFT, theme.SUCCESS),
             "warn": (theme.ACCENT_SOFT, theme.ACCENT_HOVER)}

    def __init__(self, parent, before=None):
        super().__init__(parent, bg=theme.CARD)
        self._before = before   # widget the banner is shown above, if any
        self.text = tk.Label(self, bg=theme.CARD, anchor="w", justify="left",
                             font=theme.F_SMALL, padx=10, pady=7, wraplength=520)
        self.text.pack(side="left", fill="x", expand=True)
        self.link = tk.Label(self, bg=theme.CARD, font=(theme.FONT, 9, "underline"),
                             cursor="hand2", padx=10)
        self._action = None
        self.link.bind("<Button-1>", lambda _e: self._action and self._action())

    def show(self, message, kind="info", action_text=None, action=None):
        bg, fg = self.KINDS[kind]
        for w in (self, self.text, self.link):
            w.configure(bg=bg)
        self.text.configure(text=message, fg=fg)
        self._action = action
        if action_text:
            self.link.configure(text=action_text, fg=fg)
            self.link.pack(side="right")
        else:
            self.link.pack_forget()
        if not self.winfo_manager():
            options = {"fill": "x", "pady": (0, 10)}
            if self._before is not None:
                options["before"] = self._before
            self.pack(**options)

    def hide(self):
        self.pack_forget()


# ---- fields ----------------------------------------------------------------

class Field(ttk.Frame):
    """Label + entry + inline error message."""

    def __init__(self, parent, label, *, variable=None, width=14, unit=None,
                 hint=None):
        super().__init__(parent, style="Card.TFrame")
        if label:
            text = f"{label} ({unit})" if unit else label
            ttk.Label(self, text=text, style="Field.TLabel").pack(anchor="w")
        self.var = variable or tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(fill="x", pady=(3, 0))
        self.error = ttk.Label(self, text=hint or "", style="Muted.TLabel")
        self.error.pack(anchor="w")
        self._hint = hint or ""
        self.var.trace_add("write", lambda *_: self.clear_error())

    def get(self):
        return self.var.get().strip()

    def set(self, value):
        self.var.set("" if value is None else f"{value:g}" if isinstance(value, float) else str(value))

    def set_error(self, message):
        self.error.configure(text=message, style="Error.TLabel")
        self.entry.configure(style="Invalid.TEntry")

    def clear_error(self):
        self.error.configure(text=self._hint, style="Muted.TLabel")
        self.entry.configure(style="TEntry")

    def set_readonly(self, readonly):
        self.entry.configure(state="readonly" if readonly else "normal")


class NumberField(Field):
    def __init__(self, parent, label, *, required=True, minimum=0.0,
                 allow_equal=True, integer=False, **kwargs):
        super().__init__(parent, label, **kwargs)
        self.rules = dict(required=required, minimum=minimum,
                          allow_equal=allow_equal, integer=integer)

    def value(self, quiet=False):
        """Parsed number (or None if optional and blank).

        Raises InputError and shows it inline unless ``quiet``.
        """
        try:
            return parse_number(self.var.get(), **self.rules)
        except InputError as exc:
            if not quiet:
                self.set_error(str(exc))
            raise


def collect(fields, quiet=False):
    """Validate every field; returns {key: value} or raises InputError."""
    values, failed = {}, False
    for key, field in fields.items():
        try:
            values[key] = field.value(quiet=quiet)
        except InputError:
            failed = True
    if failed:
        raise InputError("Please correct the highlighted fields.")
    return values


class ResultTile(tk.Frame):
    def __init__(self, parent, label, unit="", accent=False):
        bg = theme.ACCENT_SOFT if accent else theme.BG
        super().__init__(parent, bg=bg, padx=16, pady=12)
        tk.Label(self, text=label.upper(), bg=bg, fg=theme.MUTED,
                 font=theme.F_RESULT_LABEL).pack(anchor="w")
        row = tk.Frame(self, bg=bg)
        row.pack(anchor="w", pady=(2, 0))
        self.value = tk.Label(row, text="—", bg=bg,
                              fg=theme.ACCENT if accent else theme.TEXT,
                              font=theme.F_RESULT)
        self.value.pack(side="left")
        if unit:
            tk.Label(row, text=" " + unit, bg=bg, fg=theme.MUTED,
                     font=theme.F_BASE).pack(side="left", anchor="s", pady=(0, 5))

    def set(self, text):
        self.value.configure(text=text)


class StatusLabel(ttk.Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="", style="Muted.TLabel", **kwargs)

    def error(self, text):
        self.configure(text=text, foreground=theme.ERROR)

    def ok(self, text):
        self.configure(text=text, foreground=theme.SUCCESS)

    def note(self, text):
        self.configure(text=text, foreground=theme.ACCENT_HOVER)

    def clear(self):
        self.configure(text="")


# ---- shared material selection ---------------------------------------------

class MaterialState:
    """The one material/SG selection shared by every page of both modules."""

    def __init__(self, root):
        self.material = tk.StringVar(root, value=materials.MATERIALS[0][0])
        self.custom_name = tk.StringVar(root, value="")
        self.sg = tk.StringVar(root, value=f"{materials.MATERIALS[0][1]:.2f}")
        self.material.trace_add("write", self._on_material)

    def _on_material(self, *_):
        sg = materials.specific_gravity(self.material.get())
        if sg is not None:
            self.sg.set(f"{sg:.2f}")

    @property
    def is_custom(self):
        return self.material.get() == materials.CUSTOM_LABEL

    def select(self, name):
        self.material.set(name)

    def resolve(self):
        """(material name, specific gravity); raises InputError if invalid."""
        try:
            sg = parse_number(self.sg.get(), minimum=0, allow_equal=False)
        except InputError as exc:
            raise InputError(f"Specific gravity: {str(exc).lower()}")
        if self.is_custom:
            name = self.custom_name.get().strip()
            if not name:
                raise InputError("Enter a name for the custom material")
            return name, sg
        return self.material.get(), sg

    def is_steel(self):
        return self.material.get() in materials.STEEL_MATERIALS


class MaterialPicker(ttk.Frame):
    """Material dropdown + SG field; every picker edits the same MaterialState."""

    def __init__(self, parent, state):
        super().__init__(parent, style="Card.TFrame")
        self.state = state
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)

        left = ttk.Frame(self, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Label(left, text="Material", style="Field.TLabel").pack(anchor="w")
        self.combo = ttk.Combobox(
            left, textvariable=state.material, state="readonly",
            values=materials.material_names() + [materials.CUSTOM_LABEL])
        self.combo.pack(fill="x", pady=(3, 0))

        self.name_box = ttk.Frame(self, style="Card.TFrame")
        self.name_box.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(self.name_box, text="Custom material name",
                  style="Field.TLabel").pack(anchor="w")
        ttk.Entry(self.name_box, textvariable=state.custom_name).pack(fill="x", pady=(3, 0))

        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=0, column=2, sticky="ew")
        ttk.Label(right, text="Specific gravity (g/cm³)",
                  style="Field.TLabel").pack(anchor="w")
        self.sg_entry = ttk.Entry(right, textvariable=state.sg, width=10)
        self.sg_entry.pack(fill="x", pady=(3, 0))

        self.error = ttk.Label(self, text="", style="Error.TLabel")
        self.error.grid(row=1, column=0, columnspan=3, sticky="w")

        state.material.trace_add("write", lambda *_: self._sync())
        state.sg.trace_add("write", lambda *_: self.error.configure(text=""))
        state.custom_name.trace_add("write", lambda *_: self.error.configure(text=""))
        self._sync()

    def _sync(self):
        custom = self.state.is_custom
        self.sg_entry.configure(state="normal" if custom else "readonly")
        if custom:
            self.name_box.grid()
        else:
            self.name_box.grid_remove()
        self.error.configure(text="")

    def resolve(self):
        try:
            return self.state.resolve()
        except InputError as exc:
            self.error.configure(text=str(exc))
            raise
