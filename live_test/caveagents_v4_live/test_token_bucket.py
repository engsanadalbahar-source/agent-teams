import math
import time
from concurrent.futures import ThreadPoolExecutor
import pytest

from token_bucket import TokenBucket


def test_init_valid():
    tb = TokenBucket(capacity=10, refill_rate_per_sec=2.0)
    assert tb.get_available_tokens() == pytest.approx(10.0)


@pytest.mark.parametrize("capacity,rate", [
    (0, 1.0),
    (-5, 1.0),
    (10, 0.0),
    (10, -2.0),
    (10, float("nan")),
    (10, float("inf")),
    (10, float("-inf")),
    (float("nan"), 1.0),
    ("10", 1.0),
    (10, "1.0"),
])
def test_init_invalid_values(capacity, rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=capacity, refill_rate_per_sec=rate)


def test_consume_basic():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=1.0)
    assert tb.consume(2) is True
    assert tb.get_available_tokens() == pytest.approx(3.0, abs=0.1)
    assert tb.consume() is True
    assert tb.get_available_tokens() == pytest.approx(2.0, abs=0.1)


def test_consume_insufficient():
    tb = TokenBucket(capacity=2, refill_rate_per_sec=0.1)
    assert tb.consume(3) is False
    assert tb.get_available_tokens() == pytest.approx(2.0, abs=0.1)


@pytest.mark.parametrize("tokens", [0, -1, -5, float("nan"), float("inf"), "1", None])
def test_consume_invalid(tokens):
    tb = TokenBucket(capacity=10, refill_rate_per_sec=1.0)
    with pytest.raises(ValueError):
        tb.consume(tokens)


def test_burst_ceiling():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=10.0)
    time.sleep(0.1)
    assert tb.get_available_tokens() <= 5.0
    assert tb.get_available_tokens() == pytest.approx(5.0)


def test_refill_over_time():
    tb = TokenBucket(capacity=5, refill_rate_per_sec=10.0)
    assert tb.consume(5) is True
    assert tb.get_available_tokens() < 1.0
    time.sleep(0.2)
    tokens = tb.get_available_tokens()
    assert 1.5 <= tokens <= 3.5


def test_thread_safety():
    capacity = 100
    tb = TokenBucket(capacity=capacity, refill_rate_per_sec=0.01)
    workers = 20
    requests_per_worker = 10

    success_count = 0

    def worker():
        nonlocal success_count
        local_success = 0
        for _ in range(requests_per_worker):
            if tb.consume(1):
                local_success += 1
        return local_success

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker) for _ in range(workers)]
        results = [f.result() for f in futures]

    total_success = sum(results)
    assert total_success == capacity
    assert tb.get_available_tokens() < 1.0
