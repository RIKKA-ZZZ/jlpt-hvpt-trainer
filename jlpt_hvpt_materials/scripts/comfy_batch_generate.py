from __future__ import annotations

import argparse
import copy
import csv
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "derived" / "jlpt_vocab_imageable_candidates.csv"
DEFAULT_OUT = ROOT / "images" / "comfy_generated"
DEFAULT_COMFY_URL = "http://127.0.0.1:8188"
DEFAULT_CHECKPOINT = "animagine-xl-4.0-opt.safetensors"
DEFAULT_WORKFLOW_TEMPLATE = None
ZH_TOOLS = ROOT.parent / "hvpt_site" / "tools"
if ZH_TOOLS.exists():
    sys.path.insert(0, str(ZH_TOOLS))
try:
    from zh_meanings import meaning_to_zh
except Exception:  # noqa: BLE001
    def meaning_to_zh(meaning: str) -> str:
        return ""

REVIEW_COLUMNS = (
    "image_review",
    "NO",
    "no",
    "image_review_status",
    "review_status",
    "manual_review",
    "image_note",
    "review",
)
DEFAULT_REDO_REVIEW_VALUES = {
    "redo",
    "no",
    "bad",
    "red",
    "ng",
    "problem",
    "issue",
    "fix",
    "\u95ee\u9898",
    "\u91cd\u505a",
    "\u4e0d\u5408\u683c",
    "\u7ea2\u8272",
}
NO_PICTURE_REVIEW_VALUES = {
    "no picture",
    "no-picture",
    "no_picture",
    "nopicture",
    "\u65e0\u56fe",
    "\u4e0d\u914d\u56fe",
    "\u4e0d\u8981\u56fe\u7247",
}
DEFAULT_SKIP_REVIEW_VALUES = DEFAULT_REDO_REVIEW_VALUES | {
    "skip",
    "ignore",
    "\u8df3\u8fc7",
} | NO_PICTURE_REVIEW_VALUES


NEGATIVE_PROMPT = (
    "text, letters, Japanese text, English text, watermark, logo, caption, signature, "
    "multiple panels, comic panel, UI, icon, app icon, flat icon, silhouette, simple blob, "
    "abstract shape, color block, posterized, vector logo, cluttered background, cropped subject, "
    "blurry, low quality, low resolution, distorted, deformed, extra limbs, extra fingers, "
    "bad hands, scary, horror, gore, nsfw"
)


QUERY_OVERRIDES = {
    "animal": "a friendly wild animal",
    "body": "a standing anime human full body figure, neutral pose, whole body visible",
    "health": "a cheerful healthy anime student smiling with energetic pose",
    "mouth": "a close-up of a human mouth on an anime person's face, lips visible, gentle smile",
    "hand": "one open human hand with five fingers, palm visible, wrist attached",
    "tooth": "a smiling human mouth showing clean white teeth",
    "eye": "a close-up of one human eye on an anime person's face, visible iris, eyelashes and eyebrow",
    "ear": "one human ear on the side of an anime person's head, hair tucked behind the ear",
    "medicine": "a set of medicine pills and a medicine bottle",
    "foot": "lower legs and sock-covered human feet standing on a simple floor, ankles visible, feet are the main subject",
    "nose": "a close-up of a human nose on an anime person's face, nose bridge and nostrils visible",
    "stomach": "front-view clothed torso with a soft colored circle highlighting the belly area on the shirt",
    "business shirt": "a white dress shirt",
    "western-style clothes": "neatly folded clothes",
    "green tea": "a cup of green tea",
    "rice bowl": "a rice bowl",
    "chicken meat": "raw chicken meat on a plate",
    "coffee lounge": "a small coffee shop interior",
    "cooked rice": "a bowl of cooked rice",
    "midday meal": "a lunch meal set",
    "evening meal": "a dinner meal set",
    "black tea": "a cup of black tea",
    "weather": "a simple sky showing weather",
    "cloudy weather": "a cloudy sky",
}


