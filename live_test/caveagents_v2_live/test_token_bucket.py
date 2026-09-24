import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
import pytest

# Ensure module path is accessible
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from token_bucket import TokenBucket


def test_init_valid():
    tb = TokenBucket(capacity=10, refill_rate_per_sec=2.0)
    assert tb.get_available_tokens() == pytest.approx(10.0)


@pytest.mark.parametrize("invalid_capacity", [0, -1, -100])
def test_init_invalid_capacity_non_positive(invalid_capacity):
    with pytest.raises(ValueError):
        TokenBucket(capacity=invalid_capacity, refill_rate_per_sec=1.0)


@pytest.mark.parametrize("invalid_capacity", [float("nan"), float("inf"), float("-inf")])
def test_init_invalid_capacity_nan_inf(invalid_capacity):
    with pytest.raises(ValueError):
        TokenBucket(capacity=invalid_capacity, refill_rate_per_sec=1.0)


@pytest.mark.parametrize("invalid_rate", [0, 0.0, -1.0, -10.5])
def test_init_invalid_refill_rate_non_positive(invalid_rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=10, refill_rate_per_sec=invalid_rate)


@pytest.mark.parametrize("invalid_rate", [float("nan"), float("inf"), float("-inf")])
def test_init_invalid_refill_rate_nan_inf(invalid_rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=10, refill_rate_per_sec=invalid_rate)


def test_consume_default():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=1.0)
    assert tb.consume() is True
    assert tb.get_available_tokens() == pytest.approx(4.0, abs=0.1)


def test_consume_custom_amount():
    tb = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    assert tb.consume(4) is True
    assert tb.get_available_tokens() == pytest.approx(6.0, abs=0.1)
    assert tb.consume(6) is True
    assert tb.get_available_tokens() == pytest.approx(0.0, abs=0.1)


def test_consume_insufficient_tokens():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=0.001)
    assert tb.consume(6) is False
    assert tb.get_available_tokens() == pytest.approx(5.0, abs=0.1)


@pytest.mark.parametrize("invalid_tokens", [0, -1, -5, float("nan"), float("inf"), float("-inf")])
def test_consume_invalid_tokens(invalid_tokens):
    tb = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    with pytest.raises(ValueError):
        tb.consume(invalid_tokens)


def test_burst_limit_ceiling():
    current_time = 1000.0

    def mock_time():
        return current_time

    # Patch both monotonic and time to support either implementation
    with patch("time.monotonic", side_effect=mock_time), patch("time.time", side_effect=mock_time):
        tb = TokenBucket(capacity=10, refill_rate_per_sec=5.0)
        assert tb.get_available_tokens() == pytest.approx(10.0)

        # Fast forward a long time
        current_time += 1000.0
        assert tb.get_available_tokens() == pytest.approx(10.0)

        # Consume half
        assert tb.consume(5) is True
        assert tb.get_available_tokens() == pytest.approx(5.0)

        # Fast forward again
        current_time += 1000.0
        assert tb.get_available_tokens() == pytest.approx(10.0)


def test_refill_deterministic_mock_clock():
    current_time = 100.0

    def mock_time():
        return current_time

    with patch("time.monotonic", side_effect=mock_time), patch("time.time", side_effect=mock_time):
        tb = TokenBucket(capacity=10, refill_rate_per_sec=2.0)
        assert tb.consume(10) is True
        assert tb.get_available_tokens() == pytest.approx(0.0)

        # Advance 1.5 seconds -> refill 3.0 tokens
        current_time += 1.5
        assert tb.get_available_tokens() == pytest.approx(3.0)

        # Consume 2 tokens
        assert tb.consume(2) is True
        assert tb.get_available_tokens() == pytest.approx(1.0)

        # Advance 2.0 seconds -> 1.0 + 4.0 = 5.0 tokens
        current_time += 2.0
        assert tb.get_available_tokens() == pytest.approx(5.0)


def test_concurrency_race_condition_safety():
    # 100 capacity, negligible refill rate during test
    capacity = 100
    tb = TokenBucket(capacity=capacity, refill_rate_per_sec=0.0001)

    workers = 20
    attempts_per_worker = 10  # Total 200 consume attempts for 1 token each

    def worker_task():
        successful_consumes = 0
        for _ in range(attempts_per_worker):
            if tb.consume(1):
                successful_consumes += 1
        return successful_consumes

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker_task) for _ in range(workers)]
        results = [f.result() for f in futures]

    total_consumed = sum(results)
    assert total_consumed == capacity, f"Expected exactly {capacity} consumed, got {total_consumed}"
    assert tb.get_available_tokens() >= 0.0
    assert tb.get_available_tokens() < 1.0
