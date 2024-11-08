import random
from typing import List, Optional, Tuple
from gf2 import add_assign_binary
from octet import Octet
from octets import BinaryOctetVec
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
    def __init__(self, height: int, width: int):
        self.height = height
        self.width = width
        self.elements = [0] * (height * ((width + WORD_WIDTH - 1) // WORD_WIDTH))

    def bit_position(self, row: int, col: int) -> Tuple[int, int]:
        return (row * self.row_word_width() + col // WORD_WIDTH, col % WORD_WIDTH)

    def row_word_width(self) -> int:
        return (self.width + WORD_WIDTH - 1) // WORD_WIDTH

    @staticmethod
    def select_mask(bit: int) -> int:
        return 1 << bit

    @staticmethod
    def clear_bit(word: int, bit: int) -> int:
        return word & ~DenseBinaryMatrix.select_mask(bit)

    @staticmethod
    def set_bit(word: int, bit: int) -> int:
        return word | DenseBinaryMatrix.select_mask(bit)

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

    def height(self) -> int:
        return self.height

    def width(self) -> int:
        return self.width

    def size_in_bytes(self) -> int:
        import sys
        size = sys.getsizeof(self)
        size += sys.getsizeof(self.elements)
        size += len(self.elements) * sys.getsizeof(int())
        return size

    def count_ones(self, row: int, start_col: int, end_col: int) -> int:
        start_word, start_bit = self.bit_position(row, start_col)
        end_word, end_bit = self.bit_position(row, end_col)
        if start_word == end_word:
            mask = (self.select_mask(start_bit) - 1) ^ ((self.select_mask(end_bit) - 1) if end_bit > 0 else 0)
            return bin(self.elements[start_word] & mask).count('1')
        ones = bin(self.elements[start_word] & (~0 << start_bit)).count('1')
        ones += sum(bin(self.elements[word]).count('1') for word in range(start_word + 1, end_word))
        if end_bit > 0:
            ones += bin(self.elements[end_word] & ((1 << end_bit) - 1)).count('1')
        return ones

    def swap_rows(self, i: int, j: int):
        row_i = i * self.row_word_width()
        row_j = j * self.row_word_width()
        for k in range(self.row_word_width()):
            self.elements[row_i + k], self.elements[row_j + k] = self.elements[row_j + k], self.elements[row_i + k]

    def swap_columns(self, i: int, j: int, start_row_hint: int):
        word_i, bit_i = self.bit_position(0, i)
        word_j, bit_j = self.bit_position(0, j)
        unset_i = ~self.select_mask(bit_i)
        unset_j = ~self.select_mask(bit_j)
        bit_i = self.select_mask(bit_i)
        bit_j = self.select_mask(bit_j)
        for row in range(start_row_hint, self.height):
            row_offset = row * self.row_word_width()
            i_set = self.elements[row_offset + word_i] & bit_i != 0
            self.elements[row_offset + word_i] = (self.elements[row_offset + word_i] & unset_i) | (self.elements[row_offset + word_j] & bit_j)
            self.elements[row_offset + word_j] = (self.elements[row_offset + word_j] & unset_j) | (bit_i if i_set else 0)

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
