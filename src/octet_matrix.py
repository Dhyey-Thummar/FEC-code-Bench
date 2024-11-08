from octet import Octet
from octets import add_assign, fused_addassign_mul_scalar_binary, mulassign_scalar, fused_addassign_mul_scalar
from util import get_both_indices

class DenseOctetMatrix:
    def __init__(self, height, width, _=0):
        self.height = height
        self.width = width
        self.elements = [[0 for _ in range(width)] for _ in range(height)]

    def fma_sub_row(self, row, start_col, scalar, other):
        # This function performs fused add-assign multiplication with a binary vector
        fused_addassign_mul_scalar_binary(
            self.elements[row][start_col:start_col + len(other)],
            other,
            scalar
        )

    def set(self, i, j, value):
        self.elements[i][j] = value.byte()

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def mul_assign_row(self, row, value):
        mulassign_scalar(self.elements[row], value)

    def get(self, i, j):
        return Octet(self.elements[i][j])

    def swap_rows(self, i, j):
        self.elements[i], self.elements[j] = self.elements[j], self.elements[i]

    def swap_columns(self, i, j, start_row_hint=0):
        for row in range(start_row_hint, len(self.elements)):
            self.elements[row][i], self.elements[row][j] = self.elements[row][j], self.elements[row][i]

    def fma_rows(self, dest, multiplicand, scalar):
        assert dest != multiplicand
        dest_row, temp_row = get_both_indices(dest, multiplicand)

        if scalar == Octet.one():
            add_assign(dest_row, temp_row)
        else:
            fused_addassign_mul_scalar(dest_row, temp_row, scalar)