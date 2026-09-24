import math
import threading
import time


class TokenBucket:
    """Thread-safe Token Bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate_per_sec: float) -> None:
        if not isinstance(capacity, (int, float)) or math.isnan(capacity) or math.isinf(capacity) or capacity <= 0:
            raise ValueError(f"capacity must be a positive finite number, got {capacity}")
        if not isinstance(refill_rate_per_sec, (int, float)) or math.isnan(refill_rate_per_sec) or math.isinf(refill_rate_per_sec) or refill_rate_per_sec <= 0:
            raise ValueError(f"refill_rate_per_sec must be a positive finite number, got {refill_rate_per_sec}")

        self._capacity = float(capacity)
        self._refill_rate = float(refill_rate_per_sec)
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill_locked(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
            self._last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        if not isinstance(tokens, (int, float)) or math.isnan(tokens) or math.isinf(tokens) or tokens <= 0:
            raise ValueError(f"tokens must be a positive finite number, got {tokens}")

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
