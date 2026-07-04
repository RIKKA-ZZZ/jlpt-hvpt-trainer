from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


SITE = Path(__file__).resolve().parents[1]
SOURCE_DIR = SITE / "assets" / "images"
OUTPUT_DIR = SITE / "assets" / "images-webp"
SUMMARY_PATH = SITE / "data" / "optimized-image-summary.json"

MAX_SIZE = 512
QUALITY = 78


def webp_path_for(source: Path) -> Path:
    return OUTPUT_DIR / f"{source.stem}.webp"


def image_has_alpha(image: Image.Image) -> bool:
    return image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    )


def convert_one(source: Path) -> dict[str, object]:
    output = webp_path_for(source)
    output.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as image:
        image.load()
        original_size = image.size
        image.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
        if image_has_alpha(image):
            converted = image.convert("RGBA")
        else:
            converted = image.convert("RGB")
        converted.save(output, "WEBP", quality=QUALITY, method=6)

    return {
        "source": str(source.relative_to(SITE)).replace("\\", "/"),
        "optimized": str(output.relative_to(SITE)).replace("\\", "/"),
        "originalBytes": source.stat().st_size,
        "optimizedBytes": output.stat().st_size,
        "originalSize": original_size,
        "optimizedSize": Image.open(output).size,
    }


def main() -> None:
    rows = []
    for source in sorted(SOURCE_DIR.glob("*.png")):
        rows.append(convert_one(source))

    original_total = sum(int(row["originalBytes"]) for row in rows)
    optimized_total = sum(int(row["optimizedBytes"]) for row in rows)
    summary = {
        "version": 1,
        "format": "webp",
        "maxSize": MAX_SIZE,
        "quality": QUALITY,
        "count": len(rows),
        "originalBytes": original_total,
        "optimizedBytes": optimized_total,
        "savedBytes": original_total - optimized_total,
        "items": rows,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    saved_percent = 100 * (1 - optimized_total / original_total) if original_total else 0
    print(
        f"Optimized {len(rows)} images: "
        f"{original_total / 1024 / 1024:.1f} MB -> "
        f"{optimized_total / 1024 / 1024:.1f} MB "
        f"({saved_percent:.1f}% smaller)"
    )


if __name__ == "__main__":
    main()
