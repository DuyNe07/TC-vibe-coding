"""Session keys shared by the costsheet pages: the costsheet being worked on (Screen 2)."""

from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse
from frontend.core.session_state import SessionState

OPEN_ID = "cs.open_id"  # id of the costsheet version open on Screen 2 (None = create mode)
WORKING = "cs.working"  # last CostsheetResponse received: every widget of Screen 2 is seeded from it
REV = "cs.rev"  # +1 each time WORKING is replaced: widget keys change so they are seeded again
DIRTY = "cs.dirty"  # recalculated but not saved yet ("Có thay đổi chưa lưu")
# UC-16 auto-calculation: ((costsheet id, REV), fingerprint of the cells) seen on the first run after WORKING changed;
# a later run whose cells give another fingerprint recalculates once (no loop: the fingerprint is not recomputed
# from the answer, the next WORKING starts a new baseline)
CALC_BASE = "cs.calc_base"
CUSTOMER_CHOICE = "cs.customer_choice"  # customer just added / picked in the "Thêm khách hàng" dialog
CUSTOMER_REV = "cs.customer_rev"


def replace_working(state: SessionState, response: CostsheetResponse, *, dirty: bool = False) -> None:
    state.set(WORKING, response)
    state.set(OPEN_ID, response.id or state.get(OPEN_ID))
    state.set(REV, int(state.get(REV, 0)) + 1)
    state.set(DIRTY, dirty)
    state.pop(CUSTOMER_CHOICE)


def needs_calculation(state: SessionState, costsheet_id: str | None, fingerprint: str) -> bool:
    """UC-16 (2026-11-23): True when the cells on screen differ from those of the first run of the current WORKING."""
    seen = (costsheet_id, int(state.get(REV, 0)))
    base = state.get(CALC_BASE)
    if base is None or tuple(base[0]) != seen:
        state.set(CALC_BASE, (seen, fingerprint))
        return False
    return base[1] != fingerprint


def open_id(state: SessionState, costsheet_id: str | None) -> None:
    """Ask Screen 2 to open another costsheet version (loaded on its next run)."""
    state.set(OPEN_ID, costsheet_id)
    state.pop(WORKING)
    state.set(DIRTY, False)
    state.pop(CUSTOMER_CHOICE)


def choose_customer(state: SessionState, name: str) -> None:
    """Put a customer in the "Khách hàng" box at the next run (new widget key -> the box shows it)."""
    state.set(CUSTOMER_CHOICE, name)
    state.set(CUSTOMER_REV, int(state.get(CUSTOMER_REV, 0)) + 1)
