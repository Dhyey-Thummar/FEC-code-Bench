from typing import List
from sparse_vec import SparseBinaryVec
from arraymap import ImmutableListMapBuilder
from iterators import OctetIter
from octet import Octet
from octets import BinaryOctetVec
from util import get_both_indices
import sys, unittest

class SparseBinaryMatrix:
    WORD_WIDTH = 64

    def __init__(self, height: int, width: int, trailing_dense_column_hint: int):
        assert(height < 16777216)
        assert(width < 65536)
        self.height = height
        self.width = width
        row_mapping = [i & 0xFFFFFFFF for i in range(height)]
        col_mapping = [i & 0xFFFF for i in range(width)]
        self.sparse_elements: List[SparseBinaryVec] = [SparseBinaryVec.with_capacity(10) for i in range(height)]
        self.dense_elements = [0] * (height * ((trailing_dense_column_hint - 1) // SparseBinaryMatrix.WORD_WIDTH + 1)) if trailing_dense_column_hint > 0 else []
        self.sparse_columnar_values = None  # To store column values if needed
        self.logical_row_to_physical = row_mapping.copy()
        self.physical_row_to_logical = row_mapping
        self.logical_col_to_physical = col_mapping.copy()
        self.physical_col_to_logical = col_mapping
        self.column_index_disabled = True
        self.num_dense_columns = trailing_dense_column_hint
        self.debug_indexed_column_valid = [True] * width

    def verify(self):
        if self.column_index_disabled:
            return
        columns = self.sparse_columnar_values
        if columns is None:
            raise ValueError("Expected sparse_columnar_values to be set.")
        for row in range(self.height):
            for col, value in self.sparse_elements[row].keys_values():
                if value != Octet.zero():
                    assert row in columns.get(col), f"Verification failed for row {row} and column {col}"

    def logical_col_to_dense_col(self, col: int) -> int:
        assert col >= self.width - self.num_dense_columns
        return col - (self.width - self.num_dense_columns)

    def bit_position(self, row: int, col: int):
        return (row * self.row_word_width() + self.word_offset(col),
                (self.left_padding_bits() + col) % SparseBinaryMatrix.WORD_WIDTH)

    def row_word_width(self) -> int:
        return (self.num_dense_columns + SparseBinaryMatrix.WORD_WIDTH - 1) // SparseBinaryMatrix.WORD_WIDTH

    def left_padding_bits(self) -> int:
        return (SparseBinaryMatrix.WORD_WIDTH - (self.num_dense_columns % SparseBinaryMatrix.WORD_WIDTH)) % SparseBinaryMatrix.WORD_WIDTH

    def word_offset(self, bit: int) -> int:
        return (self.left_padding_bits() + bit) // SparseBinaryMatrix.WORD_WIDTH

    @staticmethod
    def select_mask(bit: int) -> int:
        return 1 << bit

    @staticmethod
    def clear_bit(word: int, bit: int) -> int:
        return word & ~SparseBinaryMatrix.select_mask(bit)

    @staticmethod
    def set_bit(word: int, bit: int) -> int:
        return word | SparseBinaryMatrix.select_mask(bit)

    def set(self, i: int, j: int, value: Octet):
        physical_i = self.logical_row_to_physical[i]
        physical_j = self.logical_col_to_physical[j]
        if self.width - j <= self.num_dense_columns:
            word, bit = self.bit_position(physical_i, self.logical_col_to_dense_col(j))
            if value == Octet.zero():
                self.dense_elements[word] = SparseBinaryMatrix.clear_bit(self.dense_elements[word], bit)
            else:
                self.dense_elements[word] = SparseBinaryMatrix.set_bit(self.dense_elements[word], bit)
        else:
            self.sparse_elements[physical_i].insert(physical_j, value)
            assert self.column_index_disabled

    def count_ones(self, row: int, start_col: int, end_col: int) -> int:
        if end_col > self.width - self.num_dense_columns:
            raise NotImplementedError("It was assumed that this wouldn't be needed, because the method would only be called on the V section of matrix A")
        ones = 0
        physical_row = self.logical_row_to_physical[row]
        for physical_col, value in self.sparse_elements[physical_row].keys_values():
            col = self.physical_col_to_logical[physical_col]
            if start_col <= col < end_col and value == Octet.one():
                ones += 1
        return ones

    def get_sub_row_as_octets(self, row: int, start_col: int) -> BinaryOctetVec:
        first_dense_column = self.width - self.num_dense_columns
        assert start_col == first_dense_column
        physical_row = self.logical_row_to_physical[row]
        first_word, _ = self.bit_position(physical_row, self.logical_col_to_dense_col(start_col))
        last_word = first_word + self.row_word_width()

        return BinaryOctetVec(
            self.dense_elements[first_word:last_word].copy(),
            self.num_dense_columns
        )

    def query_non_zero_columns(self, row: int, start_col: int) -> List[int]:
        assert start_col == self.width - self.num_dense_columns
        result = []
        physical_row = self.logical_row_to_physical[row]
        word, bit = self.bit_position(physical_row, self.logical_col_to_dense_col(start_col))
        col = start_col
        block = self.dense_elements[word]
        while block.bit_length() > bit:
            result.append(col + (block.bit_length() - bit - 1))
            block &= ~(1 << (block.bit_length() - 1))
        col += SparseBinaryMatrix.WORD_WIDTH - bit
        word += 1

        while col < self.width:
            block = self.dense_elements[word]
            while block != 0:
                result.append(col + (block.bit_length() - 1))
                block &= ~(1 << (block.bit_length() - 1))
            col += SparseBinaryMatrix.WORD_WIDTH
            word += 1

        return result

    def get(self, i: int, j: int) -> Octet:
        physical_i = self.logical_row_to_physical[i]
        physical_j = self.logical_col_to_physical[j]
        if self.width - j <= self.num_dense_columns:
            word, bit = self.bit_position(physical_i, self.logical_col_to_dense_col(j))
            if self.dense_elements[word] & (1 << bit) == 0:
                return Octet.zero()
            else:
                return Octet.one()
        else:
            return self.sparse_elements[physical_i].get(physical_j)

    def get_row_iter(self, row: int, start_col: int, end_col: int):
        if end_col > self.width - self.num_dense_columns:
            raise NotImplementedError("It was assumed that this wouldn't be needed, because the method would only be called on the V section of matrix A")
        physical_row = self.logical_row_to_physical[row]
        sparse_elements = self.sparse_elements[physical_row]
        return OctetIter.new_sparse(start_col, end_col, sparse_elements, self.physical_col_to_logical)

    def get_ones_in_column(self, col: int, start_row: int, end_row: int) -> List[int]:
        assert not self.column_index_disabled
        physical_col = self.logical_col_to_physical[col]
        rows = []
        for physical_row in self.sparse_columnar_values.get(physical_col):
            logical_row = self.physical_row_to_logical[physical_row]
            if start_row <= logical_row < end_row:
                rows.append(logical_row)
        return rows

    def swap_rows(self, i: int, j: int):
        physical_i = self.logical_row_to_physical[i]
        physical_j = self.logical_row_to_physical[j]
        self.logical_row_to_physical[i], self.logical_row_to_physical[j] = (
            self.logical_row_to_physical[j],
            self.logical_row_to_physical[i],
        )
        self.physical_row_to_logical[physical_i], self.physical_row_to_logical[physical_j] = (
            self.physical_row_to_logical[physical_j],
            self.physical_row_to_logical[physical_i],
        )

    def swap_columns(self, i: int, j: int, _: int):
        if j >= self.width - self.num_dense_columns:
            raise NotImplementedError("It was assumed that this wouldn't be needed, because the method would only be called on the V section of matrix A")
        self.logical_col_to_physical[i], self.logical_col_to_physical[j] = (
            self.logical_col_to_physical[j],
            self.logical_col_to_physical[i],
        )
        physical_i = self.logical_col_to_physical[i]
        physical_j = self.logical_col_to_physical[j]
        self.physical_col_to_logical[physical_i], self.physical_col_to_logical[physical_j] = (
            self.physical_col_to_logical[physical_j],
            self.physical_col_to_logical[physical_i],
        )

    def enable_column_access_acceleration(self):
        self.column_index_disabled = False
        builder = ImmutableListMapBuilder(self.height)
        for physical_row, elements in enumerate(self.sparse_elements):
            for physical_col, _ in elements.keys_values():
                builder.add(physical_col & 0xFFFF, physical_row)
        self.sparse_columnar_values = builder.build()

    def disable_column_access_acceleration(self):
        self.column_index_disabled = True
        self.sparse_columnar_values = None

    def hint_column_dense_and_frozen(self, i: int):
        assert self.width - self.num_dense_columns - 1 == i, "Can only freeze the last sparse column"
        assert (not self.column_index_disabled)
        self.num_dense_columns += 1
        last_word, _ = self.bit_position(self.height - 1, self.num_dense_columns - 1)
        if last_word >= len(self.dense_elements):
            src = len(self.dense_elements)
            self.dense_elements.extend([0] * self.height)
            dest = len(self.dense_elements)
            while src > 0:
                src -= 1
                dest -= 1
                self.dense_elements[dest] = self.dense_elements[src]
                if dest % self.row_word_width() == 1:
                    dest -= 1
                    self.dense_elements[dest] = 0

            assert(src == 0)
            assert(dest == 0)

        physical_i = self.logical_col_to_physical[i]
        for maybe_present_in_row in self.sparse_columnar_values.get(physical_i):
            physical_row = maybe_present_in_row
            value = self.sparse_elements[physical_row].remove(physical_i)
            if value is not None:
                word, bit = self.bit_position(physical_row, 0)
                if value == Octet.zero():
                    self.dense_elements[word] &= ~(1 << bit)
                else:
                    self.dense_elements[word] |= (1 << bit)

    def add_assign_rows(self, dest: int, src: int, start_col: int):
        assert dest != src
        assert start_col == 0 or start_col == self.width - self.num_dense_columns, "start_col must be zero or at the beginning of the U matrix"
        physical_dest = self.logical_row_to_physical[dest]
        physical_src = self.logical_row_to_physical[src]
        if self.num_dense_columns > 0:
            dest_word, _ = self.bit_position(physical_dest, 0)
            src_word, _ = self.bit_position(physical_src, 0)
            for word in range(self.row_word_width()):
                self.dense_elements[dest_word + word] ^= self.dense_elements[src_word + word]
        
        if start_col == 0:
            dest_row, temp_row = get_both_indices(self.sparse_elements, physical_dest, physical_src)
            assert(self.column_index_disabled or len(temp_row) == 1)

            column_added = dest_row.add_assign(temp_row)
            assert(self.column_index_disabled or not column_added)

        # something related to debug_assertions was here
        self.verify()

    def resize(self, new_height, new_width):
        assert new_height <= self.height, "new_height must be less than or equal to current height"

        # Only support same width or removing all dense columns
        columns_to_remove = self.width - new_width
        assert columns_to_remove == 0 or columns_to_remove >= self.num_dense_columns, \
            "Only support resizing with same width or removing all dense columns"

        if not self.column_index_disabled:
            raise NotImplementedError(
                "Resize should only be used in phase 2, after column indexing is no longer needed"
            )

        new_sparse = [None] * new_height
        for i in range(len(self.sparse_elements) - 1, -1, -1):
            logical_row = self.physical_row_to_logical[i]
            sparse = self.sparse_elements.pop()
            if logical_row < new_height:
                new_sparse[logical_row] = sparse

        if columns_to_remove == 0 and self.num_dense_columns > 0:
            # Create a new dense matrix
            new_dense = [0] * (new_height * self.row_word_width())
            for logical_row in range(new_height):
                physical_row = self.logical_row_to_physical[logical_row]
                for word in range(self.row_word_width()):
                    new_dense[logical_row * self.row_word_width() + word] = \
                        self.dense_elements[physical_row * self.row_word_width() + word]
            self.dense_elements = new_dense
        else:
            columns_to_remove -= self.num_dense_columns
            self.dense_elements.clear()
            self.num_dense_columns = 0

        self.logical_row_to_physical = self.logical_row_to_physical[:new_height]
        self.physical_row_to_logical = self.physical_row_to_logical[:new_height]
        for i in range(new_height):
            self.logical_row_to_physical[i] = i
            self.physical_row_to_logical[i] = i

        self.sparse_elements = [row for row in new_sparse if row is not None]

        # Remove sparse columns if needed
        if columns_to_remove > 0:
            physical_to_logical = self.physical_col_to_logical
            for row in range(len(self.sparse_elements)):
                # self.sparse_elements[row] = [
                #     (col, value) for col, value in self.sparse_elements[row]
                #     if physical_to_logical[col] < new_width
                # ]
                self.sparse_elements[row].retain(lambda col, _: physical_to_logical[col] < new_width)

        self.height = new_height
        self.width = new_width

        # Debug-only verification
        self.verify()


    def size_in_bytes(self):
        bytes_count = sys.getsizeof(self)
        for x in self.sparse_elements:
            bytes_count += x.size_in_bytes()
        
        bytes_count += sys.getsizeof(0) * len(self.dense_elements)  # Assuming 0 is a u64 (integer)
        
        if self.sparse_columnar_values is not None:
            bytes_count += self.sparse_columnar_values.size_in_bytes()
        
        bytes_count += sys.getsizeof(0) * len(self.logical_row_to_physical)  # Assuming 0 is a u32 (integer)
        bytes_count += sys.getsizeof(0) * len(self.physical_row_to_logical)  # Assuming 0 is a u32 (integer)
        bytes_count += sys.getsizeof(0) * len(self.logical_col_to_physical)  # Assuming 0 is a u16 (integer)
        bytes_count += sys.getsizeof(0) * len(self.physical_col_to_logical)  # Assuming 0 is a u16 (integer)

        bytes_count += sys.getsizeof(True) * len(self.debug_indexed_column_valid)

        return bytes_count
    
if __name__ == '__main__':
    from systematic_constants import num_intermediate_symbols, MAX_SOURCE_SYMBOLS_PER_BLOCK
    class TestMaxWidthOptimization(unittest.TestCase):
        def test_check_max_width_optimization(self):
            # Check that the optimization of limiting matrix width to 2^16 is safe.
            # Matrix width will never exceed L
            self.assertTrue(num_intermediate_symbols(MAX_SOURCE_SYMBOLS_PER_BLOCK) < 65536)

    unittest.main()