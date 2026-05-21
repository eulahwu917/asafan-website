#!/usr/bin/env python
"""Integrate the 2026-05-20 photo drop into `assets/product/`.

Layout of `raw_assets/0520/`:
  FOTOS FUNDO BRANCO/   — 64 white-background product photos (PNG/JPG, 4-6 MB)
  fotos de capa_/       — multi-photo carousel shots (A82.png, A122 (2).png)
  dados para site.xlsx  — updated spreadsheet (handled by generate_cards.py)

Pipeline per source image:
  1. Determine target slug (filename → lowercase, RENAME map applied).
  2. Resize to max long-edge 1200px (preserve aspect).
  3. If RGBA/palette-with-transparency: composite onto white.
  4. Save as JPG @ 85% quality, optimized + progressive.

Tela SKU rename (per customer 2026-05-20 xlsx update):
  3006P.jpg → 3012p.jpg   (was M80 — 80×80 cromada arame, rename only)
  3007P.jpg → 3026p.jpg   (was M90 modelo 3007P preto → 3026P cromada;
                           xlsx also changed color from preto to cromada)

Cover-photo convention (`fotos de capa_/`):
  These are full-width marketing banners ("Desempenho que resiste ao frio"
  cold-performance campaign), one per product model. They go in the homepage
  hero carousel, not per-product detail pages. Target filename:
  `assets/hero-carousel/cold-<slug>.jpg`. Any `(N)` suffix in the source is
  stripped (e.g. `A122 (2).png` → `cold-a122.jpg`).
"""
import pathlib
import re
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / 'raw_assets' / '0520'
DST_DIR = ROOT / 'assets' / 'product'
HERO_DIR = ROOT / 'assets' / 'hero-carousel'
MAX_DIM = 1200
HERO_MAX_DIM = 1600
JPG_QUALITY = 85

# Source-stem → target-stem (lowercase). Applied only on FOTOS FUNDO BRANCO files.
RENAME = {
    '3006p': '3012p',
    '3007p': '3026p',
}


def process_image(src_path: pathlib.Path, dst_path: pathlib.Path, max_dim: int = MAX_DIM) -> int:
    """Open, composite-on-white if needed, resize, save as JPG. Returns bytes written."""
    with Image.open(src_path) as img:
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGBA')
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert('RGB')

        w, h = img.size
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        img.save(dst_path, 'JPEG', quality=JPG_QUALITY, optimize=True, progressive=True)
    return dst_path.stat().st_size


def integrate_primary(primary_dir: pathlib.Path, results: list):
    """FOTOS FUNDO BRANCO: each file becomes the primary photo for its SKU."""
    for src in sorted(primary_dir.iterdir()):
        if src.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
            continue
        stem = src.stem.lower()
        target = RENAME.get(stem, stem)
        dst = DST_DIR / f'{target}.jpg'
        size = process_image(src, dst)
        results.append(('primary', src.name, dst.name, size))


def integrate_capa(capa_dir: pathlib.Path, results: list):
    """fotos de capa_: full-bleed cold-performance marketing banners.

    These go into assets/hero-carousel/ as cold-<slug>.jpg (1600px-wide JPG,
    higher resolution than product photos since they're displayed full-width
    on the homepage). The (N) suffix in source filenames is stripped — it was
    photographer's pagination, not a slide ordinal we care about here.
    """
    if not capa_dir.exists():
        return
    HERO_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(capa_dir.iterdir()):
        if src.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
            continue
        stem = src.stem
        m = re.match(r'^(.+?)\s*\(\d+\)\s*$', stem)
        base = (m.group(1) if m else stem).strip().lower()
        dst = HERO_DIR / f'cold-{base}.jpg'
        size = process_image(src, dst, max_dim=HERO_MAX_DIM)
        results.append(('capa', src.name, dst.name, size))


def main():
    if not SRC_DIR.exists():
        sys.exit(f'source dir not found: {SRC_DIR}')
    DST_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    integrate_primary(SRC_DIR / 'FOTOS FUNDO BRANCO', results)
    integrate_capa(SRC_DIR / 'fotos de capa_', results)

    total_bytes = sum(r[3] for r in results)
    n_primary = sum(1 for r in results if r[0] == 'primary')
    n_capa = sum(1 for r in results if r[0] == 'capa')

    for kind, srcname, dstname, size in results:
        marker = '[capa]' if kind == 'capa' else '      '
        print(f'  {marker} {srcname:32} -> {dstname:16} ({size // 1024} KB)')

    print()
    print(f'{n_primary} primary + {n_capa} capa photos integrated')
    print(f'Total payload: {total_bytes / 1024 / 1024:.1f} MB '
          f'({total_bytes // 1024 // len(results)} KB avg)')


if __name__ == '__main__':
    main()
