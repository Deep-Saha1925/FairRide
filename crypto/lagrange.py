# ============================================================
# FairRide Project — lagrange.py
# Purpose: Reconstruct the secret using Lagrange Interpolation
# ============================================================
 
PRIME = 208351617316091241234326746312124448251235562226470491514186331217050270460481

def mod_inverse(a, p):
    """
    Calculate modular inverse of a under prime p.
    i.e., find x such that (a * x) % p == 1
 
    We use Fermat's Little Theorem:
        a^(p-1) ≡ 1 (mod p)
        => a^(p-2) ≡ a^(-1) (mod p)
 
    This works because p is PRIME.
    """

    return pow(a, p-2, p)

def lagrange_interpolation(shares, prime=PRIME):
    """
    Reconstruct the secret from k shares using Lagrange Interpolation.
 
    Parameters:
        shares : list of tuples → [(x1,y1), (x2,y2), ...]
        prime  : the prime field we are working in
 
    Returns:
        secret : the reconstructed secret (integer)
 
    HOW IT WORKS:
    -------------
    For each share (xi, yi), we compute a basis polynomial Li(0):
 
        Li(0) = ∏  (0 - xj) / (xi - xj)   for all j ≠ i
 
    Then the secret is:
        f(0) = Σ yi * Li(0)   (mod prime)
    """
     
    secret = 0

    for i, (xi, yi) in enumerate(shares):

        # --- Step 1: Calculate the Lagrange basis Li(0) ---
        numerator = 1
        denominator = 1

        for j, (xj, yj) in enumerate(shares):
            if i == j:
                continue

            numerator = (numerator * (0 - xj)) % prime
            denominator = (denominator * (xi - xj)) % prime

        # --- Step 2: Li(0) = numerator / denominator (mod prime) ---
        lagrange_basis = (numerator * mod_inverse(denominator, prime)) % prime

        # STEP 3: Add yi * Li(0) to the secret
        secret = (secret + yi * lagrange_basis) % prime

    return secret

if __name__ == "__main__":
    print("=" * 60)
    print("  FairRide — Lagrange Interpolation Test")
    print("=" * 60)

    # f(x) = 7 + 3x
    # Shares: (1,10), (2,13), (3,16)
    # Secret should be f(0) = 7

    test_shares = [(1, 10), (2, 13)]  # Using only 2 of 3 shares

    result = lagrange_interpolation(test_shares, prime=PRIME)
    print(f"\nShares used     : {test_shares}")
    print(f"Reconstructed   : {result}")
    print(f"Expected secret : 7")
    print(f"Test passed     : {result == 7} " if result == 7 else "Test FAILED ")
