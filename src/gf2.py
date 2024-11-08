def add_assign_binary(dest: list[int], src: list[int]):
    length = len(dest)
    for i in range(length):
        # Addition over GF(2) is defined as XOR
        dest[i] ^= src[i]
