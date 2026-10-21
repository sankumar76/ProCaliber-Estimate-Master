"""Cross-section sketches for the Weight Calculator pages.

Each sketch labels its dimensions with the same letters used on the page's
input fields (D, OD, ID, L, W, t, H, B, tw, tf, A), so users can see which
measurement goes where.
"""

import tkinter as tk

from gui import theme

WIDTH, HEIGHT = 280, 200
OUTLINE = theme.WEIGHT_DARK
FILL = "#E0F2FE"
DIM = "#94A3B8"
LABEL_FONT = (theme.FONT, 9, "bold")


def _dim(c, x1, y1, x2, y2, label, dx=0, dy=0, anchor="center"):
    c.create_line(x1, y1, x2, y2, arrow="both", arrowshape=(6, 7, 3), fill=DIM)
    c.create_text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, text=label,
                  fill=theme.TEXT, font=LABEL_FONT, anchor=anchor)


def _note(c, text):
    c.create_text(WIDTH / 2, HEIGHT - 8, text=text, fill=theme.MUTED, font=theme.F_SMALL)


def _poly(c, *points):
    c.create_polygon(*points, fill=FILL, outline=OUTLINE, width=2)


def round_bar(c):
    c.create_oval(80, 35, 200, 155, fill=FILL, outline=OUTLINE, width=2)
    _dim(c, 80, 95, 200, 95, "D", dy=-10)
    _note(c, "Length L runs along the bar")


def pipe(c):
    c.create_oval(80, 40, 200, 160, fill=FILL, outline=OUTLINE, width=2)
    c.create_oval(115, 75, 165, 125, fill="white", outline=OUTLINE, width=2)
    _dim(c, 80, 26, 200, 26, "OD", dy=-9)
    _dim(c, 115, 100, 165, 100, "ID", dy=11)
    _note(c, "Length L runs along the pipe")


def box_section(c):
    c.create_rectangle(70, 40, 210, 150, fill=FILL, outline=OUTLINE, width=2)
    c.create_rectangle(84, 54, 196, 136, fill="white", outline=OUTLINE, width=2)
    _dim(c, 70, 26, 210, 26, "L", dy=-9)
    _dim(c, 224, 40, 224, 150, "W", dx=12)
    _dim(c, 70, 95, 84, 95, "t", dx=-14)
    _note(c, "Total length runs into the page")


def plate(c):
    _poly(c, 60, 100, 100, 62, 230, 62, 190, 100)          # top face
    _poly(c, 190, 100, 230, 62, 230, 102, 190, 140)         # side face
    _poly(c, 60, 100, 190, 100, 190, 140, 60, 140)          # front face
    _dim(c, 60, 154, 190, 154, "L", dy=10)
    _dim(c, 196, 104, 236, 68, "W", dx=12, dy=4)
    _dim(c, 46, 100, 46, 140, "T", dx=-10)


def beam(c):
    _poly(c, 80, 30, 200, 30, 200, 48, 147, 48, 147, 152, 200, 152, 200, 170,
          80, 170, 80, 152, 133, 152, 133, 48, 80, 48)
    _dim(c, 80, 18, 200, 18, "B", dy=-8)
    _dim(c, 64, 30, 64, 170, "H", dx=-10)
    _dim(c, 212, 30, 212, 48, "tf", dx=14)
    _dim(c, 133, 100, 147, 100, "tw", dx=22)


def channel(c):
    _poly(c, 90, 30, 190, 30, 190, 46, 106, 46, 106, 154, 190, 154, 190, 170, 90, 170)
    _dim(c, 90, 18, 190, 18, "B", dy=-8)
    _dim(c, 74, 30, 74, 170, "H", dx=-10)
    _dim(c, 202, 30, 202, 46, "tf", dx=14)
    _dim(c, 90, 100, 106, 100, "tw", dx=24)


def angle(c):
    _poly(c, 90, 30, 106, 30, 106, 154, 200, 154, 200, 170, 90, 170)
    _dim(c, 74, 30, 74, 170, "A", dx=-10)
    _dim(c, 90, 184, 200, 184, "B", dx=0, dy=-9)
    _dim(c, 90, 18, 106, 18, "t", dx=14)


def tee(c):
    _poly(c, 80, 30, 200, 30, 200, 48, 147, 48, 147, 170, 133, 170, 133, 48, 80, 48)
    _dim(c, 80, 18, 200, 18, "B", dy=-8)
    _dim(c, 64, 30, 64, 170, "H", dx=-10)
    _dim(c, 212, 30, 212, 48, "tf", dx=14)
    _dim(c, 133, 184, 147, 184, "tw", dx=22)


def make(parent, kind):
    """A canvas showing the sketch for ``kind`` (a function name above)."""
    canvas = tk.Canvas(parent, width=WIDTH, height=HEIGHT, bg=theme.CARD,
                       highlightthickness=0)
    globals()[kind](canvas)
    return canvas
