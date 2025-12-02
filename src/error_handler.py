
import logging
import time
from functools import wraps
from typing import Callable, Any
import requests

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when data validation fails"""
    pass


class APIError(Exception):
    """Raised when API calls fail"""
    pass


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0, 
                     exceptions: tuple = (Exception,)):
    """
    Decorator to retry a function on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator


def validate_candle_data(candles: list) -> bool:
    """
    Validate candle data for completeness and sanity
    
    Args:
        candles: List of candle dictionaries
    
    Returns:
        True if valid, raises DataValidationError otherwise
    """
    if not candles:
        raise DataValidationError("Empty candle list")
    
    required_keys = {'t', 'o', 'h', 'l', 'c', 'v'}
    
    for i, candle in enumerate(candles):
        # Check required keys
        missing_keys = required_keys - set(candle.keys())
        if missing_keys:
            raise DataValidationError(f"Candle {i} missing keys: {missing_keys}")
        
        # Check for None values in critical fields
        if candle['c'] is None:
            raise DataValidationError(f"Candle {i} has None close price")
        
        # Validate OHLC relationship
        o, h, l, c = candle['o'], candle['h'], candle['l'], candle['c']
        
        if o is not None and h is not None and l is not None:
            if not (l <= o <= h and l <= c <= h):
                logger.warning(
                    f"Candle {i} has invalid OHLC: O={o}, H={h}, L={l}, C={c}"
                )
        
        # Check for negative values
        for key in ['o', 'h', 'l', 'c', 'v']:
            val = candle[key]
            if val is not None and val < 0:
                raise DataValidationError(f"Candle {i} has negative {key}: {val}")
        
        # Check for extreme price changes (possible data error)
        if i > 0:
            prev_close = candles[i-1]['c']
            if prev_close and c:
                change_pct = abs(c - prev_close) / prev_close
                if change_pct > 0.5:  # 50% change - likely an error
                    logger.warning(
                        f"Candle {i} has extreme price change: {change_pct*100:.1f}% "
                        f"(from {prev_close} to {c})"
                    )
    
    return True


def validate_symbol(symbol: str) -> bool:
    """Validate stock symbol format"""
    if not symbol or not isinstance(symbol, str):
        raise DataValidationError(f"Invalid symbol: {symbol}")
    
    if len(symbol) > 20:
        raise DataValidationError(f"Symbol too long: {symbol}")
    
    return True


def safe_float_convert(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        if value is None or value != value:  # None or NaN
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_convert(value: Any, default: int = 0) -> int:
    """Safely convert value to int"""
    try:
        if value is None or value != value:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def handle_api_errors(response: requests.Response) -> dict:
    """
    Handle API response errors consistently
    
    Args:
        response: requests Response object
    
    Returns:
        Parsed JSON data
    
    Raises:
        APIError: If request failed
    """
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status_code = response.status_code
        
        if status_code == 429:
            raise APIError(f"Rate limit exceeded: {e}")
        elif status_code >= 500:
            raise APIError(f"Server error ({status_code}): {e}")
        elif status_code == 404:
            raise APIError(f"Resource not found: {e}")
        else:
            raise APIError(f"HTTP error ({status_code}): {e}")
    except requests.exceptions.ConnectionError as e:
        raise APIError(f"Connection error: {e}")
    except requests.exceptions.Timeout as e:
        raise APIError(f"Request timeout: {e}")
    except ValueError as e:
        raise APIError(f"Invalid JSON response: {e}")


def log_exception_context(func: Callable) -> Callable:
    """Decorator to log detailed exception context"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(
                f"Exception in {func.__name__}: {e}\n"
                f"Args: {args}\n"
                f"Kwargs: {kwargs}"
            )
            raise
    return wrapper

