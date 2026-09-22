# Business documents

One file per feature: `docs/business/<feature_key>.md`, created from [_TEMPLATE.md](_TEMPLATE.md)
(automatically by `scripts/new_feature.py`). The user (or analyst) writes the business content; the AI
implements it and keeps section 11 "Implementation map" up to date.

## Rules for the AI
1. Read the WHOLE document before coding. It is the source of truth for data, use cases, rules and screens.
2. Keep the IDs: `UC-xx` (use cases), `BR-xx` (business rules), `AC-xx` (acceptance criteria).
   - Each `UC-xx` -> one service + one controller method whose docstring starts with `UC-xx`.
   - Each `BR-xx` -> a rule class with `code = "BR-xx"` (the architecture test checks the code exists here)
     or a clearly named method in a `BaseBusiness` class, referenced in section 11.
   - Each screen -> one page.
3. Never invent rules. While WRITING the document (Prompt 1), ask the user about anything missing or
   ambiguous - application-level questions only, never about code - and settle everything before setting
   `Status: Ready for implementation`. While IMPLEMENTING (Prompt 2), ask ONE round of questions about the look of
   the screens only (recorded in section 8 as `### Giao diện đã chốt (UI concept)`), then never ask again: choose the
   safest behaviour consistent with the document, write it in section 10 as `Giả định (triển khai): ...` and report it.
4. When the user changes a requirement, update this document first, then the code and tests.
5. Error messages shown to users come from the "Error message" column of section 7.
6. `sample_product_import.md` is the complete reference example.
