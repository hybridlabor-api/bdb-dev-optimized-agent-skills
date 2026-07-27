import hashlib
from pathlib import Path


def iter_text_files(root: Path):
    exts = {".md", ".markdown", ".html", ".htm", ".txt"}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def stable_uid(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()  # nosec - non-crypto id

