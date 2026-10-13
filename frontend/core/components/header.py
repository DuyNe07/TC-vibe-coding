"""Page header (every page, via BasePage): breadcrumb, title with icon, description, brand thread stripe."""

from collections.abc import Sequence

import streamlit as st


def page_header(title: str, *, icon: str = "", description: str = "", breadcrumbs: Sequence[str] = ()) -> None:
    with st.container(key="tc-page-header", gap="xxsmall"):
        crumbs = [c for c in breadcrumbs if c]
        if crumbs:
            st.caption(" › ".join(crumbs))
        st.title(title, icon=icon or None, anchor=False)
        if description:
            st.caption(description)
