"""Error hierarchy. Raise ``AppError`` subclasses for every *expected* failure.

``message`` is shown to end users in the UI, so write it in Vietnamese and make it actionable.
Controllers let them propagate; ``BasePage`` catches them and shows ``message`` in the UI.
"""

from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import ValidationError as PydanticValidationError


class AppError(Exception):
    """Root of all handled errors. Subclass it; never raise bare ``Exception``."""

    code: ClassVar[str] = "APP_ERROR"
    default_message: ClassVar[str] = "Have an error in app."

    def __init__(self, message: str | None = None, *, details: Any = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class InvalidInputError(AppError):
    code = "INVALID_INPUT"
    default_message = "Input data is invalid."

    @classmethod
    def from_pydantic(cls, exc: PydanticValidationError) -> "InvalidInputError":
        errors = [
            {"field": ".".join(str(part) for part in err["loc"]) or "(root)", "message": err["msg"]}
            for err in exc.errors()
        ]
        summary = "; ".join(f"{e['field']}: {e['message']}" for e in errors[:5])
        return cls(f"Input data is invalid — {summary}", details=errors)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    default_message = "Entity not found."


class ConflictError(AppError):
    code = "CONFLICT"
    default_message = "Entity conflict."


class FileProcessingError(AppError):
    code = "FILE_ERROR"
    default_message = "Can not process file."


class BusinessRuleViolation(AppError):
    """Raised when one or more business rules (BR-xx) are violated."""

    code = "BUSINESS_RULE_VIOLATION"
    default_message = "Business rule violation."

    def __init__(self, violations: Sequence[Any] = (), message: str | None = None) -> None:
        self.violations = tuple(violations)
        if message is None and self.violations:
            message = "; ".join(getattr(v, "message", str(v)) for v in self.violations)
        details = [v.model_dump() if hasattr(v, "model_dump") else v for v in self.violations]
        super().__init__(message, details=details)


class ConfigurationError(Exception):
    """Developer mistake (wrong wiring / inheritance). Not shown as a friendly message; fix the code."""
