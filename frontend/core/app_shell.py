"""AppShell: the layout applied to EVERY page (config, theme, login, sidebar menu, page, footer)."""

import streamlit as st

from backend.core.config import get_settings
from frontend.core.admin_page import AdminPage
from frontend.core.auth import require_login
from frontend.core.base_page import BasePage
from frontend.core.branding import page_icon
from frontend.core.components import render_footer, render_sidebar_nav
from frontend.core.registry import FeatureRegistry
from frontend.core.router import Router, set_current_router
from frontend.core.theme import apply_theme


class AppShell:
    def __init__(self, home_page: BasePage) -> None:
        self.home_page = home_page

    def run(self) -> None:
        settings = get_settings()
        st.set_page_config(
            page_title=settings.name, page_icon=page_icon(), layout="wide", initial_sidebar_state="expanded"
        )
        apply_theme()
        user = require_login()  # draws the login form and stops when nobody is logged in
        router = Router(FeatureRegistry.discover(), self.home_page, user, AdminPage())
        set_current_router(router)
        current_page = router.navigation()
        render_sidebar_nav(router, current_page)
        current_page.run()
        render_footer()
