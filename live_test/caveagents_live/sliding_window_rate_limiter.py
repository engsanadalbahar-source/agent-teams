import collections
import math
import threading
import time
from typing import Deque, Dict, Tuple


class SlidingWindowLimiter:
    """Thread-safe sliding window rate limiter."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        if isinstance(limit, bool) or not isinstance(limit, (int, float)):
            raise ValueError("limit must be a positive integer")
        if math.isnan(limit) or math.isinf(limit):
            raise ValueError("limit cannot be NaN or Inf")
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if not isinstance(limit, int) and not limit.is_integer():
            raise ValueError("limit must be an integer")
        self.limit = int(limit)

        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a positive number")
        if math.isnan(window_seconds) or math.isinf(window_seconds):
            raise ValueError("window_seconds cannot be NaN or Inf")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than 0")
        self.window_seconds = float(window_seconds)

        self._lock = threading.Lock()
        self._history: Dict[str, Deque[Tuple[float, int]]] = collections.defaultdict(collections.deque)
        self._usage: Dict[str, int] = collections.defaultdict(int)

    def _cleanup(self, key: str, now: float) -> None:
        queue = self._history.get(key)
        if not queue:
            return
        cutoff = now - self.window_seconds
        while queue and queue[0][0] <= cutoff:
            _, old_cost = queue.popleft()
            self._usage[key] -= old_cost
        if not queue:
            self._history.pop(key, None)
            self._usage.pop(key, None)

    def allow_request(self, key: str = "default", cost: int = 1) -> bool:
        if isinstance(cost, bool) or not isinstance(cost, (int, float)):
            raise ValueError("cost must be a positive integer")
        if math.isnan(cost) or math.isinf(cost):
            raise ValueError("cost cannot be NaN or Inf")
        if cost <= 0:
            raise ValueError("cost must be greater than 0")
        if not isinstance(cost, int) and not cost.is_integer():
            raise ValueError("cost must be an integer")
        cost = int(cost)

        with self._lock:
            now = time.monotonic()
            self._cleanup(key, now)

            current_usage = self._usage[key]
            if current_usage + cost <= self.limit:
                self._history[key].append((now, cost))
                self._usage[key] = current_usage + cost
                return True
            return False

    def get_remaining_limit(self, key: str = "default") -> int:
        with self._lock:
            now = time.monotonic()
            self._cleanup(key, now)
            current_usage = self._usage.get(key, 0)
            return max(0, self.limit - current_usage)

    def reset(self, key: str = "default") -> None:
        with self._lock:
            self._history.pop(key, None)
            self._usage.pop(key, None)
