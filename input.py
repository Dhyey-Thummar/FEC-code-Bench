import socket
import pickle
from LTcode.lt import encode, sampler
import sys
import time


def encode_FEC(filename, blocksize=256, max_blocks=10000):
    blocks = []
    with open(filename, 'rb') as f:
        for block in encode.encoder(f, blocksize, 2067261, sampler.DEFAULT_C, sampler.DEFAULT_DELTA, max_blocks=max_blocks):
            blocks.append(block)
    return blocks

def send_data(sock, data):
    serialized_data = pickle.dumps(data)
    sock.sendall(len(serialized_data).to_bytes(8, 'big'))  # Send data size first
    print("Sending : ", len(serialized_data), " bytes")
    sock.sendall(serialized_data)  # Send the actual data

def main():
    try :
        filename = sys.argv[1]
        blocksize = int(sys.argv[2])
        max_blocks = int(sys.argv[3])
    except :
        print("Usage: python3 input.py <filename> <blocksize> <max_blocks>")
        sys.exit(1)
    host = 'localhost'
    port = 8000
    print("Encoding FEC...")
    start = time.time()
    blocks = encode_FEC(filename, blocksize=blocksize, max_blocks=max_blocks)
    end = time.time()
    print(f"Encoded {len(blocks)} blocks. Time taken (encoding): {end - start:.2f}s")
    print("Connecting to sim.py...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        while True:
            try:
                s.connect((host, port))
                print("Connected.")
                break
            except ConnectionRefusedError:
                print("Connection refused. Retrying...")
                time.sleep(5)
                continue
        send_data(s, blocks)
        print("Blocks sent to sim.py.")

if __name__ == "__main__":
    main()
