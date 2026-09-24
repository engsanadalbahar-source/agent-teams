import math
import threading
import time


class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float) -> None:
        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, (int, float))
            or math.isnan(capacity)
            or math.isinf(capacity)
            or capacity <= 0
        ):
            raise ValueError(f"Invalid capacity: {capacity}")

        if (
            isinstance(refill_rate_per_sec, bool)
            or not isinstance(refill_rate_per_sec, (int, float))
            or math.isnan(refill_rate_per_sec)
            or math.isinf(refill_rate_per_sec)
            or refill_rate_per_sec <= 0
        ):
            raise ValueError(f"Invalid refill rate: {refill_rate_per_sec}")

        self.capacity: float = float(capacity)
        self.refill_rate_per_sec: float = float(refill_rate_per_sec)
        self.tokens: float = float(capacity)
        self.last_refill: float = time.monotonic()
        self._lock: threading.Lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_sec)
            self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        if (
            isinstance(tokens, bool)
            or not isinstance(tokens, (int, float))
            or math.isnan(tokens)
            or math.isinf(tokens)
            or tokens <= 0
        ):
            raise ValueError(f"Invalid tokens: {tokens}")

        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= float(tokens)
                return True
            return False

    def get_available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self.tokens
