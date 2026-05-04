#!/usr/bin/env python
"""One-off audit: map every file in raw_assets/product_site_update/ to a SKU código.

Reads dados para site.xlsx to build código <-> modelo <-> tipo lookup, then walks
the new photo drop and reports:
  - mapped files (which códigos each file covers)
  - unmapped files (need user help)
  - códigos with NO photo from this drop (still placeholder)
"""
import openpyxl
import pathlib
import re
import sys
from collections import defaultdict

XLSX = pathlib.Path('raw_assets/product_site/dados para site.xlsx')
DROP = pathlib.Path('raw_assets/product_site_update')
SKIP_SUBDIRS = {'FOTOS ATUAIS_'}  # already imported in earlier session


def norm(s):
    return str(s).strip() if s else ''


def load_skus():
    """Return list of dicts: codigo, modelo, tipo, dim, voltagem."""
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb['Planilha1']
    rows = [tuple(norm(c) for c in row[:9]) for row in ws.iter_rows(values_only=True)]

    skus = []
    sections = [
        ('micro-ac', range(1, 11)),
        ('micro-dc', range(11, 41)),
        ('axial', range(43, 64)),
        ('tela', range(67, 74)),
        ('grelha', range(76, 79)),
        ('porta-filtro', range(81, 84)),
        ('termostato', range(86, 89)),
    ]
    for tipo, idx_range in sections:
        for i in idx_range:
            if i >= len(rows):
                continue
            r = rows[i]
            codigo = r[1]
            modelo = r[2]
            if not codigo:
                continue
            skus.append({
                'codigo': codigo,
                'modelo': modelo,
                'tipo': tipo,
                'extra': r[3],  # voltagem (most rows) or cor (acessórios)
                'dim': r[4],
            })
    return skus


def tokenize(filename):
    """Split filename into uppercase tokens for matching.
    Strips extension, normalizes separators, drops the trailing 'ASA AC' / 'ASA DC' /
    'SOPRADOR' / 'EXAUSTOR' / 'sem masc' / 'com masc' boilerplate.
    """
    stem = pathlib.Path(filename).stem.upper()
    # Replace common separators with spaces
    stem = re.sub(r'[,_\-/]+', ' ', stem)
    # Collapse spaces
    tokens = [t for t in stem.split() if t]
    # Filter out obvious noise tokens (dimensions, boilerplate, parenthetical counters)
    BOILERPLATE = {'ASA', 'AC', 'DC', 'SOPRADOR', 'EXAUSTOR', 'COM', 'SEM', 'MASC',
                   '(2)', '(3)'}
    DIM_RE = re.compile(r'^\d+X\d+(X\d+)?$')  # 120x120x25 etc.
    DIM_SHORT = re.compile(r'^\d+X\d+$')
    out = []
    for t in tokens:
        if t in BOILERPLATE:
            continue
        if DIM_RE.match(t):
            continue
        if DIM_SHORT.match(t):
            continue
        if t.startswith('(') and t.endswith(')'):
            continue
        out.append(t)
    return out


def main():
    skus = load_skus()
    by_codigo = {s['codigo'].upper(): s for s in skus}
    by_modelo = defaultdict(list)
    for s in skus:
        m = s['modelo'].upper()
        if m:
            by_modelo[m].append(s)

    files = []
    for sub in DROP.iterdir():
        if not sub.is_dir():
            continue
        if sub.name in SKIP_SUBDIRS:
            continue
        for f in sub.iterdir():
            if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                files.append(f)

    matched = []  # (file, [codigos])
    unmatched = []
    photo_for_codigo = defaultdict(list)  # codigo -> [files]

    for f in sorted(files):
        tokens = tokenize(f.name)
        hit_codigos = set()
        hit_modelos = set()
        for t in tokens:
            if t in by_codigo:
                hit_codigos.add(t)
            elif t in by_modelo:
                hit_modelos.add(t)

        # Modelos can resolve to multiple códigos (e.g. modelo 3000A = X301 + X302)
        for m in hit_modelos:
            for s in by_modelo[m]:
                hit_codigos.add(s['codigo'].upper())

        if hit_codigos:
            matched.append((f, sorted(hit_codigos), sorted(hit_modelos)))
            for c in hit_codigos:
                photo_for_codigo[c].append(f)
        else:
            unmatched.append((f, tokens))

    # Report
    print('=' * 70)
    print(f'PHOTO DROP AUDIT — {DROP}')
    print('=' * 70)
    print(f'\nTotal SKUs in xlsx: {len(skus)}')
    print(f'Files in drop (excl. FOTOS ATUAIS_): {len(files)}')
    print(f'Mapped files:    {len(matched)}')
    print(f'Unmapped files:  {len(unmatched)}')
    print(f'Códigos with photo from this drop: {len(photo_for_codigo)} / {len(skus)}')

    # Currently-placeholder códigos (those with NO file in assets/product/)
    existing = pathlib.Path('assets/product')
    existing_slugs = {f.stem.lower() for f in existing.iterdir() if f.is_file()}
    def slug(c):
        return c.lower().replace('/', '-').replace(' ', '')
    placeholder_codigos = [s for s in skus if slug(s['codigo']) not in existing_slugs]
    placeholder_set = {s['codigo'].upper() for s in placeholder_codigos}

    print(f'\nCurrently-placeholder códigos (no file in assets/product/): {len(placeholder_codigos)}')

    print('\n' + '-' * 70)
    print('MAPPED FILES (per file -> códigos covered)')
    print('-' * 70)
    for f, codes, modelos in matched:
        rel = f.relative_to(DROP)
        # Mark which codes are currently placeholder
        marked = []
        for c in codes:
            if c in placeholder_set:
                marked.append(c + ' *')
            else:
                marked.append(c)
        modelo_str = f' (modelos: {", ".join(modelos)})' if modelos else ''
        print(f'  {rel}')
        print(f'    -> {", ".join(marked)}{modelo_str}')

    print('\n* = currently using placeholder (filling this is a net gain)\n')

    print('-' * 70)
    print('UNMAPPED FILES (need user help)')
    print('-' * 70)
    if not unmatched:
        print('  (none — every file maps to at least one código)')
    for f, tokens in unmatched:
        rel = f.relative_to(DROP)
        print(f'  {rel}')
        print(f'    tokens after stripping: {tokens}')

    print('\n' + '-' * 70)
    print('CÓDIGOS WITHOUT A PHOTO IN THIS DROP')
    print('-' * 70)
    no_photo_drop = [s for s in skus if s['codigo'].upper() not in photo_for_codigo]
    for s in no_photo_drop:
        in_assets = slug(s['codigo']) in existing_slugs
        marker = '(has existing photo)' if in_assets else '(STILL PLACEHOLDER)'
        print(f'  {s["codigo"]:8s} {s["tipo"]:14s} modelo={s["modelo"]:10s} {marker}')

    print('\n' + '=' * 70)
    print('SUMMARY')
    print('=' * 70)
    still_placeholder = [s for s in no_photo_drop
                         if slug(s['codigo']) not in existing_slugs]
    print(f'After integrating this drop, {len(still_placeholder)} códigos would remain placeholder:')
    for s in still_placeholder:
        print(f'  - {s["codigo"]} ({s["tipo"]}, modelo={s["modelo"]})')


if __name__ == '__main__':
    main()
