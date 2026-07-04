from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT = Path(
    r"D:\codex-2\jlpt_hvpt_materials\derived\jlpt_vocab_imageable_candidates.csv"
)
COL_JA = "Sentence"
COL_EN = "Sentence(eg)"
COL_ZH = "Sentence(zh)"
REVIEW_COL = "Sentence(zh)_needs_review"
NOTE_COL = "Sentence(zh)_note"


@dataclass
class SentenceItem:
    i: int
    row_index: int
    row: dict[str, str]


@dataclass
class SentenceTranslation:
    zh: str = ""
    needs_review: bool = False
    note: str = ""


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


def parse_response(text: str) -> dict[int, SentenceTranslation]:
    text = strip_code_fence(strip_model_thinking(text))
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]

    data = json.loads(text)
    items = data.get("items") or data.get("translations") or []
    if not isinstance(items, list):
        raise ValueError("Ollama returned JSON without an items array.")

    out: dict[int, SentenceTranslation] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        raw_index = item.get("i", item.get("index"))
        if raw_index is None:
            continue
        zh = item.get("sentence_zh") or item.get("zh") or item.get("translation") or ""
        note = item.get("note") or item.get("reason") or ""
        out[int(raw_index)] = SentenceTranslation(
            zh=normalize_text(str(zh)),
            needs_review=parse_bool(item.get("needs_review", False)),
            note=normalize_text(str(note)),
        )
    return out


def post_ollama_json(payload: dict, base_url: str, timeout: int, retries: int) -> dict:
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
        "You are a professional Japanese/English-to-Simplified-Chinese sentence translator "
        "for a JLPT learning website. Translate each example sentence into natural Simplified Chinese. "
        "Prefer the Japanese sentence as the source of truth; use the English sentence only as context. "
        "Keep the translation faithful, concise, and learner-friendly. "
        "Do not add explanations, pinyin, Japanese, romaji, or English in the sentence_zh field. "
        "If the source sentence is odd, ambiguous, or incomplete, translate the most likely meaning and set needs_review true. "
        "Return JSON only, exactly like: "
        "{\"items\":[{\"i\":1,\"sentence_zh\":\"我今天去学校。\",\"needs_review\":false,\"note\":\"\"}]}."
    )


def make_payload(batch: list[SentenceItem]) -> dict:
    return {
        "items": [
            {
                "i": item.i,
                "id": item.row.get("id", ""),
                "jlpt_level": item.row.get("jlpt_level", ""),
                "word": item.row.get("word", ""),
                "reading": item.row.get("reading", ""),
                "sentence_ja": item.row.get(COL_JA, ""),
                "sentence_en": item.row.get(COL_EN, ""),
            }
            for item in batch
        ]
    }


def validate_translation(item: SentenceItem, translation: SentenceTranslation) -> SentenceTranslation:
    zh = normalize_text(translation.zh)
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

    return SentenceTranslation(
        zh=zh,
        needs_review=needs_review,
        note="; ".join(dict.fromkeys(note for note in notes if note)),
    )


def translate_batch(batch: list[SentenceItem], args: argparse.Namespace) -> dict[int, SentenceTranslation]:
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
    data = post_ollama_json(payload, args.base_url, args.timeout, args.retries)
    content = data.get("message", {}).get("content", "")
    translated = parse_response(content)
    return {
        item.i: validate_translation(item, translated.get(item.i, SentenceTranslation()))
        for item in batch
    }


