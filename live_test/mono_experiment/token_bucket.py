"""Thread-safe Token Bucket implementation for rate limiting."""

import threading
import time
from typing import Callable, Optional


class TokenBucket:
    """A thread-safe Token Bucket implementation.

    Attributes:
        capacity: Maximum number of tokens the bucket can hold.
        refill_rate_per_sec: Number of tokens added to the bucket per second.
    """

    def __init__(
        self,
        capacity: int,
        refill_rate_per_sec: float,
        time_func: Optional[Callable[[], float]] = None,
    ) -> None:
        """Initialize the TokenBucket.

        Args:
            capacity: Maximum token capacity (must be a positive integer).
            refill_rate_per_sec: Tokens added per second (must be positive).
            time_func: Optional time provider returning current time in seconds
                (defaults to time.monotonic). Useful for testing.

        Raises:
            ValueError: If capacity <= 0, refill_rate_per_sec <= 0, or if invalid types are given.
        """
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise ValueError(f"capacity must be a positive integer, got: {capacity!r}")

        if (
            isinstance(refill_rate_per_sec, bool)
            or not isinstance(refill_rate_per_sec, (int, float))
            or refill_rate_per_sec <= 0
        ):
            raise ValueError(
                f"refill_rate_per_sec must be a positive number, got: {refill_rate_per_sec!r}"
            )

        self._capacity = float(capacity)
        self._refill_rate_per_sec = float(refill_rate_per_sec)
        self._time_func = time_func if time_func is not None else time.monotonic

        self._tokens = float(capacity)
        self._last_refill = self._time_func()
        self._lock = threading.Lock()

    @property
    def capacity(self) -> int:
        """Return the maximum token capacity."""
        return int(self._capacity)

    @property
    def refill_rate_per_sec(self) -> float:
        """Return the refill rate in tokens per second."""
        return self._refill_rate_per_sec

    def _refill(self) -> None:
        """Refill tokens based on elapsed time since last refill.

        Must be called while holding self._lock.
        """
        now = self._time_func()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate_per_sec)
            self._last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume the specified number of tokens from the bucket.

        Args:
            tokens: Number of tokens to consume (must be a positive integer).

        Returns:
            True if tokens were consumed, False if not enough tokens available.

        Raises:
            ValueError: If tokens <= 0 or is not an integer.
        """
        if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens <= 0:
            raise ValueError(f"tokens must be a positive integer, got: {tokens!r}")

        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def get_available_tokens(self) -> float:
        """Get the current number of available tokens after refilling.

        Returns:
            Current available tokens as a float.
        """
        with self._lock:
            self._refill()
            return self._tokens
