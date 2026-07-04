@echo off
setlocal

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
echo Generating all imageable JLPT vocabulary images.
echo Existing generated images are skipped, so it is safe to stop and rerun.
echo Review-marked rows are skipped in this full pass.
echo.

set "PYTHON=C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "SCRIPT=D:\codex-2\jlpt_hvpt_materials\scripts\comfy_batch_generate.py"
set "OUTDIR=D:\codex-2\jlpt_hvpt_materials\images\comfy_generated"

"%PYTHON%" "%SCRIPT%" ^
  --comfy-url "http://127.0.0.1:8188" ^
  --workflow-template "E:\AI\ComfyUI_workflows\AnimagineXL4_text_to_image.json" ^
  --use-template-settings ^
  --levels N5 N4 N3 N2 N1 ^
  --limit 0 ^
  --checkpoint "animagine-xl-4.0-opt.safetensors" ^
  --style anime ^
  --width 768 ^
  --height 768 ^
  --steps 28 ^
  --cfg 7.0 ^
  --sampler dpmpp_2m ^
  --scheduler karras ^
  --max-errors 20 ^
  --skip-default-review-values ^
  --out-dir "%OUTDIR%"

echo.
echo Finished. Check the summary above.
pause
