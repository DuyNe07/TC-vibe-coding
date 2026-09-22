# Prompt mẫu: từ nghiệp vụ đến chức năng chạy trên UI (2 lượt)

Mỗi file prompt là **toàn bộ nội dung cần dán**: mở file → `Ctrl + A` → `Ctrl + C` → dán vào ô chat của AI.
Không cần sửa gì trong prompt.

| Bước | Bạn làm gì | Kết quả |
|---|---|---|
| 0 | Mở phiên chat mới với AI (Claude Code, Cursor...) trong thư mục dự án. Giải thích nghiệp vụ, dán nội dung, đính kèm file mẫu (Excel, Word, PDF, ảnh). Có thể đặt file vào `docs/business/_sources/` | AI nắm được nghiệp vụ |
| 1 | Dán toàn bộ [01-business-analysis.md](01-business-analysis.md). Trả lời câu hỏi của AI (chỉ hỏi về cách ứng dụng hoạt động, không hỏi về code). Đọc bản tóm tắt cuối và trả lời "đồng ý" để chốt | Tài liệu `docs/business/<tên_chức_năng>.md` (tiếng Việt), trạng thái `Ready for implementation` |
| 2 | Dán toàn bộ [02-implement-feature.md](02-implement-feature.md). AI đưa ra đề xuất giao diện (có hình phác) và hỏi **một lượt**: bảng như Excel chỉ xem hay sửa trực tiếp, nhập bằng form / bảng / file Excel, bộ lọc, số liệu tổng hợp, biểu đồ... Trả lời theo số hoặc gõ "ok" | AI tự lập kế hoạch (`docs/plans/`), chia việc cho AI phụ (backend và giao diện, chạy song song), chạy toàn bộ kiểm tra, rồi hướng dẫn cách dùng |
| 3 | Chạy `powershell -ExecutionPolicy Bypass -File .\run.ps1` và thử theo hướng dẫn | Chức năng xuất hiện ở Trang chủ |

**Nếu không dán được vì prompt quá dài** (một số công cụ giới hạn độ dài): gõ một dòng thay thế:
- Bước 1: `Đọc file docs/prompt/01-business-analysis.md và làm đúng từng bước trong đó.`
- Bước 2: `Đọc file docs/prompt/02-implement-feature.md và làm đúng từng bước trong đó.`

Lưu ý:
- Câu hỏi về **nghiệp vụ** (dữ liệu, quy tắc, cách tính, file) nằm ở **bước 1**: ở mỗi điểm dừng, AI chờ bạn trả lời.
- **Bước 2** chỉ hỏi một lượt về **giao diện**, sau đó chạy tự động đến khi có trên giao diện; chỉ sửa trong phạm vi
  chức năng đó, không ảnh hưởng chức năng khác, giữ nguyên dữ liệu đã có. Nếu bị gián đoạn (hết lượt, mất mạng...),
  dán lại prompt 2: AI làm tiếp từ bước dở, không hỏi lại.
- Trong Claude Code, AI có thể xin quyền chạy lệnh hoặc sửa file: hãy chọn cho phép (Yes / Allow) để AI làm tiếp.
- Muốn sửa nghiệp vụ sau này: làm lại bước 1 (AI cập nhật tài liệu cũ), rồi bước 2 (AI cập nhật code tại chỗ).
- Chỉ muốn đổi giao diện: gõ `Đổi giao diện chức năng <tên chức năng>` rồi dán prompt 2 ngay trong cùng tin nhắn.
