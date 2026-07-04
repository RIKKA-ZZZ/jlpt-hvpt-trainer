from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "derived" / "jlpt_vocab_imageable_candidates.csv"
DEFAULT_OUT = ROOT / "images" / "wikimedia"
API_URL = "https://commons.wikimedia.org/w/api.php"


BAD_TITLE_WORDS = {
    "map",
    "diagram",
    "chart",
    "graph",
    "logo",
    "icon",
    "symbol",
    "flag",
    "coat of arms",
    "seal",
    "text",
    "script",
}


DOMAIN_HINTS = {
    "animal": "animal photo",
    "body_health": "human anatomy photo",
    "clothing": "clothing photo",
    "food_drink": "food drink photo",
    "nature_weather": "nature weather photo",
    "object_tool": "object photo",
    "person_family": "person photo",
    "place_building": "building place photo",
    "transport": "vehicle transport photo",
    "action_state": "person action photo",
    "color_shape": "color object photo",
}


def sanitize_filename(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value.strip())
    value = re.sub(r"_+", "_", value)
    return value[:120] or "image"


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
        "image_status",
        "image_query_en",
        "search_query",
        "local_path",
        "source_provider",
        "source_page",
        "thumb_url",
        "file_title",
        "mime",
        "license",
        "license_url",
        "artist",
        "credit",
        "match_status",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def request_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JLPT-HVPT-local-image-fetcher/0.1 (personal learning tool)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_file(url: str, out_path: Path, timeout: int = 60) -> None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JLPT-HVPT-local-image-fetcher/0.1 (personal learning tool)",
            "Accept": "image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out_path.write_bytes(resp.read())


def get_meta(meta: dict, key: str) -> str:
    value = meta.get(key, {})
    if isinstance(value, dict):
        return str(value.get("value", "") or "")
    return ""


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def score_candidate(page: dict, query: str) -> int:
    title = str(page.get("title", "")).lower()
    imageinfo = (page.get("imageinfo") or [{}])[0]
    mime = str(imageinfo.get("mime", "")).lower()
    meta = imageinfo.get("extmetadata") or {}
    title_words = set(re.findall(r"[a-z]+", title))
    query_words = set(re.findall(r"[a-z]+", query.lower()))

    score = 0
    if mime in {"image/jpeg", "image/png", "image/webp"}:
        score += 20
    if "thumburl" in imageinfo:
        score += 20
    if query_words and query_words & title_words:
        score += 20
    if "photograph" in title or "photo" in title:
        score += 8
    if any(bad in title for bad in BAD_TITLE_WORDS):
        score -= 35
    license_short = get_meta(meta, "LicenseShortName")
    if license_short:
        score += 10
    width = int(imageinfo.get("width") or 0)
    height = int(imageinfo.get("height") or 0)
    if width >= 400 and height >= 400:
        score += 10
    return score


def wikimedia_search(query: str, limit: int, thumb_width: int) -> list[dict]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "gsrsearch": f"{query} filetype:bitmap",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime|size",
        "iiurlwidth": str(thumb_width),
        "redirects": "1",
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    data = request_json(url)
    pages = list((data.get("query", {}).get("pages", {}) or {}).values())
    pages.sort(key=lambda page: score_candidate(page, query), reverse=True)
    return pages


def build_query(row: dict[str, str]) -> str:
    base = (row.get("image_query_en") or row.get("meaning") or row.get("word") or "").strip()
    domain = row.get("visual_domain", "")
    hint = DOMAIN_HINTS.get(domain, "")
    if domain == "action_state":
        return base
    if hint and hint.lower() not in base.lower():
        return f"{base} {hint}"
    return base


def choose_candidate(pages: list[dict], query: str) -> dict | None:
    for page in pages:
        imageinfo = (page.get("imageinfo") or [{}])[0]
        if not imageinfo.get("thumburl"):
            continue
        if str(imageinfo.get("mime", "")).lower() not in {"image/jpeg", "image/png", "image/webp"}:
            continue
        if score_candidate(page, query) < 20:
            continue
        return page
    return None


