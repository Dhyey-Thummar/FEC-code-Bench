import random, unittest
from typing import List, Optional, Tuple
from gf2 import add_assign_binary
from octet import Octet
from octets import BinaryOctetVec
from iterators import OctetIter
from util import get_both_ranges

class BinaryMatrix:
    def new(height: int, width: int, trailing_dense_column_hint: int):
        raise NotImplementedError

    def set(self, i: int, j: int, value: Octet):
        raise NotImplementedError

    def height(self) -> int:
        raise NotImplementedError

    def width(self) -> int:
        raise NotImplementedError

    def size_in_bytes(self) -> int:
        raise NotImplementedError

    def count_ones(self, row: int, start_col: int, end_col: int) -> int:
        raise NotImplementedError

    def get_row_iter(self, row: int, start_col: int, end_col: int):
        raise NotImplementedError

    def get_ones_in_column(self, col: int, start_row: int, end_row: int) -> List[int]:
        raise NotImplementedError

    def get_sub_row_as_octets(self, row: int, start_col: int):
        raise NotImplementedError

    def query_non_zero_columns(self, row: int, start_col: int) -> List[int]:
        raise NotImplementedError

    def get(self, i: int, j: int) -> Octet:
        raise NotImplementedError

    def swap_rows(self, i: int, j: int):
        raise NotImplementedError

    def swap_columns(self, i: int, j: int, start_row_hint: int):
        raise NotImplementedError

    def enable_column_access_acceleration(self):
        pass

    def disable_column_access_acceleration(self):
        pass

    def hint_column_dense_and_frozen(self, i: int):
        pass

    def add_assign_rows(self, dest: int, src: int, start_col: int):
        raise NotImplementedError

    def resize(self, new_height: int, new_width: int):
        raise NotImplementedError

WORD_WIDTH = 64

