# Business analysis plan - Tính giá vải dệt

| Ngày | 2026-11-20 |
|---|---|
| Nguồn chính | `docs/business/_sources/woven-costing-discovery.md` (đã xác nhận) |
| Trạng thái | Đã chốt - woven_costing.md Ready for implementation |

## 1. Feature split

### Quyết định
Tất cả các phần của bài toán (dữ liệu gốc, costsheet, giá hóa chất TCDN, NGC, xác nhận chi phí ngành) dùng chung một bộ
dữ liệu: mã vải, sợi, định mức, costsheet, OC. Các chức năng trong khung sườn thì độc lập, không đọc được dữ liệu của
nhau. Vì vậy ta làm **một chức năng duy nhất**, xây theo 4 đợt.

| Thông tin | Giá trị |
|---|---|
| feature_key | `woven_costing` |
| Tên hiển thị | Tính giá vải dệt |
| Nhóm trên Trang chủ | Kinh doanh Woven |
| Biểu tượng | 🧵 |
| Người phụ trách | Sales Woven (team FS) |
| Mục tiêu | Sales lập, lưu, duyệt costsheet vải dệt trên một ứng dụng dùng chung dữ liệu gốc do SO cập nhật, thay cho các file Excel rời rạc. |
| Người dùng | Sales FS1/FS2, trưởng team, trưởng đơn vị, phòng SO, PD (nhập mã gấp), quản trị viên |

### Phạm vi theo đợt
- **Tài liệu lần này (đợt 1):** dữ liệu gốc + costsheet sales HCM/TCDN + duyệt + danh sách tổng hợp + in nhãn.
- **Các đợt sau** dùng Prompt 05 (mở rộng chức năng) trên cùng `woven_costing`:
  - đợt 2: báo giá ngành Nhuộm TCDN;
  - đợt 3: NGC;
  - đợt 4: ngành xác nhận chi phí theo OC.
- Trong đợt 1, các ô giá hóa chất / báo giá riêng của TCDN vẫn do sales nhập tay như hiện nay. Đợt 2 sẽ nối tự động.

### Use case dự kiến (đợt 1)

**Phòng SO (dữ liệu gốc)**
- Tải 4 file Peace/WFX -> xem trước thay đổi -> lưu.
- Nhập nhanh / sửa mã vải gấp.
- Tra cứu mã vải.
- Cập nhật tỷ giá tháng.
- Tải file mẫu định mức -> tải lên định mức theo ngày hiệu lực (Dệt, Se, Hồ, Cone, Mắc-Kiểm, Nhuộm HCM, Nhuộm TCDN,
  công đoạn / tính năng đặc biệt HCM, HC CPB Tenter).
- Cập nhật tham số chung (S&A %, VAT %, tiêu hao, hệ số số lượng, % B/C, ngưỡng GP%/OP%).
- Quản lý khách hàng.
- Quản lý sales - team - vai trò duyệt.
- Cập nhật độ co mắc theo mã.

**Sales**
- Tạo costsheet (HCM hoặc TCDN).
- Lưu nháp.
- Tính lại.
- Sao chép.
- Gửi duyệt.
- Tạo phiên bản mới.
- Nhập OC / chốt đơn.
- Hủy.
- In nhãn (Word).
- Thêm khách hàng.

**Duyệt**
- Trưởng team / trưởng đơn vị duyệt hoặc trả lại.

**Tất cả**
- Danh sách tổng hợp (lọc).
- "Việc chờ tôi".

### Quy tắc chính dự kiến
- Toàn bộ công thức Sợi / Dệt / Nhuộm HCM / Nhuộm TCDN / Giá bán của 2 file Excel.
- Gợi ý Se / Hồ.
- Độ co lớn hơn 5% hoặc có lý do.
- Kiểm tra dạng OC.
- Luồng trạng thái.
- Phân quyền xem theo team.
- Phiên bản.
- Ngày hiệu lực của định mức.
- Gộp Peace / WFX.

