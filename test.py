from utils import *
from raptor import *
from constants import *
from luby import *

filename = "test5.io"
outname = "regen_" + filename

f = open(filename, "rb")
message = f.read()
FILE_SIZE = len(message)
BLOCK_SIZE = 8192
NUM_BLOCKS = (FILE_SIZE + BLOCK_SIZE - 1) // BLOCK_SIZE
OVERHEAD = 10

print("Working with: " + filename)
print(f"File size: {FILE_SIZE} bytes")
print(f"Num blocks: {NUM_BLOCKS}")
print(f"Block size: {BLOCK_SIZE} bytes")

c = RaptorCodec(NUM_BLOCKS, BLOCK_SIZE)
# message = b"abcdefghijklmnopqrstuvwxyz"

ids = [random.randint(0, 60000) for _ in range(1000)]
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