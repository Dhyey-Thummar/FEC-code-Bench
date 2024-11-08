import random
from typing import List, Tuple, Optional


SPARSE_MATRIX_THRESHOLD = 250


class EncoderBuilder:
    def __init__(self):
        self.decoder_memory_requirement = 10 * 1024 * 1024
        self.max_packet_size = 1024

    def set_decoder_memory_requirement(self, bytes: int):
        self.decoder_memory_requirement = bytes

    def set_max_packet_size(self, bytes: int):
        self.max_packet_size = bytes

    def build(self, data: bytes) -> 'Encoder':
        config = ObjectTransmissionInformation.generate_encoding_parameters(
            len(data), self.max_packet_size, self.decoder_memory_requirement
        )
        return Encoder(data, config)


def calculate_block_offsets(data: bytes, config: 'ObjectTransmissionInformation') -> List[Tuple[int, int]]:
    kt = (config.transfer_length + config.symbol_size - 1) // config.symbol_size
    kl, ks, zl, zs = partition(kt, config.source_blocks)

    data_index = 0
    blocks = []
    for _ in range(zl):
        offset = kl * config.symbol_size
        blocks.append((data_index, data_index + offset))
        data_index += offset

    for _ in range(zs):
        offset = ks * config.symbol_size
        if data_index + offset > len(data):
            assert kt * config.symbol_size > len(data)
        blocks.append((data_index, data_index + offset))
        data_index += offset

    return blocks


class Encoder:
    def __init__(self, data: bytes, config: 'ObjectTransmissionInformation'):
        self.config = config
        self.blocks = []
        cached_plan = None

        for i, (start, end) in enumerate(calculate_block_offsets(data, config)):
            if end > len(data):
                padded = data[start:] + bytes(end - len(data))
                block = padded
            else:
                block = data[start:end]

            symbol_count = len(block) // config.symbol_size
            if not cached_plan or cached_plan.source_symbol_count != symbol_count:
                plan = SourceBlockEncodingPlan.generate(symbol_count)
                cached_plan = plan

            self.blocks.append(
                SourceBlockEncoder.with_encoding_plan(i, config, block, cached_plan)
            )

    @classmethod
    def with_defaults(cls, data: bytes, mtu: int) -> 'Encoder':
        config = ObjectTransmissionInformation.with_defaults(len(data), mtu)
        return cls(data, config)

    def get_config(self) -> 'ObjectTransmissionInformation':
        return self.config

    def get_encoded_packets(self, repair_packets_per_block: int) -> List['EncodingPacket']:
        packets = []
        for encoder in self.blocks:
            packets.extend(encoder.source_packets())
            packets.extend(encoder.repair_packets(0, repair_packets_per_block))
        return packets

    def get_block_encoders(self) -> List['SourceBlockEncoder']:
        return self.blocks


class SourceBlockEncodingPlan:
    def __init__(self, operations: List['SymbolOps'], source_symbol_count: int):
        self.operations = operations
        self.source_symbol_count = source_symbol_count

    @classmethod
    def generate(cls, symbol_count: int) -> 'SourceBlockEncodingPlan':
        symbols = [Symbol.new(bytes([0])) for _ in range(symbol_count)]
        _, ops = gen_intermediate_symbols(symbols, 1, SPARSE_MATRIX_THRESHOLD)
        return cls(ops, symbol_count)


