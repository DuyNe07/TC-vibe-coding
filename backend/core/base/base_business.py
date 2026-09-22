"""Base classes for business logic (``business/`` folder).

Business code is PURE: it receives models, returns models/values, raises ``BusinessRuleViolation``.
It never reads files, calls repositories, services or Streamlit.

* ``BaseBusinessRule`` - ONE rule from ``docs/business/<feature>.md`` (``code = "BR-01"``).
* ``BaseBusiness``     - groups the rules and calculations of one business capability.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar, Generic, TypeVar

from backend.core.base._generics import is_abstract
from backend.core.base.base_model import BaseValueObject
from backend.core.exceptions import BusinessRuleViolation, ConfigurationError
from backend.core.naming import RULE_CODE_PATTERN

TTarget = TypeVar("TTarget")


class RuleViolation(BaseValueObject):
    """Result of a failed rule. ``message`` is user-facing (Vietnamese)."""

    rule_code: str
    message: str
    field: str | None = None


class BaseBusinessRule(ABC, Generic[TTarget]):
    """One business rule. ``code`` MUST exist in the feature's business document."""

    code: ClassVar[str] = ""
    message: ClassVar[str] = ""
    field: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if is_abstract(cls):
            return
        if not RULE_CODE_PATTERN.match(cls.code):
            raise ConfigurationError(f"{cls.__name__}.code must look like 'BR-01' (got {cls.code!r})")
        if not cls.message:
            raise ConfigurationError(f"{cls.__name__}.message (Vietnamese, user-facing) is required")

    @abstractmethod
    def is_satisfied_by(self, target: TTarget) -> bool:
        """Return True when ``target`` respects the rule."""

    def describe_violation(self, target: TTarget) -> str:
        """Override to build a dynamic message (e.g. include the wrong value)."""
        return self.message

    def evaluate(self, target: TTarget) -> RuleViolation | None:
        if self.is_satisfied_by(target):
            return None
        return RuleViolation(rule_code=self.code, message=self.describe_violation(target), field=self.field)

    def check(self, target: TTarget) -> None:
        violation = self.evaluate(target)
        if violation is not None:
            raise BusinessRuleViolation([violation])


class BaseBusiness(ABC, Generic[TTarget]):
    """Business logic of one capability: owns its rules and domain calculations.

    Override ``rules()`` to declare the rules applied by ``collect_violations`` / ``ensure_valid``
    and add domain methods (calculations, decisions, state transitions).
    """

    def rules(self) -> Sequence[BaseBusinessRule[TTarget]]:
        return ()

    def collect_violations(
        self, target: TTarget, rules: Sequence[BaseBusinessRule[TTarget]] | None = None
    ) -> list[RuleViolation]:
        active = self.rules() if rules is None else rules
        return [v for rule in active if (v := rule.evaluate(target)) is not None]

    def is_valid(self, target: TTarget) -> bool:
        return not self.collect_violations(target)

    def ensure_valid(self, target: TTarget) -> None:
        violations = self.collect_violations(target)
        if violations:
            raise BusinessRuleViolation(violations)
