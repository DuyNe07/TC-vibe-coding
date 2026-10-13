"""Global footer, rendered after every page by AppShell."""

from datetime import date

import streamlit as st

from backend.core.config import get_settings


def render_footer() -> None:
    settings = get_settings()
    st.space("large")
    st.caption(f"© {date.today().year} {settings.name}. Môi trường: {settings.env}.")
