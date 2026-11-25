# Ghi chép tìm hiểu nghiệp vụ: Tính giá vải dệt (Woven costing)
| Ngày | 2026-11-20 |
|---|---|
| Người trao đổi | Sales Woven (team FS) - người phụ trách file tính giá |
| Trạng thái | Đã xác nhận với người dùng |

## 1. Công việc hiện tại
- Sales Woven (team FS1, FS2) tính giá từng đơn bằng 2 file Excel có macro:
  "Tinh Gia Det - HCM (Official) 2026 07 01.xlsm" (nhuộm tại HCM) và "Tinh Gia Det - TCDN (Official) 2026 07 01.xlsm"
  (nhuộm tại TCDN). Sales tự chọn nhà máy nhuộm. Mỗi đơn là 1 file riêng, lưu rời rạc.
- Hơn 200 đơn/tháng. Lỗi hay gặp:
  - tick sai sợi se / sợi hồ;
  - mã vải mới hoặc vải thí nghiệm chưa có thông số, nhập sai mật độ nên sai độ co.
- Dữ liệu gốc do phòng SO cập nhật:
  - SO tải 4 file thô từ hệ thống Peace và WFX về.
  - Ghép bằng file "UPDATE TCFNO AND EXCHANGE RATE.xlsx" rồi để trên SharePoint.
  - File tính giá đọc lại từ SharePoint.
  - Tỷ giá lấy từ email kế toán hằng tháng.
  - Định mức được gõ sẵn trong file tính giá.
- Sales gia công nhuộm (NGC) dùng file riêng "Forrmat NGC Nhuộm TCDN.xlsm": 1 phiếu nhiều mã vải, mỗi dòng 1 OC.
- Ngành Nhuộm TCDN làm 2 loại báo giá:
  - "BAO GIA TUNG MAT HANG" (~150 sheet, mỗi sheet 1 mặt hàng hoặc 1 OC có quy trình không chuẩn);
  - "[BÁO GIÁ TCDN] - BÁO GIÁ HÓA CHẤT" (giá hóa chất Coating / Santa / Bonding / tính năng đặc biệt).
  - Sales nhận giá qua email.
- Hằng tháng các ngành (Dệt HCM, Nhuộm HCM, Nhuộm TCDN) lập báo cáo doanh thu ngành theo OC, dựa trên costsheet của
  sales. Costsheet hay thiếu số OC nên khó đối chiếu.
- Báo giá chỉ được duyệt miệng hoặc qua email, không có danh sách tổng hợp, không có lịch sử phiên bản.

## 2. Mong muốn (kết quả cuối cùng)
Một ứng dụng duy nhất "Tính giá vải dệt", thay toàn bộ các file trên:
1. Sales lập costsheet HCM / TCDN ngay trên app, tính đúng như Excel. App gợi ý tick Se / Hồ kèm lý do và cảnh báo độ co.
2. Lưu mọi costsheet. Cho sao chép, tạo phiên bản mới.
   - Trạng thái: Nháp -> Chờ duyệt -> Đã duyệt / Trả lại -> Đã chốt đơn (có OC) / Hủy.
   - Báo giá đã duyệt mà sửa thì tạo phiên bản mới; nếu giá thay đổi thì phải duyệt lại.
   - Cảnh báo khi GP% / OP% thấp hơn ngưỡng do SO đặt.
3. Danh sách tổng hợp (overall) mọi costsheet kèm trạng thái và thông tin chính.
4. In nhãn thông số vải như sheet PRINT. Không cần xuất costsheet ra Excel.
5. Quản lý số OC 2 cấp; danh sách "OC chưa có costsheet" để sales gắn vào.
6. Ngành Nhuộm TCDN báo giá trên app:
   - sales gửi "Yêu cầu báo giá", ngành trả giá ngay trên yêu cầu, trưởng ngành duyệt;
   - giá đã duyệt tự vào costsheet.
7. Tính giá gia công nhuộm (NGC) trên app.
8. Ngành xác nhận chi phí theo OC hằng tháng:
   - ngành tick dòng sai kèm phản hồi để sales kiểm tra lại;
   - xác nhận xong thì khóa tháng;
   - tải Excel theo mẫu báo cáo của từng ngành.
9. SO cập nhật dữ liệu gốc bằng cách tải file lên (không cần file xử lý trung gian), cộng thêm form nhập nhanh mã gấp.

