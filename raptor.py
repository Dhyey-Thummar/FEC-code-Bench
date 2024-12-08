import math
from functools import reduce
from block import *
from constants import *
from utils import *

def raptor_rand(x, i, m):
    v0 = v0table[(x + i) % 256]
    v1 = v1table[((x // 256) + i) % 256]
    return (v0 ^ v1) % m

def deg(v):
    f = [0, 10241, 491582, 712794, 831695, 948446, 1032189, 1048576]
    d = [0, 1, 2, 3, 4, 10, 11, 40]

    for j in range(1, len(f) - 1):
        if v < f[j]:
            return d[j]

    return d[-1]

def intermediate_symbols(k):
    x = int(math.floor(math.sqrt(2 * k)))
    if x < 1:
        x = 1

    while (x * (x - 1)) < (2 * k):
        x += 1

    s = int(math.ceil(0.01 * k)) + x
    s = smallest_prime_greater_or_equal(s)

    h = int(math.floor(math.log(s + k) / math.log(4)))
    while center_binomial(h) < k + s:
        h += 1

    return k + s + h, s, h

def triple_generator(k, x):
    l, _, _ = intermediate_symbols(k)
    lprime = smallest_prime_greater_or_equal(l)
    q = 65521
    jk = systematicIndexTable[k]

    a = (53591 + (jk * 997)) % q
    b = (10267 * (jk + 1)) % q
    y = (b + (x * a)) % q
    v = raptor_rand(y, 0, 1048576)
    d = deg(v)
    a = 1 + raptor_rand(y, 1, lprime - 1)
    b = raptor_rand(y, 2, lprime)

    return d, a, b

def find_lt_indices(k, x):
    l, _, _ = intermediate_symbols(k)
    lprime = smallest_prime_greater_or_equal(l)
    d, a, b = triple_generator(k, x)

    if d > l:
        d = l

    indices = []
    while b >= l:
        b = (b + a) % lprime
    indices.append(b)

    for _ in range(1, d):
        b = (b + a) % lprime
        while b >= l:
            b = (b + a) % lprime
        indices.append(b)

    return sorted(indices)

def lt_encode(k, x, c):
    indices = find_lt_indices(k, x)

    result = Block()
    for i in indices:
        result.xor(c[i])

    return result

def raptor_intermediate_blocks(source):
    """
    This function takes source blocks and generates intermediate encoding blocks using
    a systematic LT code.
    """
    lt_decoder = RaptorDecoder(RaptorCodec(alignment_size=1, source_blocks=len(source)), 1)
    for i in range(len(source)):
        indices = find_lt_indices(len(source), i)
        lt_decoder.matrix.add_equation(indices, source[i])

    lt_decoder.matrix.reduce()

    intermediate = lt_decoder.matrix.v
    return intermediate

class RaptorCodec:
    def __init__(self, source_blocks, alignment_size):
        """
        Initialize a new RaptorCodec object with the specified number of source blocks and symbol alignment size.
        """
        self.source_blocks = source_blocks
        # Symbol size must be within [4, 8192]
        self.symbol_size = alignment_size

    def generate_intermediate_blocks(self, message, num_blocks):
        """
        Generate intermediate blocks from a given message using the specified number of blocks.
        """
        source_long, source_short = partition_bytes(message, num_blocks)
        source = equalize_block_lengths(source_long, source_short)
        return raptor_intermediate_blocks(source)

    def pick_indices(self, code_block_index):
        """
        Choose a set of indices for the provided CodeBlock index value.
        """
        return find_lt_indices(self.source_blocks, code_block_index)

    def new_decoder(self, message_length):
        """
        Create a new RaptorDecoder for a given message length.
        """
        return RaptorDecoder(self, message_length)

# Create a new RaptorCodec instance
def new_raptor_codec(source_blocks, alignment_size):
    """
    Create and return a new RaptorCodec instance.
    """
    return RaptorCodec(source_blocks, alignment_size)

class RaptorDecoder:
    def __init__(self, codec, message_length):
        self.codec = codec
        self.message_length = message_length
        l, s, h = intermediate_symbols(codec.source_blocks)

        # Initialize the sparse matrix used for decoding.
        self.matrix = SparseMatrix()
        self.matrix.coeff = [[] for _ in range(l)]
        self.matrix.v = [Block() for _ in range(l)]

        k = codec.source_blocks
        compositions = [[] for _ in range(s)]

        for i in range(k):
            a = 1 + (int(math.floor(i / s)) % (s - 1))
            b = i % s
            compositions[b].append(i)
            b = (b + a) % s
            compositions[b].append(i)
            b = (b + a) % s
            compositions[b].append(i)
        for i in range(s):
            compositions[i].append(k + i)
            self.matrix.add_equation(compositions[i], Block())

        compositions = [[] for _ in range(h)]

        hprime = int(math.ceil(h / 2))
        m = build_gray_sequence(k + s, hprime)
        for i in range(h):
            for j in range(k + s):
                if bit_set(m[j], i):
                    compositions[i].append(j)
            compositions[i].append(k + s + i)
            self.matrix.add_equation(compositions[i], Block())

    def add_blocks(self, blocks):
        for block in blocks:
            indices = find_lt_indices(self.codec.source_blocks, block.block_code)
            self.matrix.add_equation(indices, Block(data=block.data))
        return self.matrix.determined()

    def decode(self):
        if not self.matrix.determined():
            return None

        self.matrix.reduce()

        # Use the encoder function to recover the source blocks.
        intermediate = self.matrix.v
        source = [lt_encode(self.codec.source_blocks, i, intermediate) for i in range(self.codec.source_blocks)]

        len_long, len_short, num_long, num_short = partition(self.message_length, self.codec.source_blocks)
        out = bytearray()
        for i in range(num_long):
            out.extend(source[i].data[:len_long])
        for i in range(num_long, num_long + num_short):
            out.extend(source[i].data[:len_short])
        return bytes(out)
