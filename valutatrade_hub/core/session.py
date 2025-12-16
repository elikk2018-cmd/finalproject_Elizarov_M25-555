"""In-memory session manager with file persistence."""

from __future__ import annotations

import json
from pathlib import Path


class SessionUser:
    """Current user in session."""

    def __init__(self, user_id: int, username: str) -> None:
        self.user_id = user_id
        self.username = username


class SessionManager:
    """Session manager with file persistence."""

    def __init__(self) -> None:
        self._current_user: SessionUser | None = None
        self._session_file = Path("data/.session.json")
        self._load_session()

    @property
    def is_authenticated(self) -> bool:
        """Return True if user is logged in."""
        if self._current_user is None:
            self._load_session()
        return self._current_user is not None

    @property
    def current_user(self) -> SessionUser | None:
        """Return current logged-in user (or None)."""
        if self._current_user is None:
            self._load_session()
        return self._current_user

    def login(self, user_id: int, username: str) -> None:
        """Set current user and save to file."""
        self._current_user = SessionUser(user_id=user_id, username=username)
        self._save_session()

    def logout(self) -> None:
        """Clear session and remove file."""
        self._current_user = None
        if self._session_file.exists():
            self._session_file.unlink()

    def _load_session(self) -> None:
        """Load session from file if exists."""
        if not self._session_file.exists():
            return
        try:
            with open(self._session_file, encoding="utf-8") as f:
                data = json.load(f)
            self._current_user = SessionUser(
                user_id=int(data["user_id"]),
                username=str(data["username"]),
            )
        except Exception:
            self._current_user = None

    def _save_session(self) -> None:
        """Save session to file."""
        if self._current_user is None:
            return
        self._session_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._session_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "user_id": self._current_user.user_id,
                        "username": self._current_user.username,
                    },
                    f,
                    ensure_ascii=False,
                )
        except Exception:
            pass


session_manager = SessionManager()
