import math
import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from token_bucket import TokenBucket


def test_valid_initialization():
    tb = TokenBucket(capacity=10, refill_rate_per_sec=2.5)
    tokens = tb.get_available_tokens()
    assert abs(tokens - 10.0) < 1e-3


@pytest.mark.parametrize("invalid_capacity", [0, -1, -10, float("nan"), float("inf"), float("-inf"), True, False, 1.5, "10"])
def test_invalid_capacity(invalid_capacity):
    with pytest.raises(ValueError):
        TokenBucket(capacity=invalid_capacity, refill_rate_per_sec=1.0)


@pytest.mark.parametrize("invalid_rate", [0, -0.1, -5, float("nan"), float("inf"), float("-inf"), True, False, "1.0"])
def test_invalid_refill_rate(invalid_rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=10, refill_rate_per_sec=invalid_rate)


@pytest.mark.parametrize("invalid_tokens", [0, -1, float("nan"), float("inf"), True, False, 1.5, "1"])
def test_invalid_consume_tokens(invalid_tokens):
    tb = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    with pytest.raises(ValueError):
        tb.consume(invalid_tokens)


def test_consumption_and_balance_tracking():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=0.01)
    assert tb.consume(2) is True
    assert abs(tb.get_available_tokens() - 3.0) < 0.1
    assert tb.consume(3) is True
    assert abs(tb.get_available_tokens() - 0.0) < 0.1
    assert tb.consume(1) is False


def test_refill_rate_over_elapsed_time():
    tb = TokenBucket(capacity=10, refill_rate_per_sec=10.0)
    assert tb.consume(10) is True
    assert tb.consume(1) is False
    time.sleep(0.2)
    # Refilled approx 2 tokens
    assert tb.consume(1) is True


def test_burst_ceiling():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=100.0)
    time.sleep(0.1)
    assert tb.get_available_tokens() <= 5.0
    assert tb.consume(5) is True
    assert tb.consume(1) is False


def test_concurrency_safety():
    capacity = 100
    tb = TokenBucket(capacity=capacity, refill_rate_per_sec=0.001)

    successful_consumptions = 0
    num_workers = 20
    attempts_per_worker = 10

    def attempt_consume():
        return tb.consume(1)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(attempt_consume) for _ in range(num_workers * attempts_per_worker)]
        results = [f.result() for f in futures]

    successful_consumptions = sum(1 for r in results if r)
    assert successful_consumptions == capacity
    assert tb.get_available_tokens() < 1.0
