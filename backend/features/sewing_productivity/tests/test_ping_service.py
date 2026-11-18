"""The scaffold ping use case is gone: the controller exposes only the use cases of the business document."""

from backend.features.sewing_productivity import SewingProductivityController


def test_controller_has_one_method_per_use_case_and_no_ping() -> None:
    actions = SewingProductivityController.actions()
    assert "ping" not in actions
    assert len(actions) == 26
