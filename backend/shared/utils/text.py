"""Text helpers (Vietnamese aware)."""

import re
import unicodedata


def strip_accents(text: str) -> str:
    """``"Số lượng Đơn giá"`` -> ``"So luong Don gia"``."""
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_key(text: object) -> str:
    """Normalize a header/label for matching: ``" Mã  SP "`` -> ``"ma sp"``."""
    value = strip_accents(str(text or "")).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return value.strip()
