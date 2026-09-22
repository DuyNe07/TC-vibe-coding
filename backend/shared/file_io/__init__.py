"""File readers/writers. ALWAYS use these instead of calling openpyxl / python-docx / pypdf directly."""

from backend.shared.file_io.base_file import BaseFileReader, BaseFileWriter, FileSource, read_source
from backend.shared.file_io.excel import ExcelReader, ExcelWriter
from backend.shared.file_io.pdf import PdfTextReader
from backend.shared.file_io.word import WordContent, WordReader, WordTemplateRenderer, WordWriter

__all__ = [
    "BaseFileReader",
    "BaseFileWriter",
    "ExcelReader",
    "ExcelWriter",
    "FileSource",
    "PdfTextReader",
    "WordContent",
    "WordReader",
    "WordTemplateRenderer",
    "WordWriter",
    "read_source",
]
