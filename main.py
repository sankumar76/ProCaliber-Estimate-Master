"""ProCaliber Estimator - entry point."""

import sys


def _enable_dpi_awareness():
    """Crisp text on high-DPI Windows displays."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def main():
    _enable_dpi_awareness()
    from gui.app import App
    App().mainloop()


if __name__ == "__main__":
    main()
