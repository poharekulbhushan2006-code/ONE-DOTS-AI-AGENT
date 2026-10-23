@echo off
title ONE DOTS - Always-On Autonomous AI Agent Platform
echo =========================================================================
echo   Starting ONE DOTS
echo   Conversational Workstation UI : http://127.0.0.1:8000
echo   Learn & Documentation Hub     : http://127.0.0.1:8000/learn
echo   Google Gemini AI              : Active (gemini-3.5-flash-lite / 3.8-flash)
echo   Specialist Archetypes         : Blue, Green, Yellow, Purple, Dev Dots
echo =========================================================================
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)
pause
