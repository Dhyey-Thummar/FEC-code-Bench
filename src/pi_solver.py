import copy
from typing import List, Optional, Tuple, Union

class RowOp:
    AddAssign = "AddAssign"
    Swap = "Swap"

class FirstPhaseRowSelectionStats:
    def __init__(self, matrix, end_col, end_row):
        self.original_degree = U16ArrayMap(0, 0)
        self.ones_per_row = U16ArrayMap(0, matrix.height())
        self.ones_histogram = U32VecMap(0)
        self.start_col = 0
        self.end_col = end_col
        self.start_row = 0
        self.rows_with_single_one = []
        self.col_graph = ConnectedComponentGraph(end_col)

        for row in range(matrix.height()):
            ones = matrix.count_ones(row, 0, end_col)
            self.ones_per_row.insert(row, ones)
            self.ones_histogram.increment(ones)
            if ones == 1:
                self.rows_with_single_one.append(row)

        self.original_degree = copy.deepcopy(self.ones_per_row)
        self.rebuild_connected_components(0, end_row, matrix)

    def swap_rows(self, i: int, j: int):
        self.ones_per_row.swap(i, j)
        self.original_degree.swap(i, j)
        for index, row in enumerate(self.rows_with_single_one):
            if row == i:
                self.rows_with_single_one[index] = j
            elif row == j:
                self.rows_with_single_one[index] = i

    def swap_columns(self, i: int, j: int):
        self.col_graph.swap(i, j)

    def add_graph_edge(self, row: int, matrix, start_col: int, end_col: int):
        ones = []
        for col, value in matrix.get_row_iter(row, start_col, end_col):
            if value == Octet.one():
                ones.append(col)
            if len(ones) == 2:
                break
        assert len(ones) == 2
        self.col_graph.add_edge(ones[0], ones[1])

    def remove_graph_edge(self, row: int, matrix):
        pass  # No-op as per the comments

    def recompute_row(self, row: int, matrix):
        ones = matrix.count_ones(row, self.start_col, self.end_col)
        if row in self.rows_with_single_one:
            self.rows_with_single_one.remove(row)
        if ones == 1:
            self.rows_with_single_one.append(row)
        self.ones_histogram.decrement(self.ones_per_row.get(row))
        self.ones_histogram.increment(ones)
        if self.ones_per_row.get(row) == 2:
            self.remove_graph_edge(row, matrix)
        self.ones_per_row.insert(row, ones)
        if ones == 2:
            self.add_graph_edge(row, matrix, self.start_col, self.end_col)

    def resize(self, start_row: int, end_row: int, start_col: int, end_col: int, ones_in_start_col, matrix):
        assert end_col <= self.end_col
        assert self.start_row == start_row - 1
        assert self.start_col == start_col - 1

        if matrix.get(self.start_row, self.start_col) == Octet.one():
            row = self.start_row
            self.ones_per_row.decrement(row)
            ones = self.ones_per_row.get(row)
            if ones == 0:
                if row in self.rows_with_single_one:
                    self.rows_with_single_one.remove(row)
            elif ones == 1:
                self.remove_graph_edge(row, matrix)
            self.ones_histogram.decrement(ones + 1)
            self.ones_histogram.increment(ones)

        possible_new_graph_edges = []
        for row in ones_in_start_col:
            row = int(row)
            self.ones_per_row.decrement(row)
            ones = self.ones_per_row.get(row)
            if ones == 0:
                if row in self.rows_with_single_one:
                    self.rows_with_single_one.remove(row)
            elif ones == 1:
                self.rows_with_single_one.append(row)
                self.remove_graph_edge(row, matrix)
            if ones == 2:
                possible_new_graph_edges.append(row)
            self.ones_histogram.decrement(ones + 1)
            self.ones_histogram.increment(ones)

        self.col_graph.remove_node(start_col - 1)

        for col in range(end_col, self.end_col):
            for row in matrix.get_ones_in_column(col, self.start_row, end_row):
                row = int(row)
                self.ones_per_row.decrement(row)
                ones = self.ones_per_row.get(row)
                if ones == 0:
                    if row in self.rows_with_single_one:
                        self.rows_with_single_one.remove(row)
                elif ones == 1:
                    self.rows_with_single_one.append(row)
                    self.remove_graph_edge(row, matrix)
                if ones == 2:
                    possible_new_graph_edges.append(row)
                self.ones_histogram.decrement(ones + 1)
                self.ones_histogram.increment(ones)
            self.col_graph.remove_node(col)

        for row in possible_new_graph_edges:
            if self.ones_per_row.get(row) == 2:
                self.add_graph_edge(row, matrix, start_col, end_col)

        self.start_col = start_col
        self.end_col = end_col
        self.start_row = start_row

    def first_phase_selection(self, start_row: int, end_row: int, matrix):
        r = None
        for i in range(1, self.end_col - self.start_col + 1):
            if self.ones_histogram.get(i) > 0:
                r = i
                break
        if r is None:
            return None, None

        if r == 2:
            row = self.first_phase_graph_substep(start_row, end_row, matrix)
            return row, r
        else:
            row = self.first_phase_original_degree_substep(start_row, end_row, r)
            return row, r

# Remaining classes and methods omitted for brevity; follow the similar translation pattern as shown above
