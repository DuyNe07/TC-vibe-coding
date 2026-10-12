"""Screen 7 (`dashboard`) - Dashboard kiểm soát (UC-30..UC-32, UC-37)."""

from datetime import date

import pandas as pd
import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.dashboard_dto import (
    CheckNsmAnomaliesRequest,
    CheckPriceAnomaliesRequest,
    GetDashboardRequest,
)
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, empty_state, panel, section_title, stat_row
from frontend.core.formatting import format_datetime, format_number
from frontend.features.yarn_costing.components.columns import ANOMALY_CONFIG, count_col, price_anomaly_rows
from frontend.features.yarn_costing.components.display import fmt_date, percent_text, percent_value, plain
from frontend.features.yarn_costing.components.group_menu import render_group_menu
from frontend.features.yarn_costing.components.labels import (
    FINAL_STATUSES,
    STATUS_LABELS,
    STATUS_ORDER,
    factory_codes,
    factory_label,
    label_of,
)
from frontend.features.yarn_costing.components.recalc_diff import open_recalc_diff_dialog

BOTH = "Cả hai"
NO_DATA = "Không có dữ liệu trong khoảng ngày đã chọn."


class DashboardPage(BasePage):
    title = "[Chung] Dashboard kiểm soát"
    icon = "📊"
    slug = "dashboard"
    description = (
        "Theo dõi hiệu quả báo giá, khả năng đáp ứng, chênh lệch lần tính lại, sai lệch giá và NSM bất thường."
    )

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        render_group_menu(self, reference)
        today = date.today()
        with panel("Bộ lọc", icon="🔎"):
            c1, c2, c3 = st.columns([2, 1, 1], vertical_alignment="bottom")
            choice = c1.segmented_control(
                "Xưởng",
                [BOTH, *factory_codes(reference.factories)],
                default=BOTH,
                format_func=lambda c: c if c == BOTH else factory_label(reference.factories, c),
                key=self.key("factory"),
            )
            date_from = c2.date_input(
                "Từ ngày", value=today.replace(day=1), format="DD/MM/YYYY", key=self.key("date_from")
            )
            date_to = c3.date_input("Đến ngày", value=today, format="DD/MM/YYYY", key=self.key("date_to"))
        factory = None if choice in (None, BOTH) else choice
        if date_from is None or date_to is None:
            st.info("Vui lòng chọn Từ ngày và Đến ngày.")
            return
        if date_from > date_to:
            st.warning("Từ ngày phải trước hoặc bằng Đến ngày.")
            return

        d = feature.get_dashboard(GetDashboardRequest(factory_code=factory, date_from=date_from, date_to=date_to))
        stat_row(
            [
                ("Sợi báo giá", format_number(d.quoted_count)),
                ("Sợi có đơn hàng", f"{format_number(d.ordered_count)} ({percent_text(d.ordered_ratio)})"),
                ("Yêu cầu mới", format_number(d.new_request_count)),
                ("Khả năng đáp ứng", percent_text(d.fulfilment_ratio)),
                ("Đang chờ xưởng xem", format_number(d.waiting_count)),
            ]
        )

        has_chart = bool(d.weekly) and (d.has_data or any(w.new_requests for w in d.weekly) or d.quoted_count > 0)
        if not has_chart:
            empty_state(d.empty_message or NO_DATA)
        else:
            frame = pd.DataFrame(
                [
                    {
                        "Tuần": w.week_start.isoformat(),
                        "Yêu cầu mới": w.new_requests,
                        "Khả năng đáp ứng (%)": percent_value(w.fulfilment_ratio),
                    }
                    for w in d.weekly
                ]
            )
            left, right = st.columns(2)
            left.markdown("**Yêu cầu mới theo tuần**")
            left.bar_chart(frame, x="Tuần", y="Yêu cầu mới", x_label="Tuần (ngày đầu tuần)", y_label="Số yêu cầu")
            right.markdown("**Khả năng đáp ứng theo tuần**")
            right.line_chart(frame, x="Tuần", y="Khả năng đáp ứng (%)", x_label="Tuần (ngày đầu tuần)", y_label="%")

        section_title("Số dòng giá theo trạng thái")
        stat_row(
            [
                (label_of(STATUS_LABELS, s), format_number(d.status_counts.get(str(s), 0)))
                for s in STATUS_ORDER
                if s not in FINAL_STATUSES
            ]
        )

        with panel("Lần tính lại gần nhất", icon="🔁"):
            batch = d.last_batch
            if batch is None:
                empty_state("Không có lần tính lại nào trong khoảng ngày đã chọn.")
            else:
                st.caption(
                    f"{batch.batch_id} · {batch.trigger.value} · hiệu lực {fmt_date(batch.effective_date)} · "
                    f"{batch.run_by or '-'} lúc {format_datetime(batch.run_at)}"
                )
                stat_row(
                    [
                        ("Dòng tăng", format_number(d.last_batch_up)),
                        ("Dòng giảm", format_number(d.last_batch_down)),
                        ("Chênh lệch % trung bình", percent_text(d.last_batch_avg_percent)),
                    ]
                )
                if st.button("Xem chi tiết", icon="🔍", key=self.key("last_batch_detail")):
                    open_recalc_diff_dialog(feature, batch.batch_id, self.key(f"dash_diff.{batch.batch_id}"))

        with panel("Sai lệch giá", icon="⚠️"):
            anomalies = feature.check_price_anomalies(CheckPriceAnomaliesRequest(factory_code=factory))
            stat_row(
                [
                    ("Nhóm vi phạm", format_number(anomalies.group_count)),
                    ("Cặp vi phạm", format_number(anomalies.pair_count)),
                ]
            )
            data_table(
                price_anomaly_rows(anomalies.items),
                column_config=ANOMALY_CONFIG,
                empty_message="Không có cặp mã nào vi phạm.",
                key=self.key("price_anomalies"),
            )

        with panel("NSM bất thường", icon="🧪"):
            nsm = feature.check_nsm_anomalies(CheckNsmAnomaliesRequest(factory_code=factory))
            data_table(
                [
                    {
                        "Xưởng": a.factory_code,
                        "Công nghệ": a.technology,
                        "Nhóm tiêu hao": a.loss_group_key,
                        "Công đoạn": a.stage_code,
                        "Giá trị phổ biến": plain(a.common_value),
                        "Mã khác biệt": a.yarn_code,
                        "NSM của mã": plain(a.nsm),
                        "Lý do đã ghi": a.reason,
                    }
                    for a in nsm.items
                ],
                column_config={
                    "Giá trị phổ biến": count_col("Giá trị phổ biến"),
                    "NSM của mã": count_col("NSM của mã"),
                },
                empty_message="Không có NSM bất thường.",
                key=self.key("nsm_anomalies"),
            )
