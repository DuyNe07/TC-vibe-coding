# Extension 2026-11-25 (b) - woven_costing: phiếu gia công nhuộm nhiều mã hàng (NGC)

## Thêm / thay đổi
- Màn hình 8 "Gia công nhuộm" (nhóm Sales): danh sách phiếu + phiếu đang mở (đầu phiếu, bảng dòng mã hàng, chi tiết
  dòng, tổng, nút).
- Dữ liệu mới: 4.21 phiếu, 4.22 dòng, 4.23 kết quả, 4.24 bảng hệ số vận hành (trong bộ tham số).
- UC-40..UC-46, BR-92..BR-99, F-09 (Excel như sheet Output), AC-76..AC-83.
- Sửa BR-02: chỉ bỏ chữ "G" đầu mã khi mã dài hơn 10 ký tự; thông báo ghi mã sau khi làm sạch.
- Cách tính theo file NGC (Power Query của "Forrmat NGC Nhuộm TCDN.xlsm"):
  - hóa chất công đoạn: CPB theo bảng; Santa / Bonding / Coating / Soaping = giá sales nhập (không chia co, tiêu hao);
    Mercerizing / Suse 2 theo bảng ÷ (1 − tiêu hao); khác = 0;
  - 6 khoản còn lại × (1 + n) ÷ (1 − co) ÷ (1 − tiêu hao) ÷ hệ số vận hành; "Phụ trợ" không chia co; CPB không chia tiêu hao;
  - nhuộm tiêu chuẩn, WR, tính năng như BR-25; × h (chiết khấu / phụ phí);
  - báo giá riêng thay toàn bộ;
  - Định mức TP = ÷ (1 − % B/C); chi phí = SL × định mức TP; giá GC = SL × đơn giá; GP, %GP.

## Ảnh hưởng tới phần đã có
- Costsheet thường (Màn hình 2) không đổi cách tính; phiếu Gia công nhuộm 1 mã vẫn giữ.
- Bộ tham số (4.6) thêm bảng 4.24; bộ cũ đọc bảng với giá trị ban đầu (không đổi dữ liệu đã lưu).
- Màn hình 3 Việc chờ tôi thêm phiếu gia công chờ duyệt / bị trả lại; Màn hình 5 thêm bảng hệ số vận hành.
- BR-02 sửa: mã đã lưu không đổi (chỉ ảnh hưởng mã gõ / nhập mới).

## Dữ liệu đã lưu
- 2 bảng mới (phiếu gia công, dòng gia công) có cờ xóa; không đụng bảng cũ.
- Bộ tham số: trường mới có mặc định; không cần chuyển dữ liệu.

## Câu hỏi đã trả lời (2026-11-25, "theo đề xuất")
1. Một phiếu nhiều dòng, duyệt 1 lần.  2. Tính đúng file NGC, SO sửa hệ số vận hành.  3. Kết quả như sheet Output
(GP, %GP, cảnh báo ngưỡng chung).  4. % B/C mặc định 0%.  5. Có số lần xử lý thêm, 2 tính năng, báo giá riêng.
6. Có Xuất Excel.  7. Chọn được HCM, mặc định TCDN.
- Thêm: gia công dệt giữ như costsheet thường; mã hàng, độ co sales tự gõ.

## Giao diện
Đã chốt trong câu trả lời trên (bảng dòng sửa trong ô + chi tiết dòng, mặc định TCDN) -> bỏ vòng hỏi giao diện riêng.

## Traceability
| Spec item | Code element | Test | Status |
|---|---|---|---|
| 4.21..4.23 | models/dyeing_job.py, repositories | test_dyeing_job_20261125 | ✅ |
| 4.24, BR-93 | models/parameter_set.py / parameter_tables.py, parameter_editor | test_dyeing_job_20261125 | ✅ |
| BR-92, BR-94, BR-95 | business/dyeing_job_business.py (dùng lại dyeing_tcdn / dyeing_hcm) | test_dyeing_job_20261125 (AC-76..AC-79) | ✅ |
| BR-96..BR-99, UC-40..UC-45 | services/*dyeing_job*, controller | test_dyeing_job_20261125 (AC-80) | ✅ |
| UC-46, F-09 | builders/dyeing_job_excel_builder.py | AC-81 | ✅ |
| BR-02 sửa | business/fabric_business.py | AC-82 | ✅ |
| Screen 8, Screen 3, Screen 5 | frontend pages/dyeing_job_page.py, manifest | render | ✅ |
| regression: existing tests (AC-09 …) | | toàn bộ test cũ | ✅ |

(Mọi dòng trên: ✅ 2026-11-25.)

## Kết quả (2026-11-25)
- check.py: ALL CHECKS PASSED (472 test, 8 test mới); migrate status: up to date (woven_costing 0001); doctor: APP IS
  HEALTHY.
- Phiếu S-ONE: mỗi dòng 4.860,52 đ/m, tổng chi phí 68.586.774,56, giá GC 111.553.141,73, %GP 38,52% (khớp file).
- Trình duyệt: Màn hình 8 tạo phiếu GC-SONE-2026-00001 (mặc định TCDN), mở phiếu, tự tính khi sửa số lần xử lý thêm
  (4.861 -> 5.836 đ/m, không lưu); Màn hình 5 thẻ Nhuộm TCDN có bảng hệ số vận hành.
- Không sửa test cũ: thông báo BR-02 giữ câu cũ.
