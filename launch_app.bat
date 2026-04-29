@echo off
cd /d "%~dp0"
set "PYTHONPATH=%APPDATA%\Python\Python314\site-packages;%PYTHONPATH%"
set "PYTHONNOUSERSITE="
"C:\Python314\python.exe" -m streamlit run Home.py
