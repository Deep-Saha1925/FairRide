# 🚌 FairRide

### Distributed Group Authentication System for Women's Free Bus Booking
**Powered by Shamir's Secret Sharing & Lagrange Interpolation**

---

## 📌 Overview

FairRide is a privacy-preserving, distributed authentication system built for the **NBSTC Women's Free Bus Travel Scheme**. It ensures that:

- Each eligible woman can book a **maximum of 2 free tickets**
- No single server ever holds her **complete identity**
- The system remains secure even if **one node is compromised**

This project demonstrates the real-world application of **threshold cryptography** in a multi-client socket environment.

---

## 🧠 Core Concepts

| Concept | Role in FairRide |
|---|---|
| **Shamir's Secret Sharing** | Splits user identity into `n` shares |
| **Lagrange Interpolation** | Reconstructs the secret from `k` shares |
| **Socket Programming** | Real-time communication between clients, broker, and nodes |
| **Threshold Scheme (k-of-n)** | Any 2-of-3 nodes can reconstruct the identity |
| **Modular Arithmetic** | All crypto operations done in a prime field for security |

---

## 🏗️ Architecture

```
        Woman (Client)
              │
              │  "Book ticket for PRIYA_W1234"
              ▼
      ┌───────────────┐
      │    BROKER     │  ← Port 9000 (Central Hub)
      │  (Port 9000)  │
      └──────┬────────┘
             │  Splits identity into 3 shares
     ┌───────┼───────┐
     ▼       ▼       ▼
  Node 1   Node 2   Node 3
 (9001)   (9002)   (9003)
  Share1   Share2   Share3

Broker collects any 2-of-3 shares → Lagrange Interpolation → Verify Identity
```

---

## 📁 Project Structure

```
FairRide/
├── crypto/
│   ├── shamir.py          # Shamir's Secret Sharing (split + reconstruct)
│   └── lagrange.py        # Lagrange Interpolation (math engine)
├── server/
│   ├── broker.py          # Central broker (booking manager)
│   └── node.py            # Auth node (holds one share)
├── client/
│   └── client.py          # Woman's booking client
├── test_fairride.py       # Automated integration tests
└── README.md
```

---

## ⚙️ Requirements

- Python 3.7+
- No external libraries needed — uses only Python standard library!

---

## 🚀 How to Run

You need **5 terminals** open simultaneously.

### Terminal 1 — Start Node 1
```bash
cd FairRide/server
python node.py 9001
```

### Terminal 2 — Start Node 2
```bash
cd FairRide/server
python node.py 9002
```

### Terminal 3 — Start Node 3
```bash
cd FairRide/server
python node.py 9003
```

### Terminal 4 — Start Broker
```bash
cd FairRide/server
python broker.py
```

### Terminal 5 — Run Client
```bash
cd FairRide/client
python client.py
```

---

## 🧪 Run Automated Tests

To test everything automatically (no manual terminals needed):

```bash
cd FairRide
PYTHONPATH=client:server:crypto python test_fairride.py
```

### Expected Output:
```
✅ Test 1: First booking       → CONFIRMED
✅ Test 2: Second booking      → CONFIRMED
✅ Test 3: Third booking       → REJECTED (limit enforced)
✅ Test 4: Different user      → CONFIRMED

🎉 ALL TESTS PASSED! FairRide is working!
```

---

## 🔐 How the Security Works

### Step 1 — Identity to Secret
```
User ID: "PRIYA_W1234"
    ↓ SHA-256 Hash
Secret: 84328535804324... (large number in prime field)
```

### Step 2 — Secret Splitting (Shamir SSS)
```
f(x) = Secret + a₁x    (random polynomial, degree k-1)

Share 1 → f(1) → sent to Node 9001
Share 2 → f(2) → sent to Node 9002
Share 3 → f(3) → sent to Node 9003
```

### Step 3 — Reconstruction (Lagrange Interpolation)
```
Collect any 2 shares → Lagrange at x=0 → Recover Secret
Compare with expected hash → ✅ Authenticated!
```

### Step 4 — Booking Limit
```
booking_db["PRIYA_W1234"] = 0  → +1 → +1 → REJECTED (≥ 2)
```

---

## 🛡️ Security Properties

| Property | Description |
|---|---|
| **Privacy** | No single node knows the full identity |
| **Threshold Security** | Attacker needs k nodes to learn anything |
| **Information-Theoretic** | Below threshold, zero information is leaked |
| **Fault Tolerance** | System works even if 1 node is down (k=2 of n=3) |

---

## 📡 Message Protocol

All communication uses JSON over TCP sockets.

### Client → Broker
```json
{ "type": "BOOK_REQUEST", "user_id": "PRIYA_W1234" }
```

### Broker → Node (Store)
```json
{ "type": "STORE_SHARE", "user_id": "PRIYA_W1234", "share": [1, 139599...] }
```

### Broker → Node (Fetch)
```json
{ "type": "GET_SHARE", "user_id": "PRIYA_W1234" }
```

### Broker → Client (Response)
```json
{ "status": "CONFIRMED", "message": "Booking confirmed! You have used 1/2 bookings." }
{ "status": "REJECTED",  "reason": "Booking limit reached! (max 2)" }
{ "status": "ERROR",     "reason": "Authentication failed." }
```

---

## 👩‍💻 Authors

Built as a college project demonstrating applied cryptography in public transport systems.

**Technologies:** Python · Socket Programming · Shamir's Secret Sharing · Lagrange Interpolation · Threshold Cryptography

---

## 📚 References

- Shamir, A. (1979). *How to share a secret*. Communications of the ACM.
- NBSTC Women's Free Travel Scheme, West Bengal
- Lagrange Interpolation — Numerical Methods