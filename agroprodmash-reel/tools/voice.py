"""Builds the voiceover track from take 1 and a beat-aligned timeline the edit, music and captions follow.

Phrases are chosen by word index from assets/vo/take1_words.json (GigaAM transcript of take 1),
long pauses are squeezed, the speech is sped up slightly, and every section starts on a beat.
Outputs assets/vo.wav and assets/timeline.json / assets/timeline.js.
"""
import json
import math
import subprocess

import numpy as np
import soundfile as sf

SRC = "../озвучка агропродмаш.MOV"
BEAT = 60 / 128
TEMPO = 1.12
SR = 48000
PAUSE_MAX = 0.14  # longest pause kept inside a section, seconds (before tempo)
PHRASE_GAP = 0.16

words = json.load(open("assets/vo/take1_words.json"))
for i, w in enumerate(words):
    # Token timestamps mark word starts; a word ends where the next one starts (capped).
    nxt = words[i + 1]["s"] if i + 1 < len(words) else w["s"] + 0.8
    w["e"] = min(nxt, w["s"] + 0.15 + 0.075 * len(w["w"]))

# section name, [(first word, last word), ...], beats of music after the voice ends
SECTIONS = [
    ("hook", [(0, 16)], 3),  # "это не отдельный завод ... агропродмаш"
    ("arrival", [(21, 40), (41, 49)], 0),  # "я поехал ... огромное помещение" + "куда же пойти ... к роботам"
    ("robots", [(50, 62), (63, 73), (74, 81)], 0),
    ("food", [(82, 83), (85, 104)], 0),
    ("pack", [(105, 105), (109, 125)], 0),
    ("people", [(126, 131), (132, 142)], 1),
    ("cta", [(144, 154)], 3),
]

raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", SRC, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(raw, dtype=np.float32).copy()

# 10 ms RMS envelope to find pauses.
hop = SR // 100
rms = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, mode="same"))[::hop]
floor = np.percentile(rms, 20)
speech = rms > max(floor * 3, 10 ** (-42 / 20))


def keep_intervals(a, b):
    """Spans of [a, b] with internal pauses squeezed to PAUSE_MAX."""
    out, i0 = [], int(a * 100)
    i, n = i0, int(b * 100)
    start = a
    while i < n:
        if not speech[i]:
            j = i
            while j < n and not speech[j]:
                j += 1
            if (j - i) / 100 > PAUSE_MAX and i > i0 and j < n:
                cut_a = i / 100 + PAUSE_MAX / 2
                cut_b = j / 100 - PAUSE_MAX / 2
                out.append((start, cut_a))
                start = cut_b
            i = j
        else:
            i += 1
    out.append((start, b))
    return out


def render(intervals):
    fade = int(0.008 * SR)
    parts = []
    for a, b in intervals:
        seg = audio[int(a * SR):int(b * SR)].copy()
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        parts.append(seg)
    return np.concatenate(parts)


def tempo(x):
    p = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
         "-af", f"atempo={TEMPO}", "-f", "f32le", "-"], input=x.astype(np.float32).tobytes(),
        capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32)


timeline = {"beat": BEAT, "sections": [], "words": []}
pieces = []  # (output start seconds, samples)
beat = 0
for name, phrases, tail in SECTIONS:
    t0 = beat * BEAT + (0.05 if beat else 0.0)
    clean, wmap, t_clean = [], [], 0.0
    for k, (w0, w1) in enumerate(phrases):
        a, b = words[w0]["s"] - 0.06, words[w1]["e"] + 0.06
        ivs = keep_intervals(a, b)
        for i in range(w0, w1 + 1):
            # map the word start through the squeezed intervals
            s, acc = words[i]["s"], 0.0
            for x, y in ivs:
                if s < y:
                    wmap.append((i, t_clean + acc + max(0.0, s - x)))
                    break
                acc += y - x
        seg = render(ivs)
        clean.append(seg)
        t_clean += len(seg) / SR
        if k < len(phrases) - 1:
            clean.append(np.zeros(int(PHRASE_GAP * SR), dtype=np.float32))
            t_clean += PHRASE_GAP
    sped = tempo(np.concatenate(clean))
    pieces.append((t0, sped))
    for i, t in wmap:
        timeline["words"].append({"w": words[i]["w"], "t": round(t0 + t / TEMPO, 3), "section": name})
    vo_end = t0 + len(sped) / SR
    end_beat = math.ceil(vo_end / BEAT - 0.25) + tail
    timeline["sections"].append({"name": name, "start": beat, "end": end_beat})
    beat = end_beat

timeline["beats"] = beat
timeline["duration"] = round(beat * BEAT, 3)
n = int(timeline["duration"] * SR) + SR
mix = np.zeros(n, dtype=np.float32)
for t0, x in pieces:
    i = int(t0 * SR)
    mix[i:i + len(x)] += x[: n - i]
sf.write("build/vo_raw.wav", mix, SR, subtype="FLOAT")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/vo_raw.wav", "-af",
                "highpass=f=80,afftdn=nf=-28,equalizer=f=3500:t=q:w=1.2:g=3,"
                "acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2,loudnorm=I=-15:TP=-1.5:LRA=7",
                "-ar", "48000", "-t", str(timeline["duration"]), "assets/vo.wav"], check=True)
json.dump(timeline, open("assets/timeline.json", "w"), ensure_ascii=False, indent=1)
with open("assets/timeline.js", "w") as f:
    f.write("window.TIMELINE = " + json.dumps(timeline, ensure_ascii=False) + ";\n")
for s in timeline["sections"]:
    print(s["name"], s["start"], s["end"], f"{s['start'] * BEAT:.2f}s")
print("total", timeline["beats"], "beats", timeline["duration"], "s")
