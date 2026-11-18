# Sewing Performance - mở rộng 2026-11-06 (Prompt 5)

## Thêm và thay đổi
1. Card "Vinh Long - HCM" (BR-58): một nút ＋ chung ở đầu khu card. Bật lên thì dưới dòng HCM của cả 5 card hiện thêm
   Fac 2, Fac 3, Fac 5, mỗi dòng có thanh so sánh như Vinh Long và HCM. Tắt thì về như cũ (BR-60).
2. Bảng "Metrics by factory" ở Screen 1 (BR-61):
   - Đổi tên ở màn hình, biểu đồ, file Excel: "%Efficiency (with ratio - sum)" thành "%Efficiency (with ratio)",
     "Target (with ratio - sum)" thành "Target (with ratio)" (sửa BR-56).
   - Thứ tự dòng: Target (with ratio), Output, %Efficiency (with ratio), %Efficiency (with ratio) vs target,
     Target B (no ratio), %Efficiency B (no ratio), CM earning, MO 8h, Average CM price, Average working hours,
     Line strength match, Weekly changeover, Weekly changeover per line.
   - Ẩn mặc định: %Efficiency target, MO 8h target, MO 8h vs target, và 3 dòng with ratio - system. Một nút gạt
     "Show targets & with ratio - system" mở lại tất cả, xếp về đúng nhóm (sửa BR-59).
   - Cột "Category" bên trái, nhãn màu nhẹ theo nhóm: Output, Efficiency, CM, MO 8h, Other. Dòng chính vẫn in đậm.

## Ảnh hưởng tới phần đã có
- Không đổi cách tính, không đổi dữ liệu đã lưu, không cần chuyển dữ liệu. Không xoá dòng nào.
- Thứ tự dòng mới chỉ áp dụng cho bảng ở Screen 1. Bảng ở Screen 3 và file Excel báo cáo tuần giữ thứ tự cũ; file Excel
  chỉ đổi tên (BR-52).
- Bài kiểm tra cũ giữ nguyên. Hai bài ghim tên "%Efficiency (with ratio - sum)" (`test_sewing_performance.py`,
  `test_efficiency_kinds.py`, thêm ngày 05/11) phải đổi theo tên mới vì người dùng đổi tên: chỉ đổi chuỗi tên, không đổi số.

## Câu hỏi đã trả lời (06/11/2026, "Ok hết đề xuất")
1. Nút ＋: một nút chung cho cả 5 card.
2. Đổi tên ở màn hình, biểu đồ và Excel.
3. Một nút gạt cho các dòng target và with ratio - system.
4. Thứ tự dòng như trên; "%Efficiency (with ratio) vs target" vẫn hiện.
5. Cột Category có nhãn màu nhẹ.

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| BR-60 | `components/overview_charts.py::group_summary`, `_hcm_detail_button` | trình duyệt: 5 card cùng cao, Fac 2 + 3 + 5 khớp HCM (AC-66) |
| BR-61 | `components/report_cells.py::grouped_metric_rows`, `METRIC_GROUPS`, `HIDDEN_METRICS`; `pages/overview_page.py` | trình duyệt: 13 dòng mặc định, bật nút gạt thêm đúng 6 dòng (AC-67, AC-69) |
| BR-56 (sửa tên) | `dto/display_names.py` (`EFFICIENCY_SUM`, `TARGET_SUM`) | `test_sewing_performance.py`, `test_efficiency_kinds.py` (AC-68) |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` |
