# woven_costing – Mở rộng 2026-11-27 (2): duyệt nhiều phiếu ngay trên "Việc chờ tôi"

## Yêu cầu của người dùng
"Tôi không thể duyệt trên màn hình việc chờ tôi mà phải click mở để duyệt từng phiếu hả?" -> muốn duyệt hàng loạt;
"đề xuất và hỏi lại các thông tin cần thể hiện ở bảng đó để sales leader có thể nhìn bên ngoài và duyệt".

## Câu hỏi đã trả lời
| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Cột bảng duyệt | Đề xuất + thêm Tên vải, Thị trường, Nhà máy nhuộm, Ngày giao hàng, Độ co (%), GP (đ/m), Giá có VAT, Tiền sợi / Dệt / Nhuộm (đ/m) |
| 2 | Cách thể hiện điểm cần chú ý | a) 1 cột chữ "Cần chú ý"; GP% / OP% dưới ngưỡng tô đỏ |
| 3 | Phiếu có điểm cần chú ý duyệt hàng loạt? | a) Được, hộp xác nhận liệt kê riêng |
| 4 | So phiên bản đã duyệt | a) Có: Giá bán trước → nay, GP% trước → nay |
| 5 | Trả lại | a) Ngay trên bảng (1 phiếu, nhập lý do) |
| 6 | Xem nhanh | b) Không cần, bấm Mở |
| 7 | Phiếu gia công nhuộm | a) Cũng duyệt nhiều phiếu, cột riêng |

## Thay đổi
- UC-47 (duyệt nhiều costsheet), UC-48 (duyệt nhiều phiếu gia công); UC-30 sửa (cột, nút).
- BR-101 Cần chú ý, BR-102 duyệt nhiều phiếu (từng phiếu kiểm tra riêng, phiếu lỗi không chặn phiếu khác), BR-103 so
  phiên bản đã duyệt.
- Screen 3 + Giao diện đã chốt: bảng Chờ tôi duyệt (29 cột theo thứ tự), bảng Phiếu gia công chờ tôi duyệt (10 cột).
- AC-95..AC-100 (AC-100 hồi quy các nhóm khác và duyệt từng phiếu).

## Ảnh hưởng tới phần đang có
- Duyệt từng phiếu trong Màn hình 2 / Màn hình 8 không đổi (dùng lại đúng UC-21 / UC-22 / UC-43).
- Các nhóm khác của Việc chờ tôi giữ nguyên.
- Dữ liệu đã lưu: không thêm / đổi trường nào; các cột mới đọc từ phiếu, kết quả tính, Chuỗi nhu cầu và lịch sử có
  sẵn. Không cần chuyển dữ liệu.

## Kế hoạch làm (sau "đồng ý")
Backend: dto dòng việc chờ thêm trường; builder dòng chờ duyệt (Cần chú ý, so phiên bản, tiền sợi / dệt / nhuộm từ chuỗi
nhu cầu, ngày gửi duyệt từ lịch sử); service + controller "duyệt nhiều phiếu" (costsheet và phiếu gia công) gọi lại đúng
logic duyệt một phiếu; test cho BR-101..BR-103, UC-47, UC-48. Frontend: my_tasks_page (bảng nhiều dòng, hộp xác nhận,
trả lại trên bảng). Kiểm tra: check.py, doctor.py, trình duyệt.
