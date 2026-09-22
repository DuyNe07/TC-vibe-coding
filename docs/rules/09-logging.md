# 09 - Logging (file + on-screen log panel)

Users cannot read a terminal. All logs go to **`logs/app.log`** and are shown **on screen** in the
"📜 Nhật ký chạy (log)" panel, where users can copy or download them to send to the AI / a developer.
The panel is not realtime: it refreshes when the page reruns or when "Tải lại" is pressed.

## What is automatic (framework)
| Where | What is logged |
|---|---|
| `Gateway.call()` | every action: `<Controller>.<action> done in N ms` (INFO), `failed: [CODE] message` (WARNING), `crashed` + traceback (ERROR) |
| `BaseService.handle()` | `<Service> started` / `finished in N ms` (DEBUG) |
| `BasePage.run()` | page crashes with traceback (ERROR) |
| `FeatureRegistry` | features that fail to load (ERROR) |
| Log panel | bottom of every feature page = logs of that feature only (Home has no log panel) |

## What you MUST do in every business feature
1. In each service, log the important steps with `self.logger`:
   ```python
   self.logger.info("Read %s rows from %s", len(rows), request.file.filename)
   self.logger.info("Validation: %s valid, %s invalid", valid, invalid)
   self.logger.info("Saved %s products (created=%s, updated=%s)", n, created, updated)
   ```
   Log inputs (without secrets or full file contents), counts, decisions and results.
2. Use levels correctly: `debug` details, `info` normal steps, `warning` handled problems, `error` failures
   (`self.logger.exception(...)` inside `except` to include the traceback).
3. Keep the page log panel (`show_log_panel = True` - the default). Do not remove it.
4. Pages may log user actions: `self.logger.info("User clicked export (keyword=%r)", keyword)`.
5. Never `print()`. Outside classes: `logger = get_logger(__name__)`.

## Base functions (`backend/core/logger.py`)
| Function | Use |
|---|---|
| `get_logger(__name__)` | logger of a module (services/controllers/pages already have `self.logger`) |
| `read_log_entries(feature_key=None, min_level="INFO", limit=200)` | last entries, filtered by feature (via module path `...features.<key>...`) |
| `log_file_path()` | path of `logs/app.log` |
UI: `frontend.core.components.log_panel(feature_key, key=...)` (already added by `BasePage`).
The log file rotates at 2 MB (3 backups). Level is set by `APP_LOG_LEVEL` in `.env`.
