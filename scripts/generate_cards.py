#!/usr/bin/env python
"""Generate product card HTML for produtos.html from dados para site.xlsx.

Output: scripts/_generated_cards.html  (paste between <div class="catalog__grid"> and </div>)

Card data attributes (for filter JS):
  data-tipo:      micro-ac | micro-dc | axial | acessorio
  data-subtipo:   (acessorio only) tela | grelha | porta-filtro | termostato
  data-tensao:    bivolt | 12v | 24v | 48v | 220v | 220v-380v | (none)
  data-mancal:    (micro only) rolamento | bucha
  data-funcao:    (axial only) soprador | exaustor
"""
import openpyxl
import pathlib
import html
import sys

XLSX = 'raw_assets/product_site/dados para site.xlsx'
ASSETS = pathlib.Path('assets/product')
WA_HREF = 'https://wa.me/551134065088?text=Ol%C3%A1!%20Gostaria%20de%20solicitar%20uma%20cota%C3%A7%C3%A3o.'


def norm(s):
    return str(s).strip() if s else ''


def slug(code):
    """URL-safe slug from código (e.g. 'D91/2' -> 'd91-2')."""
    return code.lower().replace('/', '-').replace(' ', '')


def find_image(code):
    s = slug(code)
    for ext in ('.jpg', '.png', '.jpeg'):
        f = ASSETS / (s + ext)
        if f.exists():
            return f'assets/product/{s}{ext}'
    return 'assets/product/placeholder.png'


CAP_MAP = {
    'ALUMINIO': 'Alumínio',
    'NYLON': 'Nylon',
    'ABS': 'ABS',
    'PLASTICO': 'Plástico',
    'ARAME': 'Arame',
    'ROLAMENTO': 'Rolamento',
    'BUCHA': 'Bucha',
    'CROMADA': 'Cromada',
    'BEGE': 'Bege',
    'PRETO': 'Preto',
    'SOPRADOR': 'Soprador',
    'EXAUSTOR': 'Exaustor',
}


def cap(word):
    if not word:
        return ''
    key = word.upper().strip()
    return CAP_MAP.get(key, word.capitalize())


def tensao_slug(voltagem):
    v = voltagem.upper().replace(' ', '')
    if v in ('110V/220', '110V/220V'):
        return 'bivolt'
    if v == '12V':
        return '12v'
    if v == '24V':
        return '24v'
    if v == '48V':
        return '48v'
    if v == '220V':
        return '220v'
    if v in ('220V/380V',):
        return '220v-380v'
    return ''


IMG_STYLE_OVERRIDES = {
    # Per-código <img> style. Use when object-fit: cover crops badly on a specific photo.
    'E171': 'object-position: center 75%;',  # portrait shot — keep fan body visible
}


def card(data_attrs, img_src, sku, title, specs, alt=None):
    attrs = ' '.join(f'{k}="{v}"' for k, v in data_attrs.items() if v)
    alt = alt or f'Produto {sku}'
    style_attr = ''
    override = IMG_STYLE_OVERRIDES.get(sku)
    if override:
        style_attr = f' style="{override}"'
    return f'''        <article class="product-card" {attrs}>
          <div class="product-card__img"><img src="{img_src}" alt="{html.escape(alt)}" loading="lazy"{style_attr}></div>
          <div class="product-card__body">
            <p class="product-card__sku">{html.escape(sku)}</p>
            <h3 class="product-card__title">{html.escape(title)}</h3>
            <p class="product-card__specs">{html.escape(specs)}</p>
            <div class="product-card__actions">
              <a href="fale-conosco.html" class="product-card__btn product-card__btn--outline">Especificações</a>
              <a href="{WA_HREF}" target="_blank" rel="noopener noreferrer" class="product-card__btn product-card__btn--red">Cotação</a>
            </div>
          </div>
        </article>'''