## 3. Dữ liệu vào (file mẫu đã xem: tên file, sheet, các cột)
Tất cả nằm trong thư mục `D:\Vibe Coding\Woven-fabric\Format`.

**Dữ liệu gốc vải (thư mục "Master vai")**

Peace là nguồn ưu tiên. WFX là hệ thống mới, nhưng R&D vẫn chỉnh thông số bên Peace.
- **Raw data - Peace/Weaving control.xlsx** (~2.743 mã vải):
  - TCFNO_INST, TCFNO_NO, TCFNO_SEQ, TCFNO_YEAR, TCFNO, Code, Fabric, Structure, Fabric Kind, Fabric type, Open/Tube,
    TCFNO Status, Date create, In-Charge;
  - nhóm "Before" (mộc): Width, Cut W., Weight, G/Mt, Density Warp, Density Weft, Wale, Gause, Loop, Needle, SHR-Warp,
    SHR-Weft, Course;
  - nhóm "After" (thành phẩm): các cột giống nhóm Before;
  - đặc điểm file: 2 dòng tiêu đề + 1 dòng tổng ở đầu; ngày ghi dạng yyyy/mm/dd.
- **Raw data - Peace/TCFNO STANDARD.xlsx** (~9.760 dòng sợi):
  - TCFNO, YARN (WARP/WEFT), TCFNO-YARN, CONDITIONS, SEARCH, FCODE, CSP, Code, FNAME (tên sợi đầy đủ của vải), YCODE,
    YNAME, Direction, Rate (tỷ lệ), Direction (Soi doc/Soi ngang), YSEL_TCFNO_YARN, Loai soi (Soi don/Soi se), YCODE,
    YNAME (sợi gốc), RATE.
- **Raw data - WFX/Weaving_Control_Report.xlsx** (~384 mã): cột như Peace (không có 4 cột TCFNO_*), thêm Use, Remark,
  RAW_MATERIAL. Ngày ghi dạng dd/mm/yyyy.
- **Raw data - WFX/TCFNO_Standard_Report.xlsx** (~1.173 dòng sợi): cột như Peace, thêm TPM. Mã có thể bắt đầu bằng
  chữ "G" (ví dụ GEF29900023), hướng sợi viết "Warp/Weft".

**File xử lý hiện tại: "File xử lý/UPDATE TCFNO AND EXCHANGE RATE.xlsx"**
- Cách làm: ghép Peace + WFX, rồi các sheet TCFNOStand / TCFNO-Yarn lấy dữ liệu theo số thứ tự dòng.
- Quy tắc làm sạch mã TCFNO: bỏ chữ "G" ở đầu, bỏ dấu chấm, lấy 10 ký tự đầu. Phần đuôi sau 10 ký tự là **tên hàng SY**
  (ví dụ EF29500023**SN04**, EF30650023**RV04A**; 584 mã có đuôi).
- Điểm yếu phát hiện được:
  - 2 mã bị rơi khỏi sheet thông số và 6 mã bị rơi khỏi sheet sợi;
  - 291 mã có ở cả Peace và WFX, Excel lấy dòng gặp trước;
  - 89 mã chỉ có ở WFX (vẫn lấy).
- **TCFNOStand** (~3.118 mã):
  - TCFNO, **ĐỘ CO MẮC** (gõ tay, 3.098 mã để 10%, khoảng 20 mã có số riêng), FABRIC, Created Date;
  - thông số mộc: Width, Width-Cuteble, g/m2, g/m, Warp density, Weft density, Shrinkage warp/weft…;
  - thông số thành phẩm: Width, Weight, GMT, Density warp/weft, Shrinkage…;
  - TCFNO RAW.
- **TCFNO-Yarn** (~10.900 dòng): TCFNO, YARN, TCFNO-YARN, CONDITIONS (số thứ tự sợi), SEARCH (khóa "TCFNO-WARP-n"),
  FNAME, YCODE, YNAME, Rate, Hướng sợi, Loai soi, YCODE_RAW, YNAME_RAW, RATE, T/M (độ săn).
