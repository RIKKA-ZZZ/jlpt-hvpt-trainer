from __future__ import annotations

import argparse
import bz2
import csv
import datetime as dt
import heapq
import json
import re
import shutil
import tarfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "jlpt_hvpt_materials" / "derived" / "jlpt_vocab_imageable_candidates.csv"
DEFAULT_TATOEBA_DIR = ROOT / "jlpt_hvpt_materials" / "raw" / "tatoeba"
DEFAULT_REPORT_DIR = ROOT / "jlpt_hvpt_materials" / "derived"

COL_SENTENCE_JA = "Sentence"
COL_SENTENCE_EN = "Sentence(eg)"
COL_SENTENCE_ZH = "Sentence(zh)"
TARGET_COLUMNS = [COL_SENTENCE_EN, COL_SENTENCE_ZH, COL_SENTENCE_JA]

JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
BAD_TEXT_RE = re.compile(r"[�ㄅ-ㄩ]|https?://|www\.|@")
SPLIT_RE = re.compile(r"\s*(?:/|／|、|,|，|;|；|\||・)\s*")


def read_vocab(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    for column in TARGET_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)
            for row in rows:
                row[column] = ""
    return fieldnames, rows


def write_vocab(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def primary_parts(value: str) -> list[str]:
    text = (value or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in SPLIT_RE.split(text) if p.strip()]
    return parts or [text]


def looks_japanese(text: str) -> bool:
    return bool(JAPANESE_RE.search(text))


def sentence_is_usable(text: str, min_chars: int, max_chars: int) -> bool:
    stripped = text.strip()
    if not (min_chars <= len(stripped) <= max_chars):
        return False
    if BAD_TEXT_RE.search(stripped):
        return False
    jp_count = len(JAPANESE_RE.findall(stripped))
    return jp_count >= max(2, int(len(stripped) * 0.35))


def build_terms(rows: list[dict[str, str]], levels: set[str] | None, limit: int) -> tuple[dict[str, list[tuple[int, str, int]]], set[int]]:
    by_first: dict[str, list[tuple[int, str, int]]] = defaultdict(list)
    target_rows: set[int] = set()

    for idx, row in enumerate(rows):
        if levels and row.get("jlpt_level", "").upper() not in levels:
            continue
        if limit and len(target_rows) >= limit:
            break
        target_rows.add(idx)

        terms: list[tuple[str, int]] = []
        for word in primary_parts(row.get("word", "")):
            if looks_japanese(word):
                terms.append((word, 40))
        for reading in primary_parts(row.get("reading", "")):
            if looks_japanese(reading):
                terms.append((reading, 26))

        seen = set()
        for term, base_score in terms:
            term = term.strip()
            if not term or term in seen:
                continue
            seen.add(term)
            by_first[term[0]].append((idx, term, base_score))

    # Longer terms should be checked first when many terms share the same first char.
    for key in list(by_first):
        by_first[key].sort(key=lambda item: len(item[1]), reverse=True)

    return by_first, target_rows


def line_parts(line: str) -> list[str]:
    return line.rstrip("\n").split("\t")


def load_sentence_subset(path: Path, wanted_ids: set[int] | None = None) -> dict[int, dict[str, str]]:
    out: dict[int, dict[str, str]] = {}
    with bz2.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line_parts(line)
            if len(parts) < 4:
                continue
            sid = int(parts[0])
            if wanted_ids is not None and sid not in wanted_ids:
                continue
            out[sid] = {
                "id": str(sid),
                "lang": parts[1],
                "text": parts[2],
                "author": parts[3],
            }
    return out


def candidate_score(sentence: str, term: str, base_score: int) -> int:
    length = len(sentence)
    ideal = 18
    length_score = max(0, 24 - abs(length - ideal))
    punctuation_score = 4 if sentence.endswith(("。", "！", "？")) else 0
    term_score = base_score + min(len(term), 8) * 2
    return term_score + length_score + punctuation_score


def push_candidate(
    heaps: dict[int, list[tuple[int, int, str, dict[str, str]]]],
    row_idx: int,
    candidate: dict[str, str],
    score: int,
    max_candidates: int,
) -> None:
    heap = heaps[row_idx]
    item = (score, int(candidate["sentenceId"]), candidate.get("matchedTerm", ""), candidate)
    if len(heap) < max_candidates:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def scan_japanese_candidates(
    tatoeba_dir: Path,
    by_first: dict[str, list[tuple[int, str, int]]],
    min_chars: int,
    max_chars: int,
    max_candidates: int,
) -> dict[int, list[dict[str, str]]]:
    path = tatoeba_dir / "jpn_sentences_detailed.tsv.bz2"
    heaps: dict[int, list[tuple[int, int, str, dict[str, str]]]] = defaultdict(list)

    with bz2.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line_parts(line)
            if len(parts) < 4:
                continue
            sid, _lang, text, author = parts[:4]
            if not sentence_is_usable(text, min_chars, max_chars):
                continue

            checked: set[tuple[int, str]] = set()
            for ch in set(text):
                for row_idx, term, base_score in by_first.get(ch, []):
                    key = (row_idx, term)
                    if key in checked:
                        continue
                    checked.add(key)
                    if term in text:
                        score = candidate_score(text, term, base_score)
                        push_candidate(
                            heaps,
                            row_idx,
                            {
                                "sentenceId": sid,
                                "sentenceJa": text,
                                "authorJa": author,
                                "matchedTerm": term,
                                "baseScore": str(score),
                            },
                            score,
                            max_candidates,
                        )

    out: dict[int, list[dict[str, str]]] = {}
    for row_idx, heap in heaps.items():
        out[row_idx] = [item[3] for item in sorted(heap, reverse=True)]
    return out


def load_links_for_ids(tatoeba_dir: Path, target_ids: set[int]) -> dict[int, set[int]]:
    links: dict[int, set[int]] = defaultdict(set)
    if not target_ids:
        return links
    path = tatoeba_dir / "links.tar.bz2"
    with tarfile.open(path, "r:bz2") as tar:
        member = tar.getmember("links.csv")
        with tar.extractfile(member) as f:
            assert f is not None
            for raw in f:
                line = raw.decode("utf-8", errors="replace").rstrip("\n")
                if not line:
                    continue
                left, right = line.split("\t", 1)
                a = int(left)
                b = int(right)
                if a in target_ids:
                    links[a].add(b)
                if b in target_ids:
                    links[b].add(a)
    return links


def choose_translation(ids: set[int], sentences: dict[int, dict[str, str]], max_chars: int) -> dict[str, str] | None:
    candidates = []
    for sid in ids:
        item = sentences.get(sid)
        if not item:
            continue
        text = item["text"].strip()
        if not text or len(text) > max_chars:
            continue
        candidates.append((abs(len(text) - 42), len(text), sid, item))
    if not candidates:
        return None
    return sorted(candidates)[0][3]


def select_best_candidate(
    candidates: list[dict[str, str]],
    links: dict[int, set[int]],
    second_hop_links: dict[int, set[int]],
    eng_sentences: dict[int, dict[str, str]],
    cmn_sentences: dict[int, dict[str, str]],
    max_translation_chars: int,
) -> dict[str, str] | None:
    best: tuple[int, dict[str, str]] | None = None
    for candidate in candidates:
        sid = int(candidate["sentenceId"])
        linked_ids = links.get(sid, set())
        indirect_ids: set[int] = set()
        for linked_id in linked_ids:
            indirect_ids.update(second_hop_links.get(linked_id, set()))
        eng = choose_translation(linked_ids, eng_sentences, max_translation_chars)
        cmn = choose_translation(linked_ids, cmn_sentences, max_translation_chars)
        if not cmn:
            cmn = choose_translation(indirect_ids, cmn_sentences, max_translation_chars)
        score = int(candidate["baseScore"])
        if eng:
            score += 26
        if cmn:
            score += 20
        if eng and cmn:
            score += 12
        enriched = dict(candidate)
        enriched["sentenceEn"] = eng["text"] if eng else ""
        enriched["authorEn"] = eng["author"] if eng else ""
        enriched["sentenceZh"] = cmn["text"] if cmn else ""
        enriched["authorZh"] = cmn["author"] if cmn else ""
        enriched["finalScore"] = str(score)
        if best is None or score > best[0]:
            best = (score, enriched)
    return best[1] if best else None


def should_fill(row: dict[str, str], overwrite: bool) -> bool:
    if overwrite:
        return True
    return not (row.get(COL_SENTENCE_JA, "").strip() and row.get(COL_SENTENCE_EN, "").strip() and row.get(COL_SENTENCE_ZH, "").strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill JLPT vocabulary CSV sentence columns from Tatoeba.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--tatoeba-dir", type=Path, default=DEFAULT_TATOEBA_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--levels", nargs="*", help="Example: --levels N5 N4")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N matching vocab rows.")
    parser.add_argument("--min-ja-chars", type=int, default=5)
    parser.add_argument("--max-ja-chars", type=int, default=44)
    parser.add_argument("--max-translation-chars", type=int, default=120)
    parser.add_argument("--max-candidates", type=int, default=8)
    parser.add_argument("--no-indirect-zh", action="store_true", help="Only use directly linked Chinese translations.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fieldnames, rows = read_vocab(args.csv)
    levels = {level.upper() for level in args.levels} if args.levels else None
    by_first, target_rows = build_terms(rows, levels, args.limit)

    print(f"Vocabulary rows: {len(rows)}")
    print(f"Target rows: {len(target_rows)}")
    print("Scanning Japanese Tatoeba sentences...")
    candidates_by_row = scan_japanese_candidates(
        args.tatoeba_dir,
        by_first,
        args.min_ja_chars,
        args.max_ja_chars,
        args.max_candidates,
    )

    candidate_jpn_ids = {
        int(candidate["sentenceId"])
        for row_idx, candidates in candidates_by_row.items()
        if row_idx in target_rows
        for candidate in candidates
    }
    print(f"Candidate Japanese sentences: {len(candidate_jpn_ids)}")

    print("Loading translation links...")
    links = load_links_for_ids(args.tatoeba_dir, candidate_jpn_ids)
    linked_ids = {sid for linked in links.values() for sid in linked}
    second_hop_links: dict[int, set[int]] = {}
    if not args.no_indirect_zh:
        print("Loading one-hop translation links for Chinese fallback...")
        second_hop_links = load_links_for_ids(args.tatoeba_dir, linked_ids)
    second_hop_ids = {sid for linked in second_hop_links.values() for sid in linked}

    print("Loading linked English and Chinese sentences...")
    eng_sentences = load_sentence_subset(args.tatoeba_dir / "eng_sentences_detailed.tsv.bz2", linked_ids | second_hop_ids)
    cmn_sentences = load_sentence_subset(args.tatoeba_dir / "cmn_sentences_detailed.tsv.bz2", linked_ids | second_hop_ids)

    report_rows: list[dict[str, str]] = []
    filled = 0
    matched = 0
    with_en = 0
    with_zh = 0
    skipped_existing = 0

    for row_idx in sorted(target_rows):
        row = rows[row_idx]
        if not should_fill(row, args.overwrite):
            skipped_existing += 1
            continue

        best = select_best_candidate(
            candidates_by_row.get(row_idx, []),
            links,
            second_hop_links,
            eng_sentences,
            cmn_sentences,
            args.max_translation_chars,
        )
        if not best:
            report_rows.append({
                "row": str(row_idx + 2),
                "id": row.get("id", ""),
                "level": row.get("jlpt_level", ""),
                "word": row.get("word", ""),
                "reading": row.get("reading", ""),
                "status": "no_match",
            })
            continue

        matched += 1
        if best.get("sentenceEn"):
            with_en += 1
        if best.get("sentenceZh"):
            with_zh += 1

        row[COL_SENTENCE_JA] = best.get("sentenceJa", "")
        row[COL_SENTENCE_EN] = best.get("sentenceEn", "")
        row[COL_SENTENCE_ZH] = best.get("sentenceZh", "")
        filled += 1

        report_rows.append({
            "row": str(row_idx + 2),
            "id": row.get("id", ""),
            "level": row.get("jlpt_level", ""),
            "word": row.get("word", ""),
            "reading": row.get("reading", ""),
            "matchedTerm": best.get("matchedTerm", ""),
            "sentenceId": best.get("sentenceId", ""),
            "sentenceJa": best.get("sentenceJa", ""),
            "sentenceEn": best.get("sentenceEn", ""),
            "sentenceZh": best.get("sentenceZh", ""),
            "authorJa": best.get("authorJa", ""),
            "authorEn": best.get("authorEn", ""),
            "authorZh": best.get("authorZh", ""),
            "score": best.get("finalScore", ""),
            "status": "matched",
        })

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    args.report_dir.mkdir(parents=True, exist_ok=True)

    report_csv = args.report_dir / f"tatoeba_sentence_match_report_{timestamp}.csv"
    report_fields = [
        "row", "id", "level", "word", "reading", "matchedTerm", "sentenceId",
        "sentenceJa", "sentenceEn", "sentenceZh", "authorJa", "authorEn",
        "authorZh", "score", "status",
    ]
    with report_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=report_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report_rows)

    summary = {
        "generatedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "csv": str(args.csv),
        "targetRows": len(target_rows),
        "filledRows": filled,
        "matchedRows": matched,
        "withEnglish": with_en,
        "withChinese": with_zh,
        "skippedExisting": skipped_existing,
        "noMatch": sum(1 for row in report_rows if row.get("status") == "no_match"),
        "dryRun": args.dry_run,
        "reportCsv": str(report_csv),
    }
    summary_path = args.report_dir / f"tatoeba_sentence_match_summary_{timestamp}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.dry_run:
        print("Dry run: CSV was not modified.")
    else:
        backup = args.csv.with_name(f"{args.csv.stem}.before_tatoeba_sentences_{timestamp}{args.csv.suffix}")
        shutil.copy2(args.csv, backup)
        write_vocab(args.csv, fieldnames, rows)
        print(f"Backup: {backup}")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
