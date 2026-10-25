@echo off
rem Starts the RAG app. Works from any folder, double-click, cmd or PowerShell.
setlocal
cd /d "%~dp0.."

set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo Creating virtual environment...
    py -3.11 -m venv .venv || python -m venv .venv || goto :error
)

"%PYTHON%" -c "import streamlit, faiss, langchain_google_genai, pypdf, docx2txt, openpyxl, xlrd" 2>nul
if errorlevel 1 (
    echo Installing libraries, this takes a few minutes the first time...
    "%PYTHON%" -m pip install -r project2\requirements.txt || goto :error
)

echo Starting app... it opens in your browser. Press Ctrl+C here to stop.
"%PYTHON%" -m streamlit run project2\rag.py
goto :eof

:error
echo.
echo Setup failed. Copy the error above and send it to me.
pause
