import math
import threading
import time
from typing import Union


def _validate_positive_number(val: Union[int, float], name: str, integer_only: bool = False) -> None:
    if isinstance(val, bool):
        raise ValueError(f"{name} must not be a boolean")
    if not isinstance(val, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if integer_only and not isinstance(val, int):
        raise ValueError(f"{name} must be an integer")
    if math.isnan(val) or math.isinf(val):
        raise ValueError(f"{name} must be a finite number")
    if val <= 0:
        raise ValueError(f"{name} must be greater than 0")


class TokenBucket:
    """Thread-safe Token Bucket rate limiter."""

    def __init__(self, capacity: int, refill_rate_per_sec: float) -> None:
        _validate_positive_number(capacity, "capacity", integer_only=True)
        _validate_positive_number(refill_rate_per_sec, "refill_rate_per_sec", integer_only=False)

        self._capacity: float = float(capacity)
        self._refill_rate: float = float(refill_rate_per_sec)
        self._tokens: float = float(capacity)
        self._last_refill_time: float = time.monotonic()
        self._lock: threading.Lock = threading.Lock()

    def _refill_locked(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill_time
        if elapsed > 0:
            refill_amount = elapsed * self._refill_rate
            self._tokens = min(self._capacity, self._tokens + refill_amount)
            self._last_refill_time = now

    def consume(self, tokens: int = 1) -> bool:
        _validate_positive_number(tokens, "tokens", integer_only=True)
        with self._lock:
            self._refill_locked()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def get_available_tokens(self) -> float:
        with self._lock:
            self._refill_locked()
            return self._tokens
