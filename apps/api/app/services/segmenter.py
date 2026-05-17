"""Heuristic clause segmenter.

Most contracts follow one of three layouts:

1. **Numbered clauses** — "1.", "1.1", "2.3.4", "(a)", "(i)". Numbers act as
   reliable anchors; we split on the line that starts with one.
2. **Section headings followed by paragraphs** — "TERMINATION.", "Liability:",
   etc. We treat an UPPERCASE / title-case line that ends in `.` or `:` as a
   heading.
3. **Free-form paragraphs** — pure prose like a privacy policy. We fall back to
   blank-line separated paragraphs and treat each as a clause.

This module is intentionally **regex-only** — Phase 3's LLM extractor will
refine boundaries. Doing it without LLM here keeps the $5 budget intact.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from app.models import Clause

_NUMBERED_LINE = re.compile(
    r"""
    ^                                       # start of line
    (?:                                     # one of:
        \d+(?:\.\d+){0,4}\.?\s+             #   1   |  1.1  |  2.3.4
      | \(\s?[ivxlcdm]+\s?\)\s+             #   (i) (ii) (iii)
      | \(\s?[a-zA-Z]\s?\)\s+               #   (a) (b) (c)
      | [a-zA-Z]\.\s+                       #   a.  b.  c.
    )
    """,
    re.VERBOSE | re.MULTILINE,
)

_HEADING_LINE = re.compile(
    r"^(?P<heading>[A-Z][A-Z0-9 \-/&]{2,80})(?:[\.:])\s*$",
    re.MULTILINE,
)

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")

MIN_CLAUSE_CHARS = 30
MAX_CLAUSE_CHARS = 4_000


@dataclass(frozen=True, slots=True)
class _Chunk:
    start: int
    end: int
    text: str


def _normalize(text: str) -> str:
    """Normalise line endings, collapse runs of spaces, but preserve newlines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing spaces per-line (don't collapse internal spacing — it
    # may be meaningful inside legal lists).
    return "\n".join(line.rstrip() for line in text.split("\n"))


def _segment_by_numbered(text: str) -> list[_Chunk]:
    matches = list(_NUMBERED_LINE.finditer(text))
    if len(matches) < 3:
        return []
    boundaries = [m.start() for m in matches] + [len(text)]
    chunks: list[_Chunk] = []
    for i, start in enumerate(boundaries[:-1]):
        end = boundaries[i + 1]
        body = text[start:end].strip()
        if len(body) >= MIN_CLAUSE_CHARS:
            chunks.append(_Chunk(start=start, end=end, text=body))
    return chunks


def _segment_by_heading(text: str) -> list[_Chunk]:
    matches = list(_HEADING_LINE.finditer(text))
    if len(matches) < 2:
        return []
    boundaries = [m.start() for m in matches] + [len(text)]
    chunks: list[_Chunk] = []
    for i, start in enumerate(boundaries[:-1]):
        end = boundaries[i + 1]
        body = text[start:end].strip()
        if len(body) >= MIN_CLAUSE_CHARS:
            chunks.append(_Chunk(start=start, end=end, text=body))
    return chunks


def _segment_by_paragraph(text: str) -> list[_Chunk]:
    chunks: list[_Chunk] = []
    offset = 0
    for para in _PARAGRAPH_SPLIT.split(text):
        body = para.strip()
        # Move the offset forward by the length of the original split chunk
        # (paragraph + separator). We can't recover that exactly post-split, so
        # we anchor to the first occurrence after `offset`.
        idx = text.find(body, offset) if body else -1
        if idx >= 0 and len(body) >= MIN_CLAUSE_CHARS:
            chunks.append(_Chunk(start=idx, end=idx + len(body), text=body))
            offset = idx + len(body)
    return chunks


def _truncate(chunks: list[_Chunk]) -> list[_Chunk]:
    """Hard-cap absurdly long clauses to keep token costs predictable."""
    out: list[_Chunk] = []
    for c in chunks:
        if len(c.text) <= MAX_CLAUSE_CHARS:
            out.append(c)
        else:
            out.append(_Chunk(start=c.start, end=c.start + MAX_CLAUSE_CHARS, text=c.text[:MAX_CLAUSE_CHARS]))
    return out


def segment(text: str) -> list[Clause]:
    """Return ordered, non-overlapping clauses extracted from `text`."""
    if not text or not text.strip():
        return []
    normalized = _normalize(text)

    chunks = _segment_by_numbered(normalized)
    if not chunks:
        chunks = _segment_by_heading(normalized)
    if not chunks:
        chunks = _segment_by_paragraph(normalized)

    chunks = _truncate(chunks)

    return [
        Clause(
            id=uuid.uuid4().hex,
            index=i,
            text=chunk.text,
            start_offset=chunk.start,
            end_offset=chunk.end,
        )
        for i, chunk in enumerate(chunks)
    ]
