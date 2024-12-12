# FEC-code-Bench
The repository includes a complete pipeline built with python to simulate packet loss, implement error correction, and assess recovery performance.
It also contains benchmarking scripts that allow for benchmarking LT-codes, Raptor Codes, and Implement the HSC-Encoding Algorithm (with bencmarking scripts on videos)


# Step 1: Start the input script
```sh
python3 input.py <input filename> <blocksize> <max_blocks>
```

E.g. ```python3 input.py test.mp4 2560 10000```

# Step 2: Run the simulation script
```sh
python3 sim.py <channel> <probability> <std>
```

# Step 3: Start the output script
```sh
python3 output.py <input filename>
```
