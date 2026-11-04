# Framework hardening plan (main, 2026-11-03)

Requested by the framework owner.

## Scope
1. **Soft delete everywhere (cờ xoá).** `BaseEntity` gets `is_deleted`, `deleted_at`, `deleted_by` (excluded from
   `model_dump()` so `XxxDTO(**entity.model_dump())` keeps working; repositories store them explicitly).
   `delete()` / `clear()` only set the flag; reads (`get`, `list_all`, `find`, `find_one`, `exists`, `count`) skip
   flagged rows; `restore(id)` and `list_deleted()` added. `_load()` still returns every stored row (seeding
   subclasses stay correct). Hard delete only for framework login sessions (`purge`). Migrations:
   `update_documents(... -> None)` flags the document instead of deleting the row.
2. **Row guards** (the "1 million rows" class of bugs): `ExcelReader(max_rows=...)`, `data_table` / `editable_table`
   caps with a Vietnamese warning (an over-size editable table returns its rows unchanged, never `[]`), a WARNING in
   the log when a table read from the database is very large. Caps are `Settings` fields (`APP_MAX_*`).
3. **lru_cache** on values recomputed per call: `database_url()` (keyed on the settings values),
   `feature_developer()`. Row caches stay `db.cached_table` (versioned); `get()` / `exists()` no longer copy the
   whole table.
4. **Charts**: one shared component `frontend/core/components/charts.py` (`bar_chart`, `line_chart`, `pie_chart`):
   aggregation / point caps before drawing, theme colours, Vietnamese number format, empty state. Sample page uses it.
5. **Supreme rules** `SUPREME-RULES.md`: never writable by AI (hook + settings deny), printed at every session start;
   framework paths frozen for AI tools; PowerShell tool covered by the gate too.

6. **App registry** `backend/app_registry.py` (added mid-way): one line `("<prefix>", "<key>")` per app ->
   a list of all apps in the system, with their prefixes and keys.
## Verification
- `scripts/check.py` -> ALL CHECKS PASSED; `scripts/doctor.py` -> APP IS HEALTHY on a throw-away SQLite database
  (the shared PostgreSQL 172.22.0.79:5433 was unreachable from this machine: connect timeout).

## Not in scope
- The `vibe/tinh-gia-soi-1210` branch: its next sync with main (Prompt 6) must re-check its `repository.delete()`
  calls (now soft deletes) and its `_load` override.
