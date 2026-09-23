"""The shared web reader: parsing a page and the failure messages of ``fetch_page`` (no real network)."""

from typing import Any

import pytest
import requests

from backend.shared.web import WebFetchError, WebPage, fetch_file, fetch_page

HTML = """
<html><body>
  <h2>Giá thép hôm nay</h2>
  <script>var a = 1;</script>
  <table><tr><th>Mã</th><th>Giá</th></tr><tr><td>SP01</td><td>1000</td></tr><tr><td>SP02</td><td></td></tr></table>
  <a href="/chi-tiet/sp01">Chi tiết SP01</a>
</body></html>
"""


class FakeResponse:
    def __init__(self, content: bytes, *, status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        self._content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.encoding = "utf-8"
        self.url = "https://example.com/final"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            error = requests.HTTPError(f"{self.status_code}")
            error.response = self  # type: ignore[assignment]
            raise error

    def iter_content(self, chunk_size: int = 1) -> Any:
        for start in range(0, len(self._content), chunk_size):
            yield self._content[start : start + chunk_size]


class FakeSession:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> Any:
        self.calls.append({"url": url, **kwargs})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_page_gives_text_tables_and_absolute_links() -> None:
    page = WebPage(url="https://example.com/gia", status_code=200, html=HTML)
    assert "Giá thép hôm nay" in page.text() and "var a" not in page.text()
    rows = page.tables()[0]
    assert rows[0] == {"Mã": "SP01", "Giá": 1000}
    assert rows[1]["Giá"] is None
    assert page.links() == [{"text": "Chi tiết SP01", "url": "https://example.com/chi-tiet/sp01"}]
    assert page.find_texts("//h2") == ["Giá thép hôm nay"]


def test_page_without_table_returns_no_table() -> None:
    assert WebPage(url="https://example.com", status_code=200, html="<p>Xin chào</p>").tables() == []


def test_fetch_page_sends_a_user_agent_and_returns_the_final_url() -> None:
    session = FakeSession(FakeResponse(HTML.encode()))
    page = fetch_page("https://example.com/gia", session=session)
    assert page.status_code == 200 and page.url == "https://example.com/final"
    assert "TC-Vibe-Coding" in session.calls[0]["headers"]["User-Agent"]
    assert session.calls[0]["timeout"] == 20
    assert page.tables()[0][0]["Mã"] == "SP01"


def test_fetch_file_takes_the_name_from_the_url() -> None:
    session = FakeSession(FakeResponse(b"xlsx-bytes"))
    content, name = fetch_file("https://example.com/bao-cao/thang-1.xlsx", session=session)
    assert content == b"xlsx-bytes" and name == "thang-1.xlsx"


def test_fetch_file_prefers_the_name_sent_by_the_server() -> None:
    session = FakeSession(FakeResponse(b"x", headers={"Content-Disposition": 'attachment; filename="bao cao.xlsx"'}))
    assert fetch_file("https://example.com/download?id=3", session=session)[1] == "bao cao.xlsx"


@pytest.mark.parametrize("url", ["ftp://example.com/a", "example.com", "", "https://"])
def test_a_wrong_address_is_refused_before_any_call(url: str) -> None:
    session = FakeSession(FakeResponse(b""))
    with pytest.raises(WebFetchError, match="Invalid web address"):
        fetch_page(url, session=session)
    assert session.calls == []


def test_http_error_becomes_a_readable_message() -> None:
    with pytest.raises(WebFetchError, match="returned error 404"):
        fetch_page("https://example.com/missing", session=FakeSession(FakeResponse(b"", status_code=404)))


def test_timeout_becomes_a_readable_message() -> None:
    with pytest.raises(WebFetchError, match="did not answer within"):
        fetch_page("https://example.com/slow", session=FakeSession(requests.Timeout()))


def test_a_page_bigger_than_the_limit_is_refused() -> None:
    session = FakeSession(FakeResponse(b"x" * 2_000))
    with pytest.raises(WebFetchError, match="bigger than"):
        fetch_page("https://example.com/huge", max_bytes=1_000, session=session)
