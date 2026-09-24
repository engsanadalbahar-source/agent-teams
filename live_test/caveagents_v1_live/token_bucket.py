import math
import threading
import time


class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        if isinstance(capacity, bool) or not isinstance(capacity, (int, float)):
            raise ValueError("capacity must be a positive number")
        if math.isnan(capacity) or math.isinf(capacity) or capacity <= 0:
            raise ValueError("capacity must be positive and finite")

        if isinstance(refill_rate_per_sec, bool) or not isinstance(refill_rate_per_sec, (int, float)):
            raise ValueError("refill_rate_per_sec must be a positive number")
        if math.isnan(refill_rate_per_sec) or math.isinf(refill_rate_per_sec) or refill_rate_per_sec <= 0:
            raise ValueError("refill_rate_per_sec must be positive and finite")

        self.capacity = float(capacity)
        self.refill_rate_per_sec = float(refill_rate_per_sec)
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()
        self._lock = threading.Lock()

    def _refill_locked(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        if elapsed >= 0.001:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_sec)
            self.last_refill_time = now
        elif elapsed < 0:
            self.last_refill_time = now

    def consume(self, tokens: int = 1) -> bool:
        if isinstance(tokens, bool) or not isinstance(tokens, (int, float)):
            raise ValueError("tokens must be a positive number")
        if math.isnan(tokens) or math.isinf(tokens) or tokens <= 0:
            raise ValueError("tokens must be positive and finite")

        with self._lock:
            self._refill_locked()
            if self.tokens >= tokens:
                self.tokens -= float(tokens)
                return True
            return False

    def get_available_tokens(self) -> float:
        with self._lock:
            self._refill_locked()
            return float(self.tokens)
