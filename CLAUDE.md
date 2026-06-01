# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A collection of **self-contained, single-file animated HTML infographics**. Each
infographic is one `.html` file with all CSS (in `<style>`) and JavaScript (in
`<script>`) inlined — no build step, no package manager, no external runtime
dependencies. The accompanying `.gif` / `.png` files are static exports/renders
of the animation, used for sharing where live HTML can't run.

The existing example (on branch `claude/oil-reserve-hourglass-Cs9An`) is
`spr-hourglass.html`: an explainer on how long the U.S. Strategic Petroleum
Reserve would last, with `spr-hourglass.gif` (looping animation),
`spr-hourglass-full.gif` (full page with data), and `spr-hourglass-preview.png`.

## Working with the infographics

- **View/test:** open the `.html` file directly in a browser. There is nothing
  to build, install, or serve. There is no test or lint tooling.
- **Exports (`.gif` / `.png`):** these are generated artifacts, not source.
  No generator script is committed; regenerate them with an external screen/
  canvas capture tool when the animation changes, and keep them in sync.

## Infographic architecture

Each file follows the same internal structure — useful to know before editing:

- **Hardcoded data inline.** All figures (e.g. barrels, days, capacity) live
  directly in the markup and in JS constants near the top of the `<script>`
  (e.g. `TOTAL_BBL`, `TOTAL_DAYS`, `startFill`). Sources are cited in the
  `<footer>`. Updating numbers means editing both the visible text and the
  matching constants/`data-*` attributes so the animation stays consistent.
- **Two animation layers:**
  1. A `<canvas>` render loop driven by `requestAnimationFrame` — procedurally
     drawn (no images), using a normalized `progress` value (0→1) over a fixed
     `DURATION`, with particle systems (droplets/bubbles) and wavy gradient
     fills. Includes Replay/Pause controls.
  2. DOM **count-up** animations on `window load` that tween elements with the
     `.count` class up to their `data-to` target, plus CSS-transition bars
     sized from `data-w`.
- **Theming via CSS custom properties** declared in `:root` (`--bg0`, `--gold`,
  `--oil0`, etc.); reuse these variables rather than hardcoding colors.
- **Self-contained exports:** the canvas draws its own opaque background that
  matches the card, so frames capture cleanly for GIF/PNG export.

When adding a new infographic, mirror this single-file pattern: one `.html`
with inline styles/scripts, data and sources stated explicitly, and exported
preview assets alongside it.
