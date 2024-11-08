from typing import List, Tuple, Iterator, Iterable, Union

class ImmutableListMap:
    def __init__(self, offsets: List[int], values: List[int]):
        self.offsets = offsets
        self.values = values

    def get(self, i: int) -> List[int]:
        start = self.offsets[i]
        end = len(self.values) if i == len(self.offsets) - 1 else self.offsets[i + 1]
        return self.values[start:end]

    def size_in_bytes(self) -> int:
        from sys import getsizeof
        return getsizeof(self) + getsizeof(int) * len(self.offsets) + getsizeof(int) * len(self.values)


class ImmutableListMapBuilder:
    def __init__(self, num_keys: int):
        self.entries: List[Tuple[int, int]] = []
        self.num_keys = num_keys

    def add(self, key: int, value: int):
        self.entries.append((key, value))

    def build(self) -> ImmutableListMap:
        self.entries.sort(key=lambda x: x[0])
        assert len(self.entries) < (2**32)
        assert self.entries

        offsets = [2**32 - 1] * self.num_keys
        last_key = self.entries[0][0]
        offsets[last_key] = 0
        values = []
        for index, (key, value) in enumerate(self.entries):
            if last_key != key:
                last_key = key
                offsets[key] = index
            values.append(value)

        for i in range(len(offsets) - 1, -1, -1):
            if offsets[i] == 2**32 - 1:
                offsets[i] = len(self.entries) if i == len(offsets) - 1 else offsets[i + 1]

        return ImmutableListMap(offsets, values)


class UndirectedGraph:
    def __init__(self, start_node: int, end_node: int, edges: int):
        self.edges: List[Tuple[int, int]] = []
        self.node_edge_starting_index = U32VecMap.with_capacity(start_node, end_node)

    def add_edge(self, node1: int, node2: int):
        self.edges.append((node1, node2))
        self.edges.append((node2, node1))

    def build(self):
        self.edges.sort(key=lambda x: x[0])
        if not self.edges:
            return
        last_node = self.edges[0][0]
        self.node_edge_starting_index.insert(last_node, 0)
        for index, (node, _) in enumerate(self.edges):
            if last_node != node:
                last_node = node
                self.node_edge_starting_index.insert(last_node, index)

    def get_adjacent_nodes(self, node: int) -> Iterator[int]:
        first_candidate = self.node_edge_starting_index.get(node)
        return AdjacentIterator(iter(self.edges[first_candidate:]), node)

    def nodes(self) -> List[int]:
        result = []
        for node, _ in self.edges:
            if not result or result[-1] != node:
                result.append(node)
        return result


class AdjacentIterator:
    def __init__(self, edges: Iterable[Tuple[int, int]], node: int):
        self.edges = iter(edges)
        self.node = node

    def __iter__(self) -> 'AdjacentIterator':
        return self

    def __next__(self) -> int:
        for node, adjacent in self.edges:
            if node == self.node:
                return adjacent
        raise StopIteration


class U16ArrayMap:
    def __init__(self, start_key: int, end_key: int):
        self.offset = start_key
        self.elements = [0] * (end_key - start_key)

    def size_in_bytes(self) -> int:
        from sys import getsizeof
        return getsizeof(self) + getsizeof(int) * len(self.elements)

    def swap(self, key: int, other_key: int):
        self.elements[key - self.offset], self.elements[other_key - self.offset] = self.elements[other_key - self.offset], self.elements[key - self.offset]

    def keys(self) -> range:
        return range(self.offset, self.offset + len(self.elements))

    def insert(self, key: int, value: int):
        self.elements[key - self.offset] = value

    def get(self, key: int) -> int:
        return self.elements[key - self.offset]

    def decrement(self, key: int):
        self.elements[key - self.offset] -= 1

    def increment(self, key: int):
        self.elements[key - self.offset] += 1


class U32VecMap:
    def __init__(self, start_key: int):
        self.offset = start_key
        self.elements = [0]

    @classmethod
    def with_capacity(cls, start_key: int, end_key: int) -> 'U32VecMap':
        return cls(start_key, [0] * (end_key - start_key))

    def grow_if_necessary(self, index: int):
        if index >= len(self.elements):
            self.elements.extend([0] * (index - len(self.elements) + 1))

    def size_in_bytes(self) -> int:
        from sys import getsizeof
        return getsizeof(self) + getsizeof(int) * len(self.elements)

    def insert(self, key: int, value: int):
        self.grow_if_necessary(key - self.offset)
        self.elements[key - self.offset] = value

    def get(self, key: int) -> int:
        if key - self.offset >= len(self.elements):
            return 0
        return self.elements[key - self.offset]

    def decrement(self, key: int):
        self.grow_if_necessary(key - self.offset)
        self.elements[key - self.offset] -= 1

    def increment(self, key: int):
        self.grow_if_necessary(key - self.offset)
        self.elements[key - self.offset] += 1


# Test case equivalent in Python
def test_list_map():
    builder = ImmutableListMapBuilder(10)
    builder.add(0, 1)
    builder.add(3, 1)
    builder.add(3, 2)

    map_instance = builder.build()
    assert 1 in map_instance.get(0)
    assert 2 not in map_instance.get(0)

    assert 1 in map_instance.get(3)
    assert 2 in map_instance.get(3)
    assert 3 not in map_instance.get(3)

    assert 1 not in map_instance.get(2)

if __name__ == "__main__":
    test_list_map()