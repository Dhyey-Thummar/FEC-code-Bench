import os
import numpy as np
import time
from LTcode.lt import encode, decode, sampler
from fec_encode import encode_FEC, decode_FEC, sim_channel  # Import your LT code functions

def preprocess_video(input_video, fps, threshold, output_dir="video-application"):
    """Extract and categorize frames from a video."""
    # Clean directories
    os.system(f"rm -rf {output_dir}/*") if os.path.exists(f"{output_dir}") else None

    os.makedirs(f"{output_dir}/all_frames", exist_ok=True)
    os.makedirs(f"{output_dir}/lsc_frames", exist_ok=True)
    os.makedirs(f"{output_dir}/hsc_frames", exist_ok=True)
    os.makedirs(f"{output_dir}/final_frames", exist_ok=True)
    os.makedirs(f"{output_dir}/temp_frames", exist_ok=True)

    os.remove(f"{output_dir}/output.mp4") if os.path.exists(f"{output_dir}/output.mp4") else None

    # Extract frames from video
    os.system(f"ffmpeg -hide_banner -loglevel error -i {input_video} -vf 'fps={fps}' {output_dir}/all_frames/frame_%04d.jpg")

    # Extract low-scene change frames
    os.system(f"ffmpeg -i {output_dir}/all_frames/frame_%04d.jpg -vf \"select='lt(scene,{threshold})',showinfo\" -vsync vfr {output_dir}/temp_frames/frame_%04d.jpg > {output_dir}/output.txt 2>&1")
    os.system(f"grep -E -o 'pts: +[0-9]+' {output_dir}/output.txt > {output_dir}/temp.txt 2>&1")

    frames_all = set(range(1, len(os.listdir(f"{output_dir}/all_frames")) + 1))
    frames_lsc = set()
    with open(f"{output_dir}/temp.txt", "r") as f:
        for line in f:
            frames_lsc.add(int(line.split()[-1]))
    frames_lsc.remove(0)
    frames_hsc = frames_all - frames_lsc
    frames_all = list(frames_all)
    frames_lsc = list(frames_lsc)
    frames_hsc = list(frames_hsc)
    print(f'---------------------------------------------------')
    print(f"Total frames: {len(frames_all)}")
    print(f"Low scene change frames: {len(frames_lsc)}")
    print(f"High scene change frames: {len(frames_hsc)}")

    # Copy frames to respective directories
    for frame in frames_lsc:
        os.system(f"cp {output_dir}/all_frames/frame_{frame:04d}.jpg {output_dir}/lsc_frames/frame_{frame:04d}.jpg")
    for frame in frames_hsc:
        os.system(f"cp {output_dir}/all_frames/frame_{frame:04d}.jpg {output_dir}/hsc_frames/frame_{frame:04d}.jpg")
    
    print(f'---------------------------------------------------')
    print(f'Length of LSC frames: {len(os.listdir(f"{output_dir}/lsc_frames"))}')
    print(f'Length of HSC frames: {len(os.listdir(f"{output_dir}/hsc_frames"))}')
    

def run_simulation(case, channel_type, probability, std, fps, output_dir="output", output_file="output.mp4"):
    """Run LT encoding/decoding and simulate channel effects."""
    max_blocks = 10000
    blocksize = 512

    # Clean final and temp directories
    os.system(f"rm {output_dir}/temp_frames/*.jpg")
    # os.system(f"rm {output_dir}/final_frames/*.jpg")

    match case:
        case 0: # No frame drop, encode all frames
            input_files = os.listdir(f"{output_dir}/all_frames")
            for input_file in input_files:
                blocks = encode_FEC(f"{output_dir}/all_frames/{input_file}", blocksize, max_blocks)
                blocks = sim_channel(blocks, channel_type, probability, std)
                decode_FEC(blocks, f"{output_dir}/temp_frames/{input_file}")
        case 1: # Only encode high scene change frames
            input_files = os.listdir(f"{output_dir}/hsc_frames")
            for input_file in input_files:
                blocks = encode_FEC(f"{output_dir}/hsc_frames/{input_file}", blocksize, max_blocks)
                blocks = sim_channel(blocks, channel_type, probability, std)
                decode_FEC(blocks, f"{output_dir}/temp_frames/{input_file}")

            # Randomly drop low scene change frames
            all_lsc_frames = os.listdir(f"{output_dir}/lsc_frames")
            new_lsc_frames = sim_channel(all_lsc_frames, channel_type, probability, std)
            print(f'---------------------------------------------------')
            print(f'prev LSC frames: {len(all_lsc_frames)}, new LSC frames: {len(new_lsc_frames)}')
            print(f'Dropped LSC frames: {len(all_lsc_frames) - len(new_lsc_frames)}')
            

            # Copy new LSC frames to final directory
            os.makedirs(f"{output_dir}/temp_frames", exist_ok=True)
            for frame in new_lsc_frames:
                os.system(f"cp {output_dir}/lsc_frames/{frame} {output_dir}/temp_frames")
        
        case 2: # encode nothing, can drop all frames
            all_frames = os.listdir(f"{output_dir}/all_frames")
            final_frames = sim_channel(all_frames, channel_type, probability, std)
            print(f'---------------------------------------------------')
            print(f'prev frames: {len(all_frames)}, new frames: {len(final_frames)}')
            print(f'Dropped frames: {len(all_frames) - len(final_frames)}')

            # Copy new frames to final directory
            os.makedirs(f"{output_dir}/temp_frames", exist_ok=True)
            for frame in final_frames:
                os.system(f"cp {output_dir}/all_frames/{frame} {output_dir}/temp_frames")
            
        case _:
            raise ValueError("Invalid case")
    print(f'---------------------------------------------------')
    print(f'Total frames: {len(os.listdir(f"{output_dir}/all_frames"))}')
    print(f'Before Dropping: ')
    print(f'    High Scene Change frames: {len(os.listdir(f"{output_dir}/hsc_frames"))}')
    print(f'    Low Scene Change frames: {len(os.listdir(f"{output_dir}/lsc_frames"))}')
    print(f'After Dropping: ')
    print(f'    Final frames: {len(os.listdir(f"{output_dir}/temp_frames"))}')
    print(f'---------------------------------------------------')

    # Rename to sequential numbering
    final_frames = sorted(os.listdir(f"{output_dir}/temp_frames"))
    for i, frame in enumerate(final_frames):
        os.system(f"mv {output_dir}/temp_frames/{frame} {output_dir}/final_frames/frame_{i:04d}.jpg")
    os.system(f"ffmpeg -hide_banner -loglevel error -r {fps} -i {output_dir}/final_frames/frame_%04d.jpg -vf 'fps={fps}' {output_dir}/{output_file}")


if __name__ == "__main__":
    input_video = "videos/input_video_3.mp4"
    output_dir = "video-application"
    fps = 15
    threshold = 0.002
    preprocess_video(input_video, fps, threshold, output_dir)

    start = time.time()
    case = 0
    channel_type = 0
    probability = 0
    std = 0
    run_simulation(case, channel_type, probability, std, fps, output_dir)
    end = time.time()
    print("Time for simulation:", round(end - start, 3))
