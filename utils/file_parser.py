import io
import os
from typing import Union

from PyPDF2 import PdfReader
from docx import Document


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


class UnsupportedFileTypeError(Exception):
    pass


def _get_extension(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower()


def extract_text(file_storage) -> str:
    """
    Safely extract text from PDF, DOCX, DOC or TXT without saving to disk.
    Raises UnsupportedFileTypeError for others.
    """
    filename = file_storage.filename or ""
    ext = _get_extension(filename)

    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: {ext or 'unknown'}. Allowed: PDF, DOCX, DOC, TXT"
        )

    if ext == ".pdf":
        return _extract_from_pdf(file_storage)
    elif ext in {".docx", ".doc"}:
        return _extract_from_docx(file_storage)
    elif ext == ".txt":
        return _extract_from_txt(file_storage)
    else:
        # Shouldn't reach here due to ALLOWED_EXTENSIONS
        raise UnsupportedFileTypeError("Unsupported file type")


def _extract_from_pdf(file_storage) -> str:
    file_bytes = file_storage.read()
    reader = PdfReader(io.BytesIO(file_bytes))
    texts = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        texts.append(page_text)
    return "\n".join(texts).strip()


def _extract_from_docx(file_storage) -> str:
    file_bytes = file_storage.read()
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def _extract_from_txt(file_storage) -> str:
    data = file_storage.read()
    try:
        return data.decode("utf-8", errors="ignore").strip()
    except AttributeError:
        # if already str
        return str(data).strip()
