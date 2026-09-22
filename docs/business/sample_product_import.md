# Nhập sản phẩm từ Excel (mẫu)

| Feature key | `sample_product_import` (= folder name in `backend/features/` and `frontend/features/`) |
|---|---|
| Owner (Người phụ trách) | TC Vibe Coding |
| Status (Trạng thái) | Done - REFERENCE IMPLEMENTATION (copy its patterns, do not extend it) |
| Last updated | 2026-09-22 |

> This is the reference example of a complete business document and its implementation.
> Read it together with the code to learn how every section maps to code.

## 1. Goal (Mục tiêu)
Nhân viên kho cập nhật danh sách sản phẩm hàng loạt bằng file Excel thay vì nhập tay; hệ thống kiểm tra lỗi
trước khi lưu, cho biết tồn kho hiện tại và xuất báo cáo Excel.

## 2. Actors (Người dùng)
| Actor | Description |
|---|---|
| Nhân viên kho | Tải file mẫu, nhập file, xem và xuất tồn kho |

## 3. Glossary (Thuật ngữ)
| Term | Meaning |
|---|---|
| Mã SP | Mã định danh duy nhất của sản phẩm |
| Thành tiền | Số lượng × Đơn giá |

## 4. Data (Dữ liệu)
### 4.1 Sản phẩm (Product)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| code | text ≤ 20 | Yes | Mã SP, in hoa | SP-001 |
| name | text ≤ 200 | Yes | Tên sản phẩm | Áo thun cotton |
| unit | text | No (default "cái") | Đơn vị tính | cái |
| quantity | integer ≥ 0 | Yes | Số lượng tồn | 120 |
| unit_price | decimal > 0 | Yes | Đơn giá (VND) | 85000 |

## 5. Input / output files (File nhập / xuất)
| File | Direction | Format | Columns |
|---|---|---|---|
| File mẫu nhập | out | .xlsx | Mã SP, Tên sản phẩm, Đơn vị, Số lượng, Đơn giá |
| File nhập | in | .xlsx / .xls | Same columns (headers matched without accents/case, aliases allowed) |
| Báo cáo tồn kho | out | .xlsx | Mã SP, Tên sản phẩm, Đơn vị, Số lượng, Đơn giá, Thành tiền, Trạng thái |

## 6. Use cases (Nghiệp vụ)
### UC-01: Tải file mẫu
- **Output:** file `mau-nhap-san-pham.xlsx` with the headers and 2 example rows.

### UC-02: Kiểm tra file (không lưu)
- **Input:** Excel file.
- **Main flow:** read the file → normalize each row → apply BR-01..BR-05, BR-10 → decide create/update (BR-06).
- **Output:** every row with its result (create / update / rejected + reasons) and totals.

### UC-03: Lưu dữ liệu
- **Input:** the same file.
- **Main flow:** same checks as UC-02, then save only valid rows (BR-07).
- **Output:** number of created, updated, rejected rows.

### UC-04: Tra cứu sản phẩm
- **Input:** keyword (code or name), stock status (optional).
- **Output:** products with total value (BR-09) and stock status (BR-08), plus totals.

### UC-05: Xuất báo cáo tồn kho
- **Input:** same filters as UC-04. **Output:** Excel report.

## 7. Business rules (Quy tắc nghiệp vụ)
| ID | Rule | Error message shown to user (VI) |
|---|---|---|
| BR-01 | Mã SP required; only A-Z, 0-9, "-"; ≤ 20 chars; converted to upper case | Mã SP bắt buộc, chỉ gồm chữ in hoa, số, dấu '-' và tối đa 20 ký tự. |
| BR-02 | Tên sản phẩm required, ≤ 200 chars | Tên sản phẩm bắt buộc và tối đa 200 ký tự. |
| BR-03 | Số lượng required, integer ≥ 0 | Số lượng bắt buộc, phải là số nguyên ≥ 0. |
| BR-04 | Đơn giá required, > 0 | Đơn giá bắt buộc và phải lớn hơn 0. |
| BR-05 | A code appearing more than once in the same file: ALL those rows are rejected | Mã SP '<code>' bị trùng trong file. |
| BR-06 | Code already stored → update name, unit, quantity, price; otherwise create | - |
| BR-07 | Only valid rows are saved; invalid rows are reported back | - |
| BR-08 | Stock status: quantity = 0 → Hết hàng; 1-9 → Sắp hết; ≥ 10 → Còn hàng | - |
| BR-09 | Thành tiền = Số lượng × Đơn giá | - |
| BR-10 | File must be .xlsx/.xls, ≤ 10 MB, contain all required columns, 1-5000 data rows | File thiếu cột bắt buộc: ... |

## 8. Screens (Màn hình)
### Screen 1: Nhập sản phẩm từ Excel (landing page)
- Step 1 panel: download template (UC-01).
- Step 2 panel: upload box (.xlsx/.xls).
- Step 3 panel: KPIs (total, valid, errors, create, update), toggle "only errors", result table,
  button "Lưu N dòng hợp lệ" (UC-03), link to Screen 2.

### Screen 2: Danh sách sản phẩm
- Filters: keyword, status. KPIs: count, total quantity, total value, out/low stock.
- Table + "Xuất Excel" button (UC-05) + donut chart of stock status.

## 9. Acceptance criteria (Tiêu chí nghiệm thu)
- [x] AC-01: The template file, uploaded unchanged, has 2 valid rows and 0 errors.
- [x] AC-02: A file without a required column shows "File thiếu cột bắt buộc".
- [x] AC-03: Duplicated codes in one file are all rejected with BR-05.
- [x] AC-04: Importing an existing code updates it (same id), never duplicates it.

## 10. Open questions (Câu hỏi mở)
- None.

## 11. Implementation map (filled by the AI)
| Spec item | Code |
|---|---|
| Section 4.1 | `backend/features/sample_product_import/models/product.py::Product` |
| Section 5 | `constants.py::IMPORT_COLUMNS`, `builders/import_rows_builder.py`, `builders/product_builders.py` |
| UC-01 | `SampleProductImportController.download_template()` → `services/download_template_service.py` |
| UC-02 | `SampleProductImportController.preview_import()` → `services/preview_import_service.py` |
| UC-03 | `SampleProductImportController.commit_import()` → `services/commit_import_service.py` |
| UC-04 | `SampleProductImportController.list_products()` → `services/list_products_service.py` |
| UC-05 | `SampleProductImportController.export_products()` → `services/export_products_service.py` |
| BR-01..BR-05 | `business/import_rules.py` |
| BR-06, BR-07, BR-10 (row limit) | `business/import_business.py::ProductImportBusiness` |
| BR-08, BR-09 | `business/stock_business.py::ProductStockBusiness`, `models/product.py::Product.total_value` |
| BR-10 (format/columns) | `builders/import_rows_builder.py::ImportRowsBuilder` |
| Screen 1 | `frontend/features/sample_product_import/pages/import_page.py` |
| Screen 2 | `frontend/features/sample_product_import/pages/product_list_page.py` |
| Logs | every service logs its steps; log panel at the bottom of both pages |
| Tests | `backend/features/sample_product_import/tests/` |
