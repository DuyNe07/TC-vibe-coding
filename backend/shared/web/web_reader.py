"""Read data from public web pages (download -> text / tables / links / files).

Use it ONLY from ``builders/`` or ``services/`` of a feature, never from the frontend::

    from backend.shared.web import fetch_page

    page = fetch_page("https://example.com/gia-thep")
    rows = page.tables()[0]              # list of dicts, empty cells are None

Limits: public pages only (no login), no JavaScript rendering (no browser), one page per call.
"""

import math
import re
from dataclasses import dataclass, field
from io import StringIO
from pathlib import PurePosixPath
from typing import Any, Final
from urllib.parse import unquote, urlparse

import pandas as pd
import requests
from lxml import html as lxml_html

from backend.core.exceptions import AppError
from backend.core.logger import get_logger

WEB_TIMEOUT_SECONDS: Final[int] = 20
WEB_MAX_BYTES: Final[int] = 10_000_000
WEB_USER_AGENT: Final[str] = "TC-Vibe-Coding/1.0 (internal tool)"

_WHITESPACE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")
_logger = get_logger(__name__)


class WebFetchError(AppError):
    """The page could not be downloaded (wrong address, no network, blocked, too big...)."""

    code = "WEB_FETCH_ERROR"
    default_message = "Cannot download data from the web page."


def _clean(value: Any) -> Any:
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (TypeError, ValueError):
            return value
        return None if isinstance(value, float) and math.isnan(value) else value
    return value


@dataclass(frozen=True)
class WebPage:
    """One downloaded page: its address, HTTP status and HTML."""

    url: str
    status_code: int
    html: str
    headers: dict[str, str] = field(default_factory=dict)

    def _document(self) -> Any:
        try:
            document = lxml_html.fromstring(self.html)
        except Exception as exc:  # malformed / empty HTML
            raise WebFetchError(f"Cannot read the content of '{self.url}': {exc}") from exc
        document.make_links_absolute(self.url, resolve_base_href=True)
        return document

    def text(self) -> str:
        """Visible text of the page, without scripts/styles and without extra blank lines."""
        document = self._document()
        for element in document.xpath("//script | //style | //noscript"):
            element.getparent().remove(element)
        lines = [_WHITESPACE.sub(" ", line).strip() for line in document.text_content().splitlines()]
        return _BLANK_LINES.sub("\n\n", "\n".join(line for line in lines if line))

    def tables(self) -> list[list[dict[str, Any]]]:
        """Every HTML table as a list of rows (dicts); empty cells are ``None``."""
        try:
            frames = pd.read_html(StringIO(self.html), flavor="lxml")
        except ValueError:
            return []
        return [
            [{str(k): _clean(v) for k, v in record.items()} for record in frame.to_dict("records")] for frame in frames
        ]

    def links(self) -> list[dict[str, str]]:
        """All links as ``{"text": ..., "url": absolute address}``."""
        return [
            {"text": _WHITESPACE.sub(" ", (element.text_content() or "").strip()), "url": element.get("href", "")}
            for element in self._document().xpath("//a[@href]")
        ]

    def find_texts(self, xpath: str) -> list[str]:
        """Texts of the elements matching an XPath, e.g. ``//h2`` or ``//div[@class="price"]``."""
        results = []
        for node in self._document().xpath(xpath):
            text = node if isinstance(node, str) else node.text_content()
            results.append(_WHITESPACE.sub(" ", str(text)).strip())
        return [text for text in results if text]


def fetch_page(
    url: str,
    *,
    timeout: int = WEB_TIMEOUT_SECONDS,
    max_bytes: int = WEB_MAX_BYTES,
    headers: dict[str, str] | None = None,
    session: Any | None = None,
) -> WebPage:
    """Download one page and return it as a :class:`WebPage` (raises ``WebFetchError`` on failure)."""
    content, response = _download(url, timeout=timeout, max_bytes=max_bytes, headers=headers, session=session)
    encoding = response.encoding or "utf-8"
    try:
        html = content.decode(encoding, errors="replace")
    except LookupError:
        html = content.decode("utf-8", errors="replace")
    return WebPage(
        url=str(getattr(response, "url", url)),
        status_code=int(response.status_code),
        html=html,
        headers={str(k).lower(): str(v) for k, v in dict(getattr(response, "headers", {})).items()},
    )


def fetch_file(
    url: str,
    *,
    timeout: int = WEB_TIMEOUT_SECONDS,
    max_bytes: int = WEB_MAX_BYTES,
    headers: dict[str, str] | None = None,
    session: Any | None = None,
) -> tuple[bytes, str]:
    """Download a file (Excel, PDF...) and return ``(content, filename)`` for the readers of ``file_io``."""
    content, response = _download(url, timeout=timeout, max_bytes=max_bytes, headers=headers, session=session)
    disposition = str(dict(getattr(response, "headers", {})).get("Content-Disposition", ""))
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', disposition)
    name = unquote(match.group(1)) if match else PurePosixPath(urlparse(url).path).name
    return content, name or "download"


def _download(
    url: str,
    *,
    timeout: int,
    max_bytes: int,
    headers: dict[str, str] | None,
    session: Any | None,
) -> tuple[bytes, Any]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise WebFetchError(f"Invalid web address: '{url}'. It must start with http:// or https://.")
    client = session or requests.Session()
    request_headers = {"User-Agent": WEB_USER_AGENT, **(headers or {})}
    try:
        response = client.get(url, timeout=timeout, headers=request_headers, stream=True, allow_redirects=True)
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_content(chunk_size=65_536):
            content.extend(chunk)
            if len(content) > max_bytes:
                raise WebFetchError(
                    f"The page '{url}' is bigger than the {max_bytes // 1_000_000} MB limit. Use a more precise address."
                )
    except WebFetchError:
        raise
    except requests.HTTPError as exc:
        status = getattr(exc.response, "status_code", "?")
        raise WebFetchError(
            f"The page '{url}' returned error {status}. Check the address and whether it is publicly reachable."
        ) from exc
    except requests.Timeout as exc:
        raise WebFetchError(f"The page '{url}' did not answer within {timeout} seconds. Try again later.") from exc
    except Exception as exc:
        raise WebFetchError(f"Cannot download '{url}': {exc}") from exc
    _logger.debug("Fetched %s (%s bytes, status %s)", url, len(content), response.status_code)
    return bytes(content), response
