#!/usr/bin/env python
"""Build the product catalog from `dados para site.xlsx`.

Two outputs every run:

1. Catalog cards -> `scripts/_generated_cards.html`
   (paste between `<div class="catalog__grid">` and the matching `</div>` in
   produtos.html — or run `--apply` to do that surgery in-place).

2. Per-product detail pages -> `produto/<slug>.html`
   One static page per row, used by the "Especificações" button on each card.
   Picture column is a carousel; auto-detects extra images named
   `<slug>-2.jpg`, `<slug>-3.jpg`, ... for future multi-photo support.

Card data attributes (drive the catalog filter JS):
  data-tipo:      micro-ac | micro-dc | axial | acessorio
  data-subtipo:   (acessorio only) tela | grelha | porta-filtro | termostato
  data-tensao:    bivolt | 12v | 24v | 48v | 220v | 220v-380v
  data-mancal:    (micro only) rolamento | bucha
  data-funcao:    (axial only) soprador | exaustor

Usage:
  python scripts/generate_cards.py            # write outputs only
  python scripts/generate_cards.py --apply    # also patch produtos.html
                                              # and sitemap.xml in-place
"""
import argparse
import html
import json
import pathlib
import re
import sys
import urllib.parse

import openpyxl

XLSX = 'raw_assets/0520/dados para site.xlsx'
ASSETS = pathlib.Path('assets/product')
PRODUTO_DIR = pathlib.Path('produto')
OUT_CARDS = pathlib.Path('scripts/_generated_cards.html')
SITE_BASE = 'https://www.asafan.com.br'
WA_PHONE = '551134065088'
WA_GENERIC_HREF = (
    'https://wa.me/' + WA_PHONE
    + '?text=' + urllib.parse.quote('Olá! Gostaria de solicitar uma cotação.')
)


def norm(s):
    return str(s).strip() if s else ''


def slug(code):
    """URL-safe slug (e.g. 'D91/2' -> 'd91-2')."""
    return code.lower().replace('/', '-').replace(' ', '')


def find_image(code):
    s = slug(code)
    for ext in ('.jpg', '.png', '.jpeg'):
        f = ASSETS / (s + ext)
        if f.exists():
            return f'assets/product/{s}{ext}'
    return 'assets/product/placeholder.png'


def find_extra_images(code):
    """Additional photos named <slug>-2.jpg, <slug>-3.jpg, ... up to 9."""
    s = slug(code)
    extras = []
    for n in range(2, 10):
        for ext in ('.jpg', '.png', '.jpeg'):
            f = ASSETS / f'{s}-{n}{ext}'
            if f.exists():
                extras.append(f'assets/product/{s}-{n}{ext}')
                break
    return extras


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


def voltagem_display(voltagem):
    """Friendly voltage label for spec tables."""
    v = voltagem.strip()
    if v.upper().replace(' ', '') in ('110V/220', '110V/220V'):
        return '110V/220V (Bivolt)'
    return v


# Per-código <img> style overrides on the catalog card, when default crop is bad.
IMG_STYLE_OVERRIDES = {
}


# ---------------------------------------------------------------------------
# Pass 1: walk the xlsx and produce structured records.
# ---------------------------------------------------------------------------

