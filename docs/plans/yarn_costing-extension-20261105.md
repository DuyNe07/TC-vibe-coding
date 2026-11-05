# yarn_costing - Mở rộng 2026-11-05: kiểm tra Siro / Compact bất thường (Prompt 5)

## Yêu cầu của người dùng
Trên Dashboard kiểm soát, khi so sánh các sợi cùng nhóm sợi: năng suất máy (NSM) công đoạn Con / Con - compact của sợi
Siro hoặc Compact thấp hơn sợi thường 5%, của sợi Siro Compact thấp hơn 10%; sợi Siro / Compact phải đắt hơn sợi thường.
Chỉ sửa phần kiểm tra trên Dashboard; tự điền NSM (BR-37, UC-20) và cảnh báo NSM khi lưu (BR-38) giữ nguyên.

## Câu hỏi đã trả lời
| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Áp vào đâu | Vòng 1: cả 3 chỗ; sau khi biết tự điền chép nguyên NSM và cảnh báo không xét Thô / Con / Ống / MVS → **chỉ Dashboard** |
| 2 | So trong phạm vi nào | Cùng nhóm sợi (`yarn_group`), cùng xưởng, cùng chi số; mỗi xưởng so riêng, cùng một quy tắc cho S1 và S4 |
| 3 | Nhận ra loại sợi | Chữ trong tên sợi |
| 4 | Công đoạn | Con (S) và Con - compact (S Compact) |
| 5 | Kiểm tra gì | Cả NSM Con (chuẩn = mốc × 95% / 90%) và giá (Siro / Compact đắt hơn thường, Siro Compact đắt hơn Siro / Compact) |
| 6 | Mốc khi không có sợi thường | Quy đổi từ sợi Siro / Compact cùng nhóm (NSM ÷ hệ số); nhiều giá trị → giá trị phổ biến (bằng nhau: nhỏ nhất) |
| 7 | Mức lệch NSM | > 1% so với NSM chuẩn |
| 8 | Phần đang có | Giữ nguyên BR-39, BR-54 (UC-30, UC-31); phần mới là khối riêng; xét cả mã cũ, không sửa NSM, không tính lại giá |

## Thêm / đổi
- Mới: BR-71 (loại sợi Siro / Compact + 2 kiểm tra), UC-46 (Kiểm tra Siro / Compact bất thường), khối mới ở Screen 7,
  AC-90..AC-94, thuật ngữ "Loại sợi Siro / Compact".
- Không đổi: UC-20, UC-21, UC-30, UC-31, BR-37, BR-38, BR-39, BR-54, mọi màn hình khác, mọi file nhập / xuất.

## Ảnh hưởng tới dữ liệu đã lưu
Không có trường mới, không đổi định dạng: loại sợi tính từ tên mỗi lần kiểm tra. Không migration, không tính lại giá, không
sửa NSM. Kiểm tra chỉ đọc (Người xem), xét mọi bản NSM gốc đã có giá hiện có.

## Truy vết (điền ở bước làm)
| Hạng mục | Code | Test |
|---|---|---|
| BR-71 loại sợi | `SiroCompactBusiness.kind_of` | `test_kind_from_name` |
| BR-71 kiểm tra NSM Con | `SiroCompactBusiness.nsm_anomalies`, `spin_nsm` | AC-90, AC-91, AC-93 |
| BR-71 kiểm tra giá | `SiroCompactBusiness.price_anomalies` | AC-92, AC-93 |
| UC-46 | `CheckSiroAnomaliesService`, `YarnCostingController.check_siro_anomalies` | `test_uc46_service_empty_message` |
| Screen 7 khối mới | `DashboardPage._siro_compact` | chạy thử trang (AppTest): 2 ô số liệu, 2 bảng, lọc Loại sợi |
| regression: existing tests | toàn bộ `backend/features/yarn_costing/tests/` | 232 passed (AC-94: BR-39 giữ nguyên) |
