"""Shared UI components. Reuse these before writing new widgets; add feature-specific widgets
to ``frontend/features/<key>/components/`` instead of here.
"""

from frontend.core.components.data_table import data_table, editable_table, frame_to_records
from frontend.core.components.feedback import show_error, show_success, show_unexpected_error
from frontend.core.components.files import download_button, file_upload
from frontend.core.components.footer import render_footer
from frontend.core.components.header import hero, page_header
from frontend.core.components.log_panel import log_panel
from frontend.core.components.panel import empty_state, panel, section_title, stat_row
from frontend.core.components.sidebar_nav import render_sidebar_nav

__all__ = [
    "data_table",
    "download_button",
    "editable_table",
    "empty_state",
    "file_upload",
    "frame_to_records",
    "hero",
    "log_panel",
    "page_header",
    "panel",
    "render_footer",
    "render_sidebar_nav",
    "section_title",
    "show_error",
    "show_success",
    "show_unexpected_error",
    "stat_row",
]