def translate_batch_resilient(batch: list[SentenceItem], args: argparse.Namespace) -> dict[int, SentenceTranslation]:
    try:
        translated = translate_batch(batch, args)
    except Exception as exc:  # noqa: BLE001
        if len(batch) <= 1:
            item = batch[0]
            print(f"  Translation failed for CSV row {item.row_index + 2}: {exc}")
            return {
                item.i: SentenceTranslation(
                    zh="",
                    needs_review=True,
                    note=f"translation failed: {exc}",
                )
            }
        midpoint = len(batch) // 2
        print(f"  Batch failed, retrying smaller batches: {batch[0].i}-{batch[-1].i}")
        out: dict[int, SentenceTranslation] = {}
        out.update(translate_batch_resilient(batch[:midpoint], args))
        out.update(translate_batch_resilient(batch[midpoint:], args))
        return out

    missing = [item for item in batch if not translated.get(item.i, SentenceTranslation()).zh]
    if missing and len(batch) > 1:
        print("  Missing translations, retrying individually: " + ", ".join(str(item.i) for item in missing))
        for item in missing:
            translated.update(translate_batch_resilient([item], args))
    return translated


def chunks(items: list[SentenceItem], size: int) -> Iterable[list[SentenceItem]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise SystemExit(f"No CSV header found: {path}")
        return list(reader.fieldnames), list(reader)


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ensure_fields(fields: list[str], rows: list[dict[str, str]]) -> list[str]:
    out = list(fields)
    for column in [REVIEW_COL, NOTE_COL]:
        if column not in out:
            out.append(column)
            for row in rows:
                row[column] = ""
    return out


def has_source_sentence(row: dict[str, str]) -> bool:
    return bool(normalize_text(row.get(COL_JA, "")) or normalize_text(row.get(COL_EN, "")))


def build_items(rows: list[dict[str, str]], limit: int | None) -> list[SentenceItem]:
    items: list[SentenceItem] = []
    for row_index, row in enumerate(rows):
        if normalize_text(row.get(COL_ZH, "")):
            continue
        if not has_source_sentence(row):
            continue
        items.append(SentenceItem(i=len(items) + 1, row_index=row_index, row=row))
        if limit and len(items) >= limit:
            break
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill missing Sentence(zh) cells using local Ollama.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model", default=os.environ.get("OLLAMA_TRANSLATION_MODEL", "qwen3:8b"))
    parser.add_argument("--base-url", default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    parser.add_argument("--chunk-size", type=int, default=10)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.chunk_size < 1:
        raise SystemExit("--chunk-size must be greater than 0.")

    fields, rows = read_csv_rows(args.input)
    missing_columns = [col for col in [COL_JA, COL_EN, COL_ZH] if col not in fields]
    if missing_columns:
        raise SystemExit("CSV is missing columns: " + ", ".join(missing_columns))
    fields = ensure_fields(fields, rows)

    items = build_items(rows, args.limit)
    no_source_sentence = sum(1 for row in rows if not has_source_sentence(row))
    missing_zh_with_source = sum(
        1 for row in rows
        if has_source_sentence(row) and not normalize_text(row.get(COL_ZH, ""))
    )

    print(f"Input: {args.input}")
    print(f"Rows: {len(rows)}")
    print(f"No source sentence rows: {no_source_sentence}")
    print(f"Missing Sentence(zh) with source: {missing_zh_with_source}")
    print(f"Todo this run: {len(items)}")
    print(f"Model: {args.model}")

    if args.dry_run:
        print("Dry run: CSV was not modified.")
        return
    if not items:
        print("Nothing to translate.")
        return

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = args.input.with_name(f"{args.input.stem}.before_sentence_zh_ollama_{timestamp}{args.input.suffix}")
    shutil.copy2(args.input, backup)
    print(f"Backup: {backup}")

    total_batches = (len(items) + args.chunk_size - 1) // args.chunk_size
    for batch_no, batch in enumerate(chunks(items, args.chunk_size), start=1):
        print(f"Translating batch {batch_no}/{total_batches}: items {batch[0].i}-{batch[-1].i}")
        translated = translate_batch_resilient(batch, args)
        for item in batch:
            result = translated.get(item.i, SentenceTranslation())
            item.row[COL_ZH] = result.zh
            item.row[REVIEW_COL] = "TRUE" if result.needs_review else "FALSE"
            item.row[NOTE_COL] = result.note
        write_rows(args.input, fields, rows)

    print("Done.")


if __name__ == "__main__":
    main()
