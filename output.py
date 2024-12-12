import socket
import pickle
import os
from LTcode.lt import decode
import sys
import time

def decode_FEC(blocks, output_filename):
    with open(output_filename, 'wb') as out_f:
        decode.decode(blocks, out_f)

def receive_data(sock):
    data_size = int.from_bytes(sock.recv(8), 'big')  # Receive data size
    data = b""
    while len(data) < data_size:
        packet = sock.recv(4096)
        if not packet:
            break
        data += packet
    return pickle.loads(data)

def main():
    host = 'localhost'
    port = 8001
    try:
        filename = sys.argv[1]
    except:
        print("Usage: python3 output.py <input filename>")
        sys.exit(1)
    filename = sys.argv[1]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(1)
        print("Waiting for sim.py...")
        conn, addr = s.accept()
        with conn:
            blocks = receive_data(conn)
            print(f"Received {len(blocks)} blocks from sim.py.")

    output_filename = "output_" + filename
    start = time.time()
    decode_FEC(blocks, output_filename)
    end = time.time()
    print(f"File reconstructed. Time taken (decoding): {end - start:.2f}s")

    diff = os.system("diff test.mp4 output_test.mp4")
    if diff == 0:
        print("Files are the same.")
    else:
        print("Files are different.")

if __name__ == "__main__":
    main()
