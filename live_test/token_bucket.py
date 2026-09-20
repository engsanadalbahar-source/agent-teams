import threading
import time


class TokenBucket:
    """A thread-safe token bucket rate limiter implementation."""

    def __init__(self, capacity: int, refill_rate_per_sec: float):
        if capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {capacity}")
        if refill_rate_per_sec <= 0:
            raise ValueError(f"Refill rate must be positive, got {refill_rate_per_sec}")

        self.capacity: float = float(capacity)
        self.refill_rate_per_sec: float = float(refill_rate_per_sec)
        self.tokens: float = float(capacity)
        self.last_refill_time: float = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Calculate and apply refilled tokens based on elapsed time.

        Must be called while holding self._lock.
        """
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        if elapsed > 0:
            refilled = elapsed * self.refill_rate_per_sec
            self.tokens = min(self.capacity, self.tokens + refilled)
            self.last_refill_time = now

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume the specified number of tokens from the bucket.

        Args:
            tokens: The number of tokens to consume (default 1).

        Returns:
            True if tokens were successfully consumed, False otherwise.

        Raises:
            ValueError: If tokens <= 0.
        """
        if tokens <= 0:
            raise ValueError(f"Tokens to consume must be positive, got {tokens}")

        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_available_tokens(self) -> float:
        """Get the current number of available tokens in the bucket.

        Returns:
            Current available tokens as a float, capped at capacity.
        """
        with self._lock:
            self._refill()
            return self.tokens
