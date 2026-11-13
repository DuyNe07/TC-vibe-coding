# Sewing Performance - mở rộng 2026-11-13 lần 3 (Prompt 5): "Line trend" có màu theo kết quả, "Back to filters"

## Yêu cầu của người dùng
Gộp 2 biểu đồ của "Line trend" thành 1 (cột + đường, nhiều màu như hình Shortship), ghi số lên biểu đồ, có nút ẩn / hiện
số; ô bộ lọc đi theo khi kéo trang.

## Không làm được trong app (thuộc khung sườn) và người dùng chọn không gửi đề nghị (1b)
Biểu đồ gộp cột + đường hai trục có số trên điểm và nút ẩn / hiện số; ô bộ lọc dính đầu trang.

## Thêm và thay đổi (BR-91)
1. Cột Output của mỗi kỳ có màu theo %Efficiency (with ratio): "On target" (xanh dương), "Below threshold" (cam),
   "No number" khi không có %Efficiency; có chú thích màu. Ngưỡng theo mức của ngày cuối kỳ (BR-26, BR-28).
2. By week hiện 26 tuần gần nhất tính đến "Đến ngày" (sửa BR-90, trước đây từ 01/01), để luôn vẽ được cột có màu;
   By month, By year giữ từ 01/01.
3. Đầu khối chi tiết chuyền: dòng tóm tắt bộ lọc đang chọn và liên kết "Back to filters" cuộn về ô bộ lọc.

## Ảnh hưởng tới phần đã có
- Đổi: số kỳ của By week (BR-90, AC-126 vẫn đúng vì tuần cuối không đổi).
- Không đổi: số của từng kỳ, biểu đồ đường, bảng số, bảng chuyền, bảng đơn hàng. Không lưu thêm dữ liệu.

## Câu hỏi đã trả lời (13/11/2026): "1b 2a 3a"

## Truy vết
| Mục | Code | Kiểm tra |
|---|---|---|
| BR-91 màu cột | `line_trend_blocks._status`, `_output_chart` | dựng thử với dữ liệu thật LINE 1 Fac Vinh Long: chuỗi "On target" #2E5AAC (xanh dương), "Below threshold" #E8850F (cam) ✅ (AC-129) |
| BR-91 26 tuần | `GetLineDetailService._trend_periods`, `TREND_WEEKS` | AC-130 ✅ (`test_line_trend.py`); dữ liệu thật: 26 tuần W19 (02.05–08.05) đến W44 (24.10–30.10) ✅ |
| BR-91 Back to filters | `line_detail_page._filter_note`, `FILTERS_ANCHOR`, `line_details(filter_note=)` | dựng thử: dòng tóm tắt đúng bộ lọc, liên kết `#filters` ✅; cuộn trang trong trình duyệt: chưa xem (cần đăng nhập) (AC-131) |
| regression: existing tests | toàn bộ bài kiểm tra của app | quality gate: ALL CHECKS PASSED (488 passed) ✅; health check: APP IS HEALTHY ✅ |

## Fix log
