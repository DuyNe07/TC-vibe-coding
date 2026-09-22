"""Home page (/home): lists every enabled feature as a card, grouped, with search."""

from html import escape

import streamlit as st

from backend.core.config import get_settings
from frontend.core.base_page import BasePage
from frontend.core.components import empty_state, hero, panel
from frontend.core.feature_manifest import FeatureManifest
from frontend.core.router import get_router

ALL_GROUPS = "Tất cả"
CARDS_PER_ROW = 3


class HomePage(BasePage):
    title = "Trang chủ"
    icon = "🏠"
    show_log_panel = False  # logs are shown only on feature pages

    def __init__(self) -> None:
        super().__init__("home")

    def render_header(self) -> None:
        registry = get_router().registry
        hero(
            get_settings().name,
            "Cổng tổng hợp các công cụ nội bộ. Chọn một chức năng bên dưới để bắt đầu.",
            meta=f"{len(registry.features)} chức năng · {len(registry.groups())} nhóm",
        )

    def render(self) -> None:
        router = get_router()
        registry = router.registry
        self._render_load_errors()
        if not registry.features:
            empty_state(
                "Chưa có chức năng nào.",
                "Yêu cầu AI: “Đọc docs/README.md rồi triển khai chức năng theo docs/business/<tên>.md”.",
                icon="🧩",
            )
            return

        groups = registry.groups()
        search_col, group_col = st.columns([2, 3], vertical_alignment="bottom")
        keyword = search_col.text_input(
            "Tìm chức năng", key=self.key("search"), placeholder="Nhập tên hoặc mô tả...", type="search"
        )
        selected = (
            group_col.pills("Nhóm", [ALL_GROUPS, *groups.keys()], default=ALL_GROUPS, key=self.key("group"))
            or ALL_GROUPS
        )

        shown = 0
        for group, manifests in groups.items():
            if selected not in (ALL_GROUPS, group):
                continue
            visible = [m for m in manifests if self._matches(m, keyword)]
            if not visible:
                continue
            shown += len(visible)
            st.markdown(f"##### {group}")
            for start in range(0, len(visible), CARDS_PER_ROW):
                columns = st.columns(CARDS_PER_ROW)
                for column, manifest in zip(columns, visible[start : start + CARDS_PER_ROW], strict=False):
                    with column:
                        self._render_card(manifest)
        if shown == 0:
            empty_state("Không tìm thấy chức năng phù hợp.", "Thử từ khoá khác.", icon="🔍")

    def _render_card(self, manifest: FeatureManifest) -> None:
        router = get_router()
        with panel(key=f"tc-card-{manifest.key}"):
            st.markdown(
                f"""<div class="tc-card-title">{escape(manifest.icon)} {escape(manifest.title)}</div>
                    <div class="tc-card-desc">{escape(manifest.description)}</div>
                    <div class="tc-card-meta">{escape(manifest.owner and "Phụ trách: " + manifest.owner)}</div>""",
                unsafe_allow_html=True,
            )
            if st.button("Mở chức năng →", key=self.key(f"open.{manifest.key}"), width="stretch"):
                st.switch_page(router.landing_page(manifest.key))

    def _render_load_errors(self) -> None:
        errors = get_router().registry.errors
        if not errors:
            return
        with st.expander(f"⚠️ {len(errors)} chức năng không tải được (các chức năng khác vẫn hoạt động)", expanded=True):
            for error in errors:
                st.markdown(f"**{error.feature_key}** — {error.message}")
                st.code(error.traceback, language="text")

    @staticmethod
    def _matches(manifest: FeatureManifest, keyword: str) -> bool:
        needle = keyword.strip().lower()
        return not needle or needle in f"{manifest.title} {manifest.description} {manifest.owner}".lower()
