# 07 - Testing and Verification

## One command
```
python scripts/check.py          # ruff lint + all tests. MUST print "ALL CHECKS PASSED"
python scripts/check.py --fix    # auto-fix lint/format first
```
The Claude Code Stop hook runs it automatically when code changed and blocks finishing while it fails.

## Tests you write (per feature, in `backend/features/<key>/tests/`)
- Every business rule BR-xx: at least one passing and one failing case (`business.collect_violations`).
- Every service: happy path + main error path, with injected repositories:
  `ProductRepository(file_path=tmp_path / "p.json")`.
- Build input files in memory (openpyxl `Workbook` -> bytes -> `UploadedFileDTO`).
- Tests never touch the real `data/` folder (`conftest.py` redirects it).

## What the architecture tests enforce (`tests/architecture/`, never edit)
| Test | Rule |
|---|---|
| `test_structure.py` | all features and Home load; backend/frontend feature exists on both sides, required folders/files, valid key, business doc exists, no stray files |
| `test_inheritance.py` | classes inherit their layer's base; one service per file named `xxx_service.py`; exactly ONE controller per feature, exported by the feature `__init__.py`; each service called by exactly one controller method; controller methods are one `return` line; BR codes exist in the business doc; pages inherit BasePage and are listed in the manifest |
| `test_imports.py` | backend never imports streamlit/frontend; features never import each other; layer import matrix; pages import only `backend.core` + own feature root/`dto`; pages never create controllers (must use `gateway.open`); no file libraries in frontend; no `print()`; no `open()` in frontend |
| `test_pages_render.py` | Home and every feature page render headlessly (Streamlit AppTest) on first load, with no data, without any exception or error box |
| `tests/core/` | framework base classes, gateway (+ middlewares) and logging behave as documented |

## When a check fails
Read the message: it names the file, line and rule. Fix the code to follow the rule.
Never delete/skip tests, never add `# noqa` or ignores to pass.
