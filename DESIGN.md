# Design System — ASAFAN

## Product Context
- **What this is:** Corporate website for a B2B industrial ventilation supplier
- **Who it's for:** Engineers, procurement managers, and industrial buyers in Brazil
- **Space/industry:** Industrial ventilation equipment (fans, microventilators, accessories)
- **Project type:** Marketing site with product catalog (pure HTML/CSS/JS, no frameworks)

## Aesthetic Direction
- **Direction:** Industrial/Utilitarian with Luxury touches
- **Decoration level:** Intentional — subtle grain texture on hero, thin accent lines as dividers
- **Mood:** Precise, confident, trustworthy. Siemens meets a Swiss design studio. Modern but not trendy — this is equipment that runs 50,000 hours, and the site should feel equally reliable.
- **Reference sites:** tcf.com, aerovent.com, pennfan.com (category baseline to surpass)

## Typography
- **Display/Hero:** Satoshi (900, 700) — geometric, confident, modern. Not the overused Inter/Poppins. Gives a premium feel most industrial competitors lack.
- **Body:** DM Sans (400, 500, 600, 700) — clean, excellent readability, good tabular-nums support
- **UI/Labels:** DM Sans 600, uppercase, letter-spacing: 0.03em
- **Data/Tables:** DM Sans with font-variant-numeric: tabular-nums — aligns numbers perfectly in spec sheets
- **Code:** Not needed for this project
- **Loading:** Satoshi via Fontshare CDN, DM Sans via Google Fonts
- **Scale:**
  - Hero: 3rem / 48px (Satoshi 900, letter-spacing: -0.02em)
  - H1: 2.25rem / 36px (Satoshi 700)
  - H2: 1.75rem / 28px (Satoshi 700)
  - H3: 1.15rem / 18px (Satoshi 700, uppercase)
  - Body: 1rem / 16px (DM Sans 400)
  - Body large: 1.1rem / 17.6px (DM Sans 400)
  - Small/Label: 0.8rem / 12.8px (DM Sans 600, uppercase, tracking wide)
  - Micro: 0.7rem / 11.2px (DM Sans 600, uppercase, tracking wider)

## Color
- **Approach:** Restrained — navy dominates, red is reserved for CTAs and accent moments
- **Primary:** #0F1A3E — deepened navy, sophisticated (usage: headers, hero, footer, primary buttons)
- **Primary Light:** #1A2555 — hover states, secondary surfaces
- **Accent:** #C8102E — refined red, precision not emergency (usage: CTAs, links, active states)
- **Accent Hover:** #A80D25 — darkened for hover
- **Surface:** #F7F8FA — warm gray, not stark white (usage: page background, alternating sections)
- **Surface Dark:** #1A1F35 — rich dark (usage: footer, hero overlay)
- **White:** #FFFFFF — card backgrounds, input backgrounds
- **Text:** #2D3142 — softer than pure black
- **Text Light:** #6B7186 — secondary text, descriptions
- **Text Muted:** #9CA0B0 — placeholders, labels
- **Border:** #E2E5EB — subtle separation
- **Semantic:** success #0D7C3E, warning #B45309, error #C8102E, info #1D6FC0

## Spacing
- **Base unit:** 8px
- **Density:** Comfortable — generous whitespace signals confidence
- **Scale:** 2xs(2px) xs(4px) sm(8px) md(16px) lg(24px) xl(32px) 2xl(48px) 3xl(64px) 4xl(80px)
- **Section padding:** 80px vertical (desktop), 56px (mobile)
- **Container max-width:** 1120px
- **Container padding:** 24px horizontal

## Layout
- **Approach:** Grid-disciplined
- **Grid:** 3 columns for product cards, 2 columns for spec sheets, 2 columns for contact (info + form)
- **Max content width:** 1120px
- **Border radius:** sm: 4px (inputs), md: 8px (buttons, cards), lg: 12px (large cards, panels), full: 9999px (badges, pills)

## Motion
- **Approach:** Minimal-functional — subtle entrance fades, smooth hovers. No bounce/spring.
- **Easing:** ease (general), ease-out (enters), ease-in (exits)
- **Duration:** hover: 0.2s, transitions: 0.25s, page-level: 0.3s
- **Effects:** Card hover: translateY(-3px) + shadow. Button hover: translateY(-1px) + shadow. Links: gap expansion.

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-05 | Initial design system created | Created by /design-consultation based on B2B industrial competitive research |
| 2026-04-05 | Satoshi for display instead of Inter | Premium differentiation — every competitor uses generic sans-serif |
| 2026-04-05 | Warm gray (#F7F8FA) surfaces | Less clinical than pure white, more premium feel |
| 2026-04-05 | Generous whitespace (80px sections) | Most industrial sites cram content. Breathing room signals confidence |
| 2026-04-05 | Video hero with grain overlay | Differentiates from static hero images competitors use |
