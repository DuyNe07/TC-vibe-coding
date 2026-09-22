"""Global footer, rendered after every page by AppShell."""

from datetime import date
from html import escape

import streamlit as st

from backend.core.config import get_settings


def render_footer() -> None:
    settings = get_settings()
    st.markdown(
        f"""<div class="tc-footer">
            <span>© {date.today().year} {escape(settings.name)}</span>
            <span>Environment: <b>{escape(settings.env)}</b> · Built on TC Vibe Coding framework</span>
            </div>""",
        unsafe_allow_html=True,
    )
