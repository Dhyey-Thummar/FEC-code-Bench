from typing import List, Tuple
import random, unittest
from base import intermediate_tuple
from octet import Octet
from octet_matrix import DenseOctetMatrix
from rng import rand
from systematic_constants import extended_source_block_symbols, num_hdpc_symbols, num_intermediate_symbols, num_ldpc_symbols, num_lt_symbols, num_pi_symbols, calculate_p1, systematic_index

def enc_indices(source_tuple: Tuple[int, int, int, int, int, int], lt_symbols: int, pi_symbols: int, p1: int) -> List[int]:
    w = lt_symbols
    p = pi_symbols
    d, a, b, d1, a1, b1 = source_tuple

    assert d > 0
    assert 1 <= a < w
    assert b < w
    assert d1 == 2 or d1 == 3
    assert 1 <= a1 < p1
    assert b1 < p1

    indices = [b]
    for _ in range(1, d):
        b = (b + a) % w
        indices.append(b)

    while b1 >= p:
        b1 = (b1 + a1) % p1

    indices.append(w + b1)

    for _ in range(1, d1):
        b1 = (b1 + a1) % p1
        while b1 >= p:
            b1 = (b1 + a1) % p1
        indices.append(w + b1)

    return indices

def generate_hdpc_rows(Kprime: int, S: int, H: int) -> 'DenseOctetMatrix':
    matrix = DenseOctetMatrix(H, Kprime + S + H)
    result = [[0] * (Kprime + S) for _ in range(H)]

    for i in range(H):
        result[i][Kprime + S - 1] = Octet.alpha(i).byte()

    for j in range(Kprime + S - 2, -1, -1):
        for i in range(H):
            result[i][j] = (Octet.alpha(1) * Octet(result[i][j + 1])).byte()
        rand6 = rand(j + 1, 6, H)
        rand7 = rand(j + 1, 7, H - 1)
        i1 = rand6
        i2 = (rand6 + rand7 + 1) % H
        result[i1][j] ^= Octet.one().byte()
        result[i2][j] ^= Octet.one().byte()

    for i in range(H):
        for j in range(Kprime + S):
            if result[i][j] != 0:
                matrix.set(i, j, Octet(result[i][j]))

    for i in range(H):
        matrix.set(i, i + Kprime + S, Octet.one())

    return matrix

def generate_constraint_matrix(source_block_symbols: int, encoded_symbol_indices: List[int]) -> Tuple['BinaryMatrix', 'DenseOctetMatrix']:
    Kprime = extended_source_block_symbols(source_block_symbols)
    S = num_ldpc_symbols(source_block_symbols)
    H = num_hdpc_symbols(source_block_symbols)
    W = num_lt_symbols(source_block_symbols)
    B = W - S
    P = num_pi_symbols(source_block_symbols)
    L = num_intermediate_symbols(source_block_symbols)

    assert S + H + len(encoded_symbol_indices) >= L
    matrix = BinaryMatrix(S + H + len(encoded_symbol_indices), L, P)

    for i in range(B):
        a = 1 + i // S
        b = i % S
        matrix.set(b, i, Octet.one())

        b = (b + a) % S
        matrix.set(b, i, Octet.one())

        b = (b + a) % S
        matrix.set(b, i, Octet.one())

    for i in range(S):
        matrix.set(i, i + B, Octet.one())

    for i in range(S):
        matrix.set(i, (i % P) + W, Octet.one())
        matrix.set(i, ((i + 1) % P) + W, Octet.one())

    lt_symbols = num_lt_symbols(Kprime)
    pi_symbols = num_pi_symbols(Kprime)
    sys_index = systematic_index(Kprime)
    p1 = calculate_p1(Kprime)

    for row, i in enumerate(encoded_symbol_indices):
        tuple_values = intermediate_tuple(i, lt_symbols, sys_index, p1)
        for j in enc_indices(tuple_values, lt_symbols, pi_symbols, p1):
            matrix.set(row + S + H, j, Octet.one())

    return matrix, generate_hdpc_rows(Kprime, S, H)

if __name__ == '__main__':
    from octets import add_assign, fused_addassign_mul_scalar

    def reference_generate_hdpc_rows(Kprime, S, H):
        matrix = DenseOctetMatrix(H, Kprime + S + H, 0)
        # G_HDPC

        # Generates the MT matrix
        # See section 5.3.3.3
        mt = [[0] * (Kprime + S) for _ in range(H)]
        for i in range(H):
            for j in range(Kprime + S - 1):
                rand6 = rand(j + 1, 6, H)
                rand7 = rand(j + 1, 7, H - 1)
                if i == rand6 or i == (rand6 + rand7 + 1) % H:
                    mt[i][j] = 1
            mt[i][Kprime + S - 1] = Octet.alpha(i).byte()

        # Multiply by the GAMMA matrix
        # See section 5.3.3.3
        gamma_row = [0] * (Kprime + S)
        for j in range(Kprime + S):
            gamma_row[j] = Octet.alpha((Kprime + S - 1 - j) % 255).byte()

        for i in range(H):
            result_row = [0] * (Kprime + S)
            for j in range(Kprime + S):
                scalar = Octet(mt[i][j])
                if scalar == Octet.zero():
                    continue
                if scalar == Octet.one():
                    add_assign(
                        result_row[: j + 1],
                        gamma_row[(Kprime + S - j - 1):(Kprime + S)]
                    )
                else:
                    fused_addassign_mul_scalar(
                        result_row[: j + 1],
                        gamma_row[(Kprime + S - j - 1):(Kprime + S)],
                        scalar
                    )
            for j in range(Kprime + S):
                if result_row[j] != 0:
                    matrix.set(i, j, Octet(result_row[j]))

        # I_H
        for i in range(H):
            matrix.set(i, i + (Kprime + S), Octet.one())

        return matrix

    def assert_matrices_eq(matrix1, matrix2):
        assert matrix1.height() == matrix2.height()
        assert matrix1.width() == matrix2.width()
        for i in range(matrix1.height()):
            for j in range(matrix1.width()):
                assert matrix1.get(i, j) == matrix2.get(i, j), f"Matrices are not equal at row={i} col={j}"

    class TestHDPCGeneration(unittest.TestCase):
        def test_fast_hdpc(self):
            source_block_symbols = random.randint(1, 49999)
            Kprime = extended_source_block_symbols(source_block_symbols)
            S = num_ldpc_symbols(source_block_symbols)
            H = num_hdpc_symbols(source_block_symbols)
            expected = reference_generate_hdpc_rows(Kprime, S, H)
            generated = generate_hdpc_rows(Kprime, S, H)
            assert_matrices_eq(expected, generated)


    unittest.main()