def collect_records(ws):
    rows = [tuple(norm(c) for c in row[:9]) for row in ws.iter_rows(values_only=True)]
    records = []

    # Microventiladores AC — rows 2-11 (indices 1-10)
    for r in rows[1:11]:
        _, codigo, modelo, voltagem, dimensao, mancal, vida, fios, carcaca = r
        if not codigo:
            continue
        dim_display = dimensao.replace('X', '×') + 'mm'
        fios_display = fios.lower().strip()
        records.append({
            'codigo': codigo,
            'modelo': modelo,
            'tipo_slug': 'micro-ac',
            'tensao_slug': tensao_slug(voltagem),
            'mancal_slug': mancal.lower() if mancal else '',
            'subtipo_slug': '',
            'funcao_slug': '',
            'category_label': 'Microventilador AC',
            'breadcrumb_label': 'Microventiladores AC',
            'breadcrumb_filter': 'micro-ac',
            'title': f'Microventilador AC {dim_display}',
            'description': (
                f'{codigo} — Microventilador AC {dim_display}, {voltagem_display(voltagem)}, '
                f'modelo {modelo}, mancal de {cap(mancal).lower()}, '
                f'carcaça em {cap(carcaca).lower()}, {fios_display}. '
                f'Vida útil {vida.strip()}.'
            ),
            'specs_table': [
                ('Tipo', 'Microventilador AC'),
                ('Modelo', modelo),
                ('Voltagem', voltagem_display(voltagem)),
                ('Dimensão', dim_display),
                ('Mancal', cap(mancal)),
                ('Fios', fios_display),
                ('Carcaça', cap(carcaca)),
                ('Vida útil', vida.strip()),
            ],
        })

    # Microventiladores DC — rows 12-41 (indices 11-40)
    for r in rows[11:41]:
        _, codigo, modelo, voltagem, dimensao, mancal, vida, fios, carcaca = r
        if not codigo:
            continue
        dim_display = dimensao.replace('X', '×') + 'mm'
        fios_display = fios.lower().strip()
        records.append({
            'codigo': codigo,
            'modelo': modelo,
            'tipo_slug': 'micro-dc',
            'tensao_slug': tensao_slug(voltagem),
            'mancal_slug': mancal.lower() if mancal else '',
            'subtipo_slug': '',
            'funcao_slug': '',
            'category_label': 'Microventilador DC',
            'breadcrumb_label': 'Microventiladores DC',
            'breadcrumb_filter': 'micro-dc',
            'title': f'Microventilador DC {dim_display}',
            'description': (
                f'{codigo} — Microventilador DC {dim_display} ({voltagem}), '
                f'modelo {modelo}, mancal de {cap(mancal).lower()}, '
                f'carcaça em {cap(carcaca).lower()}, {fios_display}. '
                f'Vida útil {vida.strip()}.'
            ),
            'specs_table': [
                ('Tipo', 'Microventilador DC'),
                ('Modelo', modelo),
                ('Voltagem', voltagem),
                ('Dimensão', dim_display),
                ('Mancal', cap(mancal)),
                ('Fios', fios_display),
                ('Carcaça', cap(carcaca)),
                ('Vida útil', vida.strip()),
            ],
        })

    # Axiais — rows 44-64 (indices 43-63)
    for r in rows[43:64]:
        _, codigo, modelo, voltagem, dimensao, funcao, pas, carcaca, vida = r
        if not codigo:
            continue
        funcao_l = funcao.lower() if funcao else ''
        title_prefix = 'Soprador' if funcao_l == 'soprador' else 'Exaustor'
        records.append({
            'codigo': codigo,
            'modelo': modelo,
            'tipo_slug': 'axial',
            'tensao_slug': tensao_slug(voltagem),
            'mancal_slug': '',
            'subtipo_slug': '',
            'funcao_slug': funcao_l,
            'category_label': f'Ventilador Axial {title_prefix}',
            'breadcrumb_label': 'Ventiladores Axiais',
            'breadcrumb_filter': 'axial',
            'title': f'{title_prefix} Axial {dimensao}',
            'description': (
                f'{codigo} — Ventilador axial ({title_prefix.lower()}) {dimensao}, '
                f'modelo {modelo}, voltagem {voltagem}.'
            ),
            'specs_table': [
                ('Tipo', f'Ventilador Axial — {title_prefix}'),
                ('Modelo', modelo),
                ('Voltagem', voltagem),
                ('Dimensão', dimensao),
                ('Função', cap(funcao)),
                ('Pás', pas.lower() if pas else ''),
                ('Carcaça', cap(carcaca)),
                ('Vida útil', vida.strip() if vida else ''),
            ],
        })

    # Telas metálicas — rows 68-74 (indices 67-73)
    for r in rows[67:74]:
        _, codigo, modelo, cor, tamanho, material, *_rest = r
        if not codigo:
            continue
        dim_display = tamanho.replace('X', '×').replace('x', '×') + 'mm'
        records.append({
            'codigo': codigo,
            'modelo': modelo,
            'tipo_slug': 'acessorio',
            'tensao_slug': '',
            'mancal_slug': '',
            'subtipo_slug': 'tela',
            'funcao_slug': '',
            'category_label': 'Tela Metálica',
            'breadcrumb_label': 'Acessórios',
            'breadcrumb_filter': 'acessorio',
            'title': f'Tela Metálica {dim_display}',
            'description': (
                f'{codigo} — Tela metálica {dim_display}, modelo {modelo}, '
                f'material {cap(material).lower()}, cor {cap(cor).lower()}.'
            ),
            'specs_table': [
                ('Tipo', 'Tela Metálica'),
                ('Modelo', modelo),
                ('Material', cap(material)),
                ('Cor', cap(cor)),
                ('Tamanho', dim_display),
            ],
        })

    # Grelhas ABS — rows 77-79 (indices 76-78)
    for r in rows[76:79]:
        _, codigo, modelo, cor, tamanho, material, *_rest = r
        if not codigo:
            continue
        dim_display = tamanho.replace('X', '×').replace('x', '×') + 'mm'
        records.append({
            'codigo': codigo,
            'modelo': modelo,
            'tipo_slug': 'acessorio',
            'tensao_slug': '',
            'mancal_slug': '',
            'subtipo_slug': 'grelha',
            'funcao_slug': '',
            'category_label': 'Grelha ABS',
            'breadcrumb_label': 'Acessórios',
            'breadcrumb_filter': 'acessorio',
            'title': f'Grelha ABS {dim_display}',
            'description': (
                f'{codigo} — Grelha ABS {dim_display}, modelo {modelo}, '
                f'material {cap(material).lower()}, cor {cap(cor).lower()}.'
            ),
            'specs_table': [
                ('Tipo', 'Grelha ABS'),
                ('Modelo', modelo),
                ('Material', cap(material)),
                ('Cor', cap(cor)),
                ('Tamanho', dim_display),
            ],
        })

    # Porta-filtros — rows 82-84 (indices 81-83)
    for r in rows[81:84]:
        _, codigo, modelo, cor, tamanho, material, *_rest = r
        if not codigo:
            continue
        dim_display = tamanho.replace('X', '×').replace('x', '×') + 'mm'
        records.append({
            'codigo': codigo,
            'modelo': modelo,
            'tipo_slug': 'acessorio',
            'tensao_slug': '',
            'mancal_slug': '',
            'subtipo_slug': 'porta-filtro',
            'funcao_slug': '',
            'category_label': 'Porta-filtro',
            'breadcrumb_label': 'Acessórios',
            'breadcrumb_filter': 'acessorio',
            'title': f'Porta-filtro {dim_display}',
            'description': (
                f'{codigo} — Porta-filtro {dim_display}, modelo {modelo}, '
                f'material {cap(material).lower()}, cor {cap(cor).lower()}.'
            ),
            'specs_table': [
                ('Tipo', 'Porta-filtro'),
                ('Modelo', modelo),
                ('Material', cap(material)),
                ('Cor', cap(cor)),
                ('Tamanho', dim_display),
            ],
        })

    # Termostatos — rows 87-89 (indices 86-88)
    for r in rows[86:89]:
        _, codigo, modelo, voltagem, tamanho, amperagem, *_rest = r
        if not codigo:
            continue
        dim_display = tamanho.replace('X', '×').replace('x', '×') + 'mm'
        records.append({
            'codigo': codigo,
            'modelo': modelo,
            'tipo_slug': 'acessorio',
            'tensao_slug': tensao_slug(voltagem),
            'mancal_slug': '',
            'subtipo_slug': 'termostato',
            'funcao_slug': '',
            'category_label': 'Termostato',
            'breadcrumb_label': 'Acessórios',
            'breadcrumb_filter': 'acessorio',
            'title': f'Termostato {dim_display}',
            'description': (
                f'{codigo} — Termostato {dim_display}, modelo {modelo}, '
                f'voltagem {voltagem}, amperagem {amperagem}.'
            ),
            'specs_table': [
                ('Tipo', 'Termostato'),
                ('Modelo', modelo),
                ('Voltagem', voltagem),
                ('Tamanho', dim_display),
                ('Amperagem', amperagem),
            ],
        })

    return records


