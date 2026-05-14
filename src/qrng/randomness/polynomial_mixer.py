from .generator import HMAC_DRBG

def UniversalHash(input_bytes, abort_event=None):
    """
    Extract randomness from input_bytes using Universal Hashing (Polynomial Hash).

    Args:
        input_bytes (bytes): Input data. Must be a multiple of 64 bytes (512 bits).
        abort_event (threading.Event, optional): Event to signal cancellation.

    Returns:
        bytes: Extracted randomness.
    """
    if len(input_bytes) < 64:
        raise ValueError("Input length must be at least 64 bytes.")

    if len(input_bytes) % 64 != 0:
        raise ValueError("Input length must be a multiple of 64 bytes (512 bits).")

    # 1. Use first 48 bytes (384 bits) as seed for DRBG
    seed_bytes = input_bytes[:48]
    seed_int = int.from_bytes(seed_bytes, 'big')

    # Initialize DRBG
    # drbg = HMAC_DRBG(seed=seed_int)
    drbg = HMAC_DRBG()

    output_chunks = []

    # Prime for GF(2^128) arithmetic could be 2^128 - 159 (largest 128-bit prime)
    # However, for simplicity and speed in Python, we can work modulo 2^128 (no bias if input is uniform,
    # but strictly speaking universal hashing usually wants a prime field).
    # Given the context of "randomness extraction" where we want to mix bits,
    # using a large prime is better to avoid algebraic attacks or patterns.
    # Largest prime less than 2^128 is 2^128 - 159.
    P = (1 << 128) - 159

    # Process input in 16-byte (128-bit) chunks
    chunk_size = 16
    for i in range(0, len(input_bytes), chunk_size):
        if abort_event and abort_event.is_set():
            return b""
        chunk = input_bytes[i:i + chunk_size]

        # Generator random a and b coefficients (16 bytes each)
        a_bytes = drbg.randbytes(16)
        b_bytes = drbg.randbytes(16)

        m_int = int.from_bytes(chunk, 'big')
        a_int = int.from_bytes(a_bytes, 'big')
        b_int = int.from_bytes(b_bytes, 'big')

        # Ensure a is not 0 mod P, otherwise H(m) = b for all m, losing all entropy.
        if a_int % P == 0:
            a_int = 1

        # Polynomial Hash: H(m) = (a*m + b) mod p
        # We also mod 2^128 at the end to fit into 16 bytes if p < 2^128 (which it is).

        h_int = ((a_int * m_int) + b_int) % P

        output_chunks.append(h_int.to_bytes(16, 'big'))

    return b"".join(output_chunks)
