from __future__ import annotations

import os
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document


class UnsupportedFileTypeError(ValueError):
    pass


def _extract_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_pdf(path: Path) -> str:
    doc = fitz.open(str(path))
    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text"))
        return "\n".join(p for p in parts if p)
    finally:
        doc.close()


def _extract_docx(path: Path) -> str:
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(parts)


def extract_text(file_path: str | os.PathLike[str]) -> str:
    """
    Extract text from a file on disk.

    Supported: .txt, .pdf, .docx
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(str(path))

    suffix = path.suffix.lower()
    if suffix == ".txt":
        return _extract_txt(path)
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)

    raise UnsupportedFileTypeError(f"Unsupported file type: {suffix}")

