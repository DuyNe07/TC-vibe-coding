# Sewing Performance - mở rộng 2026-11-13 lần 4 (Prompt 5): Overview mới (hàng & khách), dữ liệu 2025

## Thêm và thay đổi
1. Overview (Screen 1):
   - bỏ biểu đồ "Output vs Target (with ratio - system) by factory" và cả phần Ranking (10 chuyền cao nhất / thấp
     nhất, nút chọn chỉ số) (BR-92);
   - giữ thứ tự: bộ lọc, 7 thẻ số, bảng chỉ số theo xưởng (luôn mở, chỗ cũ) + nút tải báo cáo tuần, 2 biểu đồ theo ngày
     (%Efficiency, MO 8h) xếp cạnh nhau;
   - thêm khu "Products & customers" (BR-93 đến BR-96): Cơ cấu hàng theo xưởng (% sản lượng) + bảng pcs / %;
     Top 10 nhóm khách hàng theo sản lượng (mỗi xưởng một màu); Giá CM trung bình theo nhóm hàng; Cơ cấu hàng theo tháng.
2. Dữ liệu 2025 (BR-97): file chỉ có sheet `Production data` được nhận khi mọi ngày trong file trước 01/01/2026
   (sửa BR-02). Số thợ mỗi ngày của xưởng = tổng số người (REVISE MO, BR-21) của các chuyền trong ngày, app tự tính và
   lưu (4.3, trường mới `derived`). Không có Target system: %Efficiency (with ratio - system) "-"; không có tổng nhân
   sự: %Direct labor "-". Đổi số chuyền Fac 1 (BR-11) áp cả cho 2025. Tải một lần ở Data Update, dữ liệu ở lại; tải
   file 2026 sau này không đụng tới 2025 (BR-07: mỗi sheet chỉ thay khoảng ngày của chính nó).
3. Xưởng cũ đã giải thể "SHCM-Factory 1" (BR-98): lưu lại để tham khảo với tên "Fac 1 HCM (closed)", không hiện ở màn
   hình, bộ lọc, thẻ, bảng, biểu đồ hay file Excel nào.

## Ảnh hưởng tới phần đã có
- UC-05 đổi nội dung biểu đồ; BR-44 (xếp hạng) bỏ khỏi màn hình; BR-02 có ngoại lệ năm cũ; BR-06 thêm 1 tên xưởng.
- Dữ liệu: thêm dòng 2025 (khoảng 40 nghìn dòng sản lượng, dưới giới hạn 200 nghìn của một bảng); dòng số thợ cũ
  có `derived` = không. Không xoá dòng nào. Các màn hình mở lần đầu có thể chậm hơn một chút vì dữ liệu gấp đôi.
- File 2026 thiếu sheet vẫn bị từ chối như cũ.

## Câu hỏi đã trả lời (13/11/2026)
"1a, 2abcd, 3b, 4a, 5a, 6 Fac 1 là 1 xưởng cũ đã giải thể nên có trong data, không cần để nó vào giao diện bây giờ,
chỉ để ref cho 2025".

## Truy vết
| Mục | Code | Kiểm tra |
|---|---|---|
| BR-92 | `overview_page.py`, `overview_charts.daily_charts` | dựng Overview với dữ liệu thật: không còn Output vs Target và Ranking, 6 biểu đồ, không lỗi ✅ (AC-132) |
| BR-93 | `ProductMixBusiness.top_groups` / `shares`, `product_mix_blocks._mix_chart` / `_mix_table` | AC-133 + bài 5 nhóm + Other ✅; màu nhóm thống nhất giữa 2 biểu đồ ✅ |
| BR-94 | `ProductMixBusiness.top_customers`, `_customers_chart` | AC-134 ✅ |
| BR-95 | `ProductMixBusiness.cm_prices`, `_cm_chart` | AC-135 ✅ |
| BR-96 | `ProductMixBusiness.monthly`, `_monthly_chart` | AC-136 ✅ |
| BR-97, 4.3 `derived` | `UploadBusiness.ensure_sheets` / `parse` / `derived_workers`, `RawWorkbookBuilder._read` | AC-137, AC-138 ✅; đọc thử file thật `Data sewing 2025 (format 2026).xlsx` (không lưu): 39,567 dòng, bỏ qua 0, 1,282 dòng số thợ tính ra ✅ |
| BR-98 | `Factory.FAC_1_HCM`, `REPORT_FACTORIES`, `ALL_FACTORIES` | AC-139 ✅; file 2025 thật: 3,146 dòng Fac 1 HCM (closed) đọc được |
| regression: existing tests | toàn bộ bài kiểm tra của app | quality gate: ALL CHECKS PASSED (496 passed) ✅; health check: APP IS HEALTHY ✅ |

Chưa làm: tải file 2025 vào cơ sở dữ liệu chung (người dùng tự tải ở Data Update).

## Fix log
