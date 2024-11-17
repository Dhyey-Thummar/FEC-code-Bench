from typing import List, Tuple, TypeVar

T = TypeVar('T')

def get_both_ranges(vector: List[T], i: int, j: int, length: int) -> Tuple[List[T], List[T]]:
    assert i != j, "Indices must be different"
    assert i + length <= len(vector), "First range exceeds vector length"
    assert j + length <= len(vector), "Second range exceeds vector length"

    if i < j:
        assert i + length <= j, "Ranges must not overlap"
        first, last = vector[:j], vector[j:]
        return first[i:i + length], last[:length]
    else:
        assert j + length <= i, "Ranges must not overlap"
        first, last = vector[:i], vector[i:]
        return last[:length], first[j:j + length]

def get_both_indices(vector: List[T], i: int, j: int) -> Tuple[T, T]:
    assert i != j, "Indices must be different"
    assert i < len(vector), "Index i is out of bounds"
    assert j < len(vector), "Index j is out of bounds"

    if i < j:
        first, last = vector[:j], vector[j:]
        return first[i], last[0]
    else:
        first, last = vector[:i], vector[i:]
        return last[0], first[j]

def int_div_ceil(num: int, denom: int) -> int:
    """Integer division with ceiling.
    This assumes denom is not zero, and that the result will not overflow a 32-bit integer."""
    assert denom != 0, "Denominator must not be zero"
    result = (num // denom + 1) if num % denom != 0 else (num // denom)
    return result & 0xFFFF