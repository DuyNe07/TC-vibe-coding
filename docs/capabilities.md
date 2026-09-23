# Ứng dụng này làm được những gì (danh mục khả năng)

Dành cho người dùng nghiệp vụ và cho AI: trước khi hứa với người dùng điều gì, AI phải đối chiếu danh mục này.
Mỗi dòng "Làm được" đều đã có sẵn thư viện và lớp dùng chung trong khung sườn, không cần cài thêm gì.

## 1. File Excel (.xlsx, .xls, .csv) - dùng nhiều nhất
| Làm được | Ở đâu trong code |
|---|---|
| Đọc file người dùng tải lên, kiểm tra từng dòng theo quy tắc, báo dòng nào sai vì sao | `ExcelReader` (`backend/shared/file_io`) + `business/` (BR-xx) |
| Tạo **file mẫu** để người dùng tải về rồi điền | `ExcelWriter` trong một service "tải file mẫu" |
| Xuất báo cáo Excel (nhiều sheet, nhiều bảng, tiêu đề cột tiếng Việt) | `ExcelWriter` |
| Nhận nhiều file một lần, gộp lại, đối chiếu giữa các file | nhiều `ExcelReader` trong cùng một service |
| Chấp nhận tên cột viết khác nhau (có dấu / không dấu / hoa thường) | `normalize_key` (`backend/shared/utils`) |
| Giới hạn dung lượng và số dòng để không treo máy | `constants.py` của chức năng |

## 2. File Word (.docx) và PDF
| Làm được | Ở đâu |
|---|---|
| Đọc nội dung Word (đoạn văn, bảng) để lấy dữ liệu | `WordReader` |
| Tạo file Word mới (tiêu đề, đoạn văn, bảng) | `WordWriter` + `WordContent` |
| Điền dữ liệu vào **file Word mẫu** có chỗ trống (hợp đồng, quyết định, phiếu) | `WordTemplateRenderer` |
| Đọc chữ trong PDF để lấy số liệu | `PdfTextReader` |
| Không làm được: sửa trực tiếp PDF, đọc PDF chỉ là ảnh chụp (scan) | - |

## 3. Lưu dữ liệu trong ứng dụng
| Làm được | Ở đâu |
|---|---|
| Lưu danh sách/bản ghi lâu dài (thêm, sửa, xoá, tìm, lọc) | `JsonFileRepository` -> `data/<chức_năng>/*.json` |
| Trạng thái và luồng duyệt (ví dụ Nháp -> Đã gửi -> Đã duyệt) | enum trong `models/` + quy tắc chuyển trạng thái trong `business/` |
| Lịch sử thay đổi (ai sửa, lúc nào) nếu nghiệp vụ cần | thêm trường vào model + ghi log |
| Không làm được: nối tới SQL Server / ERP / Google Sheets; nhiều người sửa cùng một dòng cùng lúc | - |

## 4. Giao diện (Streamlit)
| Làm được | Ở đâu |
|---|---|
| Bảng như Excel: lọc, sắp xếp, tìm, xem toàn màn hình, tải CSV | `data_table` |
| Sửa trực tiếp trong ô như Excel, thêm/xoá dòng rồi bấm Lưu | `editable_table` |
| Chọn một dòng để xem chi tiết / sửa | `data_table(selection="single")` |
| Form nhập liệu (chữ, số, ngày, chọn một / nhiều, bật tắt) | `st.text_input`, `st.number_input`, `st.date_input`, `st.selectbox`... |
| Ô số liệu tổng hợp (KPI), biểu đồ cột / đường / tròn | `stat_row`, `st.bar_chart`, `st.plotly_chart` |
| Tải file lên, tải file về | `file_upload`, `download_button` |
| Hộp thoại xác nhận, tab, khối gấp gọn | `st.dialog`, `st.tabs`, `st.expander` |
| Nhiều màn hình cho một chức năng, hiện ở menu bên trái | `manifest.py` (`pages=(...)`) |
| Khung nhật ký chạy (log) để copy khi gặp lỗi | có sẵn ở cuối mỗi trang |
| Không làm được: đăng nhập / phân quyền, đổi logo-màu riêng cho một chức năng, giao diện mobile riêng, tự động cập nhật theo thời gian thực | - |