WORD_PROMPT_OVERRIDES = {
    "口": (
        "close-up portrait of one anime person's face, the human mouth is the main focus, "
        "lips and open mouth clearly visible, one small finger points near the mouth, simple background"
    ),
    "体": (
        "full-length portrait of one anime person standing front view, whole human body is the main subject, "
        "head, torso, arms, legs and feet all visible, simple clothes, centered"
    ),
    "身体": (
        "full-length portrait of one anime person standing front view, whole human body is the main subject, "
        "head, torso, arms, legs and feet all visible, simple clothes, centered"
    ),
    "人体": (
        "full-length portrait of one anime person standing front view, whole human body is the main subject, "
        "head, torso, arms, legs and feet all visible, simple clothes, centered"
    ),
    "おなか": (
        "front-view anime person from shoulders to hips, wearing a plain fitted shirt, "
        "stomach and belly area centered, soft colored circle highlighting the belly area on the shirt, "
        "no exposed skin, hands small and not the main subject"
    ),
    "お腹": (
        "front-view anime person from shoulders to hips, wearing a plain fitted shirt, "
        "stomach and belly area centered, soft colored circle highlighting the belly area on the shirt, "
        "no exposed skin, hands small and not the main subject"
    ),
    "目": (
        "close-up portrait of one anime person's face, one human eye is the main focus, "
        "visible iris, eyelashes and eyebrow, simple background"
    ),
    "耳": (
        "side portrait of one anime person's head, one human ear is the main focus, "
        "hair tucked behind the ear, simple background"
    ),
    "鼻": (
        "close-up portrait of one anime person's face, human nose is the main focus, "
        "nose bridge and nostrils visible, simple background"
    ),
    "足": (
        "lower legs and sock-covered human feet standing on a simple floor, ankles visible, "
        "feet are the main subject, no bare skin, no toes"
    ),
}


DOMAIN_NEGATIVE_PROMPTS = {
    "body_health": (
        "animal, bird, feathers, wings, beak, paw, claw, hoof, talon, monster, creature, "
        "medical diagram, x-ray, abstract anatomy, grid, chart, calendar, spreadsheet, "
        "window frame, wall panels, door panels, vertical stripes, empty room"
    ),
}


WORD_NEGATIVE_PROMPTS = {
    "口": "grid, chart, calendar, spreadsheet, form, window, shelf, frame, border, blank paper, beak, snout",
    "体": "wall, wall panels, door, cabinet, vertical stripes, abstract background, empty room, object, mannequin, torso only, cropped body",
    "身体": "wall, wall panels, door, cabinet, vertical stripes, abstract background, empty room, object, mannequin, torso only, cropped body",
    "人体": "wall, wall panels, door, cabinet, vertical stripes, abstract background, empty room, object, mannequin, torso only, cropped body",
    "おなか": "hand close-up, giant hand, open hand, stomach organ, intestines, food, medical diagram, bare chest, nude, nsfw",
    "お腹": "hand close-up, giant hand, open hand, stomach organ, intestines, food, medical diagram, bare chest, nude, nsfw",
}


SUBJECT_NEGATIVE_PROMPTS = {
    "body": "object, mannequin, doll, statue, cropped head, cropped legs",
    "mouth": "beak, snout, animal mouth, monster mouth",
    "hand": "paw, claw, talon, glove, extra fingers, missing fingers",
    "tooth": "animal teeth, monster teeth, skull, comb, saw, gear, cog",
    "eye": "animal eye, bird, beak, feather, wing, glass sphere, orb, crystal, gem, planet, abstract object",
    "ear": "animal ear, cat ears, rabbit ears, dog ears, horn, bird",
    "foot": "bird, animal, paw, claw, hoof, talon, feather, wing, bare skin, toes, fetish, flipper",
    "nose": "beak, snout, animal nose, bird",
    "stomach": "food, stomach organ, intestines, medical anatomy, animal",
}


DOMAIN_STYLE = {
    "animal": "single animal, whole body visible, expressive eyes, fur or feathers, easy to recognize",
    "body_health": "human body context, clean non-medical educational picture, visible details, easy to recognize",
    "clothing": "single clothing item, product-view composition, visible fabric details",
    "food_drink": "single food or drink item, appetizing, visible details",
    "nature_weather": "clear natural scene, simple composition, recognizable weather or nature element",
    "object_tool": "single everyday object, product-view composition, visible details",
    "person_family": "one person, friendly neutral pose, clear face and clothing",
    "place_building": "single recognizable place or building, simple background",
    "transport": "single vehicle, side view, visible wheels or shape",
    "action_state": "one person performing the action, full body visible",
    "color_shape": "single simple object showing the color or shape, visible outline",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "jlpt_level",
        "word",
        "reading",
        "meaning",
        "visual_domain",
        "image_query_en",
        "review_status",
        "prompt",
        "negative_prompt",
        "checkpoint",
        "seed",
        "local_path",
        "comfy_prompt_id",
        "comfy_filename",
        "status",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_name(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value.strip())
    value = re.sub(r"_+", "_", value)
    return value[:90] or "image"


def compact_english_meaning(value: str) -> str:
    text = (value or "").strip()
    text = re.sub(r"^\(\d+\)\s*", "", text)
    text = re.sub(r"^\([^)]*\)\s*", "", text)
    text = re.split(r"[|;]", text, maxsplit=1)[0]
    text = text.split(",", 1)[0]
    text = re.sub(r"\([^)]*\)", "", text)
    return text.strip(" .")[:60]


def output_stem(row: dict[str, str]) -> str:
    parts = [row["id"], safe_name(row.get("word", ""))]
    meaning_zh = (row.get("meaning_zh") or "").strip() or meaning_to_zh(row.get("meaning", ""))
    if meaning_zh:
        parts.append(safe_name(meaning_zh))
    else:
        fallback = compact_english_meaning(row.get("meaning", ""))
        if fallback:
            parts.append(safe_name(fallback))
    return "_".join(parts)[:150]


def request_json(url: str, data: dict | None = None, timeout: int = 60) -> dict:
    body = None
    headers = {
        "User-Agent": "JLPT-HVPT-ComfyUI-batch/0.1",
        "Accept": "application/json",
    }
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = resp.read().decode("utf-8")
        return json.loads(payload) if payload else {}


def download_bytes(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JLPT-HVPT-ComfyUI-batch/0.1",
            "Accept": "image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def check_server(base_url: str) -> None:
    try:
        request_json(f"{base_url.rstrip('/')}/system_stats", timeout=10)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "ComfyUI API is not reachable. Start ComfyUI first, then rerun this script.\n"
            f"Expected: {base_url}\n"
            "On your machine, try launching:\n"
            r"E:\AI\ComfyUI_windows_portable\run_nvidia_gpu.bat"
        ) from exc


def normalize_subject(row: dict[str, str]) -> str:
    word = row.get("word", "").strip()
    if word in WORD_PROMPT_OVERRIDES:
        return WORD_PROMPT_OVERRIDES[word]
    subject = (row.get("image_query_en") or row.get("meaning") or row.get("word") or "").strip()
    subject = subject.split("|")[0].split(",")[0].strip()
    return QUERY_OVERRIDES.get(subject.lower(), subject)


def subject_key(row: dict[str, str]) -> str:
    subject = (row.get("image_query_en") or row.get("meaning") or row.get("word") or "").strip()
    return subject.split("|")[0].split(",")[0].strip().lower()


def build_negative_prompt(row: dict[str, str], base_negative: str = NEGATIVE_PROMPT) -> str:
    parts = [base_negative]
    domain_negative = DOMAIN_NEGATIVE_PROMPTS.get(row.get("visual_domain", ""))
    if domain_negative:
        parts.append(domain_negative)
    word_negative = WORD_NEGATIVE_PROMPTS.get(row.get("word", "").strip())
    if word_negative:
        parts.append(word_negative)
    subject_negative = SUBJECT_NEGATIVE_PROMPTS.get(subject_key(row))
    if subject_negative:
        parts.append(subject_negative)
    return ", ".join(parts)


def build_prompt(row: dict[str, str], style: str) -> str:
    subject = normalize_subject(row)
    domain = row.get("visual_domain", "")
    domain_style = DOMAIN_STYLE.get(domain, "single clear subject")

    if domain == "action_state":
        core = f"{subject}, {domain_style}"
    elif subject.lower().startswith(("a ", "an ", "the ", "one ")):
        core = f"{subject}, {domain_style}"
    else:
        core = f"a {subject}, {domain_style}"

    if style == "anime" and domain == "body_health":
        return (
            f"masterpiece, best quality, clean anime educational spot illustration, {core}, centered, "
            "simple light background, soft colors, clean line art, gentle shading, "
            "clear recognizable human subject, single main subject, no text, no watermark, "
            "no border, no frame, no chart"
        )
    if style == "anime":
        return (
            f"masterpiece, best quality, anime picture dictionary illustration, {core}, centered, "
            "simple warm light background, soft colors, clean line art, gentle shading, "
            "clear recognizable subject, educational vocabulary card, single main subject, "
            "no text, no watermark"
        )
    if style == "photo":
        return (
            f"A bright realistic photo of {core}, centered, simple light background, "
            "clear subject, educational vocabulary card image, no text, no watermark"
        )
    if style == "flat":
        return (
            f"A clean flat vector illustration of {core}, centered, simple light background, "
            "clear shape, educational vocabulary card image, no text, no watermark"
        )
    return (
        f"A clean educational illustration of {core}, centered, simple light background, "
        "soft natural colors, clear subject, suitable for a Japanese vocabulary learning app, "
        "no text, no watermark"
    )


def make_workflow(
    prompt: str,
    negative: str,
    checkpoint: str,
    seed: int,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    sampler: str,
    scheduler: str,
    filename_prefix: str,
) -> dict:
    return {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": filename_prefix, "images": ["8", 0]},
        },
    }


