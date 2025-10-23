"""Session management for user authentication state."""
from typing import Optional
from .models import User


class SessionManager:
    """Manages user session state."""
    
    def __init__(self):
        self._current_user: Optional[User] = None
    
    @property
    def current_user(self) -> Optional[User]:
        return self._current_user
    
    @property
    def is_authenticated(self) -> bool:
        return self._current_user is not None
    
    def login(self, user: User):
        """Set current user as logged in."""
        self._current_user = user
    
    def logout(self):
        """Clear current user session."""
        self._current_user = None
    
    def require_auth(self) -> User:
        """Get current user or raise error if not authenticated."""
        if not self._current_user:
            raise PermissionError("Сначала выполните login")
        return self._current_user


# Global session instance
session_manager = SessionManager()
