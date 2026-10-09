# TASK: Push the user's work to GitHub on a new branch (Prompt 4, only when they want to send code)

You help a NON-programmer send their work to GitHub so a developer can review it. You ask for what is missing, in
simple Vietnamese, in ONE round of questions, then do everything with git yourself. You never change application code
here: only git operations (branch, commit, push).

## 1. Hard rules
1. Only git commands + reading `git status`. Never edit code, never run the app, never create `.gate-unlock`.
2. **Never push to `main` / `master`** and never use `--force`. Always a new branch.
3. **Never commit secrets or data**: before committing, run `git status --short` and make sure nothing matching
   `.env`, `data/`, `logs/`, `*.pem`, `*.key`, `.gate-unlock`, `*token*`, `*secret*` is staged (they are git-ignored;
   if one appears anyway, stop and tell the user).
4. The token the user gives you: use it ONLY inside the single `git push` command. Never write it into a file, never
   into `.git/config`, never repeat it back in your messages, never `git remote add` with it inside the URL.
5. If a command fails, show the real error in simple Vietnamese and the one thing the user must do (wrong token,
   no permission, repo not found, no network), then stop. Never retry a failed push more than twice.

## 2. Step 1 - Look at the repository first (no questions yet)
Run and read:
```
git rev-parse --is-inside-work-tree
git remote -v
git branch --show-current
git config user.name
git config user.email
git status --short
```
From that you know: is it a git repo, is there already a remote, which branch, who is configured, what changed.
If it is NOT a git repo yet: run `git init` and `git branch -M main` (nothing is pushed yet, this is safe).

## 3. Step 2 - ONE round of questions -> STOP
Ask ONLY what you could not find above. Numbered, in simple Vietnamese, with the proposed default marked
`(đề xuất)`. Example:

1. **Repo GitHub để đẩy lên:** dán địa chỉ dạng `https://github.com/<chủ-repo>/<tên-repo>`
   (nếu `git remote -v` đã có thì ghi: "Tôi thấy repo `<url>` — dùng repo này nhé? (đề xuất)").
2. **Tên nhánh (branch) sẽ tạo:** đề xuất `vibe/<tên-chức-năng>-<ngày-tháng>`, ví dụ `vibe/don-nghi-phep-0910`.
   Tên nhánh chỉ gồm chữ không dấu, số, dấu `-` và `/`.
3. **Tên và email để ghi vào lịch sử code:** ví dụ `Nguyen Van A` và `a.nguyen@congty.vn`
   (nếu `git config` đã có thì chỉ hỏi xác nhận).
4. **Tên đăng nhập GitHub** của bạn.
5. **Mã truy cập (Personal Access Token)** — GitHub **không còn cho dùng mật khẩu** để đẩy code. Cách lấy:
   mở `https://github.com/settings/tokens` → *Generate new token* → chọn **Fine-grained token**, phần *Repository
   access* chọn đúng repo ở câu 1, phần *Permissions* bật **Contents: Read and write**, *Expiration* chọn 7 ngày →
   *Generate* → copy dãy ký tự bắt đầu bằng `github_pat_...` và dán vào đây.
   *(Nếu bạn không muốn dán mã vào chat: trả lời "tôi tự push" — tôi sẽ chuẩn bị mọi thứ và đưa bạn đúng một lệnh để
   tự chạy trong PowerShell.)*
6. **Mô tả ngắn công việc này** (1 câu, tiếng Việt) để ghi vào commit, ví dụ "Thêm chức năng đơn nghỉ phép".

Add this warning in one line: "Mã truy cập sẽ nằm trong nội dung chat này. Hãy dùng token hạn 7 ngày như hướng dẫn,
và sau khi đẩy xong có thể vào GitHub xoá token đó (Settings → Developer settings → Tokens → Delete)."
**STOP** and wait.

## 4. Step 3 - Quality check before sending (tell, do not block)
Run `.venv/Scripts/python.exe scripts/check.py` (macOS/Linux: `.venv/bin/python`).
- Passes: say "Kiểm tra code: đạt" and continue.
- Fails or `.venv` is missing: say in one Vietnamese line that the code currently has an error (or chưa cài môi
  trường), that you will still push it so the developer can look at it, and continue. Do NOT try to fix the code here.

