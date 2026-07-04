@echo off
chcp 65001 >nul
setlocal

echo Checking ComfyUI API at http://127.0.0.1:8188 ...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -UseBasicParsing -TimeoutSec 5; Write-Host 'OK: ComfyUI API is reachable.'; exit 0 } catch { Write-Host 'FAIL: ComfyUI API is not reachable.'; Write-Host $_.Exception.Message; exit 1 }"

echo.
echo If this says OK, run:
echo D:\codex-2\jlpt_hvpt_materials\scripts\comfy_generate_all_resume.bat
echo.
pause
