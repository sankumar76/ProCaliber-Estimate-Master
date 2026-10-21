"""Application identity shown on the About page and in the exe's properties."""

APP_NAME = "ProCaliber Estimator"
VERSION = "1.0"
RELEASE_DATE = "01-Oct-2026"
DEVELOPER = "Santhosh Kumar. S"
COMPANY = "ProCaliber Technologies"
CREDIT = f"Designed & developed by {DEVELOPER}, {COMPANY}"

SUMMARY = ("A desktop tool for estimating the weight and cost of machined "
           "metal parts, producing Excel estimates in the ProCaliber format.")

DESCRIPTION = (
    "ProCaliber Estimator brings the two steps of quoting a machined part into "
    "one application. The Weight Calculator works out the weight of bars, pipes, "
    "box sections, plates and standard IS structural sections for any material. "
    "The Cost Estimator turns a part's size, material price and machining times "
    "into a full price breakup, and adds it to an Excel estimate that follows "
    "the ProCaliber Estimate Guide. That estimate keeps live formulas, so it can "
    "still be reviewed and edited in Excel."
)

FEATURES = [
    ("Weight Calculator",
     "Round bar, pipe, box section and plate, plus IS beams, channels, angles "
     "and tees (standard or custom sizes). Includes a specific-gravity "
     "reference for 14 materials and a unit converter."),
    ("Cost Estimator",
     "Raw material, cutting, CNC and VMC machining, overheads and scrap "
     "return, with a live cost preview. Parts are added to a new or existing "
     "Excel estimate."),
    ("Works offline",
     "A single program file with nothing to install. No internet connection is "
     "needed, and your data stays on your computer."),
]
