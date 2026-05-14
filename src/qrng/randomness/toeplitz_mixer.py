from .generator import HMAC_DRBG

def Toeplitz(input_bytes, abort_event=None):
    """
    Extract randomness from input_bytes using Toeplitz hashing.

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

    # Process input in 16-byte (128-bit) chunks
    # We process ALL input bytes, as requested, to avoid wastage.
    chunk_size = 16
    for i in range(0, len(input_bytes), chunk_size):
        if abort_event and abort_event.is_set():
            return b""
        chunk = input_bytes[i:i + chunk_size]

        # Generator random key of 32 bytes (256 bits)
        # 128 bits for input + 128 bits for shift = 256 bits needed for Toeplitz matrix
        key_bytes = drbg.randbytes(32)

        chunk_int = int.from_bytes(chunk, 'big')
        key_int = int.from_bytes(key_bytes, 'big')

        # Toeplitz Hash: Matrix-vector multiplication equivalent
        # In bitwise terms: Accumulate shifted versions of the key based on input bits.
        # We need to produce 128 bits of output.
        # The key is 256 bits.
        # Input bit j (from 0 to 127) selects a 128-bit window of Key starting at output index.

        result_int = 0
        # Iterate over 128 bits of the chunk
        for j in range(128):
            # Check if j-th bit of input is set
            # We treat bit 0 as MSB or LSB? Standard convention:
            # If we view input as vector [x0, x1, ...], x0 is usually MSB of integer.
            # key window: [k0, k1, ..., k127] for x0
            # [k1, k2, ..., k128] for x1

            # Let's align with big-endian integer:
            # bit 127 is LSB, bit 0 (conceptually) is MSB.
            # (chunk_int >> (127 - j)) & 1 checks bit j from MSB.

            if (chunk_int >> j) & 1:
                # XOR with a 128-bit window of key
                # We want 128 bits. The key is 256 bits.
                # Which window?
                # If we align LSBs:
                # key_int has 256 bits.
                # We want result to have 128 bits.
                # For LSB of input (j=0), we might want the lower 128 bits of key.
                # For bit 1, we want key shifted by 1.

                # Let's standardize:
                # result ^= (key_int >> j) & ((1 << 128) - 1)

                # If j=0 (LSB of input), we take lowest 128 bits of key.
                # If j=1, we take bits 1..129

                result_int ^= (key_int >> j)

        # Mask result to 128 bits (16 bytes)
        result_int &= ((1 << 128) - 1)

        output_chunks.append(result_int.to_bytes(16, 'big'))

    return b"".join(output_chunks)
