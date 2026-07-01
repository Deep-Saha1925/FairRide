# ============================================================
# FairRide Project — client.py
# Purpose: Woman's booking client
#          Connects to broker and requests a free bus ticket
# ============================================================

import socket
import json


BROKER_HOST = "localhost"
BROKER_PORT = 9000


def send_booking_request(user_id):
    """
    Send a booking request to the broker and return response.

    Parameters:
        user_id : the woman's ID (e.g., Aadhaar number or token)

    Returns:
        response dict from broker
    """
    try:
        # Step 1: Create a TCP socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)

        # Step 2: Connect to broker
        client.connect((BROKER_HOST, BROKER_PORT))

        # Step 3: Send booking request as JSON
        message = {
            "type": "BOOK_REQUEST",
            "user_id": user_id
        }
        client.send(json.dumps(message).encode())

        # Step 4: Wait for response
        raw = client.recv(4096).decode()
        response = json.loads(raw)

        client.close()
        return response

    except ConnectionRefusedError:
        return {
            "status": "ERROR",
            "reason": "Could not connect to broker. Is it running on port 9000?"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "reason": str(e)
        }


def print_response(response):
    """Pretty print the broker's response."""
    status = response.get("status")

    print("\n" + "=" * 45)
    if status == "CONFIRMED":
        print("  BOOKING CONFIRMED!")
        print(f"  {response.get('message')}")
    elif status == "REJECTED":
        print("  BOOKING REJECTED!")
        print(f"  Reason: {response.get('reason')}")
    else:
        print("  ERROR!")
        print(f"  Reason: {response.get('reason')}")
    print("=" * 45 + "\n")


def run_client():
    """Interactive client — prompts user for ID and books ticket."""
    print("\n" + "=" * 45)
    print("   Welcome to FairRide")
    print("   Free Women's Bus Booking System")
    print("   Powered by Shamir's Secret Sharing")
    print("=" * 45)

    while True:
        print("\nOptions:")
        print("  1. Book a ticket")
        print("  2. Exit")

        choice = input("\nEnter choice (1/2): ").strip()

        if choice == "2":
            print("\nThank you for using FairRide!\n")
            break

        elif choice == "1":
            user_id = input("Enter your ID (e.g., PRIYA_W1234): ").strip()

            if not user_id:
                print("Please enter a valid ID.")
                continue

            print(f"\n[CLIENT] Sending booking request for: {user_id}")
            print("[CLIENT] Connecting to broker...")

            response = send_booking_request(user_id)
            print_response(response)

        else:
            print("Invalid choice. Enter 1 or 2.")


if __name__ == "__main__":
    run_client()