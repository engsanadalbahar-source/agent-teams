import math
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest

from token_bucket import TokenBucket


def test_init_valid():
    tb = TokenBucket(capacity=10, refill_rate_per_sec=2.0)
    assert tb.get_available_tokens() == 10.0


@pytest.mark.parametrize("cap", [0, -1, -100, float("nan"), float("inf"), -float("inf")])
def test_init_invalid_capacity(cap):
    with pytest.raises(ValueError):
        TokenBucket(capacity=cap, refill_rate_per_sec=1.0)


@pytest.mark.parametrize("rate", [0.0, -1.0, -0.5, float("nan"), float("inf"), -float("inf")])
def test_init_invalid_refill_rate(rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=10, refill_rate_per_sec=rate)


def test_consume_basic_and_balance_tracking():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=1.0)
    assert tb.consume(2) is True
    assert math.isclose(tb.get_available_tokens(), 3.0, abs_tol=1e-2)
    assert tb.consume(3) is True
    assert math.isclose(tb.get_available_tokens(), 0.0, abs_tol=1e-2)
    assert tb.consume(1) is False
    assert math.isclose(tb.get_available_tokens(), 0.0, abs_tol=1e-2)


@pytest.mark.parametrize("tokens", [0, -1, -5, float("nan"), float("inf")])
def test_consume_invalid_tokens(tokens):
    tb = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    with pytest.raises(ValueError):
        tb.consume(tokens)


def test_refill_rate_deterministic_and_burst_ceiling():
    current_time = 1000.0

    def mock_time():
        return current_time

    with patch("time.monotonic", side_effect=mock_time):
        tb = TokenBucket(capacity=10, refill_rate_per_sec=2.0)
        assert tb.consume(10) is True
        assert tb.get_available_tokens() == 0.0

        # Advance 2 seconds -> should refill 4 tokens
        current_time += 2.0
        assert math.isclose(tb.get_available_tokens(), 4.0, abs_tol=1e-5)
        assert tb.consume(3) is True
        assert math.isclose(tb.get_available_tokens(), 1.0, abs_tol=1e-5)

        # Advance 10 seconds -> should cap at capacity (10 tokens)
        current_time += 10.0
        assert math.isclose(tb.get_available_tokens(), 10.0, abs_tol=1e-5)
        # Verify ceiling cannot exceed capacity
        current_time += 50.0
        assert math.isclose(tb.get_available_tokens(), 10.0, abs_tol=1e-5)


def test_thread_safety_concurrency():
    capacity = 100
    refill_rate = 0.0001  # negligible refill during burst test
    tb = TokenBucket(capacity=capacity, refill_rate_per_sec=refill_rate)

    num_threads = 20
    requests_per_thread = 10

    def worker():
        successes = 0
        for _ in range(requests_per_thread):
            if tb.consume(1):
                successes += 1
        return successes

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_threads)]
        total_successes = sum(f.result() for f in futures)

    # Exactly capacity tokens should have been consumed
    assert total_successes == capacity
    assert tb.get_available_tokens() < 1.0
