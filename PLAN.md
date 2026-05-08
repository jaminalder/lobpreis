# Lobpreis Songbook — Implementation Plan

A static, offline-capable songbook generated from ChordPro files. Built with Python, deployed as plain HTML/CSS/JS to Cloudflare Pages or any HTTP server.

## 1. Scope (locked)

**In:**
- Build-time generation from `chordpro_files/*.cho` → `dist/`
- One HTML page per source file (multi-song files render all songs stacked on one page)
- Searchable index (title substring match, plain JS, no library)
- Light / dark / system theme with manual toggle
- Adjustable lyrics font size
- Show/hide chords toggle
- Mobile-first responsive layout
- Progressive Web App, fully offline (service worker + manifest)
- Persists user preferences (theme, font size, chord visibility) in `localStorage`

**Out (v1):**
- Transposition
- Auto-scroll, metronome, audio playback
- Setlists / playlists / favorites
- In-browser editing
- User accounts
- Print stylesheet (can be added cheaply later)
- Per-song language metadata / language flags

## 2. Source of truth

`chordpro_files/*.cho` is the **only** editable source. Any content change → edit `.cho` → rerun build → all HTML, JSON, and the service-worker cache version are regenerated. The `dist/` directory is fully reproducible and never edited by hand.

## 3. ChordPro dialect supported

Only what's currently used in the corpus:

- `{title: ...}` — song title.
- `{new_song}` — separator inside a multi-song file.
- `[Chord]` — inline chord marker, attached to the syllable that follows.
- Blank lines separate stanzas.

Anything else passes through as plain text. No transposition, no `{comment}`, no chord definitions in v1.

## 4. Multi-song file handling

A file may contain N songs separated by `{new_song}`. **All songs in a file render on the same page**, in source order, because the user sings them together (typically the same song in different languages). The index lists every individual song title; multiple titles from the same file all link to the same page (with an optional hash anchor, see §6).

Example: `adoramos.cho` contains "Adoramos" (PT) and "Du bist Sieger" (DE). The index shows both entries; both link to `/song/adoramos/` (with anchors `#adoramos` and `#du-bist-sieger`).

## 5. Output file layout (`dist/`)

```
dist/
├── index.html                # search + alphabetical song list
├── song/
│   ├── adoramos/index.html   # one page per source file
│   ├── all-honour/index.html
│   └── …
├── assets/
│   ├── style.css
│   ├── app.js                # theme/font-size/chord-toggle, persistence
│   └── search.js             # index-page-only: search filter
├── songs.json                # search index (titles + slugs + anchors)
├── manifest.webmanifest
├── icon-192.png              # PWA icons (generated from SVG)
├── icon-512.png
├── icon.svg                  # source for icons + favicon
└── sw.js                     # service worker, cache-versioned by source hash
```

## 6. URL & slug scheme

- `/` — index.
- `/song/<slug>/` — song page. `<slug>` is the source filename stem with underscores → hyphens (e.g. `adoramos.cho` → `adoramos`, `du_grosser_gott.cho` → `du-grosser-gott`).
- For multi-song files, each song inside the page gets an `id` anchor derived from its title (slugified). The index links to `/song/<file-slug>/#<title-slug>` for non-first songs, `/song/<file-slug>/` for the first.

## 7. Build script: `scripts/build_site.py`

A single Python script (no third-party deps; stdlib only) that:

1. Loads every `.cho` from `chordpro_files/`.
2. Parses each file into a list of songs `[{title, blocks}]`, where `blocks` is a list of `{type: "stanza"|"blank", lines: [[chunks]]}` and each line is a list of `{chord?, text}` chunks.
3. Renders `dist/song/<slug>/index.html` per file using a small string template, embedding all songs in source order, each wrapped in `<section id="<title-slug>">`.
4. Renders `dist/index.html`: search box + alphabetical `<ul>` of `{title, href}` entries (one per song, including all titles inside multi-song files).
5. Writes `dist/songs.json`: `[{title, slug, anchor?}]`, sorted alphabetically (case-insensitive, diacritics-folded for sort key but display preserves diacritics).
6. Copies `assets/`, `manifest.webmanifest`, `icon.svg` from a source directory `site/` (handwritten, checked into the repo).
7. Generates `icon-192.png` and `icon-512.png` from `icon.svg` (using a tiny SVG-rasterization fallback — see §13).
8. Computes a SHA-256 over all source `.cho` files plus all asset files, and bakes the first 8 hex chars into `sw.js` as the cache name (`lobpreis-v<hash>`). This guarantees stale clients pick up changes on next load.
9. Generates a precache list inside `sw.js`: every emitted file under `dist/`.

Run locally: `python3 scripts/build_site.py`. Output: `dist/`.

### Parsing details

