from .generator import HMAC_DRBG

def XOR_Extraction(input_bytes, abort_event=None):
    """
    Extract randomness from input_bytes by XORing with a DRBG stream.

    Args:
        input_bytes (bytes): Input data. Must be a multiple of 64 bytes (512 bits).
        abort_event (threading.Event, optional): Event to signal cancellation.

    Returns:
        bytes: Extracted randomness (same length as input).
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

    # Process input in chunks to avoid generator limit (7500 bits / ~937 bytes)
    # We use 64 bytes (512 bits) as the chunk size, matching the minimum input size.
    chunk_size = 64
    output_chunks = []

    for i in range(0, len(input_bytes), chunk_size):
        if abort_event and abort_event.is_set():
            return b""
        chunk = input_bytes[i:i + chunk_size]
        current_chunk_size = len(chunk)

        # Generate random bytes for this chunk
        mask_bytes = drbg.randbytes(current_chunk_size)

        chunk_int = int.from_bytes(chunk, 'big')
        mask_int = int.from_bytes(mask_bytes, 'big')

        result_int = chunk_int ^ mask_int
        output_chunks.append(result_int.to_bytes(current_chunk_size, 'big'))

    return b"".join(output_chunks)