- Các sheet khác:
  - Tỷ giá (Month, Year, Tỷ giá);
  - QT sản xuất (Order, TCFNO, Item, Cấp màu, Color, PROCESS, Finish, Ngày cập nhật), đọc từ file "QT sản xuất.xlsx" chưa
    xem được;
  - Data / DATA HCM (danh sách chọn: loại đơn hàng, khách hàng, sales, hình thức bán, thị trường, hệ sợi, chi số, độ săn,
    nguyên liệu hồ, loại giá, nguyên liệu nhuộm, cấp màu, công đoạn / tính năng đặc biệt, loại kiểm, mắc phân băng);
  - Dữ liệu (hệ sợi, chi số, chi số chuyển đổi, độ săn);
  - Định mức Dệt (theo mật độ ngang: Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, CPQL, Tổng).

**File tính giá sales: "Tinh Gia Det - HCM / TCDN (Official) 2026 07 01.xlsm", sheet CostSheet**
- Thông tin đơn:
  - Khách hàng, Thị trường (Xuất khẩu/Nội địa), Loại đơn hàng (Thí nghiệm/Sản xuất), OC (ô "PO"), Style;
  - Hình thức bán (Mộc / Vải Thành Phẩm / Vải Nhuộm = mộc mua ngoài, có giá mộc);
  - Ngày giao, Sales, Ngày tính giá (-> tỷ giá theo tháng), TCFNO (10 ký tự), Số mét.
- Thông số vải lấy theo TCFNO: khổ, mật độ dọc / ngang, g/m, g/m2 (mộc và thành phẩm).
- Sợi:
  - tối đa 9 sợi dọc + 9 sợi ngang; tỷ lệ lấy theo TCFNO;
  - sales nhập giá sợi (USD × tỷ giá hoặc VND) và tỷ lệ sợi cặn;
  - tick Se / Hồ.
- Ngành Dệt:
  - Se: hệ sợi, chi số, độ săn, số lượng;
  - gia công Se; Mắc Hồ (nguyên liệu hồ); gia công Hồ; Mắc phân băng (Có/Không); Cone; Dệt (theo mật độ ngang); Kiểm;
  - gia công dệt, chi phí khác;
  - bảng chi tiết theo khoản mục: Điện, Nhân công, Khấu hao, Vật tư, Nhiên liệu, Hóa chất, CPQL.
- Ngành Nhuộm HCM:
  - nguyên liệu nhuộm (Cotton thường, TC/CVC/TR thường, PE thường, Sọc màu, Melange, Blended theo tỷ trọng);
  - cấp màu (Trắng / Nhạt / Trung bình / Đậm / Đặc biệt); khổ đơn / đôi / ba; tiêu hao nhuộm (sales nhập);
  - công đoạn đặc biệt, tính năng đặc biệt, chi phí đặc biệt, chi phí phát sinh, gia công.
- Ngành Nhuộm TCDN:
  - nguyên liệu nhuộm + cấp màu -> mã quy trình "Nhuộm tiêu chuẩn-<NL>-<cấp màu>";
  - công đoạn ngoài quy trình chuẩn kèm giá hóa chất đ/m (ví dụ Soaping 362);
  - WR, tính năng đặc biệt (6 dòng), chi phí phát sinh (theo khoản mục), gia công ngoài.
- Giá bán và lợi nhuận:
  - giá bán (USD × tỷ giá hoặc VND), chi phí phát sinh vào giá vốn (ví dụ chi phí test vải);
  - giá vốn, Gross Profit, GP%, S&A, Commission, chi phí vận chuyển và bảo hiểm, Operation Profit, OP%;
  - lãi vay đơn hàng trả chậm, giá bao gồm VAT, quy đổi USD.
- Các sheet khác:
  - PRINT (nhãn: TCFNO, tên vải, sợi dọc / ngang, khổ cm / inch, trọng lượng g/m2 g/m, mật độ, ghi chú);
  - bảng định mức ẩn (DM Se, DM Ho, DM Cone, DM Mac/Kiem, Định mức Dệt);
  - TỔNG HỢP (định mức nhuộm HCM đ/kg); Tiêu chuẩn và HC CPB Tenter (TCDN).

**5 file kết quả thật (thư mục "File kết quả")**, dùng làm bài kiểm tra. Không có ô công thức nào bị gõ đè.

