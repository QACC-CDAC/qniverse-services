"""QRNG service for generating quantum random numbers"""

from typing import Dict, Any, List, Optional

from datetime import datetime
from pathlib import Path
import json

from src.utils.logger import logger
from src.config import get_settings
from src.core.exceptions import ValidationError, QRNGError
from src.models import PostProcessingMethod
from src.qrng.randomness.randomness_processor import generateQRNG


settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "qrng" / "cloudqrng" / "data"

FILES = [
    DATA_DIR / "bit_1.txt",
    DATA_DIR / "bit_2.txt",
    DATA_DIR / "bit_3.txt",
    DATA_DIR / "bit_4.txt",
    DATA_DIR / "bit_5.txt",
]

STATE_FILE = DATA_DIR / "state.json"


class QRNGService:
    """Service for generating quantum random numbers"""
    
    def generate_random_numbers(self, count: int, post_processing: Optional[PostProcessingMethod] = None) -> Dict[str, Any]:
        """Generate quantum random numbers using the QRNG API"""
        if count <= 512:
            raise ValidationError("Count must be greater than 512")
        
        # Simulate QRNG API call (replace with actual API integration)
        try:
            # Here you would integrate with the actual QRNG API
            # For demonstration, we will generate random numbers using Python's random module
            random_numbers = generateQRNG(length=count, postprocessing=post_processing)
            logger.info(f"info  before: {post_processing}")  

            new_post_processing = "none" if post_processing == None else post_processing
            return {"random_numbers": random_numbers, "count": count, "post_processing": new_post_processing}
        except Exception as e:
            logger.error(f"Failed to generate random numbers: {str(e)} {post_processing}")
            raise QRNGError("Failed to generate random numbers") from e
    
    def load_state(self):

        if not STATE_FILE.exists():
            return {
                "file_index": 0,
                "bit_index": 0
            }

        with open(STATE_FILE, "r") as f:
            return json.load(f)

    def save_state(self, state):

        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

    def get_bits(self, count: int):

            state = self.load_state()

            file_index = state["file_index"]
            bit_index = state["bit_index"]

            collected_bits = ""

            while len(collected_bits) < count:

                if file_index >= len(FILES):
                    raise Exception("No more bits available")

                with open(FILES[file_index], "r") as f:
                    data = f.read().strip()

                remaining = len(data) - bit_index

                needed = count - len(collected_bits)

                take = min(remaining, needed)

                collected_bits += data[bit_index: bit_index + take]

                bit_index += take

                # file exhausted
                if bit_index >= len(data):
                    file_index += 1
                    bit_index = 0

            # save updated cursor
            self.save_state({
                "file_index": file_index,
                "bit_index": bit_index
            })
            return {"random_numbers": collected_bits, "count": count, "post_processing": "none"}
        
    


# Singleton instance
qrng_service = QRNGService()