class SourceBlockEncoder:
    def __init__(self, source_block_id: int, source_symbols: List['Symbol'], intermediate_symbols: List['Symbol']):
        self.source_block_id = source_block_id
        self.source_symbols = source_symbols
        self.intermediate_symbols = intermediate_symbols

    @classmethod
    def with_encoding_plan(cls, source_block_id: int, config: 'ObjectTransmissionInformation', data: bytes, plan: 'SourceBlockEncodingPlan') -> 'SourceBlockEncoder':
        source_symbols = cls.create_symbols(config, data)
        assert len(source_symbols) == plan.source_symbol_count
        intermediate_symbols = gen_intermediate_symbols_with_plan(source_symbols, config.symbol_size, plan.operations)
        return cls(source_block_id, source_symbols, intermediate_symbols)

    @staticmethod
    def create_symbols(config: 'ObjectTransmissionInformation', data: bytes) -> List['Symbol']:
        assert len(data) % config.symbol_size == 0
        return [Symbol(data[i:i + config.symbol_size]) for i in range(0, len(data), config.symbol_size)]

    def source_packets(self) -> List['EncodingPacket']:
        return [EncodingPacket(PayloadId(self.source_block_id, i), symbol.data) for i, symbol in enumerate(self.source_symbols)]

    def repair_packets(self, start_repair_symbol_id: int, packets: int) -> List['EncodingPacket']:
        start_encoding_symbol_id = start_repair_symbol_id + extended_source_block_symbols(len(self.source_symbols))
        result = []
        lt_symbols = num_lt_symbols(len(self.source_symbols))
        sys_index = systematic_index(len(self.source_symbols))
        p1 = calculate_p1(len(self.source_symbols))
        for i in range(packets):
            tuple_values = intermediate_tuple(start_encoding_symbol_id + i, lt_symbols, sys_index, p1)
            result.append(EncodingPacket(PayloadId(self.source_block_id, len(self.source_symbols) + start_repair_symbol_id + i), enc(len(self.source_symbols), self.intermediate_symbols, tuple_values).data))
        return result


class ObjectTransmissionInformation:
    def __init__(self, transfer_length: int, symbol_size: int, source_blocks: int, sub_blocks: int, symbol_alignment: int):
        self.transfer_length = transfer_length
        self.symbol_size = symbol_size
        self.source_blocks = source_blocks
        self.sub_blocks = sub_blocks
        self.symbol_alignment = symbol_alignment

    @classmethod
    def with_defaults(cls, length: int, mtu: int) -> 'ObjectTransmissionInformation':
        return cls(length, mtu, 1, 1, 1)

    @classmethod
    def generate_encoding_parameters(cls, length: int, mtu: int, memory_requirement: int) -> 'ObjectTransmissionInformation':
        return cls(length, mtu, 1, 1, 1)


class EncodingPacket:
    def __init__(self, payload_id: 'PayloadId', data: bytes):
        self.payload_id = payload_id
        self.data = data


class PayloadId:
    def __init__(self, source_block_id: int, symbol_id: int):
        self.source_block_id = source_block_id
        self.symbol_id = symbol_id


class Symbol:
    def __init__(self, data: bytes):
        self.data = data

    def __add__(self, other: 'Symbol') -> 'Symbol':
        return Symbol(bytes(a ^ b for a, b in zip(self.data, other.data)))

    @classmethod
    def new(cls, data: bytes) -> 'Symbol':
        return cls(data)


def extended_source_block_symbols(symbols: int) -> int:
    return symbols  # Placeholder


def num_lt_symbols(symbols: int) -> int:
    return symbols  # Placeholder


def systematic_index(symbols: int) -> int:
    return symbols  # Placeholder


def calculate_p1(symbols: int) -> int:
    return symbols  # Placeholder


def gen_intermediate_symbols(source_symbols: List['Symbol'], symbol_size: int, threshold: int) -> Tuple[List['Symbol'], List['SymbolOps']]:
    # Placeholder function
    return source_symbols, []


def gen_intermediate_symbols_with_plan(source_symbols: List['Symbol'], symbol_size: int, operation_vector: List['SymbolOps']) -> List['Symbol']:
    # Placeholder function
    return source_symbols


def intermediate_tuple(symbol_id: int, lt_symbols: int, sys_index: int, p1: int) -> Tuple[int, int, int, int, int, int]:
    # Placeholder function
    return (0, 0, 0, 0, 0, 0)


def enc(symbols_count: int, intermediate_symbols: List['Symbol'], source_tuple: Tuple[int, int, int, int, int, int]) -> 'Symbol':
    # Placeholder function
    return intermediate_symbols[0]