| File | Kết quả |
|---|---|
| IMA-HCM-COSTING EM3579.00.26 (Ichimura, HCM, thí nghiệm, Mộc, 31 m) | GP 19,2%, OP 11,0% |
| Tinh Gia Det HCM - LONG GIANG - TM01510696 - 5.000 m | GP 15,2%, OP 6,6% |
| IMA-TCĐN-COSTING EF3532.00.26 (Ichimura, TCDN, 10.000 m) | GP 20,0%, OP 11,9% |
| Tinh Gia Det TCDN - TAN TIEN THANH - EM04150201 - 8.278 m | GP 23,0%, OP 15,3% |
| S-ONE DVDP-SAFM001-PA (NGC, 2 OC 8643 / 8644) | GP 38,5% |

**File NGC "Forrmat NGC Nhuộm TCDN.xlsm"**
- Sheet Input:
  - đầu phiếu: số hợp đồng, khách hàng, đơn vị gia công, tỷ giá, hình thức gia công;
  - mỗi dòng: % thành phẩm B/C, mã vải, tên vải / style, OC, ODNO (số đơn khách), g/m, g/m2, độ co, nguyên liệu nhuộm,
    cấp màu, phẩm nhuộm đặc biệt, giá hóa chất thuốc nhuộm, quy trình chuẩn, loại WR, số lượng, đơn giá nhận gia công;
  - 27 cột tick công đoạn (Chuẩn Bị, CPB, Singeing, …, Santa, Bonding, Coating, Kiểm Hàng-Đóng Gói), 27 cột "số lần xử
    lý thêm", 2 tính năng đặc biệt (tên + đơn giá), cột "báo giá riêng từng mặt hàng";
  - ô Coating chứa luôn giá hóa chất (ví dụ 1.861 đ/m).
- Sheet Output: theo dòng có tổng định mức, thành tiền chi phí, thành tiền giá gia công, GP, %GP và chi phí theo khoản
  mục.
- Các sheet khác: Operation Rate, Tiêu chuẩn, TNDB, WR, HC CPB Tenter.

**Báo giá ngành Nhuộm TCDN**
- "BAO GIA TUNG MAT HANG - template.xlsx": mỗi sheet 1 mặt hàng. Theo từng công đoạn:
  - thời gian sản xuất × định mức/phút (Nhân công, Khấu hao, Điện, Nhiên liệu, Vật tư, CPQL) ÷ sản lượng ÷ (1 − tiêu
    hao) ÷ (1 − độ co);
  - cộng toa hóa chất (lượng × đơn giá lấy từ sheet Giá HC);
  - ra VND/m và USD/m;
  - sheet Dinh muc, Giá HC, Tên công đoạn tính giá.
- "[BÁO GIÁ TCDN] - BÁO GIÁ HÓA CHẤT.xlsx":
  - **Coating** (394 dòng): Mã SO (CT-xxx), khách hàng, tên hàng TC (gần như trống), **tên hàng SY**, gia công / tính
    năng, quy trình, máy, tốc độ, toa hóa chất g/yard, ghi chú, ngày cập nhật, USD/m, đơn giá tổng và theo lần (VND/m);
  - **Santa, Bonding** (tra theo tên hàng SY);
  - **Tinh Nang Dac Biet** (mã SO, khách hàng, TCFNO, tên SY, tính năng, công đoạn, đơn giá VND/m và USD/m, ngày cập
    nhật);
  - Cation&AK, Don gia HC (bảng giá hóa chất), HC CPB Tenter;
  - sheet Báo giá (phiếu báo giá cho sales, đơn vị mét / yard, VND / USD).

**Báo cáo doanh thu ngành (mẫu tháng 10/2026)**
- "BCDT Ngành Dệt HCM":
  - STT, Loại hàng, OC (cột "Số PO"), Mặt hàng, Quy trình, Khách hàng, Sản lượng, ĐVT;
  - chi phí đ/m và tổng theo Nhân công, Khấu hao, Điện, Vật tư, CPQL, Hóa chất, Nhiên liệu, GC ngoài;
  - giá vốn, doanh thu, chênh lệch nhận gia công.
- "BCDT NN TCDN": như trên, thêm Nhuộm?, Nguyên liệu, Cấp màu, Số mét; Loại hàng FS1 / FS2-FOB / FS2-GC.
- "BCDT Ngành Nhuộm HCM":
  - Nhóm hàng, Loại hàng, Loại đơn hàng (BU/SX), OC, Mặt hàng, Quy trình, NL, Cấp màu, Khách hàng, Số mét, Số kg;
  - chi phí HCTN, Điện, Nhiên liệu, Nhân công, Vật tư, Khấu hao, Quản lý NN, GC ngoài;
  - có cả vải đan (ngoài phạm vi).
