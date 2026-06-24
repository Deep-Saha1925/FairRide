# ============================================================
# FairRide Project — shamir.py
# Purpose: Split a secret into n shares using Shamir's SSS
# ============================================================

import random
from lagrange import lagrange_interpolation, PRIME


def generate_coefficients(secret, k, prime=PRIME):
    """
    Build a random polynomial of degree (k-1) with secret as f(0).

    f(x) = secret + a1*x + a2*x^2 + ... + a(k-1)*x^(k-1)

    Parameters:
        secret : the number we want to hide (integer)
        k      : threshold — minimum shares needed to reconstruct
        prime  : prime field

    Returns:
        coefficients : list where coefficients[0] = secret
    """
    coefficients = [secret]  # f(0) = secret is always the first coefficient

    # Generate k-1 random coefficients for x, x^2, ..., x^(k-1)
    for _ in range(k - 1):
        coefficients.append(random.randrange(1, prime))

    return coefficients


def evaluate_polynomial(coefficients, x, prime=PRIME):
    """
    Evaluate the polynomial at a given x using Horner's method.

    Normal way:  f(x) = a0 + a1*x + a2*x^2 + a3*x^3
    Horner's way: f(x) = a0 + x*(a1 + x*(a2 + x*a3))

    Horner's method is faster and more efficient.

    Parameters:
        coefficients : list of polynomial coefficients
        x            : the point to evaluate at
        prime        : prime field

    Returns:
        result : f(x) mod prime
    """
    result = 0

    # Traverse coefficients from highest degree to lowest (Horner's method)
    for coefficient in reversed(coefficients):
        result = (result * x + coefficient) % prime

    return result


def split_secret(secret, k, n, prime=PRIME):
    """
    Split a secret into n shares with threshold k.

    Parameters:
        secret : the secret number to hide
        k      : minimum shares needed to reconstruct (threshold)
        n      : total number of shares to generate
        prime  : prime field

    Returns:
        shares : list of n tuples [(1, f(1)), (2, f(2)), ..., (n, f(n))]

    IMPORTANT:
        - k <= n always
        - secret < prime always
        - x values start from 1 (never 0, because f(0) IS the secret!)
    """
    if k > n:
        raise ValueError(f"Threshold k={k} cannot be greater than total shares n={n}")

    if secret >= prime:
        raise ValueError("Secret must be smaller than the prime field")

    # Step 1: Generate random polynomial with secret as f(0)
    coefficients = generate_coefficients(secret, k, prime)

    # Step 2: Evaluate polynomial at x = 1, 2, 3, ..., n
    shares = []
    for x in range(1, n + 1):
        y = evaluate_polynomial(coefficients, x, prime)
        shares.append((x, y))

    return shares


def reconstruct_secret(shares, prime=PRIME):
    """
    Reconstruct the secret from k (or more) shares.

    Simply calls Lagrange Interpolation at x=0.

    Parameters:
        shares : list of at least k tuples [(x1,y1), (x2,y2), ...]
        prime  : prime field

    Returns:
        secret : the reconstructed secret
    """
    return lagrange_interpolation(shares, prime)


# ============================================================
# QUICK TEST — Run this file directly to verify
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  FairRide — Shamir Secret Sharing Test")
    print("=" * 50)

    # --- Test 1: Basic 2-of-3 scheme ---
    SECRET = 7
    K = 2  # Minimum shares needed
    N = 3  # Total shares

    print(f"\n[Test 1] Secret={SECRET}, k={K}, n={N}")
    shares = split_secret(SECRET, K, N)
    print(f"All shares generated : {shares}")

    # Reconstruct using only 2 shares
    recovered = reconstruct_secret(shares[:2])
    print(f"Reconstructed secret : {recovered}")
    print(f"Test passed          : {recovered == SECRET} ✅" if recovered == SECRET else "Test FAILED ❌")

    # --- Test 2: Real user token (larger number) ---
    import hashlib
    user_id   = "PRIYA_W1234"
    token     = int(hashlib.sha256(user_id.encode()).hexdigest(), 16) % PRIME

    print(f"\n[Test 2] User ID = {user_id}")
    print(f"Token (hashed)       : {token}")

    shares2   = split_secret(token, K, N)
    recovered2 = reconstruct_secret(shares2[:2])

    print(f"Reconstructed token  : {recovered2}")
    print(f"Test passed          : {recovered2 == token} ✅" if recovered2 == token else "Test FAILED ❌")

    # --- Test 3: Verify that k-1 shares reveal NOTHING ---
    print(f"\n[Test 3] Using only 1 share (below threshold)...")
    wrong = reconstruct_secret(shares[:1])  # Only 1 share — should be WRONG
    print(f"Result with 1 share  : {wrong}")
    print(f"Is it the secret?    : {wrong == SECRET} (should be False ✅)")