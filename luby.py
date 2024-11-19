import random
from block import *
from utils import *

class Codec:
    def generate_intermediate_blocks(self, message, num_blocks):
        raise NotImplementedError()

    def pick_indices(self, code_block_index):
        raise NotImplementedError()

class LTBlock:
    def __init__(self, block_code, data):
        self.block_code = block_code
        self.data = data

def generate_luby_transform_block(source, indices):
    symbol = Block()

    for i in indices:
        if i < len(source):
            symbol.xor(source[i])

    return symbol

class LubyCodec(Codec):
    def __init__(self, source_blocks, random_gen, degree_cdf):
        self.source_blocks = source_blocks
        self.random_gen = random_gen
        self.degree_cdf = degree_cdf

    def pick_indices(self, code_block_index):
        self.random_gen.seed(code_block_index)
        d = pick_degree(self.random_gen, self.degree_cdf)
        return sample_uniform(self.random_gen, d, self.source_blocks)

    def generate_intermediate_blocks(self, message, num_blocks):
        long_blocks, short_blocks = partition_bytes(message, self.source_blocks)
        return equalize_block_lengths(long_blocks, short_blocks)

    def new_decoder(self, message_length):
        return LubyDecoder(self, message_length)

class LubyDecoder:
    def __init__(self, codec, message_length):
        self.codec = codec
        self.message_length = message_length
        self.matrix = SparseMatrix()
        self.matrix.coeff = [[] for _ in range(codec.source_blocks)]
        self.matrix.v = [Block() for _ in range(codec.source_blocks)]

    def add_blocks(self, blocks):
        for block in blocks:
            indices = self.codec.pick_indices(block.block_code)
            self.matrix.add_equation(indices, Block(block.data))
        return self.matrix.determined()

    def decode(self):
        if not self.matrix.determined():
            return None

        self.matrix.reduce()

        len_long, len_short, num_long, num_short = partition(self.message_length, self.codec.source_blocks)
        return self.matrix.reconstruct(self.message_length, len_long, len_short, num_long, num_short)


def encode_lt_blocks(message, encoded_block_ids, codec):
    source = codec.generate_intermediate_blocks(message, codec.source_blocks)

    lt_blocks = []
    for block_id in encoded_block_ids:
        indices = codec.pick_indices(block_id)
        block = generate_luby_transform_block(source, indices)
        lt_block = LTBlock(block_code=block_id, data=block.data)
        lt_blocks.append(lt_block)
    
    return lt_blocks
