from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT = Path(
    r"D:\codex-2\jlpt_hvpt_materials\derived\jlpt_vocab_imageable_candidates.csv"
)

NEW_COLUMNS = ["meaning_zh", "meaning_zh_needs_review", "meaning_zh_note"]


@dataclass
class VocabItem:
    i: int
    row: dict[str, str]


@dataclass
class Translation:
    meaning_zh: str = ""
    needs_review: bool = True
    note: str = ""


def die(message: str, exit_code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(exit_code)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def strip_model_thinking(text: str) -> str:
    text = text.strip()
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>", start) + len("</think>")
        text = (text[:start] + text[end:]).strip()
    return text


def contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def contains_japanese_kana(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u31f0-\u31ff]", text or ""))


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "review"}
    return bool(value)


def parse_translation_response(text: str) -> dict[int, Translation]:
    text = strip_code_fence(strip_model_thinking(text))
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]

    data = json.loads(text)
    items = data.get("items") or data.get("translations") or data.get("segments")
    if not isinstance(items, list):
        raise ValueError("Ollama returned JSON without an items array.")

    result: dict[int, Translation] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        raw_index = item.get("i", item.get("index"))
        if raw_index is None:
            continue

        zh = (
            item.get("meaning_zh")
            or item.get("zh")
            or item.get("translation")
            or item.get("text")
            or ""
        )
        note = item.get("note") or item.get("reason") or ""
        result[int(raw_index)] = Translation(
            meaning_zh=normalize_text(str(zh)),
            needs_review=parse_bool(item.get("needs_review", False)),
            note=normalize_text(str(note)),
        )
    return result


def post_ollama_json(
    payload: dict,
    base_url: str,
    timeout: int,
    retries: int,
) -> dict:
    url = base_url.rstrip("/") + "/api/chat"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last_error = exc

        if attempt < retries:
            wait_seconds = min(20, 2**attempt)
            print(f"Ollama request failed, retrying in {wait_seconds}s ({attempt}/{retries})...")
            time.sleep(wait_seconds)

    raise RuntimeError(f"Ollama request failed: {last_error}")


def system_prompt() -> str:
    return (
        "You are a professional JLPT Japanese-to-Simplified-Chinese vocabulary editor. "
        "Translate each vocabulary entry into concise natural Simplified Chinese glosses for learners. "
        "Use the Japanese word, reading, part of speech, English meaning, and JMdict glosses together. "
        "Prefer the common JLPT learner sense over rare or slang senses. "
        "Keep the Chinese gloss short, usually 1 to 8 Chinese characters or a brief phrase. "
        "If there are important multiple senses, separate them with a Chinese semicolon. "
        "Do not output pinyin, Japanese kana, romaji, or English unless it is a proper noun or acronym. "
        "Do not explain in the meaning_zh field. Put uncertainty in note and set needs_review true. "
        "Return JSON only, exactly like: "
        "{\"items\":[{\"i\":1,\"meaning_zh\":\"动物\",\"needs_review\":false,\"note\":\"\"}]}."
    )


def make_payload(batch: list[VocabItem]) -> dict:
    items = []
    for item in batch:
        row = item.row
        items.append(
            {
                "i": item.i,
                "id": row.get("id", ""),
                "jlpt_level": row.get("jlpt_level", ""),
                "word": row.get("word", ""),
                "reading": row.get("reading", ""),
                "part_of_speech": row.get("jmdict_pos", ""),
                "english_meaning": row.get("meaning", ""),
                "jmdict_glosses": row.get("jmdict_glosses", ""),
                "visual_domain": row.get("visual_domain", ""),
            }
        )
    return {"items": items}


def validate_translation(item: VocabItem, translation: Translation) -> Translation:
    zh = normalize_text(translation.meaning_zh)
    needs_review = translation.needs_review
    notes = [translation.note] if translation.note else []

    if not zh:
        needs_review = True
        notes.append("empty translation")
    if contains_japanese_kana(zh):
        needs_review = True
        notes.append("contains Japanese kana")
    if zh and not contains_cjk(zh):
        needs_review = True
        notes.append("no Chinese characters")

    return Translation(
        meaning_zh=zh,
        needs_review=needs_review,
        note="; ".join(dict.fromkeys(note for note in notes if note)),
    )


def translate_batch(
    batch: list[VocabItem],
    args: argparse.Namespace,
) -> dict[int, Translation]:
    payload = {
        "model": args.model,
        "stream": False,
        "format": "json",
        "options": {"temperature": args.temperature},
        "messages": [
            {"role": "system", "content": system_prompt()},
            {
                "role": "user",
                "content": "/no_think\n" + json.dumps(make_payload(batch), ensure_ascii=False),
            },
        ],
    }

    data = post_ollama_json(
        payload=payload,
        base_url=args.base_url,
        timeout=args.timeout,
        retries=args.retries,
    )
    content = data.get("message", {}).get("content", "")
    translated = parse_translation_response(content)
    return {
        item.i: validate_translation(item, translated.get(item.i, Translation()))
        for item in batch
    }


