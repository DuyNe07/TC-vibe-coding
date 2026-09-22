# Prompt mẫu: từ nghiệp vụ đến chức năng chạy trên UI (2 lượt)

| Bước | Bạn làm gì | Prompt | Kết quả |
|---|---|---|---|
| 0 | Mở phiên chat mới với AI trong thư mục dự án. Giải thích nghiệp vụ, dán nội dung, đính kèm file mẫu (Excel, Word, PDF, ảnh chụp...) | - | AI nắm được nghiệp vụ |
| 1 | Dán toàn bộ nội dung prompt 1 (sửa các chỗ `<...>` nếu cần) | [01-business-analysis.md](01-business-analysis.md) | AI lập kế hoạch, hỏi lại bạn, rồi viết `docs/business/<tên_chức_năng>.md` (nội dung tiếng Việt) |
| 2 | Đọc lại tài liệu nghiệp vụ, sửa nếu cần. Dán prompt 2 và điền tên chức năng | [02-implement-feature.md](02-implement-feature.md) | AI lập kế hoạch triển khai trong `docs/plans/`, chờ bạn duyệt, rồi viết backend + giao diện, chạy kiểm tra |
| 3 | Chạy `powershell -ExecutionPolicy Bypass -File .\run.ps1`, thử chức năng theo hướng dẫn AI đưa ra, phản hồi nếu cần sửa | - | Chức năng xuất hiện ở Trang chủ |

Lưu ý:
- Ở mỗi điểm **STOP**, AI sẽ dừng lại chờ bạn trả lời. Hãy đọc kỹ kế hoạch và các câu hỏi trước khi đồng ý.
- AI không tự bịa quy tắc nghiệp vụ: chỗ nào chưa rõ sẽ được hỏi lại, hoặc ghi vào mục "Open questions" của tài liệu.
- Muốn sửa chức năng sau này: sửa tài liệu `docs/business/<tên>.md` trước, rồi yêu cầu AI cập nhật code theo tài liệu.
