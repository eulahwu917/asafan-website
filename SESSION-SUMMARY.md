# ASAFAN Website Upgrade — Session Summary

## Project Overview
Complete rebuild of asafan.com.br — from a Locaweb "Criador de Sites" template to a modern, professional static website. Pure HTML/CSS/JS, no frameworks, ready for FTP upload to Locaweb shared hosting.

---

## What Was Done

### 1. Content Scraping & Reference
- Scraped all 8 pages of asafan.com.br via curl (SSL cert issues blocked WebFetch)
- Extracted all text, navigation, images, contact info, form fields
- Saved as `REFERENCE.md`

### 2. Design System (via /design-consultation)
- Researched B2B industrial competitors (Siemens, ABB, Twin City Fan, Aerovent)
- Created complete design system saved in `DESIGN.md`
- Generated visual preview page for approval
- **Key design decisions:**
  - **Fonts:** Satoshi (display, 900/700) + DM Sans (body, 400-700) — replaces generic Inter
  - **Colors:** #0F1A3E deepened navy, #C8102E refined red, #F7F8FA warm gray surfaces
  - **Aesthetic:** Industrial/Utilitarian with Luxury touches — "Siemens meets Swiss design studio"
  - **Grain texture** on hero, page headers, and tagline sections
  - Hero title: sentence case at 3rem Satoshi 900 (matches Siemens/ABB/Schneider pattern)

### 3. Assets
- **Logo:** Upscaled to 1080×1080 with transparent background (from user's `assets_upgrade`)
- **Partner logos:** 6 individual PNGs (Schindler, Schulz, Mercedes-Benz, Mundial SA, Faber-Castell, ELVI) — displayed in grayscale row, color on hover
- **Product/spec sheet images:** White background versions from user (raw assets pending)
- **Hero video:** `hero-video.mp4` — aerial Amazon forest footage with translucent navy overlay
- **All images served locally** — no external image dependencies

### 4. Website Pages

| Page | File | Key Features |
|------|------|-------------|
| Home | `index.html` | Video hero, product showcase cards (320px tall), tagline, partners row, CTA |
| Nossa História | `quem-somos.html` | Rewritten professional Portuguese copy, CTA |
| Produtos | `produtos.html` | Large showcase cards (same as homepage), subtitle only (no duplicate heading) |
| Microventiladores | `microventiladores.html` | 2-column spec sheet gallery on white bg with padding |
| Axiais | `axiais.html` | Same gallery layout |
| Acessórios | `acessorios.html` | Same gallery layout |
| Entre em Contato | `fale-conosco.html` | Contact info + form + Google Maps embed |
| Trabalhe na ASAFAN | `carreira.html` | Career form with Sexo dropdown (M/F/Prefiro não informar) |

### 5. Copy Polish (Portuguese)
- Full professional Portuguese pass across all pages
- Fixed grammar issues ("seguimento" → "segmento")
- More professional tone: "Dúvidas?" → "Precisa de ajuda com seu projeto?"
- "E-mail Reclamações" → "SAC / Pós-venda"
- "Veja Mais" → "Ver detalhes"
- Page headers match content (no duplicate headings)
- Breadcrumbs removed from all inner pages

---

## File Structure
```
asafan-website-upgrade/
├── index.html                  # Homepage
├── quem-somos.html             # About / History
├── produtos.html               # Products overview
├── microventiladores.html      # Microventilators catalog
├── axiais.html                 # Axial fans catalog
├── acessorios.html             # Accessories catalog
├── fale-conosco.html           # Contact + Google Maps
├── carreira.html               # Careers + application form
├── css/
│   └── style.css               # Complete design system stylesheet
├── js/
│   └── main.js                 # Mobile menu + mailto form handlers
├── assets/
│   ├── logo.png                # 1080×1080 transparent bg (upscaled)
│   ├── logo-white.png          # White background version
│   ├── favicon.png
│   ├── hero-video.mp4          # Aerial forest footage
│   ├── hero-bg.jpg             # Video poster/fallback
│   ├── cta-bg.jpg              # CTA section background
│   ├── contact-bg.jpg
│   ├── partner-*.png           # 6 individual partner logos
│   ├── microventiladores-thumb.png
│   ├── axiais-thumb.png
│   ├── acessorios-thumb.png
│   ├── micro-*.png             # 6 spec sheets
│   ├── axiais-*.png            # 6 spec sheets
│   └── acessorios-*.png        # 2 spec sheets
├── assets_upgrade/             # Source upgraded assets (can delete after deploy)
├── REFERENCE.md                # Original site content reference
├── DESIGN.md                   # Design system documentation
└── SESSION-SUMMARY.md          # This file
```

---

## Deployment

### To deploy on Locaweb:
1. Upload all files (HTML, css/, js/, assets/) to `public_html` via FTP
2. Do NOT upload: `assets_upgrade/`, `REFERENCE.md`, `DESIGN.md`, `SESSION-SUMMARY.md`, `.claude/`, `.gstack/`
3. No build step needed — everything is static

### External dependencies (CDN):
- Google Fonts: DM Sans
- Fontshare: Satoshi
- Google Maps embed iframe

### Forms:
- Both forms use `mailto:` links (no server-side backend)
- Sends to `comercial@asafan.com.br`
- For proper form handling, consider adding a PHP mailer or Formspree later

---

## Still TODO / Future Improvements
- [ ] Get raw product images with transparent backgrounds (user needs original assets)
- [ ] Consider PHP contact form for better UX than mailto
- [ ] Add WhatsApp floating button (common for Brazilian B2B)
- [ ] SEO: add structured data (LocalBusiness schema)
- [ ] Performance: compress hero-video.mp4 (currently ~9.6MB)
- [ ] Consider adding a product PDF download section
- [ ] Favicon: update to match new upscaled logo
