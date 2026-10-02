"""Cuts the source footage on the 128 BPM beat grid into one graded 1080x1920 base video."""
import json
import os
import subprocess

SRC = "../footage/agroprodmash"
FPS = 30
TL = json.load(open("assets/timeline.json"))
BEAT = TL["beat"]

# Shots per section: (clip, source in-point s, min beats, speed, anchor word or None).
# An anchored shot starts on the beat where that word is spoken (first match inside the section).
SHOTS = {
    "hook": [
        ("0977", 8.0, 2, 1.0, None), ("0984", 15.0, 2, 1.0, None), ("0976", 6.5, 2, 1.0, None),
        ("0987", 16.5, 2, 1.0, None), ("0994", 25.0, 2, 1.0, None), ("0985", 22.0, 2, 1.0, None),
        ("0972", 2.0, 2, 1.0, "агропродмаш"),
    ],
    "arrival": [
        ("0971", 4.0, 6, 1.0, None), ("0972", 5.0, 2, 1.5, None), ("0981", 0.0, 2, 1.5, "заходим"),
        ("0990", 0.5, 2, 1.5, "огромное"), ("0974", 3.0, 2, 1.0, "куда"), ("0990", 7.0, 2, 1.0, None),
        ("0983", 27.0, 2, 1.0, None),
    ],
    "robots": [
        ("0984", 5.0, 3, 1.0, None), ("0985", 6.0, 3, 1.0, "бригада"), ("0985", 22.0, 2, 1.0, None),
        ("0987", 16.0, 2, 1.0, "конфеты"), ("0985", 13.5, 4, 1.0, "человеку"), ("0984", 33.0, 2, 1.0, None),
        ("0983", 22.0, 2, 1.0, "сбился"), ("0987", 1.0, 2, 1.0, None),
    ],
    "food": [
        ("0977", 3.0, 2, 1.0, None), ("0977", 9.5, 2, 1.0, "шоколад"), ("0977", 14.0, 2, 1.0, "кондитерка"),
        ("0994", 3.0, 2, 1.0, "полуфабрикаты"), ("0994", 22.5, 2, 1.0, None), ("0976", 7.0, 2, 1.0, "овощи"),
        ("0976", 16.0, 2, 1.0, None), ("0993", 15.0, 2, 1.0, "мясорубки"), ("0993", 8.0, 2, 1.0, "холодильник"),
    ],
    "pack": [
        ("0979", 15.5, 2, 1.0, None), ("0988", 2.0, 2, 1.0, "рулон"), ("0988", 9.0, 2, 1.0, "готовая"),
        ("0979", 5.5, 2, 1.0, None), ("0988", 14.0, 2, 1.0, None), ("0986", 20.0, 2, 1.0, "столиками"),
    ],
    "people": [
        ("0991", 17.0, 4, 1.0, None), ("0990", 12.5, 3, 1.0, "итог"), ("0987", 20.0, 2, 1.0, "роботы"),
        ("0971", 26.0, 2, 1.0, "начало"),
    ],
    "cta": [("0972", 2.5, 2, 0.6, None)],
}


def plan():
    """Turns the section shot lists into a flat list of (clip, in, beats, speed)."""
    edl = []
    for sec in TL["sections"]:
        words = [w for w in TL["words"] if w["section"] == sec["name"]]
        starts, shots = [], []
        for clip, t_in, minb, speed, anchor in SHOTS[sec["name"]]:
            if anchor:
                t = next(w["t"] for w in words if w["w"] == anchor)
                b = max(round(t / BEAT), starts[-1] + 1 if starts else sec["start"])
            else:
                b = starts[-1] + shots[-1][2] if starts else sec["start"]
            if b >= sec["end"]:
                continue
            # drop unanchored shots that would collide with an anchored one
            starts.append(b)
            shots.append((clip, t_in, minb, speed))
        for i, (clip, t_in, _, speed) in enumerate(shots):
            nxt = starts[i + 1] if i + 1 < len(starts) else sec["end"]
            if nxt > starts[i]:
                edl.append((clip, t_in, nxt - starts[i], speed))
    return edl


EDL = plan()

# iPhone footage is tagged HLG/BT.2020; the grade was tuned on it viewed as SDR, so retag as BT.709
# (otherwise HyperFrames switches to an HDR render path).
SDR = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"
GRADE = "eq=contrast=1.08:saturation=1.22:brightness=0.01:gamma=0.98,unsharp=5:5:0.5,vignette=PI/6"

os.makedirs("build/seg", exist_ok=True)
beat = 0
frame = 0
parts = []
for i, (clip, start, beats, speed) in enumerate(EDL):
    beat += beats
    end_frame = round(beat * BEAT * FPS)
    n = end_frame - frame
    frame = end_frame
    out = f"build/seg/{i:02d}.mp4"
    parts.append(out)
    vf = f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},scale=1080:1920,{GRADE},{SDR}"
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
     "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
     "-movflags", "+faststart", "assets/base.mp4"],
    check=True,
)
with open("assets/shots.js", "w") as f:
    f.write("window.SHOT_BEATS = " + json.dumps([e[2] for e in EDL]) + ";\n")
print("shots", len(EDL), "beats", beat, "frames", frame, "seconds", frame / FPS)