- **Title extraction:** regex `^\{title:\s*(.*?)\s*\}$`.
- **Song split:** `{new_song}` line creates a new song; the first song begins at file start.
- **Chord-line parsing:** scan each non-directive line for `[chord]` markers using regex; the text between markers is the run that "belongs to" the preceding chord (or to no chord, for the leading text before the first marker). Output a list of `{chord, text}` chunks per line.
- **Blank lines:** preserved as paragraph separators between stanzas.
- **Whitespace:** preserved verbatim within text runs.

## 8. HTML structure for a song page

Per song, inside the page:

```html
<article class="song" id="adoramos">
  <h2>Adoramos</h2>
  <div class="lyrics">
    <p class="line">
      <span class="syl"><span class="chord">G</span>Ador</span><span class="syl"><span class="chord">D</span>amos, </span>…
    </p>
    <p class="line">…</p>
    <!-- blank line in source = </div><div class="stanza"> boundary or just empty <p> -->
  </div>
</article>
```

**Chord placement (E=1, inline-block):**

- Each `.syl` is `display: inline-block; position: relative; padding-top: 1.2em` so the chord sits above without overlapping the previous syllable.
- `.chord` is `position: absolute; top: 0; left: 0; font-weight: bold` and styled in the accent color.
- Word wrapping: spaces between words are emitted as their own non-syllable text nodes (or as `.syl` with empty `.chord`) so the browser can wrap at word boundaries.
- Hide chords: `body.no-chords .chord { visibility: hidden }` and remove `padding-top` so the line collapses to plain lyrics height.

This degrades gracefully on narrow screens — long lines wrap at word boundaries and chords stay attached to their syllables.

## 9. Index page

Layout (J=1, simple alphabetical list with search at top):

```
[ Lobpreis logo / title ]
[ search input            ]   [ ☀/🌙 ] [ A−/A+ ] [ ♪ on/off ]
─────────
A
  Adoramos
  All honour
  As the mountains are around Jerusalem
B
  Bleibend ist deine Treu
  …
```

- Search input filters the list client-side: lowercase + diacritics-folded substring match against title. ~20 lines of JS in `search.js`.
- Letter group headings are `<h2>` elements; if all entries in a group are filtered out, hide the heading.
- The header controls (theme / font / chords) are global and persist on the song pages too.

## 10. Page chrome (header / controls)

Same header on every page:

- Title link → `/`
- Theme toggle: cycles **system → light → dark → system**. Initial: system. Persists in `localStorage` as `theme` (`"system"|"light"|"dark"`).
- Font size: A− / A+ buttons. Adjusts CSS variable `--lyrics-size` between e.g. `0.9rem` and `1.6rem` in 0.1rem steps. Persists as `fontSize`.
- Chord toggle: shows/hides chords by toggling `body.no-chords`. Persists as `chords` (`"on"|"off"`).
- All controls work without JS for the first paint (defaults applied via CSS); JS hydrates state from `localStorage` on load and wires up buttons.

To prevent FOUC on theme: a tiny inline `<script>` in `<head>` reads `localStorage.theme` and applies `data-theme` to `<html>` before stylesheet loads.

## 11. Styling (D=1, hand-written CSS)

Single `style.css`, ~3–5 KB. Uses CSS custom properties for theming.

**Color palette — warm, eye-friendly, good contrast:**

Light theme (cream / dark warm brown):
- `--bg: #faf5ec` (warm cream)
- `--fg: #2b211a` (warm near-black, AAA contrast on bg)
- `--muted: #6b5a4a`
- `--accent: #b8551f` (terracotta, for chords + links)
- `--rule: #e6dcc7`

Dark theme (deep warm brown / soft cream):
- `--bg: #1d1714`
- `--fg: #ece1cf`
- `--muted: #a89682`
- `--accent: #e09060` (warmer / lighter terracotta for dark bg)
- `--rule: #322822`

PWA `theme_color`: `#b8551f` (terracotta accent — visible on both themes).

