"""Tắt nút theo vai trò của tài khoản đang đăng nhập (BR-47, BR-48) - chỉ để hiển thị; backend vẫn là nơi quyết định."""

import streamlit as st

from backend.core.current_user import get_current_user
from backend.features.yarn_costing.dto.common_dto import ROLE_FACTORY, USE_CASE_PERMISSIONS, GroupCode

FEATURE_KEY = "yarn_costing"
SO_ROLE = GroupCode.SO.value
NO_ROLE = "Tài khoản của bạn chưa có vai trò cho thao tác này (quản trị viên cấp ở trang /admin)."


def _permitting_roles(uc: str) -> list[str] | None:
    """Vai trò của tài khoản cho phép thao tác (None = không giới hạn: quản trị viên hoặc chưa có người dùng)."""
    user = get_current_user()
    if user is None or user.is_admin:
        return None
    allowed = USE_CASE_PERMISSIONS.get(uc, (SO_ROLE,))
    return [r for r in user.roles_in(FEATURE_KEY) if r == SO_ROLE or r in allowed]


def action_state(uc: str, factory_code: str | None = None) -> tuple[bool, str | None]:
    """(disabled, help) cho một nút thao tác."""
    roles = _permitting_roles(uc)
    if roles is None:
        return False, None
    if not roles:
        return True, NO_ROLE
    factories = {ROLE_FACTORY.get(r) for r in roles}
    if factory_code and None not in factories and str(factory_code) not in factories:
        return True, f"Bạn chỉ được thao tác dữ liệu của xưởng {', '.join(sorted(str(f) for f in factories))}."
    return False, None


def is_so() -> bool:
    """Phòng SO: có vai trò SO, là quản trị viên hoặc chưa có người dùng."""
    user = get_current_user()
    return user is None or user.is_admin or SO_ROLE in user.roles_in(FEATURE_KEY)


def own_factory() -> str | None:
    """Xưởng mặc định của màn hình: xưởng của tài khoản khi tài khoản chỉ có vai trò của đúng một xưởng."""
    user = get_current_user()
    factories = {ROLE_FACTORY[r] for r in user.roles_in(FEATURE_KEY) if r in ROLE_FACTORY} if user else set()
    return factories.pop() if len(factories) == 1 else None


def explain(*reasons: str | None) -> None:
    """Chú thích dưới nhóm nút bị tắt (mục 8: nút không có quyền bị tắt kèm chú thích)."""
    shown: list[str] = []
    for reason in reasons:
        if reason and reason not in shown:
            shown.append(reason)
    for reason in shown:
        st.caption(f"🔒 {reason}")
