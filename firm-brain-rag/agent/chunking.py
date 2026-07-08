"""
Splits an uploaded document into section-level chunks for embedding.

Tries markdown '##' section splitting first (works for .md/.txt written with
that structure); if that collapses to a single chunk on a reasonably long
document -- the common case for a real PDF export where headings aren't
literal '#' characters -- falls back to paragraph-based chunking instead of
embedding the whole document as one block.

Section-level chunking (rather than fixed-size windows) keeps each chunk
semantically whole -- e.g. the "Risks" section of a memo stays together --
which matters more for citation/answer quality than raw retrieval recall.
"""
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _split_sections(body: str) -> list[tuple[str, str]]:
    """Split a markdown body into (heading, section_text) pairs on '## ' headings."""
    parts = re.split(r"(?m)^## ", body)
    sections = []
    intro = parts[0].strip()
    if intro:
        title_match = re.match(r"(?m)^# (.+)$", intro)
        heading = title_match.group(1).strip() if title_match else "Overview"
        sections.append((heading, intro))
    for part in parts[1:]:
        lines = part.split("\n", 1)
        heading = lines[0].strip()
        text = lines[1].strip() if len(lines) > 1 else ""
        if text:
            sections.append((heading, f"## {heading}\n{text}"))
    return sections


def _chunk_by_paragraphs(text: str, max_words: int = 220) -> list[tuple[str, str]]:
    """Fallback chunker for documents with no markdown '##' structure --
    real-world PDFs (a memo exported from Word/Google Docs, for example)
    have headings as bold/larger font, not literal '#' characters, so
    `_split_sections` alone would treat the whole file as one chunk. This
    groups consecutive paragraphs up to `max_words` each instead, which is
    a reasonable default for retrieval even without section structure."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current, word_count = [], 0
    for para in paragraphs:
        w = len(para.split())
        if current and word_count + w > max_words:
            chunks.append((f"Part {len(chunks) + 1}", "\n\n".join(current)))
            current, word_count = [], 0
        current.append(para)
        word_count += w
    if current:
        chunks.append((f"Part {len(chunks) + 1}", "\n\n".join(current)))
    return chunks or [("Overview", text.strip())]


def chunk_uploaded_text(filename: str, text: str, extra_meta: dict[str, Any] | None = None) -> list[Chunk]:
    """Chunk a live-uploaded document into retrievable, citeable sections."""
    meta = {"source_file": filename, "doc_type": "uploaded", "company": "N/A"}
    if extra_meta:
        meta.update(extra_meta)

    sections = _split_sections(text)
    if len(sections) <= 1 and len(text.split()) > 300:
        sections = _chunk_by_paragraphs(text)

    chunks = []
    for i, (heading, section_text) in enumerate(sections):
        chunk_id = f"{filename}::{i}::{heading}"
        chunk_meta = {**meta, "section": heading}
        chunks.append(Chunk(chunk_id=chunk_id, text=section_text, metadata=chunk_meta))
    return chunks
