"""Comprehensive test suite for TokenBucket."""

import concurrent.futures
import threading
import time
import pytest

from token_bucket import TokenBucket


class MockClock:
    """Mock clock for deterministic time simulation."""

    def __init__(self, initial_time: float = 0.0) -> None:
        self._current_time = initial_time
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._current_time

    def advance(self, seconds: float) -> None:
        with self._lock:
            self._current_time += seconds


# ---------------------------------------------------------------------------
# Input Validation & Initialization Tests
# ---------------------------------------------------------------------------


def test_initialization_valid():
    bucket = TokenBucket(capacity=10, refill_rate_per_sec=2.5)
    assert bucket.capacity == 10
    assert bucket.refill_rate_per_sec == 2.5
    assert bucket.get_available_tokens() == 10.0


@pytest.mark.parametrize("invalid_capacity", [0, -1, -100, 3.5, True, False, "10", None])
def test_initialization_invalid_capacity(invalid_capacity):
    with pytest.raises(ValueError):
        TokenBucket(capacity=invalid_capacity, refill_rate_per_sec=1.0)


@pytest.mark.parametrize("invalid_rate", [0, 0.0, -1, -0.5, True, False, "2.0", None])
def test_initialization_invalid_refill_rate(invalid_rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=10, refill_rate_per_sec=invalid_rate)


@pytest.mark.parametrize("invalid_tokens", [0, -1, -5, 1.5, True, False, "1", None])
def test_consume_invalid_tokens(invalid_tokens):
    bucket = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    with pytest.raises(ValueError):
        bucket.consume(invalid_tokens)


# ---------------------------------------------------------------------------
# Burst Capacity Tests
# ---------------------------------------------------------------------------


def test_burst_capacity_full_consumption():
    bucket = TokenBucket(capacity=5, refill_rate_per_sec=1.0)
    # Starts full
    assert bucket.get_available_tokens() == 5.0

    # Consume all 5 in burst
    for _ in range(5):
        assert bucket.consume(1) is True

    # 6th attempt should fail immediately
    assert bucket.consume(1) is False
    assert bucket.get_available_tokens() < 1.0


def test_burst_capacity_single_large_consumption():
    bucket = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    assert bucket.consume(10) is True
    assert bucket.consume(1) is False


def test_consume_more_than_capacity():
    bucket = TokenBucket(capacity=5, refill_rate_per_sec=1.0)
    # Requesting more tokens than total capacity
    assert bucket.consume(6) is False
    # Bucket should still have 5 tokens intact
    assert bucket.get_available_tokens() == 5.0


def test_burst_partial_consumption():
    bucket = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    assert bucket.consume(4) is True
    assert bucket.consume(4) is True
    assert bucket.consume(4) is False  # Only 2 left
    assert bucket.consume(2) is True
    assert bucket.consume(1) is False


# ---------------------------------------------------------------------------
# Refill Rate Tests
# ---------------------------------------------------------------------------


def test_refill_rate_deterministic():
    clock = MockClock(0.0)
    bucket = TokenBucket(capacity=10, refill_rate_per_sec=2.0, time_func=clock)

    # Empty the bucket
    assert bucket.consume(10) is True
    assert bucket.get_available_tokens() == 0.0

    # Advance 1.5 seconds -> 1.5 * 2.0 = 3.0 tokens
    clock.advance(1.5)
    assert bucket.get_available_tokens() == pytest.approx(3.0)

    # Consume 2 tokens -> 1.0 left
    assert bucket.consume(2) is True
    assert bucket.get_available_tokens() == pytest.approx(1.0)

    # Advance 0.5 seconds -> 1.0 + 1.0 = 2.0 tokens
    clock.advance(0.5)
    assert bucket.get_available_tokens() == pytest.approx(2.0)


def test_refill_capped_at_capacity():
    clock = MockClock(0.0)
    bucket = TokenBucket(capacity=5, refill_rate_per_sec=10.0, time_func=clock)

    # Consume 3 tokens -> 2 left
    assert bucket.consume(3) is True
    assert bucket.get_available_tokens() == pytest.approx(2.0)

    # Advance 100 seconds (would generate 1000 tokens)
    clock.advance(100.0)
    # Must be capped at capacity
    assert bucket.get_available_tokens() == 5.0


def test_refill_with_real_sleep():
    bucket = TokenBucket(capacity=5, refill_rate_per_sec=10.0)
    assert bucket.consume(5) is True
    assert bucket.consume(1) is False

    # Sleep 0.15s -> ~1.5 tokens refilled
    time.sleep(0.15)
    assert bucket.consume(1) is True


# ---------------------------------------------------------------------------
# Concurrency / Thread Safety Tests
# ---------------------------------------------------------------------------


def test_concurrent_burst_exact_capacity():
    """Ensure no race condition allows more tokens consumed than capacity."""
    capacity = 100
    bucket = TokenBucket(capacity=capacity, refill_rate_per_sec=0.001)  # Negligible refill
    num_threads = 200

    start_event = threading.Event()
    results = []

    def worker():
        start_event.wait()
        results.append(bucket.consume(1))

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for t in threads:
        t.start()

    # Release all threads simultaneously
    start_event.set()
    for t in threads:
        t.join()

    successful_consumptions = sum(1 for r in results if r is True)
    assert successful_consumptions == capacity
    assert bucket.get_available_tokens() < 1.0


def test_concurrent_heavy_contention():
    """Heavy contention with multiple threads consuming variable tokens."""
    capacity = 500
    refill_rate = 50.0  # 50 tokens/sec
    bucket = TokenBucket(capacity=capacity, refill_rate_per_sec=refill_rate)

    num_threads = 20
    consumptions_per_thread = 50
    successful_tokens_consumed = 0
    lock = threading.Lock()

    def worker():
        nonlocal successful_tokens_consumed
        local_consumed = 0
        for _ in range(consumptions_per_thread):
            if bucket.consume(1):
                local_consumed += 1
            time.sleep(0.001)  # small jitter
        with lock:
            successful_tokens_consumed += local_consumed

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_threads)]
        concurrent.futures.wait(futures)

    # Tokens available should never be negative
    available = bucket.get_available_tokens()
    assert available >= 0.0
    assert available <= capacity
    # Total consumed should not exceed capacity + generated tokens
    assert successful_tokens_consumed <= capacity + refill_rate * 5.0
