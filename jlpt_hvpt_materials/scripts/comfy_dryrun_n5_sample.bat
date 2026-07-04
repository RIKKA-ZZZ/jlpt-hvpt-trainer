@echo off
chcp 65001 >nul
setlocal

set "PYTHON=C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "SCRIPT=D:\codex-2\jlpt_hvpt_materials\scripts\comfy_batch_generate.py"

"%PYTHON%" "%SCRIPT%" ^
  --workflow-template "E:\AI\ComfyUI_workflows\AnimagineXL4_text_to_image.json" ^
  --use-template-settings ^
  --levels N5 ^
  --limit 20 ^
  --checkpoint "animagine-xl-4.0-opt.safetensors" ^
  --style anime ^
  --dry-run ^
  --out-dir "D:\codex-2\jlpt_hvpt_materials\images\comfy_generated_dryrun"

pause
