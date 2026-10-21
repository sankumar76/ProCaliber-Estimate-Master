"""Find, save and close a workbook that is open in Microsoft Excel.

Before the app writes a part into a spreadsheet, the file must not be open
in Excel, because Excel locks open files. These helpers let the app close it
for the user, after saving their Excel edits if they want. Everything is
best effort: if Excel automation is unavailable, ``find_workbook`` returns
None and the caller asks the user to close the file themselves.
"""

import os


class ExcelBusyError(Exception):
    """Excel refused the request (e.g. a cell is being edited)."""


def _norm(path):
    return os.path.normcase(os.path.abspath(path))


def _com():
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return None, None
    try:
        pythoncom.CoInitialize()
    except pythoncom.com_error:
        pass  # already initialised on this thread
    return pythoncom, win32com.client


def find_workbook(path):
    """The open Excel Workbook object for ``path``, or None if not found."""
    pythoncom, client = _com()
    if client is None:
        return None
    target = _norm(path)
    # Open workbooks are registered in the Running Object Table under their
    # full path, whichever Excel window they are in.
    try:
        rot = pythoncom.GetRunningObjectTable()
        ctx = pythoncom.CreateBindCtx(0)
        for moniker in rot:
            try:
                name = moniker.GetDisplayName(ctx, None)
                if _norm(name) != target:
                    continue
                obj = rot.GetObject(moniker)
                return client.Dispatch(obj.QueryInterface(pythoncom.IID_IDispatch))
            except (pythoncom.com_error, OSError, ValueError):
                continue
    except pythoncom.com_error:
        pass
    try:
        excel = client.GetActiveObject("Excel.Application")
        for wb in excel.Workbooks:
            if _norm(wb.FullName) == target:
                return wb
    except pythoncom.com_error:
        pass
    return None


def has_unsaved_changes(wb):
    try:
        return not bool(wb.Saved)
    except Exception:
        return False


def close_workbook(wb, save_changes):
    """Close ``wb`` in Excel, saving it first if ``save_changes``."""
    try:
        if save_changes:
            wb.Save()
        wb.Close(SaveChanges=False)
    except Exception as exc:
        raise ExcelBusyError(
            "Excel didn't respond to the request to close the spreadsheet. "
            "If you're editing a cell in Excel, press Enter or Esc there, then "
            f"try again.\n\n({exc})")
