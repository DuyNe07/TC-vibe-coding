# Ghi chép tìm hiểu nghiệp vụ: Sắp xếp menu theo mục đích và đơn vị sử dụng

| Ngày | 2026-09-26 |
|---|---|
| Người trao đổi | Phòng SO (claude09@thanhcong.com.vn) |
| Trạng thái | Đã xác nhận với người dùng |

## 1. Công việc hiện tại
Hai chức năng "Điều chuyển chi phí nội bộ" (`internal_cost_transfer`) và "Tính giá sợi" (`yarn_costing`) cùng nằm trong nhóm
"Tài chính - Kế toán" trên Trang chủ và menu; các màn hình trong mỗi chức năng không thể hiện đơn vị nào dùng.

## 2. Mong muốn (kết quả cuối cùng)
- Tách hai chức năng ra hai nhóm riêng trên Trang chủ / menu, đặt tên theo mục đích sử dụng.
- Sắp các màn hình theo đơn vị sử dụng, ghi đơn vị trước tên màn hình, để chuẩn bị cho phân quyền sau này.
- Ẩn chức năng mẫu khỏi Trang chủ và menu.

## 3. Dữ liệu vào
Không có (chỉ đổi cách hiển thị).

## 4. Dữ liệu ra
Không có.

## 5. Quy tắc đã chốt
- Nhóm Trang chủ: `internal_cost_transfer` → **"Chi phí nội bộ"**; `yarn_costing` → **"Giá thành sợi"** (giữ tên đề xuất).
- Cách thể hiện đơn vị (lựa chọn 2a): sắp màn hình theo thứ tự đơn vị và ghi nhãn đơn vị trước tên màn hình, ví dụ
  "[Sales] Yêu cầu tính giá"; không thêm tiêu đề con trong menu (không sửa phần khung dùng chung).
- Tính giá sợi, thứ tự màn hình:
  - Dùng chung: Bảng giá đã tính (trang chính), Dashboard kiểm soát
  - Sales: Yêu cầu tính giá
  - Xưởng sợi: Nhập NSM & tính giá, Tiêu hao
  - Phòng SO: Dữ liệu nền & định mức, Nhập dữ liệu từ Excel, Người dùng & nhật ký
  - Kế toán: nhập mã kế toán ngay trên Bảng giá (không có màn hình riêng)
- Điều chuyển chi phí nội bộ, thứ tự màn hình:
  - Đơn vị: Giao dịch của đơn vị tôi (trang chính), Duyệt theo hạn mức, Báo cáo theo đơn vị
  - Dùng chung: Danh sách giao dịch, So sánh chi phí theo tháng, Báo cáo giao dịch treo
  - Phòng SO: Khai báo đơn vị, Khai báo loại chi phí, Khai báo hạn mức duyệt, Chốt sổ hằng tháng
- Chức năng mẫu "Nhập sản phẩm từ Excel (mẫu)": ẩn khỏi Trang chủ và menu (lựa chọn 3a).

## 6. Quy mô, tần suất, người dùng
Như hai chức năng hiện có.

## 7. Chia thành chức năng
Không tạo chức năng mới: cập nhật tài liệu và giao diện của `internal_cost_transfer` và `yarn_costing`.

## 8. Khả năng đã kiểm tra
- Làm được: đổi nhóm Trang chủ, thứ tự và tên màn hình của từng chức năng.
- Không làm được trong quy trình tính năng: tiêu đề con trong menu (phải sửa khung dùng chung); đăng nhập / ẩn màn hình theo
  người dùng (cần nâng cấp khung sườn).
- Chức năng mẫu là chức năng tham chiếu của khung sườn; quy tắc không cho sửa nó trong quy trình tính năng → việc ẩn cần người
  phụ trách khung sườn thực hiện.

