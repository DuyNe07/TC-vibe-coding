"""Header components: ``page_header`` (every page, via BasePage) and ``hero`` (Home)."""

from collections.abc import Sequence
from html import escape

import streamlit as st


def page_header(title: str, *, icon: str = "", description: str = "", breadcrumbs: Sequence[str] = ()) -> None:
    crumbs = '<span class="sep">›</span>'.join(escape(c) for c in breadcrumbs if c)
    st.markdown(
        f"""<div class="tc-page-header">
            {f'<div class="tc-breadcrumb">{crumbs}</div>' if crumbs else ""}
                <div class="tc-title"><span>{escape(icon)}</span><span>{escape(title)}</span></div>
            {f'<p class="tc-desc">{escape(description)}</p>' if description else ""}
            </div>""",
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, meta: str = "") -> None:
    st.markdown(
        f"""<div class="tc-hero"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p>
            {f'<div class="tc-hero-meta">{escape(meta)}</div>' if meta else ""}</div>""",
        unsafe_allow_html=True,
    )
