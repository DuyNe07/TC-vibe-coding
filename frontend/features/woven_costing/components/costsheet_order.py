"""Screen 2 block A "Thông tin đơn" and the create panel (UC-15)."""

from datetime import date
from typing import Any

import streamlit as st

from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import (
    CostsheetAction,
    DyePlant,
    Market,
    OrderType,
    PriceType,
    SaleForm,
    ShrinkageException,
)
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, CreateCostsheetRequest
from backend.features.woven_costing.dto.list_dto import CostsheetOptionsResponse
from frontend.core.base_page import BasePage
from frontend.core.components import panel
from frontend.features.woven_costing.components.customer_dialog import add_customer_dialog
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.flash import set_flash
from frontend.features.woven_costing.components.labels import dec, enum_values, index_of, num, text, with_value
from frontend.features.woven_costing.components.working import CUSTOMER_CHOICE, CUSTOMER_REV, replace_working

DYE_PLANTS = enum_values(DyePlant)
MARKETS = enum_values(Market)
ORDER_TYPES = enum_values(OrderType)
SALE_FORMS = enum_values(SaleForm)
PRICE_TYPES = enum_values(PriceType)
SHRINKAGE_EXCEPTIONS = enum_values(ShrinkageException)
GREIGE = SaleForm.GREIGE.value
DYED = SaleForm.DYED.value
JOB_FORMS = (SaleForm.WEAVING_JOB.value, SaleForm.DYEING_JOB.value)  # 2026-11-25 (BR-89, BR-90)
OUTSOURCE = OrderType.OUTSOURCE.value


def job_order_type(
    sale_form: str | None, old_sale_form: str | None, order_type: str | None, old_type: str | None
) -> str | None:
    """BR-91: switching the sale form to a job form sets Loại đơn = "Gia Công" unless the sales changed it too."""
    if sale_form in JOB_FORMS and sale_form != old_sale_form and order_type == old_type:
        return OUTSOURCE
    return order_type


def _select(label: str, options: list[str], value: Any, key: str, **kwargs: Any) -> str | None:
    current = text(value)
    options = with_value(options, current)
    return st.selectbox(label, options, index=index_of(options, current), key=key, **kwargs)


def customer_box(page: BasePage, feature: WovenCostingController, options: CostsheetOptionsResponse, *,
                 current: str, key: str, can_add: bool, disabled: bool = False) -> str | None:  # fmt: skip
    """Selectbox "Khách hàng" + button "Thêm khách hàng" (UC-18)."""
    chosen = page.state.get(CUSTOMER_CHOICE) or current
    names = [c.name for c in options.customers]
    with st.container(horizontal=True, gap="small", vertical_alignment="bottom"):
        customer = _select(
            "Khách hàng",
            names,
            chosen,
            f"{key}.{page.state.get(CUSTOMER_REV, 0)}",
            placeholder="Chọn khách hàng",
            disabled=disabled,
        )
        if can_add and st.button("Thêm khách hàng", icon=":material/person_add:", key=f"{key}.add", disabled=disabled):
            add_customer_dialog(page, feature)
    if not names:
        st.caption('Chưa có khách hàng. Bấm "Thêm khách hàng" hoặc nhờ SO tải danh sách.')
    return customer


