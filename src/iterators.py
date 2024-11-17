from typing import List, Optional, Tuple, Iterator
from octet import Octet
from sparse_vec import SparseBinaryVec

def select_mask(bit: int):
    return 1 << bit

class ClonedOctetIter:
    def __init__(self, sparse: bool, end_col: int, dense_elements: Optional[List[int]] = None,
                 dense_index: int = 0, dense_word_index: int = 0, dense_bit_index: int = 0,
                 sparse_elements: Optional[List[Tuple[int, Octet]]] = None, sparse_index: int = 0):
        self.sparse = sparse
        self.end_col = end_col
        self.dense_elements = dense_elements
        self.dense_index = dense_index
        self.dense_word_index = dense_word_index
        self.dense_bit_index = dense_bit_index
        self.sparse_elements = sparse_elements
        self.sparse_index = sparse_index

    def __iter__(self):
        return self

    def __next__(self) -> Tuple[int, Octet]:
        if self.sparse:
            if self.sparse_index == len(self.sparse_elements):
                raise StopIteration
            old_index = self.sparse_index
            self.sparse_index += 1
            return self.sparse_elements[old_index]
        elif self.dense_index == self.end_col:
            raise StopIteration
        else:
            old_index = self.dense_index
            value = Octet.zero() if self.dense_elements[self.dense_word_index] & select_mask(self.dense_bit_index) == 0 else Octet.one()
            self.dense_index += 1
            self.dense_bit_index += 1
            if self.dense_bit_index == 64:
                self.dense_bit_index = 0
                self.dense_word_index += 1
            return old_index, value


class OctetIter:
    def __init__(self, sparse: bool, start_col: int, end_col: int,
                 dense_elements: Optional[List[int]] = None, dense_index: int = 0,
                 dense_word_index: int = 0, dense_bit_index: int = 0,
                 sparse_elements: Optional[SparseBinaryVec] = None,
                 sparse_index: int = 0, sparse_physical_col_to_logical: Optional[List[int]] = None):
        self.sparse = sparse
        self.start_col = start_col
        self.end_col = end_col
        self.dense_elements = dense_elements
        self.dense_index = dense_index
        self.dense_word_index = dense_word_index
        self.dense_bit_index = dense_bit_index
        self.sparse_elements = sparse_elements
        self.sparse_index = sparse_index
        self.sparse_physical_col_to_logical = sparse_physical_col_to_logical

    @classmethod
    def new_sparse(cls, start_col: int, end_col: int, sparse_elements: SparseBinaryVec,
                   sparse_physical_col_to_logical: List[int]) -> 'OctetIter':
        return cls(True, start_col, end_col, None, 0, 0, 0, sparse_elements, 0, sparse_physical_col_to_logical)

    @classmethod
    def new_dense_binary(cls, start_col: int, end_col: int, start_bit: int, dense_elements: List[int]) -> 'OctetIter':
        return cls(False, 0, end_col, dense_elements, start_col, 0, start_bit, None, 0, None)

    def clone(self) -> ClonedOctetIter:
        sparse_elements = None
        if self.sparse_elements is not None:
            sparse_elements = [
                (self.sparse_physical_col_to_logical[physical_col], value)
                for physical_col, value in self.sparse_elements.keys_values()
                if self.start_col <= self.sparse_physical_col_to_logical[physical_col] < self.end_col
            ]
        return ClonedOctetIter(
            self.sparse,
            self.end_col,
            self.dense_elements.copy() if self.dense_elements else None,
            self.dense_index,
            self.dense_word_index,
            self.dense_bit_index,
            sparse_elements,
            self.sparse_index
        )

    def __iter__(self):
        return self

    def __next__(self) -> Tuple[int, Octet]:
        if self.sparse:
            if self.sparse_elements and self.sparse_index < self.sparse_elements.len():
                while self.sparse_index < self.sparse_elements.len():
                    entry = self.sparse_elements.get_by_raw_index(self.sparse_index)
                    self.sparse_index += 1
                    logical_col = self.sparse_physical_col_to_logical[entry[0]]
                    if self.start_col <= logical_col < self.end_col:
                        return logical_col, entry[1]
            raise StopIteration
        elif self.dense_index == self.end_col:
            raise StopIteration
        else:
            old_index = self.dense_index
            self.dense_index += 1
            value = Octet.zero() if self.dense_elements[self.dense_word_index] & select_mask(self.dense_bit_index) == 0 else Octet.one()
            self.dense_bit_index += 1
            if self.dense_bit_index == 64:
                self.dense_bit_index = 0
                self.dense_word_index += 1
            return old_index, value