## 5. Step 4 - Commit the user's work, THEN pull the latest code
Commit first so nothing of the user's work can be lost, then merge the newest code from GitHub:
```
git config user.name "<Tên>"
git config user.email "<email>"
git checkout -b <branch>
git add -A
git status --short
git commit -m "<mô tả ngắn>"
echo push > .gate-unlock
git fetch https://<github-user>:<token>@github.com/<chủ-repo>/<tên-repo>.git main
git merge FETCH_HEAD --no-edit
```
Notes:
- `git checkout -b` fails because the branch exists -> use `git checkout <branch>` and continue.
- `git commit` says "nothing to commit" -> there is nothing new of the user's, but still do the pull below.
- If the default branch is not `main`, use its real name (`git remote show origin` after the fetch, or ask nothing and
  try `main` then `master`).
- If this branch already exists on GitHub, fetch that branch too and merge it the same way.
- `.gate-unlock` is needed because the workflow gate otherwise refuses to write code files while resolving conflicts.
  Delete it in Step 6. Never do anything else with it.
- Forbidden here: `git reset --hard`, `git checkout -- .`, `git clean -fd`, `git rebase`, `git push --force` - they
  throw the user's work away.

## 6. Step 5 - Resolve conflicts (if the merge stopped)
`git merge` prints `CONFLICT`: list the files with `git status --short` (`UU` = conflict) and resolve them ONE by ONE,
in simple Vietnamese telling the user which file you are merging. Decision rules:
1. **The user's own feature** (`backend/features/<key>/`, `frontend/features/<key>/`, `docs/business/<key>.md`,
   `docs/plans/<key>-*.md`): keep the user's version -> `git checkout --ours -- <file>`.
2. **Framework / shared files** (`backend/core/`, `backend/shared/`, `frontend/core/`, `frontend/app.py`,
   `frontend/home/`, `scripts/`, `tests/`, `docs/rules/`, `CLAUDE.md`, `run.ps1`, `requirements.txt`,
   `pyproject.toml`, `.streamlit/`): take GitHub's version -> `git checkout --theirs -- <file>`.
3. **A file both sides really changed on purpose** (e.g. `requirements.txt` with a new library on each side, or two
   features added to the same document): open it, keep BOTH changes by hand, delete every `<<<<<<<`, `=======`,
   `>>>>>>>` marker. Never delete the other side's lines just to make it compile.
Then: `git add <file>` for each resolved file, `git commit --no-edit` to close the merge.
After the merge, run `.venv/Scripts/python.exe scripts/check.py` and `.venv/Scripts/python.exe scripts/doctor.py`.
If they now fail because of the merge, repair it following `docs/rules/10-self-repair.md` (smallest fix, only in the
user's feature folders, never by deleting a rule or a test). If after 5 attempts something still fails, push anyway and
say exactly what is broken in the final report - the developer will take it from there.

## 7. Step 6 - Push
```
git push https://<github-user>:<token>@github.com/<chủ-repo>/<tên-repo>.git <branch>
rm .gate-unlock
```
Notes:
- The push is rejected as "non-fast-forward" -> the branch moved on GitHub: fetch it and merge it (Step 4-5), then
  push again. Never `--force`.
- The push URL is used only in that one command; do not save it anywhere.
- If the user answered "tôi tự push": do Steps 4-5 with a plain `git fetch origin main` (it works without a token for a
  public repo; for a private one tell them to run the fetch themselves), then give them exactly one command to paste in
  their PowerShell: `git push https://github.com/<chủ-repo>/<tên-repo>.git <branch>` - Git/Windows will ask for their
  GitHub login (username + token in the password box).
- Always `rm .gate-unlock` at the end, even when the push failed.

## 8. Step 7 - Report (Vietnamese, short)
1. Đã đẩy lên nhánh `<branch>` của repo `<tên-repo>`; số file đã gửi; đã lấy code mới nhất từ GitHub về và gộp vào
   (nói rõ: không có xung đột / đã xử lý xung đột ở những file nào, giữ bên nào).
2. Kết quả `scripts/check.py` và `scripts/doctor.py` sau khi gộp (nếu còn lỗi: ghi rõ lỗi gì).
3. Link để người kiểm tra mở: `https://github.com/<chủ-repo>/<tên-repo>/tree/<branch>`
   và link tạo Pull Request: `https://github.com/<chủ-repo>/<tên-repo>/pull/new/<branch>`.
4. Nhắc một dòng: có thể xoá token trên GitHub nếu không dùng nữa.
5. Lần sau muốn gửi tiếp: dán lại prompt này, tôi sẽ tạo nhánh mới (hoặc đẩy thêm vào nhánh cũ nếu bạn muốn).
