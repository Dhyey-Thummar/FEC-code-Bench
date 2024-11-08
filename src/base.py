import random
from typing import List, Tuple
from rng import rand
import unittest
from systematic_constants import *
from util import *

class PayloadId:
    def __init__(self, source_block_number: int, encoding_symbol_id: int):
        # Encoding Symbol ID must be a 24-bit unsigned int
        assert encoding_symbol_id < 16777216

        # Source Block Number must be a 8-bit unsigned int
        assert source_block_number < 256
        self.source_block_number = source_block_number
        self.encoding_symbol_id = encoding_symbol_id

    @staticmethod
    def deserialize(data: bytes) -> 'PayloadId':
        return PayloadId(
            source_block_number=data[0],
            encoding_symbol_id=(data[1] << 16) + (data[2] << 8) + data[3]
        )

    def serialize(self) -> bytes:
        return bytes([
            self.source_block_number & 0xFF,
            (self.encoding_symbol_id >> 16) & 0xFF,
            (self.encoding_symbol_id >> 8) & 0xFF,
            self.encoding_symbol_id & 0xFF
        ])

    def source_block_number(self) -> int:
        return self.source_block_number

    def encoding_symbol_id(self) -> int:
        return self.encoding_symbol_id
    
    def __eq__(self, other):
        return self.source_block_number == other.source_block_number and self.encoding_symbol_id == other.encoding_symbol_id

class EncodingPacket:
    def __init__(self, payload_id: PayloadId, data: List[int]):
        self.payload_id = payload_id
        self.data = data

    @staticmethod
    def deserialize(data: bytes) -> 'EncodingPacket':
        payload_data = data[:4]
        return EncodingPacket(
            payload_id=PayloadId.deserialize(payload_data),
            data=list(data[4:])
        )

    def serialize(self) -> bytes:
        serialized = bytearray(self.payload_id.serialize())
        serialized.extend(self.data)
        return bytes(serialized)

    def payload_id(self) -> PayloadId:
        return self.payload_id

    def data(self) -> List[int]:
        return self.data

    def split(self) -> Tuple[PayloadId, List[int]]:
        return self.payload_id, self.data
    
    def __eq__(self, other):
        return self.payload_id == other.payload_id and self.data == other.data

