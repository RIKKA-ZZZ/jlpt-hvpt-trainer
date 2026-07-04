# JLPT / HVPT material pack

This folder collects source material for building a Japanese HVPT listening trainer.

## What is included

### `tanos_vocab/`

JLPT vocabulary lists from Tanos for N1-N5:

- Word documents: `Tanos_VocabList_N*.doc`
- PDFs: `Tanos_VocabList_N*.pdf`
- Anki exports:
  - `Tanos_N*_vocab_kanji_eng.anki`
  - `Tanos_N*_vocab_kanji_hiragana.anki`
- Memrise exports:
  - `Tanos_N*_vocab_kanji_eng.mem`
  - `Tanos_N*_vocab_kanji_hiragana.mem`
- Spreadsheet:
  - `Tanos_jlpt_vocab_2345.xls`

Main source page:

https://www.tanos.co.uk/jlpt/skills/vocab/

### `tanos_audio/`

Vocabulary audio archives from Tanos:

- `Tanos_old_JLPT_N1_vocab_mp3.zip`
- `Tanos_old_JLPT_N2_vocab_mp3.zip`
- `Tanos_JLPT_N4_vocab_mp3.zip`
- `Tanos_JLPT_N5_vocab_mp3.zip`

Note: the Tanos vocabulary page does not list an N3 audio archive. N1/N2 audio comes from the older JLPT audio section on Tanos; N4/N5 audio comes from the newer vocabulary section.

### `jmdict/`

JMdict dictionary data and reference pages:

- `JMdict_e.gz`
- `EDRDG_licence.html`
- `JMdict_project_page.html`

JMdict can be used to enrich the Tanos word lists with readings, parts of speech, variants, and English glosses.

Project page:

https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project

## Licensing notes

Tanos provides a "Use my data" page from its navigation. Before publishing a website that redistributes these materials, confirm the current Tanos sharing terms and keep attribution visible.

JMdict / EDRDG data has its own license. Keep `jmdict/EDRDG_licence.html` with the project and review it before redistribution.

For an HVPT site, a safe first approach is:

1. Use these files as internal seed data.
2. Generate your own derived training pairs.
3. Store source attribution per item.
4. Avoid redistributing raw downloaded archives unless the source license clearly allows it.

## Suggested next processing steps

1. Convert the Tanos `.anki` or `.mem` files into CSV/JSON.
2. Normalize fields into:
   - `jlpt_level`
   - `kanji`
   - `reading`
   - `meaning`
   - `source`
3. Use JMdict to fill missing readings and meanings.
4. Generate HVPT contrast candidates:
   - long vs short vowel
   - geminate vs non-geminate consonant
   - voiced vs unvoiced consonant
   - yoon vs non-yoon
   - pitch-accent contrast
5. Use TTS or recorded audio to create multi-speaker samples.

## Derived image vocabulary lists

The script `scripts/build_imageable_vocab.py` converts the downloaded Tanos Anki decks into image-memory word lists and enriches them with JMdict part-of-speech data.

Generated files live in `derived/`:

- `jlpt_vocab_imageability_all.csv`  
  All extracted JLPT vocabulary with automatic imageability classification.
- `jlpt_vocab_imageable_candidates.csv`  
  Strict candidates that are suitable for picture-choice training. Use this first.
- `jlpt_vocab_imageable_candidates.json`  
  Same strict candidates in JSON format for web apps.
- `jlpt_vocab_image_needs_review.csv`  
  Words that may be usable but need human review.
- `imageable_vocab_summary.json`  
  Counts by level, status, and visual domain.

Classification labels:

- `direct_image`: a single object, animal, place, food, body part, etc.
- `scene_image`: an action or visual state that needs a scene image.
- `review`: possible but not reliable enough for automatic use.
- `skip`: abstract, grammatical, or weak for image-choice training.

## Image fetching scripts

Two experimental image fetchers are available:

- `scripts/fetch_openverse_images.py`  
  Searches Openverse and downloads Creative Commons thumbnails. Default license filter is `cc0,pdm,by,by-sa`.
- `scripts/fetch_wikimedia_images.py`  
  Searches Wikimedia Commons and downloads thumbnails with attribution metadata. Wikimedia may rate-limit fast runs.

Sample outputs:

- `images/openverse_v2/`  
  N5 first-50 sample using improved Openverse queries.
- `images/openverse_v2/openverse_image_manifest.csv`  
  Image manifest with local path, source URL, creator, license, and attribution.
- `images/openverse_v2/openverse_v2_preview_contact_sheet.jpg`  
  Contact sheet for quick visual review.

Important: automatic web-image matching is noisy. Use the manifest as candidate material, not as final approved website art. For production-quality picture-choice training, review the contact sheets or generate controlled images with a local text-to-image workflow.

Example:

```powershell
& "C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "D:\codex-2\jlpt_hvpt_materials\scripts\fetch_openverse_images.py" `
  --levels N5 --limit 50 --out-dir "D:\codex-2\jlpt_hvpt_materials\images\openverse_v2"
