"""App branding (framework): browser-tab icon and UI logo, loaded from ``frontend/public/``.

* ``frontend/public/logo.png``    -> browser tab icon (padded to a square so it is never stretched)
* ``frontend/public/Logo_TC.png`` -> logo shown in the UI (sidebar), scaled by height, width keeps the ratio
Replace the files to rebrand; keep the names. Missing files fall back to an emoji / text.
"""

import base64
from functools import lru_cache
from pathlib import Path

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


@lru_cache
def logo_data_uri() -> str | None:
    """Logo_TC.png as a data URI for ``<img>`` (None when the file is missing)."""
    if not LOGO_PATH.exists():
        return None
    return "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
