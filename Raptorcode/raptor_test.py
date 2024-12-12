import unittest
from utils import *
from raptor import *
from constants import *
from luby import encode_lt_blocks

def print_intermediate_encoding(intermediate):
    print("Intermediate Encoding Blocks")
    print("----------------------------")
    kb = 0
    for s in intermediate:
        print("intermediate", kb, s.data)
        kb += 1

class TestRaptorCodec(unittest.TestCase):
    def test_raptor_rand(self):
        rand_tests = [
            (1, 4, 150, 50),
            (20005, 19, 25, 6),
            (2180, 11, 1383483, 1166141)
        ]
        for x, i, m, expected_r in rand_tests:
            result = raptor_rand(x, i, m)
            self.assertEqual(result, expected_r, f"raptorRand({x}, {i}, {m}) = {result}, should be {expected_r}")

    def test_deg(self):
        degree_tests = [
            (0, 1),
            (10000, 1),
            (10240, 1),
            (10241, 2),
            (10242, 2),
            (715000, 4),
            (1000000, 11),
            (1034300, 40),
            (1048575, 40),
            (1048576, 40)
        ]
        for x, expected_d in degree_tests:
            result = deg(x)
            self.assertEqual(result, expected_d, f"deg({x}) = {result}, should be {expected_d}")

    def test_intermediate_symbols(self):
        intermediate_tests = [
            (0, 4, 2, 2),
            (1, 8, 3, 4),
            (10, 23, 7, 6),
            (13, 26, 7, 6),
            (14, 28, 7, 7),
            (500, 553, 41, 12),
            (5000, 5166, 151, 15)
        ]
        for k, expected_l, expected_s, expected_h in intermediate_tests:
            l, s, h = intermediate_symbols(k)
            self.assertEqual((l, s, h), (expected_l, expected_s, expected_h),
                             f"intermediateSymbols({k}) = ({l}, {s}, {h}), should be {expected_l}, {expected_s}, {expected_h}")

    def test_triple_generator(self):
        triple_tests = [
            (0, 3, 2, 4, 3),
            (1, 4, 4, 2, 5),
            (4, 0, 10, 13, 1),
            (4, 4, 4, 6, 2),
            (500, 514, 2, 107, 279),
            (1000, 52918, 3, 1070, 121)
        ]
        for k, x, expected_d, expected_a, expected_b in triple_tests:
            d, a, b = triple_generator(k, x)
            self.assertEqual((d, a, b), (expected_d, expected_a, expected_b),
                             f"tripleGenerator({k}, {x}) = ({d}, {a}, {b}), should be {expected_d}, {expected_a}, {expected_b}")

    def test_systematic_indices(self):
        self.assertEqual(systematicIndexTable[4], 18, "Systematic index for 4 should be 18")
        self.assertEqual(systematicIndexTable[21], 2, "Systematic index for 21 should be 2")
        self.assertEqual(systematicIndexTable[8192], 2665, "Systematic index for 8192 should be 2665")

    def test_lt_indices(self):
        lt_index_tests = [
            (4, 0, [1, 2, 3, 4, 6, 7, 8, 10, 11, 12]),
            (4, 4, [2, 3, 8, 9]),
            (100, 1, [51, 104]),
            (1000, 727, [306, 687, 1040]),
            (10, 57279, [19, 20, 21, 22])
        ]
        for k, x, expected_indices in lt_index_tests:
            indices = find_lt_indices(k, x)
            self.assertEqual(indices, expected_indices,
                             f"findLTIndices({k}, {x}) = {indices}, should be {expected_indices}")

    def test_raptor_decoder_construction(self):
        decoder = RaptorDecoder(RaptorCodec(alignment_size=1, source_blocks=10), 1)
        # Note: assuming print_matrix function is replaced with debug printing if necessary
        self.assertEqual(decoder.matrix.coeff[0], [0, 5, 6, 7, 10],
                         f"First matrix equation was {decoder.matrix.coeff[0]}, should be {0, 5, 6, 7, 10}")
        self.assertEqual(decoder.matrix.coeff[1], [1, 2, 3, 8, 13],
                         f"Second matrix equation was {decoder.matrix.coeff[1]}, should be {1, 2, 3, 8, 13}")
        self.assertEqual(decoder.matrix.coeff[2], [2, 3, 4, 7, 9, 14],
                         f"Third matrix equation was {decoder.matrix.coeff[2]}, should be {2, 3, 4, 7, 9, 14}")

    def test_intermediate_blocks(self):
        blocks = [
            Block(data=[0, 0, 0, 1]),
            Block(data=[0, 0, 1, 0]),
            Block(data=[0, 1, 0, 0]),
            Block(data=[1, 0, 0, 0])
        ]

        src_blocks = [Block() for _ in blocks]
        for i, block in enumerate(blocks):
            src_blocks[i].xor(block)

        intermediate = raptor_intermediate_blocks(src_blocks)
        self.assertEqual(len(intermediate), 14, f"Length of intermediate blocks is {len(intermediate)}, should be 14")

        for i in range(4):
            block = lt_encode(4, i, intermediate)
            self.assertEqual(block.data, blocks[i].data,
                             f"The result of LT encoding on the intermediate blocks for block {i} is {block.data}, should be the source blocks {blocks[i].data}")

    def test_systematic_raptor_code(self):
        c = RaptorCodec(13, 2)
        message = b"abcdefghijklmnopqrstuvwxyz"
        blocks = c.generate_intermediate_blocks(message, c.source_blocks)

        message_copy = bytearray(message)
        source_long, source_short = partition_bytes(message_copy, c.source_blocks)
        source_copy = equalize_block_lengths(source_long, source_short)

        for test_index in [0, 1, 2, 3, 4, 5]:
            b = lt_encode(13, test_index, blocks)
            self.assertEqual(b.data, source_copy[test_index].data,
                             f"LT encoding of CodeBlock={test_index} was ({b.data}), should be the {test_index}'th source block ({source_copy[test_index].data})")
    
    def test_intermediate_blocks_13(self):
        blocks = [Block(bytearray(13)) for _ in range(13)]
        for i in range(len(blocks)):
            blocks[i].data[i] = 1

        src_blocks = [Block() for _ in range(13)]
        for i in range(len(blocks)):
            src_blocks[i].xor(blocks[i])

        intermediate = raptor_intermediate_blocks(src_blocks)  # destructive to srcBlocks
        self.assertEqual(len(intermediate), 26, f"Length of intermediate blocks is {len(intermediate)}, should be 26")

        # print_intermediate_encoding(intermediate)

        # print("Finding intermediate equations")
        for i in range(13):
            block = lt_encode(13, i, intermediate)
            self.assertEqual(block.data, blocks[i].data,
                             f"The result of LT encoding on the intermediate blocks for block {i} is {block.data}, should be {blocks[i].data}")

        ids = [int(random.randint(0, 60000)) for _ in range(45)]
        codec = RaptorCodec(source_blocks=13, alignment_size=13)

        src_blocks = [Block() for _ in range(13)]
        for i in range(len(blocks)):
            src_blocks[i].xor(blocks[i])

        message = bytearray()
        for block in blocks:
            message.extend(block.data)

        code_blocks = encode_lt_blocks(message, ids, codec)  # destructive to srcBlocks

        # print("DECODE--------")
        decoder = RaptorDecoder(codec, len(message))
        for i in range(17):
            decoder.add_blocks([code_blocks[i]])

        message = bytearray()
        for block in blocks:
            message.extend(block.data)

        if decoder.matrix.determined():
            # print("Recovered:\n", [b.data for b in decoder.matrix.v])
            out = decoder.decode()
            # print("Recovered:\n", out)
            self.assertEqual(message, out, f"Decoding result must equal {message}, got {out}")

    def test_raptor_codec(self):
        codec = RaptorCodec(13, 2)
        message = b"abcdefghijklmnopqrstuvwxyz"
        ids = [random.randint(0, 60000) for _ in range(45)]

        message_copy = message[:]

        code_blocks = encode_lt_blocks(message_copy, ids, codec)

        # print("DECODE--------")
        decoder = RaptorDecoder(codec, len(message))
        for i in range(17):
            decoder.add_blocks([code_blocks[i]])

        if decoder.matrix.determined():
            # print("Recovered:\n", [b.data for b in decoder.matrix.v])
            out = decoder.decode()
            # print("Recovered:\n", out)
            self.assertEqual(message, out, f"Decoding result must equal {message}, got {out}")


if __name__ == "__main__":
    unittest.main()
