# yarn_costing - mở rộng 2026-11-19: đổi tên sợi sang nhóm tiêu hao đã có khi sợi chưa có giá

Nguồn: người dùng gặp lỗi trên server ngày 18/11/2026. Họ muốn đổi tên S1-1328 "Cotton/Pinapple 30/1 (70/30)", trạng thái Chưa tính
được, thành "COTTON/PINEAPPLE 30/1 (70/30)". App báo "Nhóm tiêu hao 'COTTON/PINEAPPLE (70/30)' đã có; đổi tên sẽ làm đổi tiêu hao...".
Thực tế sợi chưa có giá nên không có tiêu hao nào bị đổi. Nhóm theo tên viết sai không có ở xưởng, nên chính vì vậy sợi chưa tính được.

## 1. Thêm / đổi gì
| # | Nội dung | Mục / UC / BR / AC |
|---|---|---|
| 1 | Đổi tên làm nhóm tiêu hao mới K' **đã có** ở xưởng thì vẫn cho đổi, khi một trong hai điều kiện đúng: nhóm cũ K không có ở xưởng, hoặc mã gốc và mọi bản ĐCNSM đều chưa có giá (không có bản Đã tính giá / Có mã kế toán). Khi đó sợi dùng nhóm K' có sẵn; nhóm K giữ nguyên, không đổi tên, không xoá | BR-105 (sửa), AC-166, AC-169 |
| 2 | Sợi đã có giá đổi tên sang nhóm khác đã có → vẫn chặn, câu báo như cũ | BR-105, AC-167 |
| 3 | Sau khi đổi, các bản "Chưa tính được" được tính lại ngay theo nhóm K' (như BR-40); đủ dữ liệu → "Đã tính giá", thiếu → giữ "Chưa tính được" với lý do mới | BR-105, UC-68, AC-166, AC-168 |
| 4 | Câu báo khi đổi: thêm nhóm tiêu hao đã dùng và kết quả tính giá | UC-68, AC-166 |
| 5 | Đổi tên hàng loạt bằng file (UC-69) dùng cùng quy tắc | UC-69 (qua BR-105), AC-169 |

## 2. Ảnh hưởng tới cái đang có
- Các trường hợp khác của BR-105 giữ nguyên: K' = K; K' chưa có (đổi tên nhóm K); K còn dùng cho sợi khác khi K' chưa có; chặn đổi chi số / công nghệ / compact.
- Sợi đã có giá không bị đổi giá nào. Không tính lại toàn bộ.
- Trước đây UC-68 ghi "Không tính lại giá". Nay chỉ tính lại các bản Chưa tính được, trong đúng trường hợp mục 1.

## 3. Dữ liệu đã lưu
- Không thêm trường, không thêm bảng, không cần chuyển đổi dữ liệu. Nhóm tiêu hao cũ không bị xoá.

## 4. Câu hỏi đã trả lời (2026-11-18, người dùng trả lời "ok" = dùng toàn bộ đề xuất)
1. Cho đổi khi nhóm cũ không có ở xưởng HOẶC sợi chưa có giá (1a).
2. Sợi đã có giá: vẫn chặn (2a).
3. Tự tính lại giá ngay nếu đủ năng suất máy (3a).
4. Nhóm tiêu hao theo tên cũ: giữ nguyên (4a).
5. Câu báo "Đã đổi tên ...; sợi dùng nhóm tiêu hao '...' đã có; đã tính giá: ... đ/kg." (5a).
