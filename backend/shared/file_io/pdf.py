"""PDF text extraction: ``pages = PdfTextReader().read(uploaded_file)`` -> list[str] (one per page)."""

from io import BytesIO

from pypdf import PdfReader

from backend.shared.file_io.base_file import BaseFileReader


class PdfTextReader(BaseFileReader[list[str]]):
    supported_extensions = (".pdf",)

    def _read(self, stream: BytesIO, extension: str) -> list[str]:
        return [(page.extract_text() or "").strip() for page in PdfReader(stream).pages]
