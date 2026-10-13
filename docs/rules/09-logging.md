# 09 - Logging (file only)

All logs go to **`logs/app.log`** (rotates at 2 MB, 3 backups; level `APP_LOG_LEVEL` in `.env`, default INFO).
There is NO log panel on screen (it re-read the log file on every rerun and made every page slow). When something
goes wrong the user describes it (or sends a screenshot) and the AI reads `logs/app.log`.

## What is automatic (framework)
| Where | What is logged |
|---|---|
| `Gateway.call()` | failed calls `failed: [CODE] message` (WARNING), crashes + traceback (ERROR); successful calls only at DEBUG |
| `BaseService.handle()` | `<Service> started` / `finished in N ms` (DEBUG) |
| `BasePage.run()` | page crashes with traceback (ERROR) |
| `FeatureRegistry` | features that fail to load (ERROR) |

## What you MUST do in every business feature
1. In each service, log the important steps with `self.logger.info(...)`: inputs (without secrets or file contents),
   counts, decisions and results - e.g. `self.logger.info("Saved %s products", n)`.
2. Use levels correctly: `debug` details, `info` normal steps, `warning` handled problems, `error` failures
   (`self.logger.exception(...)` inside `except` to include the traceback).
3. Never `print()`. Outside classes: `logger = get_logger(__name__)`.

## Base functions (`backend/core/logger.py`)
| Function | Use |
|---|---|
| `get_logger(__name__)` | logger of a module (services/controllers/pages already have `self.logger`) |
| `log_file_path()` | path of `logs/app.log` |
