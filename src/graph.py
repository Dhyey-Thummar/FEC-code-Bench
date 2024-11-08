from typing import Dict, List

NO_CONNECTED_COMPONENT = 0

class U16ArrayMap:
    def __init__(self, start_key: int, end_key: int):
        self.offset = start_key
        self.elements = [0] * (end_key - start_key)

    def get(self, key: int) -> int:
        return self.elements[key - self.offset]

    def insert(self, key: int, value: int):
        self.elements[key - self.offset] = value

    def increment(self, key: int):
        self.elements[key - self.offset] += 1

    def decrement(self, key: int):
        self.elements[key - self.offset] -= 1

    def swap(self, key1: int, key2: int):
        self.elements[key1 - self.offset], self.elements[key2 - self.offset] = self.elements[key2 - self.offset], self.elements[key1 - self.offset]

    def keys(self) -> range:
        return range(self.offset, self.offset + len(self.elements))


class ConnectedComponentGraph:
    def __init__(self, max_nodes: int):
        first_connected_component = NO_CONNECTED_COMPONENT + 1
        self.node_connected_component = U16ArrayMap(0, max_nodes)
        self.merged_connected_components = U16ArrayMap(
            first_connected_component, first_connected_component + max_nodes
        )
        self.connected_component_size = U16ArrayMap(
            first_connected_component, first_connected_component + max_nodes
        )
        self.num_connected_components = 0

        for i in self.merged_connected_components.keys():
            self.merged_connected_components.insert(i, i)

    def create_connected_component(self) -> int:
        self.num_connected_components += 1
        return NO_CONNECTED_COMPONENT + self.num_connected_components

    def add_node(self, node: int, connected_component: int):
        assert connected_component <= self.num_connected_components
        assert self.node_connected_component.get(node) == NO_CONNECTED_COMPONENT
        canonical = self.canonical_component_id(connected_component)
        self.node_connected_component.insert(node, canonical)
        self.connected_component_size.increment(canonical)

    def swap(self, node1: int, node2: int):
        self.node_connected_component.swap(node1, node2)

    def contains(self, node: int) -> bool:
        return self.node_connected_component.get(node) != NO_CONNECTED_COMPONENT

    def remove_node(self, node: int):
        connected_component = self.canonical_component_id(self.node_connected_component.get(node))
        if connected_component == NO_CONNECTED_COMPONENT:
            return
        self.connected_component_size.decrement(connected_component)
        self.node_connected_component.insert(node, NO_CONNECTED_COMPONENT)

    def get_node_in_largest_connected_component(self, start_node: int, end_node: int) -> int:
        max_size = 0
        largest_connected_component = NO_CONNECTED_COMPONENT
        for i in range(1, self.num_connected_components + 1):
            size = self.connected_component_size.get(i)
            if size > max_size:
                max_size = size
                largest_connected_component = i
        assert largest_connected_component != NO_CONNECTED_COMPONENT

        # Find a node (column) in that connected component
        for node in range(start_node, end_node):
            if self.canonical_component_id(self.node_connected_component.get(node)) == largest_connected_component:
                return node
        raise ValueError("No node found in the largest connected component")

    def add_edge(self, node1: int, node2: int):
        connected_component1 = self.canonical_component_id(self.node_connected_component.get(node1))
        connected_component2 = self.canonical_component_id(self.node_connected_component.get(node2))

        if connected_component1 == NO_CONNECTED_COMPONENT and connected_component2 == NO_CONNECTED_COMPONENT:
            connected_component_id = self.create_connected_component()
            self.node_connected_component.insert(node1, connected_component_id)
            self.node_connected_component.insert(node2, connected_component_id)
            self.connected_component_size.insert(connected_component_id, 2)
        elif connected_component1 == NO_CONNECTED_COMPONENT:
            self.connected_component_size.increment(connected_component2)
            self.node_connected_component.insert(node1, connected_component2)
        elif connected_component2 == NO_CONNECTED_COMPONENT:
            self.connected_component_size.increment(connected_component1)
            self.node_connected_component.insert(node2, connected_component1)
        elif connected_component1 != connected_component2:
            merge_to = min(connected_component1, connected_component2)
            merge_from = max(connected_component1, connected_component2)
            to_size = self.connected_component_size.get(merge_to)
            from_size = self.connected_component_size.get(merge_from)
            self.connected_component_size.insert(merge_from, 0)
            self.connected_component_size.insert(merge_to, to_size + from_size)
            self.merged_connected_components.insert(merge_from, merge_to)

    def canonical_component_id(self, id: int) -> int:
        if id == NO_CONNECTED_COMPONENT:
            return id
        while self.merged_connected_components.get(id) != id:
            id = self.merged_connected_components.get(id)
        return id

    def reset(self):
        for i in range(1, self.num_connected_components + 1):
            self.connected_component_size.insert(i, 0)
            self.merged_connected_components.insert(i, i)
        self.num_connected_components = 0
        for i in self.node_connected_component.keys():
            self.node_connected_component.insert(i, NO_CONNECTED_COMPONENT)