- Sheet tổng BCDT_SO: sản lượng, doanh thu hàng công ty / nhận gia công, tổng chi phí theo khoản mục.

**Khác**
- Hướng dẫn: 2 file PDF "20251010 Huong dan su dung file tinh gia vai det HCM / TCDN - 2025.pdf".
- Khách hàng: "D:\XUAN\2026\Analysis\5 year performance\Output\Data_clean_2022_2026.xlsx" (sheet Data: Segment, Team,
  Customer). Lấy team FS1 / FS2, khoảng 200 khách hàng, cần làm sạch tên trùng.

## 4. Dữ liệu ra (file/báo cáo, người nhận)
| Đầu ra | Người nhận |
|---|---|
| Costsheet đã lưu (xem trên app), có phiên bản và trạng thái | Sales, trưởng team, trưởng đơn vị |
| Danh sách tổng hợp costsheet (lọc theo trạng thái, team, khách hàng, OC) | Sales, trưởng team, trưởng đơn vị, SO |
| Nhãn thông số vải (file Word theo mẫu sheet PRINT, mở ra in) | Sales, gửi khách |
| Phiếu báo giá hóa chất / báo giá từng mặt hàng đã duyệt | Sales, ngành TCDN |
| Phiếu NGC với GP, %GP từng dòng | Sales gia công, trưởng team |
| Bảng chi phí ngành theo OC từng tháng, tải Excel theo mẫu BCDT của từng ngành | Ngành Dệt HCM, Nhuộm HCM, Nhuộm TCDN |
| Danh sách "Việc chờ tôi" (chờ duyệt, yêu cầu báo giá, phản hồi của ngành), thay cho email | Từng người dùng |

## 5. Quy tắc và cách tính đã biết
**Sợi và lượng mộc**
- Tiêu hao sợi dọc = 0,82% + 1% nếu tick Se + 2,06% nếu tick Hồ.
- Tiêu hao sợi ngang nội suy theo khổ mộc:
  - có Se: 6,77% @130, 5,47% @175, 4,77% @215;
  - không Se: 5,75%, 4,45%, 3,75% ở cùng các khổ đó.
- Lượng sợi = Lượng mộc × Tỷ lệ ÷ (1 − tiêu hao) ÷ (1 − sợi cặn).
  Tiền sợi = Lượng sợi × Giá − Lượng mộc × Tỷ lệ × Sợi cặn × Giá thanh lý sợi cặn.
- % B/C:
  - hàng Mộc: 4% (mộc), 0% (thành phẩm);
  - hàng khác: 5% (mộc), 4% (thành phẩm).
- Số mét thành phẩm cần = Số mét ÷ (1 − %B/C thành phẩm).
  Số mét mộc = Số mét thành phẩm cần ÷ (1 − tiêu hao nhuộm) ÷ (1 − độ co) [÷ (1 − %B/C mộc) nếu không phải Vải Nhuộm].
- **Độ co** = (mật độ ngang thành phẩm − mật độ ngang mộc) ÷ mật độ ngang thành phẩm.
  - Phải lớn hơn 5%, nếu không thì app cảnh báo.
  - Ngoại lệ, độ co = 0:
    - (a) hàng nhận gia công, mộc của khách đã ổn định;
    - (b) có **pre-setting**: các công đoạn trước pre-setting vẫn tính co, các công đoạn sau bằng 0.
  - Khi độ co = 0: sales ghi lý do; phiếu được tô màu cho trưởng team khi duyệt và được đánh dấu trong danh sách ngành xác
    nhận cuối tháng. Không cần ngành bấm xác nhận từng phiếu.
- Hệ số theo số lượng:
  - thí nghiệm: ×2;
  - theo số mét: dưới 5.000 m ×1,1; 5.000 m ×1,05; 10.000–20.000 m ×1; 50.000 m ×0,92; trên 100.000 m ×0,9; nội suy
    ở giữa.
- Kiểm tra: lượng sợi se ước tính phải bằng lượng sợi se nhập.

