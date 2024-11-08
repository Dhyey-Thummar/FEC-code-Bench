import socket
import sys
import time
import random
import numpy as np
import math

def receive_blocks_from_input(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    print("Waiting for connection...")
    
    conn, addr = s.accept()
    print("Connection established with:", addr)
    
    # Receive start message
    start_msg = conn.recv(5).decode()
    if start_msg != "START":
        print("Error: Expected START message, got", start_msg)
        conn.close()
        return
    
    # Receive file metadata
    print("Receiving file name and length...")
    file_name = conn.recv(100).decode().strip('\0')
    file_length = int.from_bytes(conn.recv(8), sys.byteorder)
    block_size = int.from_bytes(conn.recv(8), sys.byteorder)
    block_num_size = int.from_bytes(conn.recv(8), sys.byteorder)
    num_blocks = int.from_bytes(conn.recv(8), sys.byteorder)
    print(f"File Name: {file_name}")
    print(f"File Length: {file_length} bytes")
    print(f"Block Size: {block_size} bytes")
    print(f"Block Num Size: {block_num_size} bytes")
    print(f"Number of Blocks: {num_blocks}")
    # Start receiving blocks
    print("Receiving blocks...")
    blocks = []
    start_block_msg = conn.recv(10).decode()
    if start_block_msg != "STARTBLOCK":
        print("Error: Expected STARTBLOCK message, got", start_block_msg)
        conn.close()
        return

    for i in range(num_blocks):
        block = conn.recv(block_size)
        if not block:
            break
        block_num = int.from_bytes(block[:block_num_size], sys.byteorder)
        # print("Block: ", block_num, "data: ", block[:block_num_size+10])
        blocks.append(block)

    try: 
        end_block_msg = conn.recv(8).decode()
        if end_block_msg != 'ENDBLOCK':
            print("Error: Expected ENDBLOCK message, got", end_block_msg)
        else:
            print("Received ENDBLOCK message.")
        end_msg = conn.recv(3).decode()
        if end_msg != 'END':
            print("Error: Expected END message, got", end_msg)
        else:
            print("Received END message.")
    except:
        print("Error: Invalid end message.")
    print("File transfer complete. Received", len(blocks), "blocks.")
    
    conn.close()
    s.close()
    print("Connection closed.")

    return blocks, block_size, file_name, file_length, block_num_size

def send_blocks_to_output(blocks, host, port, file_name, file_length, block_size, block_num_size, num_blocks):
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

def run_sim(host, receive_input_port, send_output_port, channel_param, probability):
    blocks, block_size, file_name, file_length, block_num_size = receive_blocks_from_input(host, receive_input_port)
    blocks = sim_channel(blocks, channel_param)
    send_blocks_to_output(blocks, host, send_output_port, file_name, file_length, block_size, block_num_size, len(blocks))

def sim_channel(blocks, channel, probability, std):
    match channel:
        case 0:
            # No dropping
            print("Not dropping any blocks.")
            return blocks
        case 1:
            # No dropping but only rearranging
            seed = random.randint(50)
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
            print("Rearranging ", k, "blocks.")
            return blocks
        case 2:
            # Dropping with probability BEC
            new_blocks = []
            k = 0
            for b in range(0, len(blocks)):
                if (random.uniform(0, 1) >= probability):
                    k = k + 1
                    new_blocks.append(blocks[b])
            print("Dropping ", len(blocks) - k, "blocks.")
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
            print("Dropping ", len(blocks) - k, "blocks.")
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
            print("Dropping ", len(blocks) - k, "blocks.")
            return new_blocks

if __name__ == '__main__':
    channel_param = int(sys.argv[0])
    channel_prob = int(sys.argv[1])
    assert(channel_param >= 0)
    assert(channel_param <= 4)
    host = 'localhost'
    receive_input_port = 12345
    send_output_port = 12346
    run_sim(host, receive_input_port, send_output_port, channel_param, channel_prob)