#!/usr/bin/env python3
"""Convert chord-above-lyric .txt song files to ChordPro .cho format.

Reads txt_files/*.txt and writes chordpro_files/*.cho.

Conversions:
  - Setext-style title (`Title` underlined with dashes) -> `{title: Title}`.
    Multi-song files get `{new_song}` between songs.
  - Chord line followed by lyric line -> chords inlined as [Chord] markers
    immediately before the syllable at the matching column.
  - Standalone chord-only lines (no lyric below) -> bracketed chord run,
    e.g. `[C] [G] [Am]`.
  - Plain lyric lines and blank lines pass through unchanged.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "txt_files"
OUT = REPO_ROOT / "chordpro_files"

# A chord token: root note (A-H, with optional # or b), then any combo of
# quality modifiers (m, M, maj, min, sus, add, dim, aug) and interval numbers,
# optional augmented '+', and optional slash-bass note. Examples that match:
#   C, Am, F#m, D7, Gmaj7, Cdim7/Eb, D/F#, Em7, A/C#, Bb, H, D+, Csus4, F#m7/A
# Examples that don't match: "All", "Adoramos", "Es", "Du", words generally.
CHORD_TOKEN_RE = re.compile(
    r"^\(?"
    r"[A-H][#b]?"
    r"(?:maj|min|sus|add|dim|aug|m|M|\d+)*"
    r"\+?"
    r"(?:/[A-H][#b]?(?:maj|min|sus|add|dim|aug|m|M|\d+)*)?"
    r"\)?"
    r"$"
)
TITLE_DASH_RE = re.compile(r"^-+$")


def is_chord_token(tok: str) -> bool:
    return bool(CHORD_TOKEN_RE.match(tok))


def is_chord_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    tokens = s.split()
    return all(is_chord_token(t) for t in tokens)


def merge_chords(chord_line: str, lyric_line: str) -> str:
    """Inline the chords from `chord_line` into `lyric_line` as [chord] markers."""
    chords: list[tuple[int, str]] = []
    i = 0
    while i < len(chord_line):
        if chord_line[i] == " ":
            i += 1
            continue
        start = i
        while i < len(chord_line) and chord_line[i] != " ":
            i += 1
        chords.append((start, chord_line[start:i]))

    if not chords:
        return lyric_line

    parts: list[str] = []
    last_pos = 0
    for col, name in chords:
        if col > len(lyric_line):
            col = len(lyric_line)
        if col < last_pos:
            col = last_pos
        parts.append(lyric_line[last_pos:col])
        parts.append(f"[{name}]")
        last_pos = col
    parts.append(lyric_line[last_pos:])
    return "".join(parts)


def chord_only_line(line: str) -> str:
    return " ".join(f"[{t}]" for t in line.split())


def convert_text(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    is_first_song = True
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # Setext title: "Title" then "----" on next line.
        if (
            i + 1 < n
            and line.strip()
            and TITLE_DASH_RE.match(lines[i + 1].strip())
        ):
            title = line.strip()
            if is_first_song:
                out.append(f"{{title: {title}}}")
                is_first_song = False
            else:
                while out and not out[-1].strip():
                    out.pop()
                out.append("")
                out.append("{new_song}")
                out.append(f"{{title: {title}}}")
            i += 2
            while i < n and not lines[i].strip():
                i += 1
            out.append("")
            continue

        # Chord line followed by a lyric -> inline.
        if is_chord_line(line) and i + 1 < n:
            nxt = lines[i + 1]
            nxt_s = nxt.strip()
            if (
                nxt_s
                and not is_chord_line(nxt)
                and not TITLE_DASH_RE.match(nxt_s)
            ):
                out.append(merge_chords(line, nxt))
                i += 2
                continue
            # Standalone chord run -> bracketed.
            out.append(chord_only_line(line))
            i += 1
            continue

        # Plain pass-through.
        out.append(line)
        i += 1

    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out) + "\n"


def main() -> int:
    if not SRC.is_dir():
        print(f"missing source dir: {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(exist_ok=True)
    count = 0
    for src in sorted(SRC.glob("*.txt")):
        text = src.read_text(encoding="utf-8")
        out_text = convert_text(text)
        dst = OUT / f"{src.stem}.cho"
        dst.write_text(out_text, encoding="utf-8")
        count += 1
    print(f"wrote {count} files to {OUT.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
