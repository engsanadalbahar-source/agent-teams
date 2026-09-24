import math
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest

from token_bucket import TokenBucket


def test_init_valid():
    tb = TokenBucket(capacity=10, refill_rate_per_sec=2.0)
    assert tb.get_available_tokens() == 10.0


@pytest.mark.parametrize("invalid_capacity", [0, -1, -100, float("nan"), float("inf"), float("-inf")])
def test_init_invalid_capacity(invalid_capacity):
    with pytest.raises(ValueError):
        TokenBucket(capacity=invalid_capacity, refill_rate_per_sec=1.0)


@pytest.mark.parametrize("invalid_rate", [0, 0.0, -1.0, -0.01, float("nan"), float("inf"), float("-inf")])
def test_init_invalid_refill_rate(invalid_rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=10, refill_rate_per_sec=invalid_rate)


def test_consume_default_and_balance_tracking():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=1.0)
    assert tb.consume() is True
    assert tb.get_available_tokens() <= 4.0
    assert tb.consume(2) is True
    assert tb.get_available_tokens() <= 2.0


def test_consume_insufficient_tokens():
    tb = TokenBucket(capacity=3, refill_rate_per_sec=0.1)
    assert tb.consume(3) is True
    before = tb.get_available_tokens()
    assert tb.consume(1) is False
    assert tb.get_available_tokens() == pytest.approx(before, abs=0.05)


@pytest.mark.parametrize("invalid_tokens", [0, -1, -5, float("nan"), float("inf"), float("-inf")])
def test_consume_invalid_tokens(invalid_tokens):
    tb = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    with pytest.raises(ValueError):
        tb.consume(invalid_tokens)


def test_burst_limit_ceiling():
    current_time = [1000.0]

    def mock_time():
        return current_time[0]

    with patch("time.monotonic", side_effect=mock_time):
        tb = TokenBucket(capacity=10, refill_rate_per_sec=5.0)
        assert tb.get_available_tokens() == 10.0
        # Fast-forward 100 seconds
        current_time[0] += 100.0
        assert tb.get_available_tokens() == 10.0
        assert tb.consume(10) is True
        # Fast-forward another 100 seconds
        current_time[0] += 100.0
        assert tb.get_available_tokens() == 10.0


def test_refill_rate_over_elapsed_time():
    current_time = [1000.0]

    def mock_time():
        return current_time[0]

    with patch("time.monotonic", side_effect=mock_time):
        tb = TokenBucket(capacity=10, refill_rate_per_sec=2.0)
        assert tb.consume(10) is True
        assert tb.get_available_tokens() == 0.0

        # Advance 1.5 seconds -> 3.0 tokens refilled
        current_time[0] += 1.5
        assert tb.get_available_tokens() == pytest.approx(3.0, abs=1e-5)

        # Consume 2 tokens -> 1.0 remaining
        assert tb.consume(2) is True
        assert tb.get_available_tokens() == pytest.approx(1.0, abs=1e-5)

        # Cannot consume 2 tokens
        assert tb.consume(2) is False

        # Advance 0.5s -> 2.0 available
        current_time[0] += 0.5
        assert tb.get_available_tokens() == pytest.approx(2.0, abs=1e-5)
        assert tb.consume(2) is True


def test_multithreaded_concurrency_safety():
    # Exactly 50 capacity, 0 refill rate during contention
    current_time = [1000.0]

    with patch("time.monotonic", side_effect=lambda: current_time[0]):
        tb = TokenBucket(capacity=50, refill_rate_per_sec=0.0001)

        total_requests = 100
        tokens_per_request = 1

        def attempt_consume(_):
            return tb.consume(tokens_per_request)

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(attempt_consume, range(total_requests)))

        success_count = sum(1 for r in results if r is True)
        fail_count = sum(1 for r in results if r is False)

        assert success_count == 50
        assert fail_count == 50
        assert tb.get_available_tokens() < 1.0