def order_block(
    page: BasePage,
    feature: WovenCostingController,
    w: CostsheetResponse,
    options: CostsheetOptionsResponse,
    sfx: str,
) -> dict[str, Any]:
    """Widgets of block A seeded from the costsheet; returns the header fields of CostsheetInputRequest."""
    data = w.input
    off = not w.editable
    allowed = set(w.allowed_actions)

    def key(name: str) -> str:
        return page.key(f"{name}.{sfx}")

    with panel("Thông tin đơn", icon="📝"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            dye_plant = st.segmented_control(
                "Nhà máy nhuộm",
                DYE_PLANTS,
                default=text(data.dye_plant) or DyePlant.HCM.value,
                required=True,
                key=key("dye_plant"),
                disabled=off,
            )
        with c2:
            customer = customer_box(
                page,
                feature,
                options,
                current=data.customer_name,
                key=key("customer"),
                can_add=CostsheetAction.ADD_CUSTOMER in allowed,
                disabled=off,
            )
        with c3:
            market = _select("Thị trường", MARKETS, data.market, key("market"), disabled=off)
        with c4:
            order_type = _select("Loại đơn hàng", ORDER_TYPES, data.order_type, key("order_type"), disabled=off)
        c1, c2, c3, c4 = st.columns(4)
        style = c1.text_input("Style", value=data.style, max_chars=100, key=key("style"), disabled=off)
        with c2:
            sale_form = _select("Hình thức bán", SALE_FORMS, data.sale_form, key("sale_form"), disabled=off)
        order_type = job_order_type(sale_form, text(data.sale_form), order_type, text(data.order_type))
        greige_buy_price = data.greige_buy_price
        if sale_form == DYED:
            greige_buy_price = dec(
                c3.number_input(
                    "Giá mộc mua ngoài (đ/m)",
                    min_value=0.0,
                    step=100.0,
                    value=num(data.greige_buy_price),
                    key=key("greige_buy"),
                    disabled=off,
                )
            )
        delivery = c4.date_input(
            "Ngày giao hàng", value=data.delivery_date, format="DD/MM/YYYY", key=key("delivery"), disabled=off
        )
        c1, c2, c3, c4 = st.columns(4)
        costing = c1.date_input(
            "Ngày tính giá", value=data.costing_date, format="DD/MM/YYYY", key=key("costing"), disabled=off
        )
        tcfno = c2.text_input("Mã vải", value=data.tcfno, max_chars=15, key=key("tcfno"), disabled=off)
        meters = c3.number_input(
            "Số lượng đặt (m)", min_value=0.0, step=100.0, value=num(data.order_meters), key=key("meters"), disabled=off
        )
        with c4:
            price_type = _select("Loại giá", PRICE_TYPES, data.price_type, key("price_type"), disabled=off)
        c1, c2, c3 = st.columns([1, 1, 2])
        oc_no = c1.text_input(
            "Số OC",
            value=data.oc_no,
            max_chars=40,
            placeholder="KDV10-SX-LO-0726-6564.1",
            key=key("oc"),
            disabled=not (w.editable or CostsheetAction.SAVE_OC in allowed),
        )
        low = w.result.low_shrinkage
        with c2:
            exception = _select(
                "Lý do ngoại lệ độ co" + (" :orange-badge[Độ co thấp]" if low else ""),
                SHRINKAGE_EXCEPTIONS,
                data.shrinkage_exception,
                key("shrink_exc"),
                disabled=off,
            )
        shrinkage_reason = data.shrinkage_reason
        if low or data.shrinkage_reason:
            shrinkage_reason = c3.text_input(
                "Lý do độ co thấp / bằng 0", value=data.shrinkage_reason, max_chars=300, key=key("shrink_reason"),
                disabled=off,
            )  # fmt: skip
        note = st.text_area("Ghi chú", value=data.note, max_chars=1000, height=68, key=key("note"), disabled=off)
    return {
        "dye_plant": dye_plant or text(data.dye_plant),
        "customer_name": customer or "",
        "market": market,
        "order_type": order_type,
        "style": (style or "").strip(),
        "sale_form": sale_form,
        "greige_buy_price": greige_buy_price,
        "delivery_date": delivery,
        "costing_date": costing,
        "tcfno": (tcfno or "").strip().upper(),
        "order_meters": dec(meters),
        "price_type": price_type,
        "oc_no": (oc_no or "").strip(),
        "shrinkage_exception": exception or ShrinkageException.NONE.value,
        "shrinkage_reason": (shrinkage_reason or "").strip(),
        "note": (note or "").strip(),
    }


def create_panel(page: BasePage, feature: WovenCostingController, options: CostsheetOptionsResponse) -> None:
    """UC-15 Tạo costsheet: order information -> the app fetches fabric, norms, parameters and calculates."""
    with panel(
        "Tạo costsheet mới",
        icon="➕",
        description="Nhập thông tin đơn, app lấy thông số vải, định mức, tham số và tính ngay.",
    ):
        customer = customer_box(page, feature, options, current="", key=page.key("new.customer"), can_add=True)
        with st.form(page.key("new.form"), border=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                dye_plant = st.segmented_control(
                    "Nhà máy nhuộm", DYE_PLANTS, default=DyePlant.HCM.value, required=True, key=page.key("new.dye")
                )
                market = st.selectbox("Thị trường", MARKETS, index=0, key=page.key("new.market"))
                order_type = st.selectbox("Loại đơn hàng", ORDER_TYPES, index=1, key=page.key("new.order_type"))
                style = st.text_input("Style", max_chars=100, key=page.key("new.style"))
            with c2:
                sale_form = st.selectbox("Hình thức bán", SALE_FORMS, index=1, key=page.key("new.sale_form"))
                greige_buy = st.number_input(
                    "Giá mộc mua ngoài (đ/m, khi Vải Nhuộm)",
                    min_value=0.0,
                    step=100.0,
                    value=None,
                    key=page.key("new.greige_buy"),
                )
                delivery = st.date_input(
                    "Ngày giao hàng", value=None, format="DD/MM/YYYY", key=page.key("new.delivery")
                )
                costing = st.date_input(
                    "Ngày tính giá", value=date.today(), format="DD/MM/YYYY", key=page.key("new.costing")
                )
            with c3:
                tcfno = st.text_input("Mã vải", max_chars=15, placeholder="Ví dụ EM35790026", key=page.key("new.tcfno"))
                meters = st.number_input(
                    "Số lượng đặt (m)", min_value=0.0, step=100.0, value=None, key=page.key("new.meters")
                )
                price_type = st.selectbox("Loại giá", PRICE_TYPES, index=0, key=page.key("new.price_type"))
                oc_no = st.text_input("Số OC (có thể nhập sau)", max_chars=40, key=page.key("new.oc"))
            submitted = st.form_submit_button("Tạo costsheet", type="primary", icon=":material/add:")
        if submitted:
            created = attempt(
                lambda: feature.create_costsheet(
                    CreateCostsheetRequest(
                        dye_plant=dye_plant or DyePlant.HCM.value,
                        customer_name=customer or "",
                        market=market,
                        order_type=job_order_type(sale_form, SALE_FORMS[1], order_type, ORDER_TYPES[1]),
                        style=(style or "").strip(),
                        sale_form=sale_form,
                        greige_buy_price=dec(greige_buy),
                        delivery_date=delivery,
                        costing_date=costing,
                        tcfno=(tcfno or "").strip().upper(),
                        order_meters=dec(meters),
                        price_type=price_type,
                        oc_no=(oc_no or "").strip(),
                    )
                )
            )
            if created is not None:
                replace_working(page.state, created)
                set_flash(page.state, created.message or f"Đã tạo costsheet {created.costsheet_no}.")
                st.rerun()
