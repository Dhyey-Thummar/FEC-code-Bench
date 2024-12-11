import unittest
import random
from block import *

class TestRaptorCodec(unittest.TestCase):
    def test_block_length(self):
        length_tests = [
            (Block(), 0),
            (Block(b'\x01\x00\x01'), 3),
            (Block(b'\x01\x00\x01', 1), 4),
        ]
        for block, expected_length in length_tests:
            self.assertEqual(block.length(), expected_length)
            self.assertEqual(block.is_empty(), expected_length == 0)

    def test_block_xor(self):
        xor_tests = [
            (Block(b'\x01\x00\x01'), Block(b'\x01\x01\x01'), Block(b'\x00\x01\x00')),
            (Block(b'\x01'), Block(b'\x00\x0e\x06'), Block(b'\x01\x0e\x06')),
            (Block(), Block(b'\x64\xc8'), Block(b'\x64\xc8')),
            (Block(b'', 5), Block(b'\x00\x01\x00'), Block(b'\x00\x01\x00', 2)),
            (Block(b'', 5), Block(b'\x00\x01\x00\x02\x03'), Block(b'\x00\x01\x00\x02\x03')),
            (Block(b'', 5), Block(b'\x00\x01\x00\x02\x03\x07'), Block(b'\x00\x01\x00\x02\x03\x07')),
            (Block(b'\x01', 4), Block(b'\x00\x01\x00\x02\x03\x07'), Block(b'\x01\x01\x00\x02\x03\x07')),
        ]
        for a, b, expected_out in xor_tests:
            original_length = a.length()
            a.xor(b)
            self.assertGreaterEqual(a.length(), original_length)
            self.assertEqual(a.data, expected_out.data)

    def test_partition_bytes(self):
        a = bytes(range(100))
        partition_tests = [
            (11, 1, 10),
            (3, 1, 2),
        ]
        for num_partitions, len_long, len_short in partition_tests:
            long, short = partition_bytes(a, num_partitions)
            self.assertEqual(len(long), len_long)
            self.assertEqual(len(short), len_short)
            self.assertEqual(short[-1].padding, 0)

    def test_equalize_block_lengths(self):
        b = b"abcdefghijklmnopq"
        equalize_tests = [
            (1, 17, 0),
            (2, 9, 1),
            (3, 6, 1),
            (4, 5, 1),
            (5, 4, 1),
            (6, 3, 1),
            (7, 3, 1),
            (8, 3, 1),
            (9, 2, 1),
            (10, 2, 1),
            (16, 2, 1),
            (17, 1, 0),
        ]
        for num_partitions, length, padding in equalize_tests:
            long, short = partition_bytes(b, num_partitions)
            blocks = equalize_block_lengths(long, short)
            self.assertEqual(len(blocks), num_partitions)
            for block in blocks:
                self.assertEqual(block.length(), length)
            self.assertEqual(blocks[-1].padding, padding)

    def print_matrix(self, m):
        print("------- matrix -----------")
        for i in range(len(m.coeff)):
            print(f"{m.coeff[i]} = {m.v[i].data}")

    def test_matrix_xor_row(self):
        xor_row_tests = [
            ([0, 1], [2, 3], [0, 1, 2, 3]),
            ([0, 1], [1, 2, 3], [0, 2, 3]),
            ([], [1, 2, 3], [1, 2, 3]),
            ([1, 2, 3], [], [1, 2, 3]),
            ([1], [2], [1, 2]),
            ([1], [1], []),
            ([1, 2], [1, 2, 3, 4], [3, 4]),
            ([3, 4], [1, 2, 3, 4], [1, 2]),
            ([1, 2, 3, 4], [1, 2], [3, 4]),
            ([0, 1, 2, 3, 4], [1, 2], [0, 3, 4]),
            ([3, 4], [1, 2, 3, 4, 5], [1, 2, 5]),
            ([3, 4, 8], [1, 2, 3, 4, 5], [1, 2, 5, 8]),
        ]

        for arow, r, expected in xor_row_tests:
            m = SparseMatrix()
            m.coeff = [arow]
            m.v = [Block(b'\x01')]

            test_block = Block(b'\x02')
            r, test_block = m.xor_row(0, r, test_block)

            if not r:
                r = []

            self.assertEqual(r, expected, f"XOR row result got {r}, should be {expected}")
            self.assertEqual(test_block.data, b'\x03', f"XOR row block got {test_block.data}, should be b'\x03'")

    def test_matrix_basic(self):
        m = SparseMatrix()
        m.coeff = [[] for _ in range(2)]
        m.v = [Block() for _ in range(2)]

        m.add_equation([0], Block(b'\x01'))
        self.assertFalse(m.determined(), "2-row matrix should not be determined after 1 equation")
        self.print_matrix(m)

        m.add_equation([0, 1], Block(b'\x02'))
        self.assertTrue(m.determined(), "2-row matrix should be determined after 2 equations")
        self.print_matrix(m)

        self.assertEqual(m.coeff[0], [0])
        self.assertEqual(m.v[0].data, b'\x01')

        self.assertEqual(m.coeff[1], [1])
        self.assertEqual(m.v[1].data, b'\x03')

        m.reduce()
        self.assertEqual(m.coeff[0], [0])
        self.assertEqual(m.v[0].data, b'\x01')

        self.assertEqual(m.coeff[1], [1])
        self.assertEqual(m.v[1].data, b'\x03')

    def test_matrix_large(self):
        m = SparseMatrix()
        m.coeff = [[] for _ in range(4)]
        m.v = [Block() for _ in range(4)]

        m.add_equation([2, 3], Block(b'\x01'))
        m.add_equation([2], Block(b'\x02'))
        self.assertFalse(m.determined(), "4-row matrix should not be determined after 2 equations")
        self.print_matrix(m)

        # Check triangular entries
        self.assertEqual(len(m.coeff[2]), 1, f"Equation 2 got {m.coeff[2]} = {m.v[2].data}, should be [2] = [2]")
        self.assertEqual(m.v[2].data, b'\x02')

        self.assertEqual(len(m.coeff[3]), 1, f"Equation 3 got {m.coeff[3]} = {m.v[3].data}, should be [3] = [3]")
        self.assertEqual(m.v[3].data, b'\x03')

        self.assertEqual(len(m.coeff[0]), 0, "Equations 0 should be empty")
        self.assertEqual(len(m.coeff[1]), 0, "Equations 1 should be empty")
        self.print_matrix(m)

        m.add_equation([0, 1, 2, 3], Block(b'\x04'))
        self.assertFalse(m.determined(), "4-row matrix should not be determined after 3 equations")
        self.print_matrix(m)

        m.add_equation([3], Block(b'\x03'))
        self.assertFalse(m.determined(), "4-row matrix should not be determined after redundant equation")
        self.print_matrix(m)

        m.add_equation([0, 2], Block(b'\x08'))
        self.assertTrue(m.determined(), "4-row matrix should be determined after 4 equations")
        self.print_matrix(m)

        # Check final matrix state
        self.assertEqual(m.coeff[0], [0, 2], f"Got {m.coeff[0]} for coeff[0], expect [0, 2]")
        self.assertEqual(m.coeff[1], [1, 3], f"Got {m.coeff[1]} for coeff[1], expect [1, 3]")

if __name__ == "__main__":
    unittest.main()
