# yarn_costing - mở rộng 2026-11-13: phương án bông riêng cho lần tính, pha bông Supima, phí Supima coin

Nguồn: `docs/business/_sources/yarn_costing-supima-discovery.md`; dữ liệu thật S4: nhóm tiêu hao "CM (SUPIMA 100%)" tổng 21,70%,
"CM" 24,20%, "CM COMPACT" 24,20%; nhóm giá "Cotton Pima" BQ tháng 11/2026 = 3,6267 USD/kg.

## 1. Thêm / đổi gì
| # | Nội dung | Mục / UC / BR / AC |
|---|---|---|
| 1 | Phương án bông riêng cho lần tính (mặc định = khai báo tháng), lưu trong báo giá | 4.28 `cotton_plan`, UC-62, BR-110, AC-149 |
| 2 | Pha bông Supima: (1 − s) bông thường ÷ (1 − tiêu hao CM / CM COMPACT) + s × (Supima + phí coin) ÷ (1 − tiêu hao CM (SUPIMA 100%)) | 4.28, 4.28.1, UC-62, BR-94 (sửa), BR-111, AC-148 |
| 3 | Tỷ lệ Supima đọc từ tên, Sales sửa được | BR-112, AC-147 |
| 4 | Ô tick "Truyền điểm Supima coin trên TG" (mặc định tắt), phí coin = giá coin × (1 + thuế nhà thầu) | 4.28, BR-111, AC-148 |
| 5 | Khai báo tháng: nhóm giá Supima, giá coin 0,552, thuế nhà thầu 5% (chép từ tháng trước) | 4.25, UC-58, BR-113, AC-150 |
| 6 | Hiển thị động: khối Pha bông chỉ khi sợi có bông; ô tick coin chỉ khi Tỷ lệ Supima > 0 | UC-62, Screen 13, AC-147 |
| 7 | File Excel báo giá thêm 4 cột | 5.12, UC-63, AC-151 |

## 2. Ảnh hưởng tới cái đang có
- Sợi không có Supima và phương án mặc định: kết quả y như trước (AC-152).
- Khai báo tháng thêm 3 ô; tháng đã lưu đọc được (mặc định nhóm Supima trống, coin 0,552, thuế 5%).
- Chưa có báo giá nào được lưu → không có dữ liệu cũ cần chuyển.

## 3. Dữ liệu đã lưu
- Trường mới có mặc định, bản ghi cũ (khai báo tháng 11/2026) đọc được; không cần chuyển đổi.

## 4. Câu hỏi đã trả lời (2026-11-13)
- Pima / Supima pha thêm vào phương án bông; hồi phế Supima 0,30 riêng; hiện chỉ bông pha ở ăn bông.
- Hai công thức (có / không truyền điểm coin trên TG), ô tick để Sales chọn.
- Tiêu hao Supima lấy từ nhóm "CM (SUPIMA 100%)"; bông thường lấy nhóm "CM" / "CM COMPACT" (b).
- Giá coin + thuế khai báo hằng tháng (2a); phương án riêng chỉ cho lần tính (3a); tỷ lệ Supima đọc từ tên (4).
- Ô tick coin mặc định tắt; khối pha bông ẩn / hiện theo sợi; giữ 4 cột Excel; chưa có báo giá cũ.

## 5. Đã làm (2026-11-13)
- Code + test AC-147..AC-151 xong, test cũ vẫn đạt (AC-152); bản đồ ở mục 11 của tài liệu.
- Chạy thử màn Tính giá báo khách trên dữ liệu tạm: sợi PE không hiện khối Pha bông; sợi CM (SUPIMA 50%) COMPACT hiện USA / Brazil / Tỷ lệ Supima 50% + ô tick coin, tính ra kết quả không lỗi.
- `scripts/check.py` ALL CHECKS PASSED (303 test), `scripts/doctor.py` APP IS HEALTHY.
