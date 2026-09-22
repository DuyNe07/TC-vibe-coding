"""Base classes. Import them ONLY from here: ``from backend.core.base import BaseEntity, ...``."""

from backend.core.base.base_builder import BaseBuilder
from backend.core.base.base_business import BaseBusiness, BaseBusinessRule, RuleViolation
from backend.core.base.base_controller import BaseController
from backend.core.base.base_dto import (
    BaseDTO,
    BaseRequestDTO,
    BaseResponseDTO,
    EmptyRequest,
    FileDownloadDTO,
    MimeType,
    UploadedFileDTO,
)
from backend.core.base.base_model import BaseEntity, BaseValueObject, utc_now
from backend.core.base.base_repository import BaseRepository, InMemoryRepository, JsonFileRepository
from backend.core.base.base_service import BaseService

__all__ = [
    "BaseBuilder",
    "BaseBusiness",
    "BaseBusinessRule",
    "BaseController",
    "BaseDTO",
    "BaseEntity",
    "BaseRepository",
    "BaseRequestDTO",
    "BaseResponseDTO",
    "BaseService",
    "BaseValueObject",
    "EmptyRequest",
    "FileDownloadDTO",
    "InMemoryRepository",
    "JsonFileRepository",
    "MimeType",
    "RuleViolation",
    "UploadedFileDTO",
    "utc_now",
]
