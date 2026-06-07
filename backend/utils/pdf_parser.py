"""PDF text extraction utility for Triage AI.

Provides a single public function, ``extract_text_from_pdf``, that accepts raw
PDF bytes and returns the concatenated text content of every page.  Encrypted
or malformed files are handled gracefully — the caller always receives a string
(empty on failure) rather than an exception.
"""

import io
import logging

from pypdf import PdfReader

logger = logging.getLogger("triage.backend.pdf_parser")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all readable text from a PDF document.

    Args:
        file_bytes: Raw bytes of the PDF file (e.g. the body of an uploaded
            attachment or a file read from disk).

    Returns:
        A single string containing the concatenated text of every page,
        separated by newline characters.  Returns an empty string when the PDF
        is encrypted, corrupted, or contains no extractable text.

    Raises:
        Nothing — all exceptions are caught and logged.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception:
        logger.exception("Failed to open PDF — file may be corrupted")
        return ""

    if reader.is_encrypted:
        logger.warning("PDF is encrypted and cannot be read without a password")
        return ""

    pages_text: list[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            logger.exception("Failed to extract text from PDF page")
            page_text = ""
        pages_text.append(page_text)

    return "\n".join(pages_text)