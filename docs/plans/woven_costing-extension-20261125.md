# Extension 2026-11-25 - woven_costing: 2 loại gia công (Gia công dệt, Gia công nhuộm)

## Thêm / thay đổi
- Hình thức bán (4.11 sale_form) thêm 2 giá trị: **Gia công dệt**, **Gia công nhuộm**.
- BR-89 Gia công dệt (khách giao sợi):
  - số lượng như Mộc;
  - sợi: tính số kg (= sợi khách cần giao), thành tiền 0, không cần giá sợi;
  - ngành Dệt tính đủ (Se, hồ, mắc, cone, dệt, kiểm, gia công ngoài, hệ số discount Dệt);
  - nhuộm 0, thanh lý B/C 0;
  - tổng = chi phí ngành Dệt.
- BR-90 Gia công nhuộm (khách giao mộc):
  - số lượng như Vải Nhuộm (không chia B/C mộc); hiện số mét mộc khách cần giao;
  - sợi, Dệt, tiền mua mộc = 0; không cần giá mộc;
  - nhuộm tính đủ (HCM / TCDN); thanh lý B/C 0;
  - tổng = chi phí nhuộm.
- BR-91: chọn gia công thì Loại đơn tự thành "Gia Công", sales sửa lại được.
- 4.6.2 bảng % B/C thêm 2 dòng: Gia công dệt 4% / 0%, Gia công nhuộm 5% / 4%.
- Giá bán của phiếu gia công = phí gia công; GP / OP / ngưỡng như phiếu thường.

## Ảnh hưởng tới phần đã có
- BR sửa: BR-13, BR-14, BR-16, BR-17, BR-18, BR-19, BR-22, BR-23, BR-25, BR-26, BR-27, BR-42, BR-88 (mỗi chỗ thêm
  trường hợp gia công, phần cũ giữ nguyên).
- UC-15 (BR-91), UC-16 (BR-89, BR-90).
- Màn hình 1 (giá trị mới trong cột Hình thức bán), Màn hình 2 (ô Hình thức bán 5 lựa chọn, ẩn / hiện thẻ, thẻ Sợi có
  ghi chú, Chuỗi nhu cầu có dòng "Sợi khách giao" / "Mộc khách giao", nhãn "Giá bán (phí gia công)"), Màn hình 5 (bảng
  % B/C 5 dòng).
- Thay giả định cũ "Loại đơn Gia Công vẫn tính sợi và dệt": cách tính nay theo Hình thức bán.

## Dữ liệu đã lưu
- Phiếu đã lưu: giữ nguyên hình thức bán và kết quả (BR-39); không đổi dữ liệu.
- Bộ tham số đã lưu (01/01, 23/11, 25/11/2026) chưa có 2 dòng gia công: khi đọc, Gia công dệt lấy dòng Mộc, Gia công
  nhuộm lấy dòng Vải Nhuộm. Không cần chuyển đổi dữ liệu; SO lưu bộ mới thì 2 dòng được lưu.
- Hình thức bán lưu dạng chữ: giá trị mới không cần chuyển đổi.

## Câu hỏi đã trả lời (2026-11-25, "đồng ý" = toàn bộ đề xuất)
1. Thêm 2 lựa chọn vào Hình thức bán.
2. Gia công dệt: bỏ sợi và nhuộm, giữ toàn bộ Dệt; hiện số kg sợi khách giao.
3. Gia công nhuộm: bỏ Dệt, sợi, tiền mộc; hiện số mét mộc khách giao.
4. B/C vẫn tính số lượng dư, không trừ thanh lý; tỷ lệ mặc định như Mộc / Vải Nhuộm, SO sửa được.
5. Giá bán = phí gia công, ngưỡng GP / OP chung.
6. Mỗi phiếu 1 mã; nhiều mã / OC trình 1 lần để đợt 3 (NGC).
7. Chọn gia công thì Loại đơn tự thành "Gia Công", sửa lại được.

## Giao diện
Đã chốt trong câu hỏi 1, 2, 3, 7 (ô chọn, ẩn / hiện thẻ, dòng chuỗi nhu cầu, ghi chú) -> bỏ vòng hỏi giao diện riêng.

## Traceability (mới / đổi)
| Spec item | Code element | Test | Status |
|---|---|---|---|
| 4.11 sale_form (+2), 4.6.2 (+2 dòng) | models/enums.py, models/parameter_tables.py | test_gia_cong_20261125 | ⬜ |
| BR-89, BR-90, BR sửa (13,14,16,17,18,19,22,23,25,26,27,42,88) | business/* (quantity, costing, weaving, dyeing, discount, submission) | test_gia_cong_20261125 | ⬜ |
| BR-91 | frontend components/costsheet_order.py | test_gia_cong_20261125 (render) | ⬜ |
| Chuỗi nhu cầu, thẻ ẩn / hiện, nhãn | builders/demand_chain_builder.py, pages/costsheet_page.py, components | test_gia_cong_20261125 | ⬜ |
| AC-70..AC-75 | | test_gia_cong_20261125 | ⬜ |
| regression: existing tests (AC-09 …) | | toàn bộ test cũ | ✅ |

(Tất cả dòng trên: ✅ 2026-11-25.)

## Kết quả (2026-11-25)
- check.py: ALL CHECKS PASSED (463 test); migrate status: up to date; doctor: APP IS HEALTHY.
- Trình duyệt, phiếu nháp CS-CONG39-2026-00003 (không lưu): Gia công dệt -> ẩn Nhuộm, Loại đơn tự "Gia Công", dòng "Sợi
  khách giao", không có Thanh lý B/C, nhãn "Giá bán (phí gia công)"; Gia công nhuộm -> ẩn Dệt / Sợi, dòng "Mộc khách
  giao"; đổi tay Loại đơn về "Sản Xuất" được giữ.
