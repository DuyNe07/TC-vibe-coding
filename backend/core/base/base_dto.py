"""Base classes for DTOs: input/output of use cases, passed between pages and controllers (``dto/`` folder)."""

from enum import StrEnum
from pathlib import PurePath

from pydantic import ConfigDict, Field

from backend.core.base.base_model import BaseSchema
from backend.core.exceptions import InvalidInputError


class MimeType(StrEnum):
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    XLS = "application/vnd.ms-excel"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PDF = "application/pdf"
    CSV = "text/csv"
    JSON = "application/json"
    BINARY = "application/octet-stream"


class BaseDTO(BaseSchema):
    """Root of every DTO. Nested DTOs (e.g. a row inside a response) inherit this directly."""


class BaseRequestDTO(BaseDTO):
    """Input of ONE use case. Immutable. Name it ``<Action>Request``."""

    model_config = ConfigDict(frozen=True)


class BaseResponseDTO(BaseDTO):
    """Output of ONE use case. Immutable. Name it ``<Thing>Response`` (lists go inside a field)."""

    model_config = ConfigDict(frozen=True)


class EmptyRequest(BaseRequestDTO):
    """Request for use cases that take no input."""


class UploadedFileDTO(BaseDTO):
    """A file sent by the UI. The backend receives bytes, never a Streamlit object."""

    model_config = ConfigDict(frozen=True)

    filename: str = Field(min_length=1)
    content: bytes = Field(repr=False)
    mime_type: str | None = None

    @property
    def extension(self) -> str:
        return PurePath(self.filename).suffix.lower()

    @property
    def size_mb(self) -> float:
        return len(self.content) / (1024 * 1024)

    def ensure_valid(self, allowed_extensions: tuple[str, ...], max_size_mb: float | None = None) -> None:
        """Raise ``InvalidInputError`` if the extension or size is not allowed."""
        if self.extension not in allowed_extensions:
            raise InvalidInputError(
                f"File '{self.filename}' is not a valid file type. Please upload a file with one of the following extensions: {', '.join(allowed_extensions)}."
            )
        if not self.content:
            raise InvalidInputError(f"File '{self.filename}' is empty.")
        if max_size_mb is not None and self.size_mb > max_size_mb:
            raise InvalidInputError(f"File '{self.filename}' exceeds the maximum allowed size of {max_size_mb:g} MB.")


class FileDownloadDTO(BaseResponseDTO):
    """A generated file returned to the UI (rendered with a download button)."""

    filename: str = Field(min_length=1)
    content: bytes = Field(repr=False)
    mime_type: str = MimeType.BINARY
