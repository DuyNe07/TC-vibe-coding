# 10 - Self-repair loop (never leave the app broken)

When something fails while you implement (Prompt 2) or fix (Prompt 3) a feature, you repair it YOURSELF, inside the
architecture, until the app really works. The user is not a programmer: a broken app is never an acceptable result -
and neither is a "done" that was not verified. Never ask the user to debug, never stop at the first red output.

The running app never rewrites its own code: repairs happen while an AI session is working on the repository.

## The loop
1. **Collect evidence.** The exact command and its full output; the last `ERROR` / `WARNING` lines of `logs/app.log`
   (or the page's log panel); what the user clicked. Never guess from the symptom's name.
2. **Reproduce it** with the cheapest tool that shows the failure: a unit test in
   `backend/features/<key>/tests/` (keep it - it becomes the regression test), `scripts/check.py`, or
   `scripts/doctor.py`.
3. **Diagnose the cause, not the symptom.** Name the layer that is wrong: models / business / builders / repositories /
   dto / services / controllers / pages / manifest / the business document. If an architecture test failed, its name
   points to the rule: read that rule in `docs/rules/` and compare with the reference feature
   `sample_product_import`.
4. **Smallest fix, right layer, inside your feature folders.**
5. **Re-verify**: `python scripts/check.py` -> `ALL CHECKS PASSED`, then `python scripts/doctor.py` ->
   `APP IS HEALTHY`.
6. **Write it down** in `docs/plans/<key>-implementation-plan.md` under a `## Fix log` section:
   `symptom -> cause -> fix -> how it was verified`. This survives an interrupted session.
7. **Same failure 3 times?** Stop editing. Re-read the rule and the reference feature, then try a DIFFERENT approach
   (another layer, a simpler supported mechanism). **After 5 attempts** on the same problem: implement the simplest
   supported behaviour that keeps the business rule intact, write `Giả định (triển khai): ...` in section 10 of the
   document, and say it plainly in the final report. Never loop silently forever.

## Allowed repairs
- everything inside `backend/features/<key>/` and `frontend/features/<key>/` (including new unit tests);
- the plan (`docs/plans/<key>-*.md`) and, in the business document, section 8 UI block, sections 10-11 and `Status`;
- deleting the scaffold leftovers (`ping`).

## Forbidden "repairs" (they hide the problem instead of fixing it)
- editing, deleting, skipping or weakening anything in `tests/`; adding `# noqa`, `pytest.skip`, `xfail`, or ignores in
  `pyproject.toml`;
- `except: pass`, swallowing an exception, returning empty/fake data when something failed, wrapping a whole page in
  `try/except` just to hide an error box;
- removing a validation, a `BR-xx`, a column, a screen element or a use case to make a check pass;
- touching `backend/core/`, `backend/shared/`, `frontend/core/`, `frontend/app.py`, `frontend/home/`, `scripts/`,
  `tests/`, `run.ps1`, `requirements.txt`, `.streamlit/`, `conftest.py`, `pyproject.toml`, or another feature;
- adding a library, replacing the gateway or the base classes, adding an API/second process/second launcher;
- deleting or resetting `data/<key>/` (that is the user's data) to make an error disappear;
- reporting success without showing both `ALL CHECKS PASSED` and `APP IS HEALTHY`.

If the real cause is in the framework (`backend/core`, `backend/shared`, `frontend/core`), do NOT change it on your
own: say it to the user in one Vietnamese sentence, ask permission, and only with their "yes" fix it AND add a test in
`tests/core/`.

## Symptom -> first thing to check
| Symptom | Look here first |
|---|---|
| ruff / formatting errors | `python scripts/check.py --fix` |
| an architecture test fails | its name names the rule: read `docs/rules/`, compare with the reference feature. Fix YOUR code, never the test |
| a unit test fails | is the expectation the document's? If the document is silent, fix the code and record the assumption |
| `test_pages_render` fails | the page calls a use case that raises when there is no data, or an input has no default: use `empty_state`, put actions inside `if st.button(...)` |
| the app does not start | the tail printed by `doctor.py`: import error, missing package (`pip install -r requirements.txt`), port busy |
| "chức năng đang lỗi" on Home | the feature's `manifest.py` (import error, a page not inheriting `BasePage`, duplicate `slug`) |
| an error box in the UI | the page's log panel or `logs/app.log`: find the `AppError` / traceback, then reproduce it in a unit test |
| wrong numbers | the calculation must be in `business/` with `Decimal`; check units and rounding against the `BR-xx` |
| old saved data now fails | models use `extra="forbid"`: new fields need defaults, removed/renamed fields need a conversion in the repository. Never delete `data/` |
| `DuplicateWidgetID` | every widget needs `key=self.key("...")` |
| the page reloads endlessly / is slow | do not call a use case on every rerun; put heavy work behind a button |
| an uploaded file is refused | the extension/size limits in `constants.py` and `UploadedFileDTO.ensure_valid(...)` |

## Definition of "it works"
Both outputs must be in your final report:
1. `python scripts/check.py` -> `ALL CHECKS PASSED` (lint + architecture + unit + page render tests)
2. `python scripts/doctor.py` -> `APP IS HEALTHY` (checks + every feature loads + the app really answers)

With a browser tool available, also walk through every `AC-xx` of the document. If something still cannot be finished,
implement everything else, make the missing part show a clear Vietnamese message, and say exactly what remains and why.
