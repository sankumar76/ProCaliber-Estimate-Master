"""Small per-user settings file (the current spreadsheet)."""

import json
import os

from core.estimate_workbook import app_data_dir

DEFAULTS = {
    "target": None,          # spreadsheet that new parts are added to
}


def _path():
    return os.path.join(app_data_dir(), "settings.json")


def load():
    settings = dict(DEFAULTS)
    try:
        with open(_path(), encoding="utf-8") as fh:
            settings.update({k: v for k, v in json.load(fh).items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    return settings


def save(settings):
    try:
        with open(_path(), "w", encoding="utf-8") as fh:
            json.dump({k: settings.get(k) for k in DEFAULTS}, fh, indent=2)
    except OSError:
        pass
