"""Open Screen 2 from another page (list, my tasks) on a given costsheet, or in create mode."""

from frontend.core.base_page import BasePage
from frontend.features.woven_costing.components.working import open_id
from frontend.features.woven_costing.pages.costsheet_page import CostsheetPage
from frontend.features.woven_costing.pages.dyeing_job_page import OPEN as JOB_OPEN
from frontend.features.woven_costing.pages.dyeing_job_page import WORKING as JOB_WORKING
from frontend.features.woven_costing.pages.dyeing_job_page import DyeingJobPage


def open_costsheet(page: BasePage, costsheet_id: str) -> None:
    open_id(page.state, costsheet_id)
    page.go_to(CostsheetPage)


def new_costsheet(page: BasePage) -> None:
    open_id(page.state, None)
    page.go_to(CostsheetPage)


def open_job(page: BasePage, job_id: str) -> None:
    """Screen 8 on a given dyeing job order (2026-11-25)."""
    page.state.set(JOB_OPEN, job_id)
    page.state.pop(JOB_WORKING)
    page.go_to(DyeingJobPage)
