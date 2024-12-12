import socket
import pickle
import random
import numpy as np
import math
import time
import sys

def sim_channel(blocks, channel=0, probability=0, std=1):
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

def receive_data(sock):
    data_size = int.from_bytes(sock.recv(8), 'big')  # Receive data size
    data = b""
    while len(data) < data_size:
        packet = sock.recv(4096)
        if not packet:
            break
        data += packet
    return pickle.loads(data)

def send_data(sock, data):
    serialized_data = pickle.dumps(data)
    sock.sendall(len(serialized_data).to_bytes(8, 'big'))  # Send data size first
    sock.sendall(serialized_data)  # Send the actual data

def main():
    host = 'localhost'
    port_receive = 8000
    port_send = 8001
    try :
        channel = int(sys.argv[1])
        probability = float(sys.argv[2])
        std = float(sys.argv[3])
    except :
        print("Usage: python3 sim.py <channel> <probability> <std>")
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_recv:
        s_recv.bind((host, port_receive))
        s_recv.listen(1)
        print("Waiting for input.py...")
        conn, addr = s_recv.accept()
        with conn:
            blocks = receive_data(conn)
            print(f"Received {len(blocks)} blocks from input.py.")

    start = time.time()
    sim_blocks = sim_channel(blocks, channel, probability, std)
    end = time.time()
    print(f"After simulation: {len(sim_blocks)} blocks. Time taken (sim): {end - start:.2f}s")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_send:
        while True:
            try:
                s_send.connect((host, port_send))
                print("Connected.")
                break
            except :
                print("Connection refused. Retrying...")
                time.sleep(5)
                continue
        send_data(s_send, sim_blocks)
        print("Simulated blocks sent to output.py.")

if __name__ == "__main__":
    main()
