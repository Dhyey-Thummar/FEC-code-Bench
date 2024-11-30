import os

from numpy import sort, delete

# Clean directories
os.system("rm extract_frames/*.jpg")
os.system("rm new_extract_frames/*.jpg")

# Extract frames from video
os.system(f"ffmpeg -i input_2.mp4 -vf 'fps=29' extract_frames/frame_%04d.jpg")
# Extract low-scene changing frames
os.system(f"ffmpeg -i other_final_extract_frames/frame_%04d.jpg -vf \"select='lt(scene,0.002)',showinfo\" -vsync vfr new_extract_frames/low_scene_changes_%03d.jpg > output.txt 2>&1")
# Map low-scene changing frames to the extracted frames (all)
os.system("grep -E -o 'pts: +[0-9]+' output.txt > temp.txt 2>&1")

with open("temp.txt", 'r') as f:
    lines = f.readlines()
    print(lines[0][5])

# CHANGE ACCORDING TO LOCAL STRUCTURE...
files = []
files = sort(os.listdir('./extract_frames')).tolist()

new_files = dict()

i = 1
for file in files:
    if int(file[6:10]) % 4 == 0:
        os.remove(f'extract_frames/{file}')
    
files = sort(os.listdir('./extract_frames')).tolist()

for file in files:
    new_files[file] = f"frame_{i:04}.jpg"
    i = i + 1

os.makedirs("./other_final_extract_frames", exist_ok=True)
for k in new_files:
    os.rename(f"./extract_frames/{k}", f"./other_final_extract_frames/{new_files[k]}")

os.system("rm other_other_final_extract_frames/*.jpg")

files = sort(os.listdir('./extract_frames')).tolist()
i = 1
os.makedirs("./other_final_extract_frames", exist_ok=True)
for file in files:
    os.rename(f"./extract_frames/{file}", f"./other_final_extract_frames/frame_{i:04}.jpg")
    i = i + 1