# ---------------------------------------------------------------------------
# Catalog card HTML.
# ---------------------------------------------------------------------------

def card_html(rec):
    sku = rec['codigo']
    img_src = find_image(sku)
    style_attr = ''
    override = IMG_STYLE_OVERRIDES.get(sku)
    if override:
        style_attr = f' style="{override}"'
    detail_href = f'produto/{slug(sku)}.html'
    data_attrs = {
        'data-tipo': rec['tipo_slug'],
        'data-tensao': rec['tensao_slug'],
        'data-mancal': rec['mancal_slug'],
        'data-subtipo': rec['subtipo_slug'],
        'data-funcao': rec['funcao_slug'],
    }
    attrs = ' '.join(f'{k}="{v}"' for k, v in data_attrs.items() if v)
    alt = f'Produto {sku}'
    return f'''        <article class="product-card" {attrs}>
          <div class="product-card__img"><img src="{img_src}" alt="{html.escape(alt)}" loading="lazy"{style_attr}></div>
          <div class="product-card__body">
            <p class="product-card__sku">{html.escape(sku)}</p>
            <h3 class="product-card__title">{html.escape(rec["title"])}</h3>
            <div class="product-card__actions">
              <a href="{detail_href}" class="product-card__btn product-card__btn--outline">Especificações</a>
              <a href="{WA_GENERIC_HREF}" target="_blank" rel="noopener noreferrer" class="product-card__btn product-card__btn--red">Cotação</a>
            </div>
          </div>
        </article>'''


