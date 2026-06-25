# ============================================================
# FairRide Project — node.py
# Purpose: Authentication Node Server
#          Each node holds ONE share of the user's secret.
#          Broker contacts nodes to collect shares.
# ============================================================

import socket       # For network communication
import json         # For message formatting
import sys          # For reading command line arguments
import threading    # For handling multiple broker requests

# ---- Node Storage ----
# In a real system this would be a database
# For now: { user_id : share_value }
share_storage = {}


def handle_broker(connection, address):
    """
    Handle a single request from the Broker.

    The broker can send 2 types of requests:
    1. STORE_SHARE  → Store a share for a user
    2. GET_SHARE    → Return the stored share for a user
    """
    print(f"  [NODE] Broker connected from {address}")

    try:
        # --- Receive message from broker ---
        raw = connection.recv(4096).decode()
        message = json.loads(raw)

        msg_type = message.get("type")
        user_id  = message.get("user_id")

        # ── Request Type 1: STORE_SHARE ──────────────────────
        if msg_type == "STORE_SHARE":
            share = message.get("share")  # (x, y) tuple
            share_storage[user_id] = share

            print(f"  [NODE] Stored share for user: {user_id}")
            response = {
                "status": "OK",
                "message": "Share stored successfully"
            }

        # ── Request Type 2: GET_SHARE ─────────────────────────
        elif msg_type == "GET_SHARE":
            if user_id in share_storage:
                share = share_storage[user_id]
                print(f"  [NODE] Sending share for user: {user_id}")
                response = {
                    "status": "OK",
                    "share": share  # Send back (x, y)
                }
            else:
                print(f"  [NODE] Share NOT found for user: {user_id}")
                response = {
                    "status": "ERROR",
                    "message": "Share not found"
                }

        # ── Unknown Request ───────────────────────────────────
        else:
            response = {
                "status": "ERROR",
                "message": f"Unknown message type: {msg_type}"
            }

        # --- Send response back to broker ---
        connection.send(json.dumps(response).encode())

    except Exception as e:
        print(f"  [NODE] Error handling broker: {e}")
        error_response = {"status": "ERROR", "message": str(e)}
        connection.send(json.dumps(error_response).encode())

    finally:
        connection.close()


def start_node(port):
    """
    Start the node server on the given port.
    Listens forever for broker connections.
    """
    # Step 1: Create a TCP socket
    # AF_INET     = IPv4 addressing
    # SOCK_STREAM = TCP (reliable, ordered delivery)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Step 2: Allow reuse of port (avoids "address already in use" errors)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Step 3: Bind to localhost on the given port
    server.bind(("localhost", port))

    # Step 4: Start listening (max 5 queued connections)
    server.listen(5)

    print(f"[NODE] Auth Node started on port {port} ✅")
    print(f"[NODE] Waiting for broker connections...\n")

    # Step 5: Accept connections forever in a loop
    while True:
        connection, address = server.accept()

        # Handle each broker request in a separate thread
        # This allows multiple requests at the same time
        thread = threading.Thread(
            target=handle_broker,
            args=(connection, address)
        )
        thread.daemon = True
        thread.start()


# ============================================================
# ENTRY POINT
# Run as: python node.py 9001
#         python node.py 9002
#         python node.py 9003
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python node.py <port>")
        print("Example: python node.py 9001")
        sys.exit(1)

    port = int(sys.argv[1])
    start_node(port)