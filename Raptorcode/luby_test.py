import random
import unittest
from luby import *

class TestLubyTransform(unittest.TestCase):

    # def test_luby_transform_block_generator(self):
    #     # TODO: This test will fail currently because we aren't using the MT PRNG

    #     message = b"abcdefghijklmnopqrstuvwxyz"
    #     # TODO: Replace random.Random with MT PRNG
    #     codec = LubyCodec(4, random.Random(200), soliton_distribution(4))

    #     want_indices = [
    #         [0],
    #         [1],
    #         [3],
    #         [0, 1],
    #         [1, 2, 3],
    #     ]

    #     # These magic seeds are chosen to generate the block compositions
    #     # in want_indices given the PRNG with which we initialized the codec.
    #     encode_blocks = [7, 34, 5, 31, 25]
    #     for i in range(len(want_indices)):
    #         indices = codec.pick_indices(encode_blocks[i])
    #         self.assertEqual(indices, want_indices[i], f"Got {indices} indices for {encode_blocks[i]}, want {want_indices[i]}")

    #     source = codec.generate_intermediate_blocks(message, codec.source_blocks)
    #     luby_blocks = [LTBlock() for _ in encode_blocks]
    #     for i in range(len(encode_blocks)):
    #         b = generate_luby_transform_block(source, want_indices[i])
    #         luby_blocks[i].block_code = encode_blocks[i]
    #         luby_blocks[i].data = b.data[:]

    #     self.assertEqual(len(source), codec.source_blocks, f"Got {len(source)} encoded blocks, want {codec.source_blocks}")

    #     self.assertEqual(luby_blocks[0].data.decode('utf-8'), "abcdefg", f"Data for {{0}} block is {luby_blocks[0].data.decode('utf-8')}, should be 'abcdefg'")
    #     self.assertEqual(luby_blocks[1].data.decode('utf-8'), "hijklmn", f"Data for {{1}} block is {luby_blocks[1].data.decode('utf-8')}, should be 'hijklmn'")
    #     self.assertEqual(luby_blocks[2].data.decode('utf-8'), "uvwxyz", f"Data for {{2}} block is {luby_blocks[2].data.decode('utf-8')}, should be 'uvwxyz'")
    #     self.assertEqual(luby_blocks[3].data[0], ord('a') ^ ord('h'), f"Data[0] for {{0, 1}} block is {luby_blocks[3].data[0]}, should be 'a'^'h' ({ord('a') ^ ord('h')})")
    #     self.assertEqual(luby_blocks[4].data[0], ord('h') ^ ord('o') ^ ord('u'), f"Data[0] for {{1, 2, 3}} block is {luby_blocks[4].data[0]}, should be 'h'^'o'^'u' ({ord('h') ^ ord('o') ^ ord('u')})")

    def test_luby_decoder(self):
        message = b"abcdefghijklmnopqrstuvwxyz"
        codec = LubyCodec(4, random.Random(200), soliton_distribution(4))

        encode_blocks = [7, 34, 5, 31, 25]
        luby_blocks = encode_lt_blocks(message, encode_blocks, codec)

        decoder = codec.new_decoder(len(message))
        determined = decoder.add_blocks(luby_blocks)
        self.assertTrue(determined, "After adding code blocks, decoder is still undetermined.")

        decoded = decoder.decode()
        self.assertEqual(decoded, message, f"Decoded luby transform message is {decoded}, expected {message}")

if __name__ == '__main__':
    unittest.main()
