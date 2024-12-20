#!/usr/bin/env python3
import argparse
import fileinput
import sys
import time
from struct import unpack, error
from random import random
from ctypes import c_int
from collections import defaultdict
from math import ceil

from lt import decode
 
def run(stream=sys.stdin.buffer):
    """Reads from stream, applying the LT decoding algorithm
    to incoming encoded blocks until sufficiently many blocks
    have been received to reconstruct the entire file.
    """
    payload = decode.decode(stream)
    # sys.stdout.buffer.write(payload)

if __name__ == '__main__':
    parser = argparse.ArgumentParser("decoder")
    try:
        run(sys.stdin.buffer)
    except error:
        print("Decoder got some invalid data. Try again.", file=sys.stderr)