Typography:
- System font stack: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` for UI.
- Lyrics: same stack but at `--lyrics-size` (default `1.1rem`). No web fonts (zero network cost).
- Chords: same stack, `font-weight: 700`, `--accent` color.

Layout:
- Single column, max-width ~720px, centered.
- Mobile-first: sticky header with controls on small screens (so toggles are always reachable). Larger screens get a wider line width and slightly more generous spacing.
- All paddings/spacings in `rem` so font-size scaling cascades naturally.

## 12. Persistence (`localStorage`)

Only three keys, all read on first paint:

- `theme`: `"system" | "light" | "dark"` (default `"system"`)
- `fontSize`: number, the rem value (default `1.1`)
- `chords`: `"on" | "off"` (default `"on"`)

Stored under namespace `lobpreis.*` to avoid collisions if served from a shared origin in the future.

## 13. PWA / offline (G=1, hand-written)

**`manifest.webmanifest`:**
```json
{
  "name": "Lobpreis",
  "short_name": "Lobpreis",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#faf5ec",
  "theme_color": "#b8551f",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icon.svg", "sizes": "any", "type": "image/svg+xml" }
  ]
}
```

**`sw.js` strategy:**
- On `install`: precache the full file list from `dist/` (the build embeds the list as a JS array).
- On `activate`: delete any cache whose name doesn't match the current `lobpreis-v<hash>`.
- On `fetch`: cache-first for same-origin GETs in the precache list; network-fallback for everything else.
- Cache name embeds the source-content hash so a content change forces a new cache and old caches are evicted on activate.

**Icons:**
- Hand-written `site/icon.svg` (a simple mark, e.g. stylized `L` or musical glyph in terracotta on cream).
- Build script rasterizes to 192×192 and 512×512 PNG. Implementation plan: try `cairosvg` if installed; otherwise fall back to a checked-in pre-rendered PNG pair so the build remains stdlib-only by default. (Decision deferred to first build; will check what's available.)

## 14. Search (C=1, plain JS, title-only)

`search.js` (loaded only on `/`):

```text
1. Read window.SONGS (inlined <script> with songs.json contents, or fetch).
2. On input: normalize query (lowercase + NFD strip combining marks).
3. Filter SONGS where normalized(title) includes normalized(query).
4. Re-render the <ul>; show "no matches" if empty.
```

Total: well under 50 lines. No fuzzy matching, no ranking — for ~90 entries substring is fast and predictable.

For diacritics: use `s.normalize("NFD").replace(/\p{M}/gu, "")` so "voce" matches "você", "ehre" matches "Ehre".

## 15. Cloudflare Pages / hosting

- **Build command:** `python3 scripts/build_site.py`
- **Output directory:** `dist`
- **Python version:** 3.11+ (Cloudflare Pages provides Python). Stdlib only by default; if PNG icon generation needs `cairosvg`, add a `requirements.txt`.
- Works identically with `python3 -m http.server --directory dist 8000` for local preview, or any static host (S3+CloudFront, Netlify, GH Pages, nginx, Caddy, etc.).

## 16. Repo structure after implementation

```
chordpro_files/        # source of truth (existing)
txt_files/             # legacy raw input (existing)
lobpreis_akkorde_photos/  # legacy photos (existing)
scripts/
  txt_to_chordpro.py   # existing
  md_to_txt.py         # existing
  build_site.py        # NEW
site/                  # NEW — handwritten static assets the build copies into dist/
  index.template.html
  song.template.html
  assets/
    style.css
    app.js
    search.js
  manifest.webmanifest
  icon.svg
  sw.template.js       # template; build injects cache name + precache list
dist/                  # NEW — generated, gitignored
PLAN.md                # this file
```

`.gitignore` will add `/dist/`.

## 17. Implementation order (proposed)

Each step is independently shippable and verifiable.

1. **Skeleton & parser**
   - Create `site/` with empty templates and a placeholder `style.css`.
   - Write `build_site.py` parser + song-page rendering. Verify output for `adoramos.cho`, `du_grosser_gott.cho`, and one single-song file.
2. **Index page**
   - Generate `index.html` with all titles and `songs.json`.
   - Plain-JS substring filter in `search.js`.
3. **Styling pass**
   - Write `style.css` with both themes, lyrics layout, mobile-first.
   - Verify chord-above-syllable on a few real songs at multiple widths.
4. **Header controls + persistence**
   - `app.js`: theme cycle, font-size buttons, chord toggle. Inline FOUC-prevention script in `<head>`.
5. **PWA**
   - `manifest.webmanifest`, `icon.svg`, icon rasterization step in build.
   - `sw.js` template + precache injection + content-hash cache name.
   - Verify Lighthouse "Installable" + offline reload after first visit.
6. **Polish & deploy**
   - `.gitignore` `/dist/`.
   - Smoke-test on a phone (or DevTools mobile emulation).
   - Document Cloudflare Pages settings in `README.md` (build command, output dir).

## 18. Acceptance checklist

- [ ] Edit a `.cho` file → rerun build → change visible on next load (cache busts via hash).
- [ ] All 75 source files render without error; titles in `index.html` match `{title:}` directives.
- [ ] Multi-song files (e.g. `adoramos`, `du_grosser_gott`) show all songs stacked on one page, both reachable from index by their respective titles.
- [ ] Search box filters titles instantly, diacritics-insensitive.
- [ ] Theme toggle cycles system/light/dark, persists, no flash on reload.
- [ ] Font size buttons resize lyrics, persist.
- [ ] Chord toggle hides chords without re-flowing layout awkwardly, persists.
- [ ] Site is fully usable on a 360 px viewport.
- [ ] After one online visit, the entire site loads with the device offline (airplane mode test).
- [ ] Lighthouse PWA: installable; Performance ≥ 95 on mobile; no JS framework warnings.
- [ ] Total transferred bytes for index page < ~30 KB gz; total cached site < ~500 KB.

## 19. Open / deferred

- Whether `cairosvg` is acceptable as a build dep, or we ship pre-rendered PNGs in `site/`. Defer to first build attempt; default to pre-rendered if it keeps the build stdlib-only.
- Whether to add a tiny `<details>` "About" block on the index (history, attribution). Not blocking.
