"""App branding (framework): browser-tab icon and UI logo, loaded from ``frontend/public/``.

* ``frontend/public/logo.png``    -> browser tab icon (padded to a square so it is never stretched)
* ``frontend/public/Logo_TC.png`` -> logo shown in the UI (sidebar), scaled by height, width keeps the ratio
Replace the files to rebrand; keep the names. Missing files fall back to an emoji / text.
"""

from functools import lru_cache
from pathlib import Path

import streamlit as st
from PIL import Image

PUBLIC_DIR = Path(__file__).resolve().parents[1] / "public"
FAVICON_PATH = PUBLIC_DIR / "logo.png"
LOGO_PATH = PUBLIC_DIR / "Logo_TC.png"
FALLBACK_ICON = "🧵"


@lru_cache
def page_icon() -> Image.Image | str:
    """Square version of logo.png for ``st.set_page_config(page_icon=...)``."""
    if not FAVICON_PATH.exists():
        return FALLBACK_ICON
    with Image.open(FAVICON_PATH) as source:
        image = source.convert("RGBA")
    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2), image)
    return canvas


def show_logo() -> None:
    """Logo_TC.png at the top of the sidebar (``st.logo``: also shown when the sidebar is collapsed)."""
    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), size="large", icon_image=str(FAVICON_PATH) if FAVICON_PATH.exists() else None)
