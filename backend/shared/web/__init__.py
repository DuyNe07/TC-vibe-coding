"""Read data from public web pages. ALWAYS use these instead of calling requests / lxml directly."""

from backend.shared.web.web_reader import (
    WEB_MAX_BYTES,
    WEB_TIMEOUT_SECONDS,
    WebFetchError,
    WebPage,
    fetch_file,
    fetch_page,
)

__all__ = [
    "WEB_MAX_BYTES",
    "WEB_TIMEOUT_SECONDS",
    "WebFetchError",
    "WebPage",
    "fetch_file",
    "fetch_page",
]
