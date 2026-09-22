"""BasePage: every Streamlit page is a class inheriting this.

    class OrderListPage(BasePage):
        title = "Danh sách đơn hàng"
        icon = "📋"
        slug = "orders"                 # required for every page except the feature's first page
        description = "Tra cứu và xuất danh sách đơn hàng."

        def render(self) -> None:
            result = OrderController().list_orders(ListOrdersRequest(keyword="A"))   # direct call
            data_table([item.model_dump() for item in result.items])

``run()`` is the fixed template (header -> render -> error boundary). Never override it.
The boundary shows any ``AppError`` raised by the backend as a friendly message, so pages simply call
their controller; catch ``AppError`` yourself only when the rest of the page must keep rendering.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import ValidationError as PydanticValidationError

from backend.core.exceptions import AppError, InvalidInputError
from backend.core.logger import get_logger
from frontend.core.components.feedback import show_error, show_unexpected_error
from frontend.core.components.header import page_header
from frontend.core.components.log_panel import log_panel
from frontend.core.session_state import SessionState


class BasePage(ABC):
    title: ClassVar[str] = ""
    icon: ClassVar[str] = "📄"
    slug: ClassVar[str] = ""
    description: ClassVar[str] = ""
    show_log_panel: ClassVar[bool] = True  # log panel at the bottom of the page (keep True for features)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "run" in cls.__dict__:
            raise TypeError(f"{cls.__name__} must not override run(); implement render()")

    def __init__(self, feature_key: str) -> None:
        self.feature_key = feature_key
        self.state = SessionState(feature_key)
        self.logger = get_logger(type(self).__module__)

    def run(self) -> None:
        """Called by the router: header -> render() inside an error boundary -> log panel."""
        self.render_header()
        try:
            self.render()
        except AppError as exc:
            show_error(exc)  # already logged by the gateway
        except PydanticValidationError as exc:
            show_error(InvalidInputError.from_pydantic(exc))
        except Exception as exc:  # Streamlit control flow (rerun/switch_page) is BaseException: not caught
            self.logger.exception("Page %s crashed", type(self).__name__)
            show_unexpected_error(exc)
        if self.show_log_panel:
            log_panel(self.feature_key, key=self.key("log_panel"))

    def render_header(self) -> None:
        """Shared header with breadcrumb. Override only for special pages (e.g. Home)."""
        from frontend.core.router import get_router

        router = get_router()
        manifest = router.registry.get(self.feature_key) if router else None
        crumbs = ["Trang chủ"]
        if manifest:
            crumbs += [manifest.group, manifest.title]
            if manifest.pages and manifest.pages[0] is not type(self):
                crumbs.append(self.title)
        page_header(self.title, icon=self.icon, description=self.description, breadcrumbs=crumbs)

    @abstractmethod
    def render(self) -> None:
        """Draw the page body. Call ONLY the controller of this feature for data/actions."""

    # ---- helpers ----
    def key(self, name: str) -> str:
        """Unique widget key: ``st.text_input(..., key=self.key("keyword"))``."""
        return self.state.key(f"{type(self).__name__}.{name}")

    def go_to(self, page_cls: type["BasePage"]) -> None:
        from frontend.core.router import get_router

        get_router().switch_to(page_cls)

    def link_to(self, page_cls: type["BasePage"], label: str | None = None, icon: str | None = None) -> None:
        from frontend.core.router import get_router

        get_router().link(page_cls, label=label, icon=icon)
