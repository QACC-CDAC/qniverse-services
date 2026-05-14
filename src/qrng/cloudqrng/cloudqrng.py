   
   
DATA_DIR = Path("data")

FILES = [
    DATA_DIR / "bits_1.txt",
    DATA_DIR / "bits_2.txt",
    DATA_DIR / "bits_3.txt",
    DATA_DIR / "bits_4.txt",
]

STATE_FILE = DATA_DIR / "state.json"

   
class CloudQRNG:
    """Service for generating quantum random numbers"""   
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

            return collected_bits
        
    