def translate_batch_resilient(
    batch: list[VocabItem],
    args: argparse.Namespace,
) -> dict[int, Translation]:
    try:
        translated = translate_batch(batch, args)
    except Exception as exc:  # noqa: BLE001
        if len(batch) <= 1:
            item = batch[0]
            print(f"  Translation failed for row {item.i}: {exc}")
            return {
                item.i: Translation(
                    meaning_zh="",
                    needs_review=True,
                    note=f"translation failed: {exc}",
                )
            }

        midpoint = len(batch) // 2
        print(f"  Batch failed, retrying smaller batches: {batch[0].i}-{batch[-1].i}")
        result: dict[int, Translation] = {}
        result.update(translate_batch_resilient(batch[:midpoint], args))
        result.update(translate_batch_resilient(batch[midpoint:], args))
        return result

    missing = [item for item in batch if not translated.get(item.i, Translation()).meaning_zh]
    if missing and len(batch) > 1:
        print("  Missing translations, retrying individually: " + ", ".join(str(item.i) for item in missing))
        for item in missing:
            translated.update(translate_batch_resilient([item], args))
    return translated


def chunks(items: list[VocabItem], size: int) -> Iterable[list[VocabItem]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            die(f"No CSV header found: {path}")
        return list(reader.fieldnames), list(reader)


def build_output_fields(input_fields: list[str]) -> list[str]:
    fields = [field for field in input_fields if field not in NEW_COLUMNS]
    insert_after = "meaning" if "meaning" in fields else fields[-1]
    insert_at = fields.index(insert_after) + 1
    return fields[:insert_at] + NEW_COLUMNS + fields[insert_at:]


def default_output_path(input_path: Path, limit: int | None) -> Path:
    suffix = "ollama_zh_preview" if limit else "ollama_zh"
    return input_path.with_name(f"{input_path.stem}.{suffix}{input_path.suffix}")


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_existing_translations(path: Path) -> dict[str, Translation]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "id" not in reader.fieldnames or "meaning_zh" not in reader.fieldnames:
            return {}

        translations: dict[str, Translation] = {}
        for row in reader:
            key = row.get("id", "")
            zh = normalize_text(row.get("meaning_zh", ""))
            if not key or not zh:
                continue
            translations[key] = Translation(
                meaning_zh=zh,
                needs_review=parse_bool(row.get("meaning_zh_needs_review", "")),
                note=normalize_text(row.get("meaning_zh_note", "")),
            )
        return translations


def apply_existing_translations(
    rows: list[dict[str, str]],
    existing: dict[str, Translation],
) -> int:
    reused = 0
    for row in rows:
        key = row.get("id", "")
        if not key or key not in existing:
            continue
        translation = existing[key]
        row["meaning_zh"] = translation.meaning_zh
        row["meaning_zh_needs_review"] = "TRUE" if translation.needs_review else "FALSE"
        row["meaning_zh_note"] = translation.note
        reused += 1
    return reused


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Translate JLPT vocabulary CSV rows to Simplified Chinese with local Ollama/Qwen."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Source CSV path.")
    parser.add_argument("--output", type=Path, help="Output CSV path. The source CSV is never overwritten.")
    parser.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_TRANSLATION_MODEL", "qwen3:8b"),
        help="Ollama model name, for example qwen3:8b or qwen2.5:7b.",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama API base URL.",
    )
    parser.add_argument("--chunk-size", type=int, default=8, help="Rows per translation batch.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Translation temperature.")
    parser.add_argument("--timeout", type=int, default=180, help="Request timeout in seconds.")
    parser.add_argument("--retries", type=int, default=3, help="Request retries per batch.")
    parser.add_argument("--limit", type=int, help="Translate only the first N rows for preview.")
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore existing output translations and start from scratch.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.chunk_size < 1:
        die("--chunk-size must be greater than 0.")
    if args.limit is not None and args.limit < 1:
        die("--limit must be greater than 0.")

    input_path = args.input.resolve()
    output_path = (args.output or default_output_path(input_path, args.limit)).resolve()
    if input_path == output_path:
        die("Refusing to overwrite the source CSV. Choose a different --output path.")
    if not input_path.exists():
        die(f"Input CSV not found: {input_path}")

    input_fields, rows = read_csv_rows(input_path)
    required = {"id", "word", "reading", "meaning", "jmdict_glosses"}
    missing = sorted(required - set(input_fields))
    if missing:
        die("Input CSV is missing required columns: " + ", ".join(missing))

    if args.limit:
        rows = rows[: args.limit]

    output_fields = build_output_fields(input_fields)
    if not args.no_resume:
        reused = apply_existing_translations(rows, load_existing_translations(output_path))
        if reused:
            print(f"Resumed existing translations: {reused}")

    items = [
        VocabItem(i=index, row=row)
        for index, row in enumerate(rows, start=1)
        if not normalize_text(row.get("meaning_zh", ""))
    ]
    total_batches = (len(items) + args.chunk_size - 1) // args.chunk_size

    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Rows:   {len(rows)}")
    print(f"Todo:   {len(items)}")
    print(f"Model:  {args.model}")

    if not items:
        write_rows(output_path, output_fields, rows)
        print("Nothing to translate.")
        print(output_path)
        return

    for batch_no, batch in enumerate(chunks(items, args.chunk_size), start=1):
        print(f"Translating batch {batch_no}/{total_batches}: rows {batch[0].i}-{batch[-1].i}")
        translated = translate_batch_resilient(batch, args)
        for item in batch:
            result = translated.get(item.i, Translation())
            item.row["meaning_zh"] = result.meaning_zh
            item.row["meaning_zh_needs_review"] = "TRUE" if result.needs_review else "FALSE"
            item.row["meaning_zh_note"] = result.note

        write_rows(output_path, output_fields, rows)

    print("Done.")
    print(output_path)


if __name__ == "__main__":
    main()
