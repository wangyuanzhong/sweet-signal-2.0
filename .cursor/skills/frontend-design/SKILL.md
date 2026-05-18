---
name: frontend-design
description: >-
  Orchestrates distinctive, production-grade UI via design dimensions (typography,
  color, motion, spatial, backgrounds) and HTML/CSS implementation for Sweet Signal.
paths:
  - web/index.html
  - desktop_app/src/index.html
---

# Frontend design (Sweet Signal)

This project vendors the **frontend-design** skill pack (see `README.md` and `sub-skills/` in this folder). Source ZIP: `https://skillmd.ai/skills/frontend-design-324/download/` (SkillMD.ai, May 2026).

## When an agent edits UI here

Follow the skill’s **8-phase workflow** in order, but keep scope proportional to the task:

1. **Design thinking** — Purpose (test-tone UX), tone (macaron / soft electro), constraints (single HTML file, no framework), one memorable element (glass card + knob).
2. **Typography** — Keep existing Nunito + Quicksand pairing unless explicitly changing brand; preserve weight hierarchy for Hz readout vs labels.
3. **Color & theme** — Modes use **distinct macaron triads** on `html.theme-*`; avoid neon; keep WCAG-ish contrast on `--text-main` vs card.
4. **Motion** — Reuse existing easing; new transitions 150–280ms, ease-out / ease-in-out; no gratuitous 2s+ tweens.
5. **Spatial composition** — Align **mode panels** to the same vertical rhythm (knob stack height, center readout slot); use an 8-based spacing scale consistent with the file.
6. **Backgrounds & details** — Orbs + grain stay subtle; theme shifts orb hues with accents, not full redesign unless requested.
7. **Implementation** — Apply parallel edits to **`web/index.html`** and **`desktop_app/src/index.html`** (pywebview shell); keep behavior JS intact.
8. **Validation** — Toggle all three modes; confirm no layout shift in knob column; confirm theme variables resolve (no missing `var()`). **Controls row:** in a column `flex` layout, never put `flex: 1` on `.output-section` / `.volume-section` or the electro-only volume row will stretch taller than the `field-sliders-row` block; use fixed `height`/`max-height` with `--volume-row-height` instead.

## Tech note

Plain **HTML + CSS + JS** only. Prefer **CSS custom properties** on `html.theme-*` for mode theming. SVG gradients may use `stop-color: var(--token)` where supported (Chromium / WebKit).
