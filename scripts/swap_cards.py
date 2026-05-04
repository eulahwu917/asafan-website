#!/usr/bin/env python
"""Swap the catalog grid contents of produtos.html with scripts/_generated_cards.html.

Finds the `<div class="catalog__grid">` ... `</div>` block in produtos.html and
replaces the inner content with the freshly-generated cards.
"""
import pathlib
import re

HTML = pathlib.Path('produtos.html')
NEW_CARDS = pathlib.Path('scripts/_generated_cards.html')


def main():
    html_text = HTML.read_text(encoding='utf-8')
    cards = NEW_CARDS.read_text(encoding='utf-8').rstrip()

    # Match: <div class="catalog__grid">...</div>
    # The grid contains 77 article blocks. The closing </div> is the FIRST </div>
    # at the right indentation level after the last </article>.
    open_tag = '<div class="catalog__grid">'
    open_idx = html_text.find(open_tag)
    if open_idx < 0:
        raise SystemExit('Could not find <div class="catalog__grid"> in produtos.html')

    # Find the matching </div>: walk forward from open_idx counting div nesting.
    # Since article blocks contain <div class="product-card__img"> etc., we need
    # to track nesting properly.
    pos = open_idx + len(open_tag)
    depth = 1
    div_re = re.compile(r'<(/?)div\b[^>]*>')
    close_idx = None
    for m in div_re.finditer(html_text, pos):
        if m.group(1):  # closing
            depth -= 1
            if depth == 0:
                close_idx = m.start()
                break
        else:
            depth += 1
    if close_idx is None:
        raise SystemExit('Could not find matching </div> for catalog__grid')

    # Replace inner content. Preserve the indentation of the closing </div>:
    # find the start of the line containing close_idx.
    line_start = html_text.rfind('\n', 0, close_idx) + 1
    closing_indent = html_text[line_start:close_idx]

    new_html = (
        html_text[:open_idx + len(open_tag)]
        + '\n'
        + cards
        + '\n'
        + closing_indent
        + html_text[close_idx:]
    )
    HTML.write_text(new_html, encoding='utf-8')

    # Sanity report
    new_card_count = new_html.count('<article class="product-card"')
    placeholder_count = new_html.count('placeholder.png')
    print(f'Swapped catalog__grid in {HTML}')
    print(f'  product cards: {new_card_count}')
    print(f'  placeholder.png references: {placeholder_count}')


if __name__ == '__main__':
    main()
