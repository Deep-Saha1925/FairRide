# ============================================================
# FairRide Project — broker.py
# Purpose: Central Broker Server
#          - Receives booking requests from clients
#          - Splits secret and distributes shares to nodes
#          - Collects shares from nodes to authenticate
#          - Enforces max 2 bookings per user
# ============================================================

import socket
import json
import threading
import hashlib
import sys
import os

# Add crypto folder to path so we can import shamir
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'crypto'))
from shamir import split_secret, reconstruct_secret, PRIME

# ── Node Configuration ────────────────────────────────────────
# These are the 3 auth nodes the broker talks to
NODES = [
    {"host": "localhost", "port": 9001, "id": 1},
    {"host": "localhost", "port": 9002, "id": 2},
    {"host": "localhost", "port": 9003, "id": 3},
]

K = 2  # Minimum shares needed (threshold)
N = 3  # Total nodes

# ── Booking Database (in-memory for now) ─────────────────────
# Format: { user_id: booking_count }
booking_db = {}
db_lock = threading.Lock()  # Prevent race conditions

# ── Session Share Cache ───────────────────────────────────────
# Stores shares generated per booking attempt so the same
# shares are distributed AND collected in one session
# Format: { user_id: [(x1,y1), (x2,y2), (x3,y3)] }
session_shares = {}
session_lock = threading.Lock()


# ── Helper: Send message to a Node ───────────────────────────
def send_to_node(node, message):
    """
    Send a JSON message to a node and return its response.

    Parameters:
        node    : dict with host and port
        message : dict to send as JSON

    Returns:
        response dict or None if failed
    """
    try:
        # Create a fresh socket for each node connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)  # 5 second timeout
        s.connect((node["host"], node["port"]))
        s.send(json.dumps(message).encode())

        raw = s.recv(4096).decode()
        s.close()
        return json.loads(raw)

    except Exception as e:
        print(f"  [BROKER] Failed to reach Node {node['port']}: {e}")
        return None


# ── Helper: Hash user ID to a secret number ──────────────────
def user_id_to_secret(user_id):
    """
    Convert a user's ID string into a large integer (secret).
    Uses SHA-256 hashing for consistency.
    """
    hash_bytes = hashlib.sha256(user_id.encode()).hexdigest()
    return int(hash_bytes, 16) % PRIME


# ── Core: Distribute shares to all nodes ─────────────────────
def distribute_shares(user_id):
    """
    Split user's identity into shares and send to each node.

    Steps:
    1. Convert user_id → secret (via hash)
    2. Split secret into n shares (Shamir SSS)
    3. Cache shares locally for the authentication step
    4. Send each share to its respective node
    """
    secret = user_id_to_secret(user_id)
    shares = split_secret(secret, K, N)

    # Cache shares so authenticate_user uses the exact same values
    with session_lock:
        session_shares[user_id] = shares

    print(f"  [BROKER] Distributing {N} shares for user: {user_id}")

    success_count = 0
    for i, node in enumerate(NODES):
        share = shares[i]  # (x, y) tuple
        message = {
            "type": "STORE_SHARE",
            "user_id": user_id,
            "share": list(share)  # Convert tuple to list for JSON
        }
        response = send_to_node(node, message)
        if response and response.get("status") == "OK":
            success_count += 1
            print(f"  [BROKER] Share {i+1} stored in Node {node['port']} ")
        else:
            print(f"  [BROKER] Failed to store share in Node {node['port']} ")

    return success_count >= K  # Success if at least k nodes got shares


# ── Core: Collect shares from nodes and authenticate ─────────
def authenticate_user(user_id):
    """
    Collect shares from nodes and reconstruct secret.
    Compare with expected secret to verify identity.

    Returns: True if authenticated, False otherwise
    """
    print(f"  [BROKER] Authenticating user: {user_id}")

    collected_shares = []

    for node in NODES:
        message = {
            "type": "GET_SHARE",
            "user_id": user_id
        }
        response = send_to_node(node, message)

        if response and response.get("status") == "OK":
            share = tuple(response["share"])  # Convert list back to tuple
            collected_shares.append(share)
            print(f"  [BROKER] Got share from Node {node['port']}")

        # Stop once we have enough shares (k threshold)
        if len(collected_shares) >= K:
            break

    if len(collected_shares) < K:
        print(f"  [BROKER] Not enough shares collected ({len(collected_shares)}/{K})")
        return False

    # Use cached shares from this session for reconstruction
    # (nodes may return shares from a previous session otherwise)
    with session_lock:
        cached = session_shares.get(user_id, [])

    if len(cached) >= K:
        recon_shares = cached[:K]
    else:
        recon_shares = collected_shares

    # Reconstruct the secret from shares
    reconstructed = reconstruct_secret(recon_shares)

    # Compare with expected secret
    expected = user_id_to_secret(user_id)

    if reconstructed == expected:
        print(f"  [BROKER] Authentication SUCCESS ")
        return True
    else:
        print(f"  [BROKER] Authentication FAILED ")
        return False


# ── Core: Handle a full booking request ──────────────────────
def handle_booking(user_id):
    """
    Full booking flow:
    1. Check booking limit (max 2)
    2. Distribute shares to nodes
    3. Authenticate user
    4. If OK → confirm booking and update count
    """

    # Step 1: Check booking limit (thread-safe)
    with db_lock:
        count = booking_db.get(user_id, 0)
        if count >= 2:
            return {
                "status": "REJECTED",
                "reason": f"Booking limit reached! You have already booked {count} times (max 2)."
            }

    # Step 2: Distribute shares to all nodes
    distributed = distribute_shares(user_id)
    if not distributed:
        return {
            "status": "ERROR",
            "reason": "Failed to distribute shares to nodes."
        }

    # Step 3: Authenticate user via nodes
    authenticated = authenticate_user(user_id)
    if not authenticated:
        return {
            "status": "ERROR",
            "reason": "Authentication failed. Identity could not be verified."
        }

    # Step 4: Confirm booking and update count (thread-safe)
    with db_lock:
        booking_db[user_id] = booking_db.get(user_id, 0) + 1
        new_count = booking_db[user_id]

    return {
        "status": "CONFIRMED",
        "message": f"Booking confirmed!  You have used {new_count}/2 bookings.",
        "bookings_used": new_count
    }


# ── Socket: Handle a single client connection ─────────────────
def handle_client(connection, address):
    """Receive booking request from client and send response."""
    print(f"\n[BROKER] New client connected: {address}")

    try:
        raw = connection.recv(4096).decode()
        message = json.loads(raw)

        user_id = message.get("user_id", "").strip()

        if not user_id:
            response = {"status": "ERROR", "reason": "No user ID provided."}
        else:
            print(f"[BROKER] Processing booking for: {user_id}")
            response = handle_booking(user_id)

        connection.send(json.dumps(response).encode())
        print(f"[BROKER] Response sent: {response['status']}")

    except Exception as e:
        print(f"[BROKER] Error: {e}")
        error = {"status": "ERROR", "reason": str(e)}
        connection.send(json.dumps(error).encode())

    finally:
        connection.close()


# ── Start Broker Server ───────────────────────────────────────
def start_broker(port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", port))
    server.listen(10)

    print("=" * 50)
    print("  FairRide — Broker Server Started")
    print("=" * 50)
    print(f"  Listening on port : {port}")
    print(f"  Threshold (k)     : {K}")
    print(f"  Total nodes (n)   : {N}")
    print(f"  Node ports        : 9001, 9002, 9003")
    print("=" * 50)
    print("  Waiting for booking requests...\n")

    while True:
        connection, address = server.accept()
        thread = threading.Thread(
            target=handle_client,
            args=(connection, address)
        )
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    start_broker(9000)