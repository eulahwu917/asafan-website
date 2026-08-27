#!/usr/bin/env python3
"""Apply shared shell, privacy, accessibility, and cache-version updates.

The site is intentionally static for Locaweb compatibility. This script keeps
the duplicated HTML shell synchronized without introducing a server runtime.
It is idempotent and safe to run after regenerating product pages.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import struct


ROOT = Path(__file__).resolve().parent.parent
VERSION = "2026-08-27a"
LASTMOD = "2026-08-27"
GENERIC_WHATSAPP_RAW = "https://wa.me/551134065088?text=Olá! Gostaria de solicitar uma cotação."
GENERIC_WHATSAPP_ENCODED = (
    "https://wa.me/551134065088?text="
    "Ol%C3%A1%21%20Gostaria%20de%20solicitar%20uma%20cota%C3%A7%C3%A3o."
)
CONSENT_HEAD = f'  <script src="/js/consent.js?v={VERSION}"></script>'
NOSCRIPT = (
    "  <noscript><div class=\"noscript-notice\">O JavaScript está desativado. "
    "Nenhum cookie opcional de analytics ou marketing será carregado.</div></noscript>"
)


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as fh:
            head = fh.read(24)
            if head.startswith(b"\x89PNG\r\n\x1a\n"):
                return struct.unpack(">II", head[16:24])
            if head[:3] == b"GIF":
                return struct.unpack("<HH", head[6:10])
            if head[:2] != b"\xff\xd8":
                return None
            fh.seek(2)
            while True:
                marker_start = fh.read(1)
                if not marker_start:
                    return None
                if marker_start != b"\xff":
                    continue
                marker = fh.read(1)
                while marker == b"\xff":
                    marker = fh.read(1)
                if marker in {bytes([n]) for n in range(0xC0, 0xC4)} | {bytes([n]) for n in range(0xC5, 0xC8)} | {bytes([n]) for n in range(0xC9, 0xCC)} | {bytes([n]) for n in range(0xCD, 0xD0)}:
                    length = struct.unpack(">H", fh.read(2))[0]
                    data = fh.read(length - 2)
                    return struct.unpack(">HH", data[1:5])[::-1]
                length_bytes = fh.read(2)
                if len(length_bytes) != 2:
                    return None
                length = struct.unpack(">H", length_bytes)[0]
                fh.seek(length - 2, 1)
    except (OSError, struct.error):
        return None


def add_image_dimensions(text: str, page: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        tag = match.group(0)
        if re.search(r"\swidth=", tag, re.I) and re.search(r"\sheight=", tag, re.I):
            return tag
        src_match = re.search(r'\ssrc=["\']([^"\']+)', tag, re.I)
        if not src_match:
            return tag
        src = src_match.group(1)
        parts = urlsplit(src)
        if parts.scheme or parts.netloc or src.startswith("data:"):
            return tag
        candidate = ROOT / unquote(parts.path).lstrip("/") if src.startswith("/") else page.parent / unquote(parts.path)
        size = image_size(candidate.resolve())
        if not size:
            return tag
        width, height = size
        attrs = ""
        if not re.search(r"\swidth=", tag, re.I):
            attrs += f' width="{width}"'
        if not re.search(r"\sheight=", tag, re.I):
            attrs += f' height="{height}"'
        return tag[:-1] + attrs + ">"

    return re.sub(r"<img\b[^>]*>", replace, text, flags=re.I)


def update_page(page: Path) -> bool:
    text = page.read_text(encoding="utf-8")
    original = text

    # Replace the original always-on integrations with the shared consent loader.
    text = re.sub(
        r"\s*<!-- Google Tag Manager -->.*?<!-- End Meta Pixel Code -->",
        "\n" + CONSENT_HEAD,
        text,
        count=1,
        flags=re.S,
    )
    if CONSENT_HEAD not in text:
        text = re.sub(r"<head>", "<head>\n" + CONSENT_HEAD, text, count=1)

    # Tracking noscript fallbacks cannot honor consent, so replace them with a notice.
    text = re.sub(
        r"\s*<!-- Google Tag Manager \(noscript\) -->.*?<!-- End Meta Pixel Code \(noscript\) -->",
        "\n" + NOSCRIPT,
        text,
        count=1,
        flags=re.S,
    )
    if NOSCRIPT not in text:
        text = re.sub(r"<body>", "<body>\n" + NOSCRIPT, text, count=1)

    text = text.replace(GENERIC_WHATSAPP_RAW, GENERIC_WHATSAPP_ENCODED)
    text = re.sub(r"style\.css\?v=[^\"']+", f"style.css?v={VERSION}", text)
    text = re.sub(r"main\.js\?v=[^\"']+", f"main.js?v={VERSION}", text)
    text = re.sub(r"consent\.js\?v=[^\"']+", f"consent.js?v={VERSION}", text)

    text = re.sub(
        r'<button class="header__toggle" onclick="toggleMenu\(\)" aria-label="Abrir menu">',
        '<button type="button" class="header__toggle" aria-label="Abrir menu" aria-controls="mainNav" aria-expanded="false">',
        text,
    )
    text = re.sub(
        r'<button class="header__toggle" aria-label="Abrir menu">',
        '<button type="button" class="header__toggle" aria-label="Abrir menu" aria-controls="mainNav" aria-expanded="false">',
        text,
    )

    text = text.replace('<form onsubmit="return handleContactForm(event)">', '<form action="/submit.php" method="post" data-form-type="contact">\n            <input type="hidden" name="type" value="contact">')
    text = text.replace('<form onsubmit="return handleCareerForm(event)">', '<form action="/submit.php" method="post" data-form-type="career">\n            <input type="hidden" name="type" value="career">')
    autocomplete_fields = {
        "contact-nome": "name",
        "contact-telefone": "tel",
        "contact-email": "email",
        "career-nome": "name",
        "career-nascimento": "bday",
        "career-email": "email",
        "career-telefone": "tel",
    }
    for field_id, token in autocomplete_fields.items():
        pattern = rf'(<(?:input|textarea|select)\b[^>]*\bid="{re.escape(field_id)}"[^>]*)(>)'
        def set_autocomplete(match: re.Match[str], value: str = token) -> str:
            tag = re.sub(r'\s+autocomplete="[^"]*"', "", match.group(1))
            return tag + f' autocomplete="{value}"' + match.group(2)
        text = re.sub(pattern, set_autocomplete, text, count=1)

    if page.name == "carreira.html" and "privacy-form-note" not in text:
        text = text.replace(
            '            <button type="submit" class="btn btn--primary"',
            '            <p class="privacy-form-note">Consulte a <a href="privacidade.html">Política de Privacidade</a> para saber sobre retenção e seus direitos.</p>\n            <button type="submit" class="btn btn--primary"',
        )
    if page.name == "fale-conosco.html" and "privacy-form-note" not in text:
        text = text.replace(
            '            <button type="submit" class="btn btn--primary"',
            '            <p class="privacy-form-note">Ao enviar, seus dados serão usados para responder à solicitação. Veja a <a href="privacidade.html">Política de Privacidade</a>.</p>\n            <button type="submit" class="btn btn--primary"',
        )

    text = text.replace('<h4 class="footer__title">', '<h2 class="footer__title">').replace('</h4>', '</h2>')
    prefix = "../" if page.parent.name == "produto" else ""
    privacy_pair = re.compile(
        r'\s*<a href="(?:\.\./)?privacidade\.html">Privacidade</a>\s*'
        r'<button type="button" class="footer__privacy-button js-cookie-settings">Preferências de cookies</button>'
    )
    text = privacy_pair.sub("", text)
    footer_at = text.find('<footer class="footer">')
    if footer_at >= 0:
        before, footer = text[:footer_at], text[footer_at:]
        contact = f'<a href="{prefix}fale-conosco.html">Contato</a>'
        addition = contact + f'\n            <a href="{prefix}privacidade.html">Privacidade</a>\n            <button type="button" class="footer__privacy-button js-cookie-settings">Preferências de cookies</button>'
        footer = footer.replace(contact, addition, 1)
        text = before + footer

    text = text.replace('width="100%"\n          height="400"', 'width="600"\n          height="400"')
    text = re.sub(r'<div class="(hero__carousel|product-detail__carousel)" aria-roledescription=', r'<div class="\1" role="region" aria-roledescription=', text)
    text = re.sub(r'<div class="(hero__dots|product-detail__dots)" aria-label=', r'<div class="\1" role="group" aria-label=', text)

    if page.name == "index.html" and "partnersHeading" not in text:
        text = text.replace('<section class="partners">', '<section class="partners" aria-labelledby="partnersHeading">\n    <h2 class="visually-hidden" id="partnersHeading">Empresas que confiam na ASA Fan</h2>')
    if page.name == "produtos.html" and "catalogFiltersHeading" not in text:
        text = text.replace('<aside class="catalog__sidebar">', '<aside class="catalog__sidebar" aria-labelledby="catalogFiltersHeading">\n          <h2 class="visually-hidden" id="catalogFiltersHeading">Filtros do catálogo</h2>')

    text = re.sub(r'(<div class="footer__logo">\s*<img\b(?![^>]*loading=)[^>]*)(>)', r'\1 loading="lazy"\2', text)
    text = add_image_dimensions(text, page)

    if text != original:
        page.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def main() -> None:
    changed = [page for page in sorted(ROOT.rglob("*.html")) if page.name != "404.html" and update_page(page)]
    sitemap = ROOT / "sitemap.xml"
    sitemap_text = sitemap.read_text(encoding="utf-8")
    updated_sitemap = re.sub(r"<lastmod>[^<]+</lastmod>", f"<lastmod>{LASTMOD}</lastmod>", sitemap_text)
    if updated_sitemap != sitemap_text:
        sitemap.write_text(updated_sitemap, encoding="utf-8", newline="\n")
        print("Updated sitemap last-modified dates.")
    print(f"Updated {len(changed)} page(s).")
    for page in changed:
        print("  " + page.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
