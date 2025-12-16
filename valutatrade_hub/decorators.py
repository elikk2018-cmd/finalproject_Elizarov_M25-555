"""Project decorators (logging actions + auth guard)."""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def log_action(
    action: str | None = None, *, verbose: bool = False
) -> Callable[[F], F]:
    """Log domain actions and re-raise exceptions.

    Args:
        action: Custom action name (BUY/SELL/REGISTER/LOGIN). Defaults to function name.
        verbose: If True, adds extra context (args/kwargs preview).

    Returns:
        Decorated callable.
    """

    def decorator(func: F) -> F:
        act = (action or func.__name__).upper()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from valuatatrade_hub.core.session import session_manager

            started = time.time()
            user = session_manager.current_user

            base_extra: dict[str, Any] = {
                "action": act,
                "result": "STARTED",
                "username": user.username if user else None,
                "user_id": user.user_id if user else None,
            }

            if verbose:
                base_extra["args_preview"] = str(args)[:200]
                base_extra["kwargs_preview"] = str(kwargs)[:200]

            logger.info("action_started", extra=base_extra)

            try:
                result = func(*args, **kwargs)
                logger.info(
                    "action_finished",
                    extra={
                        **base_extra,
                        "result": "OK",
                        "duration_ms": int((time.time() - started) * 1000),
                    },
                )
                return result
            except Exception as e:
                logger.error(
                    "action_failed",
                    extra={
                        **base_extra,
                        "result": "ERROR",
                        "duration_ms": int((time.time() - started) * 1000),
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def require_auth(func: F) -> F:
    """Require active user session for usecases/commands.

    Raises:
        AuthenticationError: If user is not logged in.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from valuatatrade_hub.core.exceptions import AuthenticationError
        from valuatatrade_hub.core.session import session_manager

        if not session_manager.is_authenticated:
            raise AuthenticationError("Сначала выполните login")
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