**Gợi ý tick Se / Hồ** (app gợi ý, sales xác nhận)
- Se: sợi có độ săn (T/M).
- Hồ: áp dụng cho **tất cả sợi dọc** của mã hàng. App gợi ý khi có ít nhất 1 trong 2 điều kiện:
  - Điều kiện 1: tên vải có chữ "HO". Cách ghi không thống nhất: "HO", "(HO)", "SIMHO", "HOSOI". Phải tránh nhận nhầm, ví
    dụ chữ "KHONG".
  - Điều kiện 2: có sợi dọc thuộc một trong các trường hợp:
    - sợi xơ ngắn (spun) có chi số từ 50 trở lên;
    - sợi xơ ngắn không se;
    - sợi filament có SIM hoặc NIM. **HIM thì không cần hồ.**
  - App hiện rõ lý do gợi ý.
- Đối chiếu trên 2.577 mã: 1.921 mã khớp giữa 2 điều kiện; 395 mã chỉ điều kiện 2 bắt được; 261 mã chỉ điều kiện 1 bắt
  được.

**Ngành Dệt**
- Mắc Hồ, Gia công Hồ, Mắc Phân Băng tính theo số mét mắc:
  - Số mét mắc = Số mét mộc ÷ (1 − 0,65%) ÷ (1 − độ co mắc).
  - Độ co mắc lưu theo từng mã, mặc định 10%, SO sửa được.
  - Hình thức "Vải Nhuộm" thì 3 dòng này bằng 0.
- Mắc phân băng: tổng canh = mật độ dọc ÷ 10 × khổ.
- Dệt: định mức theo mật độ ngang. Kiểm: theo hình thức bán. Cone, Se, Hồ: theo các bảng DM.
  - Hóa chất hồ × 1,11.
- Ngoại lệ đang gõ cứng cho mã ES17020213 / ES17020413 (×1,5; ×1,25; ×1,12 + 231). Cần xác nhận còn dùng không.

**Ngành Nhuộm**
- HCM:
  - giá đ/kg theo nguyên liệu × cấp màu; Blended tính theo tỷ trọng (tổng 100%); chia theo khổ đơn / đôi / ba;
  - ×2 nếu thí nghiệm hoặc dưới 250 kg;
  - cộng công đoạn đặc biệt, tính năng đặc biệt, chi phí đặc biệt, chi phí phát sinh, gia công.
- TCDN:
  - quy trình tiêu chuẩn theo nguyên liệu và cấp màu, đ/m theo khoản mục + tiêu hao;
  - hệ số: từ 50.000 m trở lên ×0,95; nhuộm đến 150 m ×1,2; partial đến 100 m ×1,5;
  - công đoạn ngoài quy trình chuẩn, WR, tính năng đặc biệt, chi phí phát sinh, gia công ngoài.
  - Mục tiêu tiêu hao: Nhuộm 3%, Tenter 1%.
  - Công đoạn lặp lại thì thêm dòng, hóa chất chỉ tính ở dòng đầu.
- **Quy trình sản xuất TCDN chỉ để tham khảo**: hiện cho sales biết để chọn công đoạn ngoài quy trình chuẩn. App tự cập
  nhật từ dữ liệu quy trình của ngành Nhuộm TCDN khi ngành tải lên hằng tháng.

**Chi phí phát sinh / báo giá riêng**
- Là chi phí ngành báo giá khi không chạy quy trình tiêu chuẩn. SO không tham gia.
- Ngành tính giá, sales nhập vào costsheet. App gợi ý giá nếu tìm được mã hàng trùng. Sales sửa giá thì phải ghi lý do.

**Giá hóa chất TCDN (Coating, Santa, Bonding, tính năng đặc biệt)**
- Tra theo **tên hàng SY**, không theo TCFNO.
- Một tên SY có thể có tới 17 dòng giá, khác nhau theo khách hàng, tính năng / gia công, quy trình, ghi chú. Giá từ
  khoảng 1.200 đến 11.800 đ/m.
- Cách chọn: sales chọn tên hàng SY -> khách hàng (gồm "tất cả khách hàng") -> tính năng / gia công -> quy trình. App
  hiện giá, ngày cập nhật và mã dòng giá (ví dụ CT-001).
- App tự gợi ý tên SY từ đuôi mã TCFNO trong Peace, hoặc từ cột Item của quy trình sản xuất. App ghi nhớ mã vải đi với
  tên SY nào.
