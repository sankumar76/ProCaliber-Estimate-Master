"""Colours, fonts and ttk styling shared by every page."""

from tkinter import ttk

# Palette
BG = "#F1F5F9"            # content background
CARD = "#FFFFFF"
BORDER = "#E2E8F0"
TEXT = "#0F172A"
MUTED = "#64748B"
ACCENT = "#EA580C"        # ProCaliber orange (echoes the estimate template)
ACCENT_HOVER = "#C2410C"
ACCENT_SOFT = "#FFF7ED"
ERROR = "#DC2626"
SUCCESS = "#15803D"
READONLY_BG = "#F8FAFC"
BUTTON = "#E2E8F0"        # secondary buttons
BUTTON_HOVER = "#CBD5E1"

SUCCESS_SOFT = "#F0FDF4"
INFO_SOFT = "#EFF6FF"
INFO = "#1D4ED8"

SIDEBAR_BG = "#0F172A"
SIDEBAR_TEXT = "#CBD5E1"
SIDEBAR_MUTED = "#64748B"
SIDEBAR_HOVER = "#1E293B"
SIDEBAR_ACTIVE = "#1E293B"
SIDEBAR_GROUP = "#131C31"   # module panel background in the sidebar

# Each main module has its own colour, used in the sidebar and page headers.
WEIGHT_COLOR = "#38BDF8"    # Weight Calculator (sky blue)
WEIGHT_DARK = "#0369A1"
COST_COLOR = "#FB923C"      # Cost Estimator (orange)
COST_DARK = ACCENT

FONT = "Segoe UI"
F_BASE = (FONT, 10)
F_SMALL = (FONT, 9)
F_BOLD = (FONT, 10, "bold")
F_TITLE = (FONT, 18, "bold")
F_SUBTITLE = (FONT, 10)
F_CARD_TITLE = (FONT, 11, "bold")
F_RESULT = (FONT, 20, "bold")
F_RESULT_LABEL = (FONT, 9)
F_KEY_PRICE = (FONT, 13, "bold")
F_BRAND = (FONT, 14, "bold")
F_NAV = (FONT, 10)
F_NAV_HEADER = (FONT, 8, "bold")
F_MODULE = (FONT, 11, "bold")
F_EYEBROW = (FONT, 8, "bold")
F_TAB = (FONT, 10)
F_TAB_ACTIVE = (FONT, 10, "bold")
F_BADGE = (FONT, 8, "bold")


def apply(root):
    root.configure(bg=BG)
    root.option_add("*Font", F_BASE)
    root.option_add("*TCombobox*Listbox.font", F_BASE)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG, foreground=TEXT, font=F_BASE,
                    bordercolor=BORDER, focuscolor=ACCENT)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=F_SMALL)
    style.configure("Field.TLabel", background=CARD, foreground=MUTED, font=F_SMALL)
    style.configure("Error.TLabel", background=CARD, foreground=ERROR, font=F_SMALL)

    field_opts = dict(fieldbackground=CARD, bordercolor="#CBD5E1",
                      lightcolor=CARD, darkcolor=CARD, padding=(8, 5),
                      insertcolor=TEXT)
    style.configure("TEntry", **field_opts)
    style.map("TEntry",
              fieldbackground=[("readonly", READONLY_BG), ("disabled", READONLY_BG)],
              foreground=[("readonly", MUTED), ("disabled", MUTED)],
              bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])
    style.configure("Invalid.TEntry", **dict(field_opts, bordercolor=ERROR,
                                             lightcolor=ERROR))

    style.configure("TCombobox", **field_opts, arrowcolor=MUTED,
                    background=CARD)
    style.map("TCombobox",
              fieldbackground=[("readonly", CARD), ("disabled", READONLY_BG)],
              foreground=[("disabled", MUTED)],
              selectbackground=[("readonly", CARD)],
              selectforeground=[("readonly", TEXT)],
              bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])

    style.configure("TButton", padding=(14, 7), font=F_BOLD, borderwidth=1,
                    relief="flat", background=BUTTON, foreground=TEXT, width=-6,
                    bordercolor=BUTTON, lightcolor=BUTTON, darkcolor=BUTTON)
    style.map("TButton",
              background=[("pressed", BUTTON_HOVER), ("active", BUTTON_HOVER)],
              bordercolor=[("active", BUTTON_HOVER)],
              lightcolor=[("active", BUTTON_HOVER)],
              darkcolor=[("active", BUTTON_HOVER)])
    style.configure("Accent.TButton", background=ACCENT, foreground="white",
                    bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT)
    style.map("Accent.TButton",
              background=[("pressed", ACCENT_HOVER), ("active", ACCENT_HOVER),
                          ("disabled", "#FDBA74")],
              bordercolor=[("active", ACCENT_HOVER)],
              lightcolor=[("active", ACCENT_HOVER)],
              darkcolor=[("active", ACCENT_HOVER)])
    style.configure("Small.TButton", padding=(10, 4), font=F_SMALL)
    style.configure("Link.TButton", padding=(4, 2), font=F_SMALL,
                    background=CARD, foreground=ACCENT, bordercolor=CARD,
                    lightcolor=CARD, darkcolor=CARD)
    style.map("Link.TButton", foreground=[("active", ACCENT_HOVER)],
              background=[("active", CARD)], bordercolor=[("active", CARD)])

    style.configure("TRadiobutton", background=CARD, foreground=TEXT,
                    indicatorcolor=CARD, font=F_BASE)
    style.map("TRadiobutton",
              indicatorcolor=[("selected", ACCENT)],
              background=[("active", CARD)])
    style.configure("TCheckbutton", background=CARD, foreground=TEXT, font=F_SMALL,
                    indicatorcolor=CARD, indicatorbackground=CARD)
    style.map("TCheckbutton",
              indicatorcolor=[("selected", ACCENT)],
              background=[("active", CARD)])

    style.configure("Treeview", background=CARD, fieldbackground=CARD,
                    foreground=TEXT, rowheight=28, bordercolor=BORDER,
                    lightcolor=CARD, darkcolor=CARD)
    style.configure("Treeview.Heading", background=BG, foreground=MUTED,
                    font=F_SMALL, relief="flat", bordercolor=BORDER,
                    lightcolor=BG, darkcolor=BG, padding=(8, 6))
    style.map("Treeview", background=[("selected", ACCENT_SOFT)],
              foreground=[("selected", TEXT)])
    style.map("Treeview.Heading", background=[("active", BORDER)])

    style.configure("Vertical.TScrollbar", background=BG, troughcolor=BG,
                    bordercolor=BG, arrowcolor=MUTED, lightcolor=BG, darkcolor=BG)
    style.configure("TSeparator", background=BORDER)
    return style
