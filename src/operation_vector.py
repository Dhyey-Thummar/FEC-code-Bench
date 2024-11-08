from enum import Enum
from typing import List, Union


class SymbolOps(Enum):
    AddAssign = "AddAssign"
    MulAssign = "MulAssign"
    FMA = "FMA"
    Reorder = "Reorder"


class Symbol:
    def __init__(self, data: List[int]):
        self.data = data

    def as_bytes(self):
        return self.data

    def __iadd__(self, other):
        self.data = [x ^ y for x, y in zip(self.data, other.data)]
        return self

    def mulassign_scalar(self, scalar):
        self.data = [(x * scalar.byte()) % 256 for x in self.data]

    def fused_addassign_mul_scalar(self, other, scalar):
        self.data = [x ^ ((y * scalar.byte()) % 256) for x, y in zip(self.data, other.data)]


class Octet:
    def __init__(self, value: int):
        self.value = value

    @staticmethod
    def new(value: int):
        return Octet(value)

    @staticmethod
    def zero():
        return Octet(0)

    @staticmethod
    def one():
        return Octet(1)

    def byte(self):
        return self.value

    def __mul__(self, other):
        if isinstance(other, Octet):
            return Octet((self.value * other.value) % 256)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Octet):
            return self.value == other.value
        return False


def get_both_indices(symbols: List[Symbol], dest: int, src: int):
    return symbols[dest], symbols[src]


def perform_op(op: Union[SymbolOps, dict], symbols: List[Symbol]):
    if op["type"] == SymbolOps.AddAssign.value:
        dest, temp = get_both_indices(symbols, op["dest"], op["src"])
        dest += temp
    elif op["type"] == SymbolOps.MulAssign.value:
        symbols[op["dest"]].mulassign_scalar(op["scalar"])
    elif op["type"] == SymbolOps.FMA.value:
        dest, temp = get_both_indices(symbols, op["dest"], op["src"])
        dest.fused_addassign_mul_scalar(temp, op["scalar"])
    elif op["type"] == SymbolOps.Reorder.value:
        temp_symbols = [symbol for symbol in symbols]
        symbols.clear()
        for row_index in op["order"]:
            symbols.append(temp_symbols[row_index])


# Tests (translated to Python)

import random


def test_add():
    rows = 2
    symbol_size = 1316
    data = [Symbol([random.randint(0, 255) for _ in range(symbol_size)]) for _ in range(rows)]

    data0 = [data[0].as_bytes()[i] for i in range(symbol_size)]
    data1 = [data[1].as_bytes()[i] for i in range(symbol_size)]
    result = [x ^ y for x, y in zip(data0, data1)]

    symbol0 = Symbol(data0)
    symbol1 = Symbol(data1)
    symbol0 += symbol1

    perform_op({"type": SymbolOps.AddAssign.value, "dest": 0, "src": 1}, data)
    assert result == data[0].as_bytes()


def test_add_mul():
    rows = 2
    symbol_size = 1316
    data = [Symbol([random.randint(0, 255) for _ in range(symbol_size)]) for _ in range(rows)]

    value = 173
    data0 = [data[0].as_bytes()[i] for i in range(symbol_size)]
    data1 = [data[1].as_bytes()[i] for i in range(symbol_size)]
    result = [x ^ ((Octet.new(y) * Octet.new(value)).byte()) for x, y in zip(data0, data1)]

    perform_op({"type": SymbolOps.FMA.value, "dest": 0, "src": 1, "scalar": Octet.new(value)}, data)
    assert result == data[0].as_bytes()


def test_mul():
    rows = 1
    symbol_size = 1316
    data = [Symbol([random.randint(0, 255) for _ in range(symbol_size)]) for _ in range(rows)]

    value = 215
    data0 = [data[0].as_bytes()[i] for i in range(symbol_size)]
    result = [(Octet.new(x) * Octet.new(value)).byte() for x in data0]

    perform_op({"type": SymbolOps.MulAssign.value, "dest": 0, "scalar": Octet.new(value)}, data)
    assert result == data[0].as_bytes()


def test_reorder():
    rows = 10
    symbol_size = 10
    data = [Symbol([i] * symbol_size) for i in range(rows)]

    assert data[0].as_bytes()[0] == 0
    assert data[1].as_bytes()[0] == 1
    assert data[2].as_bytes()[0] == 2
    assert data[9].as_bytes()[0] == 9

    perform_op({"type": SymbolOps.Reorder.value, "order": [9, 7, 5, 3, 1, 8, 0, 6, 2, 4]}, data)
    assert data[0].as_bytes()[0] == 9
    assert data[1].as_bytes()[0] == 7
    assert data[2].as_bytes()[0] == 5
    assert data[3].as_bytes()[0] == 3
    assert data[4].as_bytes()[0] == 1
    assert data[5].as_bytes()[0] == 8
    assert data[6].as_bytes()[0] == 0
    assert data[7].as_bytes()[0] == 6
    assert data[8].as_bytes()[0] == 2
    assert data[9].as_bytes()[0] == 4


# Run tests
test_add()
test_add_mul()
test_mul()
test_reorder()
