from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATERIALS = ROOT / "jlpt_hvpt_materials"
DERIVED = MATERIALS / "derived"
DEFAULT_INPUT = DERIVED / "jlpt_vocab_imageable_candidates.csv"
DEFAULT_TUP_FILES = ROOT / "tup_n4" / "files"
IMAGE_ID_RE = re.compile(r"^(n[1-5]_\d+)")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

ZH_TOOLS = ROOT / "hvpt_site" / "tools"
if ZH_TOOLS.exists():
    sys.path.insert(0, str(ZH_TOOLS))
try:
    from zh_meanings import meaning_to_zh
except Exception:  # noqa: BLE001
    def meaning_to_zh(meaning: str) -> str:
        return ""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
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


def desired_name(path: Path, row: dict[str, str]) -> str:
    meaning_zh = meaning_to_zh(row.get("meaning", ""))
    parts = [row["id"], safe_name(row.get("word", ""))]
    if meaning_zh:
        parts.append(safe_name(meaning_zh))
    else:
        parts.append("中文待补")
    return "_".join(parts)[:150] + path.suffix.lower()


def rename_images(paths: list[Path], rows_by_id: dict[str, dict[str, str]]) -> tuple[dict[str, Path], int]:
    paths_by_id: dict[str, Path] = {}
    renamed_count = 0
    for path in paths:
        row_id = image_id(path)
        row = rows_by_id.get(row_id)
        if not row:
            continue
        target = path.with_name(desired_name(path, row))
        if target == path:
            paths_by_id[row_id] = path
            continue
        target = unique_path(target)
        path.rename(target)
        paths_by_id[row_id] = target
        renamed_count += 1
    return paths_by_id, renamed_count


def update_manifest(manifest_path: Path, path_by_id: dict[str, Path]) -> int:
    if not manifest_path.exists():
        return 0
    rows = read_csv(manifest_path)
    if not rows:
        return 0
    fields = list(rows[0].keys())
    updated = 0
    for row in rows:
        row_id = row.get("id", "")
        path = path_by_id.get(row_id)
        if path and "local_path" in row:
            row["local_path"] = str(path)
            updated += 1
    write_csv(manifest_path, rows, fields)
    return updated


def backup_input(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.stem}.before_n4_tup_review_{stamp}{path.suffix}")
    shutil.copy2(path, backup)
    return backup


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register N4 generated image review results from tup_n4/files and rename files with Chinese meanings."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--files-dir", type=Path, default=DEFAULT_TUP_FILES)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = read_csv(args.input)
    if not rows:
        raise SystemExit("No vocabulary rows found.")
    fields = list(rows[0].keys())
    rows_by_id = {row["id"]: row for row in rows}

    pass_files = files_in(args.files_dir)
    no_files = files_in(args.files_dir / "NO")
    no_picture_files = files_in(args.files_dir / "NO_PICTURE") + files_in(args.files_dir / "NO PICTURE")

    pass_ids = {image_id(path) for path in pass_files}
    no_picture_ids = {image_id(path) for path in no_picture_files}
    no_ids = {image_id(path) for path in no_files} - pass_ids - no_picture_ids
    status_by_id: dict[str, str] = {}
    status_by_id.update({row_id: "OK" for row_id in pass_ids})
    status_by_id.update({row_id: "NO PICTURE" for row_id in no_picture_ids})
    status_by_id.update({row_id: "NO" for row_id in no_ids})

    if args.dry_run:
        paths_by_id: dict[str, Path] = {}
        renamed_count = 0
    else:
        paths_by_id = {}
        renamed_count = 0
        for batch in (pass_files, no_files, no_picture_files):
            batch_paths, batch_renamed = rename_images(batch, rows_by_id)
            paths_by_id.update(batch_paths)
            renamed_count += batch_renamed

    current_rows = []
    changed = []
    for row in rows:
        if row.get("jlpt_level") != "N4":
            continue
        row_id = row.get("id", "")
        old = row.get("image_review", "")
        new = old
        if row_id in pass_ids:
            new = "OK"
        elif row_id in no_picture_ids:
            new = "NO PICTURE"
        elif row_id in no_ids:
            new = "NO"
        if row_id in status_by_id:
            current_rows.append(
                {
                    "id": row_id,
                    "word": row.get("word", ""),
                    "reading": row.get("reading", ""),
                    "meaning": row.get("meaning", ""),
                    "meaningZh": meaning_to_zh(row.get("meaning", "")),
                    "current_review": old,
                    "folder_review": status_by_id[row_id],
                    "changed": "yes" if new != old else "no",
                }
            )
        if new != old:
            row["image_review"] = new
            changed.append(
                {
                    "id": row_id,
                    "word": row.get("word", ""),
                    "reading": row.get("reading", ""),
                    "meaning": row.get("meaning", ""),
                    "meaningZh": meaning_to_zh(row.get("meaning", "")),
                    "old_review": old,
                    "new_review": new,
                }
            )

    DERIVED.mkdir(parents=True, exist_ok=True)
    write_csv(
        DERIVED / "n4_tup_review_registered_rows.csv",
        current_rows,
        ["id", "word", "reading", "meaning", "meaningZh", "current_review", "folder_review", "changed"],
    )

    n4_review_rows = [
        {
            "id": row.get("id", ""),
            "word": row.get("word", ""),
            "reading": row.get("reading", ""),
            "meaning": row.get("meaning", ""),
            "meaningZh": meaning_to_zh(row.get("meaning", "")),
            "image_review": row.get("image_review", ""),
            "image_type": row.get("image_type", ""),
            "visual_domain": row.get("visual_domain", ""),
            "image_query_en": row.get("image_query_en", ""),
        }
        for row in rows
        if row.get("jlpt_level") == "N4"
    ]
    write_csv(
        DERIVED / "n4_current_review_rows.csv",
        n4_review_rows,
        [
            "id",
            "word",
            "reading",
            "meaning",
            "meaningZh",
            "image_review",
            "image_type",
            "visual_domain",
            "image_query_en",
        ],
    )

    summary = {
        "dry_run": args.dry_run,
        "files_dir": str(args.files_dir),
        "passed_files": len(pass_files),
        "no_files": len(no_files),
        "no_picture_files": len(no_picture_files),
        "passed_ids": len(pass_ids),
        "no_ids": len(no_ids),
        "no_picture_ids": len(no_picture_ids),
        "review_changes": len(changed),
        "renamed_files": renamed_count,
        "manifest_rows_updated": 0,
        "backup": "",
    }

    if not args.dry_run:
        if changed:
            backup = backup_input(args.input)
            write_csv(args.input, rows, fields)
            summary["backup"] = str(backup)
        manifest_updates = update_manifest(args.files_dir.parent / "comfy_image_manifest.csv", paths_by_id)
        summary["manifest_rows_updated"] = manifest_updates

    (DERIVED / "n4_tup_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
