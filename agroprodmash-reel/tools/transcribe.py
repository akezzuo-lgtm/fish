"""Transcribes take 1 of the voiceover with GigaAM v2 (sherpa-onnx) into word timestamps.

Model: https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19.tar.bz2
Usage: python3 tools/transcribe.py <model_dir>   (writes assets/vo/take1_words.json)
"""
import json
import re
import subprocess
import sys

import numpy as np
import sherpa_onnx

SRC = "../озвучка агропродмаш.MOV"
TAKE1_END = 81.2  # take 1 ends here; later takes are messier

M = sys.argv[1].rstrip("/") + "/"
rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=M + "encoder.int8.onnx", decoder=M + "decoder.onnx", joiner=M + "joiner.onnx",
    tokens=M + "tokens.txt", model_type="nemo_transducer", num_threads=4)
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", SRC, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(raw, dtype=np.float32)
sr = 16000
log = subprocess.run(["ffmpeg", "-hide_banner", "-i", SRC, "-af", "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
ev = [(k, float(v)) for k, v in re.findall(r"silence_(start|end): ([0-9.]+)", log)]
regions, cur = [], 0.0
for k, v in ev:
    if k == "start":
        if v - cur > 0.15:
            regions.append([cur, v])
    else:
        cur = v
merged = []
for a, b in regions:
    if merged and a - merged[-1][1] < 0.6 and b - merged[-1][0] < 20:
        merged[-1][1] = b
    else:
        merged.append([a, b])
words = []
for a, b in merged:
    if a > TAKE1_END:
        break
    a0 = max(0, a - 0.1)
    s = rec.create_stream()
    s.accept_waveform(sr, audio[int(a0 * sr):int((b + 0.1) * sr)])
    rec.decode_stream(s)
    cur = None
    for tok, t in zip(s.result.tokens, s.result.timestamps):
        if tok == " " or cur is None:
            if cur:
                words.append(cur)
            cur = {"w": tok.strip(), "s": round(a0 + t, 2)}
        else:
            cur["w"] += tok
    if cur:
        words.append(cur)
words = [w for w in words if w["w"]]
json.dump(words, open("assets/vo/take1_words.json", "w"), ensure_ascii=False)
print(" ".join(w["w"] for w in words))