### Dữ liệu dự kiến
- Mã vải; sợi của mã vải; tỷ giá; các bảng định mức (có ngày hiệu lực); tham số chung; khách hàng; sales-team.
- Costsheet (đầu phiếu, dòng sợi, dòng Se, dòng ngành Dệt, dòng Nhuộm, giá bán), phiên bản, lịch sử trạng thái.

### File dự kiến
- Vào:
  - 4 file Peace/WFX;
  - các file định mức (theo mẫu app tạo ra);
  - danh sách khách hàng (Data_clean, tải 1 lần).
- Ra:
  - file mẫu định mức;
  - nhãn thông số vải (Word);
  - danh sách tổng hợp (Excel).

### Màn hình dự kiến (đợt 1)
1. Danh sách costsheet (trang đầu)
2. Lập / xem costsheet
3. Việc chờ tôi / chờ duyệt
4. SO - Dữ liệu mã vải (tải Peace/WFX, nhập mã gấp, tra cứu)
5. SO - Định mức và tham số
6. SO - Tỷ giá
7. SO - Khách hàng và sales-team

## 2. Source inventory

| ID | Nội dung | Nguồn |
|---|---|---|
| S-01 | Thay 2 file tính giá HCM / TCDN; người dùng là sales Woven; dữ liệu gốc do SO tạo | Tin nhắn mở đầu |
| S-02 | 2 nhà máy nhuộm (HCM, TCDN), sales chọn trên cùng màn hình | Trả lời vòng 1 |
| S-03 | Hơn 200 đơn/tháng; lỗi tick Se/Hồ; mã mới thiếu thông số -> sai độ co | Trả lời vòng 1 |
| S-04 | Lưu mọi báo giá, cho sao chép; trưởng team duyệt | Trả lời vòng 1 |
| S-05 | Không cần xuất Excel costsheet; cần in nhãn như sheet PRINT | Trả lời vòng 1; sheet PRINT |
| S-06 | Danh sách costsheet tổng hợp kèm trạng thái | Trả lời vòng 1 và 2 |
| S-07 | Báo giá cũ giữ số cũ; định mức có ngày hiệu lực | Trả lời vòng 1 |
| S-08 | Sales nhập giá sợi (USD × tỷ giá hoặc VND) | Trả lời vòng 1; 4 file kết quả |
| S-09 | Bảng định mức có số mặc định như file; SO điều chỉnh | Trả lời vòng 1 |
| S-10 | Tick Se: sợi có độ săn | Trả lời vòng 2 |
| S-11 | Hồ: tên vải có HO, hoặc sợi dọc spun chi số từ 50, spun không se, filament SIM/NIM; HIM không hồ; áp dụng mọi sợi dọc; app gợi ý, sales xác nhận | Trả lời vòng 2-4 |
| S-12 | Độ co lớn hơn 5%; ngoại lệ mộc khách ổn định / pre-setting (công đoạn sau pre-setting co = 0) | Trả lời vòng 2-3 |
| S-13 | Độ co = 0: sales ghi lý do, tô màu cho trưởng team; đánh dấu cho ngành | Trả lời vòng 4 |
| S-14 | Trạng thái Nháp / Chờ duyệt / Đã duyệt / Trả lại / Đã chốt đơn (có OC) / Hủy | Trả lời vòng 2 |
| S-15 | Sửa báo giá đã duyệt -> phiên bản mới, duyệt lại nếu giá đổi | Trả lời vòng 2 |
| S-16 | Cảnh báo GP%/OP% thấp, ngưỡng chưa chốt | Trả lời vòng 2 |
| S-17 | Trưởng team FS1, FS2 duyệt team mình; trưởng đơn vị duyệt cả 2 team | Trả lời vòng 4 |
| S-18 | OC 2 cấp: Main OC (trước dấu chấm) và Summary OC (có dấu chấm); tính giá theo 1 trong 2 | Trả lời vòng 4 |
| S-19 | Sales thêm OC sau khi chốt đơn; báo giá project cập nhật OC và giá sợi khi có đơn thật | Trả lời vòng 2 |
| S-20 | Số PO của khách không cần | Trả lời vòng 3 |
| S-21 | Dữ liệu gốc: 4 file Peace / WFX, ưu tiên Peace, mã chỉ có ở WFX vẫn lấy | Trả lời vòng 4-5; thư mục Master vai |
| S-22 | Làm sạch TCFNO: bỏ "G" đầu, bỏ dấu chấm, 10 ký tự; đuôi là tên hàng SY | UPDATE TCFNO AND EXCHANGE RATE.xlsx |
| S-23 | Cập nhật dữ liệu cách C: tải file + form nhập mã gấp | Trả lời vòng 3 |
| S-24 | Tỷ giá theo tháng từ email kế toán (SO nhập) | Trả lời vòng 1; sheet Tỷ giá |
| S-25 | Khách hàng: danh sách FS1/FS2 từ Data_clean; sales được thêm | Trả lời vòng 2-3 |
| S-26 | Độ co mắc theo mã, mặc định 10%, dùng ở Mắc Hồ / Gia công Hồ / Mắc Phân Băng | File xử lý sheet TCFNOStand; CostSheet J70:J72 |
| S-27 | Quy trình sản xuất TCDN chỉ để tham khảo | Trả lời vòng 5 |
| S-28 | Công thức sợi: tiêu hao dọc / ngang, sợi cặn, giá thanh lý | CostSheet rows 21-41 |
| S-29 | Lượng mộc, % B/C, hệ số số lượng | CostSheet E43, H43, E47, E48, E85 |
| S-30 | Ngành Dệt: Se, Hồ, Mắc phân băng, Cone, Dệt, Kiểm, gia công, bảng khoản mục | CostSheet rows 50-80; sheet DM |
| S-31 | Nhuộm HCM: nguyên liệu × cấp màu, Blended, khổ, ×2, công đoạn / tính năng đặc biệt, chi phí phát sinh | CostSheet rows 84-110; sheet TỔNG HỢP |
| S-32 | Nhuộm TCDN: quy trình tiêu chuẩn, hệ số số lượng, ngoài QT chuẩn, WR, tính năng đặc biệt, chi phí phát sinh, gia công ngoài | CostSheet TCDN rows 84-114 |
| S-33 | Giá bán: giá vốn, GP, GP%, S&A 10,09%, commission, vận chuyển và bảo hiểm, OP, OP%, lãi vay, VAT 8%, USD | CostSheet rows 116-127 |
| S-34 | Chi phí phát sinh vào giá vốn (chi phí test vải) | CostSheet J116:K127 |
| S-35 | Chi phí phát sinh do ngành báo giá; sales sửa phải ghi lý do | Trả lời vòng 3 |
| S-36 | Ngoại lệ gõ cứng mã ES17020213 / ES17020413 | CostSheet ngành Dệt |
| S-37 | 4 costsheet thật làm bài kiểm tra (GP / OP) | Thư mục File kết quả |
| S-38 | Các bước làm theo 4 đợt, 1 ứng dụng | Trả lời Bước 5 |
| S-39 | Không có email, chạy theo giờ, kết nối SharePoint / Peace / WFX; vải đan ngoài phạm vi | Bảng khả thi |
| S-40 | Thông tin đơn hàng: loại giá (FOB...), ngày shipment, số ký, số mét | CostSheet BA8:BJ10 |
| S-41 | Hướng dẫn: KH do sales thêm; gia công ngoài thì SO xóa định mức tránh tính trùng; khổ đơn / đôi / ba | 2 file PDF hướng dẫn |

