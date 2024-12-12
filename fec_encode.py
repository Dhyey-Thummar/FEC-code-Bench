import socket
import sys
import os
import time
import random
import numpy as np
import math
from LTcode.lt import encode, decode, sampler
from struct import unpack
import csv

def encode_FEC(filename, blocksize=256, max_blocks=10000):
    blocks = []
    with open(filename, 'rb') as f:
        for block in encode.encoder(f, blocksize, 2067261, sampler.DEFAULT_C, sampler.DEFAULT_DELTA, max_blocks=max_blocks):
            blocks.append(block)
    return blocks

def decode_FEC(blocks, output_filename):
    with open(output_filename, 'wb') as out_f:
        decode.decode(blocks, out_f)

def sim_channel(blocks, channel, probability, std):
    match channel:
        case 0:
            # No dropping
            # print("Not dropping any blocks.")
            return blocks
        case 1:
            # No dropping but only rearranging
            seed = random.randint(0, 50)
            k = 0
            random.seed(seed)
            for i in range(min(len(blocks)//4, 1000)):
                x = random.randint(0, len(blocks) - 1)
                y = random.randint(0, len(blocks) - 1)
                # print("x:", x)
                # print("y:", y)
                if x != y:
                    k = k + 1
                    tmp = blocks[x]
                    blocks[x] = blocks[y]
                    blocks[y] = tmp
            # print("Rearranging", k, "blocks.")
            return blocks
        case 2:
            # Dropping with probability BEC
            new_blocks = []
            k = 0
            for b in range(0, len(blocks)):
                if (random.uniform(0, 1) >= probability):
                    k = k + 1
                    new_blocks.append(blocks[b])
            # print("Dropping", len(blocks) - k, "blocks.")
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
            # print("Dropping", len(blocks) - k, "blocks.")
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
                        new_blocks.append(blocks[b])
            # print("Dropping", len(blocks) - k, "blocks.")
            return new_blocks


def test_file(file_name, output_name, block_size, repetitions, max_blocks):
    encode_times = []
    decode_times = []
    filesize = os.path.getsize(file_name)
    
    for _ in range(repetitions):
        # Encode
        start1 = time.time()
        blocks = encode_FEC(file_name, block_size, max_blocks)
        end1 = time.time()
        encode_times.append(end1 - start1)
        
        start3 = time.time()
        blocks = sim_channel(blocks, 2, 0.5, 1)
        end3 = time.time()

        # Decode
        start2 = time.time()
        decode_FEC(blocks, output_name)
        end2 = time.time()
        decode_times.append(end2 - start2)
        
        # Ensure files are the same
        if os.system(f"diff {file_name} {output_name}") != 0:
            # raise ValueError(f"Files {file_name} and {output_name} are different after encoding and decoding.")
            print(f"Files {file_name} and {output_name} are different after encoding and decoding.")
            return None, None
    
    # Calculate average times
    avg_encode_time = sum(encode_times) / repetitions
    avg_decode_time = sum(decode_times) / repetitions
    
    return avg_encode_time, avg_decode_time

def main():
    # Configuration
    files = ["benchmark/input_files/data1", "benchmark/input_files/data2", "benchmark/input_files/data3", "benchmark/input_files/data4", "benchmark/input_files/data5"]  # Files of 1KB, 10KB, 100KB, 1MB, 10MB
    output_files = ["benchmark/input_files/output_data1", "benchmark/input_files/output_data2", "benchmark/input_files/output_data3", "benchmark/input_files/output_data4", "benchmark/input_files/output_data5"]
    # files = ["data1"] #10MB
    # output_files = ["output_data1"]
    max_blocks = [50000]
    block_sizes = [256, 512, 1024]
    repetitions = 5
    csv_file = "benchmark/encoding_decoding_times.csv"

    # Prepare CSV
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["File", "Num Blocks", "Avg Encode Time (s)", "Avg Decode Time (s)"])
        
        # Run tests
        for file, output_file in zip(files, output_files):
            for max_block in max_blocks:
                for block_size in block_sizes:
                    avg_encode_time, avg_decode_time = test_file(file, output_file, block_size, repetitions, max_block)
                    print(f"File: {file}, Num Blocks: {max_block}, Block Size: {block_size}, Avg Encode Time: {avg_encode_time}, Avg Decode Time: {avg_decode_time}")
                    writer.writerow([file, max_block, avg_encode_time, avg_decode_time])

if __name__ == "__main__":
    main()
