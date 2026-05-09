# Lobpreis Songbook

Static, offline-capable songbook generated from ChordPro files. Pure-stdlib Python build, plain HTML/CSS/JS output, deployable to any static host.

## Edit content

`chordpro_files/*.cho` is the only source of truth. Edit a `.cho` file, then rebuild.

### ChordPro dialect

Only the subset actually used in the corpus:

- `{title: ...}` — song title.
- `{new_song}` — separator inside a multi-song file (rare; prefer `#include`, see below).
- `[Chord]` — inline chord marker; attaches to the syllable that follows.
- Blank lines separate stanzas.
- `#include other.cho` — inline another `.cho` file at this point. See below.

Anything else passes through as plain text. No transposition, no `{comment}`, no chord definitions.

### Translations via `#include`

A song with multiple language versions lives in **one `.cho` per language**. Each file holds its own lyrics and ends with an `#include` pointing to its translation:

```
chordpro_files/adoramos.cho        — Portuguese lyrics, ends with: #include du_bist_sieger.cho
chordpro_files/du_bist_sieger.cho  — German lyrics,     ends with: #include adoramos.cho
```

At build time, `#include` is expanded **once** — the included file's content is inlined where the directive sits. Nested `#include`s inside an included file are intentionally dropped, so mutual references between a translation pair don't recurse forever.

Result:

- Each language is the primary song of its own page (`/song/adoramos/`, `/song/du-bist-sieger/`).
- Both pages render both languages, stacked.
- The index lists each title exactly once, under its first letter.

To add a new translation pair: create both `.cho` files (each with its own `{title:}` and lyrics), and add an `#include` line at the bottom of each pointing at the other.

## Build

```sh
python3 scripts/build_site.py
```

Pure stdlib, no dependencies. Output goes to `dist/` (gitignored). The build is idempotent and fully reproducible from `chordpro_files/` + `site/`.

What the build does:

- Parses every `.cho` in `chordpro_files/`, expanding `#include`s.
- Renders one HTML page per source file under `dist/song/<slug>/index.html`. Multi-song pages stack each song as its own `<article>`.
- Generates `dist/index.html` (alphabetical index) and `dist/songs.json` (search payload). Both list each title once, linked to its primary page.
- Renders PNG app icons.
- Emits a service worker (`dist/sw.js`) with a content-hashed cache name and a precache list of every asset, for full offline support.

## Preview locally

```sh
python3 -m http.server --directory dist 8000
```

Open <http://localhost:8000>.

## Deploy

### Cloudflare Pages (current setup)

Git-connected build — push to the production branch and Cloudflare rebuilds and deploys:

- **Build command**: `python3 scripts/build_site.py`
- **Build output directory**: `dist`
- **Framework preset**: *None*
- **Python version**: defaults to 3.13 (CF v3 build image). Pin via `.python-version` or `PYTHON_VERSION` env var if needed.

`dist/` is **not** committed — Cloudflare regenerates it on every push. Other branches get preview URLs automatically.

### Any static host

Run the build locally (or in CI) and upload the contents of `dist/` to any HTTP server (S3 + CloudFront, Netlify, GitHub Pages, nginx, Caddy, …). No server-side logic; everything is static.

## Repository layout

```
chordpro_files/   ← source of truth (edit here)
site/             ← handwritten templates and assets
  index.template.html
  song.template.html
  manifest.webmanifest
  icon.svg
  sw.template.js
  assets/
    style.css
    app.js          ← theme / font-size / chord-toggle controls
    search.js       ← client-side index search
scripts/
  build_site.py     ← single build script (pure stdlib)
  md_to_txt.py      ← legacy: .md → chord-above-lyric .txt
  txt_to_chordpro.py← legacy: .txt → .cho
dist/             ← generated, gitignored
PLAN.md           ← original design notes
```

Only `chordpro_files/`, `site/`, and `scripts/build_site.py` are load-bearing for builds. `md_to_txt.py` and `txt_to_chordpro.py` are one-shot import tools kept around for reference.
