@echo off
chcp 65001 >nul
setlocal

echo Start ComfyUI first if it is not already running:
echo E:\AI\ComfyUI_windows_portable\run_nvidia_gpu.bat
echo.
echo This regenerates N5 body/health vocabulary images with stricter prompts.
echo Existing generated files for those words will be overwritten.
echo.

set "PYTHON=C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "SCRIPT=D:\codex-2\jlpt_hvpt_materials\scripts\comfy_batch_generate.py"

"%PYTHON%" "%SCRIPT%" ^
  --comfy-url "http://127.0.0.1:8188" ^
  --workflow-template "E:\AI\ComfyUI_workflows\AnimagineXL4_text_to_image.json" ^
  --use-template-settings ^
  --levels N5 ^
  --domains body_health ^
  --limit 12 ^
  --checkpoint "animagine-xl-4.0-opt.safetensors" ^
  --style anime ^
  --width 768 ^
  --height 768 ^
  --steps 28 ^
  --cfg 7.0 ^
  --sampler dpmpp_2m ^
  --scheduler karras ^
  --overwrite ^
  --out-dir "D:\codex-2\jlpt_hvpt_materials\images\comfy_generated"

pause