# ---------------------------------------------------------------------------
# Detail page HTML.
# ---------------------------------------------------------------------------

WA_ICON_LARGE = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="margin-right:8px;vertical-align:middle"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'

WA_ICON_SMALL = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right:6px;vertical-align:middle"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'


def detail_page_html(rec):
    sku = rec['codigo']
    slug_str = slug(sku)
    main_image = find_image(sku)
    extra_images = find_extra_images(sku)
    all_images = [main_image] + extra_images

    page_title = f'{sku} · {rec["title"]} | ASA Fan'
    canonical = f'{SITE_BASE}/produto/{slug_str}.html'
    og_image = f'{SITE_BASE}/{main_image}'
    img_alt = f'Produto {sku} — {rec["title"]}'
    description = rec['description']

    # WhatsApp link with SKU + title pre-tagged.
    wa_msg = (
        f'Olá! Gostaria de solicitar uma cotação para o produto '
        f'{sku} ({rec["title"]}, modelo {rec["modelo"]}).'
    )
    wa_url = f'https://wa.me/{WA_PHONE}?text=' + urllib.parse.quote(wa_msg)

    # Spec table rows.
    table_rows = '\n'.join(
        f'              <tr><th scope="row">{html.escape(k)}</th><td>{html.escape(v)}</td></tr>'
        for k, v in rec['specs_table'] if v
    )

    # Carousel slides (1 + any extras found on disk).
    slide_blocks = []
    for i, img_path in enumerate(all_images):
        active = ' is-active' if i == 0 else ''
        loading = 'eager" fetchpriority="high' if i == 0 else 'lazy'
        slide_blocks.append(
            f'              <div class="product-detail__slide{active}" role="group" aria-roledescription="slide" aria-label="{i + 1} de {len(all_images)}">\n'
            f'                <img src="../{img_path}" alt="{html.escape(img_alt)}" loading="{loading}">\n'
            f'              </div>'
        )
    slides_html = '\n'.join(slide_blocks)

    dot_blocks = []
    for i in range(len(all_images)):
        active_cls = ' is-active' if i == 0 else ''
        sel = 'true' if i == 0 else 'false'
        dot_blocks.append(
            f'              <button class="product-detail__dot{active_cls}" type="button" role="tab" aria-selected="{sel}" aria-label="Imagem {i + 1}"></button>'
        )
    dots_html = '\n'.join(dot_blocks)

    # JSON-LD payloads (built as Python dicts then serialized).
    product_schema = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'sku': sku,
        'name': f'{rec["title"]} — {sku} ({rec["modelo"]})' if rec['modelo'] else f'{rec["title"]} — {sku}',
        'image': og_image,
        'description': description,
        'brand': {'@type': 'Brand', 'name': 'ASA Fan'},
        'manufacturer': {'@type': 'Organization', 'name': 'Adda South America Corporation'},
        'category': rec['category_label'],
    }
    if rec['modelo']:
        product_schema['mpn'] = rec['modelo']
    product_schema_json = json.dumps(product_schema, ensure_ascii=False, indent=2)

    breadcrumb_schema = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE_BASE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Produtos', 'item': f'{SITE_BASE}/produtos.html'},
            {'@type': 'ListItem', 'position': 3, 'name': rec['breadcrumb_label'],
             'item': f'{SITE_BASE}/produtos.html?tipo={rec["breadcrumb_filter"]}'},
            {'@type': 'ListItem', 'position': 4, 'name': sku},
        ],
    }
    breadcrumb_schema_json = json.dumps(breadcrumb_schema, ensure_ascii=False, indent=2)

    head = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{html.escape(description)}">
  <title>{html.escape(page_title)}</title>
  <link rel="canonical" href="{canonical}">

  <!-- Open Graph -->
  <meta property="og:type" content="product">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{html.escape(page_title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:locale" content="pt_BR">
  <meta property="og:site_name" content="ASA Fan">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(page_title)}">
  <meta name="twitter:description" content="{html.escape(description)}">
  <meta name="twitter:image" content="{og_image}">

  <link rel="icon" type="image/png" href="../assets/logo/favicon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
</head>'''

    header_block = f'''  <header class="header">
    <div class="container">
      <a href="../index.html" class="header__logo">
        <img src="../assets/logo/logo.png" alt="ASA Fan Logo">
      </a>
      <button class="header__toggle" onclick="toggleMenu()" aria-label="Abrir menu">
        <span></span><span></span><span></span>
      </button>
      <nav class="header__nav" id="mainNav">
        <a href="../index.html">Home</a>
        <a href="../quem-somos.html">Sobre</a>
        <div class="nav-dropdown">
          <a href="../produtos.html" class="active">Produtos</a>
          <div class="nav-dropdown__menu">
            <a href="../produtos.html">Microventiladores</a>
            <a href="../produtos.html?tipo=axial">Axiais</a>
            <a href="../produtos.html?tipo=acessorio">Acessórios</a>
          </div>
        </div>
        <a href="../aplicacoes.html">Aplicações</a>
        <a href="../carreira.html">Carreira</a>
        <a href="../fale-conosco.html">Contato</a>
        <a href="https://wa.me/{WA_PHONE}?text=Olá! Gostaria de solicitar uma cotação." target="_blank" rel="noopener noreferrer" class="header__cta">{WA_ICON_SMALL}Solicitar Cotação</a>
      </nav>
    </div>
  </header>'''

    breadcrumb_block = f'''  <nav class="breadcrumb" aria-label="Você está aqui">
    <div class="container">
      <ol class="breadcrumb__list">
        <li><a href="../index.html">Home</a></li>
        <li><a href="../produtos.html">Produtos</a></li>
        <li><a href="../produtos.html?tipo={rec["breadcrumb_filter"]}">{html.escape(rec["breadcrumb_label"])}</a></li>
        <li aria-current="page">{html.escape(sku)}</li>
      </ol>
    </div>
  </nav>'''

    detail_block = f'''  <section class="product-detail">
    <div class="container">
      <div class="product-detail__layout">

        <header class="product-detail__header">
          <p class="product-detail__sku">Código {html.escape(sku)}</p>
          <h1 class="product-detail__title">{html.escape(rec["title"])}</h1>
        </header>

        <table class="product-detail__table">
          <tbody>
{table_rows}
          </tbody>
        </table>

        <div class="product-detail__media">
          <div class="product-detail__carousel" aria-roledescription="carousel" aria-label="Imagens do produto {html.escape(sku)}">
            <div class="product-detail__slides">
{slides_html}
            </div>
            <button class="product-detail__nav product-detail__nav--prev" type="button" aria-label="Imagem anterior">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
            </button>
            <button class="product-detail__nav product-detail__nav--next" type="button" aria-label="Próxima imagem">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
            <div class="product-detail__dots" role="tablist" aria-label="Selecionar imagem">
{dots_html}
            </div>
          </div>
        </div>

        <div class="product-detail__actions">
          <a href="../produtos.html" class="btn product-detail__back">← Voltar ao Catálogo</a>
          <a href="{wa_url}" target="_blank" rel="noopener noreferrer" class="btn btn--red product-detail__cta">{WA_ICON_LARGE}Solicitar Cotação</a>
        </div>

      </div>
    </div>
  </section>'''

    footer_block = '''  <footer class="footer">
    <div class="container">
      <div class="footer__content">
        <div>
          <div class="footer__logo">
            <img src="../assets/logo/logo.png" alt="ASA Fan">
          </div>
          <p class="footer__desc">Ventilação industrial com precisão desde 1999.</p>
        </div>
        <div>
          <h4 class="footer__title">Navegação</h4>
          <div class="footer__links">
            <a href="../index.html">Home</a>
            <a href="../quem-somos.html">Sobre</a>
            <a href="../produtos.html">Produtos</a>
            <a href="../fale-conosco.html">Cotação</a>
            <a href="../fale-conosco.html">Contato</a>
          </div>
        </div>
        <div>
          <h4 class="footer__title">Produtos</h4>
          <div class="footer__links">
            <a href="../produtos.html">Microventiladores AC/DC</a>
            <a href="../produtos.html?tipo=axial">Ventiladores Axiais</a>
            <a href="../produtos.html?tipo=acessorio">Acessórios</a>
          </div>
        </div>
        <div>
          <h4 class="footer__title">Contato</h4>
          <p class="footer__contact-item">R. Santa Mônica, 1130, Cotia/SP</p>
          <p class="footer__contact-item">Tel: (11) 3406-5088</p>
          <p class="footer__contact-item">comercial@asafan.com.br</p>
        </div>
      </div>
      <div class="footer__bar">
        &copy; 2026 Adda South America Corporation. Todos os direitos reservados.
      </div>
    </div>
  </footer>'''

    scripts_block = (
        '  <script src="../js/main.js"></script>\n\n'
        '  <!-- Structured Data: Product -->\n'
        '  <script type="application/ld+json">\n'
        f'{product_schema_json}\n'
        '  </script>\n\n'
        '  <!-- Structured Data: BreadcrumbList -->\n'
        '  <script type="application/ld+json">\n'
        f'{breadcrumb_schema_json}\n'
        '  </script>'
    )

    return (
        head + '\n<body>\n\n'
        + header_block + '\n\n'
        + breadcrumb_block + '\n\n'
        + detail_block + '\n\n'
        + footer_block + '\n\n'
        + scripts_block + '\n\n'
        + '</body>\n</html>\n'
    )


# ---------------------------------------------------------------------------
# Apply patches to produtos.html and sitemap.xml.
# ---------------------------------------------------------------------------

CARDS_BEGIN = '<!-- BEGIN: product cards (auto-generated by scripts/generate_cards.py) -->'
CARDS_END = '<!-- END: product cards -->'


def patch_produtos_html(cards_html_block):
    """Replace product cards bracketed by BEGIN/END markers in produtos.html.

    Idempotent: re-running replaces only the marked block, never the surrounding
    catalog markup. If markers are missing (first run on a fresh file), we
    inject them inside the catalog__grid div before any existing cards."""
    path = pathlib.Path('produtos.html')
    src = path.read_text(encoding='utf-8')

    block = (
        '          ' + CARDS_BEGIN + '\n'
        + cards_html_block + '\n'
        + '          ' + CARDS_END
    )

    if CARDS_BEGIN in src and CARDS_END in src:
        # Idempotent path: replace existing block.
        new_src = re.sub(
            r'          ' + re.escape(CARDS_BEGIN) + r'.*?          ' + re.escape(CARDS_END),
            block,
            src,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # First run: strip any existing <article class="product-card"> ... </article>
        # blocks inside the grid, then drop our marker block in.
        if '<div class="catalog__grid">' not in src:
            raise SystemExit('produtos.html: catalog__grid div not found, refusing to patch.')
        cleaned = re.sub(
            r'\s*<article class="product-card"[^>]*>.*?</article>',
            '',
            src,
            flags=re.DOTALL,
        )
        new_src = cleaned.replace(
            '<div class="catalog__grid">\n',
            '<div class="catalog__grid">\n' + block + '\n',
            1,
        )

    path.write_text(new_src, encoding='utf-8')


SITEMAP_BEGIN = '<!-- BEGIN: product detail pages (auto-generated) -->'
SITEMAP_END = '<!-- END: product detail pages (auto-generated) -->'


def patch_sitemap(records):
    """Add a marker-bracketed block of product detail URLs to sitemap.xml.
    Idempotent — re-running replaces the previous block."""
    path = pathlib.Path('sitemap.xml')
    src = path.read_text(encoding='utf-8')

    entries = []
    for rec in records:
        loc = f'{SITE_BASE}/produto/{slug(rec["codigo"])}.html'
        entries.append(
            '  <url>\n'
            f'    <loc>{loc}</loc>\n'
            '    <changefreq>monthly</changefreq>\n'
            '    <priority>0.7</priority>\n'
            '  </url>'
        )
    block = '  ' + SITEMAP_BEGIN + '\n' + '\n'.join(entries) + '\n  ' + SITEMAP_END

    if SITEMAP_BEGIN in src:
        # Replace existing block.
        new_src = re.sub(
            r'  ' + re.escape(SITEMAP_BEGIN) + r'.*?  ' + re.escape(SITEMAP_END),
            block,
            src,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # Insert right before </urlset>.
        new_src = src.replace('</urlset>', block + '\n</urlset>')

    path.write_text(new_src, encoding='utf-8')


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true',
                        help='Patch produtos.html and sitemap.xml in place.')
    args = parser.parse_args()

    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb['Planilha1']
    records = collect_records(ws)

    # Cards.
    cards = [card_html(r) for r in records]
    cards_html_block = '\n\n'.join(cards)
    OUT_CARDS.parent.mkdir(exist_ok=True)
    OUT_CARDS.write_text(cards_html_block + '\n', encoding='utf-8')

    # Detail pages.
    PRODUTO_DIR.mkdir(exist_ok=True)
    detail_count = 0
    for rec in records:
        out = PRODUTO_DIR / f'{slug(rec["codigo"])}.html'
        out.write_text(detail_page_html(rec), encoding='utf-8')
        detail_count += 1

    print(f'Generated {len(cards)} catalog cards -> {OUT_CARDS}')
    print(f'Generated {detail_count} detail pages -> {PRODUTO_DIR}/*.html')

    placeholders = sum(1 for c in cards if 'placeholder.png' in c)
    print(f'Using placeholder.png on {placeholders} cards')

    if args.apply:
        patch_produtos_html(cards_html_block)
        print('Patched produtos.html')
        patch_sitemap(records)
        print('Patched sitemap.xml')
    else:
        print('(Run with --apply to patch produtos.html and sitemap.xml.)')


if __name__ == '__main__':
    main()
