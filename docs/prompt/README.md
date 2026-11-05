# Các prompt: từ nghiệp vụ đến chức năng chạy trên server

Mỗi file prompt là **toàn bộ nội dung cần dán**: mở file → `Ctrl + A` → `Ctrl + C` → dán vào ô chat của AI (Claude Code,
Cursor...). Không cần sửa gì trong prompt. Nếu công cụ không cho dán dài, gõ một dòng:
`Đọc file docs/prompt/<tên file> và làm đúng từng bước trong đó.`

## Làm chức năng mới (3 bước)
| Bước | Prompt | Bạn làm gì | Kết quả |
|---|---|---|---|
| 0.5 | [00-discovery.md](00-discovery.md) | Kể công việc hiện tại và mong muốn, đính kèm file mẫu (Excel, Word, PDF). Trả lời "đúng rồi" ở bản tóm tắt | Ghi chép `docs/business/_sources/<chủ đề>-discovery.md` |
| 1 | [01-business-analysis.md](01-business-analysis.md) | Trả lời câu hỏi về cách ứng dụng hoạt động (không hỏi code). Trả lời "đồng ý" để chốt | Tài liệu nghiệp vụ `docs/business/<chức năng>.md`, trạng thái `Ready for implementation` |
| 2 | [02-implement-feature.md](02-implement-feature.md) | Trả lời **một lượt** về giao diện (hoặc gõ "ok") | AI tự làm backend + giao diện, tự kiểm tra, rồi hướng dẫn cách dùng |

## Khi đã có chức năng
| Khi nào | Prompt | Bạn làm gì | Kết quả |
|---|---|---|---|
| Có lỗi (màn hình báo lỗi, kết quả sai, app không chạy, không đăng nhập được) | [03-fix-error.md](03-fix-error.md) | Dán prompt kèm mô tả: bấm gì, màn hình hiện gì, hoặc ảnh chụp | AI tự tìm nguyên nhân thật (thư viện trên máy, file `.env`, cơ sở dữ liệu, hay lỗi trong chức năng), sửa phần được phép sửa, kiểm tra lại, và nói rõ ai cần làm gì nếu không phải lỗi của chức năng |
| Cập nhật bản mới nhất / gửi công việc lên server | [04-sync-to-server.md](04-sync-to-server.md) | Trả lời **một lượt**: các nhánh cần cập nhật (đề xuất: tất cả), mô tả ngắn, chạy trên server công ty hay chỉ trên máy mình. Lần đầu trên máy: AI mở trình duyệt để bạn đăng nhập GitHub (bấm **Authorize**), không cần mã hay mật khẩu | Với **từng** nhánh chức năng của bạn: AI lưu công việc, lấy bản chung mới nhất của nhóm (`dev`), đặt công việc lên trên, sửa cho hợp khung sườn mới, kiểm tra, đẩy lên và đưa link Pull Request. **Muốn chạy trên server công ty: bắt buộc bấm link tạo Pull Request**; chỉ chạy trên máy mình: không cần |
| Muốn thêm vào một chức năng đã xong | [05-extend-feature.md](05-extend-feature.md) | AI đọc chức năng cũ, kể lại nó đang làm gì, rồi hỏi bạn muốn thêm gì. Trả lời câu hỏi, "đồng ý" ở bản tóm tắt, một lượt về giao diện | Tài liệu được cập nhật, phần mới được làm ngay trong chức năng cũ; phần cũ và dữ liệu cũ giữ nguyên |
| Chỉ muốn đổi giao diện | [02-implement-feature.md](02-implement-feature.md) | Gõ `Đổi giao diện chức năng <tên>` rồi dán prompt 2 trong cùng tin nhắn | Chỉ giao diện thay đổi, nghiệp vụ giữ nguyên |

Cấp quyền cho người dùng không cần prompt: quản trị viên làm trên trang `/admin` của ứng dụng
(chọn ứng dụng, tick màn hình cho từng người / nhóm).

## Các nhánh
- `main`: bản ổn định để giới thiệu trên GitHub; chỉ người phụ trách khung sườn cập nhật (gộp từ `dev`).
- `dev`: nhánh chung của nhóm, công việc của mọi người được gộp vào đây qua Pull Request.
- **Mỗi chức năng một nhánh riêng, tạo từ `dev` mới nhất ngay trong repo này** - không fork repo trên GitHub, không
  clone lại, không chép thư mục. AI tự tạo nhánh `vibe/<tên-người-làm>-<chức-năng>-<ngàytháng>` ở bước 2; làm 10 ứng
  dụng thì có 10 nhánh, mỗi nhánh đều tạo từ `dev`. Phát triển thêm một ứng dụng (prompt 5) thì làm tiếp trên nhánh
  của ứng dụng đó.
- Prompt 4 cập nhật **tất cả** các nhánh đó theo `dev` mới nhất, rồi đưa một link Pull Request vào `dev` cho từng
  nhánh. **Muốn chạy trên server công ty: phải tạo Pull Request theo link**, người phụ trách duyệt rồi đưa lên server.
  Chỉ chạy trên máy mình thì không cần Pull Request.
- Người ngoài nhóm chỉ muốn làm riêng: tạo nhánh từ `main` và nói với AI ở prompt 4 "tôi làm riêng, không theo nhóm".

## Lần đầu cài trên máy
Lấy mã nguồn bản của nhóm: `git clone https://github.com/DuyNe07/TC-vibe-coding.git`, `cd TC-vibe-coding`,
`git checkout dev` (đã có thư mục: `git checkout dev` rồi `git pull`).
Trong PowerShell ở thư mục dự án: `Copy-Item .env.example .env`, điền các dòng `POSTGRES_*` (xin người phụ trách khung
sườn - mọi máy dùng chung một cơ sở dữ liệu), rồi `powershell -ExecutionPolicy Bypass -File .\run.ps1`.

## Lưu ý
- **AI bị chặn viết code cho đến bước 2** (hoặc bước sửa lỗi / gửi lên server / phát triển thêm). Trước đó AI chỉ trao
  đổi và viết tài liệu, nên không "làm tắt" khi chưa hiểu đúng nghiệp vụ.
- **AI tự sửa khi gặp lỗi** trong phạm vi chức năng của nó, đến khi `scripts/check.py` và `scripts/doctor.py` đều đạt;
  không được sửa test hay giấu lỗi ([docs/rules/10-self-repair.md](../rules/10-self-repair.md)).
- Ở mỗi điểm dừng, AI chờ bạn trả lời. Sau lượt hỏi về giao diện, AI tự làm đến khi xong.
- Bị gián đoạn (hết lượt, mất mạng): dán lại đúng prompt đó, AI làm tiếp từ chỗ dở.
- Muốn biết app làm được gì: [docs/capabilities.md](../capabilities.md), hoặc hỏi AI ở bước 0.5.
- Trong Claude Code, khi AI xin quyền chạy lệnh / sửa file: chọn cho phép để AI làm tiếp.
