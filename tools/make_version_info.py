"""Write build/version_info.txt: the Windows file properties of the exe
(right-click > Properties > Details), taken from core/app_info.py."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
sys.path.insert(0, ROOT)

from core import app_info  # noqa: E402

OUT = os.path.join(ROOT, "build", "version_info.txt")


def main():
    parts = [int(p) for p in app_info.VERSION.split(".")]
    nums = tuple((parts + [0, 0, 0, 0])[:4])
    strings = {
        "ProductName": app_info.APP_NAME,
        "FileDescription": app_info.APP_NAME,
        "FileVersion": app_info.VERSION,
        "ProductVersion": app_info.VERSION,
        "InternalName": app_info.APP_NAME,
        "OriginalFilename": app_info.APP_NAME + ".exe",
        "CompanyName": app_info.COMPANY,
        "LegalCopyright": app_info.CREDIT,
        "Comments": f"Released {app_info.RELEASE_DATE}",
    }
    entries = ",\n          ".join(f"StringStruct({k!r}, {v!r})" for k, v in strings.items())
    text = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={nums}, prodvers={nums}, mask=0x3f, flags=0x0,
                    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
          {entries}])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("Wrote", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
