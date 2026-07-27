from __future__ import annotations

import re
from typing import Iterable, List


def split_paragraphs(text: str) -> List[str]:
    # Normalize line endings and split on blank lines
    parts = re.split(r"\n\s*\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def merge_to_chunks(paragraphs: Iterable[str], max_chars: int, overlap: int) -> List[str]:
    chunks: List[str] = []
    buf: List[str] = []
    buf_len = 0

    for p in paragraphs:
        # If a single paragraph is larger than max, hard-split by sentences
        if len(p) > max_chars:
            sentences = re.split(r"(?<=[。．.!?])\s+", p)
            p_parts: List[str] = []
            cur = ""
            for s in sentences:
                if not s:
                    continue
                if len(cur) + len(s) + 1 > max_chars and cur:
                    p_parts.append(cur)
                    cur = s
                else:
                    cur = (cur + " " + s).strip()
            if cur:
                p_parts.append(cur)
        else:
            p_parts = [p]

        for part in p_parts:
            if buf_len + len(part) + 2 > max_chars and buf:
                chunks.append("\n\n".join(buf))
                # overlap by characters from the end of the previous chunk
                if overlap > 0:
                    tail = chunks[-1][-overlap:]
                    buf = [tail, part]
                    buf_len = len(tail) + len(part) + 2
                else:
                    buf = [part]
                    buf_len = len(part)
            else:
                buf.append(part)
                buf_len += len(part) + 2

    if buf:
        chunks.append("\n\n".join(buf))

    return chunks

