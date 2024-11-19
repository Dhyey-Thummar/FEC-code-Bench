import math
import random
from bisect import bisect_left
from functools import lru_cache
from constants import *

def soliton_distribution(n):
    cdf = [0.0] * (n + 1)
    cdf[1] = 1 / float(n)
    for i in range(2, n + 1):
        cdf[i] = cdf[i - 1] + (1 / (float(i) * float(i - 1)))
    return cdf

def robust_soliton_distribution(n, m, delta):
    pdf = [0.0] * (n + 1)
    pdf[1] = 1 / float(n) + 1 / float(m)
    total = pdf[1]
    for i in range(2, n + 1):
        pdf[i] = (1 / (float(i) * float(i - 1)))
        if i < m:
            pdf[i] += 1 / (float(i) * float(m))
        if i == m:
            pdf[i] += math.log(float(n) / (float(m) * delta)) / float(m)
        total += pdf[i]

    cdf = [0.0] * (n + 1)
    for i in range(1, n + 1):
        pdf[i] /= total
        cdf[i] = cdf[i - 1] + pdf[i]
    return cdf

def online_soliton_distribution(eps):
    f = math.ceil(math.log(eps * eps / 4) / math.log(1 - (eps / 2)))
    cdf = [0.0] * (int(f) + 1)

    rho = 1 - ((1 + (1 / f)) / (1 + eps))
    cdf[1] = rho

    for i in range(2, int(f) + 1):
        rho_i = ((1 - rho) * f) / ((f - 1) * (i - 1) * i)
        cdf[i] = cdf[i - 1] + rho_i

    return cdf

def pick_degree(random_instance, cdf):
    r = random_instance.random()
    d = bisect_left(cdf, r)
    if d < len(cdf) and cdf[d] > r:
        return d
    return min(d + 1, len(cdf) - 1)

def sample_uniform(random_instance, num, max_val):
    if num >= max_val:
        return sorted(range(max_val))

    picks = set()
    while len(picks) < num:
        picks.add(random_instance.randint(0, max_val - 1))
    return sorted(picks)

def partition(i, j):
    il = math.ceil(i / j)
    is_ = math.floor(i / j)
    jl = i - (is_ * j)
    js = j - jl

    if jl == 0:
        il = 0
    if js == 0:
        is_ = 0

    return il, is_, jl, js

def factorial(x):
    result = 1
    for i in range(1, x + 1):
        result *= i
    return result

import math

def center_binomial(x):
    """
    Calculate choose(x, ceil(x/2)) = x! / (x/2)! / (x - (x/2))!
    """
    return choose(x, x // 2)

def choose(n, k):
    """
    Calculate the binomial coefficient "n choose k".
    Handles large n/k values.
    """
    if k > n // 2:
        k = n - k

    numerator = list(range(k + 1, n + 1))
    denominator = list(range(1, n - k + 1))

    for j in range(len(denominator) - 1, -1, -1):
        for i in range(len(numerator) - 1, -1, -1):
            if numerator[i] % denominator[j] == 0:
                numerator[i] //= denominator[j]
                denominator[j] = 1
                break

    result = 1
    for value in numerator:
        result *= value
    return result

def bit_set(x, b):
    return (x >> b) & 1 == 1

def bits_set(x):
    x -= (x >> 1) & 0x5555555555555555
    x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
    x = (x + (x >> 4)) & 0x0f0f0f0f0f0f0f0f
    return (x * 0x0101010101010101) >> 56

def gray_code(x):
    return (x >> 1) ^ x

def build_gray_sequence(length, b):
    seq = []
    x = 0
    while len(seq) < length:
        g = gray_code(x)
        if bits_set(g) == b:
            seq.append(g)
        x += 1
    return seq


def is_prime(x):
    for p in smallPrimes:
        if p * p > x:
            return True
        if x % p == 0:
            return False
    return True

def smallest_prime_greater_or_equal(x):
    if x <= smallPrimes[-1]:
        idx = bisect_left(smallPrimes, x)
        return smallPrimes[idx]
    while not is_prime(x):
        x += 1
    return x
