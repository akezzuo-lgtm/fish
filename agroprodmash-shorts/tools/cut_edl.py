"""Cuts shots from ../footage/agroprodmash into one graded 1080x1920 video.

Usage: python3 tools/cut_edl.py <project_dir>
Reads <project_dir>/edl.json: [{"clip": "0977", "in": 9.0, "dur": 3.0, "speed": 1.0}, ...]
Writes <project_dir>/assets/base.mp4 and <project_dir>/assets/shots.js (shot start/len in seconds).
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "..", "footage", "agroprodmash")
FPS = 30
# iPhone footage is tagged HLG; the grade is tuned on it viewed as SDR, so retag as BT.709.
SDR = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"
GRADE = "eq=contrast=1.08:saturation=1.22:brightness=0.01:gamma=0.98,unsharp=5:5:0.5,vignette=PI/6"

proj = sys.argv[1]
edl = json.load(open(os.path.join(proj, "edl.json")))
seg_dir = os.path.join(proj, "build", "seg")
os.makedirs(seg_dir, exist_ok=True)
os.makedirs(os.path.join(proj, "assets"), exist_ok=True)
t, frame, parts, shots = 0.0, 0, [], []
for i, s in enumerate(edl):
    t += s["dur"]
    end = round(t * FPS)
    n = end - frame
    shots.append({"start": frame / FPS, "len": n / FPS})
    frame = end
    out = os.path.join(seg_dir, f"{i:02d}.mp4")
    parts.append(out)
    vf = f"setpts=(PTS-STARTPTS)/{s.get('speed', 1.0)},fps={FPS},scale=1080:1920,{GRADE},{SDR}"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(s["in"]), "-i", f"{SRC}/IMG_{s['clip']}.mp4",
                    "-an", "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                    "-pix_fmt", "yuv420p", out], check=True)
    got = int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                       "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out]).strip())
    if got != n:
        raise SystemExit(f"shot {i} ({s['clip']}@{s['in']}) has {got} frames, wanted {n}: source too short")
with open(os.path.join(seg_dir, "list.txt"), "w") as f:
    f.writelines(f"file '{os.path.basename(p)}'\n" for p in parts)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(seg_dir, "list.txt"),
                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
                "-r", str(FPS), "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-movflags", "+faststart", os.path.join(proj, "assets", "base.mp4")], check=True)
with open(os.path.join(proj, "assets", "shots.js"), "w") as f:
    f.write("window.SHOTS = " + json.dumps(shots) + ";\nwindow.DURATION = " + str(frame / FPS) + ";\n")
print(len(shots), "shots,", frame / FPS, "s")