## 3. Questions
Xem tin nhắn gửi người dùng ngày 2026-11-20 (Q1-Q14). Câu trả lời sẽ ghi vào mục 4.

## 4. Answers

### Vòng 1
- **Q1 - Quyền xem:**
  - Sales xem phiếu của mình và của cả team, chỉ sửa phiếu của mình.
  - Trưởng team xem cả team.
  - Trưởng đơn vị và SO xem tất cả; SO chỉ xem.
- **Q2 - Cảnh báo:** chỉ cảnh báo, không chặn. Ngưỡng GP 15%; ngưỡng OP "tương ứng sau khi trừ S&A" (cần làm rõ con
  số, xem vòng 2).
- **Q3 - Duyệt lại:** phiên bản mới mà giá bán, giá vốn hoặc GP% khác phiên bản đã duyệt thì phải duyệt lại. Chỉ đổi
  OC / ghi chú / ngày giao thì không.
- **Q4 - Project nhiều OC:** mỗi costsheet 1 OC. Project ra nhiều OC thì sao chép cho từng OC, cập nhật giá sợi; được
  chỉnh các mục khác (ví dụ cấp màu).
- **Q5 - Sao chép:** lấy tỷ giá và định mức mới nhất. Giá sợi phải nhập lại nếu 2 lần tính giá cách nhau từ 5 ngày làm
  việc trở lên.
