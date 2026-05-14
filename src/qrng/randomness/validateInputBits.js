function validateInputBits(inputBits) {
  const blockSize = 8;

  // Type check
  if (typeof inputBits !== 'string') {
    throw new Error("Input must be a string.");
  }

  // Length check
  if (inputBits.length < 1024) {
    throw new Error("Input string must be at least 1024 bits long.");
  }

  // Bit content check
  if (/[^01]/.test(inputBits)) {
    throw new Error("Input string must contain only '0' and '1'.");
  }

  // Entropy analysis on non-overlapping 8-bit blocks
  const numBlocks = Math.floor(inputBits.length / blockSize);
  const freq = new Array(256).fill(0); // 2^8 = 256 possible 8-bit values

  for (let i = 0; i < numBlocks; i++) {
    const block = inputBits.slice(i * blockSize, (i + 1) * blockSize);
    const value = parseInt(block, 2);
    freq[value]++;
  }

  const maxCount = Math.max(...freq);
  const maxProb = maxCount / numBlocks;
  const minEntropyPerBit = -Math.log2(maxProb) / blockSize;

  if (parseFloat(minEntropyPerBit.toFixed(6)) < 0.1) {
    throw new Error("Insufficient entropy: min-entropy per bit is below 0.1.");
  }
}