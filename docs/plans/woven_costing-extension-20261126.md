# Extension 2026-11-26 - woven_costing: bảng cone (sợi se chung / se riêng)

## Thêm / thay đổi
- Thay 2 cặp ô "Chi số cone 1 / SL cone 1", "Chi số cone 2 / SL cone 2" (4.14) bằng **bảng cone** (4.14a): mỗi dòng 1
  cone, không giới hạn 2 dòng.
- BR-100 (thay BR-87) gợi ý bảng cone từ các dòng Se Ngang:
  - sợi phụ = carbon (BR1, WHITE C, BLACK C, CARBON, CACBON, C.TRANG, C.DEN, C TRANG) và spandex; còn lại là sợi chính;
  - mỗi sợi chính (cùng chi số + độ săn) = 1 cone; sợi phụ se chung với 1 sợi chính -> cùng cone, kg cộng lại;
  - chọn sợi chính cho sợi phụ: cùng độ săn trước, rồi tỷ lệ khớp nhất (2 sợi dài bằng nhau); còn nhiều lựa chọn cùng độ
    săn thì cảnh báo "kiểm tra lại cone";
  - chi số cone se chung = chi số sợi chính + " + " + phần sợi phụ ("CB" / "SP m" / chi số), ví dụ "150D + 30D";
  - dòng gợi ý tự cập nhật; dòng sales sửa / thêm giữ nguyên; dòng sales xóa không tạo lại (giống BR-86).
- Bảng cone chỉ hiện khi phiếu có dòng Se Ngang (hoặc đã có dòng cone lưu từ trước).
- BR-22 phần Cone: tiền cone = Σ từng dòng cone (SL × khoản mục theo chi số của dòng).

## Ảnh hưởng tới phần đã có
- BR-87 bỏ từ 2026-11-26 (thay bằng BR-100). BR-22 sửa phần Cone. UC-16 thêm BR-100.
- Màn hình 2, thẻ Ngành Dệt: bỏ 4 ô cone, thêm bảng cone + dòng cảnh báo.
- AC-60 (BR-87) thay bằng AC-84..AC-88. AC-51 (hồi quy: cone "150D" cho cùng định mức) vẫn phải đạt.
- Bài kiểm tra làm dở `tests/test_cone_split_20261125.py` (chưa từng lưu, theo cách hiểu cũ "2 chi số -> cone 1 / cone
  2", sai với mã EF27920021) được viết lại theo AC-84..AC-88.

## Dữ liệu đã lưu
- Costsheet đã lưu: cone_count_1/2 + cone_qty_1/2 chuyển thành dòng của bảng cone (giữ nguyên số, coi như "sales đã
  sửa", trừ ô còn là gợi ý). Chuyển ngay khi đọc phiếu (`Costsheet.cone_rows`), các ô cũ vẫn đọc được nên không cần bản
  cập nhật dữ liệu; lần tính / lưu tiếp theo ghi bảng cone và để trống ô cũ. Không xóa dòng nào.
- Phiếu Chờ duyệt / Đã duyệt / Hủy: kết quả đã lưu không đổi (BR-39). Phiếu Nháp / Trả lại: khi mở và tính lại, dòng
  cone còn là gợi ý được tính theo BR-100; dòng đã sửa giữ nguyên.
- Lịch sử phiếu (4.19) giữ nguyên.

## Câu hỏi đã trả lời (2026-11-26)
1. Quy luật carbon se chung với sợi chính đi kèm, sợi chính khác nhau se riêng: đúng (kiểm trên 163 mã có ≥ 2 sợi se
   ngang; ví dụ EF27920021 se chung, EF15690111 se riêng).
2. Spandex: se chung với sợi chính như carbon.
3. Từ 3 sợi chính trở lên: thêm cone, không giới hạn 2 -> bảng cone.
4. Chi số cone se chung: nối "+" (ví dụ "150D + 30D").
5. Sales sửa / thêm / xóa dòng cone được; dòng đã sửa giữ nguyên.
6. Không chắc sợi phụ đi kèm sợi nào: chọn cùng độ săn, tỷ lệ khớp nhất, hiện nhắc kiểm tra lại.
7. Phiếu cũ: giữ số cone cũ; chỉ phiếu Nháp / Trả lại khi tính lại mới gợi ý theo quy luật mới.
8. Phiếu cũ có cone nhưng không có Se Ngang: vẫn hiện bảng với số cũ.
9. Bảng cone chỉ hiện khi vải có sợi Ngang đi se.
