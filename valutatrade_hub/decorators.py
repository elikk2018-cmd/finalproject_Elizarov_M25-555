"""Enhanced decorators for comprehensive action tracking."""
import functools
import inspect
import logging
import time
from typing import Any, Callable

from .core.session import session_manager

# Get logger for this module
logger = logging.getLogger(__name__)


class LogContext:
    """Context manager for detailed operation logging."""

    def __init__(self, operation: str, user_context: bool = True, **kwargs):
        self.operation = operation.upper()
        self.user_context = user_context
        self.context = kwargs
        self.start_time = None
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        self.start_time = time.time()

        # Build log data - avoid reserved field names
        log_data = {
            'operation': self.operation,
            'status': 'STARTED',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            **self.context
        }

        # Add user context if available and requested
        if self.user_context and session_manager.is_authenticated:
            user = session_manager.current_user
            log_data.update({
                'user_id': user.user_id,
                'username': user.username,
            })

        self.logger.info("Operation started: %s", self.operation, extra=log_data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time

        log_data = {
            'operation': self.operation,
            'execution_time': f"{execution_time:.3f}s",
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        if exc_type is None:
            log_data['status'] = 'COMPLETED'
            self.logger.info("Operation completed: %s", self.operation, extra=log_data)
        else:
            log_data.update({
                'status': 'FAILED',
                'error_type': exc_type.__name__,
                'error_message': str(exc_val),
            })
            self.logger.error("Operation failed: %s", self.operation, extra=log_data)


def log_action(operation: str = None, verbose: bool = False, track_performance: bool = True):
    """
    Enhanced decorator for logging user actions with context.

    Args:
        operation: Custom operation name (defaults to function name)
        verbose: Include detailed context in logs
        track_performance: Log execution time
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get user info
            username = "anonymous"
            user_id = None
            if session_manager.is_authenticated:
                username = session_manager.current_user.username
                user_id = session_manager.current_user.user_id

            # Prepare context - avoid reserved field names like 'module'
            context = {
                'username': username,
                'user_id': user_id,
                'function_name': func.__name__,
                'function_module': func.__module__,
            }

            if verbose:
                context.update({
                    'args_preview': str(args)[:200],
                    'kwargs_keys': list(kwargs.keys()),
                })

            # Log start
            start_time = time.time()
            logger.info("Action started: %s", op_name, extra={'operation': op_name, 'status': 'STARTED', **context})

            try:
                # Execute function
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Log success
                success_context = {
                    'operation': op_name,
                    'status': 'SUCCESS',
                    'execution_time': f"{execution_time:.3f}s",
                    **context
                }

                if verbose and result is not None:
                    success_context['result_type'] = type(result).__name__
                    success_context['result_preview'] = str(result)[:500]

                logger.info("Action completed: %s", op_name, extra=success_context)
                return result

            except Exception as e:
                execution_time = time.time() - start_time

                # Log error
                error_context = {
                    'operation': op_name,
                    'status': 'ERROR',
                    'error_type': e.__class__.__name__,
                    'error_message': str(e),
                    'execution_time': f"{execution_time:.3f}s",
                    **context
                }

                logger.error("Action failed: %s", op_name, extra=error_context)
                raise

        return wrapper
    return decorator


def validate_currency(currency_param: str = 'currency'):
    """
    Decorator to validate currency code before function execution.

    Args:
        currency_param: Name of the parameter containing currency code
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from .core.currencies import get_currency
            from .core.exceptions import CurrencyNotFoundError

            # Find currency parameter using inspect instead of functools.signature
            try:
                # Get function signature
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                currency_code = bound_args.arguments.get(currency_param)
                if currency_code:
                    # Validate currency exists
                    get_currency(currency_code.upper())
            except CurrencyNotFoundError as e:
                logger.warning("Currency validation failed", extra={
                    'currency': currency_code,
                    'operation': func.__name__,
                    'error_msg': str(e)
                })
                raise
            except Exception:
                # If signature binding fails, try to get from kwargs directly
                currency_code = kwargs.get(currency_param)
                if currency_code:
                    try:
                        get_currency(currency_code.upper())
                    except CurrencyNotFoundError as e:
                        logger.warning("Currency validation failed", extra={
                            'currency': currency_code,
                            'operation': func.__name__,
                            'error_msg': str(e)
                        })
                        raise

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_authentication(func: Callable) -> Callable:
    """Decorator to require user authentication for function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not session_manager.is_authenticated:
            from .core.exceptions import AuthenticationError
            logger.warning("Authentication required but user not logged in", extra={
                'operation': func.__name__,
                'func_module': func.__module__
            })
            raise AuthenticationError("Требуется аутентификация")

        user = session_manager.current_user
        logger.debug("User authenticated", extra={
            'user_id': user.user_id,
            'username': user.username,
            'operation': func.__name__
        })

        return func(*args, **kwargs)
    return wrapper
