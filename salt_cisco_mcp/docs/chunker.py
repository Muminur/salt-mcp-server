from __future__ import annotations

import re
from dataclasses import dataclass

from salt_cisco_mcp.docs.normalizer import PageMeta


@dataclass
class Chunk:
    text: str
    heading: str
    anchor: str
    token_count: int
    kind: str


def _token_count(text: str) -> int:
    return len(text.split())


def _split_large_paragraph(text: str, max_tokens: int) -> list[str]:
    """Split a single large paragraph by words when no paragraph breaks exist."""
    words = text.split()
    if len(words) <= max_tokens:
        return [text]
    result: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        result.append(" ".join(words[start:end]))
        start = end
    return result


def _split_section(section_text: str, max_tokens: int) -> list[str]:
    """Split a section at paragraph boundaries, respecting fenced code blocks."""
    if _token_count(section_text) <= max_tokens:
        return [section_text]

    paragraphs = re.split(r"\n\n+", section_text)
    result: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0
    fence_open = False

    for para in paragraphs:
        para_tokens = _token_count(para)
        # Check if this paragraph opens or closes a fence
        para_opens_fence = len(re.findall(r"^```", para, re.MULTILINE)) % 2 == 1

        if fence_open:
            # Must keep accumulating until fence closes
            current_parts.append(para)
            current_tokens += para_tokens
            if para_opens_fence:
                fence_open = False
        else:
            if current_tokens + para_tokens > max_tokens and current_parts:
                # Flush current chunk
                result.append("\n\n".join(current_parts))
                current_parts = [para]
                current_tokens = para_tokens
                if para_opens_fence:
                    fence_open = True
            else:
                current_parts.append(para)
                current_tokens += para_tokens
                if para_opens_fence:
                    fence_open = True

    if current_parts:
        result.append("\n\n".join(current_parts))

    if not result:
        return [section_text]

    # Further split any oversized individual chunks (e.g., single large paragraph)
    final: list[str] = []
    for chunk in result:
        if _token_count(chunk) > max_tokens:
            final.extend(_split_large_paragraph(chunk, max_tokens))
        else:
            final.append(chunk)
    return final


def chunk_page(markdown: str, meta: PageMeta, max_tokens: int = 512) -> list[Chunk]:
    if not markdown or not markdown.strip():
        return []

    # Split by headings (lines starting with #)
    heading_pattern = re.compile(r"^(#{1,6}\s+.+)$", re.MULTILINE)
    parts = heading_pattern.split(markdown)

    # parts is: [pre-heading-text, heading1, section1, heading2, section2, ...]
    sections: list[tuple[str, str]] = []  # (heading, body)

    current_heading = ""
    i = 0
    # Handle any text before first heading
    if parts and not heading_pattern.match(parts[0].strip()) and parts[0].strip():
        sections.append(("", parts[0].strip()))
        i = 1
    elif parts and not heading_pattern.match(parts[0].strip()):
        i = 1
    else:
        i = 0

    # Walk pairs: heading, body
    while i < len(parts):
        part = parts[i]
        if heading_pattern.match(part.strip()):
            current_heading = part.strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if current_heading or body:
                sections.append((current_heading, body))
            i += 2
        else:
            if part.strip():
                sections.append((current_heading, part.strip()))
            i += 1

    chunks: list[Chunk] = []
    chunk_index = 0

    for heading, body in sections:
        # Combine heading + body for token counting
        full_text = (heading + "\n\n" + body).strip() if heading else body
        if not full_text:
            continue

        sub_sections = _split_section(full_text, max_tokens)

        for sub in sub_sections:
            if not sub.strip():
                continue
            if chunk_index == 0:
                anchor = meta.anchor
            else:
                anchor = meta.anchor + "-" + str(chunk_index)

            chunks.append(Chunk(
                text=sub.strip(),
                heading=heading,
                anchor=anchor,
                token_count=_token_count(sub),
                kind=meta.kind,
            ))
            chunk_index += 1

    return chunks
