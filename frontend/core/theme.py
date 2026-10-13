"""The little CSS the native theme (.streamlit/config.toml [theme]) cannot express. Applied once per run by AppShell.

Features must not inject global CSS.
"""

import streamlit as st

# The one brand mark: four threads in the colours of the TC logo under every page title.
THREADS = "#224086 0 25%, #25AAE1 25% 50%, #119C4A 50% 75%, #F79521 75% 100%"

_CSS = f"""
<style>
  .block-container {{ padding-top: 1.4rem; padding-bottom: 1rem; max-width: 1400px; }}
  .st-key-tc-page-header {{ border-style: solid; border-width: 0 0 3px 0;
                            border-image: linear-gradient(90deg, {THREADS}) 1; padding-bottom: .4rem; }}
</style>
"""


def apply_theme() -> None:
    st.html(_CSS)
