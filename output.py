import socket
import sys
import os
import io

BLOCK_NUM_SIZE = 4

def receive_blocks_from_sim(host, port):
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


# Reassemble the blocks into the original file
def reassemble_file(blocks, block_size, file_name, file_length, block_num_size):
    actual_block_size = block_size - block_num_size
    blocks.sort(key=lambda x: int.from_bytes(x[:block_num_size], sys.byteorder))
    file = io.BytesIO()
    for block in blocks:
        # print(int.from_bytes(block[:block_num_size], sys.byteorder), end=' ')
        # print("data: ", block[block_num_size:block_num_size+10])
        file.write(block[block_num_size:])
    # remove padding based on the original file size
    file.truncate(file_length)
    file.seek(0)
    # write the reassembled file
    output_file = file_name.split('.')[0] + "_reassembled." + file_name.split('.')[1]
    with open(output_file, 'wb') as f:
        f.write(file.read())
    return output_file

def decode_FEC(blocks):
    # Add FEC here
    return blocks

if __name__ == '__main__':
    host = 'localhost'
    receive_sim_port = 12346
    blocks, block_size, file_name, file_length, block_num_size = receive_blocks_from_sim(host, receive_sim_port)
    blocks = decode_FEC(blocks)
    reassembled_file = reassemble_file(blocks, block_size, file_name, file_length, block_num_size)
    print("Reassembled file:", reassembled_file)
    print("Reassembled file size:", os.path.getsize(reassembled_file))
    print("Original file size:", file_length)
    # print("Files are the same:", os.system("diff " + file_name + " " + reassembled_file))
    is_same = os.system("diff " + file_name + " " + reassembled_file)
    if is_same == 0:
        print("Files are the same.")
    else:
        print("Files are different.")