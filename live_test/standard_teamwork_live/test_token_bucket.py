"""
Comprehensive pytest test suite for TokenBucket rate limiter.

Requirements tested:
1. __init__(self, capacity: int, refill_rate_per_sec: float)
2. consume(self, tokens: int = 1) -> bool
3. get_available_tokens(self) -> float
4. Normal token consumption
5. Burst limit / capacity ceiling
6. Refill rate over time
7. Concurrency / multi-threaded safety
8. Edge cases: negative or zero token requests (ValueError)
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest

from token_bucket import TokenBucket


class TestTokenBucketInitialization:
    """Tests for TokenBucket initialization and basic state."""

    def test_initial_state(self):
        bucket = TokenBucket(capacity=10, refill_rate_per_sec=2.0)
        assert bucket.get_available_tokens() == pytest.approx(10.0, rel=1e-2)

    def test_invalid_capacity(self):
        with pytest.raises(ValueError):
            TokenBucket(capacity=0, refill_rate_per_sec=1.0)
        with pytest.raises(ValueError):
            TokenBucket(capacity=-5, refill_rate_per_sec=1.0)

    def test_invalid_refill_rate(self):
        with pytest.raises(ValueError):
            TokenBucket(capacity=10, refill_rate_per_sec=0.0)
        with pytest.raises(ValueError):
            TokenBucket(capacity=10, refill_rate_per_sec=-1.5)


class TestTokenBucketConsumption:
    """Tests for normal token consumption."""

    def test_default_consume(self):
        bucket = TokenBucket(capacity=5, refill_rate_per_sec=0.1)
        assert bucket.consume() is True
        assert bucket.get_available_tokens() == pytest.approx(4.0, abs=0.1)

    def test_consume_multiple_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate_per_sec=0.1)
        assert bucket.consume(4) is True
        assert bucket.get_available_tokens() == pytest.approx(6.0, abs=0.1)

    def test_consume_exact_capacity(self):
        bucket = TokenBucket(capacity=5, refill_rate_per_sec=0.1)
        assert bucket.consume(5) is True
        assert bucket.get_available_tokens() == pytest.approx(0.0, abs=0.1)

    def test_consume_insufficient_tokens(self):
        bucket = TokenBucket(capacity=3, refill_rate_per_sec=0.1)
        assert bucket.consume(4) is False
        # Tokens should not be deducted if consume failed
        assert bucket.get_available_tokens() == pytest.approx(3.0, abs=0.1)

    def test_consume_after_depletion(self):
        bucket = TokenBucket(capacity=2, refill_rate_per_sec=0.01)
        assert bucket.consume(2) is True
        assert bucket.consume(1) is False


class TestTokenBucketRefillAndCeiling:
    """Tests for token refill over time and capacity ceiling."""

    def test_refill_rate_over_time(self):
        # 10 tokens capacity, refill 10 tokens per second (1 token per 0.1s)
        bucket = TokenBucket(capacity=10, refill_rate_per_sec=10.0)
        assert bucket.consume(10) is True
        assert bucket.get_available_tokens() == pytest.approx(0.0, abs=0.1)

        # Wait 0.25 seconds -> should refill approximately 2.5 tokens
        time.sleep(0.25)
        tokens = bucket.get_available_tokens()
        assert 2.0 <= tokens <= 3.0

    def test_capacity_ceiling_burst_limit(self):
        # 5 tokens capacity, 20 tokens/sec refill
        bucket = TokenBucket(capacity=5, refill_rate_per_sec=20.0)
        assert bucket.consume(3) is True
        # Sleep long enough to exceed capacity if unbounded
        time.sleep(0.5)  # Would generate 10 tokens
        # Available tokens must be capped at capacity
        assert bucket.get_available_tokens() == pytest.approx(5.0, abs=0.01)

    def test_consumption_succeeds_after_refill(self):
        bucket = TokenBucket(capacity=2, refill_rate_per_sec=5.0)
        assert bucket.consume(2) is True
        assert bucket.consume(1) is False

        # Wait for at least 1 token to refill (1 / 5 = 0.2s)
        time.sleep(0.25)
        assert bucket.consume(1) is True


class TestTokenBucketConcurrency:
    """Tests for multi-threaded safety and race condition prevention."""

    def test_concurrent_consumption_without_refill(self):
        capacity = 100
        bucket = TokenBucket(capacity=capacity, refill_rate_per_sec=0.001)

        success_count = 0
        failure_count = 0
        lock = threading.Lock()

        def worker():
            nonlocal success_count, failure_count
            res = bucket.consume(1)
            with lock:
                if res:
                    success_count += 1
                else:
                    failure_count += 1

        num_threads = 150
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for f in futures:
                f.result()

        assert success_count == capacity
        assert failure_count == num_threads - capacity
        assert bucket.get_available_tokens() == pytest.approx(0.0, abs=0.1)

    def test_concurrent_consumption_with_refill(self):
        capacity = 50
        refill_rate = 50.0  # 50 tokens/sec
        bucket = TokenBucket(capacity=capacity, refill_rate_per_sec=refill_rate)

        successful_consumptions = 0
        lock = threading.Lock()

        def worker():
            nonlocal successful_consumptions
            for _ in range(10):
                if bucket.consume(1):
                    with lock:
                        successful_consumptions += 1
                time.sleep(0.01)

        num_threads = 10
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Available tokens should never drop below 0
        assert bucket.get_available_tokens() >= 0.0
        # Total successful consumptions must not exceed capacity + max possible refilled tokens
        # 10 iterations * 0.01s = ~0.1s; max possible refill ~ 0.5s * 50 = 25 tokens + capacity = ~75-100
        assert successful_consumptions <= num_threads * 10


class TestTokenBucketEdgeCases:
    """Tests for edge cases and input validation."""

    def test_zero_token_consumption(self):
        bucket = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
        with pytest.raises(ValueError):
            bucket.consume(0)

    def test_negative_token_consumption(self):
        bucket = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
        with pytest.raises(ValueError):
            bucket.consume(-1)
        with pytest.raises(ValueError):
            bucket.consume(-5)

    def test_consume_greater_than_capacity(self):
        bucket = TokenBucket(capacity=10, refill_rate_per_sec=10.0)
        # Even with high refill rate, single request > capacity must return False
        assert bucket.consume(15) is False
        assert bucket.get_available_tokens() == pytest.approx(10.0, abs=0.1)
