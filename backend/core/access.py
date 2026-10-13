"""Users, user groups and their permissions (framework level, stored in the database).

Effective permissions of a user = personal permissions + permissions of every group the user belongs to (union).
``is_admin`` users may open everything and manage users. The built-in administrator ``u-admin`` is created on first
start (password ``u-admin``: change it on the admin page) and can not be deleted or lose its admin right.

The UI uses ``AccessManager`` (login + the admin page); permission keys are described in ``current_user.py``.
A login is also a ``LoginSession``: the browser keeps its random token in a cookie, so a page reload (F5) logs the
user back in until it expires (``APP_SESSION_HOURS``), the user logs out, or the account is deactivated.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Any

from pydantic import Field

from backend.core.base import BaseEntity, SqlRepository, utc_now
from backend.core.config import get_settings
from backend.core.current_user import CurrentUser, get_current_user, in_app
from backend.core.exceptions import ConflictError, InvalidInputError, PermissionDeniedError
from backend.core.logger import get_logger

ADMIN_USERNAME = "u-admin"
ADMIN_DEFAULT_PASSWORD = "u-admin"
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, digest = stored.split("$")
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), **_SCRYPT)
    except ValueError:
        return False
    return hmac.compare_digest(actual.hex(), digest)


class User(BaseEntity):
    username: str = Field(min_length=1, max_length=50)
    full_name: str = Field(default="", max_length=100)
    password_hash: str = ""
    is_admin: bool = False
    active: bool = True
    group_ids: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class UserGroup(BaseEntity):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=300)
    permissions: list[str] = Field(default_factory=list)


class LoginSession(BaseEntity):
    token_hash: str  # sha256 of the cookie token (the token itself is never stored)
    username: str
    expires_at: datetime


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class UserRepository(SqlRepository[User]):
    table_name = "core__user"

    def by_username(self, username: str) -> User | None:
        needle = username.strip().lower()
        return self.find_one(lambda u: u.username.lower() == needle)


class UserGroupRepository(SqlRepository[UserGroup]):
    table_name = "core__user_group"


class LoginSessionRepository(SqlRepository[LoginSession]):
    table_name = "core__session"


class AccessManager:
    """Login, effective permissions and user/group administration (admin only)."""

    def __init__(
        self,
        users: UserRepository | None = None,
        groups: UserGroupRepository | None = None,
        sessions: LoginSessionRepository | None = None,
    ) -> None:
        self.users = users or UserRepository()
        self.groups = groups or UserGroupRepository()
        self.sessions = sessions or LoginSessionRepository()
        self.logger = get_logger(__name__)

    # ---- login ----
    def ensure_admin(self) -> None:
        """Create the built-in administrator when it does not exist yet."""
        if self.users.by_username(ADMIN_USERNAME) is None:
            self.users.add(
                User(username=ADMIN_USERNAME, full_name="Quản trị hệ thống", is_admin=True,
                     password_hash=hash_password(ADMIN_DEFAULT_PASSWORD))
            )  # fmt: skip
            self.logger.info("Built-in administrator %s created", ADMIN_USERNAME)

    def authenticate(self, username: str, password: str) -> CurrentUser | None:
        user = self.users.by_username(username)
        if user is None or not user.active or not verify_password(password, user.password_hash):
            self.logger.warning("Login refused for %r", username)
            return None
        self.logger.info("User %s logged in", user.username)
        return self._session_of(user)

    def refresh(self, username: str) -> CurrentUser | None:
        """Current rights of a logged-in user (None when deleted or deactivated meanwhile)."""
        user = self.users.by_username(username)
        return self._session_of(user) if user and user.active else None

    # ---- sessions (stay logged in after a page reload) ----
    def start_session(self, username: str) -> str:
        """New session for a logged-in user; returns the token the browser keeps in a cookie."""
        now = utc_now()
        for stale in self.sessions.find(lambda s: s.expires_at <= now):
            self.sessions.delete(stale.id)
        token = secrets.token_urlsafe(32)
        expires = now + timedelta(hours=get_settings().session_hours)
        self.sessions.add(LoginSession(token_hash=_token_hash(token), username=username, expires_at=expires))
        return token

    def resume(self, token: str) -> CurrentUser | None:
        """The user of a valid session token (None when unknown, expired, or the user is deactivated)."""
        digest = _token_hash(token)
        session = self.sessions.find_one(lambda s: hmac.compare_digest(s.token_hash, digest))
        if session is None or session.expires_at <= utc_now():
            return None
        return self.refresh(session.username)

    def end_session(self, token: str) -> None:
        digest = _token_hash(token)
        for session in self.sessions.find(lambda s: s.token_hash == digest):
            self.sessions.delete(session.id)

    def _session_of(self, user: User) -> CurrentUser:
        groups = {g.id: g for g in self.groups.list_all()}
        permissions = set(user.permissions)
        for group_id in user.group_ids:
            if group_id in groups:
                permissions.update(groups[group_id].permissions)
        return CurrentUser(user.username, user.full_name, user.is_admin, frozenset(permissions))

    # ---- administration ----
    def list_users(self) -> list[User]:
        return sorted(self.users.list_all(), key=lambda u: u.username.lower())

    def list_groups(self) -> list[UserGroup]:
        return sorted(self.groups.list_all(), key=lambda g: g.name.lower())

    def save_user(self, user: User, new_password: str = "") -> User:
        self._require_admin()
        other = self.users.by_username(user.username)
        if other is not None and other.id != user.id:
            raise ConflictError(f"Username '{user.username}' already exists.")
        stored = self.users.get(user.id)
        if stored is not None and stored.username == ADMIN_USERNAME:
            user.username, user.is_admin, user.active = ADMIN_USERNAME, True, True  # built-in admin stays admin
        if new_password:
            user.password_hash = hash_password(new_password)
        if not user.password_hash:
            raise InvalidInputError("A password is required for a new user.")
        self.logger.info("User %s saved (admin=%s, groups=%s)", user.username, user.is_admin, len(user.group_ids))
        return self.users.save(user)

    def delete_user(self, user_id: str) -> None:
        self._require_admin()
        if self.users.get_or_raise(user_id).username == ADMIN_USERNAME:
            raise ConflictError(f"The built-in administrator '{ADMIN_USERNAME}' can not be deleted.")
        self.users.delete(user_id)
        self.logger.info("User %s deleted", user_id)

    def save_group(self, group: UserGroup) -> UserGroup:
        self._require_admin()
        self.logger.info("Group %s saved (%s permissions)", group.name, len(group.permissions))
        return self.groups.save(group)

    def set_group_members(self, group_id: str, user_ids: set[str]) -> None:
        """Make exactly ``user_ids`` members of the group."""
        self._require_admin()
        changed = [
            u.model_copy(update={"group_ids": [g for g in u.group_ids if g != group_id] + ([group_id] if u.id in user_ids else [])})
            for u in self.users.list_all()
            if (u.id in user_ids) != (group_id in u.group_ids)
        ]  # fmt: skip
        self.users.save_many(changed)
        self.logger.info("Group %s: %s members, %s users changed", group_id, len(user_ids), len(changed))

    def set_rights_in_app(self, app_key: str, users: dict[str, set[str]], groups: dict[str, set[str]]) -> int:
        """Replace the rights in ONE app (``app_key`` = whole app, ``page_permission(...)`` = one page) of the given
        user / group ids. Their rights in other apps are kept. Returns how many users + groups changed."""
        self._require_admin()
        wrong = sorted(p for rights in (*users.values(), *groups.values()) for p in rights if not in_app(p, app_key))
        if wrong:
            raise InvalidInputError(f"Permissions {wrong} do not belong to app '{app_key}'.")

        def changed(items: list[Any], wanted: dict[str, set[str]]) -> list[Any]:
            out = []
            for item in items:
                if item.id not in wanted:
                    continue
                permissions = [p for p in item.permissions if not in_app(p, app_key)] + sorted(wanted[item.id])
                if set(permissions) != set(item.permissions):
                    out.append(item.model_copy(update={"permissions": permissions}))
            return out

        changed_users, changed_groups = changed(self.users.list_all(), users), changed(self.groups.list_all(), groups)
        if changed_users:
            self.users.save_many(changed_users)
        if changed_groups:
            self.groups.save_many(changed_groups)
        self.logger.info("Rights in %s: %s users, %s groups changed", app_key, len(changed_users), len(changed_groups))
        return len(changed_users) + len(changed_groups)

    def delete_group(self, group_id: str) -> None:
        self._require_admin()
        self.groups.delete(group_id)  # users keep the stale id; it is ignored by _session_of
        self.logger.info("Group %s deleted", group_id)

    @staticmethod
    def _require_admin() -> None:
        user = get_current_user()
        if user is not None and not user.is_admin:
            raise PermissionDeniedError("Only administrators can manage users and groups.")
