"""Cuts the source footage on the 128 BPM beat grid into one graded 1080x1920 base video."""
import os
import subprocess

SRC = "../footage/agroprodmash"
FPS = 30
BEAT = 60 / 128
END_PAD = 1.25  # extra seconds on the last shot so the music tail can ring out

# (clip, source in-point in seconds, length in beats, speed)
EDL = [
    # Hook: the most spectacular machines, two beats each
    ("0977", 8.0, 2, 1.0),
    ("0984", 15.0, 2, 1.0),
    ("0976", 6.5, 2, 1.0),
    ("0987", 16.5, 2, 1.0),
    ("0994", 25.0, 2, 1.0),
    ("0985", 22.0, 2, 1.0),
    ("0972", 2.0, 4, 1.0),  # exhibition banner -> title
    # Arrival
    ("0971", 4.0, 4, 1.0),  # selfie
    ("0972", 5.0, 2, 1.5),
    ("0981", 0.0, 2, 1.5),
    ("0990", 0.5, 4, 1.5),
    ("0973", 3.0, 2, 1.0),
    ("0974", 3.0, 2, 1.0),
    # 01 Robots (drop)
    ("0987", 1.0, 3, 1.0),
    ("0984", 5.0, 4, 1.0),
    ("0985", 6.0, 3, 1.0),
    ("0983", 22.0, 2, 1.0),
    ("0987", 16.0, 2, 1.0),
    ("0985", 13.5, 2, 1.0),
    ("0984", 33.0, 2, 1.0),
    ("0983", 9.0, 2, 1.0),
    ("0984", 16.0, 2, 1.0),
    ("0985", 26.0, 2, 1.0),
    # 02 Dough & food
    ("0977", 3.0, 3, 1.0),
    ("0977", 9.5, 3, 1.0),
    ("0977", 14.0, 2, 1.0),
    ("0994", 3.0, 2, 1.0),
    ("0994", 12.0, 2, 1.0),
    ("0994", 22.5, 2, 1.0),
    ("0976", 7.0, 3, 1.0),
    ("0976", 16.0, 3, 1.0),
    ("0993", 15.0, 2, 1.0),
    ("0993", 8.0, 2, 1.0),
    # 03 Packaging
    ("0988", 2.0, 2, 1.0),
    ("0988", 9.0, 2, 1.0),
    ("0988", 14.0, 2, 1.0),
    ("0979", 15.5, 2, 1.0),
    ("0979", 5.5, 2, 1.0),
    ("0978", 2.0, 2, 1.0),
    ("0986", 20.0, 2, 1.0),
    ("0982", 15.0, 2, 1.0),
    # Outro
    ("0991", 17.0, 4, 1.0),
    ("0980", 3.0, 2, 1.0),
    ("0981", 4.0, 2, 1.0),
    ("0975", 1.0, 2, 1.0),
    ("0990", 12.5, 4, 1.0),
    ("0971", 26.0, 4, 1.0),
    ("0972", 2.5, 6, 0.6),  # end card background, slowed down
]

GRADE = "eq=contrast=1.08:saturation=1.22:brightness=0.01:gamma=0.98,unsharp=5:5:0.5,vignette=PI/6"

os.makedirs("build/seg", exist_ok=True)
beat = 0
frame = 0
parts = []
for i, (clip, start, beats, speed) in enumerate(EDL):
    beat += beats
    end_frame = round(beat * BEAT * FPS)
    if i == len(EDL) - 1:
        end_frame += round(END_PAD * FPS)
    n = end_frame - frame
    frame = end_frame
    out = f"build/seg/{i:02d}.mp4"
    parts.append(out)
    vf = f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},scale=1080:1920,{GRADE}"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-ss", str(start), "-i", f"{SRC}/IMG_{clip}.mp4",
         "-an", "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "fast", "-crf", "14",
         "-pix_fmt", "yuv420p", out],
        check=True,
    )
    got = int(subprocess.check_output(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out]).strip())
    if got != n:
        raise SystemExit(f"segment {i} ({clip}@{start}) has {got} frames, wanted {n}: source too short")

with open("build/list.txt", "w") as f:
    f.writelines(f"file '{os.path.basename(p)}'\n" for p in parts)
os.replace("build/list.txt", "build/seg/list.txt")
subprocess.run(
    ["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", "build/seg/list.txt",
     "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS),
     "-movflags", "+faststart", "assets/base.mp4"],
    check=True,
)
print("beats", beat, "frames", frame, "seconds", frame / FPS)
