"""FeatureManifest: how a feature appears on Home and in the sidebar menu.

Every ``frontend/features/<key>/manifest.py`` defines exactly one ``FEATURE = FeatureManifest(...)``.
"""

from dataclasses import dataclass

from backend.core.naming import PAGE_SLUG_PATTERN, is_valid_feature_key
from frontend.core.base_page import BasePage


@dataclass(frozen=True)
class FeatureManifest:
    key: str  # == folder name == backend feature key
    title: str  # shown on Home card + sidebar (Vietnamese)
    description: str  # one or two sentences for the Home card
    pages: tuple[type[BasePage], ...]  # first page = landing page (/<feature-slug>)
    icon: str = "🧩"  # one emoji
    group: str = "Chức năng"  # sidebar / Home section
    owner: str = ""  # person or team responsible
    order: int = 100  # smaller = shown first inside the group
    enabled: bool = True  # False hides the feature everywhere

    def __post_init__(self) -> None:
        if not is_valid_feature_key(self.key):
            raise ValueError(f"Invalid feature key {self.key!r} (snake_case, 3-50 chars, not reserved)")
        if not self.title or not self.description:
            raise ValueError(f"Feature {self.key!r}: title and description are required")
        if not self.pages:
            raise ValueError(f"Feature {self.key!r}: at least one page is required")
        slugs: set[str] = set()
        for index, page in enumerate(self.pages):
            if not (isinstance(page, type) and issubclass(page, BasePage)):
                raise TypeError(f"Feature {self.key!r}: {page!r} must inherit BasePage")
            if not page.title:
                raise ValueError(f"{page.__name__}.title is required")
            if index > 0:
                if not PAGE_SLUG_PATTERN.match(page.slug or ""):
                    raise ValueError(f"{page.__name__}.slug is required (kebab-case) for non-landing pages")
                if page.slug in slugs:
                    raise ValueError(f"Feature {self.key!r}: duplicate page slug {page.slug!r}")
                slugs.add(page.slug)
