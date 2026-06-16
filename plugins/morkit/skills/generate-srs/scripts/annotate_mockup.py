"""Draw numbered circles onto a UI mockup image.

Input items JSON (from Claude vision analysis):
    [
      {"number": 1, "label": "Email", "kind": "input",
       "bbox": [x_pct, y_pct, w_pct, h_pct]},
      ...
    ]

Output: annotated PNG saved next to original (or to --output).

CLI:
    annotate-mockup.py --image input.png --items items.json --output annotated.png
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Color per item kind (RGB).
COLORS: dict[str, tuple[int, int, int]] = {
    "input": (52, 152, 219),     # blue
    "button": (230, 126, 34),    # orange
    "label": (149, 165, 166),    # gray
    "output": (149, 165, 166),
    "table": (39, 174, 96),      # green
    "chart": (39, 174, 96),
    "link": (155, 89, 182),      # purple
}
DEFAULT_COLOR = (52, 73, 94)
CIRCLE_RADIUS = 18
FONT_SIZE = 20
MAX_DIMENSION = 2400  # Downscale very large images first
ALPHA = 220


@dataclass
class AnnotateItem:
    number: int
    kind: str
    bbox: tuple[float, float, float, float]  # x_pct, y_pct, w_pct, h_pct


def _load_items(path: str | Path) -> list[AnnotateItem]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items_data = raw if isinstance(raw, list) else raw.get("items", [])
    out: list[AnnotateItem] = []
    for entry in items_data:
        bbox = entry.get("bbox", [0.0, 0.0, 0.0, 0.0])
        out.append(
            AnnotateItem(
                number=int(entry["number"]),
                kind=str(entry.get("kind", "label")),
                bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            )
        )
    return out


def _load_font(size: int) -> ImageFont.ImageFont:
    """Try common sans-serif fonts, fall back to PIL default."""
    candidates = [
        "Arial.ttf",
        "Helvetica.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _resize_if_needed(img: Image.Image) -> Image.Image:
    """Downscale to MAX_DIMENSION on the longer side (keep aspect)."""
    max_side = max(img.size)
    if max_side <= MAX_DIMENSION:
        return img
    scale = MAX_DIMENSION / max_side
    new_size = (int(img.width * scale), int(img.height * scale))
    return img.resize(new_size, Image.LANCZOS)


def _ensure_white_bg(img: Image.Image) -> Image.Image:
    """Composite RGBA on white so transparent areas are visible."""
    if img.mode != "RGBA":
        return img.convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, img)


def annotate(image_path: str | Path, items: list[AnnotateItem], output_path: str | Path) -> None:
    """Draw numbered circles onto image_path → save to output_path."""
    img = Image.open(str(image_path))
    img = _ensure_white_bg(img)
    img = _resize_if_needed(img)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font(FONT_SIZE)

    drawn_centers: list[tuple[int, int]] = []
    for item in items:
        x_pct, y_pct, _, _ = item.bbox
        x_pct = max(0.0, min(1.0, x_pct))
        y_pct = max(0.0, min(1.0, y_pct))
        cx = int(x_pct * img.width) + CIRCLE_RADIUS
        cy = int(y_pct * img.height) + CIRCLE_RADIUS

        # Avoid overlap: shift right if too close to a previous circle
        for prev_x, prev_y in drawn_centers:
            if abs(cx - prev_x) < 2 * CIRCLE_RADIUS and abs(cy - prev_y) < 2 * CIRCLE_RADIUS:
                cx += 2 * CIRCLE_RADIUS + 4
        drawn_centers.append((cx, cy))

        color = COLORS.get(item.kind, DEFAULT_COLOR) + (ALPHA,)
        draw.ellipse(
            [cx - CIRCLE_RADIUS, cy - CIRCLE_RADIUS, cx + CIRCLE_RADIUS, cy + CIRCLE_RADIUS],
            fill=color,
            outline=(255, 255, 255, 255),
            width=2,
        )

        text = str(item.number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (cx - text_w / 2, cy - text_h / 2 - 1),
            text,
            fill=(255, 255, 255, 255),
            font=font,
        )

    annotated = Image.alpha_composite(img, overlay)
    annotated.convert("RGB").save(str(output_path), "PNG", optimize=True)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--image", required=True)
    p.add_argument("--items", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    items = _load_items(args.items)
    annotate(args.image, items, args.output)
    print(f"Annotated {len(items)} items -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
