@echo off
REM Builds dist\ProCaliber Estimator.exe - a single file that runs on any
REM Windows 10/11 PC without installing Python or anything else.
setlocal
cd /d "%~dp0"

python -m pip install -r requirements.txt || goto :error
python tools\make_template.py "ProCaliber Estimate Guide.xlsx" || goto :error
python -m unittest discover -s tests || goto :error
python tools\make_icon.py || goto :error
python tools\make_version_info.py || goto :error

python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "ProCaliber Estimator" ^
    --icon assets\app.ico ^
    --version-file build\version_info.txt ^
    --add-data "assets\estimate_template.xlsx;assets" ^
    --add-data "assets\app.ico;assets" ^
    --exclude-module numpy --exclude-module pandas --exclude-module pytest ^
    main.py || goto :error

echo.
echo Done: dist\ProCaliber Estimator.exe
exit /b 0

:error
echo.
echo BUILD FAILED
exit /b 1
