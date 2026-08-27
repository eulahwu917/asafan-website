#!/usr/bin/env python3
"""Fast, dependency-free checks for the static site and its deploy inputs."""

from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
PUBLIC_HTML = sorted(
    page for page in ROOT.rglob("*.html")
    if not any(part.startswith(".") or part in {"node_modules", "raw_assets"} for part in page.parts)
)
CONSENT_SRC = "/js/consent.js?v=2026-08-27a"
SITE_BASE = "https://www.asafan.com.br"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.refs: list[tuple[str, str]] = []
        self.scripts: list[str] = []
        self.h1_count = 0
        self.title_count = 0
        self.description_count = 0
        self.canonical_count = 0
        self.inline_handlers: list[str] = []
        self.unsafe_blanks: list[str] = []
        self.images_without_size: list[str] = []

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        if attrs.get("id"):
            self.ids.append(attrs["id"] or "")
        for name in ("href", "src", "action"):
            if attrs.get(name):
                self.refs.append((name, attrs[name] or ""))
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"] or "")
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self.title_count += 1
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description_count += 1
        if tag == "link" and attrs.get("rel", "").lower() == "canonical":
            self.canonical_count += 1
        self.inline_handlers.extend(name for name, _ in attrs_list if name.lower().startswith("on"))
        if attrs.get("target") == "_blank":
            rel = set((attrs.get("rel") or "").lower().split())
            if "noopener" not in rel:
                self.unsafe_blanks.append(attrs.get("href") or "unknown")
        if tag == "img" and (not attrs.get("width") or not attrs.get("height")):
            self.images_without_size.append(attrs.get("src") or "unknown")


def local_target(page: Path, ref: str) -> Path | None:
    parts = urlsplit(ref)
    if parts.scheme or parts.netloc or ref.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    path = unquote(parts.path)
    if not path:
        return None
    return (ROOT / path.lstrip("/")) if path.startswith("/") else (page.parent / path)


def check_page(page: Path) -> list[str]:
    errors: list[str] = []
    relative = page.relative_to(ROOT).as_posix()
    text = page.read_text(encoding="utf-8")
    parser = PageParser()
    try:
        parser.feed(text)
    except Exception as exc:
        return [f"{relative}: HTML parser error: {exc}"]

    duplicates = sorted(key for key, count in Counter(parser.ids).items() if count > 1)
    if duplicates:
        errors.append(f"{relative}: duplicate id(s): {', '.join(duplicates)}")
    if parser.title_count != 1:
        errors.append(f"{relative}: expected one title, found {parser.title_count}")
    if parser.description_count != 1:
        errors.append(f"{relative}: expected one meta description, found {parser.description_count}")
    if parser.h1_count != 1:
        errors.append(f"{relative}: expected one h1, found {parser.h1_count}")
    if page.name != "404.html" and parser.canonical_count != 1:
        errors.append(f"{relative}: expected one canonical, found {parser.canonical_count}")
    if parser.scripts.count(CONSENT_SRC) != 1:
        errors.append(f"{relative}: consent loader count is {parser.scripts.count(CONSENT_SRC)}")
    if parser.inline_handlers:
        errors.append(f"{relative}: inline event handler(s): {', '.join(parser.inline_handlers)}")
    if parser.unsafe_blanks:
        errors.append(f"{relative}: target=_blank missing noopener: {parser.unsafe_blanks[0]}")
    if parser.images_without_size:
        errors.append(f"{relative}: image missing dimensions: {parser.images_without_size[0]}")
    if "?text=Olá!" in text:
        errors.append(f"{relative}: WhatsApp message is not URL-encoded")
    if re.search(r"G-FJ24086P54|GTM-TLD85DRR|1381605680078293", text):
        errors.append(f"{relative}: direct tracking ID found outside consent.js")
    for _, ref in parser.refs:
        target = local_target(page, ref)
        if target is not None and not target.resolve().exists():
            errors.append(f"{relative}: missing local target: {ref}")
    return errors


def expected_sitemap_urls() -> set[str]:
    urls = {f"{SITE_BASE}/"}
    for page in PUBLIC_HTML:
        if page.name in {"index.html", "404.html"}:
            continue
        urls.add(f"{SITE_BASE}/{page.relative_to(ROOT).as_posix()}")
    return urls


def check_sitemap() -> list[str]:
    tree = ET.parse(ROOT / "sitemap.xml")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    actual = {loc.text or "" for loc in tree.findall("sm:url/sm:loc", ns)}
    expected = expected_sitemap_urls()
    errors = [f"sitemap.xml: missing {url}" for url in sorted(expected - actual)]
    errors.extend(f"sitemap.xml: unexpected {url}" for url in sorted(actual - expected))
    return errors


def main() -> int:
    errors: list[str] = []
    for page in PUBLIC_HTML:
        errors.extend(check_page(page))
    errors.extend(check_sitemap())
    if errors:
        print(f"Site checks failed with {len(errors)} issue(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Site checks passed for {len(PUBLIC_HTML)} HTML pages and sitemap.xml.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
