"""Screen 7 - Data Update: the data file, the weekly changeover numbers and the upload history."""

from backend.core.base import EmptyRequest
from backend.core.exceptions import AppError
from backend.core.gateway import gateway
from backend.features.sewing_productivity import SewingProductivityController
from frontend.core.base_page import BasePage
from frontend.features.sewing_productivity.components.page_messages import show_flash, show_no_permission
from frontend.features.sewing_productivity.components.upload_blocks import upload_blocks, upload_history
from frontend.features.sewing_productivity.components.weekly_changeover_blocks import weekly_form, weekly_list


class DataUpdatePage(BasePage):
    title = "Data Update"
    icon = "📤"
    slug = "data-update"
    description = "Upload the data file and enter the weekly changeover."
    menu_group = "Data management"

    def render(self) -> None:
        feature = gateway.open(SewingProductivityController)
        try:
            logs = feature.list_upload_logs(EmptyRequest())
        except AppError as exc:  # BR-09 is the only failure of this use case
            show_no_permission(exc)
            return
        show_flash(self.state)
        options = feature.get_filter_options(EmptyRequest())  # only the default week of the form

        upload_blocks(self, feature)
        weekly_form(self, feature, options)
        weekly_list(self, feature)
        upload_history(self, logs)
