# 06 - Coding Standards

## Python
- Python 3.11 syntax (`X | None`, `list[int]`, `StrEnum`). No PEP 695 generics (3.12+).
- Full type hints on every function and method, including return types.
- Keep files short (aim < 200 lines). Split by responsibility, not by size alone.
- No wildcard imports, no relative imports beyond the feature, no module-level mutable state.
- Constants: `UPPER_CASE` in `constants.py`. No magic numbers in services/business.
- Paths: never absolute; use `get_settings().data_dir`, `get_settings().feature_data_dir(key)`.
- Money/quantities: `Decimal` in models; convert to `float` only in DTOs for display.
- Lint/format: ruff (config in `pyproject.toml`). `python scripts/check.py --fix` auto-fixes style.

## Naming
English for identifiers, comments, docstrings and log messages. See the table in 01.

## Texts shown to users
- Labels, messages and error messages follow the language of the business document (Vietnamese by default).
- Error messages say what is wrong AND what to do: "File thiếu cột bắt buộc: Đơn giá. Hãy dùng file mẫu."

## Errors
- Raise `AppError` subclasses for expected problems; let unexpected exceptions propagate (they are logged
  and shown with a traceback).
- Never swallow exceptions silently (`except: pass` is forbidden).

## Logging
- Never `print()`. See [09-logging.md](09-logging.md).

## Docstrings
- Module docstring: what the file contains (one line is enough).
- Controller methods: `"""UC-xx <use case name>."""` so the business doc and code stay linked.
