#!/usr/bin/env python3
"""Build the Lobpreis static songbook site.

Inputs:
  chordpro_files/*.cho   — source of truth for song content
  site/*                 — handwritten templates and assets

Output:
  dist/                  — fully self-contained static site

Pure stdlib. Run with: python3 scripts/build_site.py
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import sys
import unicodedata
import zlib
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "chordpro_files"
SITE = ROOT / "site"
DIST = ROOT / "dist"


# ───────────────────────────────────────────────────────────── string helpers

def slugify(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "song"


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


# ───────────────────────────────────────────────────────────── chordpro parser

CHORD_RE = re.compile(r"\[([^\]]+)\]")
TITLE_RE = re.compile(r"^\{title:\s*(.*?)\s*\}\s*$")
NEWSONG_RE = re.compile(r"^\{new_song\}\s*$")


def parse_cho(text: str) -> list[dict]:
    """Return [{title, lines}]. A line is either [] (blank) or [(chord|None, text), …]."""
    songs: list[dict] = []
    cur: dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if NEWSONG_RE.match(line):
            continue
        m = TITLE_RE.match(line)
        if m:
            cur = {"title": m.group(1).strip(), "lines": []}
            songs.append(cur)
            continue
        if cur is None:
            continue
        if not line.strip():
            cur["lines"].append([])
            continue
        cur["lines"].append(parse_chord_line(line))
    for s in songs:
        while s["lines"] and not s["lines"][-1]:
            s["lines"].pop()
    return songs


def parse_chord_line(line: str) -> list[tuple[str | None, str]]:
    """Each chord 'owns' the text up to the next chord."""
    raw_chunks: list[tuple[str | None, str]] = []
    pos = 0
    for m in CHORD_RE.finditer(line):
        if m.start() > pos:
            raw_chunks.append((None, line[pos:m.start()]))
        raw_chunks.append((m.group(1), ""))
        pos = m.end()
    if pos < len(line):
        raw_chunks.append((None, line[pos:]))

    merged: list[tuple[str | None, str]] = []
    i = 0
    while i < len(raw_chunks):
        chord, text = raw_chunks[i]
        if chord is None:
            merged.append((None, text))
            i += 1
            continue
        j = i + 1
        buf = ""
        while j < len(raw_chunks) and raw_chunks[j][0] is None:
            buf += raw_chunks[j][1]
            j += 1
        merged.append((chord, buf))
        i = j
    return merged


# ───────────────────────────────────────────────────────────── HTML rendering

SYL_SPLIT_RE = re.compile(r"^(\S*)([\s\S]*)$")


def render_song(title: str, anchor: str, lines: list) -> str:
    out: list[str] = []
    out.append(f'<article class="song" id="{escape(anchor, quote=True)}">')
    out.append(f'  <h2>{escape(title)}</h2>')
    out.append('  <div class="lyrics">')
    for line in lines:
        if not line:
            out.append('    <p class="line blank"></p>')
            continue
        parts: list[str] = []
        for chord, text in line:
            if chord is None:
                parts.append(escape(text))
            else:
                m = SYL_SPLIT_RE.match(text)
                syl = m.group(1) if m else ""
                rest = m.group(2) if m else ""
                syl_html = escape(syl) if syl else "&nbsp;"
                parts.append(
                    f'<span class="syl"><span class="chord">{escape(chord)}</span>{syl_html}</span>'
                )
                if rest:
                    parts.append(escape(rest))
        out.append('    <p class="line">' + "".join(parts) + '</p>')
    out.append('  </div>')
    out.append('</article>')
    return "\n".join(out)


def render_grouped_index(flat: list[dict]) -> str:
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for e in flat:
        letter = (fold(e["title"])[:1] or "#").upper()
        if letter not in groups:
            groups[letter] = []
            order.append(letter)
        groups[letter].append(e)
    out: list[str] = []
    for L in order:
        out.append(f'    <section class="letter"><h2>{escape(L)}</h2><ul>')
        for e in groups[L]:
            out.append(
                f'      <li><a href="{escape(e["href"], quote=True)}">{escape(e["title"])}</a></li>'
            )
        out.append('    </ul></section>')
    return "\n".join(out)


# ───────────────────────────────────────────────────────────── PNG icon rendering

def write_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    stride = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += pixels[y * stride : (y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    path.write_bytes(sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def render_icon(size: int, *, maskable: bool = False) -> bytes:
    bg = bytes((250, 245, 236, 255))
    fg = bytes((184, 85, 31, 255))
    transparent = bytes((0, 0, 0, 0))

    if maskable:
        radius = 0
        scale = 0.8
        offset = 0.1 * size
    else:
        radius = size * 96 // 512
        scale = 1.0
        offset = 0.0

    # Per-row [xmin, xmax] for the rounded square.
    ranges: list[tuple[int, int]] = []
    for y in range(size):
        if radius == 0:
            ranges.append((0, size - 1))
            continue
        if y < radius:
            dy = radius - y
            disc = radius * radius - dy * dy
            if disc < 0:
                ranges.append((size, -1))
                continue
            inset = int(radius - disc ** 0.5)
            ranges.append((inset, size - 1 - inset))
        elif y >= size - radius:
            dy = y - (size - 1 - radius)
            disc = radius * radius - dy * dy
            if disc < 0:
                ranges.append((size, -1))
                continue
            inset = int(radius - disc ** 0.5)
            ranges.append((inset, size - 1 - inset))
        else:
            ranges.append((0, size - 1))

    # L coords from source SVG viewBox 0..512.
    def fx(v: float) -> float:
        return offset + (v / 512.0) * scale * size
    lx0, lx1, lx2 = fx(170), fx(230), fx(380)
    ly0, ly1, ly2 = fx(110), fx(360), fx(410)

    stride = size * 4
    out = bytearray(size * stride)
    for y in range(size):
        xmin, xmax = ranges[y]
        if xmin > xmax:
            # row entirely transparent (already zero-filled)
            continue
        row = bytearray(stride)
        row[xmin * 4:(xmax + 1) * 4] = bg * (xmax - xmin + 1)

        # Vertical bar of L
        if ly0 <= y < ly2:
            a = max(xmin, int(lx0))
            b = min(xmax + 1, int(lx1))
            if a < b:
                row[a * 4:b * 4] = fg * (b - a)
        # Horizontal foot of L
        if ly1 <= y < ly2:
            a = max(xmin, int(lx0))
            b = min(xmax + 1, int(lx2))
            if a < b:
                row[a * 4:b * 4] = fg * (b - a)

        out[y * stride:(y + 1) * stride] = row
    return bytes(out)


# ───────────────────────────────────────────────────────────── main build

def main() -> int:
    if not SRC.is_dir():
        print(f"missing source dir: {SRC}", file=sys.stderr)
        return 1
    if not SITE.is_dir():
        print(f"missing site dir: {SITE}", file=sys.stderr)
        return 1

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "song").mkdir()

    index_tpl = (SITE / "index.template.html").read_text(encoding="utf-8")
    song_tpl = (SITE / "song.template.html").read_text(encoding="utf-8")
    sw_tpl = (SITE / "sw.template.js").read_text(encoding="utf-8")

    # 1. Parse all .cho files.
    pages = []
    for path in sorted(SRC.glob("*.cho")):
        text = path.read_text(encoding="utf-8")
        songs = parse_cho(text)
        if not songs:
            print(f"warn: no songs in {path.name}", file=sys.stderr)
            continue
        file_slug = slugify(path.stem.replace("_", "-"))
        seen: set[str] = set()
        for s in songs:
            base = slugify(s["title"])
            anchor = base
            n = 2
            while anchor in seen:
                anchor = f"{base}-{n}"
                n += 1
            seen.add(anchor)
            s["anchor"] = anchor
        pages.append({"file_slug": file_slug, "songs": songs, "src": path.name})

    # Detect slug collisions across source files.
    by_slug: dict[str, list[str]] = {}
    for p in pages:
        by_slug.setdefault(p["file_slug"], []).append(p["src"])
    for slug, sources in by_slug.items():
        if len(sources) > 1:
            print(f"warn: slug '{slug}' collides for: {sources}", file=sys.stderr)

    # 2. Render each song page (one HTML per source file, all songs stacked).
    for page in pages:
        out_dir = DIST / "song" / page["file_slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        page_title = " / ".join(s["title"] for s in page["songs"])
        body = "\n".join(
            render_song(s["title"], s["anchor"], s["lines"]) for s in page["songs"]
        )
        html = (song_tpl
                .replace("{{TITLE}}", escape(page_title))
                .replace("{{SONGS_HTML}}", body))
        (out_dir / "index.html").write_text(html, encoding="utf-8")

    # 3. Flat list of all songs for index + search index. Each .cho file lists
    # its primary song first, with translations as secondary entries; those
    # secondary titles each have their own .cho where they're primary, so
    # listing only primaries gives every unique title exactly once.
    flat: list[dict] = []
    for page in pages:
        s = page["songs"][0]
        flat.append({"title": s["title"], "href": f"/song/{page['file_slug']}/"})
    flat.sort(key=lambda e: (fold(e["title"]), e["title"]))

    # 4. Index page.
    songlist_html = render_grouped_index(flat)
    songs_json = json.dumps(flat, ensure_ascii=False, separators=(",", ":"))
    idx_html = (index_tpl
                .replace("{{SONGLIST}}", songlist_html)
                .replace("{{SONGS_JSON}}", songs_json))
    (DIST / "index.html").write_text(idx_html, encoding="utf-8")

    # 5. Standalone songs.json (also useful outside the page).
    (DIST / "songs.json").write_text(songs_json + "\n", encoding="utf-8")

    # 6. Copy assets, manifest, icon.svg.
    shutil.copytree(SITE / "assets", DIST / "assets", dirs_exist_ok=True)
    shutil.copy(SITE / "manifest.webmanifest", DIST / "manifest.webmanifest")
    shutil.copy(SITE / "icon.svg", DIST / "icon.svg")

    # 7. Render PNG icons.
    print("rendering icons…", flush=True)
    write_png(DIST / "icon-192.png", 192, 192, render_icon(192))
    write_png(DIST / "icon-512.png", 512, 512, render_icon(512))
    write_png(DIST / "icon-512-maskable.png", 512, 512, render_icon(512, maskable=True))

    # 8. Service worker: precache + content-hashed cache name.
    files = sorted(p for p in DIST.rglob("*") if p.is_file() and p.name != "sw.js")
    rels: list[str] = []
    h = hashlib.sha256()
    for p in files:
        rel = "/" + str(p.relative_to(DIST)).replace("\\", "/")
        # navigation URLs use trailing slash, not /index.html
        if rel.endswith("/index.html"):
            rel = rel[:-len("index.html")]
        rels.append(rel)
        h.update(rel.encode("utf-8"))
        h.update(p.read_bytes())
    rels = sorted(set(rels))
    cache_name = "lobpreis-v" + h.hexdigest()[:12]
    sw = (sw_tpl
          .replace("__CACHE_NAME__", cache_name)
          .replace("__FILES_JSON__", json.dumps(rels, separators=(",", ":"))))
    (DIST / "sw.js").write_text(sw, encoding="utf-8")

    print(f"built {len(pages)} pages, {len(flat)} songs → dist/  ({cache_name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
