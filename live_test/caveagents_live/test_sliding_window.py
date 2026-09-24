import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add local directory to path for import
sys.path.insert(0, os.path.dirname(__file__))

from sliding_window_rate_limiter import SlidingWindowLimiter


class TestInputValidation:
    """Validate constructor and method parameter constraints."""

    @pytest.mark.parametrize("limit", [0, -1, -100])
    def test_init_invalid_limit(self, limit: int):
        with pytest.raises(ValueError):
            SlidingWindowLimiter(limit=limit, window_seconds=1.0)

    @pytest.mark.parametrize("window_seconds", [0, 0.0, -0.5, -10])
    def test_init_invalid_window_seconds(self, window_seconds: float):
        with pytest.raises(ValueError):
            SlidingWindowLimiter(limit=10, window_seconds=window_seconds)

    @pytest.mark.parametrize("cost", [0, -1, -5])
    def test_allow_request_invalid_cost(self, cost: int):
        limiter = SlidingWindowLimiter(limit=10, window_seconds=1.0)
        with pytest.raises(ValueError):
            limiter.allow_request(key="test", cost=cost)


class TestBasicConsumptionAndLimitEnforcement:
    """Verify standard consumption, limit bounds, and cost accounting."""

    def test_initial_remaining_limit(self):
        limiter = SlidingWindowLimiter(limit=5, window_seconds=10.0)
        assert limiter.get_remaining_limit("default") == 5

    def test_default_key_parameter(self):
        limiter = SlidingWindowLimiter(limit=3, window_seconds=10.0)
        assert limiter.allow_request() is True
        assert limiter.get_remaining_limit() == 2

    def test_consume_to_exhaustion(self):
        limiter = SlidingWindowLimiter(limit=3, window_seconds=10.0)
        assert limiter.allow_request("client_1") is True
        assert limiter.allow_request("client_1") is True
        assert limiter.allow_request("client_1") is True
        assert limiter.allow_request("client_1") is False
        assert limiter.get_remaining_limit("client_1") == 0

    def test_cost_greater_than_one(self):
        limiter = SlidingWindowLimiter(limit=5, window_seconds=10.0)
        assert limiter.allow_request("client_1", cost=3) is True
        assert limiter.get_remaining_limit("client_1") == 2
        # Request cost exceeding remainder must be rejected and not consumed
        assert limiter.allow_request("client_1", cost=3) is False
        assert limiter.get_remaining_limit("client_1") == 2
        # Exact remainder cost allowed
        assert limiter.allow_request("client_1", cost=2) is True
        assert limiter.get_remaining_limit("client_1") == 0


class TestKeyIsolation:
    """Verify distinct keys maintain completely isolated rate limits."""

    def test_independent_consumption(self):
        limiter = SlidingWindowLimiter(limit=2, window_seconds=10.0)
        assert limiter.allow_request("key_a") is True
        assert limiter.allow_request("key_a") is True
        assert limiter.allow_request("key_a") is False

        # key_b unaffected by key_a exhaustion
        assert limiter.get_remaining_limit("key_b") == 2
        assert limiter.allow_request("key_b") is True
        assert limiter.get_remaining_limit("key_b") == 1

    def test_reset_isolation(self):
        limiter = SlidingWindowLimiter(limit=2, window_seconds=10.0)
        limiter.allow_request("key_a", cost=2)
        limiter.allow_request("key_b", cost=1)

        limiter.reset("key_a")
        assert limiter.get_remaining_limit("key_a") == 2
        assert limiter.get_remaining_limit("key_b") == 1
        assert limiter.allow_request("key_a") is True


class TestWindowExpirationAndSlidingCleanup:
    """Verify rolling window expiration and timestamp cleanup."""

    def test_full_window_expiration(self):
        limiter = SlidingWindowLimiter(limit=2, window_seconds=0.1)
        assert limiter.allow_request("exp_test") is True
        assert limiter.allow_request("exp_test") is True
        assert limiter.allow_request("exp_test") is False

        time.sleep(0.12)
        assert limiter.get_remaining_limit("exp_test") == 2
        assert limiter.allow_request("exp_test") is True

    def test_sliding_window_staggered_expiration(self):
        limiter = SlidingWindowLimiter(limit=2, window_seconds=0.2)
        assert limiter.allow_request("stagger") is True  # t=0
        time.sleep(0.1)
        assert limiter.allow_request("stagger") is True  # t=0.1
        assert limiter.allow_request("stagger") is False # at limit

        # At t=0.22, 1st request expired, 2nd still active
        time.sleep(0.12)
        assert limiter.get_remaining_limit("stagger") == 1
        assert limiter.allow_request("stagger") is True  # allowed (t=0.22)
        assert limiter.allow_request("stagger") is False # at limit again

        # At t=0.35, both previous requests expired, current active
        time.sleep(0.15)
        assert limiter.get_remaining_limit("stagger") == 1


class TestConcurrencySafety:
    """Verify thread-safety under concurrent access."""

    def test_concurrent_requests_exact_limit_enforcement(self):
        limit = 50
        num_threads = 100
        limiter = SlidingWindowLimiter(limit=limit, window_seconds=2.0)

        results = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(limiter.allow_request, "concurrent_key", 1) for _ in range(num_threads)]
            for future in as_completed(futures):
                results.append(future.result())

        allowed_count = sum(1 for r in results if r is True)
        denied_count = sum(1 for r in results if r is False)

        assert allowed_count == limit
        assert denied_count == num_threads - limit
        assert limiter.get_remaining_limit("concurrent_key") == 0

    def test_concurrent_multi_key_isolation(self):
        limit_per_key = 20
        limiter = SlidingWindowLimiter(limit=limit_per_key, window_seconds=2.0)
        keys = [f"worker_{i}" for i in range(5)]

        def worker_task(key):
            allowed = 0
            for _ in range(30):
                if limiter.allow_request(key, 1):
                    allowed += 1
            return key, allowed

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker_task, k) for k in keys]
            for future in as_completed(futures):
                k, allowed = future.result()
                assert allowed == limit_per_key
                assert limiter.get_remaining_limit(k) == 0
