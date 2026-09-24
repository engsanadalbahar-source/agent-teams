import math
import threading
import time


def _validate_positive_number(val: object, name: str) -> None:
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        raise ValueError(f"{name} must be a number")
    if math.isnan(val) or math.isinf(val) or val <= 0:
        raise ValueError(f"{name} must be > 0 and finite")


class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        _validate_positive_number(capacity, "capacity")
        _validate_positive_number(refill_rate_per_sec, "refill_rate_per_sec")

        self.capacity = float(capacity)
        self.refill_rate_per_sec = float(refill_rate_per_sec)
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_sec)
            self.last_refill_time = now

    def consume(self, tokens: int = 1) -> bool:
        _validate_positive_number(tokens, "tokens")
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= float(tokens)
                return True
            return False

    def get_available_tokens(self) -> float:
        with self.lock:
            self._refill()
            return float(self.tokens)
