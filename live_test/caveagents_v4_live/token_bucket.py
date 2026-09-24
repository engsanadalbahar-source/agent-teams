import math
import threading
import time
from typing import Union


class TokenBucket:
    """Thread-safe Token Bucket rate limiter."""

    def __init__(self, capacity: Union[int, float], refill_rate_per_sec: Union[int, float]) -> None:
        self._validate_positive_finite_number(capacity, "capacity")
        self._validate_positive_finite_number(refill_rate_per_sec, "refill_rate_per_sec")

        self.capacity = float(capacity)
        self.refill_rate_per_sec = float(refill_rate_per_sec)
        self._tokens = float(capacity)
        self._last_refill_time = time.monotonic()
        self._lock = threading.Lock()

    @staticmethod
    def _validate_positive_finite_number(val: object, name: str) -> None:
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ValueError(f"{name} must be numeric, got {type(val).__name__}")
        if not math.isfinite(val) or val <= 0:
            raise ValueError(f"{name} must be a positive finite number, got {val}")

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill_time
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate_per_sec)
            self._last_refill_time = now

    def consume(self, tokens: Union[int, float] = 1) -> bool:
        self._validate_positive_finite_number(tokens, "tokens")
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
