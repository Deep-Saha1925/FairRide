# ============================================================
# FairRide Project — test_fairride.py
# Purpose: Automated integration test
#          Simulates full booking flow without manual input
# ============================================================

import sys
import os
import time
import threading
import json
import socket

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'crypto'))

from node import start_node
from broker import start_broker
from client import send_booking_request


def start_background_servers():
    """Start all servers in background threads."""
    print("[TEST] Starting Node 1 on port 9001...")
    t1 = threading.Thread(target=start_node, args=(9001,), daemon=True)
    t1.start()

    print("[TEST] Starting Node 2 on port 9002...")
    t2 = threading.Thread(target=start_node, args=(9002,), daemon=True)
    t2.start()

    print("[TEST] Starting Node 3 on port 9003...")
    t3 = threading.Thread(target=start_node, args=(9003,), daemon=True)
    t3.start()

    print("[TEST] Starting Broker on port 9000...")
    t4 = threading.Thread(target=start_broker, args=(9000,), daemon=True)
    t4.start()

    # Give servers time to start
    time.sleep(1)
    print("[TEST] All servers running!\n")


def run_tests():
    print("\n" + "=" * 55)
    print("  FairRide — Integration Tests")
    print("=" * 55)

    results = []

    # ── Test 1: First booking (should be CONFIRMED) ──────────
    print("\n[TEST 1] First booking for PRIYA_W1234...")
    r = send_booking_request("PRIYA_W1234")
    passed = r["status"] == "CONFIRMED"
    results.append(("Test 1: First booking", passed))
    print(f"  Status: {r['status']} → {'PASS' if passed else 'FAIL'}")

    # ── Test 2: Second booking (should be CONFIRMED) ─────────
    print("\n[TEST 2] Second booking for PRIYA_W1234...")
    r = send_booking_request("PRIYA_W1234")
    passed = r["status"] == "CONFIRMED"
    results.append(("Test 2: Second booking", passed))
    print(f"  Status: {r['status']} → {'PASS' if passed else 'FAIL'}")

    # ── Test 3: Third booking (should be REJECTED) ───────────
    print("\n[TEST 3] Third booking for PRIYA_W1234 (should be rejected)...")
    r = send_booking_request("PRIYA_W1234")
    passed = r["status"] == "REJECTED"
    results.append(("Test 3: Third booking rejected", passed))
    print(f"  Status: {r['status']} → {'PASS' if passed else 'FAIL'}")

    # ── Test 4: Different user (should be CONFIRMED) ─────────
    print("\n[TEST 4] First booking for different user MEENA_W5678...")
    r = send_booking_request("MEENA_W5678")
    passed = r["status"] == "CONFIRMED"
    results.append(("Test 4: Different user books", passed))
    print(f"  Status: {r['status']} → {'✅ PASS' if passed else '❌ FAIL'}")

    # ── Summary ───────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  TEST SUMMARY")
    print("=" * 55)
    all_passed = True
    for name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")
        if not passed:
            all_passed = False

    print("=" * 55)
    if all_passed:
        print("  🎉 ALL TESTS PASSED! FairRide is working!")
    else:
        print("  ⚠️  Some tests failed. Check the output above.")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    start_background_servers()
    run_tests()