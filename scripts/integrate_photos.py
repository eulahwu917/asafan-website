#!/usr/bin/env python
"""Integrate raw_assets/product_site_update/ photos into assets/product/.

Folder routing (per user direction):
  - AC/DC códigos (A*, E*, D*)   → source from FOTOS ATUAIS_/<código>.<ext>
                                    (solo individual photos; AC/ and DC/ subfolders are
                                    redundant group shots and are ignored)
  - Axiais (X*)                   → source from AXIAIS/ (group shots, token-matched)
  - Acessórios (M*, G*, P*, T*)   → source from ACESSÓRIOS/ (token-matched)

Files that don't reference any código in the xlsx are ignored.

For group shots covering multiple códigos, the same source image is copied to
each código's destination filename.

Selection priority when multiple files cover the same código:
  1. Solo files (códigos count == 1) beat group shots
  2. Files without "(2)" beat files with "(2)" (primary angle)
  3. Files where the código is the FIRST listed beat later positions
  4. Tie → alphabetical filename

Run:
  python scripts/integrate_photos.py --dry-run     # preview only
  python scripts/integrate_photos.py               # actually copy
"""
import argparse
import openpyxl
import pathlib
import re
import shutil
import sys

XLSX = pathlib.Path('raw_assets/product_site/dados para site.xlsx')
DROP = pathlib.Path('raw_assets/product_site_update')
ASSETS = pathlib.Path('assets/product')


def norm(s):
    return str(s).strip() if s else ''


def slug(code):
    return code.lower().replace('/', '-').replace(' ', '')


def load_codigos():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb['Planilha1']
    codigos = []
    for row in ws.iter_rows(values_only=True):
        cells = [norm(c) for c in row[:9]]
        codigo = cells[1]
        modelo = cells[2]
        if not codigo or codigo in ('CÓDIGO', 'CÓD'):
            continue
        codigos.append({'codigo': codigo, 'modelo': modelo})
    return codigos


def tokenize_filename(name):
    """Return list of tokens from filename in original order.
    Handles D91/2 vs D91_2: emits both 'D91/2' and 'D91' so either matches.
    """
    stem = pathlib.Path(name).stem.upper()
    # Special handling: 'D91_2' is the filename form of código 'D91/2'.
    # Convert that exact pattern back so it matches the código.
    stem = re.sub(r'(D\d+)_(\d)', r'\1/\2', stem)
    # Now split on common separators (but preserve the slash inside D91/2)
    parts = re.split(r'[,_\-\s]+', stem)
    # Filter dimensions and boilerplate
    BOILERPLATE = {'ASA', 'AC', 'DC', 'SOPRADOR', 'EXAUSTOR', 'COM', 'SEM', 'MASC'}
    DIM_RE = re.compile(r'^\d+X\d+(X\d+)?$')
    out = []
    for p in parts:
        if not p:
            continue
        if p in BOILERPLATE:
            continue
        if DIM_RE.match(p):
            continue
        if p.startswith('(') and p.endswith(')'):
            continue
        out.append(p)
    return out


