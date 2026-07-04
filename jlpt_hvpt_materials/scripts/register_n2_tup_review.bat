@echo off
setlocal

set "PYTHON=C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "REGISTER_SCRIPT=D:\codex-2\jlpt_hvpt_materials\scripts\register_n2_tup_review.py"

echo Registering N2 review folders...
"%PYTHON%" "%REGISTER_SCRIPT%"
if errorlevel 1 (
  echo.
  echo FAIL: N2 review registration failed.
  pause
  exit /b 1
)

echo.
echo Finished.
pause