def existing_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    return {row["id"]: row for row in rows if row.get("id")}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Wikimedia Commons thumbnail images for JLPT imageable vocabulary."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--levels", nargs="*", default=["N5"])
    parser.add_argument("--domains", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--search-limit", type=int, default=8)
    parser.add_argument("--thumb-width", type=int, default=512)
    parser.add_argument("--sleep", type=float, default=0.35)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "wikimedia_image_manifest.csv"
    rows_by_id = existing_manifest(manifest_path)

    source_rows = read_csv(args.input)
    selected: list[dict[str, str]] = []
    levels = set(args.levels)
    domains = set(args.domains)
    for row in source_rows:
        if levels and row.get("jlpt_level") not in levels:
            continue
        if domains and row.get("visual_domain") not in domains:
            continue
        if row.get("image_status") not in {"direct_image", "scene_image"}:
            continue
        selected.append(row)
        if args.limit and len(selected) >= args.limit:
            break

    for idx, row in enumerate(selected, start=1):
        row_id = row["id"]
        existing = rows_by_id.get(row_id)
        if existing and existing.get("local_path") and Path(existing["local_path"]).exists() and not args.overwrite:
            print(f"[{idx}/{len(selected)}] SKIP existing {row['word']} -> {existing['local_path']}")
            continue

        query = build_query(row)
        manifest_row = {
            **{k: row.get(k, "") for k in [
                "id",
                "jlpt_level",
                "word",
                "reading",
                "meaning",
                "visual_domain",
                "image_status",
                "image_query_en",
            ]},
            "search_query": query,
            "source_provider": "Wikimedia Commons",
            "match_status": "not_found",
            "error": "",
        }

        print(f"[{idx}/{len(selected)}] {row['jlpt_level']} {row['word']} -> {query}")
        try:
            pages = wikimedia_search(query, args.search_limit, args.thumb_width)
            candidate = choose_candidate(pages, query)
            if not candidate:
                manifest_row["error"] = "no suitable Wikimedia Commons image found"
                rows_by_id[row_id] = manifest_row
                time.sleep(args.sleep)
                continue

            info = candidate["imageinfo"][0]
            meta = info.get("extmetadata") or {}
            ext = ".jpg"
            mime = str(info.get("mime", "")).lower()
            if mime == "image/png":
                ext = ".png"
            elif mime == "image/webp":
                ext = ".webp"
            filename = f"{row_id}_{sanitize_filename(row['word'])}_{sanitize_filename(query)}{ext}"
            local_path = args.out_dir / "files" / filename
            local_path.parent.mkdir(parents=True, exist_ok=True)
            download_file(info["thumburl"], local_path)

            manifest_row.update(
                {
                    "local_path": str(local_path),
                    "source_page": get_meta(meta, "ImageDescription") or str(info.get("descriptionurl", "")),
                    "thumb_url": str(info.get("thumburl", "")),
                    "file_title": str(candidate.get("title", "")),
                    "mime": mime,
                    "license": get_meta(meta, "LicenseShortName"),
                    "license_url": get_meta(meta, "LicenseUrl"),
                    "artist": strip_html(get_meta(meta, "Artist")),
                    "credit": strip_html(get_meta(meta, "Credit")),
                    "match_status": "matched",
                    "error": "",
                }
            )
            if not manifest_row["source_page"]:
                manifest_row["source_page"] = str(info.get("descriptionurl", ""))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            manifest_row["match_status"] = "error"
            manifest_row["error"] = f"{type(exc).__name__}: {exc}"

        rows_by_id[row_id] = manifest_row
        write_csv(manifest_path, list(rows_by_id.values()))
        time.sleep(args.sleep)

    all_rows = list(rows_by_id.values())
    write_csv(manifest_path, all_rows)
    with (args.out_dir / "wikimedia_image_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(all_rows, fh, ensure_ascii=False, indent=2)

    summary = {
        "manifest": str(manifest_path),
        "total_manifest_rows": len(all_rows),
        "matched": sum(1 for r in all_rows if r.get("match_status") == "matched"),
        "not_found": sum(1 for r in all_rows if r.get("match_status") == "not_found"),
        "errors": sum(1 for r in all_rows if r.get("match_status") == "error"),
    }
    with (args.out_dir / "wikimedia_image_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

