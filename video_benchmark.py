import os 
import numpy as np
import time
import math
import csv
from LTcode.lt import encode, decode, sampler
from fec_encode import encode_FEC, decode_FEC, sim_channel 
from sim_video import preprocess_video, run_simulation


def run_tests(input_video_file, output_video_file, fps_list, threshold_list, channels, csv_file):
    # Each for loop is a parameter choice (independent variables)
    for i_video in input_video_file:
        for fps in fps_list:
            for threshold in threshold_list:
                for channel in channels:
                    start_time = 0
                    end_time = 0
                    all_encode_time = 0
                    hsc_encode_time = 0
                    none_encode_time = 0
                    print("################################################################################")
                    # Reading for all frames encoded
                    print(f"Input Video: {i_video}  FPS: {fps}  Threshold: {threshold}  Channel: {channel} ALL_ENCODED")
                    preprocess_video(i_video, fps, threshold, output_dir=f"outputs/output_{i_video}_{fps}_{threshold}_{channel}")
                    start_time = time.time()
                    run_simulation(0, channel, 0.5, 1, fps, output_dir=f"outputs/output_{i_video}_{fps}_{threshold}_{channel}", output_file="output_0.mp4")
                    end_time = time.time()
                    all_encode_time = round(end_time - start_time, 7)

                    # Reading for only HSC frames encoded
                    print(f"Input Video: {i_video}  FPS: {fps}  Threshold: {threshold}  Channel: {channel} HSC_ENCODED")
                    preprocess_video(i_video, fps, threshold, output_dir=f"outputs/output_{i_video}_{fps}_{threshold}_{channel}")
                    start_time = time.time()
                    run_simulation(1, channel, 0.5, 1, fps, output_dir=f"outputs/output_{i_video}_{fps}_{threshold}_{channel}", output_file="output_1.mp4")
                    end_time = time.time()
                    hsc_encode_time = round(end_time - start_time, 7)

                    # Reading for no frames encoded
                    print(f"Input Video: {i_video}  FPS: {fps}  Threshold: {threshold}  Channel: {channel} NONE_ENCODED")
                    preprocess_video(i_video, fps, threshold, output_dir=f"outputs/output_{i_video}_{fps}_{threshold}_{channel}")
                    start_time = time.time()
                    run_simulation(2, channel, 0.5, 1, fps, output_dir=f"outputs/output_{i_video}_{fps}_{threshold}_{channel}", output_file="output_2.mp4")   
                    end_time = time.time()            
                    none_encode_time = round(end_time - start_time, 7)  

                    # Write timings to CSV file
                    with open(csv_file, "a+") as csv_f:
                        writer = csv.writer(csv_f)
                        writer.writerow([i_video, fps, threshold, channel, all_encode_time, hsc_encode_time, none_encode_time])
    return



def main():
    input_video_file = []
    fps_list = []
    threshold_list = []
    channels = []
    csv_file = "results/video_benchmark_results.csv"
    
    output_video_file = []

    # Fill in parameters like fps, threshold, channel...
    for file in os.listdir("videos"):
        input_video_file.append(f"videos/{file}")
    
    for fps in range(15, 55, 10):
        fps_list.append(fps)
    
    for threshold in range(2, 12, 2):
        threshold_list.append(float(threshold / 1000))

    for channel in range(0, 5):
        if channel == 1:
            continue
        channels.append(channel)

    print("All videos:", input_video_file)
    print("All FPS:", fps_list)
    print("All thresholds:", threshold_list)
    print("All channels:", channels)

    # Run the tests
    run_tests(input_video_file, output_video_file, fps_list, threshold_list, channels, csv_file)

    return 

if __name__ == "__main__":
    main()