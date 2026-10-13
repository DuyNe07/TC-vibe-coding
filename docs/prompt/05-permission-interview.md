# TASK: Set up who may open which feature / screen (Prompt 5 - permissions, by questions and answers)

You help an administrator (usually NOT a programmer) decide and apply the permissions of the app: user accounts, user
groups, and which features / screens each of them may open. You ask in simple Vietnamese, summarise, get a "đồng ý",
then apply it. You never change application code here.

## 1. What the app already does (read, do not re-implement)
- Login is required. The built-in administrator `u-admin` (first password `u-admin`) can open everything and manage users.
- Rights are given per app (= feature). Permission keys: `<feature_key>` = the whole app (also screens added later);
  `<feature_key>/<page_slug>` = one screen (landing page without slug: `<feature_key>/main`). A user's rights = personal
  keys + keys of ALL their groups (union).
- The menu, Home and URLs only show what the user may open; the gateway refuses the rest. Administrators manage
  everything on the page "Người dùng & phân quyền" (`/admin`). Code: `backend/core/access.py` (`AccessManager`,
  `User`, `UserGroup`), `backend/core/current_user.py`. Rules: `docs/rules/02-backend-architecture.md` ("Users and
  permissions").
- NOT available (never promise): login with Windows / Microsoft accounts, rights per button or per data row,
  time-limited rights, e-mail invitations. A rule like "Sales chỉ sửa yêu cầu của mình" or "xưởng S1 chỉ thấy dữ liệu
  S1" is a BUSINESS rule of a feature: write it down as a request for `docs/prompt/01-business-analysis.md`.

## 2. Hard rules
1. Do not edit any file under `backend/`, `frontend/`, `tests/`, `scripts/`; do not create `.gate-unlock`.
2. Never show or write a password in a file. Initial passwords are typed by the user in the chat or on `/admin`; tell
   them to make each person change it on first use (the admin sets a new one on `/admin`).
3. Never delete or demote `u-admin`. Never delete existing users or groups unless the user explicitly asks for that one.
4. Questions are about the organisation only (who, which group, which screen), never about code.

## 3. Step 1 - Look first (no questions yet)
1. List the features and their screens: for each `frontend/features/<key>/manifest.py` read `FEATURE.title`,
   `FEATURE.pages` and, for each page class, `title`, `slug` and `menu_group`. Build the catalogue
   `key -> "Tên chức năng › [Nhóm con] Tên màn hình"` (landing page key = `<key>/<slug or "main">`).
2. Read each `docs/business/<key>.md` section 2 "Actors" and section 8 "Screens" to know which user groups use which
   screen.
3. Read the current accounts (read only):
   ```
   .venv/Scripts/python.exe -c "from backend.core.access import AccessManager as A; a=A(); print([(u.username,u.full_name,u.is_admin,u.group_ids,u.permissions) for u in a.list_users()]); print([(g.id,g.name,g.permissions) for g in a.list_groups()])"
   ```
   (macOS/Linux: `.venv/bin/python`). It uses the database configured in `.env` (`POSTGRES_*`).

## 4. Step 2 - ONE round of questions -> STOP
In simple Vietnamese, numbered, each with the proposed default marked `(đề xuất)` built from section 2 / 8 of the
business documents. Show the catalogue of features / screens as a short list first. Ask:
1. **Nhóm người dùng** cần tạo (ví dụ "Sales", "Xưởng S1", "Phòng SO", "Kế toán") - đề xuất từ tài liệu nghiệp vụ.
2. **Mỗi nhóm được mở chức năng / màn hình nào** - đề xuất dạng bảng: nhóm | được mở. Nhắc: chọn cả chức năng thì thấy mọi
   màn hình, kể cả màn hình thêm sau này; chọn từng màn hình thì chỉ thấy đúng các màn đó.
3. **Danh sách người dùng**: tên đăng nhập (không dấu, không khoảng trắng), họ tên, thuộc nhóm nào, có cần thêm quyền riêng
   ngoài nhóm không, ai là quản trị viên (toàn quyền).
4. **Mật khẩu ban đầu**: một mật khẩu chung tạm thời cho tất cả (đề xuất) hoặc từng người; nhắc đổi sau lần đầu.
5. Có tài khoản / nhóm nào đang có cần **sửa hoặc khoá** không (khoá = tắt "Đang hoạt động", không xoá).
**STOP** and wait.

## 5. Step 3 - Summary -> "đồng ý" -> STOP
Show one table per group (nhóm | màn hình được mở) and one table of users (tên đăng nhập | họ tên | nhóm | quyền riêng |
quản trị). Mention what will change for existing accounts. Ask the user to answer "đồng ý" or correct it. **STOP**.

## 6. Step 4 - Apply
Apply exactly the confirmed summary with ONE command (write the Python in the `-c` argument, no file), using only
`AccessManager` methods: `save_group(UserGroup(...))`, `set_group_members(group_id, user_ids)`,
`save_user(User(...), password)` (new users need a password; existing users: load with `list_users()`, change fields
with `user.model_copy(update={...})`, `save_user(user)` without password to keep it), and for the rights, once per app:
`set_rights_in_app(app_key, {user_id: {keys}}, {group_id: {keys}})` (keys of that app only; other apps are kept). Re-use existing groups / users by name instead of creating duplicates.
Then run the read command of Step 1 again and check the result matches the summary.
If running Python is not possible (no `.venv`, no database access): give the administrator click-by-click steps on
`/admin` instead (thẻ "Tài khoản": Thêm người dùng; thẻ "Nhóm": Thêm nhóm, chọn thành viên; thẻ "Quyền theo ứng dụng":
chọn ứng dụng, tick màn hình cho từng người / nhóm, bấm "Lưu quyền ...").

## 7. Final report (Vietnamese, no jargon)
- Đã tạo / sửa những nhóm và tài khoản nào, mỗi nhóm thấy gì trên menu.
- Cách đăng nhập: mở app → nhập tên đăng nhập + mật khẩu ban đầu (nhấn F5 không phải đăng nhập lại cho tới khi hết
  phiên hoặc bấm Đăng xuất); quản trị viên đổi mật khẩu cho từng người ở trang phân quyền: gõ địa chỉ
  `<địa chỉ app>/admin` (trang này không có trên menu).
- Việc còn lại: các quy tắc theo dữ liệu (chỉ thấy dữ liệu của mình / của xưởng mình) cần làm theo quy trình nghiệp vụ
  (Prompt 1 → 2) cho chức năng đó.
