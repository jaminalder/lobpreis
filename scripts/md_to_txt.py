#!/usr/bin/env python3
"""Convert song .md files to chord-above-lyric .txt files in txt_files/.

Source preference per song:
  1. chords/md/<name>.md  (has inline [Chord] markers)
  2. <name>.md            (top-level, no chords) when no chord version exists

Skips: index.md, index_all.md, erstes.md.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOP = REPO_ROOT
CHORDS_MD = REPO_ROOT / "chords" / "md"
OUT = REPO_ROOT / "txt_files"

SKIP = {"index.md", "index_all.md", "erstes.md"}

CHORD_RE = re.compile(r"\[([^\]]+)\]")
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")


def transform_line(line: str) -> str:
    """Transform one source line to zero, one, or two output lines (joined by \\n).

    - `# Title` -> setext heading (`Title\\n----`).
    - Lines with `[Chord]` markers -> chord line above stripped lyric line.
    - Trailing markdown line-break double-spaces are removed.
    - Other lines pass through unchanged.
    """
    # Drop trailing whitespace (kills the markdown-double-space line break too).
    line = line.rstrip()

    m = TITLE_RE.match(line)
    if m:
        title = m.group(1).strip()
        return f"{title}\n{'-' * len(title)}"

    if "[" not in line:
        return line

    chords: list[tuple[int, str]] = []
    stripped_parts: list[str] = []
    pos = 0
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "[":
            j = line.find("]", i)
            if j == -1:
                stripped_parts.append(line[i:])
                break
            chords.append((pos, line[i + 1 : j]))
            i = j + 1
        else:
            stripped_parts.append(ch)
            pos += 1
            i += 1
    stripped = "".join(stripped_parts)

    if not chords:
        return stripped

    chord_line_chars: list[str] = []
    for col, name in chords:
        if len(chord_line_chars) < col:
            chord_line_chars.extend(" " * (col - len(chord_line_chars)))
        elif len(chord_line_chars) > 0:
            chord_line_chars.append(" ")
        chord_line_chars.extend(name)
    chord_line = "".join(chord_line_chars).rstrip()
    return f"{chord_line}\n{stripped}"


def transform_file(text: str) -> str:
    out_lines = [transform_line(ln) for ln in text.splitlines()]
    result = "\n".join(out_lines)
    if not result.endswith("\n"):
        result += "\n"
    return result


def pick_sources() -> list[tuple[str, Path]]:
    """Return list of (basename_without_ext, source_path)."""
    chord_files = {p.name: p for p in CHORDS_MD.glob("*.md")}
    top_files = {p.name: p for p in TOP.glob("*.md")}
    sources: dict[str, Path] = {}
    for name in chord_files:
        if name in SKIP:
            continue
        sources[name] = chord_files[name]
    for name, path in top_files.items():
        if name in SKIP:
            continue
        sources.setdefault(name, path)
    return sorted((Path(name).stem, path) for name, path in sources.items())


def main() -> int:
    if not CHORDS_MD.is_dir():
        print(f"missing: {CHORDS_MD}", file=sys.stderr)
        return 1
    OUT.mkdir(exist_ok=True)
    sources = pick_sources()
    for stem, path in sources:
        text = path.read_text(encoding="utf-8-sig")
        out_text = transform_file(text)
        out_path = OUT / f"{stem}.txt"
        out_path.write_text(out_text, encoding="utf-8")
    print(f"wrote {len(sources)} files to {OUT.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