def load_workflow_template(path: Path | None) -> dict | None:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if is_api_workflow(data) or is_ui_workflow(data):
        return data
    raise ValueError(f"Unsupported ComfyUI workflow format: {path}")


def is_api_workflow(data: object) -> bool:
    return isinstance(data, dict) and all(
        isinstance(value, dict) and "class_type" in value and "inputs" in value
        for value in data.values()
    )


def is_ui_workflow(data: object) -> bool:
    return isinstance(data, dict) and isinstance(data.get("nodes"), list) and isinstance(data.get("links"), list)


def ui_workflow_to_api(data: dict) -> dict:
    link_map = {link[0]: link for link in data.get("links", [])}
    api: dict[str, dict] = {}
    for node in data.get("nodes", []):
        node_id = str(node["id"])
        class_type = node["type"]
        widgets = node.get("widgets_values") or []
        inputs: dict[str, object] = {}

        if class_type == "CheckpointLoaderSimple":
            inputs["ckpt_name"] = widgets[0] if widgets else DEFAULT_CHECKPOINT
        elif class_type == "CLIPTextEncode":
            inputs["text"] = widgets[0] if widgets else ""
        elif class_type == "EmptyLatentImage":
            inputs["width"] = int(widgets[0]) if len(widgets) > 0 else 768
            inputs["height"] = int(widgets[1]) if len(widgets) > 1 else 768
            inputs["batch_size"] = int(widgets[2]) if len(widgets) > 2 else 1
        elif class_type == "KSampler":
            inputs["seed"] = int(widgets[0]) if len(widgets) > 0 else 1
            inputs["steps"] = int(widgets[2]) if len(widgets) > 2 else 28
            inputs["cfg"] = float(widgets[3]) if len(widgets) > 3 else 7.0
            inputs["sampler_name"] = widgets[4] if len(widgets) > 4 else "dpmpp_2m"
            inputs["scheduler"] = widgets[5] if len(widgets) > 5 else "karras"
            inputs["denoise"] = float(widgets[6]) if len(widgets) > 6 else 1.0
        elif class_type == "SaveImage":
            inputs["filename_prefix"] = widgets[0] if widgets else "ComfyUI"

        for input_item in node.get("inputs", []):
            link_id = input_item.get("link")
            if link_id is None:
                continue
            link = link_map.get(link_id)
            if not link:
                continue
            inputs[input_item["name"]] = [str(link[1]), int(link[2])]

        api[node_id] = {"class_type": class_type, "inputs": inputs}
    return api


