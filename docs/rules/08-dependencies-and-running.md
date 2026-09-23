# 08 - Dependencies and Running

## Running (users are not programmers: keep this working)
Open PowerShell in the project folder, then:
```
powershell -ExecutionPolicy Bypass -File .\run.ps1                        # normal run
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Port 8600             # other port
powershell -ExecutionPolicy Bypass -File .\run.ps1 -NoBrowser             # do not open the browser
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Reinstall             # force reinstalling packages
```
(`-ExecutionPolicy Bypass` is needed because Windows blocks unsigned scripts by default.)

`run.ps1` steps:
1. Check `.venv`; create it with Python 3.13 if missing (recreate it if it uses another Python version).
2. Install `requirements.txt` only when packages are missing or the file changed (hash stored in `.venv`).
3. Create `.env` from `.env.example` if missing, create `data/` and `logs/`, pick a free port.
4. Start Streamlit (ONE process) and open `http://localhost:<port>/home` as soon as the server answers.
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
   (python-docx, docxtpl), PDF (pypdf), public web pages (requests, lxml - via `backend/shared/web`),
   charts (plotly, streamlit built-ins), validation (pydantic). What the app can do with them:
   `docs/capabilities.md`.
3. After adding one, run `run.ps1` again (it auto-installs) or `.venv/Scripts/python.exe -m pip install -r requirements.txt`.

## Configuration
- `.env` (created from `.env.example`, git-ignored): `APP_NAME`, `APP_ENV`, `APP_LOG_LEVEL`, `APP_DATA_DIR`, `APP_PORT`.
- Read settings with `get_settings()` (`backend/core/config.py`). New settings go there with a default.
- Streamlit options: `.streamlit/config.toml`.

## Runtime folders (git-ignored)
- `data/<feature_key>/` - files written by repositories and features.
- `logs/app.log` - application log (see 09).