- **Q6 - Ngày áp dụng định mức:** người dùng hỏi lại "định mức là gì" (giải thích ở vòng 2).
- **Q7 - Con số cố định:** làm bảng tham số có ngày hiệu lực; hiện giá trị mặc định trong costsheet, sales sửa được;
  lưu theo từng costsheet.
- **Q8 - Ngoại lệ mã hàng:** giữ, và làm bảng "hệ số theo mã hàng" để SO thêm / bỏ. Ngoại lệ hiện có (cả HCM và
  TCDN) cho ES17020213, ES17020413:
  - hóa chất hồ × 1,5;
  - nhân công dệt × 1,25;
  - vật tư dệt × 1,12 + 231 đ.
- **Q9 - Nhập mã gấp:** SO và PD đều nhập được. File Peace/WFX tải sau có mã đó thì số của Peace/WFX đè lên.
- **Q10 - Trả lại / Hủy:**
  - trả lại bắt ghi lý do;
  - hủy được ở mọi trạng thái trừ "Đã chốt đơn", bắt ghi lý do;
  - phiếu hủy xem được, không sửa.
- **Q11 - Thí nghiệm:** cần duyệt như sản xuất.
- **Q12 - Khách hàng:** sales thêm dùng được ngay. Trước khi tạo, app hiện các tên tương tự để sales xác nhận. SO sửa
  được tên (sai chính tả, thừa ký tự).
- **Q13 - Danh sách tổng hợp:** thêm cột Loại giá (FOB / CIF / ...); nếu CIF thì có chi phí F&I. Dữ liệu gốc có 6 loại
  giá: FOB, CIF, EXW, CPT, CIP, FCA.
- **Q14 - Nhãn:** giữ như sheet PRINT; theo đề xuất.

### Vòng 2
- Định mức thay đổi theo năm; áp cho costsheet có ngày tính giá từ ngày hiệu lực của định mức mới. Chưa có tỷ giá
  tháng của ngày tính giá: không cho tính, báo SO.
- Ngưỡng OP = 6,4% (15% trừ S&A tính trên giá bán).
- Ngày làm việc thứ 2 - thứ 6; kiểm tra giá sợi khi gửi duyệt (theo đề xuất, trừ ngày lễ SO nhập).
- Tham số sales sửa: tô màu và hiện mặc định, không bắt lý do.
- F&I: CIF, CIP bắt buộc F&I; CPT bắt buộc phí vận chuyển; FOB, EXW, FCA ẩn ô F&I. Sales nhập tay đ/m.
- Commission, lãi vay: sales nhập tay; lãi vay **trừ vào OP**.

