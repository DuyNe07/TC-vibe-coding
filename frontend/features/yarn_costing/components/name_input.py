"""Ô nhập tên sợi (bổ sung 2026-11-11): Ghép tên / Gõ tay (BR-102), chữ lạ + gợi ý + lý do (BR-101). Dùng ở Screen 2 và Screen 14."""

import re
from decimal import Decimal

import streamlit as st

from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.name_dto import CheckYarnNameRequest, NameMode, YarnNameCheckResponse

MODES = [NameMode.GHEP, NameMode.GO_TAY]
MODE_LABELS = {NameMode.GHEP: "Ghép tên", NameMode.GO_TAY: "Gõ tay"}
NO_PARTS = 'Chưa có danh sách nhóm sợi / từ khoá (Phòng SO mở màn "Kiểm tra tên sợi" để khởi tạo) - hãy gõ tay.'


def replace_word(text: str, wrong: str, right: str) -> str:
    """Screen-side replacement of one word typed by the user (the backend checks the result again)."""
    return re.sub(rf"(?<![A-Za-z0-9]){re.escape(wrong)}(?![A-Za-z0-9])", right, text, flags=re.IGNORECASE)


def _use_suggestion(text_key: str, wrong: str, right: str) -> None:
    st.session_state[text_key] = replace_word(st.session_state.get(text_key, ""), wrong, right)


def name_input(
    feature: YarnCostingController,
    key: str,
    initial: str = "",
    allow_builder: bool = True,
    label: str = "Tên sợi",
) -> tuple[str, str, str, YarnNameCheckResponse | None]:
    """Draw the name block; returns (name, mode, unknown-word reason, check). ``key`` makes every widget unique."""
    options = feature.check_yarn_name(CheckYarnNameRequest())
    has_parts = bool(options.groups)
    mode = NameMode.GO_TAY
    if allow_builder:
        mode = st.radio(
            "Cách nhập tên",
            MODES if has_parts else [NameMode.GO_TAY],
            format_func=lambda m: MODE_LABELS[m],
            horizontal=True,
            key=f"{key}.mode",
        )
        if not has_parts:
            st.caption(NO_PARTS)
    if mode == NameMode.GHEP:
        groups = {g.text: g for g in options.groups}
        c1, c2, c3 = st.columns([2, 1, 2])
        group_text = c1.selectbox(
            "Nhóm sợi",
            list(groups),
            index=None,
            placeholder="Chọn nhóm sợi",
            format_func=lambda g: g + (" (mới - Sales thêm)" if not groups[g].reviewed else ""),
            key=f"{key}.group",
        )
        count = c2.number_input("Chi số", min_value=0.0, step=1.0, format="%g", key=f"{key}.count")
        group = groups.get(group_text) if group_text else None
        ratios: list[Decimal] = []
        if group is not None and group.fiber_count >= 2:
            cols = c3.columns(group.fiber_count)
            for index, col in enumerate(cols):
                value = col.number_input(
                    f"Tỷ lệ {index + 1}",
                    min_value=0.0,
                    max_value=100.0,
                    step=5.0,
                    format="%g",
                    key=f"{key}.ratio{index}",
                )
                ratios.append(Decimal(str(value)))
        keywords = st.multiselect(
            "Từ khoá",
            [k.text for k in options.keywords],
            placeholder="Chọn từ khoá (MVS, SIRO, COMPACT...)",
            key=f"{key}.keywords",
        )
        started = bool(group_text or count or keywords)  # nothing chosen yet: no message
        check = (
            feature.check_yarn_name(
                CheckYarnNameRequest(
                    mode=NameMode.GHEP,
                    group=group_text or "",
                    count=Decimal(str(count)) if count else None,
                    ratios=ratios,
                    keywords=keywords,
                )
            )
            if started
            else None
        )
        if check is not None and check.name:
            st.markdown(f"➜ **Tên sợi: {check.name}**")
    else:
        text_key = f"{key}.text"
        if initial and text_key not in st.session_state:
            st.session_state[text_key] = initial
        typed = st.text_input(label, max_chars=200, placeholder="Ví dụ: CVC 30/1 (60/40) MVS", key=text_key)
        check = (
            feature.check_yarn_name(CheckYarnNameRequest(mode=NameMode.GO_TAY, yarn_name=typed))
            if typed.strip()
            else None
        )
        if check is not None and check.name and check.name != typed.strip():
            st.caption(f"Tên sẽ lưu: {check.name}")
    if check is None:
        return "", mode.value, "", None
    if check.problem:
        st.warning(check.problem, icon="⚠️")
    reason = ""
    if check.unknown:
        st.warning(
            "Chữ chưa có trong từ điển: "
            + ", ".join(u.word for u in check.unknown)
            + ". Chọn chữ gợi ý hoặc ghi lý do giữ chữ lạ.",
            icon="🔤",
        )
        if mode == NameMode.GO_TAY:
            fixable = [u for u in check.unknown if u.suggestion]
            for col, item in zip(st.columns(max(len(fixable), 1)), fixable, strict=False):
                col.button(  # the callback runs before the next run, when the text box may still be changed
                    f"Dùng {item.suggestion} (thay {item.word})",
                    key=f"{key}.fix.{item.word}",
                    on_click=_use_suggestion,
                    args=(f"{key}.text", item.word, item.suggestion),
                )
        reason = st.text_input("Lý do giữ chữ lạ", max_chars=500, key=f"{key}.reason")
    return check.name, mode.value, reason, check
