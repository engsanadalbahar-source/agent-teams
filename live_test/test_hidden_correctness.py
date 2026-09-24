"""
Independent Held-Out Test Suite for TokenBucket Implementations.
Tests edge cases, strict input guards, lock safety, and concurrency correctness
without either the Coder or QA subagents having seen these test cases in advance.
"""

import math
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
import pytest


def run_evaluation_on_module(module_path: str):
    """Dynamically import and test TokenBucket implementation."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("tb_mod", module_path)
    tb_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tb_mod)
    TokenBucket = tb_mod.TokenBucket

    results = {"passed": 0, "failed": 0, "failures": []}

    def record_test(name, fn):
        try:
            fn()
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["failures"].append(f"{name}: {type(e).__name__} - {e}")

    # Test 1: Concurrency Race-Free Exact Drain (Double-Spend Prevention)
    def t1_concurrency_race():
        capacity = 25
        tb = TokenBucket(capacity=capacity, refill_rate_per_sec=0.0001)
        consumed_count = 0
        lock = threading.Lock()

        def worker():
            nonlocal consumed_count
            if tb.consume(1):
                with lock:
                    consumed_count += 1

        threads = [threading.Thread(target=worker) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert consumed_count == capacity, f"Expected {capacity} consumed, got {consumed_count}"
    record_test("T1_ConcurrencyRaceFree", t1_concurrency_race)

    # Test 2: Boolean Rejection (Python bool subclasses int: True == 1)
    def t2_boolean_rejection():
        for bad in [True, False]:
            try:
                TokenBucket(bad, 1.0)
                raise AssertionError(f"Allowed boolean capacity: {bad}")
            except (ValueError, TypeError):
                pass

            try:
                TokenBucket(10, bad)
                raise AssertionError(f"Allowed boolean refill rate: {bad}")
            except (ValueError, TypeError):
                pass

            tb = TokenBucket(10, 1.0)
            try:
                tb.consume(bad)
                raise AssertionError(f"Allowed boolean consume tokens: {bad}")
            except (ValueError, TypeError):
                pass
    record_test("T2_BooleanRejection", t2_boolean_rejection)

    # Test 3: NaN and Infinity Rejection
    def t3_nan_inf_rejection():
        for bad in [float("nan"), float("inf"), float("-inf")]:
            try:
                TokenBucket(bad, 1.0)
                raise AssertionError(f"Allowed non-finite capacity: {bad}")
            except (ValueError, TypeError):
                pass

            try:
                TokenBucket(10, bad)
                raise AssertionError(f"Allowed non-finite refill: {bad}")
            except (ValueError, TypeError):
                pass
    record_test("T3_NaNInfRejection", t3_nan_inf_rejection)

    # Test 4: Capacity Ceiling Boundary Invariant
    def t4_capacity_ceiling():
        tb = TokenBucket(10, 50.0)
        time.sleep(0.1)
        avail = tb.get_available_tokens()
        assert avail <= 10.0, f"Available tokens {avail} exceeded capacity 10.0"
    record_test("T4_CapacityCeiling", t4_capacity_ceiling)

    # Test 5: Default consume() parameter
    def t5_default_consume():
        tb = TokenBucket(5, 0.001)
        assert tb.consume() is True
        avail = tb.get_available_tokens()
        assert 3.9 <= avail <= 4.1, f"Expected ~4 tokens, got {avail}"
    record_test("T5_DefaultConsume", t5_default_consume)

    # Test 6: Zero/Negative Consumption Rejection
    def t6_zero_negative_rejection():
        tb = TokenBucket(5, 1.0)
        for bad in [0, -1, -5]:
            try:
                tb.consume(bad)
                raise AssertionError(f"Allowed non-positive consume: {bad}")
            except (ValueError, TypeError):
                pass
    record_test("T6_ZeroNegativeRejection", t6_zero_negative_rejection)

    # Test 7: Available tokens read does not mutate balance
    def t7_read_does_not_mutate():
        tb = TokenBucket(5, 0.0001)
        a1 = tb.get_available_tokens()
        a2 = tb.get_available_tokens()
        assert abs(a1 - a2) < 0.001, "get_available_tokens mutated token balance"
    record_test("T7_ReadDoesNotMutate", t7_read_does_not_mutate)

    return results


if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    targets = {
        "Pruned Monolith": os.path.join(base_dir, "pruned_mono_live", "token_bucket.py"),
        "CaveAgents v4 Team": os.path.join(base_dir, "caveagents_v4_live", "token_bucket.py"),
        "Caveman Monolith": os.path.join(base_dir, "caveman_mono_live", "token_bucket.py"),
        "Standard Teamwork": os.path.join(base_dir, "standard_teamwork_live", "token_bucket.py"),
    }

    print("=" * 65)
    print("   INDEPENDENT HELD-OUT ADVERSARIAL TEST EVALUATION   ")
    print("=" * 65)

    for name, path in targets.items():
        res = run_evaluation_on_module(path)
        status = "PASSED" if res["failed"] == 0 else "FAILED"
        print(f"\n• {name}: {res['passed']}/{res['passed'] + res['failed']} passed ({status})")
        if res["failures"]:
            for f in res["failures"]:
                print(f"    - FAIL: {f}")
