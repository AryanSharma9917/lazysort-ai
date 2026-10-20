import csv
import io
import json
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_text(path: Path, max_chars: int, max_file_bytes: int) -> str:
    if path.stat().st_size > max_file_bytes:
        return "[File exceeds extraction size limit]"
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".csv":
            raw = path.read_text(encoding="utf-8", errors="replace")
            rows = csv.reader(io.StringIO(raw))
            text = "\n".join(" | ".join(row) for row in rows)
        elif suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            text = json.dumps(data, ensure_ascii=False, indent=2)
        elif suffix == ".pdf":
            text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        elif suffix == ".docx":
            text = "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
        else:
            return ""
    except Exception as exc:
        return f"[Content extraction failed: {type(exc).__name__}]"
    return text[:max_chars]
