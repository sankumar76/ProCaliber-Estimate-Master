# ProCaliber Estimator — Requirements Specification

**Document purpose:** the complete specification for the native desktop app
**"ProCaliber Estimator."** Version 1.1 was the original build spec. Version
2.0 records the application **as built and released** (app version 1.0).
It includes every change agreed with the app owner during development.
Every formula, table and behaviour is specified here, so the app can be
maintained or rebuilt from this document alone.

**Status:** v2.2 (as-built), matching application release **1.0, 01-Oct-2026**.
All open questions from v1.1 are resolved (see §9). One advisory item remains.

### Revision history

| Doc version | Date | Summary |
|---|---|---|
| 1.1 | 23-Sep-2026 | Original build specification, reviewed with the app owner. |
| 2.2 | 14-Oct-2026 | Redesign. Changes: sidebar with two clearly separated module panels; Weight Calculator pages in two columns with live results and cross-section sketches; RM size (including length) sent to the Cost Estimator automatically; Cost Estimator form split into four tabs; parts written straight into the chosen spreadsheet, closing it in Excel first if open; Undo last part; current spreadsheet remembered between sessions (§4.6, §5.4, §8, §9 items 11–14). |
| 2.1 | 24-Sep-2026 | Part view picture can be pasted from the clipboard (Snipping Tool, Print Screen, copied image or file), with a thumbnail preview (§5.2.1). |
| 2.0 | 24-Sep-2026 | Updated to the as-built application (release 1.0). Changes: rates kept on a separate sheet; sheets renamed; corrected `AP` formula; cycle times in minutes; FS size optional; add-on % inputs; part-view pictures; Save / Open / append workflow; safe saving and backups; touchpad scrolling; key-price highlighting; About page; single-file distribution. Details are in §9 (decisions) and throughout. |

---

## 1. Background & Purpose

ProCaliber needs a single native desktop application with two modules:

1. **Weight Calculator** — computes the weight of metal shapes (round bar,
   pipe, box section, plate) and standard Indian Standard (IS) structural
   steel sections (beams, channels, angles, tees), given dimensions and a
   material's specific gravity.
2. **Cost Estimator** — takes a part's size and material plus
   machining/process parameters, and writes them into an Excel workbook
   (`.xlsx`) that reproduces the company's existing costing template
   ("ProCaliber Estimate Guide"), fully formatted with live formulas.

Both modules live in one app. They share one UI shell and one
material/specific-gravity reference, so a material picked in module 1
flows into module 2 without re-entry.

The costing template's layout, headers and formulas come from the
company's reference file `ProCaliber Estimate Guide.xlsx`. In that file,
sheet `tube` holds the parts and sheet `Sheet2` holds the rates. In
workbooks produced by the app, these sheets are named **`ProCaliber
Estimate`** and **`Machining cost`** (§8.4).

---

## 2. Scope

### 2.1 In scope
- A native Windows desktop app (Python 3 + Tkinter).
- **Module A — Weight Calculator**: all shapes and standard sections in
  §4, plus a Specific Gravity reference page and a Unit Converter.
- **Module B — Cost Estimator**: the costing form, live cost preview and
  `.xlsx` generation / append logic in §5–§8.
- **About page** with application identity (§10A).
- A single sidebar navigation shell containing both modules and About.
- Distribution as **one self-contained `.exe`**. Recipients double-click
  it with nothing else to install (§11).

### 2.2 Out of scope (for this version)
- The reference file's `Sheet1` (tube/plate cutting-list scratch data) is
  unrelated to this app's output and is not reproduced in new workbooks.
  If an existing workbook containing it is opened, it is left untouched.
- No cloud sync, multi-user editing or database backend. This is a local,
  single-user desktop tool.
- No PDF export in this version (acceptable fast-follow).
- No editing or deleting of parts already written to a workbook from
  within the app. Make such changes in Excel.

> **Changed from v1.1:** v1.1 proposed replacing the reference file's
> `Sheet2` rate table with cells on the main sheet (`AF21`/`AI21`). The
> app owner chose to keep the rates on their own sheet, as in the
> reference file, and that sheet is now named **`Machining cost`**
> (§6.4, §9 item 3).

---

## 3. Definitions

| Term | Meaning |
|---|---|
| RM | Raw Material (the stock size before machining) |
| FS | Finished Size (the part's final machined size) |
| VMC | Vertical Machining Centre (milling) |
| CNC | Here specifically refers to CNC turning (lathe) operations |
| OHC | Overhead Cost |
| SG | Specific Gravity (density relative to water, g/cm³) |
| Batch QTY | Total quantity of this part to be produced in the batch |
| IS | Indian Standard (structural steel section specifications) |
| Current spreadsheet | The estimate `.xlsx` that new parts are written into (§8.1) |

---

## 4. Functional Requirements — Module A: Weight Calculator

### 4.1 Core calculation rule

Every shape uses the same underlying formula:

```
weight_kg = cross_section_area_mm2 × length_mm × specific_gravity_g_cm3 × 1e-6
```

(Equivalent to volume(mm³) × density(g/cm³) ÷ 1,000, converted to kg.)

**Sanity check** to validate the implementation: a round bar with
diameter=100mm, length=1000mm, SG=7.85 should give **61.65 kg**, matching
the well-known steel-industry shortcut `kg/m = d²/162` for mild steel
(100²/162 ≈ 61.7, same figure within rounding). *As built: 61.654 kg.*

### 4.2 Shape formulas

**Solid Shaft / Round Bar** — inputs: Diameter (mm), Length (mm), material.
```
area   = π/4 × diameter²
weight = area × length × SG × 1e-6
```

**Hollow Shaft / Pipe** — inputs: External Diameter, Internal Diameter,
Length (mm), material. Internal diameter may be 0 and must be smaller
than the external diameter.
```
area   = π/4 × (outer_diameter² − inner_diameter²)
weight = area × length × SG × 1e-6
```

**Box Section** (rectangular hollow tube) — inputs: Section Length,
Section Width, Section Thickness, Total Length (mm), material.
```
inner_length = outer_length − 2×thickness
inner_width  = outer_width  − 2×thickness
area   = (outer_length × outer_width) − (inner_length × inner_width)
weight = area × total_length × SG × 1e-6
```
(Clamp inner_length/inner_width to 0 if thickness is large enough to make
them negative.)

**Plate** — inputs: Length, Width, Thickness (mm), material.
```
weight = length × width × thickness × SG × 1e-6
```
(Area shown to the user for this shape = length × width, i.e. face area.)

**Beam / Channel Section** — inputs: Section Height (H), Section Width
(B), Web Thickness (tw), Flange Thickness (tf), Length (mm), material.
Two modes: pick a **Standard IS designation** (auto-fills H/B/tw/tf from
the table in §4.4) or enter a **Custom** section manually.
```
web_height = max(H − 2×tf, 0)
area   = 2 × (B × tf) + (web_height × tw)
weight = area × length × SG × 1e-6
```
(This is the standard simplified approach for this class of calculator —
ignores root fillet radii. Validated to land within ~1-2% of published
IS 808 weight/metre values; as built, ISMB 200 gives 24.94 kg/m against
the published 25.4 kg/m.)

**Angle Section** (equal or unequal) — inputs: Leg A, Leg B, Thickness,
Length (mm), material. Standard mode picks from the equal/unequal angle
tables in §4.4; Custom mode allows any leg lengths/thickness. Thickness
must be smaller than both legs.
```
area   = thickness × (leg_A + leg_B − thickness)
weight = area × length × SG × 1e-6
```

**Tee Section** — inputs: Section Height (H), Section Width (B), Web
Thickness (tw), Flange Thickness (tf), Length (mm), material. Standard
mode picks from the tee table in §4.4; Custom mode allows manual entry.
```
web_height = max(H − tf, 0)
area   = (B × tf) + (web_height × tw)
weight = area × length × SG × 1e-6
```

### 4.3 Specific Gravity reference (materials)

This is the single material list used by **both** modules (a material
picked here also populates the Cost Estimator's material fields — see
§6). It combines generic material classes with real procurement grades:

| Material | Specific Gravity (g/cm³) |
|---|---|
| MS (Mild Steel) | 7.85 |
| Steel — C15 | 7.85 |
| Steel — C35 | 7.84 |
| Steel — C60 | 7.83 |
| SS 304 | 8.00 |
| SS 316 | 8.00 |
| EN8 | 7.85 |
| EN24 | 7.85 |
| Cast Iron | 7.20 |
| Copper | 8.96 |
| Bronze | 8.73 |
| Brass | 8.45 |
| Aluminium | 2.70 |
| Lead | 11.34 |

The picker also offers **"Custom..."**. It shows a *Custom material
name* field and makes the SG field editable. Both are required and SG
must be greater than 0. For listed materials the SG field is read-only.

The material is written to the workbook using its full list name (e.g.
"MS (Mild Steel)", not "MS"). This was confirmed by the app owner.

> Note: the standard structural section tables (§4.4) are steel-only.
> Aluminium, brass, bronze and copper don't come in these rolled shapes.
> When a non-steel material is selected in Standard mode, the page shows
> a note suggesting Custom mode. Custom mode works with any material.

### 4.4 Standard IS Section tables

Curated sets of the most commonly used sizes per series, sourced from
published IS 808 (beams, channels), IS 1852 (angles), and IS 1173 (tees)
references. **Any size not listed can still be calculated exactly via
Custom mode** (§4.2) — these tables are a convenience, not a limitation.

**Beams** — dimensions `(H, B, tw, tf)` in mm:

```
ISJB 150: (150, 80, 4.6, 6.8)      ISJB 175: (175, 90, 4.8, 7.0)
ISJB 200: (200, 100, 5.0, 7.2)     ISJB 225: (225, 110, 5.2, 7.4)

ISLB 75:  (75, 75, 4.0, 6.0)       ISLB 100: (100, 75, 4.0, 6.5)
ISLB 125: (125, 75, 4.4, 6.6)      ISLB 150: (150, 80, 4.6, 6.8)
ISLB 175: (175, 90, 4.8, 7.0)      ISLB 200: (200, 100, 5.0, 7.2)
ISLB 225: (225, 110, 5.2, 7.4)     ISLB 250: (250, 125, 5.5, 7.6)
ISLB 300: (300, 150, 6.7, 9.4)     ISLB 350: (350, 165, 7.4, 10.0)
ISLB 400: (400, 165, 8.0, 12.5)    ISLB 450: (450, 170, 8.6, 13.4)
ISLB 500: (500, 180, 9.2, 14.1)    ISLB 550: (550, 190, 9.9, 14.7)
ISLB 600: (600, 210, 10.5, 15.6)

ISMB 100: (100, 75, 4.0, 6.5)      ISMB 125: (125, 75, 4.4, 6.7)
ISMB 150: (150, 80, 4.8, 7.6)      ISMB 175: (175, 85, 5.2, 8.5)
ISMB 200: (200, 100, 5.7, 10.8)    ISMB 225: (225, 110, 6.5, 11.8)
ISMB 250: (250, 125, 6.9, 12.5)    ISMB 300: (300, 140, 7.7, 13.1)
ISMB 350: (350, 140, 8.1, 14.2)    ISMB 400: (400, 140, 8.9, 16.0)
ISMB 450: (450, 150, 9.4, 17.4)    ISMB 500: (500, 180, 10.2, 17.2)
ISMB 550: (550, 190, 11.2, 19.3)   ISMB 600: (600, 210, 12.0, 20.3)

ISWB 150: (150, 100, 5.4, 7.6)     ISWB 175: (175, 125, 5.8, 8.1)
ISWB 200: (200, 140, 5.7, 9.3)     ISWB 225: (225, 150, 6.5, 9.9)
ISWB 250: (250, 150, 6.9, 11.4)    ISWB 300: (300, 150, 7.7, 12.4)
ISWB 350: (350, 170, 8.1, 13.2)    ISWB 400: (400, 180, 8.6, 14.4)
ISWB 450: (450, 200, 9.4, 15.4)    ISWB 500: (500, 200, 10.2, 17.2)
ISWB 550: (550, 210, 11.1, 18.8)   ISWB 600: (600, 220, 12.0, 20.3)

ISHB 150: (150, 150, 5.4, 9.0)     ISHB 175: (175, 175, 5.8, 9.5)
ISHB 200: (200, 200, 6.1, 9.0)     ISHB 225: (225, 225, 6.5, 9.5)
ISHB 250: (250, 250, 6.9, 9.7)     ISHB 300: (300, 250, 7.6, 10.6)
ISHB 350: (350, 250, 8.3, 11.6)    ISHB 400: (400, 250, 9.1, 12.7)
ISHB 450: (450, 250, 9.8, 13.7)

100(P): (100, 50, 4.0, 5.6)        125(P): (125, 70, 4.1, 5.9)
150(P): (150, 80, 4.5, 6.5)        175(P): (175, 90, 4.6, 6.9)
200(P): (200, 100, 5.2, 7.6)       300(P): (300, 125, 6.0, 8.9)
```

**Channels** — dimensions `(H, B, tw, tf)` in mm:

```
ISJC 100: (100, 50, 4.2, 6.2)      ISJC 125: (125, 65, 4.4, 6.4)
ISJC 150: (150, 75, 4.6, 6.6)      ISJC 175: (175, 75, 4.8, 6.8)
ISJC 200: (200, 75, 5.0, 7.0)

ISLC 100: (100, 50, 4.0, 5.5)      ISLC 125: (125, 65, 4.2, 5.8)
ISLC 150: (150, 75, 4.4, 6.0)      ISLC 175: (175, 75, 4.8, 6.5)
ISLC 200: (200, 75, 5.0, 7.0)

ISMC 75:  (75, 40, 4.4, 7.3)       ISMC 100: (100, 50, 4.7, 7.5)
ISMC 125: (125, 65, 5.0, 8.1)      ISMC 150: (150, 75, 5.4, 9.0)
ISMC 175: (175, 75, 6.0, 9.5)      ISMC 200: (200, 75, 6.2, 11.4)
ISMC 225: (225, 80, 6.4, 12.4)     ISMC 250: (250, 82, 7.2, 14.1)
ISMC 300: (300, 90, 7.8, 13.6)     ISMC 350: (350, 100, 8.1, 13.5)
ISMC 400: (400, 100, 8.6, 15.3)

ISCG 250: (250, 75, 6.5, 12.0)     ISCG 300: (300, 90, 7.5, 13.0)
```

**Equal angles** — dimensions `(A, A, thickness)` in mm:

```
20x20x3   25x25x3   25x25x5   30x30x3   30x30x5   35x35x4
40x40x4   40x40x5   45x45x5   45x45x6   50x50x5   50x50x6
55x55x6   60x60x6   65x65x6   65x65x8   70x70x6   75x75x6
75x75x8   80x80x6   80x80x8   90x90x6   90x90x8   100x100x8
100x100x10   110x110x10   130x130x10   150x150x10   150x150x12
200x200x12   200x200x16
```
(Prefix each with "ISA", e.g. "ISA 50x50x6" → leg A=50, leg B=50, t=6.)

**Unequal angles** — dimensions `(A, B, thickness)` in mm:

```
30x20x3   30x20x4   40x25x4   40x25x5   45x30x5   50x30x5
50x30x6   60x40x5   60x40x6   65x45x5   65x45x6   75x50x6
75x50x8   80x50x6   90x60x6   90x60x8   100x65x7  100x65x8
100x75x8  125x75x8  125x75x10 125x95x8  150x75x8  150x115x8
150x115x10   200x100x10   200x150x10   200x150x12
```
(Prefix each with "ISA", e.g. "ISA 100x65x7" → leg A=100, leg B=65, t=7.)

**Tee bars** — dimensions `(H, B, tw, tf)` in mm:

```
ISNT 40: (40, 40, 4.0, 4.0)        ISNT 50: (50, 50, 4.5, 4.5)
ISNT 60: (60, 60, 5.0, 5.0)        ISNT 75: (75, 75, 5.5, 5.5)
ISNT 100: (100, 100, 6.0, 6.0)

ISDT 75: (75, 50, 5.0, 6.0)        ISDT 100: (100, 60, 6.0, 7.0)
ISDT 125: (125, 65, 6.5, 8.0)

ISLT 75: (75, 75, 4.0, 6.5)        ISLT 100: (100, 75, 4.0, 6.5)
ISLT 125: (125, 75, 4.4, 6.7)

ISMT 100: (100, 75, 4.8, 7.6)      ISMT 125: (125, 75, 5.2, 8.5)
ISMT 150: (150, 100, 5.7, 10.8)
```

### 4.5 Unit Converter

A simple utility screen with:
- **Length**: convert between mm, cm, m, inch, foot (1 inch = 25.4mm,
  1 foot = 304.8mm).
- **Weight**: convert between kg, g, tonne, lb (1 kg = 2.2046 lb).
- The result updates as you type. A **Swap** button exchanges the From and
  To units.
- Static reference facts displayed: "1 cu.m = 1000 litres = 220 gallons",
  "2.2046 Pounds = 1 Kg", "304.8 mm = 1 foot", "25.4 mm = 1 inch".

### 4.6 UI requirements for Module A (as built)

- One page per shape (Round Bar, Pipe, Box Section, Plate, Beam, Channel,
  Angle, Tee), laid out in two columns:
  - **Left:** the IS section selector (for sections), the material
    picker (§4.3), dimension inputs (mm) and **Calculate** / **Clear**.
  - **Right:** the result, a **cross-section sketch** whose letters
    (D, OD, ID, L, W, t, T, H, B, tw, tf, A) match the field labels, and
    (for mappable shapes) the Cost Estimator link.
- **Results update live** as the user types. Calculate (or Enter) also
  shows any validation errors inline.
- The result shows **Weight (kg)** prominently, plus **Cross-Section Area
  (mm²)** and **Weight per metre (kg/m)**. The plate page shows *Face area
  (L × W)* and Weight only.
- Beam, Channel, Angle and Tee pages have a **Standard IS Section /
  Custom** toggle:
  - **Standard mode:** a **Series** dropdown (e.g. ISMB, ISMC, Equal
    angles, Unequal angles, Parallel flange (P)) filters a
    **Designation** dropdown. The designation fills in the dimension
    fields, which are read-only.
  - **Custom mode:** the dimension fields are editable and the dropdowns
    are disabled.
- **Automatic RM size (v2.2).** On Round Bar, Pipe and Plate, every
  successful calculation **sends the size to the Cost Estimator's RM
  (raw material) row automatically**, including the length. No button
  press is needed.
  - **Mapping:** Round bar → Outer dia and Length. Pipe → Outer dia,
    Inner dia and Length. Plate → Length, Width and Thickness.
  - **Only the page being viewed sends**, so a shared-material change
    doesn't make other pages overwrite the size.
  - The page confirms *"✔ RM size sent: Ø53 × 16 mm"*.
  - The Cost Estimator's Size tab shows a banner naming the source shape
    and size, with **Undo** to restore the previous values.
  - **Use as FS size instead** sends the size to the FS row, and **Open
    Cost Estimator →** switches pages.
- The **Specific Gravity** page lists §4.3 with SG and density (kg/m³).
  Double-clicking a material (or **Use selected material**) makes it the
  current material everywhere in the app.
- A **Unit Converter** page (§4.5).
- All numeric inputs are validated. Invalid or empty fields get a red
  border and an inline message (e.g. "Required", "Enter a number",
  "Must be smaller than the external diameter"). The app never crashes on
  bad input.

---

## 5. Functional Requirements — Module B: Cost Estimator — Inputs

The Cost Estimator collects one part per entry. **Add Part to Spreadsheet**
writes it as a new row pair in the chosen spreadsheet (§8). In each pair, row *n*
is the RM row and row *n+1* is the FS row. Parts occupy rows 4/5, 6/7,
8/9 and so on, so *n* is always even, starting at 4. For the *k*-th
part, add `2×(k-1)` to the row number.

All cell letters below assume the **first** part (row 4/5).

| # | Input field (shown to user) | Target cell (part 1) | Notes |
|---|---|---|---|
| a | Batch QTY | `H4` | Whole number ≥ 1 (required) |
| b | Process flow | `K4` | Free text, e.g. "CUT + TURN" |
| c | RM size: Length / Width / Thickness (mm) | `O4` / `P4` / `Q4` | Rectangular stock |
| c | RM size: Outer dia / Inner dia / Length (mm) | `R4` / `S4` / `T4` | Round stock |
| c (FS) | Same 6 fields, Finished Size | `O5:T5` | **Optional** (§5.1) |
| d | RM price / kg (₹) | `X4` | Required, ≥ 0 |
| e | Cutting cost / piece (₹) | `Z4` | **Default ₹10**, editable; written as a number |
| f | VMC time / piece (**minutes**) | `AA4` | Blank = 0. Header reads "VMC Mins/piece" (§9 item 1) |
| g | VMC setting time (hours) | `AB4` | Blank = 0 |
| h | CNC time / piece (**minutes**) | `AC4` | Blank = 0. Header reads "CNC Mins/piece" |
| i | CNC setting time (hours) | `AD4` | Blank = 0 |
| j | CNC rate (₹ / hour) | `'Machining cost'!B1` | **Default ₹300**; one workbook-wide value |
| k | VMC rate (₹ / hour) | `'Machining cost'!B2` | **Default ₹450**; one workbook-wide value |
| l | Inspection cost (%) | used in `AL4` | Default 0 (§6.5) |
| m | Int/Ext transport cost (%) | used in `AM4` | Default 0 |
| n | Special packing cost (%) | used in `AN4` | Default 0 |
| o | QTY / frame | `G4` | Default 1, editable, must be > 0 |

Cycle times are in **minutes** because the template's formulas divide
`AA` and `AC` by 60 (§6.4). The app owner confirmed this.

### 5.1 Material size (RM / FS) rules
- The form has a 2 × 6 grid: an RM row and an FS row, each with
  rectangular fields (Length / Width / Thickness) and round fields
  (Outer dia / Inner dia / Length). Unused cells are left **blank**, not
  0, in the workbook.
- **RM size is required**: at least one complete set must be entered.
- **FS size is optional** (app owner's decision). If it is left blank,
  `W` (finished weight) evaluates to 0, so `AO` (scrap return) credits the
  whole RM weight as scrap. For parts that are not machined down, use
  **Copy RM → FS** so the scrap credit is 0.
- Rectangular set: fill all of Length, Width and Thickness, or none.
- Round set: Outer dia and Length are required once any round field is
  used. Inner dia is optional and must be smaller than Outer dia.

### 5.2 Other part-detail inputs
| Field | Cell | Notes |
|---|---|---|
| S.no | `A4` | Auto-increment (max existing S.no + 1) |
| Date | `B4` | Default today, entered as DD-MM-YYYY (also accepts DD/MM/YYYY, YYYY-MM-DD, etc.) |
| Drawing number | `C4` | Text |
| Rev. No | `D4` | Text |
| Description | `E4` | Text |
| Part view picture | `F4:F5` | Optional. Embedded centred and scaled to fit the merged cell. Can be supplied in two ways (§5.2.1). |
| Coating / painting | `L4` | Text |
| Remarks | `M4` | Text |

#### 5.2.1 Part view picture: file or clipboard
- **Choose file…** picks a PNG, JPG, BMP, GIF, TIFF or WEBP file.
- **Paste (Ctrl+V)** takes the picture from the Windows clipboard. This
  covers:
  - a Snipping Tool capture (Win+Shift+S) or Print Screen;
  - "Copy image" from a browser or document;
  - a picture file copied in File Explorer.
- **Ctrl+V** works anywhere on the Cost Estimate page. Inside a text
  field it still pastes text as normal, unless the clipboard holds only a
  picture.
- Pasted pictures are saved as PNG files in
  `%LOCALAPPDATA%\ProCaliber Estimator\Pictures`, so the picture is
  still available when the part is added. The 200 most recent are kept.
- A thumbnail preview confirms the attached picture. **Remove** detaches
  it.
- If the clipboard holds no picture, an inline message explains what to
  do.

### 5.3 Live cost preview
While the form is filled in, a **Cost preview** panel recalculates on
every change. It uses exactly the same formulas as the workbook (§6).
- **Plain rows:** RM weight, finished weight, RM cost, machining cost,
  subtotal and scrap return.
- **Highlighted key prices:** **Develop part cost + 15% OHC**, **Prod
  cost only** and **Total cost (all pieces)**. These appear as
  highlighted rows with large orange figures (app owner's request).
- **Headline:** a prominent **Cost / Piece** figure (white on orange).
- Any value that can't be calculated yet shows "—".
- Below the preview: **Add Part to Spreadsheet**, a "Goes to: \<file\>"
  line and **Clear form**.

### 5.4 Form layout: tabs (v2.2)
The inputs are split into four numbered tabs, shown beside the always-
visible preview:

| Tab | Contents |
|---|---|
| 1 Part details | Date, drawing number, Rev. No, description, process flow, coating, remarks, QTY / frame, Batch QTY, part view picture |
| 2 Material | Shared material picker and RM price / kg |
| 3 Size | RM / FS size grid, Copy RM → FS, link to the Weight Calculator, banner for sizes received from it |
| 4 Machining & costs | VMC / CNC times and setting times, cutting cost, add-on percentages |

- **Tab badges** show the step number only; the active tab is
  highlighted. There are no complete / incomplete markers, because each
  tab mixes required and optional fields (app owner's decision).
- **Navigation:** each tab has **← Back** / **Next →** buttons.
- **After a part is added,** the form returns to tab 1.

---

## 6. Functional Requirements — Module B: Computed / Auto-filled Cells

All of the following are written by the app when a part is added. They
are **live Excel formulas**, not pre-computed values, so the workbook
stays editable and recalculates in Excel.

### 6.1 Identity / material fields
| Cell | Value |
|---|---|
| `I4` | Material name (shared material selection, §7) |
| `J4` | Same material name ("Material specified in drawing" / "Material to be considered" both get it) |
| `N4` | Fixed text `"RM"` (matches the reference file) |
| `N5` | Fixed text `"FS"` (matches the reference file) |
| `U4` | Density factor — see §6.2 |

### 6.2 Density factor (`U4`) — important
```
U4 = specific_gravity (g/cm³) × 0.000001
```
**Not** the raw SG value. `V4` multiplies millimetre dimensions directly
by `U4` to get kilograms, so `U4` must hold kg/mm³. Example: SG 7.85 →
`U4` = `0.00000785`. The header "Density (Kg/m3)" is kept as in the
template.

### 6.3 Weight & RM cost formulas
| Cell | Formula |
|---|---|
| `V4` (RM Weight/piece, kg) | `=(O4*P4*Q4*U4)+(3.14*(R4/2)*(R4/2)*T4*U4)-(3.14*(S4/2)*(S4/2)*T4*U4)` |
| `W4` (Finished weight, kg) | `=(O5*P5*Q5*U4)+(3.14*(R5/2)*(R5/2)*T5*U4)-(3.14*(S5/2)*(S5/2)*T5*U4)` |
| `Y4` (RM Cost/piece) | `=V4*X4` |

Blank dimension cells are left **empty** (Excel treats them as 0).

### 6.4 Machining cost formulas
The rates live on the **`Machining cost`** sheet, which is the renamed
`Sheet2` of the reference file:

| Cell (`Machining cost` sheet) | Content |
|---|---|
| `A1` | `CNC Machining Cost / Hour` |
| `B1` | CNC rate, default `300` |
| `A2` | `VMC Machining Cost / Hour` |
| `B2` | VMC rate, default `450` |

| Cell | Formula |
|---|---|
| `AF4` | `=AD4*'Machining cost'!$B$1` |
| `AG4` | `=AC4*('Machining cost'!$B$1/60)` |
| `AI4` | `=AB4*'Machining cost'!$B$2` |
| `AJ4` | `=AA4*('Machining cost'!$B$2/60)` |
| `AK4` (Subtotal cost/piece) | `=SUM(AJ4,AG4,Z4,Y4)` |

`AE4` and `AH4` (Fixt columns) are left blank but formatted.

These rates are **workbook-wide**: every part's formulas point at the same
two cells, so changing a rate in the app or in Excel reprices every part.
Because the rates are on a separate sheet, they can never collide with
part rows, however many parts are added.

### 6.5 Price breakup formulas
| Cell | Formula |
|---|---|
| `AL4` (Inspection) | `=AK4*<inspection %>%` (e.g. `=AK4*0%`, `=AK4*5%`) |
| `AM4` (Transport) | `=AK4*<transport %>%` |
| `AN4` (Special packing) | `=AK4*<packing %>%` |
| `AO4` (If Scrap return) | `=((V4-W4)*80%)*(X4/4)` |
| `AP4` (Develop part cost + 15% OHC) | `=(SUM(Y4,Z4,AE4:AN4)-AK4-AO4)*G4*115%` |
| `AQ4` (After 1st part cost + 15% OHC) | `=(SUM(AK4,AL4:AN4)-AO4)*G4*115%` |
| `AR4` (Prod Cost only) | `=(AK4-AO4)*1.15` |
| `AS4` (Total Cost for all pieces) | `=AP4+((H4-1)*AR4)` |
| `AT4` (Cost / Piece) | `=AS4/H4` |

> **Changed from v1.1:** `AP4` previously read `SUM(Y4:AN4)`. That range
> includes the hour/minute columns `AA:AD` and adds them to a rupee total.
> The corrected formula `SUM(Y4,Z4,AE4:AN4)` comes from row 4 of the
> reference file and was confirmed correct by the app owner.

### 6.6 Formatting of written rows
- Both rows of each part use Arial 11 with thin borders on every cell,
  centred and wrapped, with a row height of 54.75.
- Every column **except `N`–`T`** is merged vertically across the RM/FS
  pair, matching the reference file.
- Number formats:

| Columns | Format |
|---|---|
| `A`, `C`, `G`, `H` | `0` |
| `B` | `mm-dd-yy` (displayed in the system's short-date style) |
| `V`, `W` | `0.000` |
| `AA`–`AD` | `0.00` |
| `X`–`Z` and `AE`–`AT` | Currency `"₹"\ #,##0.00` |

---

## 7. Material List

The material picker used by **both modules** (§4.3) is the single source
of truth. Every material picker in the app edits the same selection, so
choosing a material on any page (a shape page, the Specific Gravity page
or the Cost Estimator) sets it everywhere. That selection populates
`I4`/`J4` and drives `U4` (§6.2). There is no separate material list for
Module B.

---

## 8. Workflow & File Handling

> **Changed in v2.2:** parts are now written **straight into the chosen
> spreadsheet** when they are added. The separate Save / Save As step,
> "unsaved parts" and the append-on-open dialog from v2.0–2.1 were removed
> (app owner's request: *keep updating the same spreadsheet unless the user
> wants a new one*).

### 8.1 Estimate spreadsheet bar (top of the Cost Estimator page)
- **Current spreadsheet:** an Excel badge, the file name (or "No
  spreadsheet chosen yet"), the part count and folder, plus the note
  *"each part you add is written straight into it"*.
- **Buttons:**
  - **New spreadsheet…** creates an empty estimate from the template and
    makes it the current spreadsheet. The Save dialog opens in
    **`C:\Users\<user>\Documents\Cost_Calculations\`** (created
    automatically if missing). The default name is "ProCaliber Estimate
    DD-MM-YYYY.xlsx", and the user can choose any other folder or name.
  - **Choose spreadsheet…** makes an existing estimate the current
    spreadsheet (validated as in §8.4). The dialog opens in the current
    spreadsheet's folder, or in `Cost_Calculations`.
  - **Open in Excel** opens the current spreadsheet.
  - **Undo last part** removes the most recently added part (§8.3).
- **Excel handling is automatic**, with no options shown. If the
  spreadsheet is open in Excel, it is closed before updating and re-opened
  afterwards (§8.3).
- **Machining rates:** CNC and VMC ₹/hour fields showing the
  spreadsheet's rates. When changed, a note says they will be applied
  with the next part, with an **Apply to spreadsheet now** button.
- **A result line** reports each action, e.g. "✔ Part 3 added to
  estimate.xlsx (rows 8–9). Last updated 10:42."
- **Remembered between sessions:** the current spreadsheet is stored in
  `%LOCALAPPDATA%\ProCaliber Estimator\settings.json`. On start-up the
  app continues with the same spreadsheet, if it still exists.

A **Parts in \<file\>** list below the form shows every part in the
current spreadsheet: S.no, drawing number, description, material, batch
QTY and Excel rows.

### 8.2 Adding a part
1. Fill in the four tabs (§5.4), optionally using sizes from Module A.
2. Click **Add Part to Spreadsheet**. The whole form is validated.
   - Missing or invalid required fields are highlighted inline. The
     first tab with a problem is shown, and the message names the tabs
     concerned.
   - Nothing is written until everything is valid.
3. **No spreadsheet chosen yet:** a dialog asks *"Choose the spreadsheet
   for this estimate"*, with **Create a new spreadsheet…**, **Add to an
   existing spreadsheet…** or **Cancel**.
4. **The app updates the spreadsheet on disk:**
   1. If the file is open, it is released first (§8.3).
   2. The file is **re-read from disk**, so edits made in Excel are kept.
   3. The rates are applied, and the part is written to the next free
      row pair with the formatting in §6.6. To find that row pair, the
      app takes the last numeric S.no in column `A` and uses the next even
      row.
   4. The file is saved safely (§8.3).
5. **The result is confirmed** in the preview card and in the spreadsheet
   bar, and the parts list is refreshed. If the app closed the file in
   Excel and the re-open option is on, the file is opened again.
6. **The form is ready for the next part.** It keeps its values to speed
   up similar parts, and clears only Drawing number, Rev. No, Description
   and the picture. **Clear form** also resets the remarks and all size
   fields.

### 8.3 Updating the spreadsheet safely
- **Spreadsheet open in Excel.** Excel locks open files. When the file is
  locked and the auto-close option is on, the app finds the workbook in
  the running Excel (via Windows automation, pywin32).
  - **Unsaved changes in Excel:** the app asks *"Save your changes in
    Excel?"*. Yes saves them, then updates. No discards them. Cancel
    stops without updating.
  - The workbook is then closed and the app waits for Excel to release
    the file.
  - **Excel busy** (e.g. a cell is being edited): a message asks the user
    to finish editing and try again.
  - **Auto-close off, or the file is held by another program:** the app
    asks the user to close it themselves, with **Retry** / **Cancel**.
- **Safe save:** the workbook is written to a temporary file in the same
  folder, checked, the previous version is backed up, and the new file
  then replaces the old one. If any step fails, the existing file is left
  exactly as it was and no temporary files remain.
- **Backups:** before each update, the previous version is copied to
  `%LOCALAPPDATA%\ProCaliber Estimator\Backups\<name> (YYYY-MM-DD
  HHMMSS).xlsx`. The 50 most recent are kept.
- **Undo last part** asks for confirmation, naming the part and the file.
  It then removes the last part's row pair: values, formats, merges and
  its picture. The update follows the same safe steps as above.
- **Spreadsheet moved or deleted:** the app explains this and asks the
  user to choose or create a spreadsheet again.

### 8.4 New and existing spreadsheets
- **New spreadsheet:** built from a bundled template
  (`assets/estimate_template.xlsx`). The template is generated from the
  company reference file by `tools/make_template.py`, so header rows 1–3
  keep the reference file's exact fonts, theme colours, borders, merges,
  column widths and the note on `AO2`. It has sheets **`ProCaliber
  Estimate`** (parts; panes frozen below row 3) and **`Machining cost`**
  (rates).
- **Existing spreadsheet:** any `.xlsx` created by this app, or the
  reference file itself.
  - **Validation:** the app checks for the parts sheet and ten key header
    cells (A2, C2, H2, N2, O3, U3, V3, X3, AK2, AT2). A clear error
    explains any mismatch.
  - **Older files are upgraded** when they are next updated: sheets
    `tube`/`Sheet2` are renamed to `ProCaliber Estimate`/`Machining cost`,
    and formulas that point at `Sheet2!` are repointed. The `AA2`/`AC2`
    headers are corrected to "VMC Mins/piece" / "CNC Mins/piece".
  - Other sheets (e.g. `Sheet1`), existing parts, pictures and comments
    are preserved.
- **Switching spreadsheets** with New / Choose is possible at any time.
  The form is never cleared by it.
- **Closing the app** asks for confirmation only when a valid part is
  filled in but hasn't been added.

### 8.5 Error handling
- Every foreseeable problem shows a clear, plain-language message: an
  invalid input, an unreadable or wrong-format spreadsheet, a missing
  picture file, a file that is in use, Excel being busy, or an
  unwritable folder.
- Any unexpected error shows a message instead of failing silently, and
  the details are logged to
  `%LOCALAPPDATA%\ProCaliber Estimator\Logs\error.log`.

---

## 9. Decisions Log (resolved open questions)

| # | Question (v1.1) | Decision |
|---|---|---|
| 1 | AA–AD field mapping | **Confirmed**: AA/AB = VMC, AC/AD = CNC, matching the reference headers and formulas. AA and AC hold **minutes** per piece (the formulas divide by 60). Headers `AA2`/`AC2` were changed to **"VMC Mins/piece"** / **"CNC Mins/piece"**. |
| 2 | FS dimension inputs | The form collects FS sizes, but **FS is optional** for now (§5.1). |
| 3 | Rate cell placement | **Rates stay on a separate sheet**, as in the reference file (`B1` = CNC, `B2` = VMC). This supersedes `AF21`/`AI21` and avoids any collision with part rows. |
| 4 | AL/AM/AN percentages | **Editable %** inputs on the form, default 0% (formula `=AK4*<n>%`). |
| 5 | G4 (QTY / Frame) | **User input**, default 1. |
| 6 | IS section table accuracy | **Still advisory.** The tables come from published IS references and haven't been checked against an internal source. Spot-check critical sizes, or use Custom mode. |
| 7 | `AP` formula | **Row-4 formula is correct**: `=(SUM(Y4,Z4,AE4:AN4)-AK4-AO4)*G4*115%` (§6.5). |
| 8 | Material name format | Full list name is written (e.g. "MS (Mild Steel)"). |
| 9 | Sheet names | `tube` → **`ProCaliber Estimate`**, `Sheet2` → **`Machining cost`**. Older files are migrated on open (§8.4). |
| 10 | RM/FS labels in column N | `"RM"` / `"FS"`, as in the reference file (instead of the longer v1.1 text). |
| 11 | Saving workflow (v2.2) | **Each part is written straight into the chosen spreadsheet.** The app keeps updating the same spreadsheet until the user starts a new one or chooses another (§8). |
| 12 | Spreadsheet open in Excel (v2.2) | The app **closes it automatically** before updating (offering to save Excel edits), reloads it so those edits are kept, and **re-opens it** afterwards. This always happens; no options are shown. |
| 15 | Tab status markers (v2.2) | **Not shown.** Tabs mix required and optional fields, so ✓ / ! markers were removed; errors are shown on the fields themselves. |
| 16 | Default spreadsheet folder (v2.2) | `C:\Users\<user>\Documents\Cost_Calculations\`, which the user can change in the dialog. |
| 13 | RM size from the Weight Calculator (v2.2) | Sent **automatically**, including the length, from Round Bar, Pipe and Plate (§4.6). |
| 14 | Safety net for direct writes (v2.2) | **Undo last part**, plus automatic backups before every update. |

---

## 10. Reference: Header Layout (sheet `ProCaliber Estimate`)

Row 1 (merged section titles): `A1:H1`="Part details", `I1:M1`="Process
details", `N1:AO1`="Price Breakup details", `AP1:AQ1`="ProCaliber Price",
`AR1:AT1`="Vendor price"

Row 2/3 (column headers):

```
A: S.no                          N: Raw material Cost (N3: Material size)
B: Date                          O: Length (mm)
C: Drawing number                P: width (mm)
D: Rev.No                        Q: Thickness (mm)
E: Description                   R: Outer Diameter (mm)
F: Part View                     S: Inner Diameter (mm)
G: QTY / Frame                   T: Length (mm)
H: Batch QTY                     U: Density (Kg/m3)
I: Material specified in drawing V: RM Weight/piece (kg)
J: Material to be considered     W: Finished weight (Kg)
K: Process Flow                  X: RM Price / KG
L: Coating / Painting details    Y: RM Cost / Piece
M: Remarks                       Z: Cutting cost / piece
                                  AA: VMC Mins/piece      (was "VMC Hours/piece")
AE-AG: Turning (Fixt/Set-CT/Tot)  AB: VMC Setting hours
AH-AJ: VMC (Fixt/Set/Mill)        AC: CNC Mins/piece      (was "CNC Hours/piece")
                                  AD: CNC Setting hours
AK: Subtotal: Cost/Piece
AL: Inspection cost (5%)
AM: Int/Ext Transport cost (3%)
AN: If any special packing required (5%)
AO: If Scrap return               (cell note: "Should include, if high volume scrap comes.")
AP: Develop part cost + 15% OHC   (AP3: INR)
AQ: After 1st part cost + 15% OHC (AQ3: INR)
AR: Prod Cost only
AS: Total Cost for all pieces (Dev + Prod cost)
AT: Cost / Piece
```

Each part occupies 2 rows (RM row, then FS row directly below). Header
rows 1–3 appear once at the top and data starts at row 4. The machining
rates are on the separate `Machining cost` sheet (§6.4).

---

## 10A. About Page & Application Identity

A sidebar item **About** (pinned at the bottom, under a "Version 1.0"
label) opens a page showing:

| Item | Value |
|---|---|
| Application | ProCaliber Estimator |
| Version | 1.0 |
| Release date | 01-Oct-2026 |
| Designed & developed by | Santhosh Kumar. S |
| Company | ProCaliber Technologies |

The page header reads *"Designed & developed by Santhosh Kumar. S ·
ProCaliber Technologies"*. Below the header are an "About this
application" description and a "What it does" summary covering the
Weight Calculator, the Cost Estimator and offline use.

The same identity is embedded in the `.exe`'s Windows file properties
(Properties → Details):
- **Product name:** ProCaliber Estimator
- **Version:** 1.0
- **Company:** ProCaliber Technologies
- **Copyright:** "Designed & developed by Santhosh Kumar. S, ProCaliber
  Technologies"
- **Comments:** "Released 01-Oct-2026"

All of these come from one file, `core/app_info.py`.

---

## 11. Non-Functional Requirements

- **Platform**: Windows 10/11 desktop. Built and tested with Python 3.14
  and Tk 9.0 (the code supports Python 3.8+).
- **Distribution**: a single self-contained **`ProCaliber
  Estimator.exe`** (about 20 MB, built with PyInstaller `--onefile`
  `--windowed`). Recipients double-click it and need no Python, Excel
  add-ins or anything else. Windows SmartScreen may warn on first run
  ("More info → Run anyway"). Code-signing the exe would remove this
  warning.
- **Dependencies (build only):** listed in `requirements.txt` and all
  bundled into the exe. Tkinter is part of the standard library.
  - `openpyxl`: xlsx with formulas and formatting.
  - `Pillow`: part-view pictures and the icon.
  - `pywin32`: closing a spreadsheet that is open in Excel (§8.3). If
    Excel automation is unavailable, the app asks the user to close the
    file instead.
  - `pyinstaller`: packaging.
- **No internet access required.** The app is fully offline and data
  stays on the user's computer.
- **Scrolling**: every page scrolls with a mouse wheel (including
  high-resolution wheels) and with **laptop touchpad two-finger
  gestures**. Scrolling over a dropdown scrolls the page and does not
  change the dropdown's value. Lists with their own scrollbar scroll
  themselves.
- **Display**: DPI-aware for sharp text on high-DPI screens. The window
  is sized to fit the screen, with a minimum of 1080 × 680.
- **Error handling**: validate all inputs before writing, with inline
  messages. Never fail silently (§8.5). Never damage an existing workbook
  on a failed save (§8.3).
- **Visual design (v2.2)**: a modern, clean UI with a dark sidebar, white
  card panels and an orange accent that echoes the template.
  - **Sidebar:** the two main modules are separate, clearly highlighted
    panels. Each has a coloured top bar, a numbered badge (**1 Weight
    Calculator** in sky blue, **2 Cost Estimator** in orange), a short
    subtitle and its pages underneath. Weight Calculator pages are
    grouped as *Shapes*, *IS sections* and *Tools*. The active page has a
    coloured marker in its module's colour.
  - **Page headers** carry a coloured module label (e.g. "WEIGHT
    CALCULATOR") above the title.
  - Styling is consistent across both modules.
- **Formatting fidelity**: generated workbooks match the reference file's
  header styling, merges, number formats and ₹ currency format, and open
  in Excel without repair prompts.

---

## 12. Project Structure (as built)

```
main.py                         entry point (DPI awareness, starts the app)
build.bat                       one-step build: template, tests, icon,
                                version info, dist\ProCaliber Estimator.exe
requirements.txt                openpyxl, pillow, pywin32, pyinstaller
README.md                       usage, distribution and development notes
core/
  app_info.py                   name, version, release date, developer,
                                company (About page + exe properties)
  materials.py                  shared specific-gravity table (§4.3)
  sections.py                   standard IS section tables (§4.4)
  calculations.py               weight/area formulas and unit conversion
  estimate_workbook.py          create/open/migrate workbooks, next row,
                                formulas, formats, pictures, safe save,
                                backups, lock detection, undo last part,
                                cost preview mirror
  excel_link.py                 find / save / close a workbook open in Excel
  settings.py                   remembers the current spreadsheet + options
gui/
  app.py                        main window, module sidebar, error handler
  theme.py                      colours (incl. module colours), fonts, styles
  widgets.py                    cards, validated fields, scrollable page,
                                tab bar, banner, shared material picker
  diagrams.py                   cross-section sketches for Module A pages
  weight_calculator_pages.py    Module A pages, SG reference, unit converter
  cost_estimator_pages.py       Module B spreadsheet bar, tabbed form,
                                preview, parts list, Excel handling
  about_page.py                 About page (§10A)
assets/
  estimate_template.xlsx        generated header template (§8.4)
  app.ico                       application icon
tools/
  make_template.py              builds the template from the reference file
  make_icon.py                  draws the icon
  make_version_info.py          writes the exe's Windows version resource
tests/
  test_calculations.py          shape formulas, IS tables, unit conversion
  test_estimate_workbook.py     formulas, rows, append/reopen, migration,
                                headers, FS optional, pictures, rates,
                                locked-file save, backups, undo last part
```

---

## 13. Acceptance Criteria (status at release 1.0)

All criteria below are met. Where noted, a criterion was verified by
recalculating the generated workbook in Microsoft Excel rather than only
comparing formula text.

**Module A — Weight Calculator**
- [x] Round bar, pipe, box section and plate match §4.2 (100 mm × 1000 mm
      round bar, SG 7.85 → 61.654 kg).
- [x] Beam/Channel/Angle/Tee switch correctly between Standard (read-only,
      auto-filled) and Custom (editable) modes.
- [x] Specific Gravity page lists all materials in §4.3, and picking one
      sets it app-wide.
- [x] Unit Converter converts length and weight correctly.
- [x] Round Bar / Pipe / Plate sizes, including the length, reach the
      estimate's RM row automatically when calculated (only from the page
      being viewed), and can also be sent as FS size.
- [x] Results update live, and each shape shows a labelled cross-section
      sketch.

**Module B — Cost Estimator**
- [x] A new estimate with one part shows correct values in Excel for
      `V4`, `W4`, `Y4`, `AK4`, `AO4`, `AP4`, `AQ4`, `AR4`, `AS4`, `AT4`.
      These match the app's live preview to 4 decimal places (Excel
      recalculation).
- [x] A second part goes to row 6/7, with formulas referencing its own
      row and the shared rate cells.
- [x] Reopening a saved workbook and adding a third part uses row 8/9.
      Opening the reference file appends at row 14 with S.no 6.
- [x] `U4` stores `SG × 10⁻⁶`.
- [x] Changing a rate on the `Machining cost` sheet reprices **every**
      part (verified in Excel: CNC 300 → 600 changed part 1 from ₹119.57
      to ₹208.70 per piece).
- [x] The material selected anywhere sets both `U4` and the `I4`/`J4`
      text.
- [x] Opening an older file (`tube`/`Sheet2`) migrates sheet names and
      formulas, and all existing parts still calculate in Excel.
- [x] Each added part is written straight into the chosen spreadsheet.
      Later parts go to the same spreadsheet until another is chosen, and
      the choice survives an app restart.
- [x] If the spreadsheet is open in Excel with unsaved edits, the app
      offers to save them, closes the file, adds the part (keeping the
      Excel edits) and re-opens it. Verified end-to-end with Excel, both
      from source and in the packaged exe.
- [x] If the file can't be closed automatically, nothing is written and
      the file is left byte-for-byte unchanged.
- [x] Undo last part removes the part's rows, merges and picture.
- [x] Updates never leave a partial or corrupt file, and the previous
      version is backed up.
- [x] A failed Add highlights the problem fields and opens the first tab
      that needs attention.
- [x] New spreadsheets are offered in `Documents\Cost_Calculations` by
      default.
- [x] Saved workbooks, including embedded pictures, open in Excel without
      repair prompts.
- [x] A part view picture can be attached from a file, or pasted from the
      clipboard (snip, copied image or copied file) with the Paste button
      or Ctrl+V. Ctrl+V in a text field still pastes text. The pasted
      picture is embedded in the saved workbook.

**Application**
- [x] Runs from a single `.exe` with no installation.
- [x] Touchpad and mouse-wheel scrolling work on every page.
- [x] The sidebar shows the two main modules as distinct, numbered,
      colour-coded panels.
- [x] About page shows name, version 1.0, release date 01-Oct-2026,
      developer and company.
