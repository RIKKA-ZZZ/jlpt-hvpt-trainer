from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "jlpt_hvpt_materials" / "derived"
DEFAULT_INPUT = DERIVED / "jlpt_vocab_imageable_candidates.csv"
DEFAULT_FILES_DIR = ROOT / "tup_n3" / "files"
IMAGE_ID_RE = re.compile(r"^(n[1-5]_\d+)")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

ZH_TOOLS = ROOT / "hvpt_site" / "tools"
if ZH_TOOLS.exists():
    sys.path.insert(0, str(ZH_TOOLS))

from zh_meanings import meaning_to_zh  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_name(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value.strip())
    value = re.sub(r"_+", "_", value)
    return value[:90] or "image"


def image_id(path: Path) -> str:
    match = IMAGE_ID_RE.match(path.name)
    return match.group(1) if match else ""


def files_in(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS and image_id(path)
    ]


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def update_manifest(manifest_path: Path, paths_by_id: dict[str, Path]) -> int:
    if not manifest_path.exists():
        return 0
    rows = read_csv(manifest_path)
    if not rows:
        return 0
    fields = list(rows[0].keys())
    updated = 0
    for row in rows:
        row_id = row.get("id", "")
        path = paths_by_id.get(row_id)
        if path and "local_path" in row:
            old = row["local_path"]
            row["local_path"] = str(path)
            if row["local_path"] != old:
                updated += 1
    write_csv(manifest_path, rows, fields)
    return updated


def desired_name(path: Path, row: dict[str, str]) -> str:
    meaning_zh = meaning_to_zh(row.get("meaning", ""))
    parts = [row["id"], safe_name(row.get("word", ""))]
    parts.append(safe_name(meaning_zh) if meaning_zh else "中文待补")
    return "_".join(parts)[:150] + path.suffix.lower()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename N3 generated image files to include Chinese meanings without changing review markers."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--files-dir", type=Path, default=DEFAULT_FILES_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows_by_id = {row["id"]: row for row in read_csv(args.input)}
    files = files_in(args.files_dir)
    renamed = []
    missing_rows = []
    missing_zh = []
    paths_by_id: dict[str, Path] = {}

    for path in files:
        row_id = image_id(path)
        row = rows_by_id.get(row_id)
        if not row:
            missing_rows.append({"id": row_id, "file": str(path)})
            continue
        zh = meaning_to_zh(row.get("meaning", ""))
        if not zh:
            missing_zh.append(
                {
                    "id": row_id,
                    "word": row.get("word", ""),
                    "meaning": row.get("meaning", ""),
                    "file": str(path),
                }
            )
        target = path.with_name(desired_name(path, row))
        if target == path:
            paths_by_id[row_id] = path
            continue
        if target.exists():
            target = unique_path(target)
        renamed.append(
            {
                "id": row_id,
                "word": row.get("word", ""),
                "meaning": row.get("meaning", ""),
                "meaningZh": zh,
                "old_file": str(path),
                "new_file": str(target),
            }
        )
        if not args.dry_run:
            path.rename(target)
        paths_by_id[row_id] = target

    manifest_updates = 0
    if not args.dry_run:
        manifest_updates = update_manifest(args.files_dir.parent / "comfy_image_manifest.csv", paths_by_id)

    summary = {
        "dry_run": args.dry_run,
        "files_dir": str(args.files_dir),
        "image_files": len(files),
        "renamed_files": len(renamed),
        "manifest_rows_updated": manifest_updates,
        "missing_rows": len(missing_rows),
        "missing_zh": len(missing_zh),
    }
    write_csv(
        DERIVED / "n3_renamed_with_chinese_rows.csv",
        renamed,
        ["id", "word", "meaning", "meaningZh", "old_file", "new_file"],
    )
    write_csv(
        DERIVED / "n3_missing_chinese_meanings.csv",
        missing_zh,
        ["id", "word", "meaning", "file"],
    )
    (DERIVED / "n3_rename_with_chinese_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
