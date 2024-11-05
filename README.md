# FEC-code-Bench
The repository includes a complete pipeline built with python to simulate packet loss, implement error correction, and assess recovery performance.


# Step 1: Start the input script
```sh
python3 input.py <examplefile> <block_size>
```

E.g. ```python3 input.py pipeline.png 1024```

# Step 2: Run the simulation script
```sh
python3 sim.py
```

# Step 3: Start the output script
```sh
python3 output.py
```