## 8b. Yêu cầu gửi người phụ trách khung sườn (người dùng chọn phương án b, 2026-09-26)
Người dùng quyết định **chờ khung sườn nâng cấp xong mới đổi menu** của 2 chức năng; hiện chưa đổi gì trong 2 chức năng.

**YC-01 - Menu gấp / mở theo nhóm đơn vị**
- Trong menu bên trái, mỗi chức năng là một khối gấp / mở (bấm để mở danh sách màn hình con, bấm lại để thu gọn).
- Bên trong một chức năng, các màn hình được chia thành nhóm con (ví dụ "Dùng chung", "Sales", "Xưởng sợi", "Phòng SO",
  "Đơn vị"), mỗi nhóm con cũng gấp / mở được.
- Phần khai báo chức năng cần thêm thông tin "màn hình thuộc nhóm con nào" để mỗi chức năng tự khai báo.
- Nhóm trên Trang chủ và menu: "Chi phí nội bộ" (Điều chuyển chi phí nội bộ), "Giá thành sợi" (Tính giá sợi).
- Nhóm con dự kiến - Tính giá sợi: Dùng chung (Bảng giá đã tính, Dashboard kiểm soát); Sales (Yêu cầu tính giá); Xưởng sợi
  (Nhập NSM & tính giá, Tiêu hao); Phòng SO (Dữ liệu nền & định mức, Nhập dữ liệu từ Excel, Người dùng & nhật ký).
  Điều chuyển chi phí nội bộ: Đơn vị (Giao dịch của đơn vị tôi, Duyệt theo hạn mức, Báo cáo theo đơn vị); Dùng chung
  (Danh sách giao dịch, So sánh chi phí theo tháng, Báo cáo giao dịch treo); Phòng SO (Khai báo đơn vị, Khai báo loại chi phí,
  Khai báo hạn mức duyệt, Chốt sổ hằng tháng).

**YC-02 - Đăng nhập và phân quyền**
- Người dùng cần đăng nhập trước khi dùng app; mỗi tài khoản thuộc một hoặc nhiều nhóm (Sales, Xưởng S1, Xưởng S4, Phòng SO,
  Kế toán, các đơn vị của chức năng Điều chuyển chi phí).
- Chỉ hiện trên menu các chức năng / nhóm màn hình mà tài khoản được dùng (dựa trên nhóm con của YC-01).
- Hai phương án để người phụ trách khung sườn (và IT) chốt - người dùng chưa chọn:
  - Cách 1: đăng nhập bằng tài khoản Microsoft 365 công ty (@thanhcong.com.vn); cần IT đăng ký ứng dụng.
  - Cách 2: app tự quản lý tên đăng nhập / mật khẩu (lưu mật khẩu an toàn), có màn hình quản lý tài khoản.
- Sau khi có đăng nhập: 2 chức năng hiện tại bỏ bước "chọn nhóm + nhập mã nội bộ + chọn tên", dùng tài khoản đăng nhập; quy
  tắc phân quyền theo nhóm của từng chức năng giữ nguyên.

**YC-03 - Ẩn chức năng mẫu**
- Ẩn "Nhập sản phẩm từ Excel (mẫu)" khỏi Trang chủ và menu (vẫn giữ làm mẫu tham chiếu cho AI).

**Sau khi khung sườn nâng cấp:** người dùng dán lại Prompt 1 (cập nhật nhóm Trang chủ, nhóm con màn hình, bước xác thực trong
tài liệu 2 chức năng) rồi Prompt 2 (đổi giao diện), dữ liệu đang có giữ nguyên.

## 9. Chưa rõ - cần hỏi tiếp ở bước sau
- Nhãn đơn vị cụ thể: "[Chung]" / "[Sales]" / "[Xưởng]" / "[SO]" / "[Đơn vị]" (đề xuất), xác nhận ở bước 1.

## 10. Ngoài phạm vi
- Đăng nhập, phân quyền thật, ẩn màn hình theo người dùng.
- Sửa phần khung dùng chung (sidebar, Trang chủ).
