#!/usr/bin/env python
"""Side-by-side: every file in raw_assets/product_site_update/ vs the xlsx.

For each file, lists every token from the filename and where (if anywhere) it
appears in the xlsx — CÓDIGO column or MODELO column — with the row number so
you can jump straight to it in Excel.
"""
import openpyxl
import pathlib
import re

XLSX = pathlib.Path('raw_assets/product_site/dados para site.xlsx')
DROP = pathlib.Path('raw_assets/product_site_update')


def norm(s):
    return str(s).strip() if s else ''


def load_xlsx_index():
    """Return:
      codigo_index[token_upper] = (excel_row_number, codigo, modelo, section)
      modelo_index[token_upper] = (excel_row_number, codigo, modelo, section)
    Excel row numbers are 1-based to match what the user sees in Excel.
    """
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb['Planilha1']
    codigo_index = {}
    modelo_index = {}
    section = '?'
    SECTION_BY_PREFIX = {
        'A': 'Microventilador AC', 'E': 'Microventilador AC',
        'D': 'Microventilador DC',
        'X': 'Axial',
        'M': 'Tela', 'G': 'Grelha', 'P': 'Porta-filtro', 'T': 'Termostato',
    }
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        cells = [norm(c) for c in row[:9]]
        codigo = cells[1]
        modelo = cells[2]
        if not codigo or codigo in ('CÓDIGO', 'CÓD'):
            continue
        # Determine section from first letter of codigo
        first = codigo[0].upper()
        sec = SECTION_BY_PREFIX.get(first, '?')
        codigo_index[codigo.upper()] = (i, codigo, modelo, sec)
        if modelo:
            modelo_index[modelo.upper()] = (i, codigo, modelo, sec)
    return codigo_index, modelo_index


def tokenize(filename):
    stem = pathlib.Path(filename).stem.upper()
    stem = re.sub(r'[,_\-/]+', ' ', stem)
    tokens = [t for t in stem.split() if t]
    BOILERPLATE = {'ASA', 'AC', 'DC', 'SOPRADOR', 'EXAUSTOR', 'COM', 'SEM', 'MASC'}
    DIM_RE = re.compile(r'^\d+X\d+(X\d+)?$')
    out = []
    for t in tokens:
        if t in BOILERPLATE:
            continue
        if DIM_RE.match(t):
            continue
        if t.startswith('(') and t.endswith(')'):
            continue
        out.append(t)
    return out


def main():
    codigo_index, modelo_index = load_xlsx_index()

    files = []
    for sub in sorted(DROP.iterdir()):
        if not sub.is_dir() or sub.name == 'FOTOS ATUAIS_':
            continue
        for f in sorted(sub.iterdir()):
            if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                files.append(f)

    print()
    print('=' * 110)
    print(f'{"File path":<70} | {"Token":<10} | xlsx match')
    print('=' * 110)

    last_folder = None
    for f in files:
        folder = f.parent.name
        if folder != last_folder:
            print(f'\n--- {folder} ---')
            last_folder = folder
        rel = f.name
        tokens = tokenize(rel)
        if not tokens:
            print(f'{rel:<70} | {"(none)":<10} | NO TOKENS')
            continue
        first_line = True
        for t in tokens:
            if t in codigo_index:
                row, c, m, sec = codigo_index[t]
                match = f'CÓDIGO row {row} ({sec}: {c} / modelo {m})'
            elif t in modelo_index:
                row, c, m, sec = modelo_index[t]
                match = f'MODELO row {row} ({sec}: código {c} / modelo {m})'
            else:
                match = 'NOT IN XLSX'
            label = rel if first_line else ''
            print(f'{label:<70} | {t:<10} | {match}')
            first_line = False


if __name__ == '__main__':
    main()