```

## ComfyUI batch image generation

For better image consistency than web search, use the local ComfyUI batch script:

- `scripts/comfy_batch_generate.py`  
  Reads `derived/jlpt_vocab_imageable_candidates.csv`, builds prompts, queues jobs through the ComfyUI API, downloads generated images, and writes a manifest.
- `scripts/comfy_dryrun_n5_sample.bat`  
  Generates a prompt manifest only. No ComfyUI connection required.
- `scripts/comfy_generate_n5_sample.bat`  
  Generates the first 20 N5 images through ComfyUI.
- `scripts/comfy_generate_n5_body_fix.bat`  
  Regenerates the N5 body/health words with stricter word-specific prompts. Use this when words like `口`, `体`, `おなか`, `目`, or `足` turn into abstract objects, cards, walls, hands, or animals.
- `scripts/comfy_generate_all_resume.bat`  
  Generates all imageable JLPT vocabulary images. Existing files are skipped, so it can be stopped and rerun.
- `scripts/comfy_regenerate_review_marked.bat`  
  Regenerates only vocabulary rows marked as `NO`, `redo`, `bad`, `red`, `ng`, `problem`, `问题`, `重做`, or `不合格` in a review column.
- `scripts/comfy_check_api.bat`  
  Checks whether the ComfyUI API is reachable at `http://127.0.0.1:8188`.
- `scripts/make_comfy_contact_sheet.py`  
  Creates a review contact sheet from generated images.

Your local ComfyUI path is expected to be:

```text
E:\AI\ComfyUI_windows_portable
```

Available checkpoints found:

```text
sd_xl_base_1.0.safetensors
animagine-xl-4.0-opt.safetensors
ltx-video-2b-v0.9.5.safetensors
```

Recommended first run uses the anime checkpoint for a more consistent vocabulary-card style:

1. Start ComfyUI:

```text
E:\AI\ComfyUI_windows_portable\run_nvidia_gpu.bat
```

2. Run a small N5 sample:

```powershell
& "C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "D:\codex-2\jlpt_hvpt_materials\scripts\comfy_batch_generate.py" `
  --levels N5 --limit 20 --checkpoint "animagine-xl-4.0-opt.safetensors" --style anime
```

The anime prompt intentionally avoids words like `silhouette`, `icon`, and `flat icon`. Those pushed Animagine toward overly simple color-block images. Without a workflow template, the script defaults use:

```text
sampler: dpmpp_2m
scheduler: karras
steps: 28
cfg: 7.0
```

The batch scripts now reuse this saved ComfyUI workflow when available:

```text
E:\AI\ComfyUI_workflows\AnimagineXL4_text_to_image.json
```

That workflow uses:

```text
checkpoint: animagine-xl-4.0-opt.safetensors
sampler: dpmpp_2m
scheduler: karras
steps: 28
cfg: 6.5
```

The original workflow was saved at `832x1216`, but the batch scripts override the latent size to `768x768` so newly generated vocabulary images match the earlier set. The script converts the UI workflow to ComfyUI API format, then replaces the positive prompt, negative prompt, random seed, output filename, and output size for each vocabulary row.

3. Create a review sheet:

```powershell
& "C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "D:\codex-2\jlpt_hvpt_materials\scripts\make_comfy_contact_sheet.py"
```

4. Rebuild website data so generated images replace Openverse images when available:

```powershell
& "C:\Users\31520\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "D:\codex-2\hvpt_site\tools\build_site_data.py"
```

Default generated image output:

```text
D:\codex-2\jlpt_hvpt_materials\images\comfy_generated
```

### Full-batch workflow

For a first full pass, start ComfyUI and run:

```text
D:\codex-2\jlpt_hvpt_materials\scripts\comfy_generate_all_resume.bat
```

This skips images already listed in `images/comfy_generated/comfy_image_manifest.csv` with an existing local file. It is safe to stop and rerun.

For review, plain CSV files do not reliably store red cell color. Instead, add one optional column to `derived/jlpt_vocab_imageable_candidates.csv`, for example:

```csv
image_review
NO
NO PICTURE
redo
bad
skip
```

Supported review column names:

```text
image_review, image_review_status, review_status, manual_review, image_note, review
```

Then run:

```text
D:\codex-2\jlpt_hvpt_materials\scripts\comfy_regenerate_review_marked.bat
```

The full-batch script skips rows marked `NO`, `NO PICTURE`, `redo`, `bad`, `red`, `ng`, `problem`, `问题`, `重做`, `不合格`, or `跳过`. The review-regeneration script only runs rows marked as problem rows such as `NO`; it skips `NO PICTURE` rows because those are considered unsuitable for picture generation.

## Manual safe image overrides

Some body words are unreliable or sensitive for text-to-image models. For example, `おなか` may turn into hands or medical organs, and `足` may drift into fetish-like bare-foot/toe imagery or abstract shapes.

For these cases, use deterministic project-generated teaching assets instead of ComfyUI:

- `images/manual_safe/manual_safe_image_manifest.csv`
- `images/manual_safe/files/n5_07725_onaka.svg`
- `images/manual_safe/files/n5_08297_ashi.svg`

`hvpt_site/tools/build_site_data.py` gives these manual safe assets higher priority than ComfyUI and Openverse images.
