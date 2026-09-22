"""Base class for builders (``builders/`` folder).

A builder CONVERTS between representations, without business decisions:
raw data / uploaded files -> models, models -> response DTOs, models -> generated files (xlsx, docx).
Inputs go to ``__init__``; ``build()`` returns the output.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TOutput = TypeVar("TOutput")


class BaseBuilder(ABC, Generic[TOutput]):
    @abstractmethod
    def build(self) -> TOutput:
        """Assemble and return the output."""
