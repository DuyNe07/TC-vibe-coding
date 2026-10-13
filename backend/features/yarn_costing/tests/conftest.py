"""Every test of the feature runs as a logged-in Phòng SO account unless it switches user (helpers.acting_as)."""

from collections.abc import Iterator

import pytest

from backend.core.current_user import set_current_user
from backend.features.yarn_costing.tests.helpers import SO_USER


@pytest.fixture(autouse=True)
def _logged_in_so() -> Iterator[None]:
    set_current_user(SO_USER)
    yield
    set_current_user(None)  # the user lives in a ContextVar: never leak it into other tests
