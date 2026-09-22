"""Every page (Home + every feature page) renders without errors on first load, with no data.

Uses Streamlit's headless AppTest, so broken pages are caught by scripts/check.py without a browser.
"""

import pytest
from streamlit.testing.v1 import AppTest

from frontend.core.registry import FeatureRegistry


def _render(feature_key: str, page_index: int) -> None:
    # Runs as a standalone Streamlit script: imports must stay inside the function.
    from frontend.core.registry import FeatureRegistry
    from frontend.core.router import Router, set_current_router
    from frontend.home.home_page import HomePage

    router = Router(FeatureRegistry.discover(), HomePage())
    set_current_router(router)
    router.navigation()
    if feature_key == "home":
        HomePage().run()
    else:
        router.entries_of(feature_key)[page_index].page_cls(feature_key).run()


PAGES = [("home", 0)] + [
    (manifest.key, index) for manifest in FeatureRegistry.discover().features for index in range(len(manifest.pages))
]


@pytest.mark.parametrize(("feature_key", "page_index"), PAGES)
def test_page_renders_without_errors(feature_key: str, page_index: int) -> None:
    app = AppTest.from_function(_render, args=(feature_key, page_index), default_timeout=60)
    app.run()
    where = f"page #{page_index} of '{feature_key}'"
    assert not app.exception, f"{where} raised: {[e.value for e in app.exception]}"
    errors = [e.value for e in app.error]
    assert not errors, (
        f"{where} shows an error on first load (no data): {errors}. "
        "Pages must render cleanly when nothing has been entered yet (see logs/app.log / the traceback)."
    )
