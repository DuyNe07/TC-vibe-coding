"""Base classes for file readers/writers. Readers accept bytes, a path, or an ``UploadedFileDTO``."""

from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import ClassVar, Generic, TypeVar

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import FileProcessingError

FileSource = UploadedFileDTO | bytes | str | Path
TOutput = TypeVar("TOutput")
TInput = TypeVar("TInput")


def read_source(source: FileSource) -> tuple[bytes, str]:
    """Return ``(content, filename)`` for any supported source."""
    if isinstance(source, UploadedFileDTO):
        return source.content, source.filename
    if isinstance(source, bytes):
        return source, ""
    path = Path(source)
    if not path.exists():
        raise FileProcessingError(f"File not found: {path}")
    return path.read_bytes(), path.name


class BaseFileReader(ABC, Generic[TOutput]):
    supported_extensions: ClassVar[tuple[str, ...]] = ()

    def read(self, source: FileSource) -> TOutput:
        content, filename = read_source(source)
        extension = Path(filename).suffix.lower()
        if filename and self.supported_extensions and extension not in self.supported_extensions:
            raise FileProcessingError(
                f"File type '{extension}' is not supported. Supported types: {', '.join(self.supported_extensions)}."
            )
        try:
            return self._read(BytesIO(content), extension)
        except FileProcessingError:
            raise
        except Exception as exc:
            raise FileProcessingError(f"Cannot read the file '{filename or 'upload'}': {exc}") from exc

    @abstractmethod
    def _read(self, stream: BytesIO, extension: str) -> TOutput: ...


class BaseFileWriter(ABC, Generic[TInput]):
    @abstractmethod
    def write(self, data: TInput) -> bytes:
        """Return the generated file content."""
