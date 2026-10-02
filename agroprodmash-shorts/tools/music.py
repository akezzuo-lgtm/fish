"""Synthesizes a background track. Usage: python3 tools/music.py <out.wav> <seconds> <style: chill|drive>

chill: 90 BPM lo-fi pad, soft kick and shaker; loops cleanly (no intro/outro fades) for loopable videos.
drive: 120 BPM energetic groove with an intro hit and a fade-out ending.
"""
import subprocess
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

out, seconds, style = sys.argv[1], float(sys.argv[2]), sys.argv[3]
SR = 48000
BPM = 90 if style == "chill" else 120
BEAT = 60 / BPM
N = int(seconds * SR)
rng = np.random.default_rng(3)
L = np.zeros(N + SR * 4)
R = np.zeros(N + SR * 4)


def env(n, a, d):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def filt(x, kind, f):
    return sosfilt(butter(2, f, kind, fs=SR, output="sos"), x)


def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(L):
        return
    j = min(len(L), i + len(sig))
    L[i:j] += sig[: j - i] * g * (1 - max(pan, 0))
    R[i:j] += sig[: j - i] * g * (1 + min(pan, 0))


def mtof(m):
    return 440 * 2 ** ((m - 69) / 12)


def tone(freq, n, kind="saw", det=(0.0,)):
    t = np.arange(n) / SR
    o = np.zeros(n)
    for d in det:
        ph = t * freq * (1 + d)
        o += (2 * (ph % 1) - 1) if kind == "saw" else np.sin(2 * np.pi * ph)
    return o / len(det)


def kick(soft):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    f = 48 + (70 if soft else 120) * np.exp(-t / 0.035)
    return np.tanh((1.2 if soft else 2.2) * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.13))


def noise_hit(n_s, lo, hi, d):
    n = int(n_s * SR)
    return filt(filt(rng.standard_normal(n), "high", lo), "low", hi) * env(n, 0.001, d)


# Am9 - Fmaj7 - Cmaj7 - G6 voicings
CHORDS = [[57, 60, 64, 67, 71], [53, 57, 60, 64], [48, 55, 59, 64], [55, 59, 62, 64]]
bars = int(np.ceil(seconds / (4 * BEAT))) + 1
for bar in range(bars):
    t0 = bar * 4 * BEAT
    ch = CHORDS[bar % 4]
    n = int(4 * BEAT * SR)
    if style == "chill":
        pad = sum(tone(mtof(m), n, "saw", (-0.004, 0.004)) for m in ch)
        add(filt(pad, "low", 1100) * env(n, 0.25, 8.0) * 0.07, t0)
        add(np.sin(2 * np.pi * mtof(ch[0] - 24) * np.arange(n) / SR) * env(n, 0.02, 3.0) * 0.25, t0)
        for b in range(4):
            tb = t0 + b * BEAT
            if b in (0, 2):
                add(kick(True), tb, 0.55)
            if b in (1, 3):
                add(noise_hit(0.2, 1500, 6000, 0.06), tb, 0.25)
            for k in (0.5,):
                add(noise_hit(0.05, 6000, 12000, 0.02), tb + k * BEAT, 0.18, 0.3)
        # gentle pluck arpeggio
        for k, m in enumerate(ch * 2):
            tn = int(0.4 * SR)
            add(filt(tone(mtof(m + 12), tn, "saw"), "low", 2500) * env(tn, 0.002, 0.18) * 0.05, t0 + k * BEAT / 2, 1, 0.2 if k % 2 else -0.2)
    else:
        pad = sum(tone(mtof(m), n, "saw", (-0.006, 0.006)) for m in ch[:3])
        add(filt(pad, "low", 1800) * env(n, 0.05, 6.0) * 0.07, t0)
        for b in range(4):
            tb = t0 + b * BEAT
            add(kick(False), tb, 0.8)
            if b in (1, 3):
                add(noise_hit(0.22, 900, 4000, 0.07), tb, 0.6)
            add(noise_hit(0.05, 7000, 14000, 0.015), tb + BEAT / 2, 0.35, 0.3)
            bn = int(BEAT / 2 * SR)
            bl = np.tanh(filt(tone(mtof(ch[0] - 24), bn, "saw"), "low", 500) * 1.5) * env(bn, 0.003, 0.12) * 0.32
            add(bl, tb + BEAT / 2)
        for s in (0, 0.75, 1.5, 2.5, 3.0):
            sn = int(0.2 * SR)
            st = sum(tone(mtof(m + 12), sn, "saw", (-0.01, 0.01)) for m in ch[:3])
            add(filt(st, "low", 4000) * env(sn, 0.002, 0.07) * 0.07, t0 + s * BEAT)

if style == "drive":
    n = int(1.5 * SR)
    add(noise_hit(1.5, 40, 2500, 0.4) * 0.8, 0)
mix = np.stack([L[:N], R[:N]], 1)
if style == "chill":
    # crossfade the overflow back into the start so the track loops seamlessly
    tail = np.stack([L[N:N + SR], R[N:N + SR]], 1)
    mix[:SR] += tail
else:
    f = int(1.5 * SR)
    mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = np.tanh(mix * 1.3)
mix /= np.max(np.abs(mix)) * 1.05
tmp = out + ".raw.wav"
wavfile.write(tmp, SR, (mix * 32767).astype(np.int16))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-15:TP=-1:LRA=9", "-ar", "48000", out], check=True)
subprocess.run(["rm", tmp])
print(out, seconds, style)
