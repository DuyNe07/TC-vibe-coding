# 08 - Dependencies and Running

## Running (users are not programmers: keep this working)
Open PowerShell in the project folder, then:
```
powershell -ExecutionPolicy Bypass -File .\run.ps1                        # normal run
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Port 8600             # other port
powershell -ExecutionPolicy Bypass -File .\run.ps1 -NoBrowser             # do not open the browser
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Reinstall             # force reinstalling packages
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Watch                 # reload by itself when code changes
```
Without `-Watch` a code change needs a restart (Ctrl+C, run again): Streamlit's file watcher costs 2-3 seconds on the
first pages of a fresh server on Windows, so it is off by default (`.streamlit/config.toml`, `fileWatcherType`).
(`-ExecutionPolicy Bypass` is needed because Windows blocks unsigned scripts by default.)

`run.ps1` steps:
1. Check `.venv`; create it with Python 3.13 if missing (recreate it if it uses another Python version).
2. Install `requirements.txt` only when packages are missing or the file changed (hash stored in `.venv`).
3. Create `.env` from `.env.example` if missing, create `data/` and `logs/`, pick a free port.
4. Bring the database up to date: `scripts/migrate.py` (Alembic revisions, docs/rules/02 "Migrations").
5. Start Streamlit (ONE process) and open `http://localhost:<port>/home` as soon as the server answers.
Stop with Ctrl+C.

Rules:
1. `run.ps1` is the ONLY launcher. Do not create other start scripts (.sh, .bat), Dockerfiles, Makefiles or servers.
2. Keep `run.ps1` ASCII-only (Windows PowerShell 5.1 reads scripts without BOM as ANSI) and compatible with
   PowerShell 5.1 (no `&&`, `??`, ternary).
3. If you change how the app starts, update `run.ps1` and verify it still opens `/home`.

## Dependencies
1. `requirements.txt` is the ONLY dependency file. Exact pins (`package==x.y.z`) + a comment saying why.
   Every pin must have a wheel for Python 3.13 (`.python-version`, `requires-python` in `pyproject.toml`); check with
   `python -m pip install --dry-run --only-binary=:all: --python-version 3.13 -r requirements.txt --target tmp`.
2. Before adding a library, check it is not already covered: Excel (pandas, openpyxl, xlrd), Word
   (python-docx, docxtpl), PDF (pypdf), public web pages (requests, lxml - via `backend/shared/web`), database
   (sqlalchemy async + asyncpg/aiosqlite - via `SqlRepository`),
   charts (plotly; matplotlib + seaborn via `pyplot_chart`), validation (pydantic). What the app can do with them:
   `docs/capabilities.md`.
3. After adding one, run `run.ps1` again (it auto-installs) or `.venv/Scripts/python.exe -m pip install -r requirements.txt`.

## Server deployment (Docker)
Everything lives in `packaging/`. `./packaging/build.sh -v <version>` builds image `tc-vibe-coding:<version>` from
`packaging/Dockerfile` (Python 3.13, `requirements.txt`; build context = repository root). `./packaging/deploy.sh -v
<version>` runs `packaging/docker-compose.yml`: migrates the database once (service `migrate`), recreates the 3 app
replicas `tc-vibe-coding-1..3` (`.env`, shared `data/` volume, one `logs/` volume each, no published port), waits until
each answers `/_stcore/health`, then recreates nginx (`packaging/nginx.conf`: sticky `ip_hash`, WebSocket) - the ONLY
published port (80, `PORT=` to change). `build.sh ... --deploy` runs `deploy.sh` right after the build. `build.sh`
writes `packaging/RELEASE` (version, branch, commit, built_at; git-ignored), `deploy.sh` adds `deployed_version` /
`deployed_at` once the replicas are healthy.
`.dockerignore` keeps `.env`, `.venv`, `data/`, `logs/` and `.git` out of the image. `run.ps1` stays the launcher on a developer PC.

## Configuration
- `.env` (created from `.env.example`, git-ignored): `APP_NAME`, `APP_ENV`, `APP_LOG_LEVEL`, `APP_DATA_DIR`, `APP_PORT`,
  and the database: `POSTGRES_IP`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (empty = local
  SQLite file `data/app.db`). Never commit the password. `APP_SESSION_HOURS` (default 12) = how long a login
  survives page reloads. `APP_MASTER_PASSWORD` = first password of the master account `u-master` (created at start
  when set; never reset afterwards). Volume caps: `APP_DB_WARN_ROWS`, `APP_EXCEL_MAX_ROWS`, `APP_TABLE_MAX_ROWS`,
  `APP_SELECT_MAX_ROWS`, `APP_EDIT_MAX_ROWS`, `APP_CHART_MAX_POINTS`, `APP_CHART_MAX_CATEGORIES`
  (`backend/core/config.py`).
- Read settings with `get_settings()` (`backend/core/config.py`). New settings go there with a default.
- Streamlit options: `.streamlit/config.toml`.

## Runtime folders (git-ignored)
- `data/<feature_key>/` - files written by features (`data/app.db` when no PostgreSQL is configured).
- `logs/app.log` - application log (see 09).
