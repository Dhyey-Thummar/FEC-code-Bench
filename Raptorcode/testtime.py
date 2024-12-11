from utils import *
from raptor import *
import math

NUM_BLOCKS = 1000

l, s, h = intermediate_symbols(NUM_BLOCKS)
print(l, s, h)

k = NUM_BLOCKS
hprime = int(math.ceil(h/2))
print(hprime)
m = build_gray_sequence(k+s, hprime)

print(m)