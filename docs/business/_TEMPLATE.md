# <Feature title>

| Feature key | `<feature_key>` (= folder name in `backend/features/` and `frontend/features/`) |
|---|---|
| Owner (Người phụ trách) | <Owner> |
| Status (Trạng thái) | Draft |
| Last updated | YYYY-MM-DD |

> Write the content in Vietnamese or English. Keep the section titles and the IDs (UC-xx, BR-xx, AC-xx):
> the AI maps them 1-to-1 to code. Delete the hints in *italics* when done.

## 1. Goal (Mục tiêu)
*What problem does this feature solve? Who benefits? 2-4 sentences.*

## 2. Actors (Người dùng)
| Actor | Description |
|---|---|
| *e.g. Nhân viên kho* | *Uploads the monthly stock file* |

## 3. Glossary (Thuật ngữ)
| Term | Meaning |
|---|---|
| | |

## 4. Data (Dữ liệu)
*One table per business object. These become `models/`.*

### 4.1 <Object name>
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| | text / integer / decimal / date / yes-no / list | Yes/No | | |

## 5. Input / output files (File nhập / xuất)
*Excel/Word/PDF files the feature reads or produces: sheet name, column headers, template placeholders.*

| File | Direction (in/out) | Format | Columns / placeholders |
|---|---|---|---|
| | | .xlsx | |

## 6. Use cases (Nghiệp vụ) - each UC becomes ONE controller method + ONE service
### UC-01: <Name>
- **Actor:**
- **Trigger:** *what the user does*
- **Input:**
- **Main flow:**
  1.
  2.
- **Output:**
- **Errors / alternative flows:**
- **Rules applied:** BR-01, BR-02

## 7. Business rules (Quy tắc nghiệp vụ)
| ID | Rule | Error message shown to user (VI) |
|---|---|---|
| BR-01 | | |

## 8. Screens (Màn hình) - each screen becomes ONE page
### Screen 1: <Name> (landing page)
- **Purpose:**
- **Blocks / widgets:** *filters, upload box, table columns, buttons, charts*
- **Actions:** *button -> UC-xx*

## 9. Acceptance criteria (Tiêu chí nghiệm thu)
- [ ] AC-01:
- [ ] AC-02:

## 10. Open questions (Câu hỏi mở)
*The AI writes here anything ambiguous and the default it chose.*

## 11. Implementation map (filled by the AI)
| Spec item | Code |
|---|---|
| UC-01 | `XxxController.<method>()` -> `services/<name>_service.py` |
| BR-01 | `business/<file>.py::<RuleClass>` |
| Screen 1 | `frontend/features/<feature_key>/pages/<page>.py` |