## 5. Bảng đối chiếu nguồn
| S-xx | Nội dung | Covered by |
|---|---|---|
| S-01 | Thay 2 file tính giá | Mục 1, UC-15..UC-26 |
| S-02 | 2 nhà máy nhuộm, chọn trên cùng màn hình | 4.11 dye_plant, BR-25, BR-26, Screen 2 khối E |
| S-03 | Lỗi tick Se/Hồ, mã mới thiếu thông số | BR-06..BR-09, UC-03, BR-10 |
| S-04 | Lưu, sao chép, duyệt | UC-17, UC-19, UC-21 |
| S-05 | In nhãn, không xuất Excel costsheet | UC-26, F-07, BR-75 |
| S-06 | Danh sách tổng hợp | UC-27, UC-28, Screen 1 |
| S-07 | Giữ số cũ, định mức có ngày hiệu lực | BR-39, BR-62, 4.5 |
| S-08 | Giá sợi USD/VND | 4.12, BR-45 |
| S-09 | Định mức mặc định, SO điều chỉnh | UC-06, UC-07, 4.5 |
| S-10 | Gợi ý Se | BR-06 |
| S-11 | Gợi ý Hồ | BR-07, BR-08, BR-09 |
| S-12 | Độ co > 5%, ngoại lệ, pre-setting | BR-13, BR-14, BR-15 |
| S-13 | Độ co = 0: lý do, tô màu | BR-14, Screen 1-2 |
| S-14 | Trạng thái | 4.11 status, BR-30 |
| S-15 | Phiên bản, duyệt lại khi giá đổi | UC-23, BR-35, BR-37 |
| S-16 | Cảnh báo GP / OP | BR-28, 4.6 |
| S-17 | Trưởng team, trưởng đơn vị duyệt | BR-53, 4.10 |
| S-18 | OC 2 cấp | BR-40, 3. Glossary |
| S-19 | OC sau chốt đơn, project nhiều OC -> sao chép | UC-24, UC-19 |
| S-20 | Không cần PO khách | 4.11 (không có trường) |
| S-21 | Peace / WFX, ưu tiên Peace | UC-01, UC-02, BR-01 |
| S-22 | Làm sạch TCFNO, tên SY | BR-02, 4.1 sy_item |
| S-23 | Tải file + nhập mã gấp | UC-02, UC-03 |
| S-24 | Tỷ giá tháng | UC-05, BR-60, BR-61 |
| S-25 | Khách hàng FS1/FS2, sales thêm | UC-12, UC-18, BR-50 |
| S-26 | Độ co mắc | 4.1 warping_loss_rate, BR-22 |
| S-27 | Quy trình sản xuất TCDN tham khảo | Mục 10 (đợt 4) |
| S-28 | Công thức sợi | BR-11, BR-12, BR-19 |
| S-29 | Lượng mộc, B/C, hệ số số lượng | BR-16, BR-18, BR-23 |
| S-30 | Ngành Dệt | BR-20, BR-21, BR-22 |
| S-31 | Nhuộm HCM | BR-26, 4.15 |
| S-32 | Nhuộm TCDN | BR-25, 4.16 |
| S-33 | Giá bán và lợi nhuận | BR-27, BR-28 |
| S-34 | Chi phí vào giá vốn | 4.17 cogs_extra_lines, BR-27 |
| S-35 | Chi phí phát sinh, sửa ghi lý do | 4.15/4.16 extra_cost_*, BR-25, BR-26 |
| S-36 | Ngoại lệ mã hàng -> bảng hệ số | 4.7, UC-10, BR-24 |
| S-37 | 4 file kiểm tra | AC-09 |
| S-38 | 1 ứng dụng, 4 đợt | Mục 1, ghi chú đầu tài liệu |
| S-39 | Không email / theo giờ / kết nối | UC-30 thay email; UC-02 tải file |
| S-40 | Thông tin đơn hàng, loại giá | 4.11, 4.17, BR-29 |
| S-41 | Khổ đơn/đôi/ba, gia công ngoài | 4.15 width_type, BR-26, 4.16 outsourcing_lines |
