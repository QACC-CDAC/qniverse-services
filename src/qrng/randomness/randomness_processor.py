# coding: utf-8
"""
Randomness Post-Processing
==========================

This module provides algorithms for post-processing raw bitstrings to improve their entropy.
Supported Algorithms:
- Toeplitz Hashing
- Von Neumann Extraction
- XOR Extraction
- Polynomial Hashing (Universal Hash)
"""
import argparse
import sys
import re
import numpy as np

# Import mixers/extractors
from .toeplitz_mixer import Toeplitz
from .polynomial_mixer import UniversalHash
from .von_neumann_extractor import VonNeumann
from .xor_mixer import XOR_Extraction

from src.utils.logger import logger
# from toeplitz_mixer import Toeplitz
# from polynomial_mixer import UniversalHash
# from von_neumann_extractor import VonNeumann
# from xor_mixer import XOR_Extraction

# Define available algorithms
MIXER_MAP = {
    "toeplitz": Toeplitz,
    "polynomial": UniversalHash,
    "von_neumann": VonNeumann,
    "xor": XOR_Extraction,
    # "none": None
}

ALLOWED_ALGORITHMS = list(MIXER_MAP.keys())

def bitstring_to_bytes(s: str) -> bytes:
    """Convert a bitstring to bytes."""
    return int(s, 2).to_bytes((len(s) + 7) // 8, byteorder='big')

def bytes_to_bitstring(b: bytes) -> str:
    """Convert bytes to a bitstring."""
    return ''.join(f'{byte:08b}' for byte in b)

import json

def validate_input_bits(s: str):
    """
    Validate input bits. Raises ValueError if invalid.
    """
    if not isinstance(s, str):
         raise ValueError("Input must be a string.")

    # Check invalid characters first
    if not all(c in '01' for c in s):
        raise ValueError("Input contains invalid characters (only '0' and '1' allowed).")

    return

def generate_bit_string(length):
    """
    Generates a highly optimized biased bit string using NumPy ASCII manipulation.
    """

    probability_of_one = 0.52
    # 1. Generate random floats and compare to probability (creates Booleans: True/False)
    # 2. Cast to 8-bit integers (0 or 1)
    # 3. Add 48 to shift to ASCII decimal values (48='0', 49='1')
    ascii_bytes = (np.random.random(length) < probability_of_one).astype(np.uint8) + 48
    
    # 4. Convert the raw memory block to bytes, then decode to a Python string
    return ascii_bytes.tobytes().decode('ascii')




def process_bitstring(input_bits: str, postprocessing: str, abort_event=None) -> str:
    """
    Process input bits using the specified post-processing algorithm.

    Args:
        input_bits (str): Input string of '0's and '1's.
        postprocessing (str): Name of the algorithm ('toeplitz', 'polynomial', 'von_neumann', 'xor', 'none').
        abort_event (threading.Event, optional): Event to signal cancellation.

    Returns:
        str: Processed bitstring, or empty string if input is too short.
        Raises: ValueError, RuntimeError for other errors.
    """
    # 1. Clean Input (remove whitespace)
    input_bits = re.sub(r'\s+', '', input_bits)

    # 2. Validation
    validate_input_bits(input_bits)

    # Check length (64 bytes = 512 bits)
    if len(input_bits) < 512:
        return ""

        # 3. Handle 'none' case
    if postprocessing == None:
        # Return full bytes only
        usable_bits = (len(input_bits) // 8) * 8
        return input_bits[:usable_bits]
    
    
    # 2. Map algorithm
    if postprocessing not in MIXER_MAP:
        raise ValueError(f"Unknown post-processing algorithm. Allowed: {ALLOWED_ALGORITHMS}")



    mixer_func = MIXER_MAP[postprocessing]

    # 4. Padding/Truncation for Byte Conversion
    usable_bits = (len(input_bits) // 8) * 8
    # validation above ensures >= 512 bits

    input_bytes = bitstring_to_bytes(input_bits[:usable_bits])

    # 5. Handle Specific Mixer Requirements
    if postprocessing in ["toeplitz", "polynomial", "xor"]:
        usable_len = (len(input_bytes) // 64) * 64
        if usable_len == 0:
             return ""
        input_to_process = input_bytes[:usable_len]
    else:
        input_to_process = input_bytes

    # 6. Execute Mixer
    try:
        output_bytes = mixer_func(input_to_process, abort_event=abort_event)
        if abort_event and abort_event.is_set():
            return ""
    except Exception as e:
        raise RuntimeError(f"Processing failed: {str(e)}")

    # 7. Convert back to Bitstring
    return bytes_to_bitstring(output_bytes)

def generateQRNG(length: int, postprocessing: str) -> dict:
    """
    Run the processor and return the result as a dictionary.

    Args:
        input_bits (str): Input string of '0's and '1's.
        postprocessing (str): Name of the algorithm.

    Returns:
        dict: Result dictionary with 'status' and 'output_bits' or 'error'.
    """
    try:
        input_bits = generate_bit_string(length)
        result = process_bitstring(input_bits, postprocessing)
        return result
    except Exception as e:
        raise "Unable to generate QRNG."
    
    

        
        

