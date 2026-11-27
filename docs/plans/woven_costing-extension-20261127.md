# woven_costing – Mở rộng 2026-11-27: sắp xếp lại Màn hình 2 (Costsheet) cho dễ thấy chỗ nhập

## Yêu cầu của người dùng
"Thông tin đơn và chuỗi nhu cầu bị dài, các khung cùng màu làm khó nhận định được là bấm chọn vào đâu để tiếp tục,
nhấp là ở phần nhập liệu, nên làm cho nó nổi bật hơn hoặc sắp xếp lại cho hợp lý hơn." + "cho khung nhập liệu qua màu
khác".

## Câu hỏi đã trả lời (2026-11-27)
| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Khối Thông tin đơn | a) hiện sẵn ô chính; các ô còn lại gom vào mục "Thông tin thêm", bấm mới mở |
| 2 | Khối Chuỗi nhu cầu | a) thành thẻ riêng "Chuỗi nhu cầu", cạnh thẻ Giá bán & lợi nhuận |
| 3 | Phân biệt nhập / chỉ xem | a) tên thẻ cần nhập có ✏️; nhãn xanh "Nhập liệu" / nhãn xám "Chỉ xem" |
| 4 | Thứ tự thẻ | b) giữ thứ tự hiện tại (thẻ Chuỗi nhu cầu chen ngay sau Giá bán & lợi nhuận) |
| 5 | Dòng hướng dẫn | a) có, ở đầu phiếu |
| + | Khung nhập liệu màu khác | Ứng dụng chỉ tô màu được **dải tiêu đề** của khung (không tô cả nền khung): khung nhập có dải tiêu đề nền xanh, khung chỉ xem dải xám |

## Thay đổi
Chỉ đổi cách sắp xếp và hiển thị Màn hình 2. Không đổi dữ liệu, quy tắc, công thức, file, vai trò.
- Khối Thông tin đơn: hàng ô chính = Nhà máy nhuộm, Khách hàng (+ Thêm khách hàng), Mã vải, Số lượng đặt (m), Hình
  thức bán, Loại giá, Giá mộc mua ngoài (chỉ khi Vải Nhuộm). Mục thu gọn "Thông tin thêm": Thị trường, Loại đơn hàng,
  Style, Ngày giao hàng, Ngày tính giá, Số OC, Lý do ngoại lệ độ co, Lý do độ co thấp / bằng 0, Ghi chú. Mục tự mở khi
  phiếu "Độ co thấp" mà chưa có lý do; tiêu đề mục nhắc "Độ co thấp – cần lý do" trong trường hợp đó.
- Chuỗi nhu cầu: bỏ khung giữa trang, thành thẻ "Chuỗi nhu cầu" (chỉ xem, cùng nội dung, cùng các dòng theo hình thức bán).
- Thứ tự thẻ: Giá bán & lợi nhuận → Chuỗi nhu cầu → Thông số vải → Nhuộm → Ngành Dệt → Sợi → Tham số → Cảnh báo →
  Lịch sử (thẻ Nhuộm / Ngành Dệt / Sợi vẫn ẩn theo hình thức bán như BR-89 / BR-90).
- Dấu ✏️ trên tên thẻ có ô nhập: Giá bán & lợi nhuận, Nhuộm, Ngành Dệt, Sợi, Tham số. Số cảnh báo vẫn hiện trong ngoặc.
- Dải tiêu đề nền xanh + nhãn "Nhập liệu" ở khung Thông tin đơn và ở đầu các bảng / khung sửa được; dải xám + nhãn
  "Chỉ xem" ở Chuỗi nhu cầu, Thông số vải (nguồn Peace / WFX), bảng kết quả.
- Dòng hướng dẫn đầu phiếu (chỉ khi phiếu còn sửa được): "① Điền Thông tin đơn → ② Nhập ở các thẻ ✏️ → ③ Xem Giá
  bán & lợi nhuận → ④ Lưu nháp / Gửi duyệt". Phiếu chỉ xem: không hiện dòng này, không hiện ✏️ / nhãn "Nhập liệu".
- Khung "Tạo costsheet mới" giữ nguyên.

## Bổ sung sau khi dùng thử (2026-11-27)
Người dùng: "nhập giá ở 1 dòng thì phải đợi loading mới nhập tiếp dòng sau". Chọn a): các bảng nhập nhiều dòng nhập
liền (bảng chạy riêng, không tính sau mỗi ô), nút "Áp dụng & tính" dưới mỗi bảng; ô lẻ vẫn tự tính; Lưu nháp / Gửi
duyệt lấy số đang nhập. UC-16 sửa, AC-94.

## Ảnh hưởng tới phần đang có
- UC / BR: không đổi. Screen 2 + Giao diện đã chốt: ghi đổi giao diện 2026-11-27 (thay mục 3, 4, 5 của đổi giao diện
  2026-11-23).
- AC mới: AC-89..AC-93 (AC-93 là hồi quy: cùng số, cùng kết quả, mọi ô cũ vẫn có).
- Dữ liệu đã lưu: không đổi gì, không cần chuyển dữ liệu.

## Kế hoạch làm (sau "đồng ý")
`frontend/features/woven_costing/` only: `components/costsheet_order.py` (ô chính + "Thông tin thêm"),
`components/costsheet_chain.py` (thẻ), `pages/costsheet_page.py` (thứ tự thẻ, ✏️, dòng hướng dẫn), các component thẻ
(nhãn "Nhập liệu" / "Chỉ xem"). Màu chỉ dùng chữ tô nền sẵn có của ứng dụng (không thêm kiểu trang riêng). Kiểm tra:
`scripts/check.py`, `scripts/doctor.py`, mở trình duyệt xem phiếu thật.
