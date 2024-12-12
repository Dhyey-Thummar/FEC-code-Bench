# FEC-code-Bench
The repository includes a complete pipeline built with python to simulate packet loss, implement error correction, and assess recovery performance.

It also contains benchmarking scripts that allow for benchmarking LT-codes, Raptor Codes, and Implement the HSC-Encoding Algorithm (with bencmarking scripts on videos)

The project report is also included as `CS7260_Final_Report.pdf`.

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

# HSC-Encoding Algorithm
The 'videos' directory contains videos. If we need to run the HSC-Encoding script, upload the video into the 'videos' directory and run the sim_video.py.
Note: The main() function might need to be modified.

## Acknowledgements
- This project incorporates code from the [LT-code](https://github.com/anrosent/LT-code), licensed under the [MIT License](https://opensource.org/licenses/MIT). The code is included in the folder `LTcode`.