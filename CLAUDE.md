# Agent notes

For project overview, ChordPro dialect, `#include` semantics, build invocation, and deployment, **read `README.md` first**. This file only adds things an agent needs that the README doesn't cover.

## Workflow

- After any change to `chordpro_files/*.cho`, `site/*`, or `scripts/build_site.py`, rerun `python3 scripts/build_site.py` before considering the task done. The build is fast (well under a second) and is the only way to know the output is still valid.
- For visual changes (CSS, template tweaks), preview by running `python3 -m http.server --directory dist 8000`. To verify in a real browser headlessly:
  ```sh
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --headless --disable-gpu --window-size=775,1100 \
    --screenshot=/tmp/page.png http://localhost:8000/song/<slug>/
  ```
  Then `Read` the PNG. This is the only reliable way to check chord/lyric layout — diffing CSS isn't enough because layout depends on inline-block + line-box interactions (see "CSS gotchas" below).
- Don't commit `dist/` — it's gitignored and Cloudflare Pages rebuilds it. If you find yourself diffing `dist/` to verify a change, you've forgotten to rebuild instead of inspecting the generated output directly.

## Source-file invariants

- Each `.cho` should contain **exactly one** primary song (one `{title:}` at the top). Translations are pulled in via `#include other.cho` at the bottom — never paste the same translation into two files. The index dedup logic relies on this: it lists only the first song of each `.cho`.
- `#include` expansion is one-level deep on purpose. If you ever need a third translation in the same chain, the current logic will silently drop the third file's directive. Adjust `expand_includes()` in `scripts/build_site.py` and add a cycle-tracking set if that requirement comes up.
- Slugs come from `slugify(title)` (lowercased, accents stripped, non-alnum → `-`). Two songs with the same title in the same `.cho` get `-2`, `-3` suffixes. Two `.cho` files with colliding stems print a warning but the build proceeds.

## CSS gotchas (chord/lyric layout)

The chord-above-lyric layout in `site/assets/style.css` is fragile:

- Each `<span class="syl">` is `display: inline-block` with `padding-top` reserving the chord band. The `<span class="chord">` is `position: absolute` inside it.
- `top` on `.chord` resolves against the chord's **own** font-size (`0.82em`), not the `.syl`'s. So `top: 1em` is smaller than you'd think. Calibrate by measuring, not by intuition.
- The layout has to look right both for the **first visual row** of a paragraph and for **wrapped rows**. They differ subtly because the first row's space-above-chord comes from the paragraph margin, while wrapped rows' space-above-chord is whatever the previous line box leaves. Always verify wrapping by forcing a narrow viewport (e.g. `--window-size=550,1100` with a large `--lyrics-size`).
- If you change `padding-top` on `.syl`, you almost certainly also need to retune `.chord { top: ... }`.

## Service worker

`dist/sw.js` is generated with a content-hashed cache name (`lobpreis-vXXXXXX`) and a precache list. Any change to any file in `dist/` produces a new hash, which invalidates clients on next visit. Don't hand-edit `dist/sw.js`; edit `site/sw.template.js` and rebuild.

## Things that are intentional, don't "fix" them

- The build wipes and recreates `dist/` every run. Yes, it's destructive; that's the simplest way to guarantee no stale files survive a rename.
- `flat` (the search index and homepage list) only contains the primary song of each `.cho`. The HTML pages still render every song in the file. The asymmetry is the whole point of the `#include` design.
- `parse_cho` ignores lines outside a `{title:}` block. A file without a title produces no songs and prints a warning — don't add titles to translation-only files; use `#include` instead.