- Chưa có giá: sales gửi "Yêu cầu báo giá" (tự mang theo mã vải, tên SY, khách hàng, tính năng, quy trình, số lượng).
  - TCDN trả giá: 2 người báo giá quy trình, 2 người báo giá hóa chất.
  - **Trưởng ngành TCDN duyệt.**
  - Giá đã duyệt được lưu vào bảng giá, gắn với mã vải.

**Giá bán và lợi nhuận**
- Giá vốn = đơn giá + chi phí phát sinh vào giá vốn.
- GP = giá bán − giá vốn.
- S&A = giá vốn × 10,09%.
- OP = GP − S&A − Commission − vận chuyển và bảo hiểm.
- VAT 8%. USD = VND ÷ tỷ giá tháng.
- Giá sợi và giá bán nhập được bằng USD hoặc VND. Có trường hợp sales cộng thêm 3% vào giá sợi.

**Báo giá từng mặt hàng (TCDN)**
- Tiêu hao lũy kế và độ co phải tính theo logic của file tính giá sales, không gõ tay như hiện nay.

**OC**
- Dạng KDV10-SX-LO-0726-6564.1. Dữ liệu đang ghi bẩn: dấu phẩy thừa, ghi chú dính vào như "(VC260511)". App có ô OC
  riêng và kiểm tra đúng dạng.
- **Main OC** = phần trước dấu chấm. **Summary OC** = có dấu chấm, dùng để tách màu / quy trình / tính năng / cấp màu.
- Sales tính giá theo 1 trong 2 loại.
- Khi đối chiếu: tìm theo Summary OC trước, không có mới tìm theo Main OC.
- Số PO của khách: hiện không cần.
- Sales thêm OC sau khi chốt đơn. Báo giá theo project (tổng số lượng, sau đó nhiều OC) chỉ là giá ban đầu; khi có đơn
  thật phải cập nhật đúng OC và giá sợi lúc đó.
- NGC: 1 phiếu nhiều dòng, mỗi dòng 1 OC + 1 mã hàng (+ ODNO).

**Ngành xác nhận chi phí**
- Hằng tháng ngành tải danh sách OC lên (OC, mã vải, sản lượng thực tế, đơn vị tính).
- Sản lượng lấy từ file ngành, đơn giá lấy từ costsheet.
- App hiện quy trình, thông số, số lượng từng công đoạn và chi phí sản xuất theo OC.
- OC chưa gắn costsheet thì vào danh sách "OC chưa có costsheet". App gợi ý costsheet phù hợp (cùng khách hàng, mã
  vải, OC) để sales gắn.
- Ngành tick dòng sai kèm phản hồi; dòng không tick xem như đã xác nhận.
- Xác nhận xong thì khóa tháng.

**Dữ liệu gốc**
- Ưu tiên Peace. Mã chỉ có ở WFX thì lấy từ WFX.
- Mã mới gấp: PD / SO nhập trên form ngắn (thông số vải, danh sách sợi, tỷ lệ).
- Định mức có ngày hiệu lực; costsheet cũ giữ nguyên số cũ.
- Tỷ giá theo tháng, SO nhập.

**Duyệt**
- Mỗi team (FS1, FS2) có 1 trưởng team duyệt phiếu của team mình.
- 1 trưởng đơn vị duyệt được cả 2 team.

## 6. Quy mô, tần suất, người dùng
- Hơn 200 costsheet/tháng. Dữ liệu gốc khoảng 3.100 mã vải, 11.000 dòng sợi; mã mới phát sinh hằng ngày.
- Bảng giá Coating khoảng 400 dòng; khách hàng khoảng 200.
- Người dùng:
  - Sales FS1, FS2 (kể cả sales gia công nhuộm);
  - 2 trưởng team, 1 trưởng đơn vị;
  - phòng SO;
  - ngành Nhuộm TCDN (2 người báo giá quy trình, 2 người báo giá hóa chất, 1 trưởng ngành);
  - ngành Dệt HCM, Nhuộm HCM, Nhuộm TCDN (xác nhận chi phí hằng tháng).

## 7. Chia thành chức năng (tên, mục tiêu 1 câu, thứ tự làm)
Một ứng dụng duy nhất **"Tính giá vải dệt"**, vì mọi phần dùng chung dữ liệu. Menu chia nhóm: Sales, Duyệt giá, Phòng SO,
Ngành TCDN, Ngành xác nhận chi phí. Làm theo 4 đợt (người dùng đã đồng ý thứ tự):

