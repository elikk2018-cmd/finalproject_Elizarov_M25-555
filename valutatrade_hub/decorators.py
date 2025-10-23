"""Decorators for logging and action tracking."""
import functools
import time
import os
from typing import Any, Callable
from .core.session import session_manager


def log_action(verbose: bool = False):
    """
    Decorator for logging user actions.
    
    Args:
        verbose: If True, includes additional context in logs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get user info
            username = "anonymous"
            user_id = None
            if session_manager.is_authenticated:
                username = session_manager.current_user.username
                user_id = session_manager.current_user.user_id
            
            # Prepare log data
            start_time = time.time()
            action_name = func.__name__
            
            log_data = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'action': action_name.upper(),
                'username': username,
                'user_id': user_id,
                'result': 'UNKNOWN',
                'execution_time': 0,
            }
            
            # Add context for verbose logging
            if verbose:
                log_data['args'] = str(args)[:100]  # Limit length
                log_data['kwargs'] = str(kwargs)[:100]
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log success
                log_data.update({
                    'result': 'OK',
                    'execution_time': f"{execution_time:.3f}s",
                })
                
                if verbose and result:
                    log_data['result_data'] = str(result)[:200]
                
                _write_log_entry(log_data)
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log error
                log_data.update({
                    'result': 'ERROR',
                    'error_type': e.__class__.__name__,
                    'error_message': str(e),
                    'execution_time': f"{execution_time:.3f}s",
                })
                
                _write_log_entry(log_data)
                raise
        
        return wrapper
    return decorator


def _write_log_entry(log_data: dict):
    """Write log entry to file and console."""
    from .infra.settings import settings
    
    # Format log message
    if settings.get('log_format') == 'json':
        import json
        log_message = json.dumps(log_data, ensure_ascii=False)
    else:
        # Simple format
        log_message = (
            f"{log_data['timestamp']} {log_data['action']} "
            f"user='{log_data['username']}' result={log_data['result']} "
            f"time={log_data['execution_time']}"
        )
        
        if log_data['result'] == 'ERROR':
            log_message += f" error={log_data['error_type']}:{log_data['error_message']}"
    
    # Write to log file
    log_file = settings.get('log_file', 'logs/valutatrade.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    except IOError:
        # Fallback to console if file writing fails
        print(f"LOG: {log_message}")
    
    # Also print to console for important actions
    if log_data['action'] in ['REGISTER', 'LOGIN', 'BUY', 'SELL']:
        print(f"INFO: {log_data['action']} user='{log_data['username']}' result={log_data['result']}")
