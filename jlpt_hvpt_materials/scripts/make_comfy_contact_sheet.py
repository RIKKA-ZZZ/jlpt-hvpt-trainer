from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "images" / "comfy_generated" / "comfy_image_manifest.csv"
DEFAULT_OUT = ROOT / "images" / "comfy_generated" / "comfy_contact_sheet.jpg"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [
        Path(r"C:\Windows\Fonts\meiryo.ttc"),
        Path(r"C:\Windows\Fonts\YuGothM.ttc"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a review contact sheet for generated ComfyUI images.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--cols", type=int, default=5)
    parser.add_argument("--thumb-width", type=int, default=180)
    parser.add_argument("--thumb-height", type=int, default=150)
    args = parser.parse_args()

    rows = [
        row
        for row in read_csv(args.manifest)
        if row.get("status") == "done" and row.get("local_path") and Path(row["local_path"]).exists()
    ][: args.limit]
    if not rows:
        raise SystemExit(f"No generated images found in {args.manifest}")

    label_h = 58
    rows_n = (len(rows) + args.cols - 1) // args.cols
    sheet = Image.new(
        "RGB",
        (args.cols * args.thumb_width, rows_n * (args.thumb_height + label_h)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    font = load_font(14)
    small = load_font(11)

    for i, row in enumerate(rows):
        x = (i % args.cols) * args.thumb_width
        y = (i // args.cols) * (args.thumb_height + label_h)
        try:
            image = Image.open(row["local_path"]).convert("RGB")
            image.thumbnail((args.thumb_width, args.thumb_height), Image.LANCZOS)
            px = x + (args.thumb_width - image.width) // 2
            py = y + (args.thumb_height - image.height) // 2
            sheet.paste(image, (px, py))
        except Exception:
            pass

        draw.rectangle(
            [x, y + args.thumb_height, x + args.thumb_width - 1, y + args.thumb_height + label_h - 1],
            outline=(220, 220, 220),
            fill=(248, 248, 248),
        )
        title = f"{row.get('word', '')}  {row.get('meaning', '')}"
        seed = f"{row.get('jlpt_level', '')}  seed {row.get('seed', '')}"
        draw.text((x + 6, y + args.thumb_height + 5), title[:24], fill=(20, 20, 20), font=font)
        draw.text((x + 6, y + args.thumb_height + 31), seed[:30], fill=(90, 90, 90), font=small)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out, quality=90)
    print(args.out)


if __name__ == "__main__":
    main()

