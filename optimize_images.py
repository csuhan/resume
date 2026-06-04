#!/usr/bin/env python3
"""One-off image optimizer for the personal homepage.

- Paper thumbnails: max 480x270 (displayed at 240x135)
- Avatar photo: max 220x220 (displayed at 110x110)
- Timeline logos: max 100x100 (displayed at 50x50)

For every source image we emit:
  * a re-encoded version in its original format (smaller fallback)
  * a WebP version at high quality

Run with: python3 optimize_images.py
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
IMG = ROOT / "img"

PAPER_MAX = (480, 270)
LOGO_MAX = (100, 100)
AVATAR_MAX = (220, 220)

WEBP_QUALITY = 80
JPG_QUALITY = 82
PNG_OPT = True

# (source_relative_path, max_size, also_make_webp)
TARGETS: list[tuple[str, tuple[int, int], bool]] = [
    # Remaining items (paper thumbnails + avatar already processed on first run)
    ("shlab_logo.png", LOGO_MAX, True),
    ("youtu_logo.png", LOGO_MAX, True),
    ("cuhk_logo.jpg", LOGO_MAX, True),
    ("whu_logo.png", LOGO_MAX, True),
]


def fit(im: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    im = im.copy()
    im.thumbnail(max_size, Image.LANCZOS)
    return im


def save_original_format(im: Image.Image, dest: Path) -> None:
    suffix = dest.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(dest, "JPEG", quality=JPG_QUALITY, optimize=True, progressive=True)
    elif suffix == ".png":
        if im.mode == "RGBA":
            quant = im.quantize(colors=256, method=Image.FASTOCTREE)
        else:
            quant = im.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT)
        quant.save(dest, "PNG", optimize=PNG_OPT)
    elif suffix == ".webp":
        im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)
    else:
        raise ValueError(f"Unsupported format: {dest}")


def save_webp(im: Image.Image, dest: Path) -> None:
    im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)


def process(rel: str, max_size: tuple[int, int], make_webp: bool) -> None:
    src = IMG / rel
    if not src.exists():
        print(f"!! missing: {src}")
        return
    before = src.stat().st_size
    with Image.open(src) as im:
        im.load()
        small = fit(im, max_size)
        save_original_format(small, src)
    after = src.stat().st_size
    print(f"{rel}: {before/1024:.1f}KB -> {after/1024:.1f}KB ({small.size[0]}x{small.size[1]})")

    if make_webp and src.suffix.lower() != ".webp":
        webp_path = src.with_suffix(".webp")
        before_w = webp_path.stat().st_size if webp_path.exists() else 0
        # Reopen the freshly-saved file to ensure consistent color profiles.
        with Image.open(src) as im2:
            im2.load()
            small2 = fit(im2, max_size)
            save_webp(small2, webp_path)
        after_w = webp_path.stat().st_size
        print(f"   -> {webp_path.relative_to(IMG)}: {before_w/1024:.1f}KB -> {after_w/1024:.1f}KB")


def main() -> None:
    for rel, max_size, make_webp in TARGETS:
        process(rel, max_size, make_webp)


if __name__ == "__main__":
    main()