def workflow_to_api(template: dict | None) -> dict | None:
    if template is None:
        return None
    if is_api_workflow(template):
        return copy.deepcopy(template)
    if is_ui_workflow(template):
        return ui_workflow_to_api(template)
    raise ValueError("Unsupported ComfyUI workflow template")


def find_nodes_by_type(workflow: dict, class_type: str) -> list[str]:
    return [
        node_id
        for node_id, node in workflow.items()
        if node.get("class_type") == class_type and isinstance(node.get("inputs"), dict)
    ]


def find_ksampler_nodes(workflow: dict) -> list[str]:
    return [
        node_id
        for node_id, node in workflow.items()
        if node.get("class_type") in {"KSampler", "KSamplerAdvanced"} and isinstance(node.get("inputs"), dict)
    ]


def find_prompt_nodes(workflow: dict) -> tuple[str, str]:
    positive_node = ""
    negative_node = ""
    for sampler_id in find_ksampler_nodes(workflow):
        sampler_inputs = workflow[sampler_id].get("inputs", {})
        positive_ref = sampler_inputs.get("positive")
        negative_ref = sampler_inputs.get("negative")
        if isinstance(positive_ref, list) and positive_ref:
            positive_node = str(positive_ref[0])
        if isinstance(negative_ref, list) and negative_ref:
            negative_node = str(negative_ref[0])
        if positive_node and negative_node:
            return positive_node, negative_node

    text_nodes = find_nodes_by_type(workflow, "CLIPTextEncode")
    if len(text_nodes) >= 2:
        return text_nodes[0], text_nodes[1]
    if len(text_nodes) == 1:
        return text_nodes[0], ""
    raise ValueError("Workflow template does not contain a CLIPTextEncode prompt node")


