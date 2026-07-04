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
DEFAULT_OUT = ROOT / "images" / "openverse"
API_URL = "https://api.openverse.org/v1/images/"
DEFAULT_LICENSES = "cc0,pdm,by,by-sa"


QUERY_OVERRIDES = {
    "animal": "wild animal photo",
    "dog": "dog photo",
    "cat": "domestic cat photo",
    "fish": "fish photo",
    "bird": "bird photo",
    "stomach": "human belly photo",
    "body": "human body photo",
    "health": "healthy smiling person photo",
    "mouth": "human mouth close up",
    "hand": "human hand close up",
    "tooth": "human tooth close up",
    "eye": "human eye close up",
    "ear": "human ear close up",
    "medicine": "medicine pills photo",
    "foot": "human foot close up",
    "nose": "human nose close up",
    "business shirt": "dress shirt photo",
    "western-style clothes": "clothes photo",
    "green tea": "cup of green tea photo",
    "rice bowl": "rice bowl photo",
    "chicken meat": "chicken meat photo",
    "coffee lounge": "coffee shop interior photo",
    "cooked rice": "bowl of cooked rice photo",
    "midday meal": "lunch meal photo",
    "evening meal": "dinner meal photo",
    "black tea": "cup of black tea photo",
    "weather": "weather sky photo",
    "cloudy weather": "cloudy sky photo",
}


BAD_TITLE_WORDS = {
    "logo",
    "icon",
    "symbol",
    "map",
    "diagram",
    "chart",
    "graph",
    "illustration",
    "poster",
    "sign",
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
        "source",
        "source_page",
        "image_url",
        "thumb_url",
        "file_title",
        "license",
        "license_url",
        "creator",
        "creator_url",
        "attribution",
        "match_status",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def request_json(url: str, timeout: int = 30, retries: int = 3) -> dict:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "JLPT-HVPT-local-image-fetcher/0.1 (personal learning tool)",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    if last_error:
        raise last_error
    raise RuntimeError("request failed")


def download_file(url: str, out_path: Path, timeout: int = 60, retries: int = 3) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "JLPT-HVPT-local-image-fetcher/0.1 (personal learning tool)",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
                out_path.write_bytes(resp.read())
                return content_type
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    if last_error:
        raise last_error
    raise RuntimeError("download failed")


def existing_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {row["id"]: row for row in read_csv(path) if row.get("id")}


def build_query(row: dict[str, str]) -> str:
    base = (row.get("image_query_en") or row.get("meaning") or row.get("word") or "").strip()
    base = base.split("|")[0].split(",")[0].strip()
    normalized = base.lower()
    if normalized in QUERY_OVERRIDES:
        return QUERY_OVERRIDES[normalized]
    domain = row.get("visual_domain", "")
    if domain == "action_state":
        return base
    if domain == "animal":
        return f"{base} photo"
    if domain == "body_health":
        return f"human {base} close up"
    if domain == "clothing":
        return f"{base} clothing photo"
    if domain == "food_drink":
        return f"{base} food photo"
    if domain == "nature_weather":
        return f"{base} photo"
    if domain == "object_tool":
        return f"{base} object photo"
    if domain == "place_building":
        return f"{base} building photo"
    if domain == "transport":
        return f"{base} vehicle photo"
    return f"{base} photo"


def openverse_search(query: str, page_size: int, licenses: str) -> list[dict]:
    params = {
        "q": query,
        "page_size": str(page_size),
        "mature": "false",
        "license": licenses,
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    data = request_json(url)
    return list(data.get("results") or [])


def score_result(result: dict, query: str) -> int:
    title = str(result.get("title") or "").lower()
    tags = " ".join(str(tag.get("name", "")) for tag in result.get("tags") or []).lower()
    text = f"{title} {tags}"
    query_words = set(re.findall(r"[a-z]+", query.lower()))
    result_words = set(re.findall(r"[a-z]+", text))
    score = 0
    if result.get("thumbnail"):
        score += 30
    if result.get("foreign_landing_url"):
        score += 10
    if query_words and query_words & result_words:
        score += 25
    if result.get("license") in {"cc0", "pdm", "by", "by-sa"}:
        score += 15
    width = int(result.get("width") or 0)
    height = int(result.get("height") or 0)
    if width >= 400 and height >= 400:
        score += 10
    if any(bad in title for bad in BAD_TITLE_WORDS):
        score -= 20
    return score


def choose_result(results: list[dict], query: str) -> dict | None:
    usable = [r for r in results if r.get("thumbnail")]
    usable.sort(key=lambda r: score_result(r, query), reverse=True)
    return usable[0] if usable else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Openverse CC images for JLPT imageable vocabulary."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--levels", nargs="*", default=["N5"])
    parser.add_argument("--domains", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--page-size", type=int, default=5)
    parser.add_argument("--licenses", default=DEFAULT_LICENSES)
    parser.add_argument("--sleep", type=float, default=0.8)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "openverse_image_manifest.csv"
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
            "source_provider": "Openverse",
            "match_status": "not_found",
            "error": "",
        }

        print(f"[{idx}/{len(selected)}] {row['jlpt_level']} {row['word']} -> {query}")
        try:
            results = openverse_search(query, args.page_size, args.licenses)
            result = choose_result(results, query)
            if not result:
                manifest_row["error"] = "no suitable Openverse image found"
                rows_by_id[row_id] = manifest_row
                write_csv(manifest_path, list(rows_by_id.values()))
                time.sleep(args.sleep)
                continue

            filename = f"{row_id}_{sanitize_filename(row['word'])}_{sanitize_filename(query)}.jpg"
            local_path = args.out_dir / "files" / filename
            local_path.parent.mkdir(parents=True, exist_ok=True)
            content_type = download_file(result["thumbnail"], local_path)
            if content_type == "image/png":
                new_path = local_path.with_suffix(".png")
                local_path.rename(new_path)
                local_path = new_path
            elif content_type == "image/webp":
                new_path = local_path.with_suffix(".webp")
                local_path.rename(new_path)
                local_path = new_path

            manifest_row.update(
                {
                    "local_path": str(local_path),
                    "source": str(result.get("source", "")),
                    "source_page": str(result.get("foreign_landing_url", "")),
                    "image_url": str(result.get("url", "")),
                    "thumb_url": str(result.get("thumbnail", "")),
                    "file_title": str(result.get("title", "")),
                    "license": str(result.get("license", "")),
                    "license_url": str(result.get("license_url", "")),
                    "creator": str(result.get("creator", "") or ""),
                    "creator_url": str(result.get("creator_url", "") or ""),
                    "attribution": str(result.get("attribution", "") or ""),
                    "match_status": "matched",
                    "error": "",
                }
            )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            manifest_row["match_status"] = "error"
            manifest_row["error"] = f"{type(exc).__name__}: {exc}"

        rows_by_id[row_id] = manifest_row
        write_csv(manifest_path, list(rows_by_id.values()))
        time.sleep(args.sleep)

    all_rows = list(rows_by_id.values())
    write_csv(manifest_path, all_rows)
    with (args.out_dir / "openverse_image_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(all_rows, fh, ensure_ascii=False, indent=2)

    summary = {
        "manifest": str(manifest_path),
        "total_manifest_rows": len(all_rows),
        "matched": sum(1 for r in all_rows if r.get("match_status") == "matched"),
        "not_found": sum(1 for r in all_rows if r.get("match_status") == "not_found"),
        "errors": sum(1 for r in all_rows if r.get("match_status") == "error"),
        "licenses": args.licenses,
    }
    with (args.out_dir / "openverse_image_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
