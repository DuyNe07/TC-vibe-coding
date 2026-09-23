# TC-vibe-coding

Khung sườn để xây các công cụ nội bộ bằng **Streamlit** chỉ bằng cách ra lệnh cho AI ("vibe coding").
Bạn không cần biết lập trình: AI đọc bộ quy tắc trong `docs/` và luôn code theo đúng một cấu trúc.

## 1. Chạy ứng dụng

Yêu cầu: **Python 3.11** ([tải tại đây](https://www.python.org/downloads/), khi cài nhớ tick *Add python.exe to PATH*).

Mở **PowerShell** trong thư mục dự án và chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Script sẽ tự: kiểm tra/tạo môi trường `.venv` → cài thư viện (chỉ khi còn thiếu) → chạy app → mở trình duyệt
tại `http://localhost:8501/home`. Lần đầu mất vài phút để cài thư viện.
Dừng ứng dụng: bấm `Ctrl + C` trong cửa sổ PowerShell.

Tuỳ chọn thêm vào cuối lệnh: `-Port 8600` (đổi cổng), `-NoBrowser` (không mở trình duyệt), `-Reinstall` (cài lại thư viện).

## 2. Thêm một chức năng mới (ra lệnh cho AI, 3 lượt)

Làm theo hướng dẫn trong [docs/prompt/README.md](docs/prompt/README.md). AI **không được phép viết code** cho đến
lượt 3, nên cứ trao đổi nghiệp vụ thoải mái ở hai lượt đầu. Xem app làm được những gì:
[docs/capabilities.md](docs/capabilities.md).

0. Dán **Prompt 0.5** ([docs/prompt/00-discovery.md](docs/prompt/00-discovery.md)): AI giới thiệu app làm được gì rồi
   hỏi - đáp với bạn về công việc hiện tại và mong muốn, cuối cùng tóm tắt lại để bạn xác nhận là hiểu đúng.
1. Cho AI học nghiệp vụ (giải thích, dán nội dung, đính kèm file mẫu), rồi dán **Prompt 1**
   ([docs/prompt/01-business-analysis.md](docs/prompt/01-business-analysis.md)): AI hỏi lại những chỗ chưa rõ
   (chỉ về cách ứng dụng hoạt động), viết tài liệu nghiệp vụ `docs/business/<ten_chuc_nang>.md` bằng tiếng Việt
   và chờ bạn chốt.
2. Dán **Prompt 2**
   ([docs/prompt/02-implement-feature.md](docs/prompt/02-implement-feature.md)): AI hỏi **một lượt** về cách bạn muốn
   dùng giao diện (bảng như Excel chỉ xem hay sửa trực tiếp, bộ lọc, số liệu tổng hợp...; gõ "ok" để dùng đề xuất).
   Sau đó AI tự lập kế hoạch, chia việc cho các AI phụ (backend / giao diện), chạy kiểm tra mà không hỏi gì thêm, rồi
   hướng dẫn bạn cách dùng.
3. Chạy lại `run.ps1` → chức năng mới xuất hiện ở Trang chủ và menu bên trái.

Chức năng mẫu **"Nhập sản phẩm từ Excel (mẫu)"** cho thấy một chức năng hoàn chỉnh
(tài liệu: `docs/business/sample_product_import.md`).

## 3. Khi có lỗi

Cuối mỗi trang có khung **📜 Nhật ký chạy (log)**: mở ra, bấm biểu tượng copy (hoặc *Tải log*) và gửi
cho AI kèm mô tả lỗi. Toàn bộ log cũng nằm trong file `logs/app.log`.

## 4. Cấu trúc thư mục (tóm tắt)

```
backend/            Xử lý nghiệp vụ (Python thuần)
  core/             Khung chung: lớp cơ sở, cấu hình, log  (không sửa)
  shared/           Đọc/ghi Excel, Word, PDF dùng chung
  features/<tên>/   Mỗi chức năng: models, dto, business, builders, repositories, services, controllers
frontend/           Giao diện Streamlit
  core/             Khung giao diện: header, menu, panel, footer, khung log  (không sửa)
  home/             Trang chủ /home
  features/<tên>/   Các trang của từng chức năng
docs/               Quy tắc bắt buộc cho AI (rules/) + tài liệu nghiệp vụ (business/)
scripts/            new_feature.py (tạo chức năng), check.py (kiểm tra)
run.ps1             Chạy ứng dụng (PowerShell)
```

Tất cả chạy trong **một** ứng dụng Streamlit, không có server API riêng. Giao diện gọi nghiệp vụ qua một
"gateway" chung; mỗi chức năng chỉ lộ ra một tầng trên cùng (controller), bên dưới được đóng gói riêng.

Nếu cần hỗ trợ, hãy liên hệ qua: luongvudinhduy03@gmail.com