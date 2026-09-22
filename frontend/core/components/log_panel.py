"""Log panel: shows the last log entries of a feature (from logs/app.log) so users can copy them.

Rendered automatically at the bottom of every feature page by BasePage (not on Home).
Not realtime: press "Tải lại" or interact with the page to refresh.
"""

import streamlit as st

from backend.core.logger import LEVELS, read_log_entries


def log_panel(feature_key: str, *, key: str) -> None:
    with st.expander("📜 Nhật ký chạy (log)", expanded=False):
        level_col, limit_col, button_col = st.columns([2, 2, 1], vertical_alignment="bottom")
        level = level_col.selectbox("Mức tối thiểu", LEVELS[:4], index=1, key=f"{key}.level")
        limit = limit_col.selectbox("Số dòng gần nhất", (50, 200, 1000), index=1, key=f"{key}.limit")
        button_col.button("🔄 Tải lại", key=f"{key}.refresh", width="stretch")

        entries = read_log_entries(feature_key, min_level=level, limit=limit)
        if not entries:
            st.caption("Chưa có log nào.")
            return
        text = "\n".join(entry.text for entry in entries)
        st.caption("Bấm biểu tượng copy ở góc khung để sao chép, gửi cho AI / người phát triển khi cần tìm lỗi.")
        st.code(text, language="log", height=320, wrap_lines=True)
        st.download_button(
            "⬇️ Tải log (.txt)",
            data=text,
            file_name=f"log-{feature_key}.txt",
            mime="text/plain",
            key=f"{key}.download",
            on_click="ignore",
        )
