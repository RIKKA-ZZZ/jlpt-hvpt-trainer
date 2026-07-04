@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
"%PYTHON%" "%~dp0fill_tatoeba_sentences.py"
pause
