# Sewing Performance - mở rộng 2026-11-13 lần 2 (Prompt 5): "Line trend" theo tuần / tháng / năm ở chi tiết chuyền

## Thêm và thay đổi
1. Line Detail (Screen 2), khối chi tiết của chuyền đã chọn (cùng chỗ sở trường và bảng đơn hàng có tên khách), thêm
   phần "Line trend" nằm trên bảng đơn hàng (BR-90, mới):
   - nút chọn kỳ By week / By month / By year (mặc định By week) và nút chọn đường %Efficiency (with ratio) / MO 8h
     (mặc định %Efficiency);
   - biểu đồ 1: cột Output (pcs) theo kỳ; biểu đồ 2 ngay dưới, cùng trục thời gian: đường của chỉ số đã chọn;
   - ngay dưới hai biểu đồ: bảng số 3 dòng Output, %Efficiency (with ratio), MO 8h, mỗi kỳ một cột.
2. Khoảng thời gian: từ 01/01 của năm của "Đến ngày" đến "Đến ngày" đang chọn; "Từ ngày" của bảng không áp dụng.
3. Bộ lọc Customer group / Product group áp như bảng chuyền (BR-29): Output, %Efficiency theo nhóm đã chọn; MO 8h "-".
4. Biểu đồ dùng chung của app chưa vẽ được cột + đường chung một khung và chưa ghi số trên điểm: số chính xác nằm ở bảng
   số ngay dưới và khi rê chuột. Khi người phụ trách khung sườn bổ sung, app đổi sang một biểu đồ gộp có số trên điểm.

## Ảnh hưởng tới phần đã có
- Không đổi: bảng chuyền, bảng đơn hàng, khối sở trường, nút "Download Line performance", bộ lọc của Line Detail.
- Không thêm dữ liệu lưu: mọi số tính lại từ sản lượng đã lưu.

## Câu hỏi đã trả lời (13/11/2026, người dùng: "all đề xuất")
1a trong khối chi tiết của chuyền, trên bảng đơn hàng; 2a từ 01/01 năm nay đến "Đến ngày", mặc định By week;
3a cột Output + đường + bảng số ngay dưới; 4 nút chuyển %Efficiency / MO 8h, mặc định %Efficiency; 5a theo bộ lọc
khách hàng / sản phẩm, MO 8h "-" khi lọc.

## Truy vết
| Mục | Code | Kiểm tra |
|---|---|---|
| BR-90 | `LineDetailRequest.trend_line` / `trend_kind`, `GetLineDetailService._trend`, `LineOverviewBusiness.trend_point`, `LineTrendResponseBuilder`, `components/line_trend_blocks.py`, `line_detail_page._trend` | AC-125, AC-126, AC-127 ✅ (`test_line_trend.py`); dựng thử với dữ liệu thật LINE 25 Fac Vinh Long: By week 43 tuần, By month Jan–Oct, 2 biểu đồ + bảng số, không lỗi ✅ |
| regression: existing tests | toàn bộ bài kiểm tra của app | quality gate: ALL CHECKS PASSED (487 passed) ✅; health check: APP IS HEALTHY ✅ (AC-128) |

## Fix log
