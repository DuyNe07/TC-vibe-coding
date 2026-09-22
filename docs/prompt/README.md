# Prompt mẫu: từ nghiệp vụ đến chức năng chạy trên UI (2 lượt)

| Bước | Bạn làm gì | Prompt | Kết quả |
|---|---|---|---|
| 0 | Mở phiên chat mới với AI trong thư mục dự án. Giải thích nghiệp vụ, dán nội dung, đính kèm file mẫu (Excel, Word, PDF, ảnh chụp...) | - | AI nắm được nghiệp vụ |
| 1 | Dán toàn bộ nội dung prompt 1 (sửa các chỗ `<...>` nếu cần). Trả lời các câu hỏi của AI (chỉ hỏi về cách ứng dụng hoạt động, không hỏi về code) và xác nhận bản tóm tắt cuối | [01-business-analysis.md](01-business-analysis.md) | Tài liệu `docs/business/<tên_chức_năng>.md` (tiếng Việt) đã được chốt: `Ready for implementation` |
| 2 | Dán prompt 2 (điền tên chức năng hoặc để nguyên). Không cần làm gì thêm: AI không hỏi gì cả | [02-implement-feature.md](02-implement-feature.md) | AI tự lập kế hoạch trong `docs/plans/`, viết backend + giao diện, chạy kiểm tra, rồi hướng dẫn bạn cách dùng |
| 3 | Chạy `powershell -ExecutionPolicy Bypass -File .\run.ps1`, thử chức năng theo hướng dẫn AI đưa ra, phản hồi nếu cần sửa | - | Chức năng xuất hiện ở Trang chủ |

Lưu ý:
- Mọi câu hỏi và quyết định đều nằm ở **Prompt 1**: ở mỗi điểm STOP, AI dừng lại chờ bạn trả lời. Hãy đọc kỹ bản tóm tắt cuối trước khi chốt.
- **Prompt 2** chạy tự động đến khi có trên giao diện; nó chỉ sửa trong phạm vi chức năng đó, không ảnh hưởng các chức năng khác và giữ nguyên dữ liệu đã có.
- AI không tự bịa quy tắc nghiệp vụ: chỗ nào chưa rõ sẽ được hỏi lại, hoặc ghi vào mục "Open questions" của tài liệu.
- Muốn sửa chức năng sau này: sửa tài liệu `docs/business/<tên>.md` trước, rồi yêu cầu AI cập nhật code theo tài liệu.
