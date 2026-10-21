# ProCaliber Estimator

Windows desktop app with two modules:

- **Weight Calculator**: round bar, pipe, box section, plate and IS beams, channels, angles and tees. It also has a specific-gravity reference and a unit converter.
- **Cost Estimator**: adds parts to an Excel estimate laid out like *ProCaliber Estimate Guide.xlsx*. It writes live formulas, so the workbook still recalculates in Excel.

## Giving the app to someone else

Send them the single file **`dist\ProCaliber Estimator.exe`**. They double-click it to start the app, with nothing to install.
Windows SmartScreen may warn about an unrecognised app the first time it runs. They click **More info → Run anyway**. Code-signing the exe removes this warning.

## Using the Cost Estimator

1. **Choose the spreadsheet** at the top of the page: **New spreadsheet…** or **Choose spreadsheet…**. If you skip this, the app asks when you add your first part.
   - Every part you add is written straight into that spreadsheet. There is no separate Save step.
   - The app keeps using the same spreadsheet, even after a restart, until you pick another one.
2. **Fill in the four tabs:** Part details, Material, Size, and Machining & costs.
   - The Cost preview on the right updates as you type.
   - **Size from the Weight Calculator:** calculating a Round Bar, Pipe or Plate fills the RM (raw material) size, including the length, automatically.
   - **Part view picture:** click **Choose file…**, or take a snip (Win+Shift+S) or copy any picture and press **Ctrl+V**.
3. **Click Add Part to Spreadsheet.** Each part fills the next free pair of rows (4/5, 6/7, …).
   - **If the spreadsheet is open in Excel:** the app closes it first, after asking whether to save any changes you made there. It reloads the file so those changes are kept, adds the part, and re-opens it in Excel.
   - **Mistakes:** **Undo last part** removes the most recently added part.

The parts are on the **ProCaliber Estimate** sheet. The CNC and VMC hourly rates live on the **Machining cost** sheet (`B1` = CNC, `B2` = VMC).
Every part's formulas point at those two cells, so changing a rate in the app or in Excel reprices every part.

**Safe saving.** The app writes a complete new copy first and only then replaces the file, so a failed update never damages the existing spreadsheet.
Before each update, the previous version is copied to `%LOCALAPPDATA%\ProCaliber Estimator\Backups` (the last 50 are kept).
Unexpected errors are logged to `%LOCALAPPDATA%\ProCaliber Estimator\Logs\error.log`.
New spreadsheets are offered in `Documents\Cost_Calculations` by default (you can pick any other folder).
The chosen spreadsheet is remembered in `%LOCALAPPDATA%\ProCaliber Estimator\settings.json`.

Older estimates that use the reference file's sheet names (`tube` and `Sheet2`) are renamed automatically when opened.

## Development

Requirements: Python 3.8+ (tested on 3.14) and the packages in `requirements.txt`.

```
pip install -r requirements.txt
python main.py                              # run from source
python -m unittest discover -s tests        # tests
build.bat                                   # tests + template + icon + dist\ProCaliber Estimator.exe
```

| Path | Purpose |
|---|---|
| `core/materials.py` | Shared specific-gravity table |
| `core/sections.py` | Standard IS section tables |
| `core/calculations.py` | Shape area/weight formulas, unit conversion |
| `core/estimate_workbook.py` | Creates and opens estimates, finds the next row, writes formulas, formats and pictures, removes the last part |
| `core/excel_link.py` | Finds, saves and closes a spreadsheet that's open in Excel (via pywin32) |
| `core/settings.py` | Remembers the current spreadsheet |
| `gui/` | Tkinter UI: `app.py` (sidebar), `weight_calculator_pages.py`, `diagrams.py` (cross-section sketches), `cost_estimator_pages.py` |
| `assets/estimate_template.xlsx` | Header rows 1–3 and the Machining cost sheet, generated from the reference file by `tools/make_template.py` |

If the reference layout changes, rebuild the template with `python tools/make_template.py "ProCaliber Estimate Guide.xlsx"`.
