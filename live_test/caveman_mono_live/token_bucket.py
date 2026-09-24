import math
import threading
import time


def _validate_positive_number(val, name: str) -> None:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(f"{name} must be a non-boolean number")
    if math.isnan(val) or math.isinf(val):
        raise ValueError(f"{name} cannot be NaN or Inf")
    if val <= 0:
        raise ValueError(f"{name} must be greater than zero")


class TokenBucket:
    """Thread-safe Token Bucket rate limiter."""

    def __init__(self, capacity: int, refill_rate_per_sec: float):
        _validate_positive_number(capacity, "capacity")
        _validate_positive_number(refill_rate_per_sec, "refill_rate_per_sec")

        self.capacity = float(capacity)
        self.refill_rate_per_sec = float(refill_rate_per_sec)
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate_per_sec)
            self._last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        _validate_positive_number(tokens, "tokens")
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def get_available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens
