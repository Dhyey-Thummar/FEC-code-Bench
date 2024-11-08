from typing import List, Optional
from collections import defaultdict

class SparseBinaryMatrix:
    WORD_WIDTH = 64

    def __init__(self, height: int, width: int, trailing_dense_column_hint: int):
        self.height = height
        self.width = width
        self.sparse_elements = [defaultdict(int) for _ in range(height)]
        self.dense_elements = [0] * (height * ((trailing_dense_column_hint - 1) // SparseBinaryMatrix.WORD_WIDTH + 1)) \
            if trailing_dense_column_hint > 0 else []
        self.sparse_columnar_values = None  # To store column values if needed
        self.logical_row_to_physical = list(range(height))
        self.physical_row_to_logical = list(range(height))
        self.logical_col_to_physical = list(range(width))
        self.physical_col_to_logical = list(range(width))
        self.column_index_disabled = True
        self.num_dense_columns = trailing_dense_column_hint

    def logical_col_to_dense_col(self, col: int) -> int:
        assert col >= self.width - self.num_dense_columns
        return col - (self.width - self.num_dense_columns)

    def bit_position(self, row: int, col: int) -> (int, int):
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

    def set(self, i: int, j: int, value: int):
        physical_i = self.logical_row_to_physical[i]
        physical_j = self.logical_col_to_physical[j]
        if self.width - j <= self.num_dense_columns:
            word, bit = self.bit_position(physical_i, self.logical_col_to_dense_col(j))
            if value == 0:
                self.dense_elements[word] = SparseBinaryMatrix.clear_bit(self.dense_elements[word], bit)
            else:
                self.dense_elements[word] = SparseBinaryMatrix.set_bit(self.dense_elements[word], bit)
        else:
            self.sparse_elements[physical_i][physical_j] = value
            assert self.column_index_disabled

    def get(self, i: int, j: int) -> int:
        physical_i = self.logical_row_to_physical[i]
        physical_j = self.logical_col_to_physical[j]
        if self.width - j <= self.num_dense_columns:
            word, bit = self.bit_position(physical_i, self.logical_col_to_dense_col(j))
            return 1 if self.dense_elements[word] & SparseBinaryMatrix.select_mask(bit) else 0
        else:
            return self.sparse_elements[physical_i].get(physical_j, 0)

    def swap_rows(self, i: int, j: int):
        physical_i = self.logical_row_to_physical[i]
        physical_j = self.logical_row_to_physical[j]
        self.logical_row_to_physical[i], self.logical_row_to_physical[j] = self.logical_row_to_physical[j], self.logical_row_to_physical[i]
        self.physical_row_to_logical[physical_i], self.physical_row_to_logical[physical_j] = \
            self.physical_row_to_logical[physical_j], self.physical_row_to_logical[physical_i]

    def swap_columns(self, i: int, j: int):
        if j >= self.width - self.num_dense_columns:
            raise NotImplementedError("It was assumed that this wouldn't be needed, because the method would only be called on the V section of matrix A")

        physical_i = self.logical_col_to_physical[i]
        physical_j = self.logical_col_to_physical[j]
        self.logical_col_to_physical[i], self.logical_col_to_physical[j] = self.logical_col_to_physical[j], self.logical_col_to_physical[i]
        self.physical_col_to_logical[physical_i], self.physical_col_to_logical[physical_j] = \
            self.physical_col_to_logical[physical_j], self.physical_col_to_logical[physical_i]

    # Placeholder methods and other function implementations should be added to match all features.
