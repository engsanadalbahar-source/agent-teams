import math
import time
from concurrent.futures import ThreadPoolExecutor
import pytest

from token_bucket import TokenBucket


def test_initialization_valid():
    tb = TokenBucket(10, 2.0)
    assert tb.get_available_tokens() == 10.0


@pytest.mark.parametrize("bad_val", [0, -1, -5.5, float("nan"), float("inf"), float("-inf"), True, False])
def test_initialization_invalid_capacity(bad_val):
    with pytest.raises(ValueError):
        TokenBucket(bad_val, 2.0)


@pytest.mark.parametrize("bad_val", [0, -1, -5.5, float("nan"), float("inf"), float("-inf"), True, False])
def test_initialization_invalid_refill_rate(bad_val):
    with pytest.raises(ValueError):
        TokenBucket(10, bad_val)


@pytest.mark.parametrize("bad_val", [0, -1, -5.5, float("nan"), float("inf"), float("-inf"), True, False])
def test_consume_invalid_tokens(bad_val):
    tb = TokenBucket(10, 2.0)
    with pytest.raises(ValueError):
        tb.consume(bad_val)


def test_consume_normal_balance_tracking():
    tb = TokenBucket(5, 0.1)
    assert tb.consume(1) is True
    # balance should be around 4
    avail = tb.get_available_tokens()
    assert 3.9 <= avail <= 4.1

    assert tb.consume() is True  # default 1
    avail = tb.get_available_tokens()
    assert 2.9 <= avail <= 3.1

    assert tb.consume(3) is True
    avail = tb.get_available_tokens()
    assert 0.0 <= avail <= 0.2

    # Insufficient tokens
    assert tb.consume(1) is False
    # Balance should remain unchanged (not deducted on failure)
    avail2 = tb.get_available_tokens()
    assert 0.0 <= avail2 <= 0.2


def test_refill_rate_and_burst_ceiling():
    tb = TokenBucket(5, 10.0)
    assert tb.consume(5) is True
    assert tb.get_available_tokens() < 1.0

    # Wait 0.2s -> should refill ~2 tokens
    time.sleep(0.2)
    avail = tb.get_available_tokens()
    assert 1.5 <= avail <= 2.5

    # Wait long enough to exceed capacity -> check burst ceiling
    time.sleep(0.5)
    assert tb.get_available_tokens() == 5.0


def test_multithreaded_concurrency_safety():
    capacity = 100
    tb = TokenBucket(capacity, 1.0)
    num_threads = 20
    requests_per_thread = 10

    def worker():
        success_count = 0
        for _ in range(requests_per_thread):
            if tb.consume(1):
                success_count += 1
        return success_count

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_threads)]
        total_consumed = sum(f.result() for f in futures)

    # Since refill rate is 1.0/sec and run takes a few ms, total consumed should be exactly capacity (or capacity + at most 1)
    assert total_consumed <= capacity + 1
    # Balance must never be negative
    assert tb.get_available_tokens() >= 0.0