1. **Đợt 1 - Dữ liệu gốc + Costsheet sales** (rất lớn): SO cập nhật dữ liệu gốc; sales lập, lưu, sao chép, gửi duyệt
   costsheet HCM / TCDN; trưởng team và trưởng đơn vị duyệt; danh sách tổng hợp; in nhãn. Phải ra đúng số của 4 file
   thật.
2. **Đợt 2 - Báo giá ngành Nhuộm TCDN** (lớn): bảng giá hóa chất, báo giá từng mặt hàng, yêu cầu báo giá, trưởng ngành
   duyệt, nối giá vào costsheet TCDN.
3. **Đợt 3 - Tính giá gia công nhuộm NGC** (vừa): phiếu nhiều mã / OC, công đoạn và số lần xử lý thêm, giá hóa chất từ
   đợt 2, GP và %GP, duyệt.
4. **Đợt 4 - Ngành xác nhận chi phí theo OC** (lớn): tải danh sách OC, tìm theo Summary OC rồi Main OC, OC chưa có
   costsheet, tick sai và phản hồi, khóa tháng, tải Excel theo mẫu từng ngành, cập nhật quy trình tham khảo TCDN.

## 8. Khả năng đã kiểm tra (Excel / Word / PDF / web / lưu dữ liệu / biểu đồ) - làm được gì, không làm được gì
- **Làm được:**
  - mọi phép tính của các file Excel;
  - lưu costsheet, phiên bản, trạng thái, luồng duyệt;
  - phân quyền theo màn hình và theo người / nhóm;
  - tải Excel lên (4 file Peace / WFX, danh sách OC, bảng giá, định mức) và xuất Excel (báo cáo ngành);
  - danh sách tổng hợp, lọc, tìm;
  - "Việc chờ tôi" trong app.
- **Làm được nhưng theo cách khác:**
  - in nhãn: tạo file Word theo mẫu rồi mở ra in hoặc lưu PDF;
  - tỷ giá: SO nhập tay mỗi tháng;
  - dữ liệu gốc: SO tải file lên bằng tay (khoảng 1 phút), cộng thêm form nhập nhanh mã gấp.
- **Không làm được** (người dùng đã chấp nhận cách thay thế):
  - tự lấy dữ liệu từ SharePoint / Peace / WFX (cần đăng nhập, không nối được);
  - gửi email thông báo;
  - tự chạy cập nhật theo giờ;
  - đăng nhập bằng tài khoản Windows / Microsoft (tài khoản do quản trị viên tạo).
- Quy mô dữ liệu nằm trong giới hạn khoảng 200 nghìn dòng mỗi bảng.

## 9. Chưa rõ - cần hỏi tiếp ở bước sau
- Ngưỡng cảnh báo GP% / OP%: người dùng chưa chốt (SO tự đặt trong dữ liệu gốc).
- Ngoại lệ gõ cứng cho mã ES17020213 / ES17020413 còn dùng không.
- Mẫu nhãn in (sheet PRINT) giữ nguyên hay chỉnh.
- Cột chính xác của file danh sách OC ngành tải lên mỗi tháng (dự kiến: OC, mã vải, sản lượng thực tế, ĐVT) cho từng
  ngành.
- Doanh thu ngành và chênh lệch nhận gia công được tính thế nào trong báo cáo ngành.
- Danh sách khách hàng: làm sạch tên trùng (công ty mẹ / chi nhánh, dòng "TEAM FORECAST").
- Tên khách hàng trong bảng giá Coating không thống nhất (TENGLONG / TENLONG, ELAND / E-LAND WORLD / ELAND CHINA).
- Ô ghi chú quy trình sản xuất của costsheet TCDN đang báo #N/A ở cả 2 file thật.
- Nhập mã gấp: ai được nhập (PD, SO hay cả 2), và khi file Peace / WFX tải lên sau có mã đó thì lấy số nào.

## 10. Ngoài phạm vi (đã thống nhất là không làm)
- Vải đan (có trong báo cáo Nhuộm HCM).
- Xuất costsheet ra Excel.
- Gửi email / Zalo / Teams tự động; chạy tự động theo giờ.
- Kết nối trực tiếp SharePoint, Peace, WFX, ERP.
- Số PO của khách hàng.