## 5. Tính toán, xử lý bằng Python
Bất cứ tính toán nào Python làm được đều dùng được, miễn là viết trong `business/` (quy tắc, công thức) hoặc
`builders/` (biến đổi dữ liệu):
- cộng trừ nhân chia, phần trăm, làm tròn theo quy tắc kế toán (`Decimal`, không sai số);
- tính theo ngày tháng: số ngày làm việc, hạn xử lý, tuổi tồn kho;
- nhóm, tổng hợp, xếp hạng, so sánh giữa hai kỳ, đối chiếu hai danh sách (pandas);
- phân bổ, chia lô, tính giá bình quân, tính lương/thưởng theo công thức, kiểm tra trùng lặp;
- sinh mã tự động, chuẩn hoá tên (bỏ dấu, viết hoa), kiểm tra định dạng (mã số thuế, số điện thoại).

## 6. Lấy dữ liệu từ web (tải trang, "cào" dữ liệu)
| Làm được | Ở đâu |
|---|---|
| Tải một trang web công khai theo địa chỉ, lấy chữ, **bảng**, danh sách liên kết | `fetch_page` (`backend/shared/web`) -> `.text()`, `.tables()`, `.links()`, `.find_texts("//h2")` |
| Tải một file trên mạng (Excel, PDF) rồi xử lý như file người dùng tải lên | `fetch_file` + `ExcelReader` / `PdfTextReader` |
| Lặp qua danh sách địa chỉ người dùng nhập hoặc dán từ Excel, lưu kết quả và xuất Excel | service của chức năng: `fetch_page` -> `business/` -> `repositories/` -> `ExcelWriter` |
| Giới hạn an toàn: chỉ `http/https`, chờ tối đa 20 giây, tối đa 10 MB mỗi trang; lỗi báo rõ nguyên nhân (chức năng có thể bọc lại thành câu tiếng Việt của mình) | `WEB_TIMEOUT_SECONDS`, `WEB_MAX_BYTES`, `WebFetchError` |

Chưa làm được, và cách đi đường khác:
- **Tìm kiếm Google / Bing tự động:** không có sẵn. Google không cho tìm kiếm tự động miễn phí. Hai cách thay thế:
  (a) người dùng dán danh sách địa chỉ (hoặc một file Excel chứa địa chỉ) rồi app tự tải và bóc dữ liệu;
  (b) nếu đơn vị có khoá API của dịch vụ tìm kiếm (Google Custom Search, Bing...), AI có thể thêm: cần khoá đặt
  trong file `.env` và mạng nội bộ cho phép ra ngoài. Hãy nói rõ ở Prompt 0.5 nếu cần.
- **Trang cần đăng nhập, trang chỉ hiện dữ liệu sau khi chạy JavaScript, trang có CAPTCHA:** không lấy được (ứng dụng
  không mở trình duyệt thật).
- **Mạng công ty chặn ra ngoài (proxy):** nếu máy có proxy, đặt biến `HTTP_PROXY` / `HTTPS_PROXY` trong `.env`.
- Chỉ lấy dữ liệu công khai và đúng điều khoản của trang; không tải hàng loạt gây nghẽn trang của người khác.

## 7. Những việc ứng dụng không làm (đừng hứa với người dùng)
| Việc | Vì sao / thay thế |
|---|---|
| Đăng nhập, phân quyền theo người dùng | Không có hệ thống người dùng. Thay bằng: nhập tay tên người thực hiện / người duyệt |
| Gửi email, gửi Zalo/Teams tự động | Không có. Thay bằng: xuất file rồi người dùng tự gửi |
| Chạy tự động theo giờ (job định kỳ) | Ứng dụng chỉ chạy khi có người mở. Thay bằng: người dùng bấm nút khi cần |
| Nối trực tiếp vào ERP / SQL / Google Sheets | Chưa có. Thay bằng: xuất file từ hệ thống kia rồi tải lên đây |
| Dùng cho hàng triệu dòng dữ liệu | Dữ liệu lưu dạng file JSON; phù hợp hàng nghìn đến vài chục nghìn dòng |
| Chạy trên điện thoại như app cài đặt | Chỉ là web nội bộ, mở bằng trình duyệt |

Cần một khả năng chưa có trong danh mục này? Không tự ý thêm thư viện: ghi vào tài liệu nghiệp vụ và hỏi người phụ
trách khung sườn (`requirements.txt` do khung sườn quản lý - xem `docs/rules/08-dependencies-and-running.md`).