class ObjectTransmissionInformation:
    def __init__(self, transfer_length: int, symbol_size: int, source_blocks: int, sub_blocks: int, alignment: int):
        # See errata (https://www.rfc-editor.org/errata/eid5548)
        assert transfer_length <= 942574504275
        assert transfer_length < 2**64
        assert symbol_size < 2**16
        assert source_blocks < 2**8
        assert sub_blocks < 2**16
        assert alignment < 2**8
        assert symbol_size % alignment == 0

        if symbol_size != 0 and source_blocks != 0:
            symbols_required = int_div_ceil(int_div_ceil(transfer_length, symbol_size), source_blocks)
            assert symbols_required <= MAX_SOURCE_SYMBOLS_PER_BLOCK

        self.transfer_length = transfer_length
        self.symbol_size = symbol_size
        self.num_source_blocks = source_blocks
        self.num_sub_blocks = sub_blocks
        self.symbol_alignment = alignment

    @staticmethod
    def deserialize(data: bytes) -> 'ObjectTransmissionInformation':
        return ObjectTransmissionInformation(
            transfer_length=((data[0] << 32) + (data[1] << 24) + (data[2] << 16) + (data[3] << 8) + data[4]),
            symbol_size=(data[6] << 8) + data[7],
            source_blocks=data[8],
            sub_blocks=(data[9] << 8) + data[10],
            alignment=data[11]
        )

    def serialize(self) -> bytes:
        return bytes([
            (self.transfer_length >> 32) & 0xFF,
            (self.transfer_length >> 24) & 0xFF,
            (self.transfer_length >> 16) & 0xFF,
            (self.transfer_length >> 8) & 0xFF,
            self.transfer_length & 0xFF,
            0,  # Reserved
            (self.symbol_size >> 8) & 0xFF,
            self.symbol_size & 0xFF,
            self.num_source_blocks & 0xFF,
            (self.num_sub_blocks >> 8) & 0xFF,
            self.num_sub_blocks & 0xFF,
            self.symbol_alignment & 0xFF
        ])

    def transfer_length(self) -> int:
        return self.transfer_length

    def symbol_size(self) -> int:
        return self.symbol_size

    def source_blocks(self) -> int:
        return self.num_source_blocks

    def sub_blocks(self) -> int:
        return self.num_sub_blocks

    def symbol_alignment(self) -> int:
        return self.symbol_alignment

    @classmethod
    def with_defaults(cls, transfer_length: int, max_packet_size: int) -> 'ObjectTransmissionInformation':
        assert transfer_length < 2**64
        assert max_packet_size < 2**16

        return cls.generate_encoding_parameters(transfer_length, max_packet_size, 10 * 1024 * 1024)

    @classmethod
    def generate_encoding_parameters(cls, transfer_length: int, max_packet_size: int, decoder_memory_requirement: int) -> 'ObjectTransmissionInformation':
        assert transfer_length < 2**64
        assert max_packet_size < 2**16
        assert decoder_memory_requirement < 2**64

        alignment, sub_symbol_size = (8, 8) if max_packet_size >= 8*8 else (1, 1)
        assert max_packet_size >= alignment
        symbol_size = max_packet_size - (max_packet_size % alignment)

        kt = int_div_ceil(transfer_length, symbol_size)
        n_max = symbol_size // (sub_symbol_size * alignment)

        def get_kl(n: int) -> int:
            assert n < 2**32
            for (kprime, _, _, _, _) in reversed(SYSTEMATIC_INDICES_AND_PARAMETERS):
                x = int_div_ceil(symbol_size, alignment * n)
                if kprime <= (decoder_memory_requirement // (alignment * x)):
                    return kprime
            raise RuntimeError("Unreachable code reached")

        num_source_blocks = int_div_ceil(kt, get_kl(n_max))

        n = 1
        for i in range(1, n_max + 1):
            if int_div_ceil(kt, num_source_blocks) <= get_kl(i):
                n = i
                break

        return cls(transfer_length, symbol_size, num_source_blocks, n, alignment)

    def __eq__(self, other):
        return True

def partition(i: int, j: int) -> Tuple[int, int, int, int]:
    il = int_div_ceil(i, j)
    is_ = i // j
    jl = i - is_ * j
    js = j - jl
    return il, is_, jl, js


def deg(v: int, lt_symbols: int) -> int:
    assert v < 1048576
    f = [
        0, 5243, 529531, 704294, 791675, 844104, 879057, 904023, 922747, 937311, 948962, 958494,
        966438, 973160, 978921, 983914, 988283, 992138, 995565, 998631, 1001391, 1003887, 1006157,
        1008229, 1010129, 1011876, 1013490, 1014983, 1016370, 1017662, 1048576,
    ]
    for d in range(1, len(f)):
        if v < f[d]:
            return min(d, lt_symbols - 2)
    raise RuntimeError("Unexpected deg value")


def intermediate_tuple(internal_symbol_id: int, lt_symbols: int, systematic_index: int, p1: int) -> Tuple[int, int, int, int, int, int]:
    J = systematic_index
    W = lt_symbols
    P1 = p1

    A = 53591 + J * 997
    if A % 2 == 0:
        A += 1

    B = 10267 * (J + 1)
    y = (B + internal_symbol_id * A) % 4294967296
    v = rand(y, 0, 1048576)
    d = deg(v, W)
    a = 1 + rand(y, 1, W - 1)
    b = rand(y, 2, W)

    d1 = 2 + rand(internal_symbol_id, 3, 2) if d < 4 else 2
    a1 = 1 + rand(internal_symbol_id, 4, P1 - 1)
    b1 = rand(internal_symbol_id, 5, P1)

    return d, a, b, d1, a1, b1

if __name__ == '__main__':
    class TestEncodingModule(unittest.TestCase):
        def test_max_transfer_size(self):
            # Initialize an ObjectTransmissionInformation instance with specific parameters
            ObjectTransmissionInformation(942574504275, 65535, 255, 1, 1)

        def test_payload_id_serialization(self):
            # Create a new PayloadId with random values
            payload_id = PayloadId(
                random.randint(0, 2**8 - 1),
                random.randint(0, 256 * 256 * 256 - 1)
            )
            # Serialize and deserialize the payload_id, then check equality
            deserialized = PayloadId.deserialize(payload_id.serialize())
            self.assertTrue(deserialized == payload_id)

        def test_encoding_packet_serialization(self):
            # Create a new PayloadId and an EncodingPacket with random values
            payload_id = PayloadId(
                random.randint(0, 2**8 - 1),
                random.randint(0, 256 * 256 * 256 - 1)
            )
            packet = EncodingPacket(payload_id, [random.randint(0, 2**8-1)])
            # Serialize and deserialize the packet, then check equality
            deserialized = EncodingPacket.deserialize(packet.serialize())
            self.assertTrue(deserialized == packet)

        def test_oti_serialization(self):
            # Create a new ObjectTransmissionInformation with random values
            oti = ObjectTransmissionInformation.with_defaults(
                random.randint(0, 942574504275),
                random.randint(0, 2**8 - 1)
            )
            # Serialize and deserialize the oti, then check equality
            deserialized = ObjectTransmissionInformation.deserialize(oti.serialize())
            self.assertTrue(deserialized == oti)
    
    unittest.main()