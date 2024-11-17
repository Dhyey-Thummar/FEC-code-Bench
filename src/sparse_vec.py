from typing import List, Optional, Callable, Tuple
from bisect import bisect_left
from octet import Octet

class SparseBinaryVec:
    def __init__(self, capacity: int):
        assert capacity < 65536, "Capacity must be less than 65536"
        self.elements: List[int] = []

    @staticmethod
    def with_capacity(capacity):
        assert capacity < 65536, "Capacity must be less than 65536"
        return SparseBinaryVec(capacity)

    def key_to_internal_index(self, i: int) -> int:
        """Returns index of key or where it can be inserted."""
        assert i < 2**16
        index = bisect_left(self.elements, i)
        if index < len(self.elements) and self.elements[index] == i:
            return index
        return -1 - index  # This mimics the Rust behavior where Err(index) is negative

    def size_in_bytes(self) -> int:
        return (4 + len(self.elements) * 2)  # Estimate based on size of int and list items

    def len(self) -> int:
        return len(self.elements)

    def get_by_raw_index(self, i: int) -> Tuple[int, Octet]:
        return self.elements[i], Octet.one()

    def add_assign(self, other: 'SparseBinaryVec') -> bool:
        """Add elements from another vector in GF(2) logic (1 + 1 = 0)."""
        if len(other.elements) == 1:
            other_index = other.elements[0]
            index = self.key_to_internal_index(other_index)
            if index >= 0:
                self.elements.pop(index)
                return False
            else:
                self.elements.insert(-1 - index, other_index)
                return True

        result = []
        self_iter = iter(self.elements)
        other_iter = iter(other.elements)
        self_next = next(self_iter, None)
        other_next = next(other_iter, None)

        column_added = False
        while self_next is not None or other_next is not None:
            if self_next is not None and (other_next is None or self_next < other_next):
                result.append(self_next)
                self_next = next(self_iter, None)
            elif other_next is not None and (self_next is None or other_next < self_next):
                column_added = True
                result.append(other_next)
                other_next = next(other_iter, None)
            else:  # self_next == other_next
                self_next = next(self_iter, None)
                other_next = next(other_iter, None)
        self.elements = result
        return column_added

    def remove(self, i: int) -> Optional[Octet]:
        index = self.key_to_internal_index(i & 0xFFFF)
        if index >= 0:
            self.elements.pop(index)
            return Octet.one()
        return None

    def retain(self, predicate: Callable[[Tuple[int, Octet]], bool]):
        self.elements = [entry for entry in self.elements if predicate(entry, Octet.one())]

    def get(self, i: int) -> Optional[Octet]:
        index = self.key_to_internal_index(i & 0xFFFF)
        return Octet.one() if index >= 0 else Octet.zero()

    def keys_values(self):
        return ((entry, Octet.one()) for entry in self.elements)

    def insert(self, i: int, value: Octet):
        assert i < 65536, "Index must be less than 65536"
        if value == Octet.zero():
            self.remove(i)
        else:
            index = self.key_to_internal_index(i & 0xFFFF)
            if index < 0:
                self.elements.insert(-1 - index, i)
