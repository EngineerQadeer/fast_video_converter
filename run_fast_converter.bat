@echo off
echo ========================================
echo Fast Video Converter to 3GP (176x144)
echo ========================================
echo.

REM Run the Python script with GUI folder selection
python "%~dp0fast_video_converter.py"

echo.
echo Press any key to exit...
pause >nul
