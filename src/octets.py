import random, unittest
from octet import Octet, OCTET_MUL

class BinaryOctetVec:
    WORD_WIDTH = 64

    def __init__(self, elements, length):
        assert len(elements) == (length + self.WORD_WIDTH - 1) // self.WORD_WIDTH
        self.elements = elements
        self.length = length

    def len(self):
        return self.length

    def to_octet_vec(self):
        word = 0
        bit = self.padding_bits()
        result = []

        for _ in range(self.length):
            value = 0 if self.elements[word] & self.select_mask(bit) == 0 else 1
            result.append(value)
            bit += 1
            if bit == 64:
                word += 1
                bit = 0

        assert word == len(self.elements)
        assert bit == 0
        return result

    def padding_bits(self):
        return (self.WORD_WIDTH - (self.length % self.WORD_WIDTH)) % self.WORD_WIDTH

    @staticmethod
    def select_mask(bit):
        return 1 << bit
    
    def __eq__(self, other):
        return self.elements == other.elements and self.length == other.length


def fused_addassign_mul_scalar_binary(octets, other, scalar):
    assert scalar != Octet.zero(), "Don't call with zero. It's very inefficient"
    assert len(octets) == other.len()

    if scalar == Octet.one():
        return add_assign(octets, other.to_octet_vec())
    else:
        return fused_addassign_mul_scalar(octets, other.to_octet_vec(), scalar)


def add_assign(octets, other):
    assert len(octets) == len(other)
    for i in range(len(octets)):
        octets[i] ^= other[i]


def mulassign_scalar(octets, scalar):
    scalar_index = scalar.byte()
    for i in range(len(octets)):
        octet_index = octets[i]
        octets[i] = OCTET_MUL[scalar_index][octet_index]


def fused_addassign_mul_scalar(octets, other, scalar):
    assert scalar != Octet.one(), "Don't call this with one. Use += instead"
    assert scalar != Octet.zero(), "Don't call with zero. It's very inefficient"
    assert len(octets) == len(other)
    for i in range(len(octets)):
        octets[i] ^= OCTET_MUL[scalar.byte()][other[i]]

if __name__ == '__main__':
    class TestOctetOperations(unittest.TestCase):
        def test_mul_assign(self):
            size = 41
            scalar = Octet(random.randint(1, 254))
            data1 = [random.randint(0, 255) for _ in range(size)]
            expected = [(Octet(data1[i]) * scalar).byte() for i in range(size)]

            mulassign_scalar(data1, scalar)

            self.assertEqual(expected, data1)

        def test_fma(self):
            size = 41
            scalar = Octet(random.randint(2, 254))
            data1 = [random.randint(0, 255) for _ in range(size)]
            data2 = [random.randint(0, 255) for _ in range(size)]
            expected = [(Octet(data1[i]) + Octet(data2[i]) * scalar).byte() for i in range(size)]

            fused_addassign_mul_scalar(data1, data2, scalar)

            self.assertEqual(expected, data1)

        def test_fma_binary(self):
            size = 41
            scalar = Octet(random.randint(2, 254))
            binary_vec = [random.randint(0, 2**64 - 1) for _ in range((size + 63) // 64)]
            binary_octet_vec = BinaryOctetVec(binary_vec, size)
            data1 = [random.randint(0, 255) for _ in range(size)]
            data2 = binary_octet_vec.to_octet_vec()
            expected = [(Octet(data1[i]) + Octet(data2[i]) * scalar).byte() for i in range(size)]

            fused_addassign_mul_scalar_binary(data1, binary_octet_vec, scalar)

            self.assertEqual(expected, data1)

    unittest.main()