# --- Standard Library ---
import os
import hmac
import hashlib
from decimal import Decimal, getcontext

# Set precision high enough (20 digits for 64-bit fractions)
getcontext().prec = 20

# Implements an HMAC_DRBG (NIST SP 800-90A) based on HMAC_SHA256.
# Supports security strengths up to 256 bits.
# Parameters are based on recommendations provided by Appendix D of NIST SP 800-90A.
class HMAC_DRBG(object):
    """
    Implements an HMAC_DRBG (Detector Reliability Based Generator) as specified in NIST SP 800-90A.

    This implementation uses HMAC-SHA256 as the underlying primitive.
    """
    def __init__(self, seed=None):
        """
        Initialize the HMAC_DRBG instance.

        Args:
            seed (int): Optional integer seed. If None, uses os.urandom(48).

        Raises:
            RuntimeError: If os.urandom fails.
            ValueError: If seed is too large to fit in 384 bits.
        """
        self._security_strength = 256
        self._seed = seed
        self._reseed_window_width = 1
        self._reseed_bit_offset = 0

        entropy = self._get_entropy_input()
        self._instantiate(entropy, b"")

    def _get_entropy_input(self):
        """
        Helper to get 384 bits (48 bytes) of entropy based on initialization mode.
        """
        if self._seed is None:
            # Use os.urandom if no seed provided
            try:
                return os.urandom(48)
            except NotImplementedError:
                raise RuntimeError("os.urandom not available or failed to providing entropy.")
        else:
            # Convert int seed to 48 bytes (384 bits)
            try:
                return self._seed.to_bytes(48, 'big')
            except OverflowError:
                 raise ValueError("Seed is too large to fit in 384 bits.")

    def _get_reseed_entropy(self):
        """
        Get entropy for reseeding.
        If initial seed was provided, use sliding window bit-flip on original seed.
        If no initial seed, use os.urandom.
        """
        if self._seed is None:
            try:
                return os.urandom(48)
            except NotImplementedError:
                raise RuntimeError("os.urandom not available or failed to provide reseed entropy.")

        # Sliding window bit-flip logic
        # 1. Calculate mask
        # Create a mask of 'window_width' 1s
        base_mask = (1 << self._reseed_window_width) - 1
        # Shift it to the current offset
        mask = base_mask << self._reseed_bit_offset

        # 2. Apply mask to original seed
        new_seed_int = self._seed ^ mask

        # 3. Update state for next call
        self._reseed_bit_offset += 1

        # Check if window has reached the end (384 bits)
        if self._reseed_bit_offset + self._reseed_window_width > 384:
            self._reseed_window_width += 1
            self._reseed_bit_offset = 0

        # Check if window width has exceeded 384
        if self._reseed_window_width > 384:
            self._reseed_window_width = 1
            self._reseed_bit_offset = 0

        try:
            return new_seed_int.to_bytes(48, 'big')
        except OverflowError:
             raise ValueError("Generated reseed value logic error: value exceeds 384 bits.")

    def _hmac(self, key, data):
        return hmac.new(key, data, hashlib.sha256).digest()

    def _update(self, provided_data=None):
        """
        Update the internal state (K, V) using the provided data.
        """
        self._K = self._hmac(self._K, self._V + b"\x00" + (b"" if provided_data is None else provided_data))
        self._V = self._hmac(self._K, self._V)

        if provided_data is not None:
            self._K = self._hmac(self._K, self._V + b"\x01" + provided_data)
            self._V = self._hmac(self._K, self._V)

    def _instantiate(self, entropy, personalization_string):
        """
        Instantiate the DRBG internal state.
        """
        seed_material = entropy + personalization_string
        self._K = b"\x00" * 32
        self._V = b"\x01" * 32
        self._update(seed_material)
        self._reseed_counter = 1

    def reseed(self):
        """
        Reseed the DRBG with new entropy.
        Uses the original seed (if provided) or new random data from os.urandom.
        """
        entropy = self._get_reseed_entropy()
        self._update(entropy)
        self._reseed_counter = 1

    def generate(self, num_bytes):
        """
        Generate random bytes.

        Args:
            num_bytes (int): Number of bytes to generate.

        Returns:
            bytes: Generated random bytes.

        Raises:
            RuntimeError: If request exceeds limits.
        """
        if (num_bytes * 8) > 7500:
            raise RuntimeError("generate cannot generate more than 7500 bits in a single call.")

        # Auto-reseed if counter threshold reached
        if self._reseed_counter >= 10000:
            self.reseed()

        temp = b""
        while len(temp) < num_bytes:
            self._V = self._hmac(self._K, self._V)
            temp += self._V

        self._update(None)
        self._reseed_counter += 1
        return temp[:num_bytes]

    def random(self):
        """
        Return the next random floating point number in the range [0.0, 1.0).
        Uses 53 bits of randomness.
        """
        # Generate 7 bytes (56 bits) to ensure we have enough for 53 bits
        random_bytes = self.generate(7)

        # Convert to integer
        random_int = int.from_bytes(random_bytes, 'big')

        # Keep top 53 bits
        random_int >>= 3

        # Divide by 2^53
        return random_int * (2**-53)

    def randint(self, a, b):
        """
        Return a random integer N such that a <= N <= b.
        Alias for randrange(a, b+1).
        """
        return self._randrange(a, b + 1)

    def _randrange(self, start, stop=None, step=1):
        """
        Choose a random item from range(start, stop[, step]).
        This fixes the problem with randint() which includes the endpoint; in Python
        random.randrange(start, stop) excludes the endpoint.
        """
        if stop is None:
            stop = start
            start = 0

        width = stop - start
        if step == 1 and width > 0:
            # Rejection sampling
            # Get bit length of width
            n = width
            k = n.bit_length()
            num_bytes = (k + 7) // 8

            while True:
                r_bytes = self.generate(num_bytes)

                r = int.from_bytes(r_bytes, 'big')

                # Mask out extra bits
                r >>= (num_bytes * 8 - k)

                if r < width:
                    return start + r

        raise ValueError("empty range for randrange() or step != 1 (not implemented yet)")

    def randbytes(self, n):
        """
        Generate n random bytes.
        """
        return self.generate(n)
