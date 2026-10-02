"""Synthesizes a 128 BPM electronic track whose sections line up with the edit."""
import json

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
BPM = 128
BEAT = 60 / BPM
TL = json.load(open("assets/timeline.json"))
SEC = {x["name"]: x for x in TL["sections"]}
TOTAL_BEATS = TL["beats"]
BARS = -(-TOTAL_BEATS // 4)
TAIL = 0.0
N = int(TOTAL_BEATS * BEAT * SR)
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)
duck = np.ones(N)  # sidechain envelope driven by the kick


def t_of(beat):
    return int(beat * BEAT * SR)


def add(sig, beat, gain=1.0, pan=0.0):
    i = t_of(beat)
    j = min(N, i + len(sig))
    if i >= N:
        return
    s = sig[: j - i] * gain
    L[i:j] += s * (1 - pan) ** 0.5 if pan > 0 else s
    R[i:j] += s * (1 + pan) ** 0.5 if pan < 0 else s


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = int(a * SR)
    if na:
        e[:na] *= np.linspace(0, 1, na)
    return e


def lp(x, f):
    return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)


def hp(x, f):
    return sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)


def saw(freq, n, detune=(0.0,)):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in detune:
        out += 2 * ((t * freq * (1 + d)) % 1) - 1
    return out / len(detune)


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 50 + 120 * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(2.2 * np.sin(ph) * env(n, 0.001, 0.12))


def clap():
    n = int(0.25 * SR)
    x = hp(lp(rng.standard_normal(n), 3500), 900)
    e = env(n, 0.001, 0.07)
    for k in (0.01, 0.02):
        e[int(k * SR):] += 0.6 * env(n - int(k * SR), 0.001, 0.05)
    return x * e * 0.8


def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    return hp(rng.standard_normal(n), 7000) * env(n, 0.001, 0.06 if open_ else 0.015) * 0.5


def impact():
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t / 0.08)) / SR) * env(n, 0.001, 0.6)
    noise = lp(rng.standard_normal(n), 2500) * env(n, 0.001, 0.4)
    return np.tanh(1.5 * boom + 0.5 * noise)


def riser(beats):
    n = int(beats * BEAT * SR)
    t = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    # sweep a band of noise upwards in chunks
    chunk = 1024
    for i in range(0, n, chunk):
        f = 300 + 7000 * t[i] ** 2
        seg = x[i:i + chunk]
        out[i:i + chunk] = sosfilt(butter(2, [f, f * 1.6], "band", fs=SR, output="sos"), seg)
    return out * t ** 1.5 * 0.9


def whoosh():
    n = int(0.6 * SR)
    t = np.linspace(0, 1, n)
    x = lp(rng.standard_normal(n), 3000) * np.sin(np.pi * t) ** 2
    return x * 0.6


NOTE = {"A": 57, "F": 53, "C": 48, "G": 55}
CHORDS = {"A": [0, 3, 7], "F": [0, 4, 7], "C": [0, 4, 7], "G": [0, 4, 7]}
PROG = ["A", "F", "C", "G"]


def mtof(m):
    return 440 * 2 ** ((m - 69) / 12)


def pad(root, beats):
    n = int(beats * BEAT * SR)
    x = sum(saw(mtof(NOTE[root] + 12 + i), n, (-0.006, 0, 0.006)) for i in CHORDS[root])
    return lp(x, 1800) * env(n, 0.08, 6.0) * 0.12


def stab(root):
    n = int(0.22 * SR)
    x = sum(saw(mtof(NOTE[root] + 12 + i), n, (-0.01, 0.01)) for i in CHORDS[root])
    return lp(x, 4200) * env(n, 0.002, 0.08) * 0.16


def bass(root, length=0.5):
    n = int(length * BEAT * SR)
    f = mtof(NOTE[root] - 24)
    x = saw(f, n) * 0.6 + np.sin(2 * np.pi * f * np.arange(n) / SR)
    return np.tanh(lp(x, 600) * 1.5) * env(n, 0.003, 0.15) * 0.35


# Music sections follow the voiceover timeline (beats): hook, build (arrival), drop, outro (people), end (CTA).
def section_at(beat):
    if beat < SEC["arrival"]["start"]:
        return "hook"
    if beat < SEC["robots"]["start"]:
        return "build"
    if beat < SEC["people"]["start"]:
        return "drop"
    if beat < SEC["cta"]["start"]:
        return "outro"
    return "end"


add(impact(), 0, 0.9)
BUILD_HALF = (SEC["arrival"]["start"] + SEC["robots"]["start"]) // 2
for bar in range(BARS):
    root = PROG[bar % 4]
    b0 = bar * 4
    sec = section_at(b0)
    full = sec in ("hook", "drop")
    if sec != "end":
        add(pad(root, 4), b0, 1.0 if sec != "build" else 0.8)
    for beat in range(4):
        b = b0 + beat
        sec = section_at(b)
        full = sec in ("hook", "drop")
        if b >= TOTAL_BEATS:
            break
        if full or sec == "outro" or (sec == "build" and (b >= BUILD_HALF or beat in (0, 2))):
            add(kick(), b, 0.9)
            i = t_of(b)
            j = min(N, i + int(0.25 * SR))
            duck[i:j] = np.minimum(duck[i:j], 1 - 0.65 * np.exp(-np.arange(j - i) / SR / 0.08))
        if full and beat in (1, 3):
            add(clap(), b, 0.8)
        if sec != "end":
            add(hat(), b + 0.5, 0.5, 0.3)
            if full:
                add(hat(), b + 0.25, 0.25, -0.3)
                add(hat(), b + 0.75, 0.25, -0.3)
        if full or sec == "outro":
            add(bass(root), b + 0.5)
            add(bass(root, 0.25), b + 0.75, 0.6)
    sec = section_at(b0)
    full = sec in ("hook", "drop")
    if full and sec == "drop":
        for s in (0, 0.75, 1.5, 2.5, 3.0):
            add(stab(root), b0 + s, 1.0, 0.2 if s % 1 else -0.2)
    if sec == "hook":
        for s in (0, 1.5, 3):
            add(stab(root), b0 + s, 0.8)

# Build-up into the drop: riser plus snare roll.
DROP = SEC["robots"]["start"]
add(riser(8), DROP - 8, 0.7)
for k in range(16):
    add(clap(), DROP - 4 + k * 0.25, 0.25 + 0.5 * k / 16)
# Transitions between chapters.
for name in ("robots", "food", "pack", "people"):
    beat = SEC[name]["start"]
    add(impact(), beat, 0.55)
    add(whoosh(), beat - 0.6, 0.8)
# End card: final hit and a held chord.
END = SEC["cta"]["start"]
add(impact(), END, 0.9)
add(pad("A", TOTAL_BEATS - END), END, 1.6)

mix = np.stack([L, R], 1)
# Duck everything except drums would need stems; approximate by ducking the whole mix lightly.
mix *= (0.55 + 0.45 * duck)[:, None]
fade = int(1.2 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix = np.tanh(mix * 1.4)
mix /= np.max(np.abs(mix)) * 1.05
wavfile.write("assets/music_raw.wav", SR, (mix * 32767).astype(np.int16))
print("seconds", N / SR)
