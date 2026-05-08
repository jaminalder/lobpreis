# Lobpreis Songbook

Static, offline-capable songbook generated from ChordPro files.

## Edit content

`chordpro_files/*.cho` is the only source of truth. Edit a `.cho` file, then rebuild.

## Build

```sh
python3 scripts/build_site.py
```

Pure stdlib, no dependencies. Output goes to `dist/`.

## Preview locally

```sh
python3 -m http.server --directory dist 8000
```

Open <http://localhost:8000>.

## Deploy

### Cloudflare Pages

- Build command: `python3 scripts/build_site.py`
- Build output directory: `dist`
- Framework preset: *None*

### Any static host

Upload the contents of `dist/` to any HTTP server (S3 + CloudFront, Netlify, GitHub Pages, nginx, Caddy, …).

## Repository layout

```
chordpro_files/   ← source of truth (edit here)
site/             ← handwritten templates and assets
scripts/
  build_site.py   ← single build script
dist/             ← generated, gitignored
PLAN.md           ← design notes
```
