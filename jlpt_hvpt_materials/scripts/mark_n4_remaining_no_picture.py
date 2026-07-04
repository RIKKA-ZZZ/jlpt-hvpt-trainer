from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "jlpt_hvpt_materials" / "derived"
DEFAULT_INPUT = DERIVED / "jlpt_vocab_imageable_candidates.csv"
DEFAULT_FILES_DIR = ROOT / "tup_n4" / "files"
IMAGE_ID_RE = re.compile(r"^(n[1-5]_\d+)")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
NO_PICTURE = "NO PICTURE"
OK = "OK"


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def backup_input(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.stem}.before_n4_remaining_no_picture_{stamp}{path.suffix}")
    shutil.copy2(path, backup)
    return backup


def image_ids_in(folder: Path) -> set[str]:
    if not folder.exists():
        return set()
    ids = set()
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        match = IMAGE_ID_RE.match(path.name)
        if match:
            ids.add(match.group(1))
    return ids


def n4_review_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    fields = ["id", "word", "reading", "meaning", "image_review"]
    return [{field: row.get(field, "") for field in fields} for row in rows if row.get("jlpt_level") == "N4"]


def n4_generation_candidate_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    fields = ["id", "word", "reading", "meaning", "image_type", "visual_domain", "image_query_en", "review"]
    candidates = []
    for row in rows:
        if row.get("jlpt_level") != "N4":
            continue
        review = (row.get("image_review") or "").strip()
        if review in {OK, NO_PICTURE}:
            continue
        candidates.append(
            {
                "id": row.get("id", ""),
                "word": row.get("word", ""),
                "reading": row.get("reading", ""),
                "meaning": row.get("meaning", ""),
                "image_type": row.get("image_type", ""),
                "visual_domain": row.get("visual_domain", ""),
                "image_query_en": row.get("image_query_en", ""),
                "review": review,
            }
        )
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mark every remaining non-OK N4 vocabulary item as NO PICTURE."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--files-dir", type=Path, default=DEFAULT_FILES_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows, fields = read_csv(args.input)
    if not rows:
        raise SystemExit("No rows found.")
    if "image_review" not in fields:
        fields.append("image_review")
        for row in rows:
            row.setdefault("image_review", "")

    passed_ids = image_ids_in(args.files_dir)
    changed: list[dict[str, str]] = []
    changed_to_ok = 0
    changed_to_no_picture = 0
    for row in rows:
        if row.get("jlpt_level") != "N4":
            continue
        current = (row.get("image_review") or "").strip()
        new_review = OK if row.get("id") in passed_ids else NO_PICTURE
        if current == new_review:
            continue
        changed.append(
            {
                "id": row.get("id", ""),
                "word": row.get("word", ""),
                "reading": row.get("reading", ""),
                "meaning": row.get("meaning", ""),
                "previous_review": current,
                "new_review": new_review,
            }
        )
        if new_review == OK:
            changed_to_ok += 1
        else:
            changed_to_no_picture += 1
        row["image_review"] = new_review

    n4_rows = [row for row in rows if row.get("jlpt_level") == "N4"]
    review_counts = Counter((row.get("image_review") or "").strip() for row in n4_rows)
    unreviewed = [
        row
        for row in n4_rows
        if (row.get("image_review") or "").strip() not in {OK, NO_PICTURE}
    ]
    summary = {
        "input": str(args.input),
        "files_dir": str(args.files_dir),
        "dry_run": args.dry_run,
        "n4_total": len(n4_rows),
        "passed_image_ids": len(passed_ids),
        "changed_to_ok": changed_to_ok,
        "changed_to_no_picture": changed_to_no_picture,
        "total_review_changes": len(changed),
        "n4_review_counts": dict(review_counts),
        "n4_unreviewed_remaining": len(unreviewed),
    }

    DERIVED.mkdir(parents=True, exist_ok=True)
    write_csv(
        DERIVED / "n4_remaining_marked_no_picture_rows.csv",
        changed,
        ["id", "word", "reading", "meaning", "previous_review", "new_review"],
    )
    write_csv(
        DERIVED / "n4_current_review_rows.csv",
        n4_review_rows(rows),
        ["id", "word", "reading", "meaning", "image_review"],
    )
    write_csv(
        DERIVED / "n4_image_generation_candidates.csv",
        n4_generation_candidate_rows(rows),
        ["id", "word", "reading", "meaning", "image_type", "visual_domain", "image_query_en", "review"],
    )

    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if changed:
        backup = backup_input(args.input)
        write_csv(args.input, rows, fields)
        summary["updated_input"] = True
        summary["backup"] = str(backup)
    else:
        summary["updated_input"] = False
        summary["backup"] = ""

    (DERIVED / "n4_remaining_no_picture_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