def template_negative_prompt(template_api: dict | None) -> str:
    if template_api is None:
        return NEGATIVE_PROMPT
    _, negative_node = find_prompt_nodes(template_api)
    if negative_node and negative_node in template_api:
        value = template_api[negative_node].get("inputs", {}).get("text", "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return NEGATIVE_PROMPT


def set_workflow_prompts(workflow: dict, prompt: str, negative: str) -> None:
    positive_node, negative_node = find_prompt_nodes(workflow)
    workflow[positive_node]["inputs"]["text"] = prompt
    if negative_node:
        workflow[negative_node]["inputs"]["text"] = negative


def workflow_checkpoint(workflow: dict, fallback: str) -> str:
    for node_id in find_nodes_by_type(workflow, "CheckpointLoaderSimple"):
        value = workflow[node_id].get("inputs", {}).get("ckpt_name")
        if isinstance(value, str) and value:
            return value
    return fallback


def apply_workflow_generation_settings(
    workflow: dict,
    checkpoint: str,
    seed: int,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    sampler: str,
    scheduler: str,
    use_template_settings: bool,
) -> None:
    for node_id in find_nodes_by_type(workflow, "CheckpointLoaderSimple"):
        if not use_template_settings:
            workflow[node_id]["inputs"]["ckpt_name"] = checkpoint

    for node_id in find_nodes_by_type(workflow, "EmptyLatentImage"):
        inputs = workflow[node_id]["inputs"]
        inputs["width"] = width
        inputs["height"] = height
        inputs["batch_size"] = 1

    for node_id in find_ksampler_nodes(workflow):
        inputs = workflow[node_id]["inputs"]
        inputs["seed"] = seed
        if not use_template_settings:
            inputs["steps"] = steps
            inputs["cfg"] = cfg
            inputs["sampler_name"] = sampler
            inputs["scheduler"] = scheduler


def set_workflow_filename_prefix(workflow: dict, filename_prefix: str) -> None:
    save_nodes = find_nodes_by_type(workflow, "SaveImage")
    if not save_nodes:
        raise ValueError("Workflow template does not contain a SaveImage node")
    for node_id in save_nodes:
        workflow[node_id]["inputs"]["filename_prefix"] = filename_prefix


def make_workflow_from_template(
    template: dict,
    prompt: str,
    negative: str,
    checkpoint: str,
    seed: int,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    sampler: str,
    scheduler: str,
    filename_prefix: str,
    use_template_settings: bool,
) -> dict:
    workflow = workflow_to_api(template)
    if workflow is None:
        raise ValueError("Workflow template is empty")
    set_workflow_prompts(workflow, prompt, negative)
    apply_workflow_generation_settings(
        workflow=workflow,
        checkpoint=checkpoint,
        seed=seed,
        width=width,
        height=height,
        steps=steps,
        cfg=cfg,
        sampler=sampler,
        scheduler=scheduler,
        use_template_settings=use_template_settings,
    )
    set_workflow_filename_prefix(workflow, filename_prefix)
    return workflow


def wait_for_history(base_url: str, prompt_id: str, timeout: int, interval: float) -> dict:
    deadline = time.time() + timeout
    url = f"{base_url.rstrip('/')}/history/{urllib.parse.quote(prompt_id)}"
    while time.time() < deadline:
        history = request_json(url, timeout=30)
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(interval)
    raise TimeoutError(f"Timed out waiting for prompt {prompt_id}")


def extract_first_image(history_item: dict) -> dict:
    outputs = history_item.get("outputs", {})
    for output in outputs.values():
        images = output.get("images") or []
        if images:
            return images[0]
    raise RuntimeError("ComfyUI history contained no image outputs")


def fetch_comfy_image(base_url: str, image_info: dict) -> bytes:
    params = {
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output"),
    }
    url = f"{base_url.rstrip('/')}/view?{urllib.parse.urlencode(params)}"
    return download_bytes(url)


def load_existing_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {row["id"]: row for row in read_csv(path) if row.get("id")}


def split_review_values(value: str) -> set[str]:
    return {item for item in re.split(r"[\s,;|/]+", value.strip().lower()) if item}


def normalize_review_values(values: list[str]) -> set[str]:
    result: set[str] = set()
    for value in values:
        result.update(split_review_values(value))
    return result


def row_review_status(row: dict[str, str]) -> str:
    for column in REVIEW_COLUMNS:
        value = row.get(column, "").strip()
        if value:
            return value
    return ""


def row_review_matches(row: dict[str, str], values: set[str]) -> bool:
    if not values:
        return False
    status = row_review_status(row).strip().lower()
    if not status:
        return False
    if status in NO_PICTURE_REVIEW_VALUES:
        return status in values
    return status in values or bool(split_review_values(status) & values)


def select_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    rows = read_csv(args.input)
    levels = set(args.levels or [])
    domains = set(args.domains or [])
    only_review_values = normalize_review_values(args.only_review_values or [])
    skip_review_values = normalize_review_values(args.skip_review_values or [])
    if args.only_default_review_values:
        only_review_values.update(DEFAULT_REDO_REVIEW_VALUES)
    if args.skip_default_review_values:
        skip_review_values.update(DEFAULT_SKIP_REVIEW_VALUES)
    selected = []
    for row in rows:
        if levels and row.get("jlpt_level") not in levels:
            continue
        if domains and row.get("visual_domain") not in domains:
            continue
        if row.get("image_status") not in {"direct_image", "scene_image"}:
            continue
        if only_review_values and not row_review_matches(row, only_review_values):
            continue
        if skip_review_values and row_review_matches(row, skip_review_values):
            continue
        selected.append(row)
    if args.offset:
        selected = selected[args.offset :]
    if args.limit and args.limit > 0:
        selected = selected[: args.limit]
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-generate JLPT vocabulary images through a running ComfyUI API server."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--comfy-url", default=DEFAULT_COMFY_URL)
    parser.add_argument("--workflow-template", type=Path, default=DEFAULT_WORKFLOW_TEMPLATE)
    parser.add_argument(
        "--use-template-settings",
        action="store_true",
        help="Use checkpoint, steps, CFG, sampler, and scheduler from --workflow-template. Width and height still come from CLI args.",
    )
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    parser.add_argument("--levels", nargs="*", default=["N5"])
    parser.add_argument("--domains", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offset", type=int, default=0, help="Skip this many selected rows before applying --limit")
    parser.add_argument(
        "--only-review-values",
        nargs="*",
        default=[],
        help="Only generate rows whose review marker matches one of these values",
    )
    parser.add_argument(
        "--skip-review-values",
        nargs="*",
        default=[],
        help="Skip rows whose review marker matches one of these values",
    )
    parser.add_argument(
        "--only-default-review-values",
        action="store_true",
        help="Only generate rows marked with the built-in problem-review values",
    )
    parser.add_argument(
        "--skip-default-review-values",
        action="store_true",
        help="Skip rows marked with the built-in problem-review or skip values",
    )
    parser.add_argument("--style", choices=["anime", "illustration", "flat", "photo"], default="anime")
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--steps", type=int, default=28)
    parser.add_argument("--cfg", type=float, default=7.0)
    parser.add_argument("--sampler", default="dpmpp_2m")
    parser.add_argument("--scheduler", default="karras")
    parser.add_argument("--seed", type=int, default=-1, help="-1 means random seed per image")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--poll-interval", type=float, default=1.5)
    parser.add_argument("--max-errors", type=int, default=0, help="Stop after this many generation errors; 0 means no cap")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    files_dir = args.out_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "comfy_image_manifest.csv"
    existing = load_existing_manifest(manifest_path)
    rows = select_rows(args)
    workflow_template = load_workflow_template(args.workflow_template)
    workflow_template_api = workflow_to_api(workflow_template)
    base_negative_prompt = template_negative_prompt(workflow_template_api)
    effective_checkpoint = (
        workflow_checkpoint(workflow_template_api, args.checkpoint)
        if workflow_template_api and args.use_template_settings
        else args.checkpoint
    )

    if not args.dry_run:
        check_server(args.comfy_url)

    manifest = existing
    skipped_existing = 0
    generated_this_run = 0
    planned_this_run = 0
    errors_this_run = 0
    for index, row in enumerate(rows, start=1):
        row_id = row["id"]
        old = existing.get(row_id)
        if old and old.get("local_path") and Path(old["local_path"]).exists() and not args.overwrite:
            skipped_existing += 1
            print(f"[{index}/{len(rows)}] SKIP {row['word']} -> {old['local_path']}")
            continue

        prompt = build_prompt(row, args.style)
        negative_prompt = build_negative_prompt(row, base_negative_prompt)
        seed = random.randint(1, 2**48 - 1) if args.seed < 0 else args.seed
        stem = output_stem(row)
        out_name = f"{stem}.png"
        local_path = files_dir / out_name
        filename_prefix = f"jlpt_hvpt/{stem}"

        record = {
            "id": row_id,
            "jlpt_level": row.get("jlpt_level", ""),
            "word": row.get("word", ""),
            "reading": row.get("reading", ""),
            "meaning": row.get("meaning", ""),
            "visual_domain": row.get("visual_domain", ""),
            "image_query_en": row.get("image_query_en", ""),
            "review_status": row_review_status(row),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "checkpoint": effective_checkpoint,
            "seed": str(seed),
            "local_path": str(local_path),
            "comfy_prompt_id": "",
            "comfy_filename": "",
            "status": "planned" if args.dry_run else "queued",
            "error": "",
        }

        print(f"[{index}/{len(rows)}] {row['jlpt_level']} {row['word']} -> {normalize_subject(row)}")
        if args.dry_run:
            planned_this_run += 1
            manifest[row_id] = record
            continue

        try:
            if workflow_template:
                workflow = make_workflow_from_template(
                    template=workflow_template,
                    prompt=prompt,
                    negative=negative_prompt,
                    checkpoint=args.checkpoint,
                    seed=seed,
                    width=args.width,
                    height=args.height,
                    steps=args.steps,
                    cfg=args.cfg,
                    sampler=args.sampler,
                    scheduler=args.scheduler,
                    filename_prefix=filename_prefix,
                    use_template_settings=args.use_template_settings,
                )
            else:
                workflow = make_workflow(
                    prompt=prompt,
                    negative=negative_prompt,
                    checkpoint=args.checkpoint,
                    seed=seed,
                    width=args.width,
                    height=args.height,
                    steps=args.steps,
                    cfg=args.cfg,
                    sampler=args.sampler,
                    scheduler=args.scheduler,
                    filename_prefix=filename_prefix,
                )
            client_id = str(uuid.uuid4())
            response = request_json(
                f"{args.comfy_url.rstrip('/')}/prompt",
                data={"prompt": workflow, "client_id": client_id},
                timeout=60,
            )
            prompt_id = response["prompt_id"]
            record["comfy_prompt_id"] = prompt_id
            history_item = wait_for_history(args.comfy_url, prompt_id, args.timeout, args.poll_interval)
            image_info = extract_first_image(history_item)
            image_bytes = fetch_comfy_image(args.comfy_url, image_info)
            local_path.write_bytes(image_bytes)
            record["comfy_filename"] = image_info.get("filename", "")
            record["status"] = "done"
            generated_this_run += 1
        except Exception as exc:  # noqa: BLE001
            record["status"] = "error"
            record["error"] = f"{type(exc).__name__}: {exc}"
            errors_this_run += 1
            print(f"  ERROR: {record['error']}")

        manifest[row_id] = record
        write_csv(manifest_path, list(manifest.values()))
        if args.max_errors and errors_this_run >= args.max_errors:
            print(f"Stopping because --max-errors={args.max_errors} was reached.")
            break

    write_csv(manifest_path, list(manifest.values()))
    with (args.out_dir / "comfy_image_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(list(manifest.values()), fh, ensure_ascii=False, indent=2)

    summary = {
        "out_dir": str(args.out_dir),
        "manifest": str(manifest_path),
        "workflow_template": str(args.workflow_template) if args.workflow_template else "",
        "use_template_settings": args.use_template_settings,
        "checkpoint": effective_checkpoint,
        "selected": len(rows),
        "skipped_existing": skipped_existing,
        "planned_this_run": planned_this_run,
        "generated_this_run": generated_this_run,
        "errors_this_run": errors_this_run,
        "done": sum(1 for item in manifest.values() if item.get("status") == "done"),
        "planned": sum(1 for item in manifest.values() if item.get("status") == "planned"),
        "errors": sum(1 for item in manifest.values() if item.get("status") == "error"),
    }
    (args.out_dir / "comfy_image_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