class DenseBinaryMatrix(BinaryMatrix):
    def __init__(self, height: int, width: int, _: int):
        self.height = height
        self.width = width
        self.elements = [0] * (height * ((width + WORD_WIDTH - 1) // WORD_WIDTH))

    def bit_position(self, row: int, col: int) -> Tuple[int, int]:
        return (row * self.row_word_width() + self.word_offset(col), col % WORD_WIDTH)

    def row_word_width(self) -> int:
        return (self.width + WORD_WIDTH - 1) // WORD_WIDTH
    
    def word_offset(self, col) -> int:
        return (col // WORD_WIDTH)

    @staticmethod
    def select_mask(bit: int) -> int:
        return 1 << bit

    @staticmethod
    def select_bit_and_all_left_mask(bit: int) -> int:
        return ~DenseBinaryMatrix.select_all_right_of_mask(bit)
    
    @staticmethod
    def select_all_right_of_mask(bit: int) -> int:
        mask = DenseBinaryMatrix.select_mask(bit)
        # Subtract one to convert e.g. 0100 -> 0011
        return mask - 1

    @staticmethod
    def clear_bit(word: int, bit: int) -> int:
        word &= ~DenseBinaryMatrix.select_mask(bit)
        return word

    @staticmethod
    def set_bit(word: int, bit: int) -> int:
        word |= DenseBinaryMatrix.select_mask(bit)
        return word

    def set(self, i: int, j: int, value: Octet):
        word, bit = self.bit_position(i, j)
        if value == Octet.zero():
            self.elements[word] = self.clear_bit(self.elements[word], bit)
        else:
            self.elements[word] = self.set_bit(self.elements[word], bit)

    def get(self, i: int, j: int) -> Octet:
        word, bit = self.bit_position(i, j)
        if self.elements[word] & self.select_mask(bit):
            return Octet.one()
        return Octet.zero()

    def size_in_bytes(self) -> int:
        import sys
        size = sys.getsizeof(self)
        size += sys.getsizeof(self.elements)
        size += len(self.elements) * sys.getsizeof(int())
        return size
    
    def get_row_iter(self, row, start_col, end_col):
        first_word, first_bit = self.bit_position(row, start_col)
        last_word, _ = self.bit_position(row, end_col)
        return OctetIter.new_dense_binary(
            start_col,
            end_col,
            first_bit,
            self.elements[first_word:last_word + 1]
        )

    def get_ones_in_column(self, col, start_row, end_row):
        rows = []
        for row in range(start_row, end_row):
            if self.get(row, col) == Octet.one():
                rows.append(row)
        return rows

    def get_sub_row_as_octets(self, row, start_col):
        result = [0] * ((self.width - start_col + BinaryOctetVec.WORD_WIDTH - 1) // BinaryOctetVec.WORD_WIDTH)
        word = len(result)
        bit = 0
        for col in range(self.width - 1, start_col - 1, -1):
            if bit == 0:
                bit = BinaryOctetVec.WORD_WIDTH - 1
                word -= 1
            else:
                bit -= 1
            if self.get(row, col) == Octet.one():
                result[word] |= BinaryOctetVec.select_mask(bit)
        return BinaryOctetVec(result, self.width - start_col)

    def query_non_zero_columns(self, row, start_col):
        return [col for col in range(start_col, self.width) if self.get(row, col) != Octet.zero()]

    def count_ones(self, row: int, start_col: int, end_col: int) -> int:
        start_word, start_bit = self.bit_position(row, start_col)
        end_word, end_bit = self.bit_position(row, end_col)
        if start_word == end_word:
            mask = DenseBinaryMatrix.select_bit_and_all_left_mask(start_bit)
            mask &= DenseBinaryMatrix.select_all_right_of_mask(end_bit)
            bits = self.elements[start_word] & mask
            return bin(bits).count('1')
        first_word_bits = self.elements[start_word] & DenseBinaryMatrix.select_bit_and_all_left_mask(start_bit)
        ones = bin(first_word_bits).count('1')
        for word in range(start_word + 1, end_word):
            ones += bin(self.elements[word]).count('1')
        
        if end_bit > 0:
            bits = self.elements[end_word] & DenseBinaryMatrix.select_all_right_of_mask(end_bit)
            ones += bin(bits).count('1')
        
        return ones

    def swap_rows(self, i: int, j: int):
        row_i = i * self.row_word_width()
        row_j = j * self.row_word_width()
        for k in range(self.row_word_width()):
            self.elements[row_i + k], self.elements[row_j + k] = self.elements[row_j + k], self.elements[row_i + k]

    def swap_columns(self, i: int, j: int, start_row_hint: int):
        word_i, bit_i = self.bit_position(0, i)
        word_j, bit_j = self.bit_position(0, j)
        unset_i = ~DenseBinaryMatrix.select_mask(bit_i)
        unset_j = ~DenseBinaryMatrix.select_mask(bit_j)
        bit_i = DenseBinaryMatrix.select_mask(bit_i)
        bit_j = DenseBinaryMatrix.select_mask(bit_j)
        for row in range(start_row_hint, self.height):
            row_offset = row * self.row_word_width()
            i_set = self.elements[row_offset + word_i] & bit_i != 0
            if self.elements[row_offset + word_j] & bit_j == 0:
                self.elements[row_offset + word_i] &= unset_i
            else:
                self.elements[row_offset + word_i] |= bit_i

            if i_set:
                self.elements[row_offset + word_j] |= bit_j
            else:
                self.elements[row_offset + word_j] &= unset_j

    def add_assign_rows(self, dest: int, src: int, start_col: int):
        dest_word, _ = self.bit_position(dest, 0)
        src_word, _ = self.bit_position(src, 0)
        row_width = self.row_word_width()
        for k in range(row_width):
            self.elements[dest_word + k] ^= self.elements[src_word + k]

    def resize(self, new_height: int, new_width: int):
        old_row_width = self.row_word_width()
        self.height = new_height
        self.width = new_width
        new_row_width = self.row_word_width()
        words_to_remove = old_row_width - new_row_width
        if words_to_remove > 0:
            src = dest = 0
            while dest < new_height * new_row_width:
                self.elements[dest] = self.elements[src]
                src += 1
                dest += 1
                if dest % new_row_width == 0:
                    src += words_to_remove
            self.elements = self.elements[:new_height * new_row_width]

if __name__ == '__main__':
    from sparse_matrix import SparseBinaryMatrix

    def rand_dense_and_sparse(size):
        dense = DenseBinaryMatrix(size, size, 0)
        sparse = SparseBinaryMatrix(size, size, 1)
        # Generate 50% filled random matrices
        for _ in range(size * size // 2):
            i = random.randint(0, size - 1)
            j = random.randint(0, size - 1)
            value = random.randint(0, 1)

            dense.set(i, j, Octet(value))
            sparse.set(i, j, Octet(value))

        return dense, sparse

    def assert_matrices_eq(matrix1, matrix2):
        assert matrix1.height == matrix2.height
        assert matrix1.width == matrix2.width
        for i in range(matrix1.height):
            for j in range(matrix1.width):
                assert matrix1.get(i, j) == matrix2.get(i, j), f"Matrices are not equal at row={i} col={j}"

    class TestBinaryMatrices(unittest.TestCase):
        def test_row_iter(self):
            dense, sparse = rand_dense_and_sparse(8)
            for row in range(dense.height):
                start_col = random.randint(0, dense.width - 3)
                end_col = random.randint(start_col + 1, dense.width-sparse.num_dense_columns)
                dense_iter = dense.get_row_iter(row, start_col, end_col)
                sparse_iter = sparse.get_row_iter(row, start_col, end_col)
                for col in range(start_col, end_col):
                    self.assertEqual(dense.get(row, col), sparse.get(row, col))
                    self.assertEqual((col, dense.get(row, col)), next(dense_iter))
                    # Sparse iter does not return zeros
                    if sparse.get(row, col) != Octet.zero():
                        self.assertEqual((col, sparse.get(row, col)), next(sparse_iter))
                self.assertIsNone(next(dense_iter, None))
                self.assertIsNone(next(sparse_iter, None))

        def test_swap_rows(self):
            dense, sparse = rand_dense_and_sparse(8)
            dense.swap_rows(0, 4)
            dense.swap_rows(1, 6)
            dense.swap_rows(1, 7)
            sparse.swap_rows(0, 4)
            sparse.swap_rows(1, 6)
            sparse.swap_rows(1, 7)
            assert_matrices_eq(dense, sparse)

        def test_swap_columns(self):
            dense, sparse = rand_dense_and_sparse(8)
            dense.swap_columns(0, 4, 0)
            dense.swap_columns(1, 6, 0)
            dense.swap_columns(1, 1, 0)
            sparse.swap_columns(0, 4, 0)
            sparse.swap_columns(1, 6, 0)
            sparse.swap_columns(1, 1, 0)
            assert_matrices_eq(dense, sparse)

        def test_count_ones(self):
            dense, sparse = rand_dense_and_sparse(8)
            self.assertEqual(dense.count_ones(0, 0, 5), sparse.count_ones(0, 0, 5))
            self.assertEqual(dense.count_ones(2, 2, 6), sparse.count_ones(2, 2, 6))
            self.assertEqual(dense.count_ones(3, 1, 2), sparse.count_ones(3, 1, 2))

        def test_fma_rows(self):
            dense, sparse = rand_dense_and_sparse(8)
            dense.add_assign_rows(0, 1, 0)
            dense.add_assign_rows(0, 2, 0)
            dense.add_assign_rows(2, 1, 0)
            sparse.add_assign_rows(0, 1, 0)
            sparse.add_assign_rows(0, 2, 0)
            sparse.add_assign_rows(2, 1, 0)
            assert_matrices_eq(dense, sparse)

        def test_resize(self):
            dense, sparse = rand_dense_and_sparse(8)
            dense.disable_column_access_acceleration()
            sparse.disable_column_access_acceleration()
            dense.resize(5, 5)
            sparse.resize(5, 5)
            assert_matrices_eq(dense, sparse)

        def test_hint_column_dense_and_frozen(self):
            dense, sparse = rand_dense_and_sparse(8)
            sparse.enable_column_access_acceleration()
            sparse.hint_column_dense_and_frozen(6)
            sparse.hint_column_dense_and_frozen(5)
            assert_matrices_eq(dense, sparse)

        def test_dense_storage_math(self):
            size = 128
            dense, sparse = rand_dense_and_sparse(size)
            sparse.enable_column_access_acceleration()
            for i in reversed(range(size - 1)):
                sparse.hint_column_dense_and_frozen(i)
                assert_matrices_eq(dense, sparse)
            sparse.disable_column_access_acceleration()
            for _ in range(1000):
                i = random.randint(0, size - 1)
                j = random.randint(0, size - 1)
                while j == i:
                    j = random.randint(0, size - 1)
                dense.add_assign_rows(i, j, 0)
                sparse.add_assign_rows(i, j, 0)
            assert_matrices_eq(dense, sparse)

    unittest.main()