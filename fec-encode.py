import socket
import sys
import os
import time
import random
import numpy as np
import math
from LTcode.lt import encode, decode, sampler
from struct import unpack

def encode_FEC():
    filename = "test.mp4"
    blocks = []
    with open(filename, 'rb') as f:
        for block in encode.encoder(f, 256, 2067261, sampler.DEFAULT_C, sampler.DEFAULT_DELTA):
            blocks.append(block)
    return blocks

def decode_FEC(blocks):
    with open("output_test.mp4", 'wb') as out_f:
        decode.decode(blocks, out_f)

def sim_channel(blocks, channel, probability, std):
    match channel:
        case 0:
            # No dropping
            print("Not dropping any blocks.")
            return blocks
        case 1:
            # No dropping but only rearranging
            seed = random.randint(0, 50)
            k = 0
            random.seed(seed)
            for i in range(50):
                x = random.randint(0, len(blocks))
                y = random.randint(0, len(blocks))
                if x != y:
                    k = k + 1
                    tmp = blocks[x]
                    blocks[x] = blocks[y]
                    blocks[y] = tmp
            print("Rearranging", k, "blocks.")
            return blocks
        case 2:
            # Dropping with probability BEC
            new_blocks = []
            k = 0
            for b in range(0, len(blocks)):
                if (random.uniform(0, 1) >= probability):
                    k = k + 1
                    new_blocks.append(blocks[b])
            print("Dropping", len(blocks) - k, "blocks.")
            return new_blocks
        case 3:
            # Dropping with Additive White Gaussian Noise
            new_blocks = []
            k = 0
            prob_norm_function = np.random.normal(loc=0, scale=std, size=len(blocks))
            for b in range(0, len(blocks)):
                if abs(prob_norm_function[b]) < std:
                    k = k + 1
                    new_blocks.append(blocks[b])
            print("Dropping", len(blocks) - k, "blocks.")
            return new_blocks
        case 4:
            # Dropping using the Rayleigh fading channel
            additive_norm = np.random.normal(loc=0, scale=std, size=len(blocks))
            multiplicative_norm = np.random.normal(loc=0, scale=(1/math.sqrt(2)), size=len(blocks))
            new_blocks = []
            k = 0
            for b in range(0, len(blocks)):
                if abs(additive_norm[b]) < std:
                    if abs(1 - abs(multiplicative_norm[b])) < 0.5:
                        k = k + 1
                        new_blocks.append(b)
            print("Dropping", len(blocks) - k, "blocks.")
            return new_blocks

list_blocks = encode_FEC()
print(len(list_blocks))
sim_blocks = sim_channel(list_blocks, 2, 0.03, 1)
print(len(sim_blocks))
decode_FEC(sim_blocks)
diff = os.system("diff test.mp4 output_test.mp4")
if diff == 0:
    print("Files are the same.")