def main():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb['Planilha1']
    rows = [tuple(norm(c) for c in row[:9]) for row in ws.iter_rows(values_only=True)]

    cards = []

    # Section 1 — Microventiladores AC (rows 2-11, indices 1-10)
    # header row: FOTOS | CÓDIGO | MODELO | VOLTAGEM | DIMENSÃO | MANCAL | VIDA ÚTIL | DISPOSITIVO | CARCAÇA
    for r in rows[1:11]:
        _, codigo, modelo, voltagem, dimensao, mancal, vida, fios, carcaca = r
        if not codigo:
            continue
        tipo = 'micro-ac'
        tensao = tensao_slug(voltagem)
        mancal_slug = mancal.lower() if mancal else ''
        dim_display = dimensao.replace('X', '×') + 'mm'
        title = f'Microventilador AC {dim_display}'
        specs = f'{modelo} · Bivolt · {cap(mancal)} · {fios.lower().strip()} · {cap(carcaca)}'
        cards.append(card(
            {'data-tipo': tipo, 'data-tensao': tensao, 'data-mancal': mancal_slug},
            find_image(codigo), codigo, title, specs
        ))

    # Section 2 — Microventiladores DC (rows 12-41, indices 11-40)
    for r in rows[11:41]:
        _, codigo, modelo, voltagem, dimensao, mancal, vida, fios, carcaca = r
        if not codigo:
            continue
        tipo = 'micro-dc'
        tensao = tensao_slug(voltagem)
        mancal_slug = mancal.lower() if mancal else ''
        dim_display = dimensao.replace('X', '×') + 'mm'
        title = f'Microventilador DC {dim_display}'
        specs = f'{modelo} · {voltagem} · {cap(mancal)} · {fios.lower().strip()} · {cap(carcaca)}'
        cards.append(card(
            {'data-tipo': tipo, 'data-tensao': tensao, 'data-mancal': mancal_slug},
            find_image(codigo), codigo, title, specs
        ))

    # Section 3 — Axiais (rows 44-64, indices 43-63)
    # header: CÓD | MODELO | VOLT. | DIMENSÃO | FUNÇÃO
    for r in rows[43:64]:
        _, codigo, modelo, voltagem, dimensao, funcao, *_rest = r
        if not codigo:
            continue
        tipo = 'axial'
        tensao = tensao_slug(voltagem)
        funcao_slug = funcao.lower() if funcao else ''
        dim_display = dimensao  # already has 'mm' in data like '200mm'
        title_prefix = 'Soprador' if funcao_slug == 'soprador' else 'Exaustor'
        title = f'{title_prefix} Axial {dim_display}'
        specs = f'{modelo} · {voltagem}'
        cards.append(card(
            {'data-tipo': tipo, 'data-tensao': tensao, 'data-funcao': funcao_slug},
            find_image(codigo), codigo, title, specs
        ))

    # Section 4 — Telas (rows 68-74, indices 67-73)
    # header: CÓD | MODELO | COR | TAMANHO | MATERIAL
    for r in rows[67:74]:
        _, codigo, modelo, cor, tamanho, material, *_rest = r
        if not codigo:
            continue
        dim_display = tamanho.replace('X', '×').replace('x', '×') + 'mm'
        title = f'Tela Metálica {dim_display}'
        specs = f'{cap(material)} · {cap(cor)}'
        cards.append(card(
            {'data-tipo': 'acessorio', 'data-subtipo': 'tela'},
            find_image(codigo), codigo, title, specs
        ))

    # Section 5 — Grelhas (rows 77-79, indices 76-78)
    for r in rows[76:79]:
        _, codigo, modelo, cor, tamanho, material, *_rest = r
        if not codigo:
            continue
        dim_display = tamanho.replace('X', '×').replace('x', '×') + 'mm'
        title = f'Grelha ABS {dim_display}'
        specs = f'{cap(material)} · {cap(cor)}'
        cards.append(card(
            {'data-tipo': 'acessorio', 'data-subtipo': 'grelha'},
            find_image(codigo), codigo, title, specs
        ))

    # Section 6 — Porta-filtros (rows 82-84, indices 81-83)
    for r in rows[81:84]:
        _, codigo, modelo, cor, tamanho, material, *_rest = r
        if not codigo:
            continue
        dim_display = tamanho.replace('X', '×').replace('x', '×') + 'mm'
        title = f'Porta-filtro {dim_display}'
        specs = f'{cap(material)} · {cap(cor)}'
        cards.append(card(
            {'data-tipo': 'acessorio', 'data-subtipo': 'porta-filtro'},
            find_image(codigo), codigo, title, specs
        ))

    # Section 7 — Termostatos (rows 87-89, indices 86-88)
    # header: CÓD | MODELO | VOLT. | TAMANHO | AMPERAGEM
    for r in rows[86:89]:
        _, codigo, modelo, voltagem, tamanho, amperagem, *_rest = r
        if not codigo:
            continue
        tensao = tensao_slug(voltagem)
        dim_display = tamanho.replace('X', '×').replace('x', '×') + 'mm'
        title = f'Termostato {dim_display}'
        specs = f'{voltagem} · {amperagem}'
        cards.append(card(
            {'data-tipo': 'acessorio', 'data-subtipo': 'termostato', 'data-tensao': tensao},
            find_image(codigo), codigo, title, specs
        ))

    out = pathlib.Path('scripts/_generated_cards.html')
    out.parent.mkdir(exist_ok=True)
    out.write_text('\n\n'.join(cards) + '\n', encoding='utf-8')
    print(f'Generated {len(cards)} cards -> {out}')

    # Sanity: count missing images
    missing = 0
    for line in (c for c in cards):
        if 'placeholder.png' in line:
            missing += 1
    print(f'Using placeholder for {missing} products')


if __name__ == '__main__':
    main()
