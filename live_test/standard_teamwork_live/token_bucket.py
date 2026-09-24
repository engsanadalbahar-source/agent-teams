import threading
import time


class TokenBucket:
    """A thread-safe Token Bucket rate limiter implementation.

    Attributes:
        capacity: Maximum number of tokens the bucket can hold.
        refill_rate_per_sec: Rate at which tokens are replenished per second.
        tokens: Current number of tokens available in the bucket.
        last_refill_time: Monotonic timestamp of the last token replenishment.
    """

    def __init__(self, capacity: int, refill_rate_per_sec: float) -> None:
        """Initialize the TokenBucket with capacity and refill rate.

        Args:
            capacity: Maximum capacity of tokens (must be > 0).
            refill_rate_per_sec: Replenishment rate in tokens per second (must be > 0).

        Raises:
            ValueError: If capacity <= 0 or refill_rate_per_sec <= 0.
        """
        if capacity <= 0:
            raise ValueError(f"capacity must be greater than 0, got {capacity}")
        if refill_rate_per_sec <= 0:
            raise ValueError(
                f"refill_rate_per_sec must be greater than 0, got {refill_rate_per_sec}"
            )

        self.capacity: float = float(capacity)
        self.refill_rate_per_sec: float = float(refill_rate_per_sec)
        self.tokens: float = float(capacity)
        self.last_refill_time: float = time.monotonic()
        self._lock: threading.Lock = threading.Lock()

    def _refill_locked(self) -> None:
        """Refill tokens based on elapsed monotonic time. Must be called while holding _lock."""
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_sec)
            self.last_refill_time = now

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume the requested number of tokens from the bucket.

        Args:
            tokens: Number of tokens to consume (default is 1, must be > 0).

        Returns:
            True if sufficient tokens were available and deducted, False otherwise.

        Raises:
            ValueError: If tokens <= 0.
        """
        if tokens <= 0:
            raise ValueError(f"tokens to consume must be greater than 0, got {tokens}")

        with self._lock:
            self._refill_locked()
            if self.tokens >= tokens:
                self.tokens -= float(tokens)
                return True
            return False

    def get_available_tokens(self) -> float:
        """Get the current number of available tokens after accounting for elapsed refill time.

        Returns:
            The current available token count as a float.
        """
        with self._lock:
            self._refill_locked()
            return self.tokens
