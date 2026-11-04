"""Users, user groups and their permissions (framework level, stored in the database).

Effective permissions of a user = personal permissions + permissions of every group the user belongs to (union).
The built-in administrator ``u-admin`` is created on first start (password ``u-admin``: change it on the admin page)
and can not be deleted or lose its admin right.

Master (built-in ``u-master``, created when ``APP_MASTER_PASSWORD`` is set; ``User.is_master`` is derived from the
username, never stored, so the row keeps the format older app versions on the shared database read): above every
administrator. Only the master creates, changes or deletes administrators and ticks their apps; once a master
exists, an administrator opens and manages only the apps the master ticked for them. Without a master,
administrators open everything (previous behaviour).

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
MASTER_USERNAME = "u-master"
BUILTIN_USERNAMES = frozenset({ADMIN_USERNAME, MASTER_USERNAME})
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

    @property
    def is_master(self) -> bool:
        return self.username == MASTER_USERNAME


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

    def purge_expired(self, now: datetime) -> None:
        """Expired sessions are technical leftovers, not business data: the one hard delete of the framework."""
        self.purge_ids([s.id for s in self._stored().values() if s.expires_at <= now])

    def purge_ids(self, ids: list[str]) -> None:
        if ids:
            self._purge(ids)


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
        password = get_settings().master_password
        if password and self.users.by_username(MASTER_USERNAME) is None:  # never resets a password changed later
            self.users.add(
                User(username=MASTER_USERNAME, full_name="Master", is_admin=True,
                     password_hash=hash_password(password))
            )  # fmt: skip
            self.logger.info("Built-in master %s created", MASTER_USERNAME)

    def has_master(self) -> bool:
        return self.users.by_username(MASTER_USERNAME) is not None

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
        self.sessions.purge_expired(now)
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
        # sessions are technical rows, not business data: removed at logout (no delete flag in this table, so
        # app versions that do not know the flag keep reading it)
        self.sessions.purge_ids([s.id for s in self.sessions.find(lambda s: s.token_hash == digest)])

    def _session_of(self, user: User) -> CurrentUser:
        groups = {g.id: g for g in self.groups.list_all()}
        permissions = set(user.permissions)
        for group_id in user.group_ids:
            if group_id in groups:
                permissions.update(groups[group_id].permissions)
        return CurrentUser(
            user.username, user.full_name, user.is_admin or user.is_master, frozenset(permissions),
            is_master=user.is_master, admin_scoped=user.is_admin and not user.is_master and self.has_master(),
        )  # fmt: skip

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
        if user.username.lower() == MASTER_USERNAME and (stored is None or not stored.is_master):
            raise ConflictError(f"The name '{MASTER_USERNAME}' is reserved for the master account.")
        if stored is not None and stored.username in BUILTIN_USERNAMES:
            user.username, user.is_admin, user.active = stored.username, True, True  # built-ins stay admin
        self._require_master_for(stored, user)
        if new_password:
            user.password_hash = hash_password(new_password)
        if not user.password_hash:
            raise InvalidInputError("A password is required for a new user.")
        self.logger.info("User %s saved (admin=%s, groups=%s)", user.username, user.is_admin, len(user.group_ids))
        return self.users.save(user)

    def delete_user(self, user_id: str) -> None:
        self._require_admin()
        target = self.users.get_or_raise(user_id)
        if target.username in BUILTIN_USERNAMES:
            raise ConflictError(f"The built-in account '{target.username}' can not be deleted.")
        self._require_master_for(target, None)
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
        actor = get_current_user()
        if actor is not None and not actor.can_open_feature(app_key):
            raise PermissionDeniedError(f"Administrator '{actor.username}' manages no rights in app '{app_key}'.")
        if actor is not None and not actor.is_master:
            admins = sorted(u.username for u in self.users.list_all() if u.id in users and (u.is_admin or u.is_master))
            if admins:
                raise PermissionDeniedError(f"Only the master account sets the rights of administrators: {admins}.")
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
    def _require_master_for(stored: User | None, new: User | None) -> None:
        """Administrators and the master are managed by the master only (an administrator may still edit their own
        name and password)."""
        actor = get_current_user()
        if actor is None or actor.is_master:
            return
        touches_admin = (stored is not None and (stored.is_admin or stored.is_master)) or (
            new is not None and new.is_admin
        )
        own_profile = (
            stored is not None
            and new is not None
            and stored.username == actor.username
            and new.is_admin == stored.is_admin
        )
        if touches_admin and not own_profile:
            raise PermissionDeniedError("Only the master account can create, change or delete administrators.")

    @staticmethod
    def _require_admin() -> None:
        user = get_current_user()
        if user is not None and not user.is_admin:
            raise PermissionDeniedError("Only administrators can manage users and groups.")
