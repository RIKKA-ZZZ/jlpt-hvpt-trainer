@echo off
setlocal

set "PYTHON=C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "REGISTER_SCRIPT=D:\codex-2\jlpt_hvpt_materials\scripts\register_n2_tup_review.py"
set "GEN_SCRIPT=D:\codex-2\jlpt_hvpt_materials\scripts\comfy_batch_generate.py"
set "OUTDIR=D:\codex-2\tup_n2"

echo Registering current N2 review folders before retry...
"%PYTHON%" "%REGISTER_SCRIPT%"
if errorlevel 1 (
  echo.
  echo FAIL: N2 review registration failed.
  pause
  exit /b 1
)

echo.
echo Checking ComfyUI API at http://127.0.0.1:8188 ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo.
  echo FAIL: ComfyUI API is not reachable.
  echo Start ComfyUI, wait until the browser page opens, then run this file again.
  echo Expected address: http://127.0.0.1:8188
  echo.
  pause
  exit /b 1
)

echo OK: ComfyUI API is reachable.
echo.
echo Regenerating only N2 rows marked NO.
echo New images will be written to: %OUTDIR%\files
echo Existing NO folder images are kept for comparison.
echo.

"%PYTHON%" "%GEN_SCRIPT%" ^
  --comfy-url "http://127.0.0.1:8188" ^
  --workflow-template "E:\AI\ComfyUI_workflows\AnimagineXL4_text_to_image.json" ^
  --use-template-settings ^
  --levels N2 ^
  --limit 0 ^
  --checkpoint "animagine-xl-4.0-opt.safetensors" ^
  --style anime ^
  --width 768 ^
  --height 768 ^
  --steps 28 ^
  --cfg 7.0 ^
  --sampler dpmpp_2m ^
  --scheduler karras ^
  --overwrite ^
  --max-errors 20 ^
  --only-review-values NO ^
  --out-dir "%OUTDIR%"

echo.
echo Finished. Check the summary above.
pause

