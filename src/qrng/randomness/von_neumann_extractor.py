def VonNeumann(input_bytes, abort_event=None):
    """
    Extract randomness from input_bytes using Von Neumann corrector.

    Pairs of bits are processed:
    - 01 -> Output 1
    - 10 -> Output 0
    - 00 -> Discard
    - 11 -> Discard

    Args:
        input_bytes (bytes): Input data.
        abort_event (threading.Event, optional): Event to signal cancellation.

    Returns:
        bytes: Extracted randomness. Length will vary (approx 25% of input bits if input is unbiased, but could be 0).
    """
    output_bits = []

    for byte in input_bytes:
        if abort_event and abort_event.is_set():
            return b""
        # Process 4 pairs of bits per byte
        # Pairs: (7,6), (5,4), (3,2), (1,0)
        for i in range(3, -1, -1):
            pair = (byte >> (2 * i)) & 3

            # 00 -> 0, 01 -> 1, 10 -> 2, 11 -> 3

            if pair == 1:   # 01
                output_bits.append(1)
            elif pair == 2: # 10
                output_bits.append(0)
            # else 00 or 11, discard

    # Pack bits into bytes
    output_bytes = bytearray()
    current_byte = 0
    bits_collected = 0

    for bit in output_bits:
        current_byte = (current_byte << 1) | bit
        bits_collected += 1

        if bits_collected == 8:
            output_bytes.append(current_byte)
            current_byte = 0
            bits_collected = 0

    # Note: Remaining bits < 8 are discarded as we can only return full bytes

    return bytes(output_bytes)
