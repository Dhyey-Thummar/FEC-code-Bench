from utils import *
from typing import List
import copy

class Block:
    def __init__(self, data=None, padding=0):
        self.data = data
        self.padding = padding

    def length(self):
        dataLen = len(self.data) if self.data else 0
        return dataLen + self.padding

    def is_empty(self):
        return self.length() == 0

    def xor(self, a):
        # Handle empty block separately
        # If not empty, it's guaranteed that types of self.data and a.data will match
        if self.data:
                if a.data:
                    if len(self.data) < len(a.data):
                        inc = len(a.data) - len(self.data)
                        if isinstance(self.data, bytes):
                            self.data += b'\x00'*inc
                        else:
                            self.data.extend([0]*inc)
                        if self.padding > inc:
                            self.padding -= inc
                        else:
                            self.padding = 0
                
                    if isinstance(self.data, bytes):
                        res = b''
                        for i in range(len(a.data)):
                            res += (self.data[i] ^ a.data[i]).to_bytes(1, byteorder='big')
                        for i in range(len(a.data), len(self.data)):
                            res += self.data[i].to_bytes(1, byteorder='big')
                        self.data = res
                    else:
                        for i in range(len(a.data)):
                            self.data[i] = (self.data[i] ^ a.data[i])
        else:
            self.data = copy.deepcopy(a.data)

    def __str__(self):
        return str(self.data)

def partition_bytes(data, p):
    def slice_into_blocks(data, num, length):
        blocks = []
        for _ in range(num):
            if len(data) > length:
                blocks.append(Block(data[:length]))
                data = data[length:]
            else:
                blocks.append(Block(data))
                data = []
            if len(blocks[-1].data) < length:
                blocks[-1].padding = length - len(blocks[-1].data)
        return blocks, data

    len_long, len_short, num_long, num_short = partition(len(data), p)
    long_blocks, data = slice_into_blocks(data, num_long, len_long)
    short_blocks, _ = slice_into_blocks(data, num_short, len_short)
    return long_blocks, short_blocks

def equalize_block_lengths(long_blocks, short_blocks):
    if not long_blocks:
        return short_blocks
    if not short_blocks:
        return long_blocks

    for block in short_blocks:
        block.padding += long_blocks[0].length() - block.length()

    return long_blocks + short_blocks

class SparseMatrix:
    def __init__(self):
        self.coeff = []
        self.v = []

    def xor_row(self, s, indices, block):
        block.xor(self.v[s])

        new_indices = []
        coeffs = self.coeff[s]
        i, j = 0, 0
        while i < len(coeffs) and j < len(indices):
            index = indices[j]
            if coeffs[i] == index:
                i += 1
                j += 1
            elif coeffs[i] < index:
                new_indices.append(coeffs[i])
                i += 1
            else:
                new_indices.append(index)
                j += 1

        new_indices += coeffs[i:]
        new_indices += indices[j:]
        return new_indices, block

    def add_equation(self, components, block):     
        while len(components) > 0 and len(self.coeff[components[0]]) > 0:
            s = components[0]
            if len(components) >= len(self.coeff[s]):
                components, block = self.xor_row(s, components, block)
            else:
                components, self.coeff[s] = self.coeff[s], components
                block, self.v[s] = self.v[s], block

        if len(components) > 0:
            self.coeff[components[0]] = components
            self.v[components[0]] = block

    def determined(self):
        return all(len(r) > 0 for r in self.coeff)

    def reduce(self):
        for i in range(len(self.coeff) - 1, -1, -1):
            for j in range(i):
                ci, cj = self.coeff[i], self.coeff[j]
                for k in range(1, len(cj)):
                    if cj[k] == ci[0]:
                        self.v[j].xor(self.v[i])
                        continue
            self.coeff[i] = self.coeff[i][:1]

    def reconstruct(self, total_length, len_long, len_short, num_long, num_short):
        out = bytearray()
        for i in range(num_long):
            out.extend(self.v[i].data[:len_long])
        for i in range(num_long, num_long + num_short):
            out.extend(self.v[i].data[:len_short])
        return out

    def __str__(self):
        s = "-------matrix-------\n"
        for i in range(len(self.coeff)):
            s += (f"{self.coeff[i]} = {self.v[i].data}\n")
        return s