def is_secondary_angle(name):
    """True if filename has '(2)' or '(3)' marker — secondary angle photo."""
    return bool(re.search(r'\(\d+\)', name))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='print plan, do not copy')
    args = ap.parse_args()

    codigos = load_codigos()
    codigo_set = {c['codigo'].upper() for c in codigos}

    fotos_atuais = DROP / 'FOTOS ATUAIS_'
    axiais_dir = DROP / 'AXIAIS'
    acessorios_dir = None
    for d in DROP.iterdir():
        if d.is_dir() and d.name.upper().startswith('ACESS'):
            acessorios_dir = d
            break

    # Build plan: codigo -> source file
    plan = {}
    ignored_files = []

    # 1) AC/DC: prefer FOTOS ATUAIS_ solo photo
    for c in codigos:
        cd = c['codigo'].upper()
        if cd[0] in ('A', 'E', 'D'):
            for ext in ('.jpg', '.jpeg', '.png'):
                # FOTOS ATUAIS_ uses the original-case códigos; D91/2 is on disk as 'D91-2'
                disk_name = c['codigo'].replace('/', '-')
                cand = fotos_atuais / (disk_name + ext)
                if cand.exists():
                    plan[c['codigo']] = cand
                    break

    # 2) Axiais: token-match in AXIAIS/ folder
    if axiais_dir.exists():
        candidates = {c['codigo']: [] for c in codigos if c['codigo'].upper().startswith('X')}
        for f in sorted(axiais_dir.iterdir()):
            if not f.is_file() or f.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
                continue
            tokens = tokenize_filename(f.name)
            matched = [(i, t) for i, t in enumerate(tokens) if t in codigo_set]
            if not matched:
                ignored_files.append(f)
                continue
            n_codes = len(set(t for _, t in matched))
            secondary = is_secondary_angle(f.name)
            for position, t in matched:
                priority = (n_codes, 1 if secondary else 0, position, f.name)
                for c in codigos:
                    if c['codigo'].upper() == t:
                        candidates[c['codigo']].append((priority, f))
                        break
        for cd, lst in candidates.items():
            if lst:
                lst.sort(key=lambda x: x[0])
                plan[cd] = lst[0][1]

    # 3) Acessórios: token-match in ACESSÓRIOS/ folder
    if acessorios_dir and acessorios_dir.exists():
        prefixes = ('M', 'G', 'P', 'T')
        candidates = {c['codigo']: [] for c in codigos
                      if c['codigo'].upper().startswith(prefixes)}
        for f in sorted(acessorios_dir.iterdir()):
            if not f.is_file() or f.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
                continue
            tokens = tokenize_filename(f.name)
            matched = [(i, t) for i, t in enumerate(tokens) if t in codigo_set]
            if not matched:
                ignored_files.append(f)
                continue
            n_codes = len(set(t for _, t in matched))
            secondary = is_secondary_angle(f.name)
            for position, t in matched:
                priority = (n_codes, 1 if secondary else 0, position, f.name)
                for c in codigos:
                    if c['codigo'].upper() == t:
                        candidates[c['codigo']].append((priority, f))
                        break
        for cd, lst in candidates.items():
            if lst:
                lst.sort(key=lambda x: x[0])
                plan[cd] = lst[0][1]

    # 4) AC/ and DC/ subfolders: report as ignored (per user direction, FOTOS ATUAIS_
    #    is the canonical source for AC/DC)
    for sub_name in ('AC', 'DC'):
        sub = DROP / sub_name
        if sub.exists():
            for f in sorted(sub.iterdir()):
                if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                    ignored_files.append(f)

    # 5) FOTOS ATUAIS_ files for non-existent códigos (e.g. A172) → ignored
    if fotos_atuais.exists():
        used = {p.resolve() for p in plan.values()}
        for f in sorted(fotos_atuais.iterdir()):
            if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                if f.resolve() not in used:
                    ignored_files.append(f)

    # Total file count (recursive, excluding xlsx)
    total = sum(1 for sub in DROP.iterdir() if sub.is_dir()
                for f in sub.iterdir()
                if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'))

    # Report
    print(f'Drop has {total} image files; {len(ignored_files)} ignored.')
    print(f'Códigos in xlsx: {len(codigos)}')
    print(f'Códigos that will get a NEW photo from this drop: {len(plan)}\n')

    print('=' * 90)
    print('PLAN -- codigo -> source file -> destination')
    print('=' * 90)
    for c in codigos:
        cd = c['codigo']
        if cd in plan:
            src = plan[cd]
            dest = ASSETS / (slug(cd) + src.suffix.lower())
            existing = ''
            for ext in ('.jpg', '.jpeg', '.png'):
                e = ASSETS / (slug(cd) + ext)
                if e.exists():
                    existing = f' (replaces {e.name})'
                    break
            rel_src = src.relative_to(DROP)
            print(f'  {cd:8s} -> {rel_src} -> {dest.name}{existing}')
        else:
            existing_kept = False
            for ext in ('.jpg', '.jpeg', '.png'):
                e = ASSETS / (slug(cd) + ext)
                if e.exists():
                    existing_kept = True
                    print(f'  {cd:8s}   (no new photo; keeping existing {e.name})')
                    break
            if not existing_kept:
                print(f'  {cd:8s}   (no photo — placeholder)')

    print('\n' + '=' * 90)
    print('IGNORED FILES (no matching código)')
    print('=' * 90)
    for f in ignored_files:
        print(f'  {f.relative_to(DROP)}')

    if args.dry_run:
        print('\n(dry-run; no files copied)')
        return

    # Execute
    print('\nCopying...')
    copied = 0
    cleaned = 0
    for cd, src in plan.items():
        s = slug(cd)
        # Remove existing files for this slug with any extension to avoid
        # generate_cards.py picking up the wrong one
        for ext in ('.jpg', '.jpeg', '.png'):
            e = ASSETS / (s + ext)
            if e.exists() and e.suffix.lower() != src.suffix.lower():
                e.unlink()
                cleaned += 1
        dest = ASSETS / (s + src.suffix.lower())
        shutil.copy2(src, dest)
        copied += 1

    print(f'Copied {copied} files; cleaned up {cleaned} stale variants.')


if __name__ == '__main__':
    main()
