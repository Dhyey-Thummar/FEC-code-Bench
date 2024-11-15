import socket
import sys
import os
import time
from LTcode import lt

BLOCK_NUM_SIZE = 4

# Split the input file into multiple blocks
def split_file(file, block_size, block_num_size=BLOCK_NUM_SIZE):
    file_length = os.path.getsize(file)
    print("File Name: ", file)
    print("File size: ", file_length)
    file = open(file, 'rb')
    f_bytes = file.read()
    # Add 4 bytes to the blocks at the beginning to store the block number, as well as padding the last block
    blocks = []
    actual_block_size = block_size - BLOCK_NUM_SIZE
    for i in range(0, file_length, actual_block_size):
        block_num = i // actual_block_size
        block = block_num.to_bytes(BLOCK_NUM_SIZE, sys.byteorder) + f_bytes[i:i+actual_block_size].ljust(actual_block_size, b'0')
        blocks.append(block)
    return file_length, blocks

def send_blocks_to_sim(blocks, host, port, file_name, file_length, block_size, block_num_size, num_blocks):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            s.connect((host, port))
            break
        except ConnectionRefusedError:
            print("Connection refused. Retrying...")
            time.sleep(5)
            continue
    print("Sending file name and length...")
    s.sendall("START".encode())
    # truncate the file name to 100 bytes if it is too long, or pad with 0s if it is shorter
    file_name = file_name.ljust(100, '\0')
    s.sendall(file_name.encode())
    s.sendall(file_length.to_bytes(8, sys.byteorder))
    s.sendall(block_size.to_bytes(8, sys.byteorder))
    s.sendall(block_num_size.to_bytes(8, sys.byteorder))
    s.sendall(num_blocks.to_bytes(8, sys.byteorder))
    print("Sending blocks...")
    s.sendall("STARTBLOCK".encode())
    for block in blocks:
        s.sendall(block)
    s.sendall("ENDBLOCK".encode())
    s.sendall("END".encode())
    s.close()

def encode_FEC(blocks):
    filename = "pipeline.png"
    blocks = lt.encode.encoder(filename, 8, 2067261, lt.sampler.DEFAULT_C, lt.sampler.DEFAULT_DELTA)
    return blocks

if __name__ == '__main__':
    input_file = sys.argv[1]
    block_size = int(sys.argv[2])
    send_sim_port = 12345
    file_length, blocks = split_file(input_file, block_size)
    print("Number of blocks: ", len(blocks))
    print("Block size: ", block_size)
    print("First few bytes of first block: ", blocks[0][:10])
    print("Last few bytes of last block: ", blocks[-1][-10:])
    blocks = encode_FEC(blocks)
    send_blocks_to_sim(blocks, 'localhost', send_sim_port, input_file, file_length, block_size, BLOCK_NUM_SIZE, len(blocks))