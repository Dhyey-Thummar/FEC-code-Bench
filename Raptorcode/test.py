from utils import *
from raptor import *
from constants import *
from luby import *

filename = "test9.pdf"
outname = "regen_" + filename

f = open(filename, "rb")
message = f.read()
FILE_SIZE = len(message)
BLOCK_SIZE = 4096
NUM_BLOCKS = (FILE_SIZE + BLOCK_SIZE - 1) // BLOCK_SIZE
# NUM_BLOCKS = 57
# BLOCK_SIZE = FILE_SIZE // NUM_BLOCKS
OVERHEAD = 100

print("Working with: " + filename)
print(f"File size: {FILE_SIZE} bytes")
print(f"Num blocks: {NUM_BLOCKS}")
print(f"Block size: {BLOCK_SIZE} bytes")

c = RaptorCodec(NUM_BLOCKS, BLOCK_SIZE)
# message = b"abcdefghijklmnopqrstuvwxyz"

ids = [random.randint(0, 60000) for _ in range(NUM_BLOCKS+OVERHEAD)]
message_copy = message[:]
code_blocks = encode_lt_blocks(message_copy, ids, c)
decoder = RaptorDecoder(c, len(message))
decoder.add_blocks(code_blocks[:])
if decoder.matrix.determined():
    out = decoder.decode()
    c = open(outname, "wb")
    c.write(out)
    # print(out)
    assert message == out
    print("ok")
else:
    print("need more data")