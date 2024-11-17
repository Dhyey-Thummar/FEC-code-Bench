from typing import List

def add_assign_binary(dest: List[int], src: List[int]):
    length = len(dest)
    for i in range(length):
        # Addition over GF(2) is defined as XOR
        dest[i] ^= src[i]
