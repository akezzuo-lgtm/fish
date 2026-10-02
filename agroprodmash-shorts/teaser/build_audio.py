"""Builds the teaser soundtrack: two voiceover lines from take 1 plus trailer-style sound design.

Writes assets/mix.wav and assets/vo_words.js (word times on the output timeline for subtitles).
"""
import json
import subprocess

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
DUR = 12.7
TEMPO = 1.08
SRC = "../../озвучка агропродмаш.MOV"
WORDS = json.load(open("../../agroprodmash-reel/assets/vo/take1_words.json"))
# (first word, last word, source start, source end, output start)
LINES = [(0, 6, 0.30, 2.13, 0.05), (74, 81, 35.55, 38.95, 4.40)]
rng = np.random.default_rng(11)


def load_vo(a, b):
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(a), "-t", str(b - a), "-i", SRC, "-vn", "-ac", "1",
                        "-ar", str(SR), "-af", f"highpass=f=90,afftdn=nf=-28,equalizer=f=3500:t=q:w=1.2:g=3,"
                        f"acompressor=threshold=-22dB:ratio=3:attack=5:release=90,atempo={TEMPO}",
                        "-f", "f32le", "-"], capture_output=True, check=True)
    x = np.frombuffer(p.stdout, dtype=np.float32).copy()
    f = int(0.01 * SR)
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    return x


def filt(x, kind, f):
    return sosfilt(butter(2, f, kind, fs=SR, output="sos"), x)


def env(n, a, d):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


N = int(DUR * SR)
vo = np.zeros(N)
sfx = np.zeros(N)
words_out = []
for w0, w1, a, b, at in LINES:
    x = load_vo(a, b)
    i = int(at * SR)
    vo[i:i + len(x)] += x[: N - i]
    for k in range(w0, w1 + 1):
        words_out.append({"w": WORDS[k]["w"], "t": round(at + (WORDS[k]["s"] - a) / TEMPO, 3)})


def put(sig, t, g):
    i = int(t * SR)
    j = min(N, i + len(sig))
    if i < N:
        sfx[i:j] += sig[: j - i] * g


def impact(big=True):
    n = int((2.2 if big else 0.6) * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + (90 if big else 140) * np.exp(-t / 0.07)) / SR) * env(n, 0.001, 0.8 if big else 0.18)
    crack = filt(rng.standard_normal(n), "high", 1200) * env(n, 0.0005, 0.05 if big else 0.025)
    return np.tanh(1.6 * boom + 0.5 * crack)


def braam(t0, length):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = sum(2 * ((tt * f) % 1) - 1 for f in (55, 55.4, 82.4, 110.2))
    x = filt(x, "low", 900) * env(n, 0.02, 1.6)
    put(np.tanh(1.8 * x), t0, 0.5)


def riser(t0, length):
    n = int(length * SR)
    k = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    for i in range(0, n, 1024):
        f = 250 + 8000 * k[i] ** 2
        out[i:i + 1024] = sosfilt(butter(2, [f, f * 1.5], "band", fs=SR, output="sos"), x[i:i + 1024])
    tone = np.sin(2 * np.pi * np.cumsum(110 + 330 * k ** 2) / SR) * 0.3
    put((out + tone) * k ** 1.6, t0, 0.8)


def tick(t0):
    n = int(0.06 * SR)
    put(filt(rng.standard_normal(n), "high", 3000) * env(n, 0.0005, 0.008), t0, 0.6)


def whoosh(t0, length=0.5):
    n = int(length * SR)
    k = np.linspace(0, 1, n)
    put(filt(rng.standard_normal(n), "low", 2500) * np.sin(np.pi * k) ** 2, t0, 0.5)


def bell(t0):
    n = int(1.2 * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * tt) * g for f, g in ((1318.5, 1), (1975.5, 0.5), (2637, 0.25)))
    put(x * env(n, 0.002, 0.35) * 0.25, t0, 1)


# Low drone under everything except the final card.
tt = np.arange(N) / SR
drone = filt(np.sin(2 * np.pi * 55 * tt) + 0.4 * rng.standard_normal(N), "low", 180)
drone *= np.clip(tt / 1.5, 0, 1) * np.clip((9.7 - tt) / 0.4, 0, 1)
sfx += drone * 0.25

cuts = [0.867, 1.7, 2.3, 2.833, 3.4, 3.933, 4.5, 5.6, 6.7, 7.7, 9.7]
put(impact(False), 0.0, 0.6)
put(impact(True), 1.7, 0.9)
for c in cuts[2:6]:
    put(impact(False), c, 0.55)
for k in range(int((4.5 - 1.7) / 0.1333)):
    tick(1.7 + k * 0.1333)
put(impact(True), 4.5, 0.7)
whoosh(5.0, 0.4)
riser(6.95, 0.75)
put(impact(True), 7.7, 1.0)
braam(7.7, 2.2)
whoosh(9.45)
put(impact(False), 9.7, 0.5)
bell(10.6)

# Duck sound design under the voice.
venv = np.convolve(np.abs(vo), np.ones(2400) / 2400, mode="same")
duck = 1 - 0.55 * np.clip(venv / (venv.max() * 0.3 + 1e-9), 0, 1)
mix = sfx * duck + vo * 1.6
fade = int(0.8 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
mix = np.tanh(mix * 1.2)
mix /= np.max(np.abs(mix)) * 1.05
stereo = np.stack([mix, mix], 1).astype(np.float32)
p = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "loudnorm=I=-14:TP=-1:LRA=9", "-ar", "48000", "assets/mix.wav"], input=stereo.tobytes(), check=True)
with open("assets/vo_words.js", "w") as f:
    f.write("window.VO_WORDS = " + json.dumps(words_out, ensure_ascii=False) + ";\n")
print(" ".join(f"{w['w']}@{w['t']}" for